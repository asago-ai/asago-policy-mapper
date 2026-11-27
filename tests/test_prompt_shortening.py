"""Tests for prompt-shortening records: what a shortening left on the call.

A shortening made after an incomplete output must be visible afterwards:
the tracked create call attaches it to its own result, the pipeline's
record helpers copy it onto the ``LLMCallRecord``, and the output-truncation
incidents carry the character counts. One worker's diagnostics must never
leak into another's call.
"""

import copy
import hashlib
import json
import logging
import threading
from unittest.mock import MagicMock, patch

import httpx
import openai
import pytest

from asago_policy_mapper.extract.attribute import (
    ground_and_extract_evidence,
    ground_risk_group,
    ground_variants,
    synthesize_causal_chain,
)
from asago_policy_mapper.extract.models import (
    LLMCallRecord,
    ScoredCandidate,
    _JudgeVerdicts,
    _RiskEvidence,
    _RiskEvidenceList,
)
from asago_policy_mapper.extract.parse import Chunk
from asago_policy_mapper.extract.querygen import generate_queries, group_chunks
from asago_policy_mapper.extract.retrieve import judge_borderline
from asago_policy_mapper.llm import (
    _MAX_TRUNCATION_RETRIES,
    IncompleteOutputException,
    LLMConfig,
    SlimModel,
    TokenTracker,
    _shortenings_of,
    create_client,
)


class _StructuredAnswer(SlimModel):
    answer: str


def test_longest_user_message_chars_contract():
    """The longest user message wins; no user message means 0, not an error."""
    from asago_policy_mapper.llm import _longest_user_message_chars

    assert (
        _longest_user_message_chars([{"role": "user", "content": "a" * 30}, {"role": "user", "content": "b" * 70}])
        == 70
    )
    assert _longest_user_message_chars([{"role": "system", "content": "s" * 90}]) == 0
    assert _longest_user_message_chars([]) == 0
    # A message dict without content counts as an empty string.
    assert _longest_user_message_chars([{"role": "user"}]) == 0


def _length_truncated_body():
    return {
        "id": "chatcmpl-1",
        "object": "chat.completion",
        "created": 0,
        "model": "test-model",
        "choices": [{"index": 0, "finish_reason": "length", "message": {"role": "assistant", "content": None}}],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
    }


def _completion_body(content):
    return {
        "id": "chatcmpl-1",
        "object": "chat.completion",
        "created": 0,
        "model": "test-model",
        "choices": [{"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": content}}],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
    }


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _shortening_stub_client(response_body: str):
    """Build the production client over a transport that shortens once.

    The first response stops at the token limit, so the tracked call
    shortens the longest user message and retries; the second returns
    ``response_body`` and the call succeeds. A site's user prompt must
    exceed the 500-char shortening floor for the shortening to happen.
    """
    state = {"shortened": False}

    def handler(request):
        if not state["shortened"]:
            state["shortened"] = True
            return httpx.Response(200, json=_length_truncated_body())
        return httpx.Response(200, json=_completion_body(response_body))

    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    with patch(
        "asago_policy_mapper.llm.OpenAI",
        lambda **kw: openai.OpenAI(http_client=http_client, **kw),
    ):
        return create_client(LLMConfig(base_url="http://localhost:8000/v1", model="test-model", sdk_max_retries=0))


