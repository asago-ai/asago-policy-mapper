# St John’s OpenAI retrieval comparison

Date: 2026-09-24

Policy: `policy_examples/st-johns.md`
Ground truth: `evals/ground_truth/st-johns.yaml` (51 expected risks)

## Results

| Configuration | Query generation | Cross-encoder | Risks in report | Risks counted by eval | Precision | Recall | F1 | Result |
|---|---:|---|---:|---:|---:|---:|---:|---|
| OpenAI embeddings, RRF retrieval | On | None | 65 | 65 | 0.677 | 0.863 | **0.759** | PASS |
| OpenAI embeddings + GTE | On | GTE reranker | 73 | 72 | 0.597 | 0.843 | 0.699 | FAIL |
| OpenAI embeddings + GTE | Off | GTE reranker | 57 | 56 | 0.589 | 0.647 | 0.617 | FAIL |

The no-cross-encoder/query-generation configuration performed best on this policy. The
GTE configuration with query generation disabled is the first run in which the
cross-encoder handled the main per-chunk retrieval path, but it reduced recall
substantially.

### Pipeline statistics

| Configuration | Retrieval result | LLM judge | Grounding-filtered | Total tokens | Calls |
|---|---:|---:|---:|---:|---:|
| No cross-encoder, query generation on | 318 RRF-accepted | 0 | 168 | 730,563 | 289 |
| GTE, query generation on | 270 auto-accepted | 5 | 123 | 714,211 | 288 |
| GTE, query generation off | 70 auto-accepted | 28 | 25 | 492,766 | 222 |

## Commands used

All runs used GPT-6 Luna for the LLM, OpenAI `text-embedding-3-large` for the
bi-encoder, `--max-tokens 8192`, `--output-token-parameter max_completion_tokens`,
and `--temperature 1.0`.

The evaluation commands were:

```bash
uv run asago-policy-mapper eval \
  output/st-johns-openai \
  -g evals/ground_truth/st-johns.yaml

uv run asago-policy-mapper eval \
  output/st-johns-openai-with-cross-encoder \
  -g evals/ground_truth/st-johns.yaml
```

The GTE/query-generation-on run used `--cross-encoder-model
Alibaba-NLP/gte-reranker-modernbert-base` without `--no-query-gen`.

The GTE/query-generation-off run used the same cross-encoder flag plus
`--no-query-gen`.

The two GTE runs used the same output directory, so the directory currently contains
the query-generation-off run. The query-generation-on metrics above were captured
from its evaluation immediately after that run.

## How the evaluation works

These metrics were produced by the project’s evaluation code, not calculated manually.
For each run, `asago-policy-mapper eval`:

1. Loads the expected risk IDs from the ground-truth YAML.
2. Loads extracted risk IDs from `risk-extraction.json`.
3. Normalizes IDs and compares them as sets.
4. Computes:
   - precision = matched risks / extracted risks
   - recall = matched risks / expected risks
   - F1 = harmonic mean of precision and recall

The evaluator checks risk-ID agreement only. It does not independently assess whether
evidence quotes are sufficiently specific or whether causal-chain fields are correct.

The evaluator also strips text after the first space in malformed risk IDs and counts
unique IDs. This explains small differences between the CLI’s “risks matched” count and
the evaluator’s “risks extracted” count.

The evaluation command writes `eval.json` and updates the extraction HTML report with
the evaluation results.
