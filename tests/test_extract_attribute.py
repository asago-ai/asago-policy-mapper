import logging
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import httpx
import openai
import pytest
from llm_errors import (
    authentication_failure,
    connection_failure,
    json_decode_error,
    pydantic_validation_error,
    server_error,
    validation_exhaustion,
)

from asago_policy_mapper.extract.attribute import (
    ground_and_extract_evidence,
    ground_risk_group,
    synthesize_causal_chain,
)
from asago_policy_mapper.extract.models import (
    EvidenceSpan,
    LLMCallRecord,
    RetrievalScores,
    RiskMatch,
    ScoredCandidate,
    _CausalChain,
    _CausalChains,
    _RiskEvidence,
    _RiskEvidenceList,
)
from asago_policy_mapper.llm import LLMConfig, ValidationRetryExhausted, create_client
from asago_policy_mapper.prompts import render_prompt


def test_ground_and_extract_evidence_returns_grounded():
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = MagicMock(
        items=[
            MagicMock(
                risk_id="R-001",
                grounded=True,
                confidence="high",
                quotes=["AI bias was detected in the outputs.", "The model shows systematic bias."],
            ),
            MagicMock(
                risk_id="R-002",
                grounded=False,
                confidence="low",
                quotes=[],
            ),
        ]
    )

    candidates = [
        ScoredCandidate(
            risk_id="R-001",
            risk_name="Model Bias",
            risk_description="Systematic bias in AI outputs.",
            cross_encoder_score=0.85,
        ),
        ScoredCandidate(
            risk_id="R-002",
            risk_name="Data Poisoning",
            risk_description="Malicious data manipulation.",
            cross_encoder_score=0.75,
        ),
    ]

    result = ground_and_extract_evidence(
        chunk_text="AI bias was detected in the outputs. The model shows systematic bias. Data quality is good.",
        candidates=candidates,
        client=mock_client,
        model="test-model",
        document="policy.pdf",
        chunk_index=2,
        page=5,
        section="Risks",
    )

    assert "R-001" in result
    assert "R-002" not in result
    evidence, confidence = result["R-001"]
    assert len(evidence) == 2
    assert confidence == "high"
    assert evidence[0].text == "AI bias was detected in the outputs."
    assert evidence[0].document == "policy.pdf"
    assert evidence[0].chunk_index == 2
    assert evidence[0].page == 5
    assert evidence[0].section == "Risks"


def test_ground_and_extract_evidence_empty_candidates():
    mock_client = MagicMock()
    result = ground_and_extract_evidence(
        chunk_text="Some text.",
        candidates=[],
        client=mock_client,
        model="test-model",
        document="doc.pdf",
        chunk_index=0,
    )
    assert result == {}
    mock_client.chat.completions.create.assert_not_called()


def test_ground_and_extract_evidence_ignores_unknown_risk_ids():
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = MagicMock(
        items=[
            MagicMock(
                risk_id="R-UNKNOWN",
                grounded=True,
                confidence="medium",
                quotes=["Some quote."],
            ),
        ]
    )

    candidates = [
        ScoredCandidate(
            risk_id="R-001",
            risk_name="Model Bias",
            risk_description="Bias.",
            cross_encoder_score=0.8,
        ),
    ]

    result = ground_and_extract_evidence(
        chunk_text="Some text.",
        candidates=candidates,
        client=mock_client,
        model="test-model",
        document="doc.pdf",
        chunk_index=0,
    )
    assert result == {}


def test_ground_and_extract_evidence_skips_empty_quotes():
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = MagicMock(
        items=[
            MagicMock(
                risk_id="R-001",
                grounded=True,
                confidence="high",
                quotes=["Valid quote.", "", "  "],
            ),
        ]
    )

    candidates = [
        ScoredCandidate(
            risk_id="R-001",
            risk_name="Model Bias",
            risk_description="Bias.",
            cross_encoder_score=0.8,
        ),
    ]

    result = ground_and_extract_evidence(
        chunk_text="Valid quote. Other text.",
        candidates=candidates,
        client=mock_client,
        model="test-model",
        document="doc.pdf",
        chunk_index=0,
    )

    evidence, _ = result["R-001"]
    assert len(evidence) == 1
    assert evidence[0].text == "Valid quote."


