# Prompt 10 — Real ACRS and Rank Instability Analysis

You are working in `/Users/saketmaganti/Projects/causal-agent-bench`.

You are Codex acting as a benchmark statistician.

## Task

Compute real Compact-20 metrics only after postrun audit and scorer sanity pass.

## Absolute rules

- Do not use stub/mock/dry-run data.
- Do not fabricate values.
- Do not hide null/negative findings.
- Do not promote claims beyond pilot evidence.
- Do not run new model/provider calls.

## Preconditions

Required:

- run locked,
- scorer sanity pass or repaired pass,
- C10 preliminary support or limitation recorded,
- complete trajectory set or honest incomplete classification.

## Metrics

Compute clean success, intervention success, ACRS, degradation, ranks, rank shifts, rank correlation, uncertainty, per-family degradation, task-level volatility, and hardest/easiest intervention families.

## Create

- `analysis/compact20_3model/real_acrs_summary.csv`
- `analysis/compact20_3model/real_rank_instability.csv`
- `analysis/compact20_3model/real_per_family_degradation.csv`
- `analysis/compact20_3model/real_uncertainty_summary.csv`
- `reports/REAL_ACRS_RANK_INSTABILITY_COMPACT20.md`

## Claim language

Allowed: “In the Compact-20 pilot…” and “preliminary provider-backed evidence…”.

Forbidden: “CAB proves…”, “causal robustness is established…”, “definitive model ranking…”, “NeurIPS-ready…”.

## Final response format

# Real ACRS and Rank Instability Report

## 1. Executive Summary
## 2. Data Sources
## 3. Clean Success
## 4. Intervention Success
## 5. ACRS
## 6. Rank Instability
## 7. Per-Family Degradation
## 8. Uncertainty and Limitations
## 9. Claim Boundary
## 10. Next Best Action

Final verdict:

- `REAL_ANALYSIS_COMPLETE_PRELIMINARY`
- `REAL_ANALYSIS_BLOCKED_NO_AUDITED_OUTPUTS`
- `REAL_ANALYSIS_BLOCKED_SCORER_SANITY`
