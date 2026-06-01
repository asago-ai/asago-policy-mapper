# Experiment Log

## 2026-05-28: Cross-Encoder Baseline Evaluation

**Description:** Evaluated off-the-shelf cross-encoder models on a dataset built from enriched ground truth (894 risks
across 20 policies). The dataset pairs risk descriptions with document chunks, labeled positive/negative via GT evidence
matching. 7,380 train pairs / 8,132 eval pairs, 50/50 policy split stratified by difficulty.

**Models tested:**

- `cross-encoder/ms-marco-MiniLM-L-12-v2` (current pipeline model)
- `cross-encoder/ms-marco-electra-base`
- `cross-encoder/nli-deberta-v3-base`
- `cross-encoder/stsb-distilroberta-base`

**Results (eval set):**

| Model                   | AUC-ROC | Best F1 | Pos Mean | Hard Neg Mean |
|-------------------------|---------|---------|----------|---------------|
| ms-marco-MiniLM-L-12-v2 | 0.565   | 0.334   | 0.360    | 0.546         |
| ms-marco-electra-base   | 0.561   | 0.339   | 0.641    | 0.660         |
| nli-deberta-v3-base     | 0.514   | 0.307   | 0.847    | 0.866         |
| stsb-distilroberta-base | 0.529   | 0.319   | 0.639    | 0.637         |

**Conclusion:** All off-the-shelf models perform near random (AUC ~0.5). Hard negatives consistently score equal to or
higher than positives. The risk-policy relevance task is too domain-specific for generic models.

---

## 2026-05-28: Cross-Encoder Fine-Tuning

**Description:** Fine-tuned `ms-marco-MiniLM-L-12-v2` on the train split (7,380 pairs). 5 epochs, batch size 16, lr
2e-5. Also fine-tuned `nli-deberta-v3-base` for comparison.

**Results (eval set):**

| Model              | AUC-ROC | Best F1 | Precision | Recall | Speed  |
|--------------------|---------|---------|-----------|--------|--------|
| ms-marco baseline  | 0.565   | 0.334   | 0.226     | 0.645  | 98 p/s |
| Fine-tuned MiniLM  | 0.941   | 0.755   | 0.762     | 0.748  | 95 p/s |
| Fine-tuned DeBERTa | 0.938   | 0.741   | 0.744     | 0.737  | 20 p/s |

**End-to-end battery (20 policies):** Fine-tuned MiniLM improved Credo (+0.077 recall) and NIST (+0.095 recall) but
destroyed ai-risk-taxonomy (-0.40 recall). The model learned to reject ai-risk-taxonomy's tautological description
style ("X is defined as X").

**Conclusion:** Fine-tuning achieves excellent discrimination on the eval dataset but doesn't translate to end-to-end
pipeline improvement. The ai-risk-taxonomy regression and precision drop offset recall gains. MiniLM preferred over
DeBERTa (same AUC, 5x faster).

---

## 2026-05-29: Description Rewriting for Cross-Encoder

**Description:** Investigated why ms-marco scores certain risks near zero. Found the model is sensitive to description
phrasing, not just content. Tested rewording risk descriptions to match ms-marco's preferred style (short, active
voice, "AI systems may..." framing).

**Key finding:** Same concept, same chunk, 5000x score difference based on phrasing:

| Phrasing                                                              | Score  |
|-----------------------------------------------------------------------|--------|
| "Impacts due to leakage and unauthorized use..." (NIST original)      | 0.0001 |
| "AI tools may process, store, or expose personal data..." (rewritten) | 0.9070 |

**Batch rewrite attempt:** Rewrote 33 most-missed risks via Gemma LLM. Individual improvements were dramatic but
end-to-end battery showed regressions — rewritten descriptions competed differently in the cross-encoder ranking,
pushing out previously-accepted candidates.

**Conclusion:** Description rewrites help individual risks but cause collateral damage in the ranking. The cross-encoder
is a relative scorer — improving one description changes scores for all candidates in the batch. Not viable as a batch
approach without per-risk validation.

---

## 2026-05-29: Post-Retrieval Taxonomy Classification

