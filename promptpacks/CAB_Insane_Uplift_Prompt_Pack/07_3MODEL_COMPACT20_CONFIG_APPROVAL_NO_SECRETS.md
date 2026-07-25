# Prompt 07 — 3-Model Compact-20 Config Approval, No Secrets

You are working in `/Users/saketmaganti/Projects/causal-agent-bench`.

You are Codex acting as a provider-pilot configuration engineer and evidence-safety auditor.

## Task

Create a non-secret, approval-gated config for the first real 3-model Compact-20 pilot. Do not run it.

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

- `configs/compact20_3model_TEMPLATE_NOT_APPROVED.yaml`
- `configs/provider_pilot_tiny_APPROVED.yaml`
- approval docs
- Compact-20 reviewed manifest
- budget policies
- provider run docs

## Actions

1. Create `configs/compact20_3model_APPROVAL_REQUIRED.yaml`.
2. Create `docs/approvals/COMPACT20_3MODEL_PILOT_APPROVAL_TEMPLATE.md`.
3. Create `reports/COMPACT20_3MODEL_CONFIG_SAFETY_REPORT.md`.
4. Config must keep `allow_paid_calls: false`, `approved_for_live_run: false`, `scientific_claims_allowed: false`, and `paper_asset_eligibility: false`.
5. Config must represent 20 task pairs × 2 conditions × 3 models = 120 planned trajectories.
6. Use placeholder model roles: frontier/API, strong open/local, cheap baseline.
7. No API keys or secret fields.

## Deliverables

- `configs/compact20_3model_APPROVAL_REQUIRED.yaml`
- approval template
- config safety report

## Tests / Checks

- config non-runnable without approval
- paid calls false
- no secrets
- trajectory count = 120
- claims/paper eligibility false

## Allowed Commands

- Static inspection commands.
- `git status --short --branch`
- `git diff --stat`
- `python3 scripts/check_evidence_safety.py`
- Targeted fixture-only pytest when needed.

## Final Response Format

# Prompt 07 — 3-Model Compact-20 Config Approval, No Secrets Report

## 1. Executive Summary
## 2. Files Added
## 3. Files Modified
## 4. Evidence State
## 5. Tests/Checks Run
## 6. Commands Not Run
## 7. Blockers
## 8. Next Best Action

Final verdict must be one of:

- `CONFIG_READY_AWAITING_APPROVAL`
- `CONFIG_BLOCKED_MISSING_COMPACT20`
- `CONFIG_BLOCKED_SAFETY_FAILURE`
