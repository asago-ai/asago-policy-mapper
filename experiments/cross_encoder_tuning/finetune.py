"""Fine-tune a cross-encoder on the risk-policy relevance dataset.

Uses sentence-transformers CrossEncoder training API. Trains on train.jsonl,
evaluates on eval.jsonl after each epoch.

Usage:
    uv run python -m experiments.cross_encoder_tuning.finetune \
        --base-model cross-encoder/ms-marco-MiniLM-L-12-v2 \
        --dataset-dir experiments/cross_encoder_tuning/datasets \
        --output-dir experiments/cross_encoder_tuning/models/risk-reranker \
        [--epochs 5] [--batch-size 16] [--lr 2e-5]
"""

from __future__ import annotations

import argparse
import json
import logging
import math
from pathlib import Path

import numpy as np
import torch
from sentence_transformers import CrossEncoder, InputExample
from sentence_transformers.cross_encoder.evaluation import (
    CEBinaryClassificationEvaluator,
)
from torch.utils.data import DataLoader

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)


def load_examples(path: Path) -> list[InputExample]:
    examples = []
    with open(path) as f:
        for line in f:
            d = json.loads(line)
            examples.append(
                InputExample(
                    texts=[d["sentence1"], d["sentence2"]],
                    label=float(d["label"]),
                )
            )
    return examples


def load_eval_data(path: Path) -> tuple[list[list[str]], list[int]]:
    sentences_pairs = []
    labels = []
    with open(path) as f:
        for line in f:
            d = json.loads(line)
            sentences_pairs.append([d["sentence1"], d["sentence2"]])
            labels.append(d["label"])
    return sentences_pairs, labels


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-model", default="cross-encoder/ms-marco-MiniLM-L-12-v2")
    parser.add_argument("--dataset-dir", type=Path, default=Path("risk-landscaper/datasets/cross-encoder"))
    parser.add_argument("--output-dir", type=Path, default=Path("risk-landscaper/models/risk-reranker"))
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=2e-5)
    parser.add_argument("--warmup-ratio", type=float, default=0.1)
    parser.add_argument("--eval-steps", type=int, default=0, help="Eval every N steps (0=end of epoch)")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    train_path = args.dataset_dir / "train.jsonl"
    eval_path = args.dataset_dir / "eval.jsonl"

    logger.info("Loading training data from %s", train_path)
    train_examples = load_examples(train_path)
    logger.info("Training examples: %d", len(train_examples))

    logger.info("Loading eval data from %s", eval_path)
    eval_sentences, eval_labels = load_eval_data(eval_path)
    logger.info("Eval examples: %d", len(eval_labels))

    logger.info("Loading base model: %s", args.base_model)
    model = CrossEncoder(
        args.base_model,
        num_labels=1,
        automodel_args={"ignore_mismatched_sizes": True},
    )

    train_dataloader = DataLoader(
        train_examples,
        shuffle=True,
        batch_size=args.batch_size,
    )

    evaluator = CEBinaryClassificationEvaluator(
        sentence_pairs=eval_sentences,
        labels=eval_labels,
        name="risk-policy-eval",
    )

    total_steps = len(train_dataloader) * args.epochs
    warmup_steps = math.ceil(total_steps * args.warmup_ratio)
    eval_steps = args.eval_steps if args.eval_steps > 0 else len(train_dataloader)

    logger.info("Training config:")
    logger.info("  Base model: %s", args.base_model)
    logger.info("  Epochs: %d", args.epochs)
    logger.info("  Batch size: %d", args.batch_size)
    logger.info("  Learning rate: %s", args.lr)
    logger.info("  Total steps: %d", total_steps)
    logger.info("  Warmup steps: %d", warmup_steps)
    logger.info("  Eval every: %d steps", eval_steps)
    logger.info("  Output: %s", args.output_dir)

    model.fit(
        train_dataloader=train_dataloader,
        evaluator=evaluator,
        epochs=args.epochs,
        warmup_steps=warmup_steps,
        evaluation_steps=eval_steps,
        output_path=str(args.output_dir),
        optimizer_params={"lr": args.lr},
        save_best_model=True,
    )

    logger.info("Training complete. Best model saved to %s", args.output_dir)

    config = {
        "base_model": args.base_model,
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "learning_rate": args.lr,
        "warmup_ratio": args.warmup_ratio,
        "train_examples": len(train_examples),
        "eval_examples": len(eval_labels),
        "total_steps": total_steps,
    }
    (args.output_dir / "training_config.json").write_text(json.dumps(config, indent=2))


if __name__ == "__main__":
    main()