**Description:** Instead of trying to retrieve abstract framework risks (NIST, OWASP) via the retrieval pipeline,
exclude them from retrieval and classify them post-grounding from already-extracted specific risks. One LLM call per
document.

**Approach:** After grounding produces a list of specific risks (Atlas, Credo, MIT, ai-risk-taxonomy) with evidence, ask
the LLM: "Which NIST/OWASP categories do these extracted risks fall under?"

**Configurations tested:**

| Config                               | NIST F1   | OWASP F1 | Macro F1  |
|--------------------------------------|-----------|----------|-----------|
| Baseline (retrieval only)            | 0.505     | 0.545    | 0.758     |
| Classify NIST + OWASP (loose prompt) | 0.686     | 0.418    | 0.733     |
| Classify NIST + OWASP (tight prompt) | 0.731     | 0.533    | 0.733     |
| Classify NIST only                   | **0.702** | 0.533    | **0.754** |

**OWASP analysis:** Classification over-projects OWASP risks. `llm022025-sensitive-information-disclosure` generated 12
false positives (any policy discussing data protection triggers it). OWASP risks are LLM-specific vulnerabilities that
don't map cleanly from general AI policy concepts.

**Conclusion:** Classify NIST only. NIST F1 improved 0.505→0.702 (+39%). OWASP stays in retrieval (0.533 F1, within
noise of baseline 0.545). Macro F1 held at 0.754. Shipped as default configuration.

---

## 2026-05-29: DSPy Judge Prompt Optimization (v1 — random negatives, subsampled)

**Description:** Used DSPy GEPA to optimize the LLM judge prompt. Dataset: 50 train / 30 eval examples (subsampled).
Negatives sampled from pipeline extraction results (spurious + grounding-filtered candidates).

**Results (isolated judge eval):**

- Baseline F1: 82.16%
- Optimized F1: 88.38%
- Improvement: +6.22%

**Optimized prompt key innovations:**

- "Mitigation-to-Risk" reverse logic: if text mandates a safeguard, it's relevant to the risk that safeguard mitigates
- "Subset Rule": broad category text makes specific subset risks relevant
- Specificity limits to control precision
- Synonym/functional/contextual semantic mapping

**End-to-end battery:** The optimized judge degraded overall pipeline F1 (0.754→0.723). The more permissive judge
accepted too many borderline candidates, adding noise and wasting grounding budget.

**Conclusion:** Isolated judge improvement doesn't translate to pipeline improvement. The judge operates in a pipeline
context where precision matters more than recall — false accepts get filtered by grounding but cost LLM calls. Reverted
to original judge prompt.

---

## 2026-05-30: DSPy Judge Prompt Optimization (v2 — hard negatives, full dataset)

**Description:** Re-running GEPA with improved training data. Hard negatives mined using the cross-encoder itself
(highest-scoring non-GT risks per chunk) instead of random pipeline artifacts. Full dataset: 157 train / 207 eval
examples, no subsampling.

**Results (isolated judge eval):**

