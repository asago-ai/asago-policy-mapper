"""Baseline eval + GEPA optimization for NIST risk classification.

Usage:
    uv run python -m experiments.dspy_classify \
        --base-url http://localhost:8000/v1 \
        --model gemma-4-26b-a4b-it \
        --run-dir risk-landscaper/extract-runs/risk-selected_20260528_211858 \
        --nexus-base-dir /path/to/ai-atlas-nexus \
        [--auto medium]
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

import dspy

from experiments.dspy_classify.dataset import load_dataset
from experiments.dspy_classify.metric import classify_metric
from experiments.dspy_classify.module import RiskClassifier

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

_OUTPUT_DIR = Path(__file__).resolve().parent / "runs"


def _score_value(result) -> float:
    if isinstance(result, (int, float)):
        return float(result)
    if hasattr(result, "score"):
        return float(result.score)
    return float(result)


def _run_baseline(
    program: RiskClassifier,
    val: list[dspy.Example],
) -> float:
    evaluate = dspy.Evaluate(
        devset=val,
        metric=classify_metric,
        num_threads=1,
        display_progress=True,
        display_table=0,
    )
    result = evaluate(program)
    return _score_value(result)


def _run_gepa(
    program: RiskClassifier,
    train: list[dspy.Example],
    val: list[dspy.Example],
    lm: dspy.LM,
    auto: str,
) -> tuple[RiskClassifier, float]:
    optimizer = dspy.GEPA(
        metric=classify_metric,
        auto=auto,
        reflection_lm=lm,
        track_stats=True,
    )
    optimized = optimizer.compile(program, trainset=train, valset=val)

    evaluate = dspy.Evaluate(
        devset=val,
        metric=classify_metric,
        num_threads=1,
        display_progress=True,
        display_table=0,
    )
    result = evaluate(optimized)
    return optimized, _score_value(result)


def main():
    parser = argparse.ArgumentParser(description="DSPy NIST classification optimization")
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--model", default="gemma-4-26b-a4b-it")
    parser.add_argument("--api-key", default="none")
    parser.add_argument("--run-dir", required=True, type=Path,
                        help="Battery run dir with extraction results (for extracted risks)")
    parser.add_argument("--nexus-base-dir", required=True)
    parser.add_argument("--auto", default="medium", choices=["light", "medium", "heavy"],
                        help="GEPA optimization level")
    parser.add_argument("--baseline-only", action="store_true",
                        help="Only run baseline evaluation, skip optimization")
    args = parser.parse_args()

    lm = dspy.LM(
        model=f"openai/{args.model}",
        api_base=args.base_url,
        api_key=args.api_key,
        temperature=0.0,
        max_tokens=4096,
    )
    dspy.configure(lm=lm, adapter=dspy.JSONAdapter())

    logger.info("Loading dataset...")
    train, val = load_dataset(
        run_dir=args.run_dir,
        nexus_base_dir=args.nexus_base_dir,
    )

    logger.info("Train: %d examples, Eval: %d examples", len(train), len(val))

    program = RiskClassifier()

    logger.info("Running baseline evaluation...")
    baseline_f1 = _run_baseline(program, val)
    logger.info("Baseline F1: %.4f", baseline_f1)

    if args.baseline_only:
        print(f"\nBaseline F1: {baseline_f1:.4f}")
        return

    logger.info("Running GEPA optimization (auto=%s)...", args.auto)
    optimized, optimized_f1 = _run_gepa(program, train, val, lm, args.auto)
    improvement = optimized_f1 - baseline_f1

    logger.info("Optimized F1: %.4f (improvement: %+.4f)", optimized_f1, improvement)

    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    optimized_instructions = ""
    try:
        for name, predictor in optimized.named_predictors():
            if hasattr(predictor, "signature") and hasattr(predictor.signature, "instructions"):
                optimized_instructions = predictor.signature.instructions
                break
    except Exception:
        pass

    result = {
        "model": args.model,
        "auto": args.auto,
        "baseline_f1": round(baseline_f1 * 100, 2),
        "optimized_f1": round(optimized_f1 * 100, 2),
        "improvement": round(improvement * 100, 2),
        "train_examples": len(train),
        "eval_examples": len(val),
        "optimized_instructions": optimized_instructions,
        "timestamp": timestamp,
    }

    result_path = _OUTPUT_DIR / f"run_{timestamp}.json"
    result_path.write_text(json.dumps(result, indent=2))
    logger.info("Results saved to %s", result_path)

    program_path = _OUTPUT_DIR / f"program_{timestamp}.json"
    optimized.save(str(program_path))
    logger.info("Program saved to %s", program_path)

    print(f"\n{'='*60}")
    print(f"Baseline F1: {baseline_f1*100:.2f}%")
    print(f"Optimized F1: {optimized_f1*100:.2f}%")
    print(f"Improvement: {improvement*100:+.2f}%")
    if optimized_instructions:
        print(f"\nOptimized instructions:\n{optimized_instructions}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