def test_ground_and_extract_evidence_captures_call(mock_client):
    candidates = [
        ScoredCandidate(
            risk_id="R-001",
            risk_name="Bias",
            risk_description="Model bias risk",
            cross_encoder_score=0.9,
        ),
    ]
    mock_client.chat.completions.create.return_value = _RiskEvidenceList(
        items=[
            _RiskEvidence(
                risk_id="R-001",
                grounded=True,
                confidence="high",
                quotes=["AI systems must avoid bias"],
            ),
        ]
    )

    collector: list[LLMCallRecord] = []
    result = ground_and_extract_evidence(
        chunk_text="AI systems must avoid bias and protect data.",
        candidates=candidates,
        client=mock_client,
        model="test-model",
        document="policy.pdf",
        chunk_index=0,
        call_collector=collector,
    )

    assert "R-001" in result
    assert len(collector) == 1
    assert collector[0].stage == "grounding"
    assert collector[0].chunk_index == 0
    assert collector[0].risk_ids == ["R-001"]
    assert collector[0].result_summary == "1/1 grounded"
    assert collector[0].duration_ms >= 0


def test_ground_and_extract_evidence_no_collector(mock_client):
    """Existing behavior: no collector, no error."""
    candidates = [
        ScoredCandidate(
            risk_id="R-001",
            risk_name="Bias",
            risk_description="Model bias risk",
            cross_encoder_score=0.9,
        ),
    ]
    mock_client.chat.completions.create.return_value = _RiskEvidenceList(
        items=[_RiskEvidence(risk_id="R-001", grounded=True, confidence="high", quotes=["text"])]
    )

    result = ground_and_extract_evidence(
        chunk_text="text",
        candidates=candidates,
        client=mock_client,
        model="test-model",
        document="doc.pdf",
        chunk_index=0,
    )
    assert "R-001" in result


# ---------------------------------------------------------------------------
# Tests for ground_risk_group
# ---------------------------------------------------------------------------


def _make_chunks(texts: list[str]):
    """Create a list of chunk-like objects with a .text attribute."""
    return [SimpleNamespace(text=t) for t in texts]


def test_ground_risk_group_returns_grounded():
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _RiskEvidenceList(
        items=[
            _RiskEvidence(
                risk_id="R-001",
                grounded=True,
                confidence="high",
                quotes=["AI bias was detected."],
            ),
            _RiskEvidence(
                risk_id="R-002",
                grounded=False,
                confidence="low",
                quotes=[],
            ),
        ]
    )

    chunks = _make_chunks(["Chunk zero text.", "AI bias was detected. Data is clean."])
    risks = [
        {"risk_id": "R-001", "risk_name": "Model Bias", "risk_description": "Systematic bias."},
        {"risk_id": "R-002", "risk_name": "Data Poisoning", "risk_description": "Malicious data."},
    ]

    result = ground_risk_group(
        chunks=chunks,
        chunk_indices=[1],
        risks=risks,
        client=mock_client,
        model="test-model",
        document="policy.pdf",
    )

    assert "R-001" in result
    assert "R-002" not in result
    evidence, confidence = result["R-001"]
    assert len(evidence) == 1
    assert evidence[0].text == "AI bias was detected."
    assert evidence[0].document == "policy.pdf"
    assert confidence == "high"


def test_ground_risk_group_empty_risks():
    mock_client = MagicMock()
    chunks = _make_chunks(["Some text."])

    result = ground_risk_group(
        chunks=chunks,
        chunk_indices=[0],
        risks=[],
        client=mock_client,
        model="test-model",
        document="doc.pdf",
    )

    assert result == {}
    mock_client.chat.completions.create.assert_not_called()