- Baseline F1: 69.26% (lower than v1's 82.16% — harder negatives make the task more challenging)
- Optimized F1: 80.51%
- Improvement: +11.25% (bigger than v1's +6.22%)

**Optimized prompt key innovations (different from v1):**

- "Granularity Rule": broad "we protect privacy" does NOT make every sub-risk (biometric data, stalking, model
  inversion) relevant — only the category-level risk
- "Compliance Statement" nuance: "we comply with all laws" → regulatory compliance, NOT every specific risk
- Three-step mapping: identify themes → filter by specificity → check conceptual overlap
- More conservative than v1's "mitigation-to-risk" approach

**End-to-end battery (DSPy v2 judge + NIST classification):**

| Metric          | Baseline (no classify) | Old judge + NIST classify | DSPy v2 + NIST classify |
|-----------------|------------------------|---------------------------|-------------------------|
| Evals passed    | 5/20                   | 4/20                      | 5/20                    |
| Macro recall    | 0.706                  | 0.717                     | 0.705                   |
| Macro precision | 0.853                  | 0.819                     | 0.809                   |
| Macro F1        | 0.758                  | 0.754                     | 0.741                   |
| NIST F1         | 0.505                  | 0.702                     | **0.713**               |
| OWASP F1        | 0.545                  | 0.533                     | **0.552**               |

**Conclusion:** The precision-focused v2 prompt (trained on hard negatives) avoids v1's over-acceptance problem.
End-to-end macro F1 at 0.741 — slight regression from baseline 0.758 mostly due to ai-risk-taxonomy LLM
non-determinism, but NIST improved +0.208 F1 and OWASP +0.007. Best combined configuration. Shipped as default
judge prompt.

---

## 2026-05-30: DSPy NIST Classification Prompt Optimization

**Description:** Used DSPy GEPA to optimize the post-retrieval NIST classification prompt. Dataset: 10 train / 10 eval
examples (one per policy), each classifying 12 NIST risk categories from extracted risks.

**Results (isolated classification eval):**

- Baseline F1: 62.50%
- Optimized F1: 67.59%
- Improvement: +5.09%

**Optimized prompt key innovations:**

- "Mitigation vs. Risk" rule: if evidence describes a requirement/guideline, it's a mitigation NOT a risk — don't map it
- Precise domain boundaries: Data Privacy (subject identity) vs Information Security (system integrity) vs
  Information Integrity (societal truth at scale). Single hallucination = Confabulation, NOT Information Integrity.
- Human-AI Configuration requires specific phenomena (anthropomorphism, automation bias) — not general "lack of training"
- Value Chain requires upstream third-party components — not internal tool integration
- Evidence quoting: must cite specific phrases and map to NIST definition

**End-to-end battery (DSPy v2 judge + optimized NIST classification):**

| Metric          | Baseline | Prev best | Optimized classify |
|-----------------|----------|-----------|--------------------|
| NIST precision  | 0.757    | 0.588     | **0.630**          |
| NIST recall     | 0.378    | 0.905     | **0.926**          |
| NIST F1         | 0.505    | 0.713     | **0.750**          |
| Macro precision | 0.853    | 0.809     | **0.826**          |
| Macro F1        | 0.758    | 0.741     | **0.746**          |

**Conclusion:** NIST F1 improved 0.713→0.750. Precision recovered (0.588→0.630) while recall held (0.926). Macro
precision at 0.826 (up from 0.809). Macro F1 at 0.746, approaching baseline 0.758. Shipped as default classification
prompt.

---

## 2026-05-31: DSPy Grounding Prompt Optimization — Experiment Setup

**Description:** Setting up DSPy GEPA optimization for the grounding stage (`attribute.py`). The grounder decides
whether accepted candidates are actually discussed in a text chunk and extracts evidence quotes. Current prompt is
generic ("genuinely discusses that risk concept"). This is the last LLM stage without DSPy optimization.

**Hard negative strategy — no cross-encoder:** Previous experiments established that cross-encoder scores are barely
better than random (AUC ~0.56, experiment 2026-05-28). Instead of cross-encoder hard negative mining (used by
`dspy_judge`), the grounding dataset uses three negative sources:

1. **Same-document, other-chunk negatives:** GT risks whose evidence appears in different chunks of the same policy.
   Hard because they share the same domain and are genuinely relevant to the document — just not to this specific chunk.
   This tests exactly the grounder's core capability: chunk-level vs document-level relevance.
2. **Random catalog negatives:** Random risks from the full Nexus catalog (~524 risks). Easy negatives for baseline
   discrimination.
3. **Pipeline negatives (optional):** If `--run-dir` is provided, loads `grounding_filtered_candidates` from actual
   pipeline runs. These are risks that passed retrieval+judging but were rejected by grounding — the exact distribution
   the grounder sees in production.

**Dataset structure:** Same as judge — (chunk_text, candidate_risks) → expected_verdicts. Each verdict includes
`grounded` (bool) and `expected_quotes` (GT evidence strings from that chunk). 10/10 train/eval policy split.

**Metric:** Combined score = 80% decision F1 (grounded true/false) + 20% quote quality (token-level F1 between
predicted and expected quotes for true positives). Decision F1 is weighted heavily because the grounded/not decision
is the primary optimization target — quote extraction quality is more about model capability than prompt instructions.

**Key risk:** Same as judge v1 — optimizing grounding in isolation might not translate end-to-end. The grounder acts
as a precision filter (rejects candidates that passed retrieval/judging). If GEPA makes it more permissive, noise
increases. The same-document, other-chunk hard negatives are the main defense against this.

**Results (isolated grounding eval):**

- Baseline combined score: 51.74%
- Optimized combined score: 67.18%
- Improvement: +15.44%

**Optimized prompt key innovations:**

- "Mitigation-as-Evidence" principle: if text mandates a procedure to prevent a harm, the risk associated with
  that harm is grounded — policy documents describe mitigations, not risks directly
- "Rule of Explicit Mention": if text explicitly names a risk or gives a real-world example, it's grounded even
  without a specific mitigation in that sentence
- "Foundational Requirements" mapping: training/awareness → AI literacy/human error; governance/audit →
  accountability/legal liability
- Three self-correction heuristics: "Over-Correction Trap" (don't reject because too general), "Security Blanket
  Trap" (don't accept generic security for specific technical risks), "Governance Trap" (governance covers
  accountability but not prompt injection)
- Confidence calibration: high = explicit naming, medium = implied through related requirement, low = tenuous

**End-to-end battery (DSPy optimized grounding prompt):**

**MLflow:** experiment=dspy-ground-optimization

| Metric          | Baseline | Optimized grounding |
|-----------------|----------|---------------------|
| Macro precision | 0.826    | 0.676               |
| Macro recall    | 0.717    | 0.762               |
| Macro F1        | 0.749    | 0.694               |
| AI-Risk-Tax F1  | 0.680    | 0.470 (-0.209)      |
| AILuminate F1   | 0.880    | 0.765 (-0.115)      |
| Credo F1        | 0.763    | 0.773 (+0.010)      |
| IBM Atlas F1    | 0.773    | 0.803 (+0.030)      |
| MIT F1          | 0.800    | 0.816 (+0.016)      |
| NIST F1         | 0.739    | 0.712 (-0.027)      |
| OWASP F1        | 0.500    | 0.546 (+0.046)      |

**Conclusion:** Same pattern as DSPy judge v1 — isolated improvement (+15.44%) does not translate to end-to-end
improvement. Macro F1 dropped 0.749→0.694 (-0.055). The "Mitigation-as-Evidence" principle causes massive
over-grounding in ai-risk-taxonomy (-0.209 F1) and ailuminate (-0.115 F1) by accepting risks that are merely alluded
to through governance/training mandates. The grounder acts as a precision filter; making it more permissive adds noise
that the downstream merge/classify stages cannot compensate for. Reverted to original grounding prompt.

---

## 2026-05-31: DSPy Grounding Prompt Optimization v2 — Pipeline-Mined Negatives

**Description:** Re-ran GEPA with pipeline-mined negatives from `grounding_filtered_candidates` (8,066 negatives from
a baseline battery run) instead of relying solely on same-document other-chunk negatives. This mirrors the approach
that made the judge v2 succeed over v1 — using the actual distribution of false positives the grounder sees in
production.

**MLflow:** experiment=dspy-ground-optimization

**Results (isolated grounding eval):**

- Baseline combined score: 50.32%
- Optimized combined score: 69.85%
- Improvement: +19.53% (larger than v1's +15.44%)

**End-to-end battery — two variants tested:**

| Metric          | Baseline | GEPA v1 (raw) | GEPA v2 (raw) | GEPA v2 (curated) |
|-----------------|----------|---------------|---------------|-------------------|
| Macro precision | 0.838    | 0.676         | —             | 0.711             |
| Macro recall    | 0.677    | 0.762         | —             | 0.737             |
| Macro F1        | 0.749    | 0.694         | —             | 0.724             |
| AI-Risk-Tax F1  | 0.680    | 0.470         | —             | 0.515             |
| AILuminate F1   | 0.880    | 0.765         | —             | 0.765             |

"Curated" variant: manually removed GEPA's "do not be conservative" / "avoid conservatism" language, kept the
mitigation-mapping structure and added precision guardrails back. Improved over raw GEPA v1 (0.724 vs 0.694) but
still worse than baseline (0.749).

**Root cause analysis:** GEPA consistently finds "Mitigation→Risk" mapping prompts that improve isolated recall but
over-ground in production. The F1-based metric rewards balanced precision/recall, but the pipeline needs the grounder
as a precision gate. ai-risk-taxonomy risks have broad, tautological descriptions ("X is defined as X") that the
mitigation mapping connects to any governance text. This taxonomy-specific vulnerability makes the approach
structurally incompatible with permissive grounding.

**Key lesson:** Unlike the judge (where v2 hard negatives fixed the v1 over-acceptance), the grounding stage's
failure mode is metric-driven, not data-driven. Pipeline-mined negatives improved isolated scores further (+19.53%
vs +15.44%) but GEPA still converges on permissive prompts because F1 rewards recall gains. A precision-weighted
metric (F0.5 or precision-floor constraint) would be needed to change this, but the fundamental question is whether
prompt optimization can improve a stage whose original 4-line prompt already achieves near-optimal end-to-end
precision (0.838).

**Conclusion:** Reverted to original grounding prompt. The grounding stage may not be amenable to DSPy prompt
optimization — its simplicity is a feature, not a bug. Future improvement may come from the retrieval/judging stages
(feeding cleaner candidates) rather than the grounding prompt itself.

---

## 2026-06-01: Two-Tier Eval & Pipeline Restructuring

**Description:** Major restructuring of the pipeline and evaluation system. Category-level taxonomies (NIST AI RMF,
OWASP Top 10 LLM, AILuminate, OWASP ASI) are no longer retrieved or classified by the pipeline — they are evaluated
via a static SSSOM cross-taxonomy mapping (`data/risk_to_category.sssom.tsv`, 820 mappings). The LLM classify step
was removed entirely.

**Changes:**
- Removed `extract/classify.py`, classify prompt templates, `--classify-taxonomies` CLI option
- Added `_load_risk_to_category_map()`, `_derive_categories()`, `_evaluate_categories()` to eval.py
- Ground truth stripped to risk-level only (107 category entries removed from 20 existing + 78 from 7 new policies)
- 7 new policies added: amadeus, fs-isac, gray, icrc, npcc, penn, st-johns (27 total)
- GT quality fixes: 3 wrong-risk-ID fixes, 5 insufficient-evidence removals, 13 prohibition-list additions to amadeus

**New baseline (27 policies, run `risk-selected_20260601_160553`):**

| Tier | Macro P | Macro R | Macro F1 |
|------|---------|---------|----------|
| Risk-level | 0.813 | 0.649 | 0.708 |
| NIST category | 0.975 | 0.877 | 0.923 |
| OWASP LLM category | 0.917 | 0.887 | 0.902 |
| AILuminate category | 0.951 | 0.892 | 0.921 |

Pass rate: 5/27 (thresholds: P≥0.60, R≥0.80)

---

## 2026-06-01: Cross-Encoder Model Evaluation (Off-the-Shelf)

**Description:** Evaluated modern off-the-shelf cross-encoder rerankers on the updated dataset (7,208 train / 8,649
eval pairs, 27 policies, risk-level only, category taxonomies excluded from risk pool).

**Models tested:**

| Model | AUC-ROC | Best F1 | Precision | Recall | Speed |
|-------|---------|---------|-----------|--------|-------|
| ms-marco-MiniLM-L-12-v2 (baseline) | 0.636 | 0.340 | 0.243 | 0.567 | 90 p/s |
| **gte-reranker-modernbert-base** | **0.813** | **0.512** | 0.468 | 0.565 | 23 p/s |
| bge-reranker-v2-m3 | 0.788 | 0.466 | 0.522 | 0.420 | 14 p/s |

**Score distribution analysis:**
- ms-marco: scores spread across full 0-1 range (std=0.35). Positives score 0.294 mean, hard negatives 0.338 — model can't distinguish them but the wide spread makes absolute thresholds work.
- GTE: scores cluster in a 0.04-wide band around 0.65 (std=0.14). Better discrimination (AUC 0.813) but absolute thresholds are meaningless — everything scores ~0.65.
- BGE: similar clustering (std=0.05) but weaker discrimination.

**End-to-end battery with GTE (threshold_high=0.68, threshold_low=0.62):**
Regressed badly — 2/27 pass vs 5/27 baseline. The tight score clustering meant the pipeline couldn't separate accept/borderline/discard. Auto-accepted 1,443 candidates for SAP (vs 1,058 baseline) because almost everything scored above 0.68.

**Conclusion:** GTE-reranker-modernbert-base has substantially better discrimination ability (AUC +0.177) but its sigmoid-normalised scores cluster too tightly for the pipeline's absolute-threshold architecture. Two paths: (1) fine-tune GTE on our data to spread scores, or (2) change pipeline to use relative ranking instead of absolute thresholds. Fine-tuning preferred since ms-marco's absolute thresholds work well and changing architecture is high-risk.

---

## 2026-06-01: Over-Extraction Analysis

**Description:** Analysed spurious risk patterns across the 27-policy baseline run.

**Key findings:**
- 19% of spurious evidence spans are under 50 characters (single words like "transparency", "security issues")
- `mit-ai-risk-subdomain-6.3` (devaluation of human effort) is #1 spurious risk (8/27 policies) — matched on any mention of AI generating content
- 63% of spurious risks have "medium" grounding confidence, 29% "high" — grounder not discriminating
- 53% of spurious accepted by LLM judge, 47% by threshold — both paths contribute equally

**Minimum evidence length filter simulation:**
- min_len=40 chars would remove 26 spurious but also 13 true positives — too blunt
- Many "true positives" removed have genuinely thin evidence (single words). 5 of these were GT errors (removed).

**Conclusion:** Hard evidence-length filter is too blunt. The over-extraction problem is best addressed by improving the LLM judge's ability to reject risks matched on generic governance language. DSPy judge re-optimization in progress with updated dataset (27 policies, risk-level only, category taxonomies excluded).

---

## 2026-06-01: DSPy Judge Prompt Optimization v3 — Risk-Level Only Dataset

**Description:** Re-ran GEPA with the updated dataset: 187 train / 244 eval examples from 27 policies (13 train, 14 eval). Category-level taxonomies excluded from the risk pool. Hard negatives mined via cross-encoder from risk-level risks only. Amadeus (train) and ICRC (eval) split to test generalisation on EU AI Act prohibition patterns.

**Results (isolated judge eval):**

- Baseline F1: 70.90% (up from v2's 69.26% — cleaner dataset)
- Optimized F1: 80.23%
- Improvement: +9.33%

**Optimized prompt key innovations (different from v2):**

- "Avoid Over-Literalism": don't reject because the specific technical term is missing — if text manages a domain, risks in that domain are relevant
- Theme-to-risk mapping: governance/process → compliance/governance risks; data protection → privacy risks; security → adversarial risks
- "Crucial Note" on governance frameworks: approval processes, monitoring, contract reviews implicitly address the risks those guardrails prevent
- Specificity guard maintained: general privacy ≠ biometric/facial recognition

**End-to-end battery (v3 judge, 27 policies):**

| Metric          | Baseline (v2 judge) | v3 Judge  | Delta    |
|-----------------|---------------------|-----------|----------|
| Macro F1        | 0.708               | **0.719** | **+0.010** |
| Macro Precision | 0.813               | 0.814     | +0.001   |
| Macro Recall    | 0.649               | **0.665** | **+0.017** |
| Pass rate       | 5/27                | **6/27**  | +1       |
| NIST cat F1     | 0.923               | 0.920     | -0.003   |
| OWASP LLM F1   | 0.907               | **0.935** | +0.028   |

15 policies improved, 8 regressed (mostly small), 4 unchanged. Precision held — the v3 prompt's
"Avoid Over-Literalism" did NOT cause the over-acceptance that killed v1 (which regressed F1 0.754→0.723).

**Why v3 worked where v1 failed:** v1 was trained on random negatives with a subsampled dataset (50 train);
v3 used hard negatives from the cross-encoder with a full dataset (187 train) and risk-level-only risks.
The hard negatives taught the prompt to be inclusive on domain-relevant risks while rejecting
cross-domain false matches. The "Distinguish Specificity" guard (general privacy ≠ biometric) prevented
the over-acceptance pattern.

**Conclusion:** Shipped as default judge prompt. First DSPy judge optimization to improve end-to-end
performance. New baseline: P=0.814, R=0.665, F1=0.719.
