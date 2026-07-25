# Prompt 15 — Scale to 5-Model 100-Task Study

You are working in `/Users/saketmaganti/Projects/causal-agent-bench`.

You are Codex acting as a senior benchmark scaling strategist and budget-aware experiment planner.

## Task

Design the next paper-grade scale-up after Compact-20: a 5-model 100-task study. Do not execute in this prompt.

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

- Compact-20 audit
- Compact-20 analysis
- scorer sanity
- C10 status
- budget policy
- configs

## Actions

1. If Compact-20 failed, create a blocked scale-up report.
2. Create `experiments/5MODEL_100TASK_STUDY_DESIGN.md`.
3. Create `configs/5model_100task_TEMPLATE_NOT_APPROVED.yaml`.
4. Create `docs/approvals/5MODEL_100TASK_APPROVAL_TEMPLATE.md`.
5. Create `reports/5MODEL_100TASK_SCALEUP_READINESS.md`.
6. Include model selection, budget scenarios, sampling plan, statistical power logic, stop conditions, claim upgrades, and artifact requirements.

## Deliverables

- scale-up design
- config template
- approval template
- readiness report

## Tests / Checks

- template non-runnable
- no secrets
- paid calls false
- trajectory count computed
- Compact-20 dependency enforced

## Allowed Commands

- Static inspection commands.
- `git status --short --branch`
- `git diff --stat`
- `python3 scripts/check_evidence_safety.py`
- Targeted fixture-only pytest when needed.

## Final Response Format

# Prompt 15 — Scale to 5-Model 100-Task Study Report

## 1. Executive Summary
## 2. Files Added
## 3. Files Modified
## 4. Evidence State
## 5. Tests/Checks Run
## 6. Commands Not Run
## 7. Blockers
## 8. Next Best Action

Final verdict must be one of:

- `5MODEL_100TASK_PLAN_READY_NO_EXECUTION`
- `5MODEL_100TASK_BLOCKED_COMPACT20_FAILED`
- `5MODEL_100TASK_BLOCKED_CONFIG_SAFETY`
