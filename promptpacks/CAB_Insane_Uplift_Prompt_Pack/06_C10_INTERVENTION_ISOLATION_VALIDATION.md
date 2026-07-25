# Prompt 06 — C10 Intervention Isolation Validation

You are working in `/Users/saketmaganti/Projects/causal-agent-bench`.

You are Codex acting as a C10 validation analyst and benchmark construct-validity auditor.

## Task

Analyze completed real human review forms and decide whether Compact-20 intervention isolation is strong enough to proceed. Do not fabricate missing reviews.

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

- `data/human_validation/compact20_real_review/*.csv`
- C10 protocol
- adjudication templates
- task manifest
- exclusion list
- claim ledger

## Actions

1. If real reviews are missing, create `reports/C10_VALIDATION_BLOCKED_MISSING_HUMAN_REVIEWS.md` and stop.
2. If real reviews exist, compute review coverage, agreement, isolation pass rate, goal-preservation pass rate, gold correctness pass rate, disagreements, and exclusions.
3. Create `reports/C10_INTERVENTION_ISOLATION_VALIDATION.md` and `.csv`.
4. Create `data/compact20_reviewed/compact20_validated_or_blocked_manifest.json`.
5. Only update C10 if thresholds pass and project policy allows; otherwise keep C10 pending/blocked.

## Deliverables

- C10 validation report or blocked report
- validation CSV
- validated/blocked Compact-20 manifest

## Tests / Checks

- proxy-only validation rejected
- single-reviewer validation rejected unless policy allows
- C10 promotion rejected if thresholds fail
- evidence safety passes

## Allowed Commands

- Static inspection commands.
- `git status --short --branch`
- `git diff --stat`
- `python3 scripts/check_evidence_safety.py`
- Targeted fixture-only pytest when needed.

## Final Response Format

# Prompt 06 — C10 Intervention Isolation Validation Report

## 1. Executive Summary
## 2. Files Added
## 3. Files Modified
## 4. Evidence State
## 5. Tests/Checks Run
## 6. Commands Not Run
## 7. Blockers
## 8. Next Best Action

Final verdict must be one of:

- `C10_PRELIMINARY_SUPPORTED_COMPACT20_ONLY`
- `C10_BLOCKED_MISSING_HUMAN_REVIEWS`
- `C10_FAILED_ISOLATION_THRESHOLD`
- `C10_NEEDS_ADJUDICATION`
