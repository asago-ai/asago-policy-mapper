"""Tests pinning the tracked-create defaults and LLMConfig contracts.

Mutation testing flagged these paths as untested: the tracking wrapper's
injected sampling defaults (``temperature``, ``top_p``, ``top_k``), the
message snapshot incidents carry while a call is in flight, the max-context
clamp boundaries and its arithmetic, and the output-token-parameter error
text. Each test here pins a real contract a caller or operator relies on,
not an implementation detail.
"""

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import httpx
import openai
import pytest

from asago_policy_mapper.llm import (
    _SAFETY_MARGIN,
    _SCHEMA_OVERHEAD_TOKENS,
    LLMConfig,
    SlimModel,
    TokenTracker,
    _wrap_with_tracking,
    create_client,
)


class _Answer(SlimModel):
    answer: str


def _wrapped_mock(config):
    """A MagicMock client under the production tracking wrapper.

    The mock records every kwarg the wrapper forwards to
    ``create_with_completion`` and returns a completion with usage.
    """
    client = MagicMock()
    completion = SimpleNamespace(usage=SimpleNamespace(prompt_tokens=1, completion_tokens=1, total_tokens=2))
    client.create_with_completion.return_value = ("parsed", completion)
    _wrap_with_tracking(client, TokenTracker(), config)
    return client


def _config(**kwargs) -> LLMConfig:
    return LLMConfig(base_url="http://localhost:8000/v1", model="test-model", **kwargs)


class TestTrackedCreateSamplingDefaults:
    """The wrapper injects LLMConfig's sampling defaults; caller values win."""

    def test_temperature_default_is_injected(self):
        client = _wrapped_mock(_config(temperature=0.7))
        client.chat.completions.create(model="m", messages=[{"role": "user", "content": "hi"}])
        assert client.create_with_completion.call_args.kwargs["temperature"] == 0.7

    def test_caller_temperature_wins(self):
        client = _wrapped_mock(_config(temperature=0.7))
        client.chat.completions.create(model="m", messages=[{"role": "user", "content": "hi"}], temperature=0.3)
        assert client.create_with_completion.call_args.kwargs["temperature"] == 0.3

    def test_top_p_default_is_injected(self):
        client = _wrapped_mock(_config(top_p=0.9))
        client.chat.completions.create(model="m", messages=[{"role": "user", "content": "hi"}])
        assert client.create_with_completion.call_args.kwargs["top_p"] == 0.9

    def test_caller_top_p_wins(self):
        client = _wrapped_mock(_config(top_p=0.9))
        client.chat.completions.create(model="m", messages=[{"role": "user", "content": "hi"}], top_p=0.5)
        assert client.create_with_completion.call_args.kwargs["top_p"] == 0.5

    def test_top_k_default_is_injected_via_extra_body(self):
        client = _wrapped_mock(_config(top_k=64))
        client.chat.completions.create(model="m", messages=[{"role": "user", "content": "hi"}])
        assert client.create_with_completion.call_args.kwargs["extra_body"] == {"top_k": 64}

    def test_caller_extra_body_top_k_wins(self):
        client = _wrapped_mock(_config(top_k=64))
        client.chat.completions.create(model="m", messages=[{"role": "user", "content": "hi"}], extra_body={"top_k": 8})
        assert client.create_with_completion.call_args.kwargs["extra_body"] == {"top_k": 8}

    def test_unset_sampling_parameters_are_not_sent(self):
        """Without top_p/top_k configured, neither parameter reaches the wire."""
        client = _wrapped_mock(_config())
        client.chat.completions.create(model="m", messages=[{"role": "user", "content": "hi"}])
        forwarded = client.create_with_completion.call_args.kwargs
        assert "top_p" not in forwarded
        assert "extra_body" not in forwarded


class TestIncidentMessagesSnapshot:
    """Incidents snapshot the in-flight request; the slot is cleared after."""

    def _overflow_then_success(self, tracker, messages):
        """Run one call over caller-owned messages: overflow, then success."""
        requests = []

        def handler(request):
            requests.append(json.loads(request.read()))
            if len(requests) == 1:
                body = {
                    "error": {
                        "message": "maximum context length is 8192 tokens. However, you requested 4096 "
                        "output tokens and 7500 input tokens",
                        "type": "invalid_request_error",
                        "param": None,
                        "code": None,
                    }
                }
                return httpx.Response(400, json=body)
            return httpx.Response(
                200,
                json={
                    "id": "chatcmpl-1",
                    "object": "chat.completion",
                    "created": 0,
                    "model": "test-model",
                    "choices": [
                        {"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": "{}"}}
                    ],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                },
            )

        config = _config(sdk_max_retries=0)
        http_client = httpx.Client(transport=httpx.MockTransport(handler))
        with patch(
            "asago_policy_mapper.llm.OpenAI",
            lambda **kw: openai.OpenAI(http_client=http_client, **kw),
        ):
            client = create_client(config, tracker=tracker)
            client.chat.completions.create(
                model="test-model",
                messages=messages,
                max_tokens=4096,
            )
        return requests

    def test_incident_carries_the_in_flight_messages(self):
        """An incident recorded mid-call snapshots the request's messages.

        A context overflow fires while the call is in flight, so its incident
        must carry the messages that call sent — deep-copied, so mutating the
        caller's message dicts after the fact cannot rewrite the incident.
        """
        tracker = TokenTracker()
        messages = [{"role": "user", "content": "A" * 2000}]
        requests = self._overflow_then_success(tracker, messages)
        assert len(requests) == 2

        messages[0]["content"] = "rewritten after the call"

        (incident,) = [i for i in tracker.incidents if i["kind"] == "context_overflow"]
        assert incident["messages"] == [{"role": "user", "content": "A" * 2000}]

    def test_thread_local_messages_cleared_after_call(self):
        """After the call returns, no in-flight messages remain on the tracker.

        A later incident in the same thread must not carry a stale snapshot,
        so the slot is reset to None, not to any truthy placeholder.
        """
        tracker = TokenTracker()
        self._overflow_then_success(tracker, [{"role": "user", "content": "A" * 2000}])
        assert tracker._thread_local.current_messages is None

        # The practical consequence: a post-call incident carries no messages.
        tracker.record_incident("later", "recorded after the call finished")
        assert "messages" not in tracker.incidents[-1]


class TestLLMConfigClamp:
    """The max-context clamp's boundaries and arithmetic are load-bearing."""

    def test_boundary_context_of_one_still_clamps(self):
        """max_context=1 is above the guard's floor, so the clamp applies."""
        config = _config(max_context=1)
        assert config.max_tokens == 1 - _SAFETY_MARGIN - _SCHEMA_OVERHEAD_TOKENS

    def test_max_tokens_equal_to_context_clamps(self):
        """The clamp fires on equality, not only above."""
        config = _config(max_tokens=1000, max_context=1000)
        assert config.max_tokens == 1000 - _SAFETY_MARGIN - _SCHEMA_OVERHEAD_TOKENS

    def test_clamp_subtracts_both_margins(self):
        """The clamp removes the safety margin and the schema overhead."""
        config = _config(max_tokens=8192, max_context=2000)
        assert config.max_tokens == 2000 - _SAFETY_MARGIN - _SCHEMA_OVERHEAD_TOKENS

    def test_max_tokens_below_context_is_untouched(self):
        config = _config(max_tokens=512, max_context=2000)
        assert config.max_tokens == 512

    def test_output_token_parameter_error_lists_allowed_values(self):
        with pytest.raises(ValueError, match="max_tokens, max_completion_tokens"):
            _config(output_token_parameter="tokens")
