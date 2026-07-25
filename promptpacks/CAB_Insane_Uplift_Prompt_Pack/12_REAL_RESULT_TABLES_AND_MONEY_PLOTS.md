# Prompt 12 — Real Result Tables and Money Plots

You are working in `/Users/saketmaganti/Projects/causal-agent-bench`.

You are Codex acting as a paper-figure engineer and evidence-safety auditor.

## Task

Generate paper-ready result tables and money plots only from audited real analysis outputs.

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

- ACRS summary CSV
- rank instability CSV
- per-family degradation CSV
- post-run audit
- scorer sanity report
- model metadata

## Actions

1. Create `.tex` and `.csv` tables for model metadata, clean vs intervention success, ACRS/rank instability, per-family degradation, scorer sanity, and C10/manual validation linkage.
2. Create figures: clean-rank vs ACRS-rank, rank-shift lollipop, per-family heatmap, clean vs intervention bars.
3. Create `paper/FIGURE_CAPTIONS_COMPACT20_REAL.md`.
4. Create `reports/PAPER_ASSET_ELIGIBILITY_COMPACT20.md`.
5. Caption all pilot-only results as `Compact-20 pilot` unless larger evidence exists.

## Deliverables

- paper tables
- paper figures
- captions
- paper asset eligibility report

## Tests / Checks

- no plot/table from stub evidence
- tables cite source analysis CSV
- no “main result” wording for pilot-only data
- paper eligibility follows audit

## Allowed Commands

- Static inspection commands.
- `git status --short --branch`
- `git diff --stat`
- `python3 scripts/check_evidence_safety.py`
- Targeted fixture-only pytest when needed.

## Final Response Format

# Prompt 12 — Real Result Tables and Money Plots Report

## 1. Executive Summary
## 2. Files Added
## 3. Files Modified
## 4. Evidence State
## 5. Tests/Checks Run
## 6. Commands Not Run
## 7. Blockers
## 8. Next Best Action

Final verdict must be one of:

- `PILOT_ASSETS_CREATED_PRELIMINARY`
- `ASSET_CREATION_BLOCKED_NO_REAL_ANALYSIS`
- `ASSET_CREATION_BLOCKED_EVIDENCE_SAFETY`
