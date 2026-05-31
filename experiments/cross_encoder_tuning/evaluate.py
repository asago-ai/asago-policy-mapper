"""Evaluate a cross-encoder model on the cross-encoder dataset.

Scores all pairs in eval.jsonl, applies sigmoid normalization (matching
RiskIndex.rerank()), and computes classification metrics at various
thresholds.

Usage:
    uv run python -m experiments.cross_encoder_tuning.evaluate \
        --model cross-encoder/ms-marco-MiniLM-L-12-v2 \
        --dataset-dir experiments/cross_encoder_tuning/datasets \
        [--split eval]
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
from sentence_transformers import CrossEncoder


def load_pairs(path: Path) -> list[dict]:
    with open(path) as f:
        return [json.loads(line) for line in f]


def score_pairs(model: CrossEncoder, pairs: list[dict]) -> np.ndarray:
    inputs = [(p["sentence1"], p["sentence2"]) for p in pairs]
    raw_scores = model.predict(inputs, show_progress_bar=True, batch_size=64)
    raw_scores = np.array(raw_scores)
    if raw_scores.ndim == 2:
        # NLI model: columns are [contradiction, neutral, entailment]
        # Use softmax entailment probability as score
        exp_scores = np.exp(raw_scores - np.max(raw_scores, axis=1, keepdims=True))
        softmax = exp_scores / exp_scores.sum(axis=1, keepdims=True)
        return softmax[:, -1]  # entailment column
    return 1.0 / (1.0 + np.exp(-raw_scores))


def compute_metrics(labels: np.ndarray, scores: np.ndarray, threshold: float) -> dict:
    predicted = (scores >= threshold).astype(int)
    tp = int(np.sum((predicted == 1) & (labels == 1)))
    fp = int(np.sum((predicted == 1) & (labels == 0)))
    fn = int(np.sum((predicted == 0) & (labels == 1)))
    tn = int(np.sum((predicted == 0) & (labels == 0)))

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "threshold": threshold,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "predicted_pos": tp + fp,
        "predicted_neg": tn + fn,
    }


def compute_auc(labels: np.ndarray, scores: np.ndarray) -> float:
    order = np.argsort(-scores)
    sorted_labels = labels[order]
    n_pos = int(np.sum(labels))
    n_neg = len(labels) - n_pos
    if n_pos == 0 or n_neg == 0:
        return 0.0
    tp_cumsum = np.cumsum(sorted_labels)
    fp_cumsum = np.arange(1, len(labels) + 1) - tp_cumsum
    tpr = tp_cumsum / n_pos
    fpr = fp_cumsum / n_neg
    trapz = getattr(np, "trapezoid", None) or np.trapz
    auc = float(trapz(tpr, fpr))
    return round(auc, 4)


def per_pair_type_breakdown(pairs: list[dict], scores: np.ndarray, threshold: float) -> dict:
    results = {}
    for pair_type in ["positive", "hard_negative", "easy_negative"]:
        mask = np.array([p["metadata"]["pair_type"] == pair_type for p in pairs])
        if not np.any(mask):
            continue
        type_scores = scores[mask]
        type_labels = np.array([p["label"] for p in pairs])[mask]
        predicted = (type_scores >= threshold).astype(int)
        correct = int(np.sum(predicted == type_labels))
        results[pair_type] = {
            "count": int(np.sum(mask)),
            "accuracy": round(correct / int(np.sum(mask)), 4),
            "mean_score": round(float(np.mean(type_scores)), 4),
            "median_score": round(float(np.median(type_scores)), 4),
            "std_score": round(float(np.std(type_scores)), 4),
        }
    return results


def per_policy_breakdown(pairs: list[dict], labels: np.ndarray, scores: np.ndarray, threshold: float) -> dict:
    results = {}
    policies = sorted(set(p["metadata"]["policy"] for p in pairs))
    for policy in policies:
        mask = np.array([p["metadata"]["policy"] == policy for p in pairs])
        m = compute_metrics(labels[mask], scores[mask], threshold)
        results[policy] = {
            "precision": m["precision"],
            "recall": m["recall"],
            "f1": m["f1"],
            "total": int(np.sum(mask)),
            "positives": int(np.sum(labels[mask])),
        }
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--dataset-dir", type=Path, default=Path("risk-landscaper/datasets/cross-encoder"))
    parser.add_argument("--split", default="eval", choices=["train", "eval"])
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    dataset_path = args.dataset_dir / f"{args.split}.jsonl"
    print(f"Model: {args.model}")
    print(f"Dataset: {dataset_path}")

    pairs = load_pairs(dataset_path)
    labels = np.array([p["label"] for p in pairs])
    print(f"Pairs: {len(pairs)} ({int(np.sum(labels))} positive, {int(np.sum(1-labels))} negative)")

    print(f"\nLoading model...")
    model = CrossEncoder(args.model)

    print(f"Scoring {len(pairs)} pairs...")
    t0 = time.time()
    scores = score_pairs(model, pairs)
    elapsed = time.time() - t0
    print(f"Scoring done in {elapsed:.1f}s ({len(pairs)/elapsed:.0f} pairs/sec)")

    auc = compute_auc(labels, scores)
    print(f"\nAUC-ROC: {auc}")

    thresholds = [0.15, 0.3, 0.5, 0.7, 0.85, 0.9, 0.95]
    print(f"\n{'Thresh':>8s} {'Prec':>8s} {'Recall':>8s} {'F1':>8s} {'TP':>6s} {'FP':>6s} {'FN':>6s} {'TN':>6s}")
    print("-" * 65)
    all_metrics = []
    for t in thresholds:
        m = compute_metrics(labels, scores, t)
        all_metrics.append(m)
        print(f"{t:8.2f} {m['precision']:8.4f} {m['recall']:8.4f} {m['f1']:8.4f} {m['tp']:6d} {m['fp']:6d} {m['fn']:6d} {m['tn']:6d}")

    best_threshold = thresholds[0]
    best_f1 = 0
    for t in np.arange(0.05, 0.99, 0.01):
        m = compute_metrics(labels, scores, t)
        if m["f1"] > best_f1:
            best_f1 = m["f1"]
            best_threshold = round(float(t), 2)
    best_m = compute_metrics(labels, scores, best_threshold)
    print(f"\nBest F1: {best_f1:.4f} at threshold {best_threshold}")
    print(f"  Precision: {best_m['precision']:.4f}, Recall: {best_m['recall']:.4f}")

    print(f"\nScore distribution by pair type (at pipeline threshold 0.7):")
    breakdown = per_pair_type_breakdown(pairs, scores, 0.7)
    for pt, stats in breakdown.items():
        print(f"  {pt:20s}: mean={stats['mean_score']:.4f} median={stats['median_score']:.4f} std={stats['std_score']:.4f} accuracy={stats['accuracy']:.4f} (n={stats['count']})")

    print(f"\nPer-policy breakdown (at threshold {best_threshold}):")
    print(f"  {'Policy':25s} {'Prec':>8s} {'Recall':>8s} {'F1':>8s} {'Pos':>6s} {'Total':>6s}")
    policy_breakdown = per_policy_breakdown(pairs, labels, scores, best_threshold)
    for policy, stats in sorted(policy_breakdown.items()):
        print(f"  {policy:25s} {stats['precision']:8.4f} {stats['recall']:8.4f} {stats['f1']:8.4f} {stats['positives']:6d} {stats['total']:6d}")

    if args.output:
        result = {
            "model": args.model,
            "split": args.split,
            "total_pairs": len(pairs),
            "auc_roc": auc,
            "best_threshold": best_threshold,
            "best_f1": best_f1,
            "metrics_at_thresholds": all_metrics,
            "pair_type_breakdown": breakdown,
            "per_policy": policy_breakdown,
            "scoring_time_s": round(elapsed, 1),
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2))
        print(f"\nResults saved to {args.output}")


if __name__ == "__main__":
    main()
