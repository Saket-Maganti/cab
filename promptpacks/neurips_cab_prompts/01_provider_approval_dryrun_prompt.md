# Prompt 1 — Provider Approval, Approved Config, and Dry-Run Readiness

You are working in the Causal Agent Bench repository.

You are Cursor Composer acting as a provider-pilot readiness engineer, evidence-governance auditor, and reproducibility reviewer.

## Mission

Move the project from `template_safe_but_not_runnable` to `ready_for_dry_run` without running live provider calls.

This prompt is allowed to create an APPROVED config **only if explicit advisor/budget approval documentation exists** or the user provides a written self-authorization file in the repo.

## Starting assumptions

- Leakage blocker clusters are expected to be 0.
- No paper-eligible runs exist yet.
- No empirical claims are supported yet.
- No live provider run has been executed.
- No `*_APPROVED.yaml` should exist unless approved.

## Absolute rules

Do not:

- run live provider APIs
- set `allow_paid_calls: true`
- run `causal_agent_bench run`
- call local LLMs
- promote claims
- create fake approvals
- create fake results
- mark any run or asset eligible
- modify frozen data
- hide missing approval

Allowed:

- inspect docs/approvals/
- inspect provider template
- create `configs/provider_pilot_tiny_APPROVED.yaml` only if approval docs exist
- keep `allow_paid_calls: false`
- validate config
- plan run
- estimate cost
- run dry-run only if the repo supports dry-run without provider calls
- run no-run reports
- run fixture-only tests

## Tasks

### 1. Inspect approval state

Inspect:

- `docs/approvals/`
- `PROVIDER_PILOT_PREPARATION_STATUS.md`
- `configs/provider_pilot_tiny_template.yaml`
- `docs/PROVIDER_PILOT_DRY_RUN_CHECKLIST.md`
- `docs/COMMAND_AND_RUNTIME_GUIDE.md`

Determine whether approval exists.

Approval must include:

- advisor or self-authorization name
- approval date
- approved maximum budget
- approved provider/model category
- approved maximum trajectories
- approved dry-run
- live-run approval must remain false for now

If approval is missing, create `reports/PROVIDER_APPROVAL_MISSING_BLOCKER.md` and stop.

### 2. Create approved dry-run config only if allowed

If approval exists:

- copy `configs/provider_pilot_tiny_template.yaml`
- create `configs/provider_pilot_tiny_APPROVED.yaml`
- set approval metadata
- keep `allow_paid_calls: false`
- keep live approval false
- keep caps ≤ 5 trajectories
- keep budget cap ≤ approved budget
- do not put API keys in YAML
- use environment variable placeholders for model IDs

### 3. Validate approved config

Run safe commands:

```bash
python3 scripts/check_evidence_safety.py
python3 -m causal_agent_bench validate-config --config configs/provider_pilot_tiny_APPROVED.yaml
python3 -m causal_agent_bench plan-run --config configs/provider_pilot_tiny_APPROVED.yaml
python3 -m causal_agent_bench estimate-run-cost --config configs/provider_pilot_tiny_APPROVED.yaml --output-dir /tmp/cab_provider_approved_cost
python3 -m causal_agent_bench all-no-run-reports --output-dir /tmp/cab_provider_dryrun_readiness
```

If available and documented safe, run dry-run mode only. Do not run live provider calls.

### 4. Add/repair tests

Add or update fixture-only tests for:

- approved config requires approval docs
- template cannot be live runnable
- approved dry-run config keeps `allow_paid_calls: false`
- no API keys in YAML
- dry-run readiness fails if leakage blockers return
- no claim promotion

### 5. Output

Create `reports/PROVIDER_DRYRUN_READINESS_REPORT.md`.

Final response format:

# Provider Approval and Dry-Run Readiness Report

## 1. Executive Summary
## 2. Approval State
## 3. Files Added
## 4. Files Modified
## 5. Approved Config State
## 6. Validation Results
## 7. Dry-Run Readiness
## 8. Tests Added/Updated
## 9. Commands Run
## 10. Commands Not Run
## 11. Evidence State
Confirm 0 eligible scientific runs unless a dry-run artifact is explicitly non-scientific.
## 12. Remaining Blockers
## 13. Next Step

Success condition:

- `configs/provider_pilot_tiny_APPROVED.yaml` exists only with valid approval.
- `allow_paid_calls: false`.
- `validate-config` and `plan-run` pass.
- provider dry-run readiness is reached or blockers are clearly reported.
