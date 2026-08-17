from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from asago_policy_mapper.extract.annotate import (
    _find_span_in_chunk,
    _locate_evidence,
    _normalize,
    prepare_annotation_data,
)
from asago_policy_mapper.extract.parse import Chunk


class TestNormalize:
    def test_whitespace_collapse(self):
        assert _normalize("hello   world\n\tfoo") == "hello world foo"

    def test_smart_quotes(self):
        assert _normalize("“hello”") == '"hello"'
        assert _normalize("‘hi’") == "'hi'"

    def test_dashes(self):
        assert _normalize("a—b–c") == "a-b-c"

    def test_nbsp(self):
        assert _normalize("a b") == "a b"

    def test_nfkc(self):
        assert _normalize("ﬁ") == "fi"


class TestFindSpanInChunk:
    def test_exact_match(self):
        chunk = "The quick brown fox jumps over the lazy dog."
        evidence = "brown fox jumps"
        start, end, is_fuzzy = _find_span_in_chunk(evidence, chunk)
        assert chunk[start:end] == evidence
        assert not is_fuzzy

    def test_normalized_match(self):
        chunk = "The  quick\nbrown  fox  jumps."
        evidence = "quick brown fox jumps."
        start, end, is_fuzzy = _find_span_in_chunk(evidence, chunk)
        assert start < end
        assert not is_fuzzy

    def test_smart_quote_match(self):
        chunk = "He said “hello world” clearly."
        evidence = 'He said "hello world" clearly.'
        start, end, is_fuzzy = _find_span_in_chunk(evidence, chunk)
        assert start < end
        assert not is_fuzzy

    def test_fuzzy_match(self):
        chunk = "The quick brown fox jumps over the lazy dog near the river."
        evidence = "The quick brown fox leaps over the lazy dog near the river."
        start, end, is_fuzzy = _find_span_in_chunk(evidence, chunk)
        assert start < end
        assert is_fuzzy

    def test_no_match(self):
        chunk = "The quick brown fox."
        evidence = "Completely unrelated text about something else entirely different."
        start, end, is_fuzzy = _find_span_in_chunk(evidence, chunk)
        assert start == 0
        assert end == 0

    def test_empty_evidence(self):
        start, end, is_fuzzy = _find_span_in_chunk("", "some chunk text")
        assert start == 0
        assert end == 0


class TestLocateEvidence:
    def _make_chunks(self, texts: list[str]) -> list[Chunk]:
        return [Chunk(text=t, source="test.txt", index=i) for i, t in enumerate(texts)]

    def test_found_at_hinted_index(self):
        chunks = self._make_chunks(["aaa bbb ccc", "ddd eee fff", "ggg hhh iii"])
        ci, start, end, is_fuzzy = _locate_evidence("eee fff", 1, chunks)
        assert ci == 1
        assert chunks[ci].text[start:end] == "eee fff"

    def test_wrong_hint_found_elsewhere(self):
        chunks = self._make_chunks(["aaa bbb ccc", "ddd eee fff", "ggg hhh iii"])
        ci, start, end, is_fuzzy = _locate_evidence("ggg hhh", 0, chunks)
        assert ci == 2
        assert start < end

    def test_not_found_anywhere(self):
        chunks = self._make_chunks(["aaa bbb", "ccc ddd"])
        ci, start, end, is_fuzzy = _locate_evidence("zzz yyy xxx www", 0, chunks)
        assert start == 0
        assert end == 0

    def test_hint_out_of_range(self):
        chunks = self._make_chunks(["aaa bbb ccc"])
        ci, start, end, is_fuzzy = _locate_evidence("aaa bbb", 99, chunks)
        assert ci == 0
        assert chunks[ci].text[start:end] == "aaa bbb"