def test_ground_risk_group_empty_chunks():
    mock_client = MagicMock()
    risks = [
        {"risk_id": "R-001", "risk_name": "Bias", "risk_description": "Bias risk."},
    ]

    result = ground_risk_group(
        chunks=_make_chunks(["Text."]),
        chunk_indices=[],
        risks=risks,
        client=mock_client,
        model="test-model",
        document="doc.pdf",
    )

    assert result == {}
    mock_client.chat.completions.create.assert_not_called()


def test_ground_risk_group_out_of_range_chunks():
    mock_client = MagicMock()
    chunks = _make_chunks(["Only one chunk."])
    risks = [
        {"risk_id": "R-001", "risk_name": "Bias", "risk_description": "Bias risk."},
    ]

    result = ground_risk_group(
        chunks=chunks,
        chunk_indices=[5, 10],
        risks=risks,
        client=mock_client,
        model="test-model",
        document="doc.pdf",
    )

    assert result == {}
    mock_client.chat.completions.create.assert_not_called()


def test_ground_risk_group_ignores_unknown_risk_ids():
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _RiskEvidenceList(
        items=[
            _RiskEvidence(
                risk_id="R-UNKNOWN",
                grounded=True,
                confidence="medium",
                quotes=["Some evidence."],
            ),
        ]
    )

    chunks = _make_chunks(["Some text with evidence."])
    risks = [
        {"risk_id": "R-001", "risk_name": "Bias", "risk_description": "Bias risk."},
    ]

    result = ground_risk_group(
        chunks=chunks,
        chunk_indices=[0],
        risks=risks,
        client=mock_client,
        model="test-model",
        document="doc.pdf",
    )

    assert result == {}


def test_ground_risk_group_skips_empty_quotes():
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _RiskEvidenceList(
        items=[
            _RiskEvidence(
                risk_id="R-001",
                grounded=True,
                confidence="high",
                quotes=["", "  ", ""],
            ),
        ]
    )

    chunks = _make_chunks(["Chunk text here."])
    risks = [
        {"risk_id": "R-001", "risk_name": "Bias", "risk_description": "Bias risk."},
    ]

    result = ground_risk_group(
        chunks=chunks,
        chunk_indices=[0],
        risks=risks,
        client=mock_client,
        model="test-model",
        document="doc.pdf",
    )

    assert "R-001" not in result


def test_ground_risk_group_captures_call(mock_client):
    chunks = _make_chunks(["Chunk zero.", "Chunk one with bias evidence."])
    risks = [
        {"risk_id": "R-001", "risk_name": "Bias", "risk_description": "Model bias risk."},
        {"risk_id": "R-002", "risk_name": "Privacy", "risk_description": "Data privacy risk."},
    ]
    mock_client.chat.completions.create.return_value = _RiskEvidenceList(
        items=[
            _RiskEvidence(
                risk_id="R-001",
                grounded=True,
                confidence="high",
                quotes=["Chunk one with bias evidence."],
            ),
            _RiskEvidence(
                risk_id="R-002",
                grounded=False,
                confidence="low",
                quotes=[],
            ),
        ]
    )

    collector: list[LLMCallRecord] = []
    result = ground_risk_group(
        chunks=chunks,
        chunk_indices=[0, 1],
        risks=risks,
        client=mock_client,
        model="test-model",
        document="policy.pdf",
        call_collector=collector,
    )

    assert "R-001" in result
    assert len(collector) == 1
    record = collector[0]
    assert record.stage == "grounding"
    assert record.call_id.startswith("ground-expand-")
    assert record.chunk_index == 0
    assert record.risk_ids == ["R-001", "R-002"]
    assert "1/2 grounded (expansion)" == record.result_summary
    assert record.duration_ms >= 0


# ---------------------------------------------------------------------------
# Tests for causal_synthesis prompt template
# ---------------------------------------------------------------------------


def test_causal_synthesis_prompt_renders():
    messages = render_prompt(
        "causal_synthesis",
        {
            "risk_id": "atlas-bias",
            "risk_name": "AI Bias",
            "risk_description": "Systematic bias in AI model outputs.",
            "chunk_texts": "The regulation requires that AI systems used in credit scoring"
            " must not discriminate based on protected characteristics.",
        },
    )
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert "atlas-bias" in messages[1]["content"]
    assert "credit scoring" in messages[1]["content"]


