# CAB-Vision Safe Publication Strategy

Brutally honest. No fake certainty. Probability categories: `Very low · Low · Medium-low · Medium ·
Medium-high · High`.

---

## 1. Highest possible ceiling
A widely-adopted CVPR benchmark + the quotable finding *"VLMs see but don't reason causally"* — a
new evaluation axis (causal-decision validity) that standard accuracy doesn't predict, with a public
leaderboard others race on. Realistic top outcome: **`CVPR_MAIN_COMPETITIVE`** + citations. Not "safe."

## 2. What makes it CVPR-main competitive
- Image-only-answerable tasks (text-only & caption-only ≈ chance) across ≥3 real visual domains.
- ≥6 VLMs incl. ≥3 frontier; obs→int gap with CIs that survives the oracle-caption ablation.
- Causal-consistency collapse with intact recognition (the decomposition).
- Human-validated subset with IAA; visual failure gallery; pre-registered primary claims.

## 3. What makes it CVPR-main *safe(r)* (no benchmark is truly safe)
Everything in §2 **plus**: 5–10k items, a hidden test + live leaderboard, an expert-validated domain
(e.g., medical triage), and a result that visibly reframes how people evaluate VLMs.

## 4. What keeps it workshop-only
Synthetic-only or single-domain; <1k items; ≤3 models; no caption-only ablation; no human validation;
"models are bad" with no *why*. → CVPR **workshop** at best.

## 5. What causes rejection
Not CV / wrong venue; text shortcuts not ruled out; toy data; weak/few baselines; no CIs; "causal"
overclaimed without validity evidence; ambiguous labels; leakage/contamination; no insight.

## 6. Minimum viable CVPR submission
1–3k validated items, families 1–4 (+6 pairs), ≥3 real domains, ≥5 models (≥2 closed, ≥3 open) +
text-only/caption-only/oracle-caption ablations, bootstrap CIs + paired tests, ≥300-item human-validated
subset, visual failure gallery, pre-registered V1 & V4.

## 7. Ideal CVPR submission
§6 scaled to 5–10k items, families 1–6, ≥4 domains, ≥7 models, full decomposition, larger human study,
hidden test + leaderboard, all V1–V8 adjudicated in the claim ledger.

## 8. Dream (highly-cited) version
10k+ items, images+video+embodied/sim, real+synthetic, causal-graph/intervention/action annotations,
expert validation, public leaderboard, and a finding that becomes a standard VLM evaluation axis.

## 9. Month-by-month (assuming a CVPR 2027 cycle; adjust to the actual deadline)
- **Month 1:** Phases 3–4 — synthetic renderer + first real images; ≥500 items pass `cab_vision/validation`;
  freeze schema; lock annotation guide. *Gate: text-only ablation ≈ chance on a pilot slice.*
- **Month 2:** Phase 5 — paired obs/int + before/after to ≥1.5k items, ≥3 domains; Phase 6 — VLM adapters
  + mock smoke. *Gate: pilot on open models shows obs>int direction.*
- **Month 3:** Phase 8 — pilot eval (open + 1 closed); first money plot + decomposition; iterate on weak
  items. *Gate: obs→int gap with CI excluding 0 on the pilot.*
- **Month 4:** Phase 9 — human validation (≥300, IAA); drop ambiguous; Phase 10 start — full run on all
  models. *Gate: κ ≥ target; V1/V4 trending supported.*
- **Month 5:** Phase 10 finish + Phase 11 — full results, gallery, all claims adjudicated; draft complete.
  *Gate: every paper claim has a linked `supported`/`weakened` ledger row.*
- **Submission month:** Phase 12 — anonymize, supplementary, data card, ethics, repro bundle, leaderboard;
  internal mock review (use `CVPR_REVIEWER_SIMULATION.md`).

## 10. What must be avoided
Overclaiming "causal"; shipping synthetic-only; skipping the caption-only ablation; weak baselines;
no CIs; leakage; ambiguous gold; treating it as an LLM-eval paper; burning API budget before the no-run
cost estimate and the mock smoke pass.

---

## Acceptance-probability estimates (honest)

| Configuration | P(CVPR main) | Notes |
|---|---|---|
| Current CAB as-is (text, 0 runs) | **Very low** | wrong venue; desk-reject. |
| CAB + light visual tasks bolted on | **Very low → Low** | reads as an LLM eval with pictures; workshop at best. |
| CAB-Vision, 1k items, ≥5 models, ablations | **Low → Medium-low** | submit-able; "thin/toy" risk; workshop-likely. |
| CAB-Vision, 5k items, strong baselines, human validation, CIs | **Medium** | real contender if the headline result is strong. |
| Dream: real+synthetic, human/expert validation, strong baselines, leaderboard, decomposition | **Medium → Medium-high** | upper bound for a benchmark paper; "Medium-high" only with a genuinely striking, well-defended finding. |

**Reality check:** CVPR benchmark/dataset papers face above-average skepticism in the main track. Even
the dream version is **Medium-high**, not High. The single biggest lever on these odds is the
**strength + defensibility of the headline causal-failure result**, not dataset size.

## Backup venues (ranked)
1. CVPR **Workshop** (causal/robustness/embodied/VLM) — strong fit, much higher odds.
2. NeurIPS **Datasets & Benchmarks** — the infra was built for this; natural home if CV-main misses.
3. ICCV/ECCV (next cycle), WACV (benchmark-friendly), TMLR (no page pressure, rigor-friendly).
