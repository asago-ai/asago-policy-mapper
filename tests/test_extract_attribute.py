from unittest.mock import MagicMock

from concorde_policy_mapper.extract.attribute import ground_and_extract_evidence
from concorde_policy_mapper.extract.models import LLMCallRecord, ScoredCandidate, _RiskEvidence


def test_ground_and_extract_evidence_returns_grounded():
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = [
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
    mock_client.chat.completions.create.return_value = [
        MagicMock(
            risk_id="R-UNKNOWN",
            grounded=True,
            confidence="medium",
            quotes=["Some quote."],
        ),
    ]

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
    mock_client.chat.completions.create.return_value = [
        MagicMock(
            risk_id="R-001",
            grounded=True,
            confidence="high",
            quotes=["Valid quote.", "", "  "],
        ),
    ]

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
    mock_client.chat.completions.create.return_value = [
        _RiskEvidence(
            risk_id="R-001",
            grounded=True,
            confidence="high",
            quotes=["AI systems must avoid bias"],
        ),
    ]

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
    mock_client.chat.completions.create.return_value = [
        _RiskEvidence(risk_id="R-001", grounded=True, confidence="high", quotes=["text"]),
    ]

    result = ground_and_extract_evidence(
        chunk_text="text",
        candidates=candidates,
        client=mock_client,
        model="test-model",
        document="doc.pdf",
        chunk_index=0,
    )
    assert "R-001" in result
