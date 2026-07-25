# CAB-Vision CVPR Reviewer Simulation

Four reviewers + AC meta-review, assuming the **MVP submission** (`CVPR_SAFE_PUBLICATION_STRATEGY.md` §6).
CVPR scale: 1 (reject) … 5/6 (accept). Scores are *expected* given a competent MVP; weaker execution
drops them a point each.

---

## Reviewer 1 — CV benchmark expert
- **Likely score:** Borderline (3/5).
- **Strengths cited:** clear evaluation protocol; CIs; hidden test + leaderboard; reproducibility bundle;
  anti-shortcut ablations.
- **Attacks:** synthetic share too high; domain coverage thin; dataset-statistics rigor; "is the gold
  truly unambiguous?"
- **Questions:** real vs synthetic split? per-domain n with CIs? how were gold labels adjudicated?
  leakage/contamination procedure?
- **Improves score:** more real images; bigger human-validated subset; per-domain breakdowns; pHash audit.
- **Would reject if:** synthetic-only or <1k items or no human validation.
- **Revisions:** Phases 4, 9; ship `data/cab_vision/DATA_CARD.md` + dedup audit.

## Reviewer 2 — Vision-language model researcher
- **Likely score:** Lean accept (3.5–4/5) **iff** the result is striking.
- **Strengths:** decomposition (recognition intact, decision wrong); strong + current VLM baselines;
  modality ablations.
- **Attacks:** "did you use the best models / right prompts?"; "caption-only loss is your captioner's
  fault"; "CoT/agentic might fix it."
- **Questions:** model versions/dates? prompt sensitivity? oracle-caption result? open vs closed gap?
- **Improves score:** oracle-caption arm; prompt-robustness check; agentic ablation (V5); newest models.
- **Would reject if:** outdated/few models or no oracle-caption control.
- **Revisions:** Phase 6 breadth; V2/V5 evidence.

## Reviewer 3 — Causality / robustness researcher
- **Likely score:** Accept (4/5) if validity is shown; else Borderline.
- **Strengths:** paired observational/interventional design; consistency + sensitivity metrics;
  spurious-cue controls; claim ledger discipline.
- **Attacks:** "is this really *causal* or just harder VQA?"; single-factor-edit validity; "consistency
  metric could be gamed by random flipping."
- **Questions:** how validated that an edit changes only the intended factor? matched controls for cues?
  does intervention-sensitivity separate from accuracy?
- **Improves score:** intervention-isolation validation (visual C10); matched no-cue controls; show CC is
  low while IS-when-shouldn't is also low (not random flipping).
- **Would reject if:** "causal" asserted without single-factor validity evidence.
- **Revisions:** Phase 9 validity arm; `CVPR_CLAIM_LEDGER_TARGET.md` V4 evidence.

## Reviewer 4 — Skeptical, dislikes benchmark papers
- **Likely score:** Reject-leaning (2–3/5); the swing vote.
- **Strengths (grudging):** ablations are unusually careful; reproducible.
- **Attacks:** "yet another benchmark"; "unsurprising that models are bad"; "will anyone use it?";
  "incremental over causal VQA."
- **Questions:** what do we *learn* that changes practice? why is this a finding, not a leaderboard?
- **Improves score:** lead with the finding + decomposition; ranking-instability (standard accuracy
  doesn't predict causal competence, V8); concrete implication for VLM training/eval.
- **Would reject if:** the contribution reads as "a dataset" with no insight.
- **Revisions:** foreground Sec 9 (failure analysis) and V8; cut leaderboard-as-contribution framing.

---

## AC / meta-review risk summary
The paper lives or dies on **(a)** convincing the field it's genuinely *visual* (ablations) and
genuinely *causal* (single-factor validity), and **(b)** a headline finding strong enough to overcome
benchmark-paper skepticism (Reviewer 4). Expected meta-outcome for a competent MVP: **borderline**,
tilting accept if the decomposition + oracle-caption results are clean and the human validation is solid.
Most likely failure mode: split scores (R2/R3 positive, R1/R4 negative) → AC reject for "not mature
enough for main track" → workshop/D&B redirect.

## Top 10 rejection risks
1. Not perceived as CV. 2. Text/caption shortcuts not ruled out. 3. Synthetic/toy data. 4. Weak/few/old
baselines. 5. No CIs / significance. 6. "Causal" overclaimed (no single-factor validity). 7. Ambiguous
gold labels. 8. Leakage/contamination. 9. "Just another benchmark," no insight. 10. Result unsurprising /
no implication.

## Top 10 upgrades (highest ROI first)
1. Oracle-caption + caption-only ablation (kills "not visual" / "captioner's fault"). 2. Perception-vs-
causality decomposition (the headline). 3. Real images across ≥3 domains. 4. ≥6 current VLMs incl.
frontier. 5. Human-validated subset + IAA. 6. Single-factor intervention-isolation validation. 7.
Bootstrap CIs + paired tests on every headline number. 8. Visual failure gallery. 9. Ranking-instability
vs standard accuracy (V8). 10. Pre-registered primary claims + claim ledger in the supplementary.
