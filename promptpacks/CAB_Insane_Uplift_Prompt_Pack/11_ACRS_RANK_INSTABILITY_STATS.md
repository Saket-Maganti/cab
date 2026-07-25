# Prompt 11 — ACRS, Rank Instability, and Statistics

You are working in `/Users/saketmaganti/Projects/causal-agent-bench`.

You are Codex acting as a statistician, benchmark analyst, and claim-safety auditor.

## Task

Analyze only audited real run outputs. Compute clean success, intervention success, ACRS, degradation, rank shifts, per-family effects, and uncertainty.

## Global Evidence Rules

- Do not fabricate results, human annotations, provider outputs, costs, or reviewer labels.
- Do not promote C1-C8/C10 unless the required real evidence exists and the evidence-safety checks pass.
- C9 may remain `engineering_only`; stub/mock/dry-run outputs can only support pipeline wiring.
- Do not mark paper assets eligible manually.
- Do not store API keys, tokens, or secrets in YAML, Markdown, JSON, logs, CSVs, or repo files.
- Provider credentials must be checked only through environment presence checks without printing values.
- Do not leave `allow_paid_calls=true` after any live run.
- Do not run providers, local LLMs, `causal_agent_bench run`, `main_200`, `main_500`, Compact-50, or broad sweeps unless the prompt explicitly allows it and every gate passes.
- Always distinguish `engineering_only`, `zero_cost_local_preliminary`, `provider_pilot_preliminary`, `paper_candidate_pending_audit`, and `paper_eligible`.



## Inspect

- post-run audit
- run directory
- scorer sanity status
- C10 status
- trajectory review CSV
- model metadata

## Actions

1. If audited real outputs are missing, create a blocked report.
2. Compute clean success per model.
3. Compute intervention success per model.
4. Compute ACRS = intervention_success / clean_success with safe handling for clean_success=0.
5. Compute absolute and relative degradation.
6. Compute clean rank, ACRS rank, rank shift, Spearman/Kendall if valid.
7. Compute per-family degradation.
8. Add bootstrap confidence intervals if sample size supports; otherwise label uncertainty pilot-only.
9. Create analysis CSVs and `reports/COMPACT20_3MODEL_ANALYSIS_REPORT.md`.

## Deliverables

- `analysis/compact20_3model/acrs_summary.csv`
- `analysis/compact20_3model/rank_instability.csv`
- `analysis/compact20_3model/per_family_degradation.csv`
- `analysis/compact20_3model/statistical_summary.md`
- analysis report

## Tests / Checks

- refuses stub evidence
- ACRS handles divide-by-zero
- rank shift correct
- CIs honest
- claim wording preliminary

## Allowed Commands

- Static inspection commands.
- `git status --short --branch`
- `git diff --stat`
- `python3 scripts/check_evidence_safety.py`
- Targeted fixture-only pytest when needed.

## Final Response Format

# Prompt 11 — ACRS, Rank Instability, and Statistics Report

## 1. Executive Summary
## 2. Files Added
## 3. Files Modified
## 4. Evidence State
## 5. Tests/Checks Run
## 6. Commands Not Run
## 7. Blockers
## 8. Next Best Action

Final verdict must be one of:

- `ANALYSIS_COMPLETE_PRELIMINARY`
- `ANALYSIS_BLOCKED_NO_AUDITED_RUN`
- `ANALYSIS_BLOCKED_SCORER_OR_C10`