class TestShorteningRecord:
    def test_shortening_recorded_on_call_record(self):
        """A shortening the tracked create call makes lands on the record helpers' output.

        The full production stack shortens a 2000-char prompt after a
        truncated answer; the judge record helper copies the shortening onto
        its LLMCallRecord with attempt, index, sizes, hashes and reason.
        """
        requests = []

        def handler(request):
            requests.append(json.loads(request.read()))
            if len(requests) == 1:
                return httpx.Response(200, json=_length_truncated_body())
            return httpx.Response(200, json=_completion_body('{"items": []}'))

        config = LLMConfig(base_url="http://localhost:8000/v1", model="test-model", sdk_max_retries=0)
        http_client = httpx.Client(transport=httpx.MockTransport(handler))
        with patch(
            "asago_policy_mapper.llm.OpenAI",
            lambda **kw: openai.OpenAI(http_client=http_client, **kw),
        ):
            client = create_client(config)

        response = client.chat.completions.create(
            model="test-model",
            response_model=_JudgeVerdicts,
            messages=[{"role": "user", "content": "J" * 2000}],
            max_tokens=256,
        )
        assert response.items == []

        shortenings = _shortenings_of(response)
        assert len(shortenings) == 1
        s = shortenings[0]
        assert s["attempt"] == 1
        assert s["message_index"] == 0
        assert s["chars_before"] == 2000
        assert s["chars_after"] == 1200
        assert s["sha256_before"] == _sha("J" * 2000)
        assert s["sha256_after"] == _sha("J" * 1200)
        assert s["reason"] == "incomplete_output"

    def test_shortening_stays_on_its_own_call(self):
        """Each call's result carries exactly its own shortenings.

        A shortening from one call must not appear in the next call's
        result even when that next call shortens nothing.
        """
        requests = []

        def handler(request):
            requests.append(json.loads(request.read()))
            if len(requests) == 1:
                return httpx.Response(200, json=_length_truncated_body())
            return httpx.Response(200, json=_completion_body('{"answer": "ok"}'))

        config = LLMConfig(base_url="http://localhost:8000/v1", model="test-model", sdk_max_retries=0)
        http_client = httpx.Client(transport=httpx.MockTransport(handler))
        with patch(
            "asago_policy_mapper.llm.OpenAI",
            lambda **kw: openai.OpenAI(http_client=http_client, **kw),
        ):
            client = create_client(config)

        shortened = client.chat.completions.create(
            model="test-model",
            response_model=_StructuredAnswer,
            messages=[{"role": "user", "content": "S" * 2000}],
            max_tokens=256,
        )
        assert len(_shortenings_of(shortened)) == 1

        plain = client.chat.completions.create(
            model="test-model",
            response_model=_StructuredAnswer,
            messages=[{"role": "user", "content": "short"}],
            max_tokens=256,
        )
        assert _shortenings_of(plain) == []

    def test_shortening_indexes_and_attempts_across_messages(self):
        """A system message shifts message_index; each retry bumps attempt.

        With a system prompt in front, the shortened user message is index 1.
        Three truncated answers shorten three times in one call; the recorded
        attempts must be 1, 2, 3 and every message_index must be 1.
        """
        requests = []

        def handler(request):
            requests.append(json.loads(request.read()))
            if len(requests) <= 3:
                return httpx.Response(200, json=_length_truncated_body())
            return httpx.Response(200, json=_completion_body('{"answer": "ok"}'))

        config = LLMConfig(base_url="http://localhost:8000/v1", model="test-model", sdk_max_retries=0)
        http_client = httpx.Client(transport=httpx.MockTransport(handler))
        with patch(
            "asago_policy_mapper.llm.OpenAI",
            lambda **kw: openai.OpenAI(http_client=http_client, **kw),
        ):
            client = create_client(config)

        result = client.chat.completions.create(
            model="test-model",
            response_model=_StructuredAnswer,
            messages=[
                {"role": "system", "content": "You extract risks."},
                {"role": "user", "content": "B" * 5000},
            ],
            max_tokens=256,
        )

        assert result.answer == "ok"
        assert len(requests) == 4
        shortenings = _shortenings_of(result)
        assert [s["attempt"] for s in shortenings] == [1, 2, 3]
        assert [s["message_index"] for s in shortenings] == [1, 1, 1]
        assert [s["chars_before"] for s in shortenings] == [5000, 3000, 1800]
        assert [s["chars_after"] for s in shortenings] == [3000, 1800, 1080]
        assert all(s["reason"] == "incomplete_output" for s in shortenings)

    def test_last_exhausted_attempt_sends_no_further_request(self):
        """The exhausted final attempt records no request beyond the budget.

        With the truncation budget spent, the incident and exception report
        the endpoint condition; the recorded request count must equal
        _MAX_TRUNCATION_RETRIES + 1, not one more.
        """
        requests = []

        def handler(request):
            requests.append(json.loads(request.read()))
            return httpx.Response(200, json=_length_truncated_body())

        config = LLMConfig(base_url="http://localhost:8000/v1", model="test-model", sdk_max_retries=0)
        http_client = httpx.Client(transport=httpx.MockTransport(handler))
        with patch(
            "asago_policy_mapper.llm.OpenAI",
            lambda **kw: openai.OpenAI(http_client=http_client, **kw),
        ):
            client = create_client(config)

        with pytest.raises(IncompleteOutputException):
            client.chat.completions.create(
                model="test-model",
                response_model=_StructuredAnswer,
                messages=[{"role": "user", "content": "x" * 5000}],
                max_tokens=256,
            )

        assert len(requests) == _MAX_TRUNCATION_RETRIES + 1

    def test_retry_diagnostics_are_isolated_between_workers(self):
        """Parallel workers' shortenings stay on their own calls' results.

        Worker A shortens (2000 -> 1200) and succeeds; worker B runs a plain
        short call concurrently. Both barrier after their calls; B's result
        must carry no shortening and A's must hold exactly A's shortening.
        """
        barrier = threading.Barrier(2)
        seen: dict[str, list] = {}

        def handler_a(request):
            body = json.loads(request.read())
            if len(body["messages"][0]["content"]) == 2000:
                return httpx.Response(200, json=_length_truncated_body())
            return httpx.Response(200, json=_completion_body('{"answer": "a"}'))

        def handler_b(request):
            return httpx.Response(200, json=_completion_body('{"answer": "b"}'))

        clients = {}
        for name, handler in (("a", handler_a), ("b", handler_b)):
            http_client = httpx.Client(transport=httpx.MockTransport(handler))
            with patch(
                "asago_policy_mapper.llm.OpenAI",
                lambda **kw: openai.OpenAI(http_client=http_client, **kw),
            ):
                clients[name] = create_client(
                    LLMConfig(base_url="http://localhost:8000/v1", model="test-model", sdk_max_retries=0)
                )

        def worker(name: str, content: str) -> None:
            result = clients[name].chat.completions.create(
                model="test-model",
                response_model=_StructuredAnswer,
                messages=[{"role": "user", "content": content}],
                max_tokens=256,
            )
            barrier.wait()
            seen[name] = copy.deepcopy(_shortenings_of(result))

        threads = [
            threading.Thread(target=worker, args=("a", "A" * 2000)),
            threading.Thread(target=worker, args=("b", "short")),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(seen["a"]) == 1
        assert seen["a"][0]["chars_before"] == 2000
        assert seen["b"] == []


class TestRecordHelpersCopyShortenings:
    def test_judge_record_carries_shortenings(self):
        """judge_borderline's LLMCallRecord copies the calling thread's shortenings."""
        requests = []

        def handler(request):
            requests.append(json.loads(request.read()))
            if len(requests) == 1:
                return httpx.Response(200, json=_length_truncated_body())
            return httpx.Response(200, json=_completion_body('{"items": []}'))

        http_client = httpx.Client(transport=httpx.MockTransport(handler))
        with patch(
            "asago_policy_mapper.llm.OpenAI",
            lambda **kw: openai.OpenAI(http_client=http_client, **kw),
        ):
            client = create_client(
                LLMConfig(base_url="http://localhost:8000/v1", model="test-model", sdk_max_retries=0)
            )

        candidates = [
            ScoredCandidate(
                risk_id="R-001",
                risk_name="Bias",
                risk_description="Model bias risk " * 40,
                cross_encoder_score=0.5,
            ),
        ]
        collector: list[LLMCallRecord] = []
        # A long chunk so the rendered prompt's user message is truncatable.
        chunk_text = "AI systems must avoid bias. " * 120

        accepted = judge_borderline(
            candidates,
            chunk_text=chunk_text,
            client=client,
            model="test-model",
            records=collector,
        )

        assert accepted == []
        assert len(collector) == 1
        shortenings = collector[0].prompt_shortenings
        # The first response was truncated and the prompt was shortenable,
        # so exactly one shortening must be recorded with the sizes.
        assert len(shortenings) == 1
        before, after = shortenings[0]["chars_before"], shortenings[0]["chars_after"]
        assert after < before
        assert shortenings[0]["reason"] == "incomplete_output"

    def test_grounding_record_defaults_to_empty_shortenings(self):
        """Without a shortening, the grounding record carries an empty list, not None."""
        client = MagicMock()
        client.chat.completions.create.return_value = _RiskEvidenceList(
            items=[_RiskEvidence(risk_id="R-001", grounded=True, confidence="high", quotes=["text"])]
        )
        candidates = [
            ScoredCandidate(
                risk_id="R-001",
                risk_name="Bias",
                risk_description="Model bias risk",
                cross_encoder_score=0.9,
            ),
        ]
        collector: list[LLMCallRecord] = []
        ground_and_extract_evidence(
            chunk_text="AI systems must avoid bias.",
            candidates=candidates,
            client=client,
            model="test-model",
            document="policy.pdf",
            chunk_index=0,
            records=collector,
        )
        assert len(collector) == 1
        assert collector[0].prompt_shortenings == []

    def test_querygen_record_carries_shortenings(self):
        """generate_queries' inline LLMCallRecord copies the calling thread's shortenings."""
        client = _shortening_stub_client('{"queries": []}')

        chunks = [Chunk(text="Query generation source text. " * 40, source="doc.pdf", index=0, section=None)]
        collector: list[LLMCallRecord] = []
        generate_queries(
            chunks,
            group_chunks(chunks),
            client,
            "test-model",
            records=collector,
        )

        assert len(collector) == 1
        shortenings = collector[0].prompt_shortenings
        assert len(shortenings) == 1
        assert shortenings[0]["chars_before"] > shortenings[0]["chars_after"]
        assert shortenings[0]["reason"] == "incomplete_output"

    def test_grounding_record_carries_shortenings(self):
        """_record_grounding_call's LLMCallRecord copies the calling thread's shortenings."""
        client = _shortening_stub_client('{"items": []}')

        candidates = [
            ScoredCandidate(
                risk_id="R-001",
                risk_name="Bias",
                risk_description="Model bias risk",
                cross_encoder_score=0.5,
            ),
        ]
        collector: list[LLMCallRecord] = []
        ground_and_extract_evidence(
            chunk_text="AI systems must avoid bias. " * 60,
            candidates=candidates,
            client=client,
            model="test-model",
            document="policy.pdf",
            chunk_index=0,
            records=collector,
        )

        assert len(collector) == 1
        shortenings = collector[0].prompt_shortenings
        assert len(shortenings) == 1
        assert shortenings[0]["chars_before"] > shortenings[0]["chars_after"]
        assert shortenings[0]["reason"] == "incomplete_output"

    def test_variant_grounding_record_carries_shortenings(self):
        """ground_variants' LLMCallRecord copies the calling thread's shortenings."""
        client = _shortening_stub_client('{"items": []}')

        variants = [
            {
                "risk_id": "parent---variant-a",
                "name": "Variant A",
                "description": "Unauthorized processing of biometric data.",
            }
        ]
        collector: list[LLMCallRecord] = []
        ground_variants(
            chunk_text="Facial recognition data was collected without consent. " * 40,
            parent_id="parent",
            parent_name="Unauthorized processing",
            parent_description="Processing of personal data without legal basis or consent.",
            variants=variants,
            client=client,
            model="test-model",
            document="policy.pdf",
            chunk_index=0,
            records=collector,
        )

        assert len(collector) == 1
        shortenings = collector[0].prompt_shortenings
        assert len(shortenings) == 1
        assert shortenings[0]["chars_before"] > shortenings[0]["chars_after"]
        assert shortenings[0]["reason"] == "incomplete_output"

    def test_group_grounding_record_carries_shortenings(self):
        """_record_group_call's LLMCallRecord copies the calling thread's shortenings."""
        client = _shortening_stub_client('{"items": []}')

        chunks = [Chunk(text="Location data processing without awareness. " * 40, source="doc.pdf", index=0)]
        risks = [{"risk_id": "R-001", "risk_name": "Bias", "risk_description": "Model bias risk"}]
        collector: list[LLMCallRecord] = []
        ground_risk_group(
            chunks,
            chunk_indices=[0],
            risks=risks,
            client=client,
            model="test-model",
            document="policy.pdf",
            records=collector,
        )

        assert len(collector) == 1
        shortenings = collector[0].prompt_shortenings
        assert len(shortenings) == 1
        assert shortenings[0]["chars_before"] > shortenings[0]["chars_after"]
        assert shortenings[0]["reason"] == "incomplete_output"

    def test_causal_record_carries_shortenings(self):
        """synthesize_causal_chain's LLMCallRecord copies the calling thread's shortenings."""
        from test_extract_attribute import _make_risk_match

        requests = []

        def handler(request):
            requests.append(json.loads(request.read()))
            if len(requests) == 1:
                return httpx.Response(200, json=_length_truncated_body())
            return httpx.Response(
                200,
                json=_completion_body(
                    '{"items": [{"threat": "t", "threat_source": "ts", '
                    '"vulnerability": "v", "consequence": "c", "impact": "i"}]}'
                ),
            )

        http_client = httpx.Client(transport=httpx.MockTransport(handler))
        with patch(
            "asago_policy_mapper.llm.OpenAI",
            lambda **kw: openai.OpenAI(http_client=http_client, **kw),
        ):
            client = create_client(
                LLMConfig(base_url="http://localhost:8000/v1", model="test-model", sdk_max_retries=0)
            )

        collector: list[LLMCallRecord] = []
        chain = synthesize_causal_chain(
            risk_match=_make_risk_match(),
            chunk_texts={0: "Long evidence text. " * 150, 2: "More text."},
            client=client,
            model="test-model",
            records=collector,
        )

        assert chain is not None
        assert len(collector) == 1
        shortenings = collector[0].prompt_shortenings
        assert len(shortenings) == 1
        assert shortenings[0]["chars_before"] > shortenings[0]["chars_after"]
        assert shortenings[0]["reason"] == "incomplete_output"

    def test_causal_record_carries_shortenings_from_the_exception(self):
        """A failed causal call's partial shortenings reach its record.

        The call shortens twice and then dies with a validation exhaustion;
        synthesize_causal_chain downgrades to an empty result and records,
        and the record must carry the partials the failed call made — read
        from the escaped exception, not from state the call left behind.
        """
        from test_extract_attribute import _make_risk_match

        requests = []

        def handler(request):
            requests.append(json.loads(request.read()))
            if len(requests) <= 2:
                return httpx.Response(200, json=_length_truncated_body())
            # Invalid JSON three times: the validation budget exhausts.
            return httpx.Response(200, json=_completion_body("not json at all"))

        http_client = httpx.Client(transport=httpx.MockTransport(handler))
        with patch(
            "asago_policy_mapper.llm.OpenAI",
            lambda **kw: openai.OpenAI(http_client=http_client, **kw),
        ):
            client = create_client(
                LLMConfig(base_url="http://localhost:8000/v1", model="test-model", max_retries=2, sdk_max_retries=0)
            )

        collector: list[LLMCallRecord] = []
        chain = synthesize_causal_chain(
            risk_match=_make_risk_match(),
            chunk_texts={0: "Long evidence text. " * 150, 2: "More text."},
            client=client,
            model="test-model",
            records=collector,
        )

        assert chain is None
        assert len(collector) == 1
        assert collector[0].result_summary == "retry_exhausted"
        shortenings = collector[0].prompt_shortenings
        assert len(shortenings) == 2
        assert [s["attempt"] for s in shortenings] == [1, 2]
        assert shortenings[0]["chars_before"] > shortenings[0]["chars_after"]
        assert shortenings[0]["reason"] == "incomplete_output"


class TestIncidentsCarryCharCounts:
    def test_output_truncated_incidents_carry_char_counts(self, caplog):
        """Every output_truncated incident names the before/after character counts."""
        requests = []

        def handler(request):
            requests.append(json.loads(request.read()))
            return httpx.Response(200, json=_length_truncated_body())

        tracker = TokenTracker()
        config = LLMConfig(base_url="http://localhost:8000/v1", model="test-model", sdk_max_retries=0)
        http_client = httpx.Client(transport=httpx.MockTransport(handler))
        with patch(
            "asago_policy_mapper.llm.OpenAI",
            lambda **kw: openai.OpenAI(http_client=http_client, **kw),
        ):
            client = create_client(config, tracker=tracker)

        with caplog.at_level(logging.INFO, logger="asago_policy_mapper.llm"):
            with pytest.raises(IncompleteOutputException):
                client.chat.completions.create(
                    model="test-model",
                    response_model=_StructuredAnswer,
                    messages=[{"role": "user", "content": "x" * 5000}],
                    max_tokens=256,
                )

        truncated = [i for i in tracker.incidents if i["kind"] == "output_truncated"]
        assert len(truncated) == _MAX_TRUNCATION_RETRIES + 1
        # Each retry names the counts of the shortening it made, numbered by
        # attempt out of the full budget — in the incident and the log alike.
        infos = [r.getMessage() for r in caplog.records if r.levelno == logging.INFO]
        for attempt_no, incident in enumerate(truncated[:-1], start=1):
            assert incident["chars_before"] > incident["chars_after"]
            expected = (
                f"Output truncated (attempt {attempt_no}/{_MAX_TRUNCATION_RETRIES}), "
                f"retrying with shorter prompt "
                f"({incident['chars_before']} -> {incident['chars_after']} chars)"
            )
            assert incident["detail"] == expected
            assert expected in infos
        # The exhausted incident reports the longest user message's final
        # size (1080 chars after 5000 -> 3000 -> 1800 -> 1080) and, unlike
        # the retries above, does not claim a further request: no
        # "retrying" in its detail.
        final = truncated[-1]
        assert final["chars_before"] == 1080
        assert (
            f"Output truncated after {_MAX_TRUNCATION_RETRIES + 1} attempts; the truncation retry budget is "
            "exhausted with the longest user message at 1080 chars" == final["detail"]
        )
        assert "retrying" not in final["detail"]
        assert len(requests) == _MAX_TRUNCATION_RETRIES + 1

    def test_exhausted_incident_reports_longest_user_message(self):
        """The terminal incident counts the long user message, not the last message.

        A short trailing user message must not mask the size of the long one
        that the truncation budget ran out on.
        """
        requests = []

        def handler(request):
            requests.append(json.loads(request.read()))
            return httpx.Response(200, json=_length_truncated_body())

        tracker = TokenTracker()
        config = LLMConfig(base_url="http://localhost:8000/v1", model="test-model", sdk_max_retries=0)
        http_client = httpx.Client(transport=httpx.MockTransport(handler))
        with patch(
            "asago_policy_mapper.llm.OpenAI",
            lambda **kw: openai.OpenAI(http_client=http_client, **kw),
        ):
            client = create_client(config, tracker=tracker)

        with pytest.raises(IncompleteOutputException):
            client.chat.completions.create(
                model="test-model",
                response_model=_StructuredAnswer,
                messages=[
                    {"role": "system", "content": "sys"},
                    {"role": "user", "content": "L" * 5000},
                    {"role": "user", "content": "tail"},
                ],
                max_tokens=256,
            )

        truncated = [i for i in tracker.incidents if i["kind"] == "output_truncated"]
        final = truncated[-1]
        assert final["chars_before"] == 1080
        assert "1080 chars" in final["detail"]
        # The short trailing message is 4 chars; the incident must not
        # report its length.
        assert "4 chars" not in final["detail"]

    def test_unshortenable_incident_carries_counts(self):
        """A prompt below the shortening floor reports its size in counts too.

        A short user message cannot be shortened (the 500-char floor), so the
        single incident must carry its character count, not just prose.
        """
        tracker = TokenTracker()
        config = LLMConfig(base_url="http://localhost:8000/v1", model="test-model", sdk_max_retries=0)

        def handler(request):
            return httpx.Response(200, json=_length_truncated_body())

        http_client = httpx.Client(transport=httpx.MockTransport(handler))
        with patch(
            "asago_policy_mapper.llm.OpenAI",
            lambda **kw: openai.OpenAI(http_client=http_client, **kw),
        ):
            client = create_client(config, tracker=tracker)

        with pytest.raises(IncompleteOutputException):
            client.chat.completions.create(
                model="test-model",
                response_model=_StructuredAnswer,
                messages=[{"role": "user", "content": "u" * 300}],
                max_tokens=256,
            )

        (incident,) = [i for i in tracker.incidents if i["kind"] == "output_truncated"]
        assert incident["chars_before"] == 300
        assert "longest user message: 300 chars" in incident["detail"]


class TestRecordFieldShape:
    def test_llm_call_record_prompt_shortenings_default(self):
        record = LLMCallRecord(
            call_id="judge-001",
            stage="judge",
            chunk_index=0,
            risk_ids=[],
            messages=[],
            response={},
            duration_ms=0.0,
            result_summary="",
        )
        assert record.prompt_shortenings == []
        d = record.model_dump()
        assert d["prompt_shortenings"] == []
