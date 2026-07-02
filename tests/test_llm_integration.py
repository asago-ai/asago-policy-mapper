"""Integration tests exercising real LLM calls via Ollama or vLLM.

All tests are marked ``@pytest.mark.llm`` and skipped automatically when no
LLM server is reachable (see ``llm_config`` fixture in conftest.py).

Run with::

    uv run pytest --test-llm -m llm -v --timeout=120
"""

import json
import logging
import os
import sys
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Literal

import instructor
import pytest
from openai import OpenAI

from asago_policy_mapper.extract.attribute import (
    ground_and_extract_evidence,
    synthesize_causal_chain,
)
from asago_policy_mapper.extract.models import (
    EvidenceSpan,
    ExtractionResult,
    LLMCallRecord,
    RetrievalConfig,
    RetrievalScores,
    RiskMatch,
    ScoredCandidate,
)
from asago_policy_mapper.extract.pipeline import run_extraction
from asago_policy_mapper.extract.querygen import ChunkGroup, generate_queries
from asago_policy_mapper.extract.retrieve import judge_borderline
from asago_policy_mapper.llm import LLMConfig, SlimModel, TokenTracker, create_client

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
_handler = logging.StreamHandler(sys.stderr)
_handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
logger.addHandler(_handler)
logger.propagate = False


def _pp(obj: object) -> str:
    """Pretty-print an object for debug logs."""
    try:
        return json.dumps(obj, indent=2, default=str)
    except (TypeError, ValueError):
        return repr(obj)


# Apply marks to every test in this module (skipped unless --test-llm is passed)
pytestmark = [pytest.mark.llm, pytest.mark.timeout(120)]

LLM_TEST_DOCUMENT = """\
# AI Governance Policy

Organizations deploying AI systems must evaluate and mitigate risks of algorithmic bias,
ensuring that model outputs do not systematically disadvantage any demographic group.
Personal data used for training or inference must be handled in compliance with applicable
privacy regulations. AI-generated outputs must be clearly disclosed to end-users, and
organizations must provide meaningful explanations of how AI-driven decisions are made
to maintain transparency and trust.
"""

CHUNK_TEXT = (
    "Organizations deploying AI systems must evaluate and mitigate risks of algorithmic bias, "
    "ensuring that model outputs do not systematically disadvantage any demographic group. "
    "AI-generated outputs must be clearly disclosed to end-users, and organizations must provide "
    "meaningful explanations of how AI-driven decisions are made to maintain transparency and trust."
)

SAMPLE_CANDIDATES = [
    ScoredCandidate(
        risk_id="R-BIAS",
        risk_name="Algorithmic Bias",
        risk_description="Systematic errors in AI outputs that favor or disadvantage certain groups",
        rrf_score=0.8,
    ),
    ScoredCandidate(
        risk_id="R-TRANSPARENCY",
        risk_name="Lack of Transparency",
        risk_description="Failure to disclose AI involvement or explain AI-driven decisions",
        rrf_score=0.75,
    ),
    # Deliberately unrelated to the governance text — a small model must not match it
    ScoredCandidate(
        risk_id="R-ROBOT",
        risk_name="Physical Robot Safety",
        risk_description="Risk of bodily harm from autonomous robots operating in shared physical spaces with humans",
        rrf_score=0.7,
    ),
]


# Lightweight stand-in for ai-atlas-nexus risk objects (same attribute shape)
def _make_risk(id: str, name: str, description: str, concern: str = "", parent: str = "") -> SimpleNamespace:
    return SimpleNamespace(
        id=id,
        name=name,
        description=description,
        concern=concern,
        risk_type="",
        isDefinedByTaxonomy="test-taxonomy",
        isPartOf=parent,
        exact_mappings=[],
        close_mappings=[],
        broad_mappings=[],
        narrow_mappings=[],
        related_mappings=[],
    )


LLM_TEST_RISKS = [
    _make_risk(
        "R-BIAS", "Algorithmic Bias", "Systematic errors in AI outputs that favor or disadvantage certain groups"
    ),
    # Deliberately unrelated to the governance text — a small model must not match it
    _make_risk(
        "R-ROBOT",
        "Physical Robot Safety",
        "Risk of bodily harm from autonomous robots operating in shared physical spaces with humans",
    ),
    _make_risk(
        "R-PRIVACY", "Privacy Violation", "Unauthorized collection, use, or disclosure of personal data by AI systems"
    ),
    _make_risk(
        "R-TRANSPARENCY", "Lack of Transparency", "Failure to disclose AI involvement or explain AI-driven decisions"
    ),
    _make_risk(
        "R-SECURITY",
        "Model Security",
        "Vulnerabilities in AI model serving infrastructure enabling unauthorized access or manipulation",
    ),
]


