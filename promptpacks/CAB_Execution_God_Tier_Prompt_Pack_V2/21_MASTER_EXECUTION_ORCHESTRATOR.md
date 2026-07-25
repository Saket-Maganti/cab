# Master Execution Orchestrator — CAB V2

You are working in:

`/Users/saketmaganti/Projects/causal-agent-bench`

You are Codex acting as a senior ML benchmark execution engineer, evidence auditor, and paper strategist.

## Mission

Run CAB’s next execution-focused upgrade path from blocked scaffold to real evidence.

## Known state before this pack

The previous autorun ended with:

`PARTIAL_SUCCESS_BLOCKED_BY_MISSING_INPUTS`

Key missing inputs:

- human review,
- live provider approval,
- API credentials,
- real provider run,
- postrun audit,
- ACRS/rank-instability analysis.

## Your execution policy

Do not start by adding more broad docs. Start with the nearest blocker.

## Sequence

1. Run `01_HUMAN_REVIEW_COMPLETION_DRIVER.md`.
2. If human review missing, stop and tell user exactly what to fill.
3. If human review complete, run `02_COMPACT20_REPAIR_FROM_HUMAN_REVIEW.md`.
4. Then run `03_C10_VALIDATION_AND_SLICE_LOCK.md`.
5. Then run approval/preflight prompts.
6. Only execute provider run if all live gates pass.
7. After execution, immediately audit, review, score, analyze, and generate assets.
8. After Compact-20 is complete, decide whether to run 5-model/100-task.

## Session report format

# CAB V2 Execution Session Report

## 1. Prompts Attempted
## 2. Prompts Completed
## 3. Prompts Blocked
## 4. Files Added
## 5. Files Modified
## 6. Evidence Created
## 7. Claim Changes
## 8. Commands Run
## 9. Commands Not Run
## 10. Current Blocker
## 11. Next Best Action

Final verdict:

- `BLOCKED_HUMAN_REVIEW_REQUIRED`
- `READY_FOR_PROVIDER_APPROVAL`
- `PREFLIGHT_READY`
- `LIVE_EVIDENCE_CREATED_PENDING_AUDIT`
- `COMPACT20_PRELIMINARY_EVIDENCE_COMPLETE`
- `READY_FOR_5MODEL_SCALEUP`
