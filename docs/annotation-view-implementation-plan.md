# Annotation View Implementation Plan

## What This Is

A document-centric HTML report for the Asago policy mapper that renders the source policy document with extracted risks highlighted inline at their evidence locations. This is a new output alongside the existing `risk-extraction.html` (which is risk-centric — a table of risks with expandable detail rows). The annotation view inverts the axis: the document text is primary, risks are overlaid on it.

## Why We Need It

Today, reviewing extraction results or validating ground truth requires holding two artifacts in your head: the source policy document and a structured risk report. The existing HTML report doesn't render the source document text — you see risks in a table, but you can't see them in context. For a 50-page PDF with 40+ extracted risks, this means manually cross-referencing evidence quotes back to the source paragraphs.

The annotation view solves three problems:
1. **Readability** — see what the pipeline found in each section of the document at a glance
2. **Validation** — verify that evidence spans are correct and that the causal chain reasoning makes sense in context
3. **Ground truth review** — when a GT YAML is provided, see which risks are matched (TP), spurious (FP), and missed (FN) overlaid on the document, so GT curators can fix gaps without switching between files

## What We Discussed and Decided

### Why not store full text in the JSON?
We considered persisting full chunk text in `risk-extraction.json` (adding a `text` field to `ChunkSummary`). Decided against it because:
- It bloats the JSON output
- The JSON is meant to be a machine-readable downstream input (for scenario generator)
- The annotation view is a presentation layer, not a data format change
- The source document is available at extraction time anyway

### Why re-parse the source document?
`ChunkSummary.text_preview` is truncated to 200 characters (`pipeline.py:741`). Full chunk text is in memory during extraction but not persisted. Two options:
1. Re-parse at report generation time via `parse_document()` + `chunk_documents()` — requires the original file and docling
2. Persist full chunk text in JSON — contradicts the "no format changes" requirement

**Decision:** Re-parse. The annotated view is generated either during the extraction run (when chunks are in memory) or via a separate CLI command that takes the source document path as input.

### Evidence positioning
`EvidenceSpan` carries `text`, `document`, `page`, `section`, `chunk_index`, `sentence_index` — but **no byte/character offsets**. Positioning works by:
1. Finding the chunk via `chunk_index`
2. Substring matching `EvidenceSpan.text` against the full chunk text
3. Fuzzy fallback for minor differences (whitespace normalization, unicode, LLM-generated quote variations)

### Causal chain display
Each `RiskMatch` has causal chain fields: `threat`, `threat_source`, `vulnerability`, `consequence`, `impact`. These are displayed as an expandable view under each highlighted risk, giving reviewers the reasoning chain in context.