# ---------------------------------------------------------------------------
# Tests for synthesize_causal_chain
# ---------------------------------------------------------------------------


def _make_risk_match(risk_id="atlas-bias", chunk_indices=None):
    if chunk_indices is None:
        chunk_indices = [0, 2]
    return RiskMatch(
        risk_id=risk_id,
        risk_name="AI Bias",
        risk_description="Systematic bias in AI outputs.",
        taxonomy="ibm-risk-atlas",
        confidence=0.85,
        grounding_confidence="high",
        accepted_by="threshold",
        evidence=[
            EvidenceSpan(
                text="AI systems must not discriminate.",
                document="policy.pdf",
                chunk_index=idx,
            )
            for idx in chunk_indices
        ],
        scores=RetrievalScores(
            bm25_rank=1,
            embedding_distance=0.2,
            cross_encoder_score=0.85,
            rrf_score=0.03,
        ),
    )


def test_synthesize_causal_chain_success(mock_client):
    mock_client.chat.completions.create.return_value = _CausalChains(
        items=[
            _CausalChain(
                threat="AI credit scoring discriminates against protected groups",
                threat_source="Biased training data from historical lending decisions",
                vulnerability="No fairness auditing of model outputs",
                consequence="Qualified applicants denied credit",
                impact="Financial exclusion",
            ),
        ]
    )

    risk = _make_risk_match(chunk_indices=[0, 2])
    chunk_texts = {0: "AI in credit scoring must be fair.", 2: "Discrimination is prohibited."}

    result = synthesize_causal_chain(
        risk_match=risk,
        chunk_texts=chunk_texts,
        client=mock_client,
        model="test-model",
    )

    assert result is not None
    assert result.threat == "AI credit scoring discriminates against protected groups"
    assert result.vulnerability == "No fairness auditing of model outputs"


def test_synthesize_causal_chain_empty_strings_return_none(mock_client):
    mock_client.chat.completions.create.return_value = _CausalChains(
        items=[
            _CausalChain(
                threat="",
                threat_source="",
                vulnerability="",
                consequence="",
                impact="",
            ),
        ]
    )

    risk = _make_risk_match()
    chunk_texts = {0: "Some text.", 2: "More text."}

    result = synthesize_causal_chain(
        risk_match=risk,
        chunk_texts=chunk_texts,
        client=mock_client,
        model="test-model",
    )

    assert result is None


@pytest.mark.parametrize(
    "make_cause",
    [pydantic_validation_error, json_decode_error],
    ids=["pydantic-validation-error", "json-decode-error"],
)
def test_synthesize_causal_chain_validation_exhaustion_returns_none(mock_client, caplog, make_cause):
    mock_client.chat.completions.create.side_effect = validation_exhaustion(make_cause())
    collector: list[LLMCallRecord] = []

    with caplog.at_level(logging.WARNING, logger="asago_policy_mapper.extract.attribute"):
        result = synthesize_causal_chain(
            risk_match=_make_risk_match("atlas-bias"),
            chunk_texts={0: "Some text.", 2: "More text."},
            client=mock_client,
            model="test-model",
            call_collector=collector,
        )

    assert result is None
    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert any("atlas-bias" in r.getMessage() for r in warnings)
    assert len(collector) == 1
    assert collector[0].result_summary == "retry_exhausted"
    assert collector[0].response == {}


@pytest.mark.parametrize(
    "make_error",
    [connection_failure, server_error, authentication_failure],
    ids=["connection-error", "http-5xx", "http-401"],
)
def test_synthesize_causal_chain_api_error_propagates_untouched(mock_client, make_error):
    error = make_error()
    mock_client.chat.completions.create.side_effect = error
    collector: list[LLMCallRecord] = []

    with pytest.raises(type(error)) as excinfo:
        synthesize_causal_chain(
            risk_match=_make_risk_match(),
            chunk_texts={0: "Some text.", 2: "More text."},
            client=mock_client,
            model="test-model",
            call_collector=collector,
        )

    assert excinfo.value is error
    assert collector == []


