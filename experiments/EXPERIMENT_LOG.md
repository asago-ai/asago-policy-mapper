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
