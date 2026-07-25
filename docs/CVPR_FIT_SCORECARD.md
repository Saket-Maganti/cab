# CVPR Fit Scorecard — Causal Vision-Agent Bench

Scores are **1–10**. "Current" = the repo **today** (text-only, 0 runs). "Target" = the
state required to be **CVPR-main competitive**. Each row lists the exact repo changes to
close the gap. Brutally honest; no inflation.

> Reading guide: rows 13–14 are **risk** axes (lower current = worse; we want to *reduce* the
> risk, i.e., raise the score). Row 15 is a probability proxy, not a quality score.

| # | Axis | Current | Target | Gap driver |
|---|---|:--:|:--:|---|
| 1 | Computer-vision centrality | **1** | 9 | No vision at all today. |
| 2 | Novelty | 5 | 8 | Causal-pairing idea is novel-ish; must be made *visual*. |
| 3 | Benchmark value | 4 | 8 | Infra strong; no visual data/results. |
| 4 | Dataset quality | 1 | 8 | No images exist. |
| 5 | Evaluation rigor | 6 | 9 | Metrics/stats strong conceptually; unproven on vision. |
| 6 | Baseline strength | 1 | 8 | No VLM baselines run. |
| 7 | Reproducibility | 7 | 9 | Best current asset; extend to VLM runs. |
| 8 | Visual grounding depth | 1 | 9 | Must build image-only-answerable tasks. |
| 9 | Causal reasoning depth | 6 | 9 | Design is causal; needs visual interventions + validity proof. |
| 10 | Breadth across domains | 3 | 7 | Text domains don't count; need 3–5 visual domains. |
| 11 | Failure analysis quality | 5 | 9 | Have gallery infra; need visual perception-vs-causality decomposition. |
| 12 | Reviewer excitement | 3 | 8 | Needs a striking headline result. |
| 13 | Risk: "just another benchmark" (10 = low risk) | 3 | 7 | Mitigate via causal pairing + ablations. |
| 14 | Risk: "not CV enough" (10 = low risk) | 1 | 8 | Mitigate via image-only tasks + visual gallery. |
| 15 | P(CVPR main accept) proxy | 1 | 6 | See `CVPR_SAFE_PUBLICATION_STRATEGY.md`. |

**Aggregate:** current ≈ **3.5/10** as a *CVPR* artifact (it is ~8/10 as a *NeurIPS-infra* artifact).
Target ≈ **8/10**.

---

## Per-axis detail

### 1. Computer-vision centrality — 1 → 9 **(CVPR CRITICAL)**
- **Why:** `grep` over `src/` returns **0** vision references; deps lack `torch/Pillow/transformers`.
  CVPR's first filter is "is the central contribution about images/video?" Today: no.
- **To reach target:** ship `data/cab_vision/images/*` (real + synthetic), make ≥70% of items
  *image-only-answerable* (verified by the text-only ablation failing), add `cab_vision/providers`
  for image-input VLMs. **Evidence produced:** modality-ablation table showing text-only ≈ chance.
- **Reviewer objection addressed:** "wrong venue / not CV."

### 2. Novelty — 5 → 8
- **Why:** Causal/counterfactual VQA exists (e.g., CLEVRER-style, VQA-CP, Winoground-style
  compositionality). Your novelty is **paired observational↔interventional visual decisions +
  consistency metric + action validity**, not "another causal VQA set."
- **To reach target:** foreground `intervention_consistency` pairs and `action_selection`
  (decision, not description). Position against recognition/grounding benchmarks in
  `docs/RELATED_WORK_*` (reframe for vision).
- **Evidence:** related-work matrix where no prior benchmark fills the "visual + interventional +
  decision + paired-consistency" cell. **Objection addressed:** "incremental over causal VQA."

### 3. Benchmark value — 4 → 8
- **Why:** Value = does the community adopt it + does it reveal something. Infra supports adoption;
  no findings yet.
- **To reach target:** public split + hidden test + leaderboard schema (you have
  `docs/leaderboard_schema_v1.json` to adapt), plus a finding others will want to beat.
- **Evidence:** leaderboard + a clear SOTA gap. **Objection:** "will anyone use it?"

### 4. Dataset quality — 1 → 8 **(CVPR CRITICAL)**
- **Why:** No images. Placeholders only (`data/cab_vision/examples/sample_tasks.jsonl`).
- **To reach target:** 1–3k validated items (v1), curated/own/permissive images, sha256 + perceptual
  hash dedup, human-validated subset, ambiguity adjudication.
- **Evidence:** data card + IAA on validated subset. **Objection:** "toy/synthetic/ambiguous."

### 5. Evaluation rigor — 6 → 9
- **Why:** `metrics/statistics.py` + bootstrap + paired tests exist; ACRS pattern is principled.
  But unexercised on vision; metrics like causal-consistency need vision-specific definition (done in
  `cab_vision/eval/metrics.py`).
