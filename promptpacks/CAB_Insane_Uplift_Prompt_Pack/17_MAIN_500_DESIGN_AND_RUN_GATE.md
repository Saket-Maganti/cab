# Prompt 17 — Main-500 Design and Run Gate

You are working in `/Users/saketmaganti/Projects/causal-agent-bench`.

You are Codex acting as a large-scale benchmark execution architect and budget-risk auditor.

## Task

Prepare the full Main-500 study design and run gate. Do not execute it.

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

- Compact-20 evidence
- 5-model 100-task evidence or design
- scorer/human validation reports
- budget policy
- current main_500 configs

## Actions

1. Create `experiments/MAIN_500_STUDY_DESIGN.md`.
2. Create `configs/main_500_multi_provider_TEMPLATE_NOT_APPROVED.yaml`.
3. Create `docs/approvals/MAIN_500_BUDGET_APPROVAL_TEMPLATE.md`.
4. Create `reports/MAIN_500_RUN_GATE.md`.
5. Include family balance, model set, repeats/seeds, cost scenarios, rate-limit strategy, failure recovery, partial-run handling, post-run audit, statistical analysis, claim upgrade criteria, and paper asset criteria.

## Deliverables

- Main-500 design
- non-runnable config template
- approval template
- run gate report

## Tests / Checks

- no execution
- no secrets
- paid calls false
- requires earlier evidence
- requires explicit budget approval

## Allowed Commands

- Static inspection commands.
- `git status --short --branch`
- `git diff --stat`
- `python3 scripts/check_evidence_safety.py`
- Targeted fixture-only pytest when needed.

## Final Response Format

# Prompt 17 — Main-500 Design and Run Gate Report

## 1. Executive Summary
## 2. Files Added
## 3. Files Modified
## 4. Evidence State
## 5. Tests/Checks Run
## 6. Commands Not Run
## 7. Blockers
## 8. Next Best Action

Final verdict must be one of:

- `MAIN_500_DESIGN_READY_NO_EXECUTION`
- `MAIN_500_DESIGN_BLOCKED_EARLIER_EVIDENCE`