def test_synthesize_causal_chain_api_error_not_wrapped_as_validation_exhaustion(mock_client):
    # An APIConnectionError failed_attempts entry must not count as validation exhaustion.
    error = validation_exhaustion(openai.APIConnectionError(request=httpx.Request("POST", "http://localhost")))
    mock_client.chat.completions.create.side_effect = error

    with pytest.raises(ValidationRetryExhausted):
        synthesize_causal_chain(
            risk_match=_make_risk_match(),
            chunk_texts={0: "Some text.", 2: "More text."},
            client=mock_client,
            model="test-model",
        )


def test_synthesize_causal_chain_non_client_error_propagates(mock_client):
    mock_client.chat.completions.create.side_effect = ConnectionError("endpoint down")

    with pytest.raises(ConnectionError):
        synthesize_causal_chain(
            risk_match=_make_risk_match(),
            chunk_texts={0: "Some text.", 2: "More text."},
            client=mock_client,
            model="test-model",
        )


def _real_client(handler):
    """Build the production client stack (structured client -> tracked create -> retry) over a stubbed transport."""
    config = LLMConfig(base_url="http://localhost:8000/v1", model="test-model", max_retries=1)
    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    with patch(
        "asago_policy_mapper.llm.OpenAI",
        lambda **kw: openai.OpenAI(http_client=http_client, max_retries=0, **kw),
    ):
        return create_client(config)


def _completion_response(content):
    return httpx.Response(
        200,
        json={
            "id": "chatcmpl-1",
            "object": "chat.completion",
            "created": 0,
            "model": "test-model",
            "choices": [{"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": content}}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        },
    )


def test_synthesize_causal_chain_real_stack_invalid_output_is_skipped(caplog):
    calls = []

    def handler(request):
        calls.append(request)
        return _completion_response('{"items": "not a list"}')

    with caplog.at_level(logging.WARNING, logger="asago_policy_mapper.extract.attribute"):
        result = synthesize_causal_chain(
            risk_match=_make_risk_match("atlas-bias"),
            chunk_texts={0: "Some text.", 2: "More text."},
            client=_real_client(handler),
            model="test-model",
        )

    assert result is None
    assert len(calls) == 2
    assert any("atlas-bias" in r.getMessage() for r in caplog.records if r.levelno == logging.WARNING)


def test_synthesize_causal_chain_real_stack_server_error_propagates():
    def handler(request):
        return httpx.Response(503, json={"error": {"message": "unavailable"}})

    with pytest.raises(openai.InternalServerError):
        synthesize_causal_chain(
            risk_match=_make_risk_match(),
            chunk_texts={0: "Some text.", 2: "More text."},
            client=_real_client(handler),
            model="test-model",
        )


def test_synthesize_causal_chain_real_stack_connection_error_propagates():
    def handler(request):
        raise httpx.ConnectError("refused", request=request)

    with pytest.raises(openai.APIConnectionError):
        synthesize_causal_chain(
            risk_match=_make_risk_match(),
            chunk_texts={0: "Some text.", 2: "More text."},
            client=_real_client(handler),
            model="test-model",
        )


def test_synthesize_causal_chain_records_call(mock_client):
    mock_client.chat.completions.create.return_value = _CausalChains(
        items=[
            _CausalChain(
                threat="Threat",
                threat_source="Source",
                vulnerability="Vuln",
                consequence="Consequence",
                impact="Impact",
            ),
        ]
    )

    risk = _make_risk_match()
    chunk_texts = {0: "Text.", 2: "More."}
    collector: list[LLMCallRecord] = []

    synthesize_causal_chain(
        risk_match=risk,
        chunk_texts=chunk_texts,
        client=mock_client,
        model="test-model",
        call_collector=collector,
    )

    assert len(collector) == 1
    assert collector[0].stage == "causal_synthesis"
    assert collector[0].call_id == "causal-001"
    assert collector[0].risk_ids == ["atlas-bias"]
    assert collector[0].duration_ms >= 0
