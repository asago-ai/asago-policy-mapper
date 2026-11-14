import copy
import json
import logging
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import httpx
import openai
import pytest
from pydantic import ValidationError

from asago_policy_mapper.llm import (
    _MAX_TRUNCATION_RETRIES,
    IncompleteOutputException,
    LLMConfig,
    SlimModel,
    StructuredOutputMode,
    TokenTracker,
    ValidationRetryExhausted,
    _call_with_retry,
    _extract_json_span,
    _extract_response_content,
    _IncompleteOutput,
    _parse_completion,
    _retry_with_validation,
    _strip_titles,
    _StructuredClient,
    _track_completion,
    _truncate_messages,
    _wrap_with_tracking,
    budget_max_tokens,
    create_client,
)

# ---------------------------------------------------------------------------
# _strip_titles
# ---------------------------------------------------------------------------


class TestStripTitles:
    def test_removes_title_from_flat_dict(self):
        obj = {"title": "Remove me", "name": "keep"}
        result = _strip_titles(obj)
        assert "title" not in result
        assert result["name"] == "keep"

    def test_removes_title_from_nested_dicts(self):
        obj = {
            "title": "top",
            "properties": {
                "title": "nested",
                "field": {
                    "title": "deep",
                    "type": "string",
                },
            },
        }
        result = _strip_titles(obj)
        assert "title" not in result
        assert "title" not in result["properties"]
        assert "title" not in result["properties"]["field"]
        assert result["properties"]["field"]["type"] == "string"

    def test_removes_title_from_list_of_dicts(self):
        obj = [{"title": "a", "x": 1}, {"title": "b", "y": 2}]
        result = _strip_titles(obj)
        assert all("title" not in d for d in result)
        assert result[0]["x"] == 1
        assert result[1]["y"] == 2

    def test_already_clean_dict(self):
        obj = {"name": "no title here", "value": 42}
        result = _strip_titles(obj)
        assert result == {"name": "no title here", "value": 42}

    def test_non_dict_passthrough(self):
        assert _strip_titles(42) == 42
        assert _strip_titles("hello") == "hello"
        assert _strip_titles(None) is None

    def test_mixed_nested_structure(self):
        obj = {
            "title": "root",
            "items": [
                {"title": "item1", "id": 1},
                {"id": 2},
            ],
            "nested": {"title": "child", "data": [{"title": "deep"}]},
        }
        result = _strip_titles(obj)
        assert "title" not in result
        assert "title" not in result["items"][0]
        assert "title" not in result["nested"]
        assert "title" not in result["nested"]["data"][0]

    def test_mutates_in_place(self):
        obj = {"title": "gone", "keep": "yes"}
        returned = _strip_titles(obj)
        assert returned is obj
        assert "title" not in obj


# ---------------------------------------------------------------------------
# TokenTracker
# ---------------------------------------------------------------------------


