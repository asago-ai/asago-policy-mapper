"""Tests for the stage-scoped client view in llm.py.

Stage workers run in parallel. A worker makes its calls through
``client.for_stage(name)``, and the returned view routes the stage
explicitly into usage tracking and incident recording, so one worker's
stage never lands in another's totals.
"""

import contextlib
import threading
from types import SimpleNamespace
from unittest.mock import MagicMock

import openai
import pytest
from llm_errors import validation_exhaustion

from asago_policy_mapper.extract.attribute import (
    ground_and_extract_evidence,
    ground_risk_group,
    ground_variants,
    synthesize_causal_chain,
)
from asago_policy_mapper.extract.models import (
    EvidenceSpan,
    RetrievalScores,
    RiskMatch,
    ScoredCandidate,
    _CausalChain,
    _CausalChains,
    _JudgeVerdict,
    _JudgeVerdicts,
    _RiskEvidence,
    _RiskEvidenceList,
)
from asago_policy_mapper.extract.querygen import ChunkGroup, generate_queries
from asago_policy_mapper.extract.retrieve import judge_borderline
from asago_policy_mapper.llm import (
    STAGES,
    IncompleteOutputException,
    LLMConfig,
    TokenTracker,
    ValidationRetryExhausted,
    _StructuredClient,
    _track_completion,
    _wrap_with_tracking,
)


def _usage(prompt: int = 10, completion: int = 5) -> SimpleNamespace:
    return SimpleNamespace(prompt_tokens=prompt, completion_tokens=completion, total_tokens=prompt + completion)


def _context_length_error() -> openai.BadRequestError:
    """A context-length 400 in the wire shape the retry path matches."""
    import httpx

    request = httpx.Request("POST", "http://localhost:8000/v1/chat/completions")
    response = httpx.Response(400, request=request, json={"error": {"type": "invalid_request_error"}})
    message = (
        "This model's maximum context length is 4096 tokens. "
        "However, you requested 1000 tokens in the messages and 4000 output tokens; "
        "the maximum is 3096 input tokens. Please reduce the length of the messages."
    )
    return openai.BadRequestError(message, response=response, body=None)


def _tracked_client() -> tuple[MagicMock, TokenTracker]:
    """Wrap a mocked raw client with the tracking layer, as create_client does.

    The mock gets the production ``for_stage`` method bound onto it, so stage
    views over the mock route through the wrapped ``chat.completions.create``
    exactly as they do over a real structured client.
    """
    tracker = TokenTracker()
    config = LLMConfig(base_url="http://test", model="test-model", max_context=0)
    client = MagicMock()
    client.create_with_completion.return_value = ("parsed", SimpleNamespace(usage=_usage()))
    _wrap_with_tracking(client, tracker, config)
    client.for_stage = _StructuredClient.for_stage.__get__(client)  # type: ignore[method-assign]
    return client, tracker


