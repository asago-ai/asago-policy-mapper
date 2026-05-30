from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import yaml


_TAXONOMY_PREFIXES = [
    ("ai-risk-taxonomy-", "ai-risk-taxonomy"),
    ("atlas-", "ibm-risk-atlas"),
    ("credo-", "credo-ucf"),
    ("mit-ai-risk-", "mit-ai-risk-repository"),
    ("mit-ai-causal-", "mit-ai-risk-repository-causal"),
    ("nist-", "nist-ai-rmf"),
    ("ail-", "ailuminate-v1.0"),
    ("granite-", "ibm-granite-guardian"),
    ("llm0", "owasp-llm-2.0"),
    ("shieldgemma-", "shieldgemma-taxonomy"),
]


def _infer_taxonomy(risk_id: str) -> str:
    for prefix, taxonomy in _TAXONOMY_PREFIXES:
        if risk_id.startswith(prefix):
            return taxonomy
    return "unknown"


def _build_taxonomy_map(ext_data: dict) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for r in ext_data.get("risks", []):
        rid = r.get("risk_id", "").strip()
        tax = r.get("taxonomy", "")
        if rid and tax:
            mapping[rid] = tax
    for fc in ext_data.get("grounding_filtered_candidates", []):
        rid = fc.get("risk_id", "").strip()
        tax = fc.get("taxonomy", "")
        if rid and tax and rid not in mapping:
            mapping[rid] = tax
    return mapping


def _compute_prf(matched: int, expected: int, extracted: int) -> tuple[float, float, float]:
    missing = expected - matched
    spurious = extracted - matched
    precision = matched / (matched + spurious) if matched + spurious > 0 else 0.0
    recall = matched / (matched + missing) if matched + missing > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall > 0 else 0.0
    return precision, recall, f1


def _per_taxonomy_breakdown(
    expected: set[str], extracted: set[str], matched: set[str], taxonomy_map: dict[str, str],
) -> dict[str, dict]:
    all_ids = expected | extracted
    by_tax: dict[str, dict[str, set[str]]] = defaultdict(lambda: {"expected": set(), "extracted": set(), "matched": set()})

    for rid in all_ids:
        tax = taxonomy_map.get(rid) or _infer_taxonomy(rid)
        if rid in expected:
            by_tax[tax]["expected"].add(rid)
        if rid in extracted:
            by_tax[tax]["extracted"].add(rid)
        if rid in matched:
            by_tax[tax]["matched"].add(rid)

    result = {}
    for tax in sorted(by_tax):
        t = by_tax[tax]
        n_exp = len(t["expected"])
        n_ext = len(t["extracted"])
        n_match = len(t["matched"])
        precision, recall, f1 = _compute_prf(n_match, n_exp, n_ext)
        result[tax] = {
            "expected": n_exp,
            "extracted": n_ext,
            "matched": n_match,
            "missing": sorted(t["expected"] - t["matched"]),
            "spurious": sorted(t["extracted"] - t["matched"]),
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1": round(f1, 3),
        }
    return result


def evaluate_extraction(
    ground_truth_path: Path,
    extracted_path: Path,
    policy_name: str = "",
    min_recall: float = 0.80,
    min_precision: float = 0.60,
) -> dict:
    gt_data = yaml.safe_load(ground_truth_path.read_text())
    if "risks" in gt_data:
        expected = {r["id"].strip() for r in gt_data["risks"]}
    else:
        expected = {str(rid).split()[0].strip() for rid in gt_data["risk_ids"]}

    ext_data = json.loads(extracted_path.read_text())
    extracted = {r["risk_id"].strip() for r in ext_data.get("risks", [])}

    matched = expected & extracted
    missing = sorted(expected - extracted)
    spurious = sorted(extracted - expected)

    precision = len(matched) / (len(matched) + len(spurious)) if matched or spurious else 0.0
    recall = len(matched) / (len(matched) + len(missing)) if matched or missing else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    taxonomy_map = _build_taxonomy_map(ext_data)
    per_taxonomy = _per_taxonomy_breakdown(expected, extracted, matched, taxonomy_map)

    return {
        "policy": policy_name,
        "total_expected": len(expected),
        "total_extracted": len(extracted),
        "matched": len(matched),
        "matched_ids": sorted(matched),
        "missing": missing,
        "spurious": spurious,
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "pass": recall >= min_recall and precision >= min_precision,
        "per_taxonomy": per_taxonomy,
    }