@pytest.fixture(scope="session")
def llm_config():
    """LLMConfig pointing at a local OpenAI-compatible server. Skips if unreachable."""
    base_url = os.environ.get("LLM_BASE_URL", "http://localhost:11434/v1")
    model = os.environ.get("LLM_MODEL", "gemma3:1b")

    try:
        probe = OpenAI(base_url=base_url, api_key="none")
        probe.models.list()
    except Exception:
        pytest.skip(f"LLM server not available at {base_url}")

    return LLMConfig(
        base_url=base_url,
        model=model,
        max_context=8192,
        max_tokens=2048,
        max_retries=5,
        max_concurrent=1,
        temperature=0.0,
    )


@pytest.fixture(scope="session")
def llm_client(llm_config):
    """Instructor client using JSON_SCHEMA mode for server-side constrained decoding.

    Unlike the default Mode.JSON (schema in prompt), Mode.JSON_SCHEMA makes
    Ollama/vLLM enforce the schema at the token level, for small models (ie Gemma3)
    """
    tracker = TokenTracker()
    client = create_client(llm_config, tracker=tracker, mode=instructor.Mode.JSON_SCHEMA)
    return client, tracker


@pytest.fixture(scope="session")
def small_risk_set():
    return list(LLM_TEST_RISKS)


@pytest.fixture(scope="session")
def tiny_document(tmp_path_factory):
    doc = tmp_path_factory.mktemp("llm_e2e") / "policy.md"
    doc.write_text(LLM_TEST_DOCUMENT)
    return doc


# ---------------------------------------------------------------------------
# Smoke tests
# ---------------------------------------------------------------------------


class SimpleAnswer(SlimModel):
    answer: str
    confidence: float


def test_instructor_structured_output(llm_client, llm_config):
    """Instructor + model produce valid structured output."""
    client, _ = llm_client
    result = client.chat.completions.create(
        model=llm_config.model,
        response_model=SimpleAnswer,
        messages=[{"role": "user", "content": "What color is the sky on a clear day? Answer briefly."}],
        max_tokens=256,
    )
    assert isinstance(result, SimpleAnswer)
    assert result.answer
    assert isinstance(result.confidence, float)
    logger.debug("SimpleAnswer: answer=%r, confidence=%s", result.answer, result.confidence)


class ConstrainedAnswer(SlimModel):
    verdict: Literal["yes", "no"]
    reason: str


def test_instructor_retry_on_validation(llm_client, llm_config):
    """Instructor retries until the model produces a valid Literal value."""
    client, _ = llm_client
    result = client.chat.completions.create(
        model=llm_config.model,
        response_model=ConstrainedAnswer,
        messages=[
            {
                "role": "user",
                "content": (
                    "Is the sky blue? You MUST answer with verdict 'yes' or 'no' "
                    "(exactly one of those two words) and a short reason."
                ),
            }
        ],
        max_tokens=256,
    )
    assert isinstance(result, ConstrainedAnswer)
    assert result.verdict in ("yes", "no")
    assert result.reason
    logger.debug("ConstrainedAnswer: verdict=%r, reason=%r", result.verdict, result.reason)


# ---------------------------------------------------------------------------
# Component tests
# ---------------------------------------------------------------------------


def test_judge_borderline_real_llm(llm_client, llm_config):
    """judge_borderline returns a list of accepted candidates."""
    client, _ = llm_client
    call_collector: list[LLMCallRecord] = []

    accepted = judge_borderline(
        candidates=SAMPLE_CANDIDATES,
        chunk_text=CHUNK_TEXT,
        client=client,
        model=llm_config.model,
        call_collector=call_collector,
    )

    assert isinstance(accepted, list)
    accepted_ids = {c.risk_id for c in accepted}
    assert "R-BIAS" in accepted_ids, f"R-BIAS should be accepted, got {accepted_ids}"
    assert "R-ROBOT" not in accepted_ids, f"R-ROBOT should NOT be accepted, got {accepted_ids}"
    assert len(accepted) >= 1
    for c in accepted:
        assert isinstance(c, ScoredCandidate)
    assert len(call_collector) >= 1
    assert call_collector[0].stage == "judge"
    logger.debug(
        "Judge accepted %d/%d candidates: %s", len(accepted), len(SAMPLE_CANDIDATES), [c.risk_id for c in accepted]
    )
    logger.debug("Judge LLM response:\n%s", _pp(call_collector[0].response))