class TestStageScopedFacade:
    def test_for_stage_attributes_tokens(self):
        """Completions through a for_stage view land in that stage's totals."""
        client, tracker = _tracked_client()

        client.for_stage("judge").chat.completions.create(
            model="test-model", messages=[{"role": "user", "content": "hi"}]
        )

        assert tracker.per_stage["judge"]["calls"] == 1
        assert tracker.per_stage["judge"]["total_tokens"] == 15
        assert tracker.total_tokens == 15

    def test_incident_from_a_stage_view_carries_the_stage(self):
        """A validation retry exhausted through a stage view carries that stage.

        Exercises the full production path: view -> wrapped create -> retry
        loop -> record_incident.
        """
        tracker = TokenTracker()
        config = LLMConfig(base_url="http://test", model="test-model", max_retries=0, max_context=0)
        client = MagicMock()
        client.create_with_completion.side_effect = validation_exhaustion()
        _wrap_with_tracking(client, tracker, config)
        client.for_stage = _StructuredClient.for_stage.__get__(client)  # type: ignore[method-assign]

        with pytest.raises(ValidationRetryExhausted):
            client.for_stage("grounding").chat.completions.create(
                model="test-model", messages=[{"role": "user", "content": "hi"}]
            )

        assert tracker.incidents[0]["stage"] == "grounding"

    def test_incidents_from_parallel_views_keep_their_own_stages(self):
        """Two workers' incidents carry their own view's stage, not each other's.

        Both threads barrier between acquiring their view and failing the
        call, so a stage lost in transit would cross-attribute here.
        """
        tracker = TokenTracker()
        config = LLMConfig(base_url="http://test", model="test-model", max_retries=0, max_context=0)
        client = MagicMock()
        client.create_with_completion.side_effect = validation_exhaustion()
        _wrap_with_tracking(client, tracker, config)
        client.for_stage = _StructuredClient.for_stage.__get__(client)  # type: ignore[method-assign]
        barrier = threading.Barrier(2)

        def worker(stage: str) -> None:
            view = client.for_stage(stage)
            barrier.wait()
            with contextlib.suppress(ValidationRetryExhausted):
                view.chat.completions.create(model="test-model", messages=[{"role": "user", "content": "hi"}])

        threads = [threading.Thread(target=worker, args=(s,)) for s in ("judge", "causal_synthesis")]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert {i["stage"] for i in tracker.incidents} == {"judge", "causal_synthesis"}

    def test_context_overflow_incident_from_a_stage_view_carries_the_stage(self):
        """The context-overflow retry incident attributes to the view's stage."""
        tracker = TokenTracker()
        config = LLMConfig(base_url="http://test", model="test-model", max_retries=2, max_context=0)
        client = MagicMock()
        client.create_with_completion.side_effect = _context_length_error()
        _wrap_with_tracking(client, tracker, config)
        client.for_stage = _StructuredClient.for_stage.__get__(client)  # type: ignore[method-assign]

        with pytest.raises(openai.APIError):
            client.for_stage("expansion_grounding").chat.completions.create(
                model="test-model", messages=[{"role": "user", "content": "hi"}]
            )

        assert tracker.incidents[0]["kind"] == "context_overflow"
        assert tracker.incidents[0]["stage"] == "expansion_grounding"

    def test_output_truncated_incident_from_a_stage_view_carries_the_stage(self):
        """The truncation incident attributes to the view's stage."""
        tracker = TokenTracker()
        config = LLMConfig(base_url="http://test", model="test-model", max_retries=0, max_context=0)
        client = MagicMock()
        client.create_with_completion.side_effect = IncompleteOutputException()
        _wrap_with_tracking(client, tracker, config)
        client.for_stage = _StructuredClient.for_stage.__get__(client)  # type: ignore[method-assign]

        with pytest.raises(IncompleteOutputException):
            client.for_stage("variant_grounding").chat.completions.create(
                model="test-model", messages=[{"role": "user", "content": "hi"}]
            )

        kinds = [i["kind"] for i in tracker.incidents]
        assert "output_truncated" in kinds
        assert all(i["stage"] == "variant_grounding" for i in tracker.incidents)

    def test_parallel_stages_keep_their_own_totals(self):
        """Workers using different stage views keep separate buckets.

        Both threads barrier between acquiring their view and making the
        call, so interleaved acquisition cannot cross attributes.
        """
        client, tracker = _tracked_client()
        barrier = threading.Barrier(2)

        def worker(stage: str) -> None:
            view = client.for_stage(stage)
            barrier.wait()
            view.chat.completions.create(model="test-model", messages=[{"role": "user", "content": "hi"}])

        threads = [threading.Thread(target=worker, args=(s,)) for s in ("judge", "grounding")]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert tracker.per_stage["judge"]["calls"] == 1
        assert tracker.per_stage["grounding"]["calls"] == 1
        assert set(tracker.per_stage) == {"judge", "grounding"}

    def test_for_stage_view_delegates_to_the_same_underlying_create(self):
        """A stage view is a thin pass-through: the wrapped create is called once."""
        client, tracker = _tracked_client()

        client.for_stage("judge").chat.completions.create(
            model="test-model", messages=[{"role": "user", "content": "hi"}]
        )

        assert client.create_with_completion.call_count == 1
        assert tracker.calls == 1

    def test_call_without_stage_view_records_totals_only(self):
        """A call that skips for_stage records no stage, only totals.

        A call site that forgets its stage view loses stage attribution
        without breaking the run; this is exactly the failure the
        per-site tests below pin against.
        """
        client, tracker = _tracked_client()

        client.chat.completions.create(model="test-model", messages=[{"role": "user", "content": "hi"}])

        assert tracker.calls == 1
        assert tracker.per_stage == {}

    def test_incident_without_stage_view_carries_no_stage(self):
        """An incident on a call that skipped for_stage carries no stage key."""
        tracker = TokenTracker()
        config = LLMConfig(base_url="http://test", model="test-model", max_retries=0, max_context=0)
        client = MagicMock()
        client.create_with_completion.side_effect = validation_exhaustion()
        _wrap_with_tracking(client, tracker, config)

        with contextlib.suppress(ValidationRetryExhausted):
            client.chat.completions.create(model="test-model", messages=[{"role": "user", "content": "hi"}])

        assert tracker.incidents[0]["kind"] == "validation_exhausted"
        assert "stage" not in tracker.incidents[0]


class TestTrackCompletion:
    def test_track_completion_with_stage_routes_usage(self):
        tracker = TokenTracker()
        _track_completion(tracker, SimpleNamespace(usage=_usage()), stage="grounding")
        assert tracker.per_stage["grounding"]["calls"] == 1

    def test_track_completion_without_stage_totals_only(self):
        """Usage recorded without a stage still totals, without a per-stage bucket."""
        tracker = TokenTracker()
        _track_completion(tracker, SimpleNamespace(usage=_usage()))
        assert tracker.calls == 1
        assert tracker.per_stage == {}


