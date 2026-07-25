# Prompt 05 — Real Human Review Packet, Not Proxy

You are working in `/Users/saketmaganti/Projects/causal-agent-bench`.

You are Codex acting as a human-validation operations lead and evidence-boundary enforcer.

## Task

Create the real human review packet for Compact-20 task clarity, gold policy, and intervention quality. Do not fill annotations.

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

- `data/compact20_reviewed/`
- existing human validation protocols
- proxy/synthetic review files if any
- C10 protocol
- gold policy docs
- task review templates

## Actions

1. Create `data/human_validation/compact20_real_review/README.md`.
2. Create `reviewer_instructions.md`, `task_clarity_review.csv`, `gold_policy_review.csv`, `intervention_isolation_review.csv`, and `adjudication_template.csv`.
3. Create `HUMAN_REVIEW_PACKET_STATUS.md` stating annotations collected = 0, C10 pending, paper eligibility false.
4. Ensure proxy/AI review files cannot be counted as human validation.
5. Make CSVs header-only unless real human rows already exist externally and are explicitly imported with provenance.

## Deliverables

- human review packet under `data/human_validation/compact20_real_review/`
- status report with evidence boundaries

## Tests / Checks

- CSVs are header-only if no real reviews exist.
- No `ai_proxy_review` counted as human.
- C10 remains unsupported.
- Evidence safety passes.

## Allowed Commands

- Static inspection commands.
- `git status --short --branch`
- `git diff --stat`
- `python3 scripts/check_evidence_safety.py`
- Targeted fixture-only pytest when needed.

## Final Response Format

# Prompt 05 — Real Human Review Packet, Not Proxy Report

## 1. Executive Summary
## 2. Files Added
## 3. Files Modified
## 4. Evidence State
## 5. Tests/Checks Run
## 6. Commands Not Run
## 7. Blockers
## 8. Next Best Action

Final verdict must be one of:

- `REAL_HUMAN_REVIEW_PACKET_READY`
- `HUMAN_REVIEW_PACKET_BLOCKED`
