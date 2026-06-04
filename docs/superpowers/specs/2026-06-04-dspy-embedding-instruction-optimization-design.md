# DSPy Embedding Instruction Optimization

## Goal

Use DSPy's GEPA optimizer to find the optimal instruction prefix for the remote Qwen embedding model, maximizing risk-level retrieval recall against ground truth.

## Context

The retrieval pipeline uses hybrid search (BM25 + semantic + RRF fusion) to match document chunks against ~524 AI risks. When using instruction-aware embedding models like Qwen3-Embedding via vLLM's `/v1/embeddings` endpoint, queries are prefixed with `"Instruct: {instruction}\nQuery: {text}"`. The current default instruction is a hand-written string in `RetrievalConfig.query_instruction`. Optimizing this instruction can improve semantic search quality.

## Approach

**Approach A: Thin DSPy wrapper around existing pipeline.** Create a DSPy `Signature` whose `instructions` property (the docstring that GEPA optimizes) serves as the Qwen embedding instruction prefix. The module's `forward()` runs the hybrid retrieval pipeline (BM25 + semantic + RRF, no cross-encoder) and returns retrieved risk IDs. GEPA proposes instruction variations via its reflection LLM and iterates based on retrieval recall.

## Architecture

### DSPy Signature

```python
class RetrieveRisks(dspy.Signature):
    """<GEPA optimizes this docstring — it becomes the Qwen embedding instruction>"""
    chunk_text: str = dspy.InputField(desc="Policy document chunk")
    risk_ids: list[str] = dspy.OutputField(desc="Retrieved risk IDs")
```

GEPA rewrites `signature.instructions` during optimization. The module intercepts this value and passes it to the `RiskIndex` as the query instruction prefix.

### DSPy Module

```python
class EmbeddingRetriever(dspy.Module):
    def __init__(self):
        self.retrieve = dspy.Predict(RetrieveRisks)

    def forward(self, chunk_texts, risk_ids):
        instruction = self.retrieve.signature.instructions
        # Set instruction on cached RiskIndex
        # Run hybrid_search per chunk (no cross-encoder)
        # Union retrieved risk IDs across all chunks
        # Return dspy.Prediction(risk_ids=union_of_retrieved)
```

The module holds a reference to a pre-built `RiskIndex`. On each trial, it updates the query instruction on the index's remote bi-encoder, then evaluates all chunks.

### Metric

Recall-only, per-policy:

```python
def retrieval_recall_metric(example, pred, trace=None):
    expected = set(example.risk_ids)
    retrieved = set(pred.risk_ids)
    hits = expected & retrieved
    recall = len(hits) / len(expected) if expected else 1.0
    feedback = f"Recall: {recall:.2%} ({len(hits)}/{len(expected)})"
    if missing := expected - retrieved:
        feedback += f" | Missing: {', '.join(sorted(missing))}"
    return dspy.Prediction(score=recall, feedback=feedback)
```

No precision penalty — downstream stages (cross-encoder, judge, grounding) handle precision. The feedback string lets GEPA's reflection LLM understand what's missing.

### Dataset Construction

Each `dspy.Example` represents one policy document:

- `chunk_texts`: list of all chunk texts (with context padding from adjacent chunks)
- `risk_ids`: ground truth risk IDs from the policy's YAML file
- `policy_name`: for logging

The module iterates over all chunks per policy, runs hybrid search for each, and unions the retrieved risk IDs. The metric compares this union against ground truth.

**Train/eval split:** Reuses the existing split from `experiments/dspy_judge/dataset.py`:
- Train (13 policies): sap, cisco-supplier, firstsource, guy-nhs, rdash-nhs, dhs-gov, eu-com, ovic, camden-borough-work, llvm, amadeus, fs-isac, gray
- Eval (14 policies): ars, leicestershire_police, lse-legreg, aus-gov, lenovo, prosus, new-york-state, lse-marking, ebay, vps, npcc, penn, st-johns, icrc

For prototyping, start with 5-6 train policies; scale to full split once plumbing works.

### RiskIndex Caching

The corpus-side embeddings (risk descriptions) and BM25 index are instruction-independent. Only query encoding uses the instruction prefix. Strategy:

1. Build `RiskIndex` once at startup with a placeholder instruction, `cross_encoder_model=None`
2. Per GEPA trial, update the query instruction on the remote bi-encoder instance
3. Each trial only pays for re-encoding chunk queries (fast on remote GPU)

Add a `set_query_instruction()` method to `RiskIndex` to avoid reaching into private attributes.

### Retrieval Configuration

- **BM25 + semantic + RRF fusion** — full hybrid search
- **No cross-encoder** — skip reranking (adds noise at AUC ~0.50, adds latency)
- **Top-k candidates per chunk:** use existing defaults (top_k=50, bm25_top_k=100, semantic_top_k=100)
- **Candidate acceptance:** all RRF-fused candidates above `rrf_min_score` floor count as "retrieved" for recall measurement

## File Structure

```
experiments/dspy_embedding/
├── __init__.py
├── __main__.py          # calls optimize.main()
├── signature.py         # RetrieveRisks signature
├── module.py            # EmbeddingRetriever module (wraps RiskIndex)
├── metric.py            # retrieval_recall_metric
├── dataset.py           # loads policies + ground truth -> dspy.Examples
└── optimize.py          # GEPA optimization loop, baseline, save results
```

## CLI Interface

```bash
uv run python -m experiments.dspy_embedding \
  --bi-encoder-model https://qwen-embedding.apps.example.com/v1/embeddings \
  --nexus-base-dir /path/to/ai-atlas-nexus \
  --base-url http://localhost:8000/v1 \
  --model gemma-4-26b-a4b-it \
  --auto medium \
  --train-policies sap,cisco-supplier,firstsource,guy-nhs,rdash-nhs
```

Arguments:
- `--bi-encoder-model`: Remote Qwen embedding endpoint (the model being optimized)
- `--nexus-base-dir`: Path to ai-atlas-nexus repo (for loading risk catalog)
- `--base-url` / `--model`: LLM endpoint for GEPA's reflection (not the embeddings)
- `--auto`: GEPA optimization intensity (light/medium/heavy)
- `--train-policies`: comma-separated subset for prototyping (optional; defaults to full 13)

## Output

Same pattern as existing experiments:
- `runs/run_{timestamp}.json`: baseline recall, optimized recall, improvement, winning instruction, per-policy breakdown
- `runs/program_{timestamp}.json`: serialized DSPy program for reuse

## Risks and Mitigations

- **GEPA reflection LLM may not understand embedding instructions:** The reflection LLM sees recall feedback and proposes text variations. It doesn't need to know the text is an embedding instruction — it just needs to correlate text changes with recall changes. The existing judge experiments show GEPA is effective even when the optimized text serves a non-obvious purpose.
- **Remote API latency:** Each trial re-encodes all chunks across train policies. With 5-6 policies this is manageable; at 13 policies it could be slow. Mitigation: start small, parallelize chunk encoding (already batched in `_RemoteBiEncoder`).
- **Instruction overfitting:** Optimized instruction may overfit to train policy styles. Mitigation: holdout eval on 14 unseen policies; monitor per-policy recall variance.