- **To reach target:** wire bootstrap CIs + paired significance into the visual metric panel; pre-register
  the analysis (`docs/STATISTICAL_ANALYSIS_PLAN.md` → CVPR variant).
- **Evidence:** every headline number with 95% CI + paired test. **Objection:** "no CIs / cherry-picked."

### 6. Baseline strength — 1 → 8 **(CVPR CRITICAL)**
- **Why:** No VLM has been run. CVPR expects strong closed + open baselines.
- **To reach target:** ≥3 frontier closed VLMs + ≥3 open (Qwen-VL, InternVL, LLaVA) + ablations
  (text-only, caption-only, random, majority). See `CVPR_BASELINES_PLAN.md`.
- **Evidence:** results table with ≥6 models. **Objection:** "weak/outdated baselines."

### 7. Reproducibility — 7 → 9
- **Why:** Strongest current axis (`release/repro_bundle.py`, `scripts/reproduce_artifact.py`, CI).
- **To reach target:** extend bundle to capture VLM versions/prompts/seeds; cache raw VLM outputs.
- **Evidence:** one-command re-score from cached outputs. **Objection:** "can't reproduce API results."

### 8. Visual grounding depth — 1 → 9 **(CVPR CRITICAL)**
- **Why:** none yet.
- **To reach target:** tasks where the *pixels* decide (occlusion, support, before/after edits),
  plus a visual-grounding score (does the cited region match the causal region).
- **Evidence:** grounding score + caption-only-fails ablation. **Objection:** "answerable from text."

### 9. Causal reasoning depth — 6 → 9
- **Why:** Design is genuinely causal (do-style interventions, counterfactual pairs). But "causal"
  validity must be *shown* for vision (your own `FOCUSED_PROJECT_THESIS.md` already cautions on this).
- **To reach target:** intervention-isolation validation for visual edits (single-factor change),
  consistency metric, human agreement that the edit changes only the intended factor.
- **Evidence:** C10-style visual validity report + consistency results. **Objection:** "calls correlation causal."

### 10. Breadth across domains — 3 → 7
- **Why:** Current domains are text (travel/shopping/calendar).
- **To reach target:** ≥3 visual domains in v1 (e.g., physical/household, driving, safety; +medical as stretch).
- **Evidence:** per-domain results table. **Objection:** "single narrow domain."

### 11. Failure analysis quality — 5 → 9
- **Why:** `analysis/failure_gallery_doc.py` exists but for text.
- **To reach target:** visual failure gallery (image + gold + model + spurious cue), failure taxonomy
  (perception error vs causal error vs prior-override vs cue-capture), perception-vs-causality decomposition.
- **Evidence:** taxonomy figure + decomposition (recognition correct, decision wrong). **Objection:** "shows that, not why."

### 12. Reviewer excitement — 3 → 8
- **Why:** No result to be excited about yet.
- **To reach target:** a quotable headline (see Audit §5). **Evidence:** the money figure
  (interventional vs observational, with caption-only ablation overlaid). **Objection:** "unsurprising."

### 13. Risk "just another benchmark" — 3 → 7 (raise = de-risk)
- **Mitigation:** make the *finding* (causal failure under intact perception) the contribution, with the
  dataset as the instrument. **Evidence:** decomposition figure. 

### 14. Risk "not CV enough" — 1 → 8 (raise = de-risk)
- **Mitigation:** image-only tasks, visual gallery, perceptual-hash contamination audit, grounding score.

### 15. P(accept) proxy — 1 → 6
- See category estimates in `CVPR_SAFE_PUBLICATION_STRATEGY.md`.

---

## Why CVPR reviewers might reject (concise)
1. Not CV / wrong venue (if vision isn't central). 2. "Just another benchmark." 3. Text shortcuts
not ruled out. 4. Synthetic/toy data. 5. Weak or few baselines. 6. No CIs/significance. 7. "Causal"
overclaimed without validity evidence. 8. Ambiguous gold labels. 9. Data leakage/contamination.
10. No actionable insight beyond "models are bad."

## What must be PROVEN to survive review
- Tasks are **image-only-answerable** (text-only & caption-only ≈ chance).
- The interventional gap is **real** (CIs, paired tests) and **not a recognition failure**.
- Visual interventions are **single-factor valid** (human-validated subset, IAA reported).
- Findings hold across **multiple frontier VLMs** and **multiple domains**.

## What would make it genuinely exciting
SOTA VLMs with ≥90% object recognition still pick causally invalid actions; oracle captions do
**not** close the gap; causal-consistency is near chance. → "Seeing is not reasoning."

## Minimum evidence before submission
1–3k validated items across ≥3 domains and ≥4 families; ≥6 models (≥3 closed, ≥3 open); modality
ablation; bootstrap CIs + paired tests; ≥300-item human-validated subset with IAA; visual failure gallery.