class TestTokenTracker:
    def test_add_with_valid_usage(self):
        tracker = TokenTracker()
        usage = SimpleNamespace(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        tracker.add(usage)
        assert tracker.prompt_tokens == 10
        assert tracker.completion_tokens == 5
        assert tracker.total_tokens == 15
        assert tracker.calls == 1

    def test_add_accumulates(self):
        tracker = TokenTracker()
        usage1 = SimpleNamespace(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        usage2 = SimpleNamespace(prompt_tokens=20, completion_tokens=10, total_tokens=30)
        tracker.add(usage1)
        tracker.add(usage2)
        assert tracker.prompt_tokens == 30
        assert tracker.completion_tokens == 15
        assert tracker.total_tokens == 45
        assert tracker.calls == 2

    def test_add_none_usage_is_noop(self):
        tracker = TokenTracker()
        tracker.add(None)
        assert tracker.prompt_tokens == 0
        assert tracker.calls == 0

    def test_add_with_stage(self):
        tracker = TokenTracker()
        usage = SimpleNamespace(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        tracker.add(usage, stage="judge")
        assert "judge" in tracker.per_stage
        assert tracker.per_stage["judge"]["prompt_tokens"] == 10
        assert tracker.per_stage["judge"]["completion_tokens"] == 5
        assert tracker.per_stage["judge"]["total_tokens"] == 15
        assert tracker.per_stage["judge"]["calls"] == 1

    def test_add_stage_accumulates(self):
        tracker = TokenTracker()
        usage1 = SimpleNamespace(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        usage2 = SimpleNamespace(prompt_tokens=20, completion_tokens=10, total_tokens=30)
        tracker.add(usage1, stage="ground")
        tracker.add(usage2, stage="ground")
        assert tracker.per_stage["ground"]["calls"] == 2
        assert tracker.per_stage["ground"]["total_tokens"] == 45

    def test_usage_values_handles_missing_attrs(self):
        usage = SimpleNamespace()
        pt, ct, tt = TokenTracker._usage_values(usage)
        assert (pt, ct, tt) == (0, 0, 0)

    def test_usage_values_handles_none_attrs(self):
        usage = SimpleNamespace(prompt_tokens=None, completion_tokens=None, total_tokens=None)
        pt, ct, tt = TokenTracker._usage_values(usage)
        assert (pt, ct, tt) == (0, 0, 0)

    def test_to_dict(self):
        tracker = TokenTracker()
        usage = SimpleNamespace(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        tracker.add(usage, stage="judge")
        tracker.record_incident("test_error", "something failed")

        d = tracker.to_dict()
        assert d["prompt_tokens"] == 10
        assert d["completion_tokens"] == 5
        assert d["total_tokens"] == 15
        assert d["calls"] == 1
        assert "judge" in d["per_stage"]
        assert len(d["incidents"]) == 1
        assert d["incidents"][0]["kind"] == "test_error"

    def test_record_incident_basic(self):
        tracker = TokenTracker()
        tracker.record_incident("context_overflow", "max_tokens reduced")
        assert len(tracker.incidents) == 1
        assert tracker.incidents[0]["kind"] == "context_overflow"
        assert tracker.incidents[0]["detail"] == "max_tokens reduced"

    def test_record_incident_includes_stage(self):
        tracker = TokenTracker()
        tracker.set_stage("grounding")
        tracker.record_incident("error", "something broke")
        assert tracker.incidents[0]["stage"] == "grounding"

    def test_record_incident_no_stage(self):
        tracker = TokenTracker()
        tracker.record_incident("error", "no stage set")
        assert "stage" not in tracker.incidents[0]

    def test_set_stage(self):
        tracker = TokenTracker()
        tracker.set_stage("judge")
        assert tracker._current_stage == "judge"
        tracker.set_stage(None)
        assert tracker._current_stage is None


# ---------------------------------------------------------------------------
# _track_completion
# ---------------------------------------------------------------------------


class TestTrackCompletion:
    def test_valid_usage_updates_tracker(self):
        tracker = TokenTracker()
        usage = SimpleNamespace(prompt_tokens=100, completion_tokens=50, total_tokens=150)
        completion = SimpleNamespace(usage=usage)
        _track_completion(tracker, completion)
        assert tracker.prompt_tokens == 100
        assert tracker.completion_tokens == 50
        assert tracker.total_tokens == 150
        assert tracker.calls == 1

    def test_no_usage_logs_warning(self, caplog):
        tracker = TokenTracker()
        completion = SimpleNamespace(usage=None)
        with caplog.at_level(logging.WARNING):
            _track_completion(tracker, completion)
        assert tracker._warned_no_usage is True
        assert "no token usage" in caplog.text

    def test_no_usage_warns_only_once(self, caplog):
        tracker = TokenTracker()
        completion = SimpleNamespace(usage=None)
        with caplog.at_level(logging.WARNING):
            _track_completion(tracker, completion)
            caplog.clear()
            _track_completion(tracker, completion)
        assert "no token usage" not in caplog.text

    def test_zero_total_tokens_triggers_warning(self, caplog):
        tracker = TokenTracker()
        usage = SimpleNamespace(prompt_tokens=0, completion_tokens=0, total_tokens=0)
        completion = SimpleNamespace(usage=usage)
        with caplog.at_level(logging.WARNING):
            _track_completion(tracker, completion)
        assert tracker._warned_no_usage is True

    def test_no_usage_attr_triggers_warning(self, caplog):
        tracker = TokenTracker()
        completion = object()  # no .usage attribute at all
        with caplog.at_level(logging.WARNING):
            _track_completion(tracker, completion)
        assert tracker._warned_no_usage is True


# ---------------------------------------------------------------------------
# _extract_response_content
# ---------------------------------------------------------------------------


class TestExtractResponseContent:
    def test_valid_completion(self):
        msg = SimpleNamespace(content="Hello world")
        choice = SimpleNamespace(message=msg)
        completion = SimpleNamespace(choices=[choice])
        assert _extract_response_content(completion) == "Hello world"

    def test_empty_choices(self):
        completion = SimpleNamespace(choices=[])
        assert _extract_response_content(completion) is None

    def test_no_choices_attr(self):
        completion = SimpleNamespace()
        assert _extract_response_content(completion) is None

    def test_no_message_attr(self):
        choice = SimpleNamespace()
        completion = SimpleNamespace(choices=[choice])
        assert _extract_response_content(completion) is None

    def test_no_content_attr(self):
        msg = SimpleNamespace()
        choice = SimpleNamespace(message=msg)
        completion = SimpleNamespace(choices=[choice])
        assert _extract_response_content(completion) is None


# ---------------------------------------------------------------------------
# _extract_json_span
# ---------------------------------------------------------------------------


class TestExtractJsonSpan:
    """The last complete JSON object or array wins; raw non-JSON passes through."""

    def test_single_object(self):
        assert _extract_json_span('{"a": 1}') == '{"a": 1}'

    def test_prose_before_object(self):
        assert _extract_json_span('Here you go:\n{"a": 1}') == '{"a": 1}'

    def test_last_span_wins_over_earlier_quoted_span(self):
        content = 'Prompt said {"a": 1}. Answer: {"b": 2}'
        assert _extract_json_span(content) == '{"b": 2}'

    def test_span_at_index_zero(self):
        assert _extract_json_span('{"a": 1} trailing prose') == '{"a": 1}'

    def test_invalid_span_between_two_valid_ones(self):
        # The middle object is incomplete (unclosed brace), so raw_decode
        # fails at its opening index and the last complete span still wins.
        content = '{"a": 1} then {"broken: ' + "x" * 20 + ' then {"c": 3}'
        assert _extract_json_span(content) == '{"c": 3}'

    def test_array_span_wins_when_last(self):
        content = 'object {"a": 1} then array [1, 2, 3]'
        assert _extract_json_span(content) == "[1, 2, 3]"

    def test_nested_braces_inside_string_do_not_confuse(self):
        content = 'result: {"text": "a { not json start", "n": 2}'
        assert _extract_json_span(content) == '{"text": "a { not json start", "n": 2}'

    def test_raw_non_json_content_returned_as_is(self):
        content = "no json here at all"
        assert _extract_json_span(content) == content

    def test_empty_string_returned_as_is(self):
        assert _extract_json_span("") == ""

    def test_incomplete_json_only_returns_content_as_is(self):
        # An unclosed object never completes, so nothing valid was found and
        # the raw content comes back unchanged.
        content = '{"broken": '
        assert _extract_json_span(content) == content

    def test_consumed_prefix_skips_nested_open_braces(self):
        # After the first span consumes '{"a": 1}', the inner "{b" region of
        # the second object must not produce a bogus shorter span; the last
        # complete object still wins.
        content = '{"a": 1} {"x": {"b": 2}}'
        assert _extract_json_span(content) == '{"x": {"b": 2}}'

    def test_only_open_brackets_inside_larger_content(self):
        # Characters that are not object/array openers never start a span.
        content = "plain [not a span"
        assert _extract_json_span(content) == content


# ---------------------------------------------------------------------------
# _truncate_messages
# ---------------------------------------------------------------------------


class TestTruncateMessages:
    def test_truncates_long_user_message(self):
        long_content = "x" * 2000
        messages = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": long_content},
        ]
        result = _truncate_messages(messages)
        assert result is not None
        # 60% of 2000 = 1200, which is > 500 min
        assert len(result[1]["content"]) == 1200

    def test_short_user_message_returns_none(self):
        messages = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "short"},
        ]
        result = _truncate_messages(messages)
        assert result is None

    def test_exactly_min_threshold_returns_none(self):
        messages = [{"role": "user", "content": "x" * 500}]
        result = _truncate_messages(messages)
        assert result is None

    def test_no_user_messages_returns_none(self):
        messages = [{"role": "system", "content": "System only."}]
        result = _truncate_messages(messages)
        assert result is None

    def test_empty_messages_returns_none(self):
        result = _truncate_messages([])
        assert result is None

    def test_does_not_mutate_original(self):
        long_content = "x" * 2000
        messages = [{"role": "user", "content": long_content}]
        original_content = messages[0]["content"]
        _truncate_messages(messages)
        assert messages[0]["content"] == original_content
        assert len(messages[0]["content"]) == 2000

    def test_truncates_longest_user_message(self):
        messages = [
            {"role": "user", "content": "a" * 1000},
            {"role": "user", "content": "b" * 3000},
        ]
        result = _truncate_messages(messages)
        assert result is not None
        # Longest is index 1 (3000 chars), truncated to 60% = 1800
        assert len(result[0]["content"]) == 1000  # unchanged
        assert len(result[1]["content"]) == 1800

    def test_truncation_respects_minimum(self):
        # 60% of 600 = 360, which is < 500, so clamp to 500
        messages = [{"role": "user", "content": "y" * 600}]
        result = _truncate_messages(messages)
        assert result is not None
        assert len(result[0]["content"]) == 500

    def test_equal_length_user_messages_truncates_first(self):
        """Two equal-length user messages: the FIRST one is truncated."""
        messages = [
            {"role": "user", "content": "a" * 1000},
            {"role": "user", "content": "b" * 1000},
        ]
        result = _truncate_messages(messages)
        assert result is not None
        # The first message keeps its distinct content prefix after truncation.
        assert result[0]["content"] == "a" * 600
        assert result[1]["content"] == "b" * 1000

    def test_later_longer_user_message_wins(self):
        """A strictly longer later message must override an earlier selection."""
        messages = [
            {"role": "user", "content": "a" * 1000},
            {"role": "user", "content": "b" * 2000},
        ]
        result = _truncate_messages(messages)
        assert result is not None
        assert result[0]["content"] == "a" * 1000
        assert result[1]["content"] == "b" * 1200

    def test_longest_user_message_before_longer_system_message(self):
        """Only user messages are truncation candidates, regardless of length."""
        messages = [
            {"role": "system", "content": "s" * 5000},
            {"role": "user", "content": "u" * 1000},
        ]
        result = _truncate_messages(messages)
        assert result is not None
        assert result[0]["content"] == "s" * 5000
        assert result[1]["content"] == "u" * 600


# ---------------------------------------------------------------------------
# budget_max_tokens
# ---------------------------------------------------------------------------


class TestBudgetMaxTokens:
    """Pin the exact budget arithmetic with literal expected values.

    ``estimate_message_tokens`` counts 4 tokens per message plus one token per
    3 characters of content, plus a closing 2. With one message of 30 chars:
    4 + 10 + 2 = 16 estimated input tokens, plus the 500-token schema
    overhead. The safety margin is 64 and the minimum output budget is 256.
    """

    MESSAGES = [{"role": "user", "content": "a" * 30}]

    def test_zero_max_context_returns_requested_unchanged(self):
        assert budget_max_tokens(self.MESSAGES, max_context=0, requested_max_tokens=8192) == 8192

    def test_negative_max_context_returns_requested_unchanged(self):
        assert budget_max_tokens(self.MESSAGES, max_context=-8, requested_max_tokens=8192) == 8192

    def test_normal_case_caps_to_available_minus_margin(self):
        # estimated_input = 16 + 500 = 516; available = 8192 - 516 - 64 = 7612
        assert budget_max_tokens(self.MESSAGES, max_context=8192, requested_max_tokens=9999) == 7612

    def test_requested_below_available_is_returned_unchanged(self):
        # available = 7612, so a smaller request stays as-is
        assert budget_max_tokens(self.MESSAGES, max_context=8192, requested_max_tokens=3000) == 3000

    def test_available_exactly_min_returns_min(self):
        # max_context = 516 + 64 + 256 = 836 makes available exactly the
        # minimum (256), which passes the "< min" check and is returned.
        assert budget_max_tokens(self.MESSAGES, max_context=836, requested_max_tokens=9999) == 256

    def test_available_exactly_min_with_smaller_request_returns_request(self):
        """available == 256 is NOT critically low; a request below it stands.

        This pins the strict `<` in the minimum check: with the boundary
        available == _MIN_OUTPUT_TOKENS, the function caps rather than clamps.
        """
        assert budget_max_tokens(self.MESSAGES, max_context=836, requested_max_tokens=100) == 100

    def test_max_context_of_one_still_computes_budget(self):
        """max_context=1 is positive, so the budget path runs and clamps to min.

        Pins the strict `<= 0` in the guard: 1 must not be treated as "no
        context limit".
        """
        assert budget_max_tokens(self.MESSAGES, max_context=1, requested_max_tokens=9999) == 256

    def test_available_just_below_min_clamps_to_min(self):
        # max_context = 835 makes available = 255, one below the minimum.
        assert budget_max_tokens(self.MESSAGES, max_context=835, requested_max_tokens=9999) == 256

    def test_critically_low_budget_logs_warning_with_values(self, caplog):
        with caplog.at_level(logging.WARNING):
            result = budget_max_tokens(self.MESSAGES, max_context=700, requested_max_tokens=9999)
        assert result == 256
        records = [r for r in caplog.records if r.name == "asago_policy_mapper.llm"]
        assert len(records) == 1
        # The exact rendered message, not a mutated template.
        assert records[0].getMessage() == (
            "Token budget critically low: estimated_input=516, max_context=700, available_for_output=120 (min=256)"
        )

    def test_normal_capping_logs_debug_with_values(self, caplog):
        with caplog.at_level(logging.DEBUG):
            result = budget_max_tokens(self.MESSAGES, max_context=8192, requested_max_tokens=9999)
        assert result == 7612
        records = [r for r in caplog.records if r.name == "asago_policy_mapper.llm"]
        assert len(records) == 1
        assert records[0].getMessage() == "Budget: max_tokens 9999 -> 7612 (input~516, context=8192)"

    def test_no_debug_log_when_request_not_capped(self, caplog):
        with caplog.at_level(logging.DEBUG):
            budget_max_tokens(self.MESSAGES, max_context=8192, requested_max_tokens=3000)
        assert "Budget: max_tokens" not in caplog.text


# ---------------------------------------------------------------------------
# _call_with_retry
# ---------------------------------------------------------------------------


class TestCallWithRetry:
    def _make_config(self):
        return LLMConfig(base_url="http://test", model="test-model")

    def test_success_on_first_attempt(self):
        do_call = MagicMock(return_value=("result", "completion"))
        kwargs = {"messages": [{"role": "user", "content": "hello"}], "max_retries": 0}
        config = self._make_config()

        result = _call_with_retry(do_call, kwargs, config)
        assert result == ("result", "completion")
        do_call.assert_called_once()

    def test_incomplete_output_with_truncatable_messages_retries(self):
        long_content = "x" * 2000
        cause = IncompleteOutputException()
        do_call = MagicMock(side_effect=[_IncompleteOutput(cause), ("ok", "comp")])
        kwargs = {"messages": [{"role": "user", "content": long_content}], "max_retries": 0}
        config = self._make_config()

        result = _call_with_retry(do_call, kwargs, config)
        assert result == ("ok", "comp")
        assert do_call.call_count == 2

    def test_incomplete_output_short_messages_raises(self):
        cause = IncompleteOutputException()
        do_call = MagicMock(side_effect=_IncompleteOutput(cause))
        kwargs = {"messages": [{"role": "user", "content": "short"}], "max_retries": 0}
        config = self._make_config()

        with pytest.raises(IncompleteOutputException):
            _call_with_retry(do_call, kwargs, config)

    def test_incomplete_output_records_incident_when_cannot_truncate(self):
        tracker = TokenTracker()
        cause = IncompleteOutputException()
        do_call = MagicMock(side_effect=_IncompleteOutput(cause))
        kwargs = {"messages": [{"role": "user", "content": "short"}], "max_retries": 0}
        config = self._make_config()

        with pytest.raises(IncompleteOutputException):
            _call_with_retry(do_call, kwargs, config, tracker=tracker)
        assert any(i["kind"] == "output_truncated" for i in tracker.incidents)

    def test_incomplete_output_records_incident_on_retry(self):
        tracker = TokenTracker()
        long_content = "x" * 2000
        cause = IncompleteOutputException()
        do_call = MagicMock(side_effect=[_IncompleteOutput(cause), ("ok", "comp")])
        kwargs = {"messages": [{"role": "user", "content": long_content}], "max_retries": 0}
        config = self._make_config()

        _call_with_retry(do_call, kwargs, config, tracker=tracker)
        assert any(i["kind"] == "output_truncated" for i in tracker.incidents)

    def test_messages_shortened_on_retry(self):
        long_content = "x" * 2000
        cause = IncompleteOutputException()

        captured_kwargs = {}

        def side_effect(kw):
            if not captured_kwargs:
                captured_kwargs["first"] = copy.deepcopy(kw)
                raise _IncompleteOutput(cause)
            captured_kwargs["second"] = copy.deepcopy(kw)
            return ("ok", "comp")

        do_call = MagicMock(side_effect=side_effect)
        kwargs = {"messages": [{"role": "user", "content": long_content}], "max_retries": 0}
        config = self._make_config()

        _call_with_retry(do_call, kwargs, config)
        first_len = len(captured_kwargs["first"]["messages"][0]["content"])
        second_len = len(captured_kwargs["second"]["messages"][0]["content"])
        assert second_len < first_len


# ---------------------------------------------------------------------------
# _retry_with_validation
# ---------------------------------------------------------------------------


def _make_retry_exc(msg, failed_attempts=None):
    """Create a ValidationRetryExhausted with the given message and failed attempts."""
    return ValidationRetryExhausted(msg, failed_attempts=failed_attempts)


def _context_overflow_error() -> openai.BadRequestError:
    """A 400 in the shape endpoints report context-length overflow."""
    request = httpx.Request("POST", "http://test/v1/chat/completions")
    response = httpx.Response(400, request=request)
    return openai.BadRequestError(
        "maximum context length is 8192 tokens. However, you requested 4096 output tokens and 4000 input tokens",
        response=response,
        body=None,
    )


class TestRetryWithValidation:
    def _make_config(self):
        return LLMConfig(base_url="http://test", model="test-model")

    def _make_messages(self):
        return [{"role": "user", "content": "hello"}]

    def test_success_on_first_call(self):
        do_call = MagicMock(return_value=("result", "completion"))
        messages = self._make_messages()
        kwargs = {"messages": messages, "max_tokens": 4096}
        config = self._make_config()

        result = _retry_with_validation(
            do_call,
            kwargs,
            config,
            tracker=None,
            original_messages=copy.deepcopy(messages),
            current_messages=messages,
            max_retries=2,
        )
        assert result == ("result", "completion")
        do_call.assert_called_once()

    def test_incomplete_output_wraps_in_incomplete_output(self):
        cause = IncompleteOutputException()
        do_call = MagicMock(side_effect=cause)
        messages = self._make_messages()
        kwargs = {"messages": messages, "max_tokens": 4096}
        config = self._make_config()

        with pytest.raises(_IncompleteOutput) as exc_info:
            _retry_with_validation(
                do_call,
                kwargs,
                config,
                tracker=None,
                original_messages=copy.deepcopy(messages),
                current_messages=messages,
                max_retries=2,
            )
        assert exc_info.value.cause is cause

    def test_context_overflow_reduces_max_tokens(self):
        """Context overflow with a valid reduction retries with lower max_tokens."""
        exc = _context_overflow_error()
        do_call = MagicMock(side_effect=[exc, ("ok", "comp")])
        messages = self._make_messages()
        original = copy.deepcopy(messages)
        kwargs = {"messages": copy.deepcopy(messages), "max_tokens": 4096}
        config = self._make_config()

        result = _retry_with_validation(
            do_call,
            kwargs,
            config,
            tracker=None,
            original_messages=original,
            current_messages=messages,
            max_retries=1,
        )
        assert result == ("ok", "comp")
        assert do_call.call_count == 2
        # Expected new_max: 8192 - 4000 - 32 = 4160
        assert kwargs["max_tokens"] == 4160

    def test_context_overflow_records_incident(self):
        exc = _context_overflow_error()
        do_call = MagicMock(side_effect=[exc, ("ok", "comp")])
        messages = self._make_messages()
        original = copy.deepcopy(messages)
        kwargs = {"messages": copy.deepcopy(messages), "max_tokens": 4096}
        config = self._make_config()
        tracker = TokenTracker()

        _retry_with_validation(
            do_call,
            kwargs,
            config,
            tracker=tracker,
            original_messages=original,
            current_messages=messages,
            max_retries=1,
        )
        assert any(i["kind"] == "context_overflow" for i in tracker.incidents)

    def test_context_overflow_reduces_configured_completion_parameter(self):
        exc = _context_overflow_error()
        do_call = MagicMock(side_effect=[exc, ("ok", "comp")])
        messages = self._make_messages()
        original = copy.deepcopy(messages)
        kwargs = {"messages": copy.deepcopy(messages), "max_completion_tokens": 4096}
        config = LLMConfig(
            base_url="http://test",
            model="test-model",
            output_token_parameter="max_completion_tokens",
        )

        result = _retry_with_validation(
            do_call,
            kwargs,
            config,
            tracker=None,
            original_messages=original,
            current_messages=messages,
            max_retries=1,
        )
        assert result == ("ok", "comp")
        assert kwargs["max_completion_tokens"] == 4160
        assert "max_tokens" not in kwargs

    def test_validation_error_retries_with_hint(self):
        exc = _make_retry_exc("some validation error")
        do_call = MagicMock(side_effect=[exc, ("ok", "comp")])
        messages = self._make_messages()
        original = copy.deepcopy(messages)
        kwargs = {"messages": copy.deepcopy(messages), "max_tokens": 4096}
        config = self._make_config()

        result = _retry_with_validation(
            do_call,
            kwargs,
            config,
            tracker=None,
            original_messages=original,
            current_messages=messages,
            max_retries=1,
        )
        assert result == ("ok", "comp")
        assert do_call.call_count == 2
        # On retry, messages should have an appended user message with the error hint
        retry_messages = kwargs["messages"]
        assert any(msg["role"] == "user" and "Validation error:" in msg["content"] for msg in retry_messages)

    def test_max_retries_two_makes_exactly_three_wire_calls(self):
        """max_retries=2 means 1 initial call + 2 retries = exactly 3 calls."""
        exc = _make_retry_exc("persistent error")
        do_call = MagicMock(side_effect=[exc, exc, exc, ("late", "comp")])
        messages = self._make_messages()
        original = copy.deepcopy(messages)
        kwargs = {"messages": copy.deepcopy(messages), "max_tokens": 4096}
        config = self._make_config()

        # A tracker makes the final ValidationRetryExhausted branch record an
        # incident, which the trailing RuntimeError path would never do.
        tracker = TokenTracker()
        with pytest.raises(ValidationRetryExhausted):
            _retry_with_validation(
                do_call,
                kwargs,
                config,
                tracker=tracker,
                original_messages=original,
                current_messages=messages,
                max_retries=2,
            )
        # The fourth configured side effect must never be reached.
        assert do_call.call_count == 3
        assert any(i["kind"] == "validation_exhausted" for i in tracker.incidents)

    def test_max_retries_zero_makes_exactly_one_wire_call(self):
        exc = _make_retry_exc("immediate failure")
        do_call = MagicMock(side_effect=[exc, ("never", "comp")])
        messages = self._make_messages()
        original = copy.deepcopy(messages)
        kwargs = {"messages": copy.deepcopy(messages), "max_tokens": 4096}
        config = self._make_config()

        with pytest.raises(ValidationRetryExhausted):
            _retry_with_validation(
                do_call,
                kwargs,
                config,
                tracker=None,
                original_messages=original,
                current_messages=messages,
                max_retries=0,
            )
        assert do_call.call_count == 1

    def test_negative_max_retries_never_calls_and_raises_runtimeerror(self):
        """A negative max_retries permits zero attempts and hits the guard raise.

        Pins the loop bound ``range(max_retries + 1)``: with max_retries=-1
        the loop body never runs, so the wire is never called and the trailing
        RuntimeError (not a validation exception) propagates.
        """
        do_call = MagicMock(return_value=("ok", "comp"))
        messages = self._make_messages()
        kwargs = {"messages": copy.deepcopy(messages), "max_tokens": 4096}
        config = self._make_config()

        with pytest.raises(RuntimeError, match=r"^_retry_with_validation exhausted retries"):
            _retry_with_validation(
                do_call,
                kwargs,
                config,
                tracker=None,
                original_messages=copy.deepcopy(messages),
                current_messages=messages,
                max_retries=-1,
            )
        do_call.assert_not_called()

    def test_retry_messages_are_deep_copied_from_current(self):
        """Mutating the retry messages must not leak into current_messages."""
        exc = _make_retry_exc("some validation error")
        do_call = MagicMock(side_effect=[exc, ("ok", "comp")])
        messages = self._make_messages()
        original = copy.deepcopy(messages)
        kwargs = {"messages": copy.deepcopy(messages), "max_tokens": 4096}
        config = self._make_config()

        _retry_with_validation(
            do_call,
            kwargs,
            config,
            tracker=None,
            original_messages=original,
            current_messages=messages,
            max_retries=1,
        )
        retry_messages = kwargs["messages"]
        # The retry conversation grows beyond the original single message.
        assert len(retry_messages) > len(messages)
        # The caller's current_messages list stays untouched.
        assert messages == self._make_messages()
        # Deep copy: mutating the retry copy must not touch the original.
        retry_messages[0]["content"] = "mutated"
        assert messages[0]["content"] == "hello"

    def test_validation_retry_logs_warning_with_attempt_count(self, caplog):
        """Each validation retry logs attempt n/(max_retries+1) with the summary."""
        exc = _make_retry_exc("line one of error\nline two of error")
        do_call = MagicMock(side_effect=[exc, ("ok", "comp")])
        messages = self._make_messages()
        original = copy.deepcopy(messages)
        kwargs = {"messages": copy.deepcopy(messages), "max_tokens": 4096}
        config = self._make_config()

        with caplog.at_level(logging.WARNING):
            _retry_with_validation(
                do_call,
                kwargs,
                config,
                tracker=None,
                original_messages=original,
                current_messages=messages,
                max_retries=1,
            )
        warning = caplog.text
        # The full template as one string, so mutated fragments cannot pass.
        assert (
            "Structured output validation failed (attempt 1/2), "
            "retrying with fresh messages + error hint: line one of error" in warning
        )

    def test_validation_retry_with_empty_message_logs_exception_name(self, caplog):
        """An empty exception message falls back to the exception class name."""
        exc = _make_retry_exc("")
        do_call = MagicMock(side_effect=[exc, ("ok", "comp")])
        messages = self._make_messages()
        original = copy.deepcopy(messages)
        kwargs = {"messages": copy.deepcopy(messages), "max_tokens": 4096}
        config = self._make_config()

        with caplog.at_level(logging.WARNING):
            _retry_with_validation(
                do_call,
                kwargs,
                config,
                tracker=None,
                original_messages=original,
                current_messages=messages,
                max_retries=1,
            )
        warning = caplog.text
        assert "retrying with fresh messages + error hint: ValidationRetryExhausted" in warning

    def test_validation_retry_truncates_long_summary_to_200_chars(self, caplog):
        """The retry warning carries at most the first 200 chars of the summary."""
        long_summary = "E" * 250
        exc = _make_retry_exc(long_summary)
        do_call = MagicMock(side_effect=[exc, ("ok", "comp")])
        messages = self._make_messages()
        original = copy.deepcopy(messages)
        kwargs = {"messages": copy.deepcopy(messages), "max_tokens": 4096}
        config = self._make_config()

        with caplog.at_level(logging.WARNING):
            _retry_with_validation(
                do_call,
                kwargs,
                config,
                tracker=None,
                original_messages=original,
                current_messages=messages,
                max_retries=1,
            )
        warning = caplog.text
        expected_hint = "retrying with fresh messages + error hint: " + "E" * 200
        assert expected_hint in warning
        # The 201st E must not leak into the logged hint.
        assert "E" * 201 not in warning

    def test_context_overflow_retry_resets_messages_to_original(self):
        """An overflow retry calls the wire with the original messages deep-copied.

        Pins that the retry passes ``original_messages`` (not None) through to
        the budget reducer: the retry conversation must be the caller's
        original, not the mutated kwargs copy.
        """
        exc = _context_overflow_error()
        do_call = MagicMock(side_effect=[exc, ("ok", "comp")])
        original = [{"role": "user", "content": "original prompt"}]
        kwargs = {"messages": [{"role": "user", "content": "grown prompt"}], "max_tokens": 4096}
        config = self._make_config()

        _retry_with_validation(
            do_call,
            kwargs,
            config,
            tracker=None,
            original_messages=original,
            current_messages=[{"role": "user", "content": "current prompt"}],
            max_retries=1,
        )

        # The retry call used the original messages, and as a deep copy:
        second_call_messages = do_call.call_args_list[1].args[0]["messages"]
        assert second_call_messages == [{"role": "user", "content": "original prompt"}]
        second_call_messages[0]["content"] = "mutated"
        assert original[0]["content"] == "original prompt"

    def test_validation_exhausted_incident_carries_message(self):
        exc = _make_retry_exc("persistent validation error")
        do_call = MagicMock(side_effect=exc)
        messages = self._make_messages()
        original = copy.deepcopy(messages)
        kwargs = {"messages": copy.deepcopy(messages), "max_tokens": 4096}
        config = self._make_config()
        tracker = TokenTracker()

        with pytest.raises(ValidationRetryExhausted):
            _retry_with_validation(
                do_call,
                kwargs,
                config,
                tracker=tracker,
                original_messages=original,
                current_messages=messages,
                max_retries=1,
            )
        incident = next(i for i in tracker.incidents if i["kind"] == "validation_exhausted")
        assert "Validation retries exhausted" in incident["detail"]

    def test_context_overflow_on_final_attempt_reraises(self):
        """Overflow on the last permitted attempt propagates the API error."""
        exc = _context_overflow_error()
        do_call = MagicMock(side_effect=exc)
        messages = self._make_messages()
        original = copy.deepcopy(messages)
        kwargs = {"messages": copy.deepcopy(messages), "max_tokens": 4096}
        config = self._make_config()

        with pytest.raises(openai.APIError):
            _retry_with_validation(
                do_call,
                kwargs,
                config,
                tracker=None,
                original_messages=original,
                current_messages=messages,
                max_retries=1,
            )
        assert do_call.call_count == 2

    def test_validation_exhausted_raises(self):
        exc = _make_retry_exc("persistent validation error")
        do_call = MagicMock(side_effect=exc)
        messages = self._make_messages()
        original = copy.deepcopy(messages)
        kwargs = {"messages": copy.deepcopy(messages), "max_tokens": 4096}
        config = self._make_config()
        tracker = TokenTracker()

        with pytest.raises(ValidationRetryExhausted):
            _retry_with_validation(
                do_call,
                kwargs,
                config,
                tracker=tracker,
                original_messages=original,
                current_messages=messages,
                max_retries=2,
            )
        # Should have attempted max_retries + 1 = 3 times
        assert do_call.call_count == 3
        assert any(i["kind"] == "validation_exhausted" for i in tracker.incidents)

    def test_validation_error_appends_failed_content(self):
        """When failed_attempt has completion with content, it is appended as
        an assistant message before the error hint."""
        msg_obj = SimpleNamespace(content="partial JSON output")
        choice = SimpleNamespace(message=msg_obj)
        completion = SimpleNamespace(choices=[choice])
        failed_attempt = SimpleNamespace(
            attempt_number=1,
            exception=ValueError("bad field"),
            completion=completion,
        )
        exc = _make_retry_exc("validation error", failed_attempts=[failed_attempt])
        do_call = MagicMock(side_effect=[exc, ("ok", "comp")])
        messages = self._make_messages()
        original = copy.deepcopy(messages)
        kwargs = {"messages": copy.deepcopy(messages), "max_tokens": 4096}
        config = self._make_config()

        result = _retry_with_validation(
            do_call,
            kwargs,
            config,
            tracker=None,
            original_messages=original,
            current_messages=messages,
            max_retries=1,
        )
        assert result == ("ok", "comp")
        retry_messages = kwargs["messages"]
        # Should contain the failed assistant content followed by the error hint
        assistant_msgs = [m for m in retry_messages if m["role"] == "assistant"]
        assert len(assistant_msgs) >= 1
        assert assistant_msgs[-1]["content"] == "partial JSON output"
        # Error hint should reference the exception from the failed attempt
        user_hints = [m for m in retry_messages if m["role"] == "user" and "Validation error:" in m["content"]]
        assert len(user_hints) == 1
        assert "bad field" in user_hints[0]["content"]


# ---------------------------------------------------------------------------
# _apply_budget
# ---------------------------------------------------------------------------


class TestApplyBudget:
    def test_sets_max_tokens_when_max_context_is_zero(self):
        from asago_policy_mapper.llm import _apply_budget

        config = LLMConfig(base_url="http://test", model="test-model", max_tokens=8192, max_context=0)
        kwargs: dict = {"messages": [{"role": "user", "content": "hello"}]}
        _apply_budget(kwargs, config)
        assert kwargs["max_tokens"] == 8192

    def test_does_not_override_explicit_max_tokens(self):
        from asago_policy_mapper.llm import _apply_budget

        config = LLMConfig(base_url="http://test", model="test-model", max_tokens=8192, max_context=0)
        kwargs: dict = {"messages": [{"role": "user", "content": "hello"}], "max_tokens": 256}
        _apply_budget(kwargs, config)
        assert kwargs["max_tokens"] == 256

    def test_uses_max_completion_tokens_when_configured(self):
        from asago_policy_mapper.llm import _apply_budget

        config = LLMConfig(
            base_url="http://test",
            model="test-model",
            max_tokens=8192,
            output_token_parameter="max_completion_tokens",
        )
        kwargs: dict = {"messages": [{"role": "user", "content": "hello"}]}
        _apply_budget(kwargs, config)
        assert kwargs["max_completion_tokens"] == 8192
        assert "max_tokens" not in kwargs

    def test_converts_explicit_legacy_parameter_when_configured(self):
        from asago_policy_mapper.llm import _apply_budget

        config = LLMConfig(
            base_url="http://test",
            model="test-model",
            max_tokens=8192,
            output_token_parameter="max_completion_tokens",
        )
        kwargs: dict = {"messages": [{"role": "user", "content": "hello"}], "max_tokens": 256}
        _apply_budget(kwargs, config)
        assert kwargs["max_completion_tokens"] == 256
        assert "max_tokens" not in kwargs

    def test_budgets_against_max_context(self):
        from asago_policy_mapper.llm import _apply_budget

        config = LLMConfig(base_url="http://test", model="test-model", max_tokens=8192, max_context=2048)
        kwargs: dict = {"messages": [{"role": "user", "content": "hello"}]}
        _apply_budget(kwargs, config)
        assert kwargs["max_tokens"] < 8192
        assert kwargs["max_tokens"] >= 256

    def test_rejects_unknown_output_token_parameter(self):
        with pytest.raises(ValueError, match="output_token_parameter"):
            LLMConfig(base_url="http://test", model="test-model", output_token_parameter="tokens")

    @pytest.mark.parametrize("service_tier", ["default", "flex", "fast", "priority", "vendor-specific"])
    def test_accepts_arbitrary_service_tiers(self, service_tier):
        config = LLMConfig(base_url="http://test", model="test-model", service_tier=service_tier)
        assert config.service_tier == service_tier

    def test_empty_service_tier_is_omitted(self):
        config = LLMConfig(base_url="http://test", model="test-model", service_tier=" ")
        assert config.service_tier is None

    def test_service_tier_is_added_to_chat_completion_request(self):
        client = MagicMock()
        completion = SimpleNamespace(usage=SimpleNamespace(prompt_tokens=1, completion_tokens=1, total_tokens=2))
        client.create_with_completion.return_value = ("parsed", completion)
        config = LLMConfig(base_url="http://test", model="test-model", service_tier="flex")

        _wrap_with_tracking(client, TokenTracker(), config)
        result = client.chat.completions.create(messages=[{"role": "user", "content": "hello"}])

        assert result == "parsed"
        assert client.create_with_completion.call_args.kwargs["service_tier"] == "flex"

    def test_service_tier_is_omitted_when_not_configured(self):
        client = MagicMock()
        completion = SimpleNamespace(usage=SimpleNamespace(prompt_tokens=1, completion_tokens=1, total_tokens=2))
        client.create_with_completion.return_value = ("parsed", completion)
        config = LLMConfig(base_url="http://test", model="test-model")

        _wrap_with_tracking(client, TokenTracker(), config)
        client.chat.completions.create(messages=[{"role": "user", "content": "hello"}])

        assert "service_tier" not in client.create_with_completion.call_args.kwargs


# ---------------------------------------------------------------------------
# _StructuredClient over a stubbed transport (production stack)
# ---------------------------------------------------------------------------


class _StructuredAnswer(SlimModel):
    answer: str


def _stubbed_client(handler, max_retries):
    """Build the full production stack (create_client -> tracking wrapper) over a stubbed transport."""
    config = LLMConfig(base_url="http://localhost:8000/v1", model="test-model", max_retries=max_retries)
    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    with patch(
        "asago_policy_mapper.llm.OpenAI",
        lambda **kw: openai.OpenAI(http_client=http_client, max_retries=0, **kw),
    ):
        return create_client(config)


def _completion_body(content):
    return {
        "id": "chatcmpl-1",
        "object": "chat.completion",
        "created": 0,
        "model": "test-model",
        "choices": [{"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": content}}],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
    }


class TestStructuredClientRetries:
    def test_retries_come_from_the_outer_loop_with_a_warning_each(self, caplog):
        """create_with_completion is a single attempt; the tracking wrapper retries.

        With max_retries=3 and an endpoint that always returns invalid JSON,
        exactly 4 calls hit the wire, each retry starts from a fresh copy of
        the input messages carrying one failed-answer/error-hint pair, and a
        WARNING fires per retry (attempt 1/4..3/4) but not for the terminal
        failure.
        """
        requests = []

        def handler(request):
            requests.append(json.loads(request.read()))
            return httpx.Response(200, json=_completion_body('{"items": "not a list"}'))

        client = _stubbed_client(handler, max_retries=3)
        input_messages = [{"role": "user", "content": "hello"}]

        with caplog.at_level(logging.WARNING, logger="asago_policy_mapper.llm"):
            with pytest.raises(ValidationRetryExhausted) as excinfo:
                client.chat.completions.create(
                    model="test-model",
                    response_model=_StructuredAnswer,
                    messages=input_messages,
                    max_tokens=256,
                )

        assert len(requests) == 4
        # First call: the input messages untouched.
        assert requests[0]["messages"] == input_messages
        # Each retry: a fresh copy of the input with exactly one failed-answer
        # message followed by one error-hint user message.
        for body in requests[1:]:
            retry_messages = body["messages"]
            assert retry_messages[:1] == input_messages
            assistants = [m for m in retry_messages if m["role"] == "assistant"]
            hints = [m for m in retry_messages if m["role"] == "user" and "Validation error:" in m["content"]]
            assert len(assistants) == 1
            assert len(hints) == 1
        # The terminal exception carries the single failed attempt, numbered 1.
        assert len(excinfo.value.failed_attempts) == 1
        assert excinfo.value.failed_attempts[0].attempt_number == 1
        # One WARNING per retry (3 of them), none for the terminal failure.
        warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert len(warnings) == 3
        assert all("Structured output validation failed" in r.getMessage() for r in warnings)
        assert [w.args[0] for w in warnings] == [1, 2, 3]
        assert [w.args[1] for w in warnings] == [4, 4, 4]

    def test_recovery_after_one_failed_attempt(self, caplog):
        requests = []

        def handler(request):
            requests.append(json.loads(request.read()))
            content = '{"items": "not a list"}' if len(requests) == 1 else '{"answer": "ok"}'
            return httpx.Response(200, json=_completion_body(content))

        client = _stubbed_client(handler, max_retries=2)

        with caplog.at_level(logging.WARNING, logger="asago_policy_mapper.llm"):
            result = client.chat.completions.create(
                model="test-model",
                response_model=_StructuredAnswer,
                messages=[{"role": "user", "content": "hello"}],
                max_tokens=256,
            )

        assert result.answer == "ok"
        assert len(requests) == 2
        warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert len(warnings) == 1
        assert "Structured output validation failed (attempt 1/3)" in warnings[0].getMessage()

    def test_direct_create_with_completion_is_a_single_attempt(self):
        """Direct calls (health-probe style) make one attempt regardless of max_retries."""
        requests = []

        def handler(request):
            requests.append(json.loads(request.read()))
            return httpx.Response(200, json=_completion_body('{"items": "not a list"}'))

        api = openai.OpenAI(
            base_url="http://localhost:8000/v1",
            api_key="none",
            http_client=httpx.Client(transport=httpx.MockTransport(handler)),
            max_retries=0,
        )
        client = _StructuredClient(api, mode=StructuredOutputMode.JSON_SCHEMA)

        with pytest.raises(ValidationRetryExhausted) as excinfo:
            client.chat.completions.create(
                model="test-model",
                response_model=_StructuredAnswer,
                messages=[{"role": "user", "content": "hello"}],
                max_tokens=256,
                max_retries=3,
            )

        assert len(requests) == 1
        # The kwarg never reaches the SDK's create().
        assert "max_retries" not in requests[0]
        assert len(excinfo.value.failed_attempts) == 1
        assert excinfo.value.failed_attempts[0].attempt_number == 1
        assert isinstance(excinfo.value.__cause__, ValidationError)


class TestLengthTruncationRouting:
    """A length-truncated completion takes the truncation path, not validation retries."""

    def _length_response(self):
        return {
            "id": "chatcmpl-1",
            "object": "chat.completion",
            "created": 0,
            "model": "test-model",
            # vLLM-shaped truncation: no content at all when the token limit hits.
            "choices": [{"index": 0, "finish_reason": "length", "message": {"role": "assistant", "content": None}}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        }

    def test_null_content_with_length_takes_truncation_path(self, caplog):
        """content=null + finish_reason=length is a truncation problem, not a parse one.

        The prompt is truncatable (a long user message), so the wrapper
        retries with a shorter prompt instead of resending the same messages
        with a validation error hint.
        """
        requests = []

        def handler(request):
            requests.append(json.loads(request.read()))
            return httpx.Response(200, json=self._length_response())

        client = _stubbed_client(handler, max_retries=3)
        long_message = [{"role": "user", "content": "x" * 2000}]

        with caplog.at_level(logging.WARNING, logger="asago_policy_mapper.llm"):
            with pytest.raises(IncompleteOutputException):
                client.chat.completions.create(
                    model="test-model",
                    response_model=_StructuredAnswer,
                    messages=long_message,
                    max_tokens=256,
                )

        # Retries shorten the prompt (truncation path), they do not append
        # validation error hints (validation path).
        first_len = len(requests[0]["messages"][0]["content"])
        assert first_len == 2000
        for body in requests[1:]:
            hints = [m for m in body["messages"] if m.get("role") == "user" and "Validation error:" in m["content"]]
            assert not hints
            assert len(body["messages"][0]["content"]) < first_len
        # The truncation budget allows _MAX_TRUNCATION_RETRIES + 1 calls; with
        # max_retries=3 the validation budget would also allow 4, so the count
        # alone does not distinguish the paths — the shorter prompts and the
        # absent validation hints above do.
        assert len(requests) == _MAX_TRUNCATION_RETRIES + 1
        # No validation-retry warnings fire on this path.
        assert not [r for r in caplog.records if "Structured output validation failed" in r.getMessage()]

    def test_null_content_with_length_and_short_prompt_raises_incomplete(self):
        """Without room to shorten, the truncation path raises IncompleteOutputException directly."""

        def handler(request):
            return httpx.Response(200, json=self._length_response())

        client = _stubbed_client(handler, max_retries=3)

        with pytest.raises(IncompleteOutputException):
            client.chat.completions.create(
                model="test-model",
                response_model=_StructuredAnswer,
                messages=[{"role": "user", "content": "short"}],
                max_tokens=256,
            )

    def test_truncation_budget_exhaustion_raises_incomplete_output(self):
        """A long prompt that stays shortenable past the retry budget raises the endpoint condition.

        A 5000-char message shortens 5000 -> 3000 -> 1800 -> 1080 across the
        truncation attempts; the budget runs out while the message is still
        above the floor. The caller must see the IncompleteOutputException,
        not an internal RuntimeError.
        """
        requests = []

        def handler(request):
            requests.append(json.loads(request.read()))
            return httpx.Response(200, json=self._length_response())

        client = _stubbed_client(handler, max_retries=3)

        with pytest.raises(IncompleteOutputException):
            client.chat.completions.create(
                model="test-model",
                response_model=_StructuredAnswer,
                messages=[{"role": "user", "content": "x" * 5000}],
                max_tokens=256,
            )

        assert len(requests) == _MAX_TRUNCATION_RETRIES + 1
        assert [len(body["messages"][0]["content"]) for body in requests] == [5000, 3000, 1800, 1080]

    def test_parse_completion_checks_length_before_missing_content(self):
        """_parse_completion raises IncompleteOutputException for null content + length."""
        msg = SimpleNamespace(content=None)
        choice = SimpleNamespace(message=msg, finish_reason="length")
        completion = SimpleNamespace(choices=[choice])

        with pytest.raises(IncompleteOutputException):
            _parse_completion(completion, _StructuredAnswer)


class TestStructuredClientResponseFormat:
    def _capture(self, mode):
        bodies = []

        def handler(request):
            bodies.append(json.loads(request.read()))
            return httpx.Response(200, json=_completion_body('{"answer": "ok"}'))

        config = LLMConfig(base_url="http://localhost:8000/v1", model="test-model", max_context=0)
        http_client = httpx.Client(transport=httpx.MockTransport(handler))
        with patch(
            "asago_policy_mapper.llm.OpenAI",
            lambda **kw: openai.OpenAI(http_client=http_client, max_retries=0, **kw),
        ):
            client = create_client(config, mode=mode)
            client.chat.completions.create(
                model="test-model",
                response_model=_StructuredAnswer,
                messages=[{"role": "system", "content": "SYSTEM"}, {"role": "user", "content": "hello"}],
                max_tokens=256,
            )
        return bodies[0]

    def test_json_schema_mode_sends_native_schema_without_strict(self):
        body = self._capture(StructuredOutputMode.JSON_SCHEMA)
        assert body["response_format"] == {
            "type": "json_schema",
            "json_schema": {"name": "_StructuredAnswer", "schema": _StructuredAnswer.model_json_schema()},
        }
        # The wire payload never mentions strict in any form.
        assert "strict" not in json.dumps(body["response_format"])

    def test_json_schema_with_prompt_mode_appends_schema_block(self):
        body = self._capture(StructuredOutputMode.JSON_SCHEMA_WITH_PROMPT)
        assert body["response_format"]["type"] == "json_schema"
        assert body["response_format"]["json_schema"]["name"] == "_StructuredAnswer"
        assert "As a genius expert" in body["messages"][0]["content"]
        assert body["messages"][0]["content"].startswith("SYSTEM")

    def test_json_mode_sends_json_object_with_schema_in_prompt(self):
        body = self._capture(StructuredOutputMode.JSON)
        assert body["response_format"] == {"type": "json_object"}
        assert "matches this JSON schema exactly" in body["messages"][0]["content"]
        assert body["messages"][0]["content"].startswith("SYSTEM")
