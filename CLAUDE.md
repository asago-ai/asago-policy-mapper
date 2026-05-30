# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Concorde Policy Mapper extracts AI risks from policy documents using the IBM AI Atlas Nexus risk taxonomy (~524 risks). It uses hybrid retrieval (BM25 + semantic embeddings + cross-encoder reranking) to match document chunks against Nexus risks, then LLM-judges borderline candidates and grounds accepted ones with evidence quotes.

## Commands

```bash
# Install / sync dependencies
uv sync

# Run all tests
uv run pytest
just test

# Run a single test file or specific test
uv run pytest tests/test_extract_pipeline.py
uv run pytest tests/test_extract_retrieve.py::test_classify_candidates -v

# Extract risks from a document
uv run concorde-policy-mapper extract policy.pdf -o output/ \
  --base-url http://localhost:8000/v1 --model my-model \
  --nexus-base-dir /path/to/ai-atlas-nexus

# Evaluate against ground truth
uv run concorde-policy-mapper eval output/ -g evals/ground_truth/policy-name.yaml

# Run full battery (20 policies, parallel)
just run-risk-extract-battery batteries/risk-selected.yaml <base-url> <model>
# Or directly with more options:
python run_extract_battery.py batteries/risk-selected.yaml --base-url <url> --model <model> -j 6

# Run battery with MLflow tracking disabled
just no_mlflow="1" run-risk-extract-battery batteries/risk-selected.yaml <base-url> <model>

# Run battery with custom MLflow experiment name
python run_extract_battery.py batteries/risk-selected.yaml --base-url <url> --model <model> --mlflow-experiment my-experiment
```

## Architecture

### Extraction Pipeline (`extract/pipeline.py::run_extraction`)

```
Documents → parse_document() → chunk_documents() → per-chunk retrieve → judge → ground → merge → classify
                                                                    ↑ ThreadPoolExecutor (steps 7-8)
```

1. **Parse** (`parse.py`) — Docling converts PDF/DOCX/HTML to markdown; plain text passes through
2. **Chunk** (`parse.py`) — HybridChunker splits into ~512-token chunks preserving page/section metadata
3. **Agentic filter** — If document lacks agent-related terminology, agentic risks are excluded from the catalog
4. **Taxonomy split** — Risks in `classify_taxonomies` (default: nist-ai-rmf) are deferred to post-retrieval classification; the rest go through retrieval
5. **Index** (`index.py`) — `RiskIndex` builds BM25 + bi-encoder embeddings + optional cross-encoder over the retrieval risk set
6. **Retrieve** (`retrieve.py`) — Per-chunk: BM25 + semantic → RRF fusion → cross-encoder rerank → threshold classify into accepted/borderline/discarded
7. **Judge** (`retrieve.py`) — LLM judges borderline candidates using padded text (adjacent chunk sentences for context). Parallel via ThreadPoolExecutor
8. **Ground** (`attribute.py`) — LLM extracts evidence quotes + confidence (high/medium/low) for accepted candidates; ungrounded ones filtered out. Parallel via ThreadPoolExecutor
9. **Merge** (`merge.py`) — Deduplicate matches across chunks, keep best confidence and top-3 evidence spans
10. **Classify** (`classify.py`) — LLM maps already-extracted risks to high-level taxonomy categories

With `--no-cross-encoder`, steps 6-7 are replaced by RRF score floor filtering (no LLM judging).

### LLM Integration (`llm.py`)

- `create_client()` wraps OpenAI with `instructor` (JSON mode) for structured Pydantic outputs
- `TokenTracker` accumulates usage across stages; `LLMConfig` holds connection details
- Automatic retry on validation errors (appends error hint), context overflow detection (reduces max_tokens), and prompt truncation on incomplete output
- All LLM calls use `response_model=list[PydanticModel]` with `temperature=0.0`

### Prompt Templates (`templates/prompts/`)

Three Jinja2 template pairs (`_system.j2` + `_user.j2`): `judge_risk`, `ground_evidence`, `classify_risks`. Loaded by `prompts.py::render_prompt()`.

### Evaluation (`evals/eval.py`)

Compares extracted risk IDs against ground truth YAML. Computes precision/recall/F1 overall and per-taxonomy. 20 ground truth files in `evals/ground_truth/`.

### Battery Runner (`run_extract_battery.py`)

Runs `concorde-policy-mapper extract` as a subprocess per policy in a battery YAML config, with parallel execution (default 6 workers). Auto-evaluates against ground truth, generates per-run HTML reports, and a battery summary with per-taxonomy heatmaps.

## Key Conventions

- `NEXUS_BASE_DIR` env var or `--nexus-base-dir` flag points to a local clone of `github.com/IBM/ai-atlas-nexus`
- Risk IDs are taxonomy-prefixed: `atlas-` → ibm-risk-atlas, `nist-` → nist-ai-rmf, `credo-` → credo-ucf, etc. (see `evals/eval.py::_TAXONOMY_PREFIXES`)
- Excluded taxonomies (not loaded from Nexus): `mit-ai-risk-repository-causal`, `ibm-granite-guardian` (in `cli.py::EXCLUDED_TAXONOMIES`)
- `LLMCallRecord` captures every LLM call (messages, response, timing) in the ExtractionResult for analysis/debugging
- `debug.py` writes per-call JSON files when `--debug <dir>` is passed
- MLflow tracking is enabled by default in the battery runner; set `MLFLOW_TRACKING_URI` to point to your MLflow server. Pass `--no-mlflow` to disable.
- Prompt templates are synced to the MLflow Prompt Registry at the start of each tracked battery run (hash-based dedup avoids duplicate versions)

## Dependency Pins

- `ai-atlas-nexus` is pinned to a specific commit (v1.2.1) — `@main` may have breaking Pydantic schema changes
- `torch<2.12` and `transformers<5.6` — newer versions introduce an MPS-incompatible `rt_detr_v2` layout model in docling's PDF pipeline on Apple Silicon

## Development

- DO NOT skip updating the changelog with any changes made
- DO NOT skip updating CLAUDE.md and the README.md when changes require it
- 
