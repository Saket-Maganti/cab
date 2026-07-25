# CAB-Vision Evaluation Protocol

Metrics, formulas, free-form/MC/action/explanation scoring, anti-shortcut controls, statistical
testing. Reference implementation (prototype): `cab_vision/eval/metrics.py`. Statistics machinery to
reuse: `src/causal_agent_bench/metrics/statistics.py`, `src/causal_agent_bench/analysis/statistics.py`.

**Design principle:** the benchmark must show not only *that* models are wrong but *why* — so the
metric panel decomposes recognition vs causal decision, and pairs are scored for consistency.

---

## 1. Metric definitions

Notation: item *i* has gold answer `g_i`, prediction `p_i`, indicator `1[·]`. A **pair** *(o, v)* has
observational member *o* and interventional member *v* with `expected_answer_change ∈ {yes,no}`.

1. **Observational accuracy** — `Acc_obs = mean_i∈OBS 1[p_i = g_i]`.
2. **Interventional accuracy** — `Acc_int = mean_i∈INT 1[p_i = g_i]`.
   *Headline gap:* `Δ = Acc_obs − Acc_int` (report with CI; the money number).
3. **Counterfactual accuracy** — `Acc_cf` over family-2 (after-edit) items.
4. **Action validity** — `AV = mean_{i∈action} 1[p_i ∈ valid(i)]` (`action_validity`).
5. **Causal consistency** — over scorable pairs: `CC = mean_pairs 1[(p_o ≠ p_v) = (change=yes)]`
   (`causal_consistency`). Penalizes both prior-lock and over-reaction.
6. **Intervention sensitivity** — among `change=yes` pairs: `IS = mean 1[p_o ≠ p_v]`
   (`intervention_sensitivity`). Detects prior-locked models.
7. **Spurious-cue resistance** — over family-3: `SCR = mean 1[p_i ≠ trap_i]`
   (`spurious_cue_resistance`).
8. **Visual grounding score** — when the model emits a cited region/box or referenced object:
   `VG = mean IoU(region_pred, region_causal)` or hit-rate that the cited object is the causal object.
   (v2; requires grounding-capable prompting.)
9. **Explanation faithfulness** — family 5: MC-chain accuracy (v1); rubric/LLM-judge agreement +
   step-grounding overlap (v2). Reuse `analysis/llm_judge.py` *with* the judge-risk controls in
   `docs/LLM_JUDGE_RISKS.md`.
10. **Abstention / defer quality** — where "defer/request-expert" is a valid action (medical):
    reward correct abstention on truly-ambiguous items, penalize abstention on determinable items.
    `Defer_F1` over {should-defer} vs {model-defers}.
11. **Calibration under causal uncertainty** — if the model emits confidence: ECE over interventional
    items; also `Δ-ECE = ECE_int − ECE_obs` (does uncertainty rise appropriately post-intervention?).
12. **Pairwise consistency (orig/intervention)** — same as (5); reported per family and per domain.

**Composite (report, don't over-index on it):** `CausalDecisionScore = mean(Acc_int, CC, SCR, AV)`
with the **gap** and **consistency** highlighted separately so a model can't hide a causal failure
behind high observational accuracy.

---

## 2. How to evaluate each answer type

- **Multiple-choice:** constrain output to an index/letter (parser; reuse the strict-parse philosophy of
  `schemas.py` `ToolCallParseResult`). Map free text → choice by exact/normalized match; unparseable =
  wrong (logged). Randomize choice order per item to kill position bias; fix the permutation by seed.
- **Free-form answers:** normalize, then match to `answer_choices` via canonical synonyms; for genuinely
  open answers use an **LLM judge with a rubric + human-audited subset** (`docs/LLM_JUDGE_PROTOCOL.md`)
  and report judge–human agreement. Prefer MC for headline metrics; free-form for analysis.
- **Action choices:** index ∈ valid set (validity) + exact-best (accuracy). Log the rationale for the gallery.
- **Explanations:** v1 MC over candidate chains (objective). v2 rubric + grounding overlap; never let a
  fluent ungrounded chain score full marks.

---

## 3. Anti-language-shortcut controls (CVPR CRITICAL — these are gates, not just baselines)

Run these as **release gates** on the test split; a family failing the gate is revised:

| Condition | Setup | Pass criterion |
|---|---|---|
| **Text-only** | question + choices, **no image** | accuracy ≤ chance + ε (else item leaks). |
| **Caption-only** | dense caption (from a strong captioner) replaces the image | materially below image+Q (else not visual-causal). |
| **Image+Q (direct VLM)** | the real condition | the reported number. |
| **Image-pair+Q** | both pair members | for paired families. |
| **Oracle-caption** | human/gold caption replaces image | if this *closes* the gap, the failure is perception, not causal reasoning — report it; if it does **not** close the gap, the failure is causal (the strong result). |

The text-only vs caption-only vs image+Q comparison is the core evidence that the benchmark is
**visual** and the failure is **causal**. See `CVPR_BASELINES_PLAN.md`.

---

## 4. Using pairs to expose causal failure
For each `change=yes` pair, the clean storyline is: model is correct observationally, recognizes the
objects, yet does **not** update under the intervention (`IS` low) → a causal failure with intact
perception. Quantify with the **perception-vs-causality decomposition**:
- partition interventional errors into: (a) recognition error (object misread, caught by a recognition
  probe / oracle-caption closing it), vs (b) causal error (recognition correct, decision wrong).
- Headline: large (b) fraction = "seeing is not reasoning."

---

## 5. Statistical testing protocol
- **Confidence intervals:** 95% bootstrap (≥10k resamples) over items, **clustered by scene/pair** so
  paired members aren't treated as independent. Reuse/extend `metrics/statistics.py`.
- **Paired significance:** Acc_obs vs Acc_int via paired bootstrap or McNemar on matched pairs.
- **Model comparisons:** paired bootstrap on shared items; report effect sizes, not just p-values;
  correct for multiple comparisons (Holm) across model pairs.
- **Per-family / per-domain breakdown:** every metric reported overall + per family + per domain, each
  with CIs and n.
- **Pre-registration:** freeze the analysis plan (adapt `docs/STATISTICAL_ANALYSIS_PLAN.md`) before the
  full run to avoid the cherry-pick objection.

---

## 6. Failure taxonomy (drives the gallery + decomposition)
1. **Perception error** — misreads the scene (recognition probe / oracle-caption closes the gap).
2. **Prior override** — answers from object/world priors, ignoring the visible intervention (low IS).
3. **Cue capture** — chosen by the spurious cue (picks `trap`).
4. **Over-reaction** — changes the answer on cosmetic/lighting edits (hurts CC on `change=no`).
5. **Invalid action** — fluent but causally impermissible action.
6. **Ungrounded explanation** — correct/plausible chain not supported by the image.
7. **Mis-abstention** — defers when determinable, or commits when it should defer.

Each test item is auto-tagged where possible (e.g., trap-chosen, pair-unchanged) and surfaced in the
visual failure gallery (extend `analysis/failure_gallery_doc.py`).

---

## 7. Reporting requirements (so reviewers trust it)
- Every headline number: value, 95% CI, n.
- A modality-ablation table (text-only / caption-only / image+Q / oracle-caption).
- A decomposition figure (perception vs causal share of interventional errors).
- Per-family and per-domain tables.
- Human–judge agreement for any LLM-judged metric.
- Cached raw model outputs + scoring script for one-command re-score (reuse `release/repro_bundle.py`).