def test_grounding_real_llm(llm_client, llm_config):
    """ground_and_extract_evidence returns evidence dict."""
    client, _ = llm_client
    call_collector: list[LLMCallRecord] = []

    result = ground_and_extract_evidence(
        chunk_text=CHUNK_TEXT,
        candidates=SAMPLE_CANDIDATES,
        client=client,
        model=llm_config.model,
        document="policy.md",
        chunk_index=0,
        call_collector=call_collector,
    )

    assert isinstance(result, dict)
    assert len(result) >= 1
    assert "R-ROBOT" not in result, f"R-ROBOT should NOT be grounded, got {list(result.keys())}"
    for risk_id, (spans, confidence) in result.items():
        assert isinstance(risk_id, str)
        assert isinstance(spans, list)
        assert confidence in ("high", "medium", "low")
        for span in spans:
            assert isinstance(span, EvidenceSpan)
    assert len(call_collector) >= 1
    assert call_collector[0].stage == "grounding"
    logger.debug("Grounding returned %d risks: %s", len(result), list(result.keys()))
    for risk_id, (spans, confidence) in result.items():
        logger.debug("  %s (confidence=%s): %d evidence spans", risk_id, confidence, len(spans))
        for span in spans:
            logger.debug("    quote: %r", span.text[:120])
    logger.debug("Grounding LLM response:\n%s", _pp(call_collector[0].response))


def test_query_generation_real_llm(llm_client, llm_config):
    """generate_queries produces non-empty queries."""
    client, _ = llm_client

    @dataclass
    class FakeChunk:
        text: str
        source: str
        index: int
        page: int | None = None
        section: str | None = None

    chunks = [FakeChunk(text=CHUNK_TEXT, source="policy.md", index=0, section="governance")]
    groups = [ChunkGroup(chunk_indices=[0], section="governance")]
    call_collector: list[LLMCallRecord] = []

    result = generate_queries(
        chunks=chunks,  # type: ignore[arg-type]
        groups=groups,
        client=client,
        model=llm_config.model,
        call_collector=call_collector,
        max_workers=1,
    )

    assert isinstance(result, list)
    assert len(result) > 0
    for qr in result:
        assert qr.query
        assert len(qr.chunk_indices) > 0
    assert len(call_collector) >= 1
    logger.debug("Query generation produced %d queries:", len(result))
    for qr in result:
        logger.debug("  query=%r, chunk_indices=%s", qr.query, qr.chunk_indices)
    logger.debug("Query gen LLM response:\n%s", _pp(call_collector[0].response))


def test_causal_synthesis_real_llm(llm_client, llm_config):
    """synthesize_causal_chain produces a causal chain or gracefully returns None."""
    client, _ = llm_client
    call_collector: list[LLMCallRecord] = []

    risk_match = RiskMatch(
        risk_id="R-BIAS",
        risk_name="Algorithmic Bias",
        risk_description="Systematic errors in AI outputs that favor or disadvantage certain groups",
        confidence=0.9,
        grounding_confidence="high",
        accepted_by="grounding",
        evidence=[
            EvidenceSpan(
                text="must evaluate and mitigate risks of algorithmic bias",
                document="policy.md",
                chunk_index=0,
            )
        ],
        scores=RetrievalScores(bm25_rank=1, embedding_distance=0.2, cross_encoder_score=0.8, rrf_score=0.8),
    )

    chain = synthesize_causal_chain(
        risk_match=risk_match,
        chunk_texts={0: CHUNK_TEXT},
        client=client,
        model=llm_config.model,
        call_collector=call_collector,
    )

    assert len(call_collector) >= 1
    assert call_collector[0].stage == "causal_synthesis"
    assert chain is not None
    assert chain.threat or chain.vulnerability or chain.consequence
    logger.debug(
        "Causal chain: threat=%r, vulnerability=%r, consequence=%r",
        chain.threat,
        chain.vulnerability,
        chain.consequence,
    )
    logger.debug("Causal synthesis LLM response:\n%s", _pp(call_collector[0].response))


