# Changelog

## [Unreleased]

### Added
- **Two-tier evaluation**: category-level precision/recall/F1 alongside risk-level metrics. Evaluates whether the pipeline captures the right risk *themes* (NIST AI RMF, OWASP LLM, OWASP ASI categories) even when individual risk-level matches are missed. Category-level NIST F1=0.938 vs risk-level F1=0.771.
- **Cross-taxonomy SSSOM mapping** (`data/risk_to_category.sssom.tsv`): 802 mappings linking 486 specific risks (IBM Risk Atlas, Credo UCF, AIR 2024, MIT AI Risk Repository) to 4 category-level taxonomies (NIST AI RMF, OWASP Top 10 LLM, AILuminate, OWASP ASI). Built from existing Nexus mapping files + manually reviewed gap-fill.
- Risk ID sanitisation in eval to handle malformed upstream Nexus IDs (name appended after space).
- OWASP ASI (Agentic Security Initiative) taxonomy support as a category-level target.

### Changed
- **Pipeline no longer runs taxonomy classification step.** Category-level taxonomies (NIST, OWASP LLM, AILuminate, OWASP ASI, ShieldGemma) are excluded from Nexus risk loading and evaluated via the SSSOM mapping instead of LLM classification.
- Ground truth files stripped to risk-level annotations only (107 category-level entries removed across 19 files). Category-level coverage is now derived programmatically from risk-level GT via the SSSOM mapping.
- `--classify-taxonomies` CLI option removed from both `extract` command and battery runner.

### Removed
- `extract/classify.py` module (LLM-based taxonomy classification)
- `classify_risks` prompt templates (`classify_risks_system.j2`, `classify_risks_user.j2`)
- `source_risk_ids` field from `RiskMatch` model
- `"classify"` stage from `LLMCallRecord.stage` literal

### Fixed
- `_infer_taxonomy` prefix for OWASP LLM risks: `"llm0"` → `"llm"` to correctly match `llm102025-unbounded-consumption`.
- `guy-nhs` ground truth: replaced category-level `llm102025-unbounded-consumption` with risk-level `credo-risk-004` (Environmental harm).
- `dhs-gov` ground truth: added `credo-risk-014` (Obscene and sexually abusive content) to make `ail-child-sexual-exploitation` derivable before stripping.
