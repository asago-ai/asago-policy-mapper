Asago Policy Mapper extracts AI risks from policy documents using the IBM AI Atlas Nexus risk taxonomy (~524 risks). It uses hybrid retrieval (BM25 + semantic embeddings + cross-encoder reranking) to match document chunks against Nexus risks, then LLM-judges borderline candidates and grounds accepted ones with evidence quotes.

## Commands

```bash
# Install / sync dependencies
uv sync

# Run all tests
uv run pytest

# Run fast tests only (skip slow embedding-model tests)
uv run pytest -rs -m "not slow"

# Run a single test file or specific test
uv run pytest tests/test_extract_pipeline.py
uv run pytest tests/test_extract_retrieve.py::test_classify_candidates -v

# Format + lint + type check (all static checks)
uv run ruff format src/ tests/ && uv run ruff check src/ tests/ && uv run mypy src/asago_policy_mapper/

# Lint
uv run ruff check src/ tests/

# Lint single file (with auto-fix)
uv run ruff check --fix path/to/file.py

# Format
uv run ruff format src/ tests/

# Format single file
uv run ruff format path/to/file.py

# Type check
uv run mypy src/asago_policy_mapper/

# Type check single file
uv run mypy path/to/file.py

# Run LLM integration tests (requires Ollama or similar)
# env: LLM_BASE_URL=http://localhost:11434/v1  LLM_MODEL=gemma3:1b
uv run pytest --test-llm -m llm -v -s --tb=short -W ignore::DeprecationWarning

# See README.md for full CLI usage examples (extract, eval, battery, remote models)
```

## Architecture

### Extraction Pipeline

The pipeline in `src/asago_policy_mapper/extract/pipeline.py` has several alternative modes controlled by CLI flags — when modifying one path, be aware the others exist:

- **Default (query-gen on):** LLM generates search queries per section group, candidates (capped at 50 per chunk by RRF after query union) go to grounding in batches of `--grounding-batch-size` (default 15). Disable with `--no-query-gen` to use per-chunk BM25+semantic retrieval with cross-encoder reranking and LLM judging.
- `--no-cross-encoder`: RRF score floor filtering replaces cross-encoder reranking (no LLM judging)
- `--no-judge`: borderline candidates auto-promoted (skips LLM judge)
- `--no-grounding`: accepted candidates become matches without evidence extraction
- `--no-judge --no-grounding`: pure IR evaluation — no LLM calls at all
- `--no-causal-synthesis`: skips causal chain synthesis; static YAML chains from `src/asago_policy_mapper/data/` used as fallback

**Variant collapsing:** Risk IDs containing `---` (e.g. `unauthorized-processing---biometric-data`) are collapsed into synthetic parent entries for indexing. After grounding, a variant grounding step determines which specific sub-types have evidence. This affects how risk IDs flow through the entire pipeline — don't treat `---` IDs as regular risks.

**Multi-pass grounding:** Grounding and expansion each run multiple passes (default 3) and union results to reduce LLM non-determinism. Do not remove the extra passes — they stabilize which risks survive grounding. Grounding JSON is split into batches (`grounding_batch_size`, default 15) so responses stay within `LLMConfig.max_tokens` (always sent to the API, default 8192).

## Key Conventions

- The risk catalog comes from the `ai-atlas-nexus` PyPI package (pinned in `pyproject.toml`) — no local clone is needed. `NEXUS_BASE_DIR` env var or `--nexus-base-dir` flag is an optional override pointing at a local clone checkout (escape hatch for unreleased data; empty behaves like unset); startup validates the clone's data against the installed ontology models and fails on any skew. `tests/test_nexus_pin_equivalence.py` pins the filtered catalog population, taxonomy histogram and a per-risk content fingerprint (sha256 over sorted `id|taxonomy|name|description` triples) — when upgrading the dependency, update the expected counts and fingerprint there together and re-run a battery smoke
- Risk IDs are taxonomy-prefixed: `atlas-` → ibm-risk-atlas, `nist-` → nist-ai-rmf, `credo-` → credo-ucf, etc. (see `evals/eval.py::_TAXONOMY_PREFIXES`)
- Excluded taxonomies (not loaded from Nexus): category-level (`nist-ai-rmf`, `owasp-llm-2.0`, `ailuminate-v1.0`, `owasp-asi`, `shieldgemma-taxonomy`) and others (`mit-ai-risk-repository-causal`, `ibm-granite-guardian`) — see `cli.py::EXCLUDED_TAXONOMIES`
- `--check-risk-text` (off by default) logs a warning for each loaded risk whose description lacks closing punctuation; see `taxonomy.py::warn_unterminated_descriptions`. A trailing ellipsis is flagged too. Empty and whitespace-only descriptions are not flagged. Some CREDO UCF descriptions are truncated upstream, and the Nexus source CSV is truncated too. `taxonomy.py::apply_description_overrides` restores them at catalog load from the Unified Control Framework paper (arXiv:2503.05937v1, Appendix A). Each `_DESCRIPTION_OVERRIDES` entry applies only while the loaded text still equals the known truncated text. `credo-risk-045` is cut in the paper too, so it stays unpatched. Add an override only with text copied verbatim from the original source. Never complete a description yourself.
- `--custom-taxonomy` flag loads user-provided risk YAML files via `taxonomy.py`; custom risks are tier 1 (individual risks, not categories), appended to Nexus risks before extraction. No mitigations or cross-taxonomy mappings for custom risks.
- `LLMCallRecord` captures each successful pipeline-stage LLM call (messages, response, timing) in the ExtractionResult for analysis/debugging; failed wire attempts inside a retry loop are not individual records. The records are serialized into the `llm_calls` array of `risk-extraction.json` when the run completes (there is no per-call streaming — records are lost if the run dies)
- MLflow tracking is enabled by default in the battery runner; set `MLFLOW_TRACKING_URI` to point to your MLflow server. Pass `--no-mlflow` to disable.
- Prompt templates are synced to the MLflow Prompt Registry at the start of each tracked battery run (hash-based dedup avoids duplicate versions)

