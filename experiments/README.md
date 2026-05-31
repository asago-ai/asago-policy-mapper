# Experiments

DSPy prompt optimization experiments for the risk extraction pipeline. Each experiment optimizes a specific LLM stage using [DSPy GEPA](https://dspy.ai/) to find better instructions via reflection.

## Prerequisites

```bash
uv sync  # installs dspy>=2.6 from dev dependencies
```

You need:
- A running LLM endpoint (OpenAI-compatible API, e.g. vLLM serving Gemma)
- The [ai-atlas-nexus](https://github.com/ibm/ai-atlas-nexus) repo cloned locally
- For the judge experiment: no other dependencies
- For the classify experiment: a battery run directory with extraction results

## Experiments

### `dspy_judge/` — LLM Judge Prompt Optimization

Optimizes the judge that decides whether borderline candidates (cross-encoder score between 0.15–0.7) are relevant to a text chunk.

**Dataset:** 157 train / 207 eval examples built from enriched ground truth. Each example is a (chunk_text, candidate_risks) → expected_verdicts mapping. Hard negatives are mined using the cross-encoder: for each chunk, all non-GT risks are scored with ms-marco and the highest-scoring false matches become negatives.

**Build dataset + run optimization:**

```bash
uv run python -m experiments.dspy_judge \
  --base-url http://your-llm-endpoint/v1 \
  --model gemma-4-26b-a4b-it \
  --nexus-base-dir /path/to/ai-atlas-nexus \
  --auto medium
```

**Baseline only (no optimization):**

```bash
uv run python -m experiments.dspy_judge \
  --base-url http://your-llm-endpoint/v1 \
  --model gemma-4-26b-a4b-it \
  --nexus-base-dir /path/to/ai-atlas-nexus \
  --baseline-only
```

**Options:**
- `--auto light|medium|heavy` — GEPA optimization intensity (default: medium)
- `--baseline-only` — skip optimization, just evaluate the current prompt

**Output:** Results and optimized program saved to `experiments/dspy_judge/runs/`.

**Applying results:** Extract the `optimized_instructions` from the run JSON and update `risk-landscaper/src/risk_landscaper/templates/prompts/judge_risk_system.j2`. The user prompt template (`judge_risk_user.j2`) may also need updating if the optimized instructions assume a different input format.

**Time:** ~30–60 min depending on endpoint speed (207 eval calls for baseline + GEPA iterations over 157 train examples + final eval pass).

**Notes:**
- Dataset building takes ~5 min (parses all 20 policy documents + scores ~545 risks per chunk with the cross-encoder)
- The cross-encoder model (`cross-encoder/ms-marco-MiniLM-L-12-v2`) is downloaded automatically on first run (~130MB)

---

### `dspy_classify/` — NIST Classification Prompt Optimization

Optimizes the post-retrieval classification that maps extracted risks to NIST AI RMF categories. This stage runs once per document after grounding, classifying which of the 12 NIST risk categories are supported by the specific risks already found.

**Dataset:** 10 train / 10 eval examples (one per policy). Each example contains the extracted risks from a baseline pipeline run and the expected NIST verdicts from ground truth. Requires a battery run directory.

**Run optimization:**

```bash
uv run python -m experiments.dspy_classify \
  --base-url http://your-llm-endpoint/v1 \
  --model gemma-4-26b-a4b-it \
  --run-dir risk-landscaper/extract-runs/risk-selected_YYYYMMDD_HHMMSS \
  --nexus-base-dir /path/to/ai-atlas-nexus \
  --auto medium
```

**Getting a run directory:** You need extraction results from a battery run. Run the battery first:

```bash
uv run python risk-landscaper/run_extract_battery.py batteries/risk-selected.yaml \
  --base-url http://your-llm-endpoint/v1 \
  --classify-taxonomies ""  # disable classification to get pure retrieval results
```

Then pass the output directory (e.g. `risk-landscaper/extract-runs/risk-selected_20260528_211858`) as `--run-dir`.

**Options:**
- `--auto light|medium|heavy` — GEPA optimization intensity
- `--baseline-only` — skip optimization
- `--run-dir` — battery run directory with per-policy `risk-extraction.json` files

**Output:** Results and optimized program saved to `experiments/dspy_classify/runs/`.

**Applying results:** Extract `optimized_instructions` and update `risk-landscaper/src/risk_landscaper/templates/prompts/classify_risks_system.j2`.

**Time:** ~10–20 min (only 10+10 examples, each is one LLM call).

---

### `dspy_extract_ai/` — KG AI System Extraction (separate experiment)

Optimizes AI system extraction for the knowledge graph pipeline (policy-extractor). Not related to the direct risk extraction pipeline. See the code for details.

---

### `cross_encoder_tuning/` — Cross-Encoder Fine-Tuning (archived)

Scripts for building datasets, evaluating, and fine-tuning cross-encoder models. These were used to investigate whether replacing ms-marco with a fine-tuned model would improve the pipeline. Conclusion: fine-tuning dramatically improves isolated discrimination (AUC 0.56→0.94) but doesn't improve end-to-end pipeline performance due to taxonomy-specific regressions.

**Scripts:**
- `dataset.py` — builds train/eval JSONL from enriched GT + extraction results
- `evaluate.py` — scores a cross-encoder on the dataset at various thresholds
- `finetune.py` — fine-tunes a cross-encoder using sentence-transformers
- `rewrite_descriptions.py` — rewrites risk descriptions via LLM for better cross-encoder matching

See `EXPERIMENT_LOG.md` for detailed results.

## Experiment Log

See `EXPERIMENT_LOG.md` for a chronological record of all experiments, configurations, and results.

## Policy Split

All experiments use the same 10/10 train/eval policy split, stratified by difficulty (pipeline recall):

**Train:** sap, cisco-supplier, firstsource, guy-nhs, rdash-nhs, dhs-gov, eu-com, ovic, camden-borough-work, llvm

**Eval:** ars, leicestershire_police, lse-legreg, aus-gov, lenovo, prosus, new-york-state, lse-marking, ebay, vps

## End-to-End Testing

After updating prompt templates with optimized instructions, run a full battery to measure end-to-end impact:

```bash
uv run python risk-landscaper/run_extract_battery.py batteries/risk-selected.yaml \
  --base-url http://your-llm-endpoint/v1
```

Compare taxonomy-level P/R/F1 against the baseline in the battery summary. Check `EXPERIMENT_LOG.md` for reference numbers.