# ---------------------------------------------------------------------------
# E2E pipeline tests
# ---------------------------------------------------------------------------


def _log_extraction_result(result: ExtractionResult) -> None:
    if not logger.isEnabledFor(logging.DEBUG):
        return
    stages = {}
    for call in result.llm_calls:
        stages.setdefault(call.stage, []).append(call)
    logger.debug("Pipeline completed: %d LLM calls across stages %s", len(result.llm_calls), list(stages.keys()))
    for stage, calls in stages.items():
        logger.debug("  stage=%s: %d calls", stage, len(calls))
        for call in calls:
            logger.debug("    response:\n%s", _pp(call.response))
    logger.debug("Matches: %d risks found", len(result.risks))
    for m in result.risks:
        logger.debug(
            "  %s (%s) confidence=%s, evidence=%d spans",
            m.risk_id,
            m.risk_name,
            m.grounding_confidence,
            len(m.evidence),
        )
        for e in m.evidence:
            logger.debug("    quote: %r", e.text[:120])
    logger.debug("Timing:\n%s", _pp(result.retrieval_stats.timing_ms))


def test_pipeline_e2e_no_querygen(llm_client, llm_config, tiny_document, small_risk_set):
    """Full pipeline without query generation: retrieval -> judge -> grounding."""
    client, tracker = llm_client

    result = run_extraction(
        documents=[tiny_document],
        client=client,
        config=llm_config,
        risks=small_risk_set,
        retrieval=RetrievalConfig(
            query_gen=False,
            grounding_passes=1,
            expansion_passes=1,
            expand_siblings=False,
            no_causal_synthesis=True,
        ),
    )

    assert isinstance(result, ExtractionResult)
    assert result.retrieval_stats.total_chunks >= 1
    assert len(result.llm_calls) > 0
    assert len(result.risks) >= 1
    matched_ids = {m.risk_id for m in result.risks}
    assert "R-ROBOT" not in matched_ids, f"R-ROBOT should NOT be matched, got {matched_ids}"
    for call in result.llm_calls:
        assert call.messages
        assert call.response is not None
    _log_extraction_result(result)


def test_pipeline_e2e_with_querygen(llm_client, llm_config, tiny_document, small_risk_set):
    """Full pipeline with query generation (default path)."""
    client, tracker = llm_client

    result = run_extraction(
        documents=[tiny_document],
        client=client,
        config=llm_config,
        risks=small_risk_set,
        retrieval=RetrievalConfig(
            query_gen=True,
            grounding_passes=1,
            expansion_passes=1,
            expand_siblings=False,
            no_causal_synthesis=True,
        ),
    )

    assert isinstance(result, ExtractionResult)
    assert result.retrieval_stats.total_chunks >= 1
    assert len(result.llm_calls) > 0
    assert len(result.risks) >= 1
    matched_ids = {m.risk_id for m in result.risks}
    assert "R-ROBOT" not in matched_ids, f"R-ROBOT should NOT be matched, got {matched_ids}"
    querygen_calls = [c for c in result.llm_calls if c.stage == "query_gen"]
    assert len(querygen_calls) >= 1
    _log_extraction_result(result)


def test_pipeline_e2e_full(llm_client, llm_config, tiny_document, small_risk_set):
    """Full pipeline with all stages including causal synthesis."""
    client, tracker = llm_client

    result = run_extraction(
        documents=[tiny_document],
        client=client,
        config=llm_config,
        risks=small_risk_set,
        retrieval=RetrievalConfig(
            query_gen=False,
            grounding_passes=1,
            expansion_passes=1,
            expand_siblings=False,
            no_causal_synthesis=False,
        ),
    )

    assert isinstance(result, ExtractionResult)
    assert result.retrieval_stats.total_chunks >= 1
    assert len(result.llm_calls) > 0
    assert len(result.risks) >= 1
    matched_ids = {m.risk_id for m in result.risks}
    assert "R-ROBOT" not in matched_ids, f"R-ROBOT should NOT be matched, got {matched_ids}"
    assert result.retrieval_stats.timing_ms.get("grounding_ms", 0) > 0
    stages = {c.stage for c in result.llm_calls}
    assert "grounding" in stages or "judge" in stages
    _log_extraction_result(result)
