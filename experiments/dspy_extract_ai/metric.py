"""GEPA-compatible metric for AI system extraction with rich feedback."""

from __future__ import annotations

import re

import dspy

DEFINITIONAL_AI_CONCEPTS = {
    "neural network", "neural networks",
    "computer vision",
    "natural language processing", "nlp",
    "transformer model", "transformer models",
    "generative ai", "generative artificial intelligence",
    "distributed artificial intelligence",
    "robotic process automation", "rpa",
    "machine learning", "deep learning",
    "reinforcement learning", "supervised learning", "unsupervised learning",
    "convolutional neural network", "cnn",
    "recurrent neural network", "rnn",
    "large language model", "large language models", "llm", "llms",
    "expert system", "expert systems",
    "knowledge graph", "knowledge graphs",
    "open source ai", "open source ai systems",
    "artificial intelligence",
    "ai system", "ai systems",
    "ai tool", "ai tools",
    "ai technology", "ai technologies",
}

_STOPWORDS = frozenset({
    "a", "an", "the", "of", "for", "in", "on", "to", "and", "or",
    "by", "with", "is", "are", "be", "that", "this", "from", "at", "as",
})

_WORD_RE = re.compile(r"[a-z0-9]+")


def _content_tokens(name: str) -> set[str]:
    tokens = set(_WORD_RE.findall(name.lower()))
    return tokens - _STOPWORDS


def _token_overlap(a: str, b: str) -> float:
    ta = _content_tokens(a)
    tb = _content_tokens(b)
    if not ta or not tb:
        return 0.0
    intersection = ta & tb
    return len(intersection) / max(len(ta), len(tb))


def _match_systems(
    predicted: list[dict],
    expected: list[dict],
    threshold: float = 0.6,
) -> tuple[list[tuple[dict, dict]], list[dict], list[dict]]:
    matched = []
    unmatched_pred = list(predicted)
    missed = []

    for gt in expected:
        gt_name = gt["name"].lower().strip()
        best_score = 0.0
        best_idx = -1

        for i, pred in enumerate(unmatched_pred):
            pred_name = pred["name"].lower().strip()
            if pred_name == gt_name:
                best_score = 1.0
                best_idx = i
                break
            score = _token_overlap(gt_name, pred_name)
            if score > best_score:
                best_score = score
                best_idx = i

        if best_score >= threshold and best_idx >= 0:
            matched.append((gt, unmatched_pred.pop(best_idx)))
        else:
            missed.append(gt)

    return matched, missed, unmatched_pred


def _filter_definitional(systems: list[dict]) -> list[dict]:
    return [s for s in systems if s["name"].lower().strip() not in DEFINITIONAL_AI_CONCEPTS]


def ai_extraction_metric(example, prediction, trace=None, pred_name=None, pred_trace=None):
    expected = example.expected_systems

    try:
        extraction = prediction.extraction
        if hasattr(extraction, "systems"):
            predicted = [s.model_dump() if hasattr(s, "model_dump") else s for s in extraction.systems]
        else:
            predicted = []
    except (AttributeError, TypeError):
        predicted = []

    predicted = _filter_definitional(predicted)

    matched, missed, spurious = _match_systems(predicted, expected)

    n_expected = len(expected)
    n_predicted = len(predicted)
    n_matched = len(matched)

    precision = n_matched / n_predicted if n_predicted > 0 else (1.0 if n_expected == 0 else 0.0)
    recall = n_matched / n_expected if n_expected > 0 else 1.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    if pred_name is None:
        return f1

    parts = [f"F1={f1:.2f} (P={precision:.2f}, R={recall:.2f}). Matched {n_matched}/{n_expected} expected systems."]

    if missed:
        missed_strs = [f'"{m["name"]}" ({m.get("description", "")[:60]})' for m in missed]
        parts.append(f"Missed: {'; '.join(missed_strs)}.")

    if spurious:
        spurious_strs = [f'"{s["name"]}"' for s in spurious]
        parts.append(f"Spurious (not in ground truth): {', '.join(spurious_strs)}.")

    ds_mismatches = []
    for gt, pred in matched:
        gt_ds = gt.get("deployment_status", "")
        pred_ds = pred.get("deployment_status", "")
        if gt_ds and pred_ds and gt_ds != pred_ds:
            ds_mismatches.append(f'"{gt["name"]}": expected "{gt_ds}", got "{pred_ds}"')
    if ds_mismatches:
        parts.append(f"Deployment status mismatches: {'; '.join(ds_mismatches)}.")

    feedback = " ".join(parts)
    return dspy.Prediction(score=f1, feedback=feedback)