### Ground truth comparison
Reuses `evaluate_extraction()` from `eval.py:145`. This function is standalone (no battery-runner coupling) and returns `matched_ids`, `missing`, `spurious`, precision, recall, F1 via risk-ID-level set intersection. Key distinction:
- **Matched and spurious** risks have evidence spans → render as classified inline annotations
- **Missed** risks exist only in ground truth with no evidence spans → appear in the summary panel/sidebar, NOT inline (they can't be positioned in the document)

### Color coding
- **No GT overlay:** color-code by taxonomy or confidence (unclassified annotations)
- **With GT overlay:** matched = green, spurious = yellow, missed = red (in sidebar only). Use colorblind-safe palette with non-color cues (shape, label, or pattern) in both light and dark modes.

## Current State of the Codebase

### Files you need to understand

| File | What it does | Why it matters |
|------|-------------|----------------|
| `src/asago_policy_mapper/extract/report.py` | `build_risk_extraction_report()` — reads HTML template, injects JSON data, writes self-contained HTML | **Pattern to follow.** New function `build_annotation_report()` goes here. |
| `src/asago_policy_mapper/templates/risk_extraction_report_template.html` | 888-line Alpine.js + Tailwind template for the risk-centric report | **Tech stack reference.** New template uses the same stack. |
| `src/asago_policy_mapper/templates/dark_mode_snippet.html` | Dark mode CSS/JS snippet injected into reports | Reuse for annotation view. |
| `src/asago_policy_mapper/extract/models.py` | Pydantic models: `ExtractionResult`, `RiskMatch`, `EvidenceSpan`, `ChunkSummary` | **Data shapes.** `EvidenceSpan` has `text`, `chunk_index`, `page`, `section`. `RiskMatch` has causal chain fields. `ChunkSummary.text_preview` is truncated to 200 chars. |
| `src/asago_policy_mapper/extract/parse.py` | `parse_document()` → `ParsedDocument`, `chunk_documents()` → `list[Chunk]`. `Chunk` has `text`, `source`, `index`, `page`, `section`. | Used to re-parse and get full chunk text. |
| `src/asago_policy_mapper/extract/pipeline.py` | `run_extraction()` → `ExtractionResult`. Chunks built at line ~735. | Where to hook in annotation report generation during extraction. |
| `src/asago_policy_mapper/cli.py` | typer CLI. `extract` command (line 29), `eval` command (line 286). Report generated at line 280-282 (extract) and 339-341 (eval). | New `annotate` CLI command goes here, mirroring `eval`. |
| `src/asago_policy_mapper/evals/eval.py` | `evaluate_extraction()` at line 145. Takes `(ground_truth_path, extracted_path)`, returns dict with `matched_ids`, `missing`, `spurious`, metrics. | Reuse for GT comparison mode. |
| `evals/ground_truth/*.yaml` | GT files. Format: `risks: [{id: "atlas-hallucination", evidence: [{text: "...", section: "..."}]}]` | Input for comparison mode. |

### How the existing report works

```
cli.py (extract command, line 280):
    result_data = result.model_dump()
    build_risk_extraction_report(result_data, output / "risk-extraction.html")

report.py:
    def build_risk_extraction_report(data, output_path):
        html = template.read_text().replace("__REPORT_DATA__", json.dumps(data))
        html = inject_dark_mode(html)
        output_path.write_text(html)
```

The template is a single self-contained HTML file. All data is embedded as a JSON blob. The template renders client-side with Alpine.js + Tailwind. No external dependencies, opens from filesystem in any browser.

### Key data shapes

```python
# EvidenceSpan (models.py:43)
class EvidenceSpan(BaseModel):
    text: str                    # The evidence quote
    document: str                # Source document name
    page: int | None = None
    section: str | None = None
    chunk_index: int             # Which chunk this came from
    sentence_index: int = 0
    cross_encoder_score: float = 0.0

# RiskMatch (models.py:60) — each extracted risk
class RiskMatch(BaseModel):
    risk_id: str
    risk_name: str
    risk_description: str
    taxonomy: str = ""
    confidence: float
    grounding_confidence: str    # "high", "medium", "low"
    accepted_by: str             # "auto", "judge", "grounding"
    evidence: list[EvidenceSpan]
    scores: RetrievalScores
    mitigations: list[MitigationRef] = []
    threat: str | None = None           # causal chain
    threat_source: str | None = None    # causal chain
    vulnerability: str | None = None    # causal chain
    consequence: str | None = None      # causal chain
    impact: str | None = None           # causal chain

# Chunk (parse.py:30) — full text available here, NOT in ChunkSummary
@dataclass(frozen=True)
class Chunk:
    text: str           # FULL chunk text
    source: str
    index: int
    page: int | None = None
    section: str | None = None

# Ground truth YAML format
risks:
  - id: atlas-hallucination
    evidence:
      - text: "Outputs created by GenAI tools may provide fictitious answers..."
        section: "IV. Additional specific rules..."
```

### evaluate_extraction return shape

```python
{
    "policy": "amadeus",
    "total_expected": 25,
    "total_extracted": 158,
    "matched": 22,
    "matched_ids": ["atlas-hallucination", "atlas-decision-bias", ...],
    "missing": ["atlas-some-risk", ...],        # in GT but not extracted
    "spurious": ["atlas-other-risk", ...],      # extracted but not in GT
    "precision": 0.139,
    "recall": 0.880,
    "f1": 0.240,
    "pass": true,
    "per_taxonomy": {...},
    "category_eval": {...}
}
```

## Implementation Tasks

Each task is an independent, testable PR that builds on the previous one. No pipeline changes. No new dependencies — re-parsing uses existing `parse_document()` + `chunk_documents()`, fuzzy matching uses stdlib `difflib`, GT comparison calls existing `evaluate_extraction()`, report builder follows the existing template pattern, and the HTML template uses the same Alpine.js + Tailwind CDN stack.

---

### Task 1: Data preparation layer with evidence span matching

Build a data preparation function that re-parses the source policy document to recover full chunk text, then locates each extracted evidence quote within its corresponding chunk using normalized substring matching with a stdlib fuzzy fallback. Returns a structured dict for template consumption: chunks with positioned annotations (start/end character offsets), a summary with counts, and extraction metadata. No ground truth handling in this task.

Unit tests using plain text files to avoid the docling dependency: exact matching, fuzzy matching, overlapping spans, unmatched spans, zero-risk case, and chunk index alignment validation.

No pipeline changes. No new dependencies.

**PR scope:** New `annotate.py` module + tests.

---

### Task 2: Document-centric HTML template with sidebar navigation

Create a self-contained HTML report that renders the source document text chunk-by-chunk with risk evidence highlighted inline. Same tech stack and pattern as the existing risk extraction report (Alpine.js + Tailwind CDN, embedded JSON, no server needed).

Layout: summary banner with policy name and evidence span counts, sticky left sidebar with a risk index and jump-to links (filterable by risk ID or taxonomy), main content area with document text grouped by section. Evidence spans are highlighted and color-coded by taxonomy. Hover shows a tooltip with risk metadata. Click opens an expandable panel with risk description, grounding confidence, evidence quote, and causal chain fields. Dark mode support. No ground truth rendering in this task.

**PR scope:** Template file only. No Python changes beyond what Task 1 already provides.

---

### Task 3: CLI command and report builder wiring

Wire the data preparation layer and the HTML template into the CLI.

Add a report builder function following the same pattern as the existing risk extraction report builder. Add a new `annotate` CLI command that takes a run directory and source document path, produces the annotation HTML report, and prints a summary to stdout. Also hook into the existing `extract` command so every extraction run automatically produces the annotation report alongside the risk extraction report.

**PR scope:** Report builder function, CLI command, extraction hook, integration tests.

---

### Task 4: Ground truth comparison overlay

Add ground truth comparison mode across the data layer, template, and CLI.

Data layer: accept an optional ground truth YAML, call the existing evaluation function to classify each risk as matched or spurious, and populate a missed-risks list (GT risks with no extraction evidence — sidebar only, not inline).

Template: when GT data is present, re-color annotations — matched = green with checkmark, spurious = yellow with warning icon. Show missed risks in the sidebar with a red indicator. Add GT metrics (matched/spurious/missed counts, precision, recall, F1) to the summary banner.

CLI: add a ground truth flag to the annotate command. Add a source document flag to the eval command so it can regenerate the annotation report with the GT overlay.

**PR scope:** Changes across `annotate.py`, template, CLI, and tests.

---

## Summary of deliverables per task

| Task | PR Output | Depends On |
|------|-----------|------------|
| 1 | Data preparation module + unit tests | Nothing |
| 2 | HTML template | Task 1 (data shape) |
| 3 | Report builder + CLI command + integration | Tasks 1 & 2 |
| 4 | Ground truth comparison overlay | Tasks 1-3 |

## Commands reference

```bash
# Install / sync
uv sync

# Run fast tests
uv run pytest -rs -m "not slow"

# Format + lint + type check
uv run ruff format src/ tests/ && uv run ruff check src/ tests/ && uv run mypy src/asago_policy_mapper/

# Run extraction (produces both reports)
uv run asago-policy-mapper extract policy.pdf -o output/ --base-url http://... --model gemma4-26b-a4b-it

# Generate annotation view standalone
uv run asago-policy-mapper annotate output/ policy.pdf

# Generate annotation view with GT comparison
uv run asago-policy-mapper annotate output/ policy.pdf --ground-truth evals/ground_truth/policy.yaml

# Run eval with annotation view
uv run asago-policy-mapper eval output/ --source-document policy.pdf
```