class TestPrepareAnnotationData:
    @pytest.fixture()
    def source_file(self, tmp_path: Path) -> Path:
        text = textwrap.dedent("""\
            Section 1: Introduction

            AI systems must be transparent and accountable.
            Organizations should ensure fairness in all AI deployments.

            Section 2: Data Privacy

            Personal data must be protected according to regulations.
            Data collection should be minimized to what is necessary.

            Section 3: Safety

            AI systems should be tested for safety before deployment.
            Continuous monitoring is required for production systems.
        """)
        p = tmp_path / "policy.txt"
        p.write_text(text)
        return p

    @pytest.fixture()
    def extraction_data(self) -> dict:
        return {
            "risks": [
                {
                    "risk_id": "risk-transparency",
                    "risk_name": "Lack of Transparency",
                    "risk_description": "AI systems not transparent",
                    "taxonomy": "test-taxonomy",
                    "confidence": 0.95,
                    "grounding_confidence": "high",
                    "evidence": [
                        {
                            "text": "AI systems must be transparent and accountable.",
                            "document": "policy.txt",
                            "chunk_index": 0,
                        }
                    ],
                    "threat": "Opaque AI decisions",
                    "threat_source": "Complex models",
                    "vulnerability": "No explainability",
                    "consequence": "Loss of trust",
                    "impact": "Regulatory action",
                },
                {
                    "risk_id": "risk-privacy",
                    "risk_name": "Privacy Violation",
                    "risk_description": "Data privacy not ensured",
                    "taxonomy": "test-taxonomy",
                    "confidence": 0.88,
                    "grounding_confidence": "medium",
                    "evidence": [
                        {
                            "text": "Personal data must be protected according to regulations.",
                            "document": "policy.txt",
                            "chunk_index": 0,
                        }
                    ],
                    "threat": None,
                    "threat_source": None,
                    "vulnerability": None,
                    "consequence": None,
                    "impact": None,
                },
            ],
            "metadata": {"model": "test-model", "policy": "test-policy"},
        }

    def test_basic_output_structure(self, source_file: Path, extraction_data: dict):
        result = prepare_annotation_data(extraction_data, source_file)

        assert "chunks" in result
        assert "summary" in result
        assert "metadata" in result
        assert len(result["chunks"]) > 0

    def test_summary_counts(self, source_file: Path, extraction_data: dict):
        result = prepare_annotation_data(extraction_data, source_file)
        summary = result["summary"]

        assert summary["total_risks"] == 2
        assert summary["total_evidence_spans"] == 2
        assert summary["matched_spans"] + summary["unmatched_spans"] == 2

    def test_annotations_have_required_fields(self, source_file: Path, extraction_data: dict):
        result = prepare_annotation_data(extraction_data, source_file)

        for chunk in result["chunks"]:
            for ann in chunk["annotations"]:
                assert "start" in ann
                assert "end" in ann
                assert "evidence_text" in ann
                assert "matched_in_text" in ann
                assert "risk_id" in ann
                assert "risk_name" in ann
                assert "taxonomy" in ann
                assert "confidence" in ann
                assert "causal_chain" in ann

    def test_causal_chain_populated(self, source_file: Path, extraction_data: dict):
        result = prepare_annotation_data(extraction_data, source_file)

        all_annotations = [a for c in result["chunks"] for a in c["annotations"]]
        transparency = [a for a in all_annotations if a["risk_id"] == "risk-transparency"]
        assert len(transparency) == 1
        cc = transparency[0]["causal_chain"]
        assert cc["threat"] == "Opaque AI decisions"
        assert cc["impact"] == "Regulatory action"

    def test_causal_chain_none_fields(self, source_file: Path, extraction_data: dict):
        result = prepare_annotation_data(extraction_data, source_file)

        all_annotations = [a for c in result["chunks"] for a in c["annotations"]]
        privacy = [a for a in all_annotations if a["risk_id"] == "risk-privacy"]
        assert len(privacy) == 1
        cc = privacy[0]["causal_chain"]
        assert cc["threat"] is None
        assert cc["impact"] is None

    def test_metadata_passed_through(self, source_file: Path, extraction_data: dict):
        result = prepare_annotation_data(extraction_data, source_file)
        assert result["metadata"]["model"] == "test-model"

    def test_zero_risks(self, source_file: Path):
        result = prepare_annotation_data({"risks": [], "metadata": {}}, source_file)
        assert result["summary"]["total_risks"] == 0
        assert result["summary"]["total_evidence_spans"] == 0
        assert all(len(c["annotations"]) == 0 for c in result["chunks"])

    def test_chunk_fields(self, source_file: Path, extraction_data: dict):
        result = prepare_annotation_data(extraction_data, source_file)
        for chunk in result["chunks"]:
            assert "index" in chunk
            assert "text" in chunk
            assert "page" in chunk
            assert "section" in chunk
            assert "annotations" in chunk
            assert isinstance(chunk["text"], str)
            assert len(chunk["text"]) > 0

    def test_annotations_sorted_by_start(self, source_file: Path):
        extraction_data = {
            "risks": [
                {
                    "risk_id": f"risk-{i}",
                    "risk_name": f"Risk {i}",
                    "risk_description": "",
                    "taxonomy": "",
                    "confidence": 0.9,
                    "grounding_confidence": "high",
                    "evidence": [{"text": text, "document": "policy.txt", "chunk_index": 0}],
                }
                for i, text in enumerate(
                    [
                        "Organizations should ensure fairness",
                        "AI systems must be transparent",
                    ]
                )
            ],
            "metadata": {},
        }

        result = prepare_annotation_data(extraction_data, source_file)
        for chunk in result["chunks"]:
            if len(chunk["annotations"]) > 1:
                starts = [a["start"] for a in chunk["annotations"]]
                assert starts == sorted(starts)

    def test_overlapping_spans(self, source_file: Path):
        extraction_data = {
            "risks": [
                {
                    "risk_id": "risk-a",
                    "risk_name": "Risk A",
                    "risk_description": "",
                    "taxonomy": "",
                    "confidence": 0.9,
                    "grounding_confidence": "high",
                    "evidence": [
                        {
                            "text": "AI systems must be transparent and accountable.",
                            "document": "policy.txt",
                            "chunk_index": 0,
                        }
                    ],
                },
                {
                    "risk_id": "risk-b",
                    "risk_name": "Risk B",
                    "risk_description": "",
                    "taxonomy": "",
                    "confidence": 0.85,
                    "grounding_confidence": "medium",
                    "evidence": [
                        {
                            "text": "transparent and accountable.",
                            "document": "policy.txt",
                            "chunk_index": 0,
                        }
                    ],
                },
            ],
            "metadata": {},
        }

        result = prepare_annotation_data(extraction_data, source_file)
        all_annotations = [a for c in result["chunks"] for a in c["annotations"]]
        matched = [a for a in all_annotations if a["matched_in_text"]]
        assert len(matched) == 2

    def test_unmatched_span(self, source_file: Path):
        extraction_data = {
            "risks": [
                {
                    "risk_id": "risk-missing",
                    "risk_name": "Missing",
                    "risk_description": "",
                    "taxonomy": "",
                    "confidence": 0.5,
                    "grounding_confidence": "low",
                    "evidence": [
                        {
                            "text": "This text does not exist anywhere in the document at all whatsoever.",
                            "document": "policy.txt",
                            "chunk_index": 0,
                        }
                    ],
                }
            ],
            "metadata": {},
        }

        result = prepare_annotation_data(extraction_data, source_file)
        assert result["summary"]["unmatched_spans"] == 1
        all_annotations = [a for c in result["chunks"] for a in c["annotations"]]
        assert len(all_annotations) == 1
        assert not all_annotations[0]["matched_in_text"]