## Structured Output Client

`llm.py::create_client` returns a tracked structured-output client over the plain OpenAI SDK (no instructor). Call sites pass `response_model=SomePydanticModel` to `client.chat.completions.create` and receive the validated Pydantic object. The client sends the model's JSON schema as the native `json_schema` `response_format` (`StructuredOutputMode.JSON_SCHEMA`, the default), `json_object` plus a "Respond with a single JSON object that matches this JSON schema exactly:" schema-in-prompt instruction (`StructuredOutputMode.JSON`) for endpoints without schema support, or `json_schema` plus the instructor-verbatim schema block (`JSON_SCHEMA_WITH_PROMPT`, kept for battery comparisons). The mode defaults to `JSON_SCHEMA`; the `POLICY_MAPPER_STRUCTURED_OUTPUT_MODE` environment variable selects it when no explicit `mode` argument is passed. JSON content in `message.content` is parsed locally, with markdown-fence stripping. Battery finding (2026-11-05): vLLM guided decoding under `JSON_SCHEMA` costs about −0.016 micro-F1 and saves about 16% tokens versus the instructor-era schema-in-prompt wire format (whose schema block `JSON_SCHEMA_WITH_PROMPT` reuses, at −0.014 micro-F1); the `JSON` mode's prompt was never battery-measured against it.

Error semantics, pinned by tests over a stubbed transport: the structured client makes one attempt per call; the retry loop in the tracking wrapper retries parse/validation failures with an error hint and finally raises `ValidationRetryExhausted` (`failed_attempts` carries the failed attempt, with its error chained as `__cause__`). API and transport errors (`openai.APIError`) propagate untouched, except context-length 400s, which reduce the output-token budget and retry. `synthesize_causal_chain` skips a risk only on validation exhaustion and re-raises everything else. `tests/llm_errors.py` builds these exceptions in the shape production raises.

## Retrieval Architecture Notes

- The default cross-encoder (ms-marco-MiniLM) has AUC ~0.50 on pipeline-mined negatives — it does not discriminate semantically. It functions as a volume reduction filter; the grounding stage provides the actual precision filtering. Do not attempt to tune or rely on its scores for ranking. See `experiments/EXPERIMENT_LOG.md` for details.
- Do not use cross-encoder scores for hard negative mining — use pipeline-mined negatives from `grounding_filtered_candidates` instead. Eval datasets MUST use pipeline-mined negatives (from actual battery runs), not cross-encoder-mined negatives — the latter are biased toward the mining model's specific failure modes.

## Dependency Pins

- `ai-atlas-nexus==1.2.5` (PyPI) — exact pin so catalog and ontology models travel together; upgrade deliberately, then update the expected counts in `tests/test_nexus_pin_equivalence.py`
- `torch<2.12` and `transformers<5.6` — newer versions introduce an MPS-incompatible `rt_detr_v2` layout model in docling's PDF pipeline on Apple Silicon
- `numpy<2.5` — numpy 2.5.0 ships PEP 695 type stubs that mypy cannot parse when `python_version` targets 3.11

## LLM Test Diagnostics

- `tests/llm_health.py` requires a model list and a structured completion before the LLM integration tests start.
- Each probe request has a 60-second timeout and no automatic retries. Missing models and failed inference fail the tests.
- `LLM_REQUIRE_SERVER=1` makes an unavailable server fail the tests. Local runs skip unavailable servers by default.
- The Ollama CI job uses `--maxfail=1` and a 15-minute job timeout.
- CI preserves CPU details, runtime versions, model metadata, and the complete Ollama debug log in a diagnostic artifact.
- Diagnostic artifacts use the name `ollama-diagnostics-<run_id>-<attempt>` and seven-day retention.

## Experiments

- Always update `experiments/EXPERIMENT_LOG.md` with results after running any experiment or battery that produces new data points
- Include MLflow experiment name and run ID in experiment log entries when MLflow tracking is enabled (e.g., `**MLflow:** experiment=risk-extraction, run_id=abc123`)

## Development

- `AGENTS.md` is a symlink to `CLAUDE.md` — they are the same file. Do not treat them as separate files or suggest deduplication.
- DO NOT skip updating `CLAUDE.md`/`AGENTS.md` and `README.md` when changes require it