class TestCallSiteStages:
    """Each production call site makes its call through a stage view for its stage."""

    def test_judge_batch_uses_judge_stage_view(self):
        client, tracker = _tracked_client()
        client.create_with_completion.return_value = (
            _JudgeVerdicts(items=[_JudgeVerdict(risk_id="R-001", relevant=True, justification="ok")]),
            SimpleNamespace(usage=_usage()),
        )
        judge_borderline(
            [ScoredCandidate(risk_id="R-001", risk_name="Bias", risk_description="d", cross_encoder_score=0.9)],
            "chunk text",
            client,
            "test-model",
        )
        assert "judge" in tracker.per_stage

    def test_ground_and_extract_evidence_uses_grounding_stage_view(self):
        client, tracker = _tracked_client()
        client.create_with_completion.return_value = (
            _RiskEvidenceList(
                items=[_RiskEvidence(risk_id="R-001", grounded=True, confidence="high", quotes=["text"])]
            ),
            SimpleNamespace(usage=_usage()),
        )
        ground_and_extract_evidence(
            chunk_text="text",
            candidates=[
                ScoredCandidate(risk_id="R-001", risk_name="Bias", risk_description="d", cross_encoder_score=0.9)
            ],
            client=client,
            model="test-model",
            document="doc.pdf",
            chunk_index=0,
        )
        assert "grounding" in tracker.per_stage

    def test_generate_queries_uses_query_gen_stage_view(self):
        client, tracker = _tracked_client()
        client.create_with_completion.return_value = (
            SimpleNamespace(queries=["q1"]),
            SimpleNamespace(usage=_usage()),
        )
        chunks = [SimpleNamespace(text="some text", source="doc.md", page=None, section=None, index=0)]
        generate_queries(chunks, [ChunkGroup(chunk_indices=[0], section=None)], client, "test-model")
        assert "query_gen" in tracker.per_stage

    def test_ground_variants_uses_variant_grounding_stage_view(self):
        client, tracker = _tracked_client()
        client.create_with_completion.return_value = (
            _RiskEvidenceList(items=[_RiskEvidence(risk_id="R---a", grounded=True, confidence="low", quotes=["text"])]),
            SimpleNamespace(usage=_usage()),
        )
        ground_variants(
            chunk_text="text",
            parent_id="R",
            parent_name="Parent",
            parent_description="d",
            variants=[{"risk_id": "R---a", "name": "A", "description": "d"}],
            client=client,
            model="test-model",
            document="doc.pdf",
            chunk_index=0,
        )
        assert "variant_grounding" in tracker.per_stage

    def test_ground_risk_group_uses_expansion_grounding_stage_view(self):
        client, tracker = _tracked_client()
        client.create_with_completion.return_value = (
            _RiskEvidenceList(
                items=[_RiskEvidence(risk_id="R-001", grounded=True, confidence="high", quotes=["text"])]
            ),
            SimpleNamespace(usage=_usage()),
        )
        chunks = [SimpleNamespace(text="some text")]
        ground_risk_group(
            chunks=chunks,
            chunk_indices=[0],
            risks=[{"risk_id": "R-001", "risk_name": "Bias", "risk_description": "d"}],
            client=client,
            model="test-model",
            document="doc.pdf",
        )
        assert "expansion_grounding" in tracker.per_stage

    def test_synthesize_causal_chain_uses_causal_synthesis_stage_view(self):
        client, tracker = _tracked_client()
        client.create_with_completion.return_value = (
            _CausalChains(
                items=[_CausalChain(threat="t", threat_source="ts", vulnerability="v", consequence="c", impact="i")]
            ),
            SimpleNamespace(usage=_usage()),
        )
        risk_match = RiskMatch(
            risk_id="R-001",
            risk_name="Bias",
            risk_description="d",
            taxonomy="t",
            confidence=0.9,
            grounding_confidence="high",
            accepted_by="threshold",
            evidence=[EvidenceSpan(text="text", document="doc.pdf", chunk_index=0)],
            scores=RetrievalScores(bm25_rank=1, embedding_distance=0.1, cross_encoder_score=0.9, rrf_score=0.05),
        )
        synthesize_causal_chain(risk_match, {0: "text"}, client, "test-model")
        assert "causal_synthesis" in tracker.per_stage


class TestStageNames:
    def test_stages_constant_is_the_spec_set(self):
        """STAGES holds exactly the six pipeline stages, so the constant can drift nowhere."""
        assert STAGES == (
            "query_gen",
            "judge",
            "grounding",
            "variant_grounding",
            "expansion_grounding",
            "causal_synthesis",
        )

    @pytest.mark.parametrize("stage", STAGES)
    def test_spec_stage_names_are_accepted(self, stage):
        client, tracker = _tracked_client()
        view = client.for_stage(stage)
        view.chat.completions.create(model="test-model", messages=[{"role": "user", "content": "hi"}])
        assert tracker.per_stage[stage]["calls"] == 1

    def test_unknown_stage_name_is_rejected(self):
        client, _ = _tracked_client()
        with pytest.raises(ValueError, match="unknown stage"):
            client.for_stage("grounding-legacy")

    def test_rejection_leaves_the_client_usable(self):
        """A rejected name fails only the view request, not the underlying client."""
        client, tracker = _tracked_client()
        with pytest.raises(ValueError):
            client.for_stage("not-a-stage")
        client.chat.completions.create(model="test-model", messages=[{"role": "user", "content": "hi"}])
        assert tracker.calls == 1
