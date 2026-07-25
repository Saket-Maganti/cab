# Prompt 13 — Failure Gallery and Qualitative Findings

You are working in `/Users/saketmaganti/Projects/causal-agent-bench`.

You are Codex acting as a qualitative trajectory analyst and paper storyteller.

## Task

Create a failure gallery from audited real trajectories showing what agents actually do wrong under interventions.

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

- real trajectory logs
- post-run audit
- scorer sanity
- model outputs
- task/intervention metadata

## Actions

1. Create `analysis/compact20_3model/failure_gallery.csv`.
2. Create `paper/FAILURE_GALLERY_COMPACT20.md`.
3. Create `reports/QUALITATIVE_FINDINGS_COMPACT20.md`.
4. For each example record model, task, condition, intervention family, expected behavior, observed failure, sanitized excerpt, failure category, and scorer status.
5. Use categories such as tool failure recovery, memory contamination, premature-success acceptance, observation conflict, environment-state misread, overconfidence, unnecessary abstention, brittle formatting, planner loop, scorer/gold issue.

## Deliverables

- failure gallery CSV
- paper failure-gallery draft
- qualitative findings report

## Tests / Checks

- examples are from real trajectories
- no secrets/private tokens
- no fabricated outputs
- no unsupported representativeness claims

## Allowed Commands

- Static inspection commands.
- `git status --short --branch`
- `git diff --stat`
- `python3 scripts/check_evidence_safety.py`
- Targeted fixture-only pytest when needed.

## Final Response Format

# Prompt 13 — Failure Gallery and Qualitative Findings Report

## 1. Executive Summary
## 2. Files Added
## 3. Files Modified
## 4. Evidence State
## 5. Tests/Checks Run
## 6. Commands Not Run
## 7. Blockers
## 8. Next Best Action

Final verdict must be one of:

- `FAILURE_GALLERY_READY_PRELIMINARY`
- `FAILURE_GALLERY_BLOCKED_NO_REAL_TRAJECTORIES`
