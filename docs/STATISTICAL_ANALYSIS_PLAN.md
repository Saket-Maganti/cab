# Statistical Analysis Plan

**Status:** Plan only — **no results computed**  
**Scope:** Defines analysis for Stage C–F provider runs

---

## 1. Paired clean/intervention comparisons (C1)

- Unit: base task pair (same `base_task_id`)
- Metrics: clean success, intervention success, absolute Δ, relative Δ
- Test: paired bootstrap or McNemar for binary success (per agent)
- Report: mean Δ with **95% CI** per agent and pooled

---

## 2. Confidence intervals

- Default: **95%** bootstrap CI, 10,000 resamples, stratified by domain
- Report per-agent and pooled estimates
- Never report point estimates without CIs in headline claims

---

## 3. Bootstrap procedure

```
For each agent a:
  For b in 1..B:
    Resample base_task_ids with replacement
    Compute metric m_b on resampled pairs
  CI = percentile(m_, 2.5, 97.5)
```

Seed pinned in analysis config; log in paper appendix.

---

## 4. Multiple-comparison caution

- Many intervention families × many agents → pre-specify **primary** families for headline
- Secondary families: report with FDR or clearly label exploratory
- Do not cherry-pick best family after seeing results

---

## 5. Model ranking stability (C4)

- Rank agents by clean success vs ACRS
- Spearman ρ with bootstrap CI
- Report rank changes ≥2 positions
- Minimum **≥5 models** for C4 claim

---

## 6. Effect sizes

- Absolute degradation (percentage points)
- Relative degradation (ratio)
- ACRS delta vs clean success correlation
- Per-family Cohen's h or log-odds for binary success (supplement)

---

## 7. Per-intervention breakdown (C2)

- Stratify by `intervention_type`
- Minimum **n ≥ 20 pairs per family** for stable CI (main scale)
- Flag under-powered families explicitly

---

## 8. Human agreement metrics (C3, C10)

- Percent agreement on failure category
- Cohen's κ (2 annotators) / Fleiss' κ (>2)
- Exclude `invalid_sample_flag=true` items
- Report κ with **CI** (bootstrap or analytic per plugin)

**No κ values until annotations exist — do not fabricate.**

---

## 9. Minimum sample size warnings

| Scale | Can conclude | Cannot conclude |
|-------|--------------|-----------------|
| Stage B (≤5 traj) | Pipeline works | C1–C8, C4, C10 |
| Stage C (20) | Directional pilot hints | Headline NeurIPS claims |
| Stage D (100) | Partial C1/C2 with wide CIs | Final ranking claims |
| Stage F (500) | Headline claims if powered | — |

**Tiny pilot cannot support final claims** — use for debugging only.

---

## 10. Analysis implementation

- `src/causal_agent_bench/analysis/statistics.py`
- `src/causal_agent_bench/metrics/statistics.py`
- Export via `export-leaderboard`, `make_paper_assets.py`

**Run analysis only on eligible complete runs post-audit.**

---

## 11. Pre-registration discipline

Before Stage F:

1. Lock primary RQs (C1–C4)
2. Lock primary intervention families
3. Lock model set categories
4. Lock eval split (`test` for headline)

Changes require claim-ledger note + limitations disclosure.
