# Concorde Policy Mapper

Unstructured policy-to-risk mapping via [AI Risk Atlas Nexus](https://github.com/IBM/ai-atlas-nexus).

## Introduction

Corporate AI policies exist as unstructured documents — PDFs, Word files, HTML pages — written in natural language. Safety tools, evaluation frameworks, and governance processes all deal with risks, but there is no automated way to bridge from raw policy text to those risks.

This semantic gap — from *"the model must not provide medical advice"* to `atlas-hallucination`, `nist-ms-2.5`, `owasp-llm09-2025` — is the critical transformation that enables all downstream automation.

This software takes raw, unstructured policy documents and produces a **risk landscape**: a set of AI Risk Atlas Nexus risk identifiers with enrichments.

- **Risk identification** — Identifies Nexus risk IDs (e.g., `atlas-hallucination`, `air-2024-0042`, `nist-ms-2.5`) directly from policy text
- **Cross-taxonomy mapping** — Leverages Nexus's SSSOM cross-mappings to provide equivalent identifiers across all 10 included taxonomies (IBM Atlas, NIST, OWASP, AIR 2024, MIT, etc.)
- **Evidence grounding** — Each identified risk is grounded to specific passages in the source document, providing traceability from risk to policy text
- **Confidence scoring** — Each risk mapping includes a confidence score, enabling human review of uncertain mappings

### Example

```yaml
# Input: "acme-ai-policy.pdf"
#   contains: "The AI system must not generate content that could
#              be construed as medical advice..."

# Output:
risk_extraction:
  risks:
    - nexus_id: atlas-hallucination
      confidence: 0.92
      evidence:
        - exact: "The AI system must not generate content that could be construed as medical advice"
          document: "acme-ai-policy.pdf"
          page: 12
      cross_mappings:
        - nist-ms-2.5 (Confabulation)
        - owasp-llm09-2025 (Misinformation)
        - air-2024-0156 (Health misinformation)
```

## Pipeline

The service parses and chunks input documents, then uses hybrid retrieval (keyword and semantic search) against the Nexus risk catalogue to identify candidate risks directly from the policy text. An LLM judges borderline candidates and extracts grounded evidence spans.

1. **Parse** — Docling converts PDF/DOCX/HTML to markdown
2. **Chunk** — Split into ~512-token chunks with page/section metadata
3. **Index** — Build BM25 + bi-encoder + cross-encoder index over Nexus risks
4. **Retrieve** — Per-chunk hybrid search with RRF fusion and cross-encoder reranking
5. **Judge** — LLM judges borderline candidates (parallel)
6. **Ground** — LLM extracts evidence quotes and confidence (parallel)
7. **Merge** — Deduplicate across chunks, keep top-3 evidence spans
8. **Classify** — LLM maps extracted risks to high-level taxonomy categories (e.g., NIST AI RMF)

## Setup

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

You need a local clone of [ai-atlas-nexus](https://github.com/IBM/ai-atlas-nexus) — set its path via `NEXUS_BASE_DIR` env var or `--nexus-base-dir` flag.

## Usage

### Extract risks from a policy document

```bash
uv run concorde-policy-mapper extract policy.pdf -o output/ \
  --base-url http://localhost:8000/v1 \
  --model my-model \
  --nexus-base-dir /path/to/ai-atlas-nexus
```

Outputs `risk-extraction.json` and `risk-extraction.html` report.

### Evaluate against ground truth

```bash
uv run concorde-policy-mapper eval output/ -g evals/ground_truth/policy-name.yaml
```

### Run a battery of extractions

```bash
just run-risk-extract-battery batteries/risk-selected.yaml <base-url> <model>
```

Runs extraction + eval across all policies in the battery config, generates per-run reports and a summary with per-taxonomy heatmaps.

## Tests

```bash
uv run pytest
```

## License

Apache License 2.0
