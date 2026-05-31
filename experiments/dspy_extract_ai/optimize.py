#!/usr/bin/env python3
"""Run DSPy + GEPA optimization for AI system extraction.

Usage:
    uv run python -m experiments.dspy_extract_ai.optimize --base-url http://localhost:8000/v1 --model gemma-4-26b-a4b-it
    uv run python -m experiments.dspy_extract_ai.optimize --eval-only --base-url http://localhost:8000/v1 --model gemma-4-26b-a4b-it
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import dspy

from experiments.dspy_extract_ai.dataset import load_dataset
from experiments.dspy_extract_ai.metric import ai_extraction_metric
from experiments.dspy_extract_ai.module import AIExtractor

_RESULTS_DIR = Path(__file__).parent / "results"


def _configure_lm(args) -> dspy.LM:
    model_id = f"openai/{args.model}"
    lm = dspy.LM(
        model=model_id,
        api_base=args.base_url,
        api_key=args.api_key,
        temperature=0.3,
        max_tokens=8192,
    )
    dspy.configure(lm=lm)
    return lm


def _score_value(result) -> float:
    if isinstance(result, (int, float)):
        return float(result)
    if hasattr(result, "score"):
        return float(result.score)
    return float(result)


def _run_baseline(val: list[dspy.Example]) -> tuple[AIExtractor, float]:
    program = AIExtractor()
    evaluate = dspy.Evaluate(
        devset=val,
        metric=ai_extraction_metric,
        num_threads=1,
        display_progress=True,
        display_table=0,
    )
    result = evaluate(program)
    return program, _score_value(result)


def _run_gepa(
    program: AIExtractor,
    train: list[dspy.Example],
    val: list[dspy.Example],
    lm: dspy.LM,
    auto: str,
) -> tuple[AIExtractor, float]:
    optimizer = dspy.GEPA(
        metric=ai_extraction_metric,
        auto=auto,
        reflection_lm=lm,
        track_stats=True,
    )
    optimized = optimizer.compile(program, trainset=train, valset=val)

    evaluate = dspy.Evaluate(
        devset=val,
        metric=ai_extraction_metric,
        num_threads=1,
        display_progress=True,
        display_table=0,
    )
    result = evaluate(optimized)
    return optimized, _score_value(result)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base-url", default=os.environ.get("REFINER_BASE_URL"), help="LLM API base URL")
    parser.add_argument("--model", default=os.environ.get("REFINER_MODEL"), help="Model name")
    parser.add_argument("--api-key", default=os.environ.get("REFINER_API_KEY", "none"), help="API key")
    parser.add_argument("--auto", default="light", choices=["light", "medium", "heavy"], help="GEPA budget preset")
    parser.add_argument("--eval-only", action="store_true", help="Only run baseline evaluation")
    args = parser.parse_args()

    if not args.base_url:
        parser.error("--base-url or REFINER_BASE_URL required")
    if not args.model:
        parser.error("--model or REFINER_MODEL required")

    print(f"Model: {args.model}")
    print(f"Base URL: {args.base_url}")
    print()

    lm = _configure_lm(args)

    print("Loading dataset...")
    train, val = load_dataset()
    print(f"  Train: {len(train)} examples")
    print(f"  Val: {len(val)} examples")
    for ex in train:
        n_systems = len(ex.expected_systems)
        doc_len = len(ex.document_text)
        print(f"    - {n_systems} AI systems, {doc_len} chars")
    print()

    print("Running baseline evaluation...")
    program, baseline_score = _run_baseline(val)
    print(f"Baseline F1: {baseline_score:.1f}%")
    print()

    if args.eval_only:
        print("Done (eval-only mode).")
        return

    print(f"Running GEPA optimization (auto={args.auto})...")
    optimized, optimized_score = _run_gepa(program, train, val, lm, args.auto)
    print(f"Optimized F1: {optimized_score:.1f}%")
    improvement = optimized_score - baseline_score
    print(f"Improvement: {improvement:+.1f}%")
    print()

    print("Optimized instruction:")
    for name, pred in optimized.named_predictors():
        print(f"  [{name}]")
        print(f"  {pred.signature.instructions}")
        print()

    _RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_path = _RESULTS_DIR / f"run_{timestamp}.json"
    result = {
        "model": args.model,
        "auto": args.auto,
        "baseline_f1": baseline_score,
        "optimized_f1": optimized_score,
        "improvement": improvement,
        "timestamp": timestamp,
        "optimized_instructions": {
            name: pred.signature.instructions
            for name, pred in optimized.named_predictors()
        },
    }
    result_path.write_text(json.dumps(result, indent=2))
    print(f"Results saved to {result_path}")

    program_path = _RESULTS_DIR / f"program_{timestamp}.json"
    optimized.save(str(program_path))
    print(f"Optimized program saved to {program_path}")


if __name__ == "__main__":
    main()
