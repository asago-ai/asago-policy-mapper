from __future__ import annotations

import difflib
import re
import unicodedata
from pathlib import Path

from asago_policy_mapper.extract.parse import Chunk, chunk_documents, parse_document


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("’", "'").replace("‘", "'")
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("—", "-").replace("–", "-")
    text = text.replace(" ", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _find_span_in_chunk(
    evidence_text: str,
    chunk_text: str,
    fuzzy_threshold: float = 0.8,
) -> tuple[int, int, bool]:
    """Locate evidence_text within chunk_text, return (start, end, is_fuzzy).

    Tries exact substring first, then normalized, then fuzzy via
    SequenceMatcher.find_longest_match. Returns (0, 0, False) on failure.
    """
    if evidence_text in chunk_text:
        start = chunk_text.index(evidence_text)
        return start, start + len(evidence_text), False

    norm_ev = _normalize(evidence_text)
    norm_chunk = _normalize(chunk_text)

    if norm_ev in norm_chunk:
        idx = norm_chunk.index(norm_ev)
        start, end = _map_normalized_offsets(chunk_text, norm_chunk, idx, idx + len(norm_ev))
        return start, end, False

    sm = difflib.SequenceMatcher(None, norm_chunk, norm_ev, autojunk=False)
    ratio = sm.ratio()

    if ratio >= fuzzy_threshold:
        blocks = sm.get_matching_blocks()
        if blocks:
            first_a = blocks[0].a
            last = blocks[-2] if len(blocks) > 1 else blocks[0]
            last_a_end = last.a + last.size
            start, end = _map_normalized_offsets(chunk_text, norm_chunk, first_a, last_a_end)
            return start, end, True

    return 0, 0, False


def _map_normalized_offsets(original: str, normalized: str, norm_start: int, norm_end: int) -> tuple[int, int]:
    """Map character offsets in normalized text back to the original text.

    Walks both strings in parallel, tracking how positions correspond.
    Falls back to proportional mapping if the walk fails.
    """
    orig_start = 0
    found_start = False

    norm_idx = 0
    orig_idx = 0

    while norm_idx < len(normalized) and orig_idx < len(original):
        if norm_idx == norm_start and not found_start:
            orig_start = orig_idx
            found_start = True
        if norm_idx == norm_end:
            orig_end = orig_idx
            return orig_start, orig_end

        norm_char = normalized[norm_idx]
        orig_char = original[orig_idx]

        if norm_char == orig_char:
            norm_idx += 1
            orig_idx += 1
        elif orig_char in (" ", "\t", "\n", "\r", " "):
            orig_idx += 1
        else:
            norm_idx += 1
            orig_idx += 1

    if not found_start:
        ratio = len(original) / max(len(normalized), 1)
        orig_start = int(norm_start * ratio)
    orig_end = min(len(original), orig_idx)

    return orig_start, orig_end


def _locate_evidence(
    evidence_text: str,
    chunk_index: int,
    chunks: list[Chunk],
    fuzzy_threshold: float = 0.8,
) -> tuple[int, int, int, bool]:
    """Find evidence_text in chunks, return (chunk_index, start, end, is_fuzzy).

    Strategy: try the hinted chunk_index first, then scan all chunks.
    Returns (chunk_index, 0, 0, False) if not found anywhere.
    """
    if 0 <= chunk_index < len(chunks):
        start, end, is_fuzzy = _find_span_in_chunk(evidence_text, chunks[chunk_index].text, fuzzy_threshold)
        if end > start:
            return chunk_index, start, end, is_fuzzy

    for i, chunk in enumerate(chunks):
        if i == chunk_index:
            continue
        start, end, is_fuzzy = _find_span_in_chunk(evidence_text, chunk.text, fuzzy_threshold)
        if end > start:
            return i, start, end, is_fuzzy

    return chunk_index if 0 <= chunk_index < len(chunks) else 0, 0, 0, False


def _overlaps_existing(
    risk_id: str,
    chunk_index: int,
    start: int,
    end: int,
    seen: list[tuple[str, int, int, int]],
) -> bool:
    """Check if this span overlaps significantly with an existing span for the same risk."""
    for s_rid, s_ci, s_start, s_end in seen:
        if s_rid != risk_id or s_ci != chunk_index:
            continue
        overlap_start = max(start, s_start)
        overlap_end = min(end, s_end)
        if overlap_end <= overlap_start:
            continue
        overlap_len = overlap_end - overlap_start
        shorter_len = min(end - start, s_end - s_start)
        if shorter_len > 0 and overlap_len / shorter_len >= 0.5:
            return True
    return False


def prepare_annotation_data(
    extraction_data: dict,
    source_document: Path,
    ground_truth_path: Path | None = None,
    extracted_path: Path | None = None,
    ocr: bool = False,
    chunk_max_tokens: int = 512,
) -> dict:
    """Prepare annotation data for the document-centric HTML report.

    Re-parses the source document, locates evidence spans within chunk text,
    and returns a dict structured for template rendering. When ground_truth_path
    is provided, classifies each risk as matched/spurious and lists missed risks.
    """
    doc = parse_document(source_document, ocr=ocr)
    chunks = chunk_documents([doc], max_tokens=chunk_max_tokens)

    chunk_annotations: dict[int, list[dict]] = {i: [] for i in range(len(chunks))}
    seen_spans: list[tuple[str, int, int, int]] = []

    total_evidence = 0
    matched_spans = 0
    unmatched_spans = 0
    evidence_id_counter = 0

    for risk in extraction_data.get("risks", []):
        for ev in risk.get("evidence", []):
            total_evidence += 1
            ev_text = ev.get("text", "")
            hint_ci = ev.get("chunk_index", 0)

            ci, start, end, is_fuzzy = _locate_evidence(ev_text, hint_ci, chunks)

            if end > start:
                if _overlaps_existing(risk.get("risk_id", ""), ci, start, end, seen_spans):
                    continue
                seen_spans.append((risk.get("risk_id", ""), ci, start, end))
                matched_spans += 1
            else:
                unmatched_spans += 1

            evidence_id_counter += 1
            annotation = {
                "evidence_id": f"ev-{evidence_id_counter}",
                "start": start,
                "end": end,
                "evidence_text": ev_text,
                "matched_in_text": end > start,
                "is_fuzzy": is_fuzzy,
                "risk_id": risk.get("risk_id", ""),
                "risk_name": risk.get("risk_name", ""),
                "risk_description": risk.get("risk_description", ""),
                "taxonomy": risk.get("taxonomy", ""),
                "confidence": risk.get("confidence", 0.0),
                "grounding_confidence": risk.get("grounding_confidence", ""),
                "causal_chain": {
                    "threat": risk.get("threat"),
                    "threat_source": risk.get("threat_source"),
                    "vulnerability": risk.get("vulnerability"),
                    "consequence": risk.get("consequence"),
                    "impact": risk.get("impact"),
                },
            }
            chunk_annotations[ci].append(annotation)

    annotated_chunks = []
    for i, chunk in enumerate(chunks):
        annotations = sorted(chunk_annotations.get(i, []), key=lambda a: a["start"])
        annotated_chunks.append(
            {
                "index": chunk.index,
                "text": chunk.text,
                "page": chunk.page,
                "section": chunk.section,
                "annotations": annotations,
            }
        )

    total_risks = len(extraction_data.get("risks", []))

    eval_result = None
    missed_risks: list[dict] = []
    gt_matched_ids: set[str] = set()
    gt_spurious_ids: set[str] = set()
    gt_risk_ids: list[str] = []
    gt_filename = ""

    if ground_truth_path is not None and extracted_path is not None:
        import yaml as _yaml

        from asago_policy_mapper.evals.eval import evaluate_extraction

        eval_result = evaluate_extraction(
            ground_truth_path,
            extracted_path,
            policy_name=ground_truth_path.stem,
        )
        gt_matched_ids = set(eval_result.get("matched_ids", []))
        gt_spurious_ids = set(eval_result.get("spurious", []))
        gt_filename = ground_truth_path.name

        gt_data = _yaml.safe_load(ground_truth_path.read_text())
        if "risks" in gt_data:
            gt_risk_ids = [r["id"] for r in gt_data["risks"]]
        else:
            gt_risk_ids = [str(rid) for rid in gt_data.get("risk_ids", [])]

        for risk_id in eval_result.get("missing", []):
            missed_risks.append({"risk_id": risk_id})

        for chunk_data in annotated_chunks:
            for ann in chunk_data["annotations"]:  # type: ignore[attr-defined]
                rid = ann["risk_id"]
                if rid in gt_matched_ids:
                    ann["classification"] = "matched"
                elif rid in gt_spurious_ids:
                    ann["classification"] = "spurious"
                else:
                    ann["classification"] = None

    return {
        "chunks": annotated_chunks,
        "summary": {
            "total_risks": total_risks,
            "total_evidence_spans": total_evidence,
            "matched_spans": matched_spans,
            "unmatched_spans": unmatched_spans,
            "total_chunks": len(chunks),
            "gt_matched": len(gt_matched_ids) if eval_result else None,
            "gt_spurious": len(gt_spurious_ids) if eval_result else None,
            "gt_missing": len(missed_risks) if eval_result else None,
        },
        "eval": eval_result,
        "missed_risks": missed_risks,
        "gt_risk_ids": gt_risk_ids,
        "gt_filename": gt_filename,
        "source_document": source_document.name,
        "metadata": extraction_data.get("metadata", {}),
    }
