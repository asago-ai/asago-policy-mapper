from types import SimpleNamespace
from unittest.mock import MagicMock

from concorde_policy_mapper.extract.attribute import ground_and_extract_evidence, ground_risk_group
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


# ---------------------------------------------------------------------------
# Tests for ground_risk_group
# ---------------------------------------------------------------------------

def _make_chunks(texts: list[str]):
    """Create a list of chunk-like objects with a .text attribute."""
    return [SimpleNamespace(text=t) for t in texts]


def test_ground_risk_group_returns_grounded():
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = [
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
    mock_client.chat.completions.create.return_value = [
        _RiskEvidence(
            risk_id="R-UNKNOWN",
            grounded=True,
            confidence="medium",
            quotes=["Some evidence."],
        ),
    ]

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
    mock_client.chat.completions.create.return_value = [
        _RiskEvidence(
            risk_id="R-001",
            grounded=True,
            confidence="high",
            quotes=["", "  ", ""],
        ),
    ]

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
    mock_client.chat.completions.create.return_value = [
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
