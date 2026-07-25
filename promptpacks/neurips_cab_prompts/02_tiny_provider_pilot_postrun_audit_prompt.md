# Prompt 2 — Tiny Live Provider Pilot and Post-Run Audit

You are working in the Causal Agent Bench repository.

You are Cursor Composer acting as a cautious benchmark execution lead, provider-cost safety reviewer, run auditor, and evidence-governance enforcer.

## Mission

Run the first tiny provider-backed pilot **only if all live-run gates pass**, then audit it thoroughly.

This is the first real scientific evidence step. It must be tiny, capped, and audited.

## Starting assumptions

- `configs/provider_pilot_tiny_APPROVED.yaml` exists.
- Dry-run has passed.
- Leakage blockers are 0.
- Advisor/budget approval exists.
- The config is capped at ≤5 trajectories.
- Live approval must be explicit.
- The expected estimated cost is small and within approved budget.

## Absolute rules

Do not run live provider calls unless:

- `configs/provider_pilot_tiny_APPROVED.yaml` exists
- approval docs exist
- `allow_paid_calls: true` is set only in the APPROVED config
- `approved_for_live_run: true`
- budget approval exists
- provider/model env vars are configured
- cost estimate is below approved budget
- leakage blockers are 0
- preflight says live-run ready

Do not:

- run more than the approved cap
- run main benchmark
- run local LLMs
- promote claims automatically
- mark assets eligible manually
- fabricate missing outputs
- ignore failed or incomplete runs

## Tasks

### 1. Pre-live safety gate

Run:

```bash
python3 scripts/check_evidence_safety.py
python3 -m causal_agent_bench all-no-run-reports --output-dir /tmp/cab_pre_tiny_live_pilot
python3 -m causal_agent_bench validate-config --config configs/provider_pilot_tiny_APPROVED.yaml
python3 -m causal_agent_bench plan-run --config configs/provider_pilot_tiny_APPROVED.yaml
python3 -m causal_agent_bench estimate-run-cost --config configs/provider_pilot_tiny_APPROVED.yaml --output-dir /tmp/cab_tiny_live_cost
```

If any gate fails, stop and write `reports/TINY_PROVIDER_PILOT_BLOCKED.md`.

### 2. Tiny live provider pilot

If live gate passes, run only the approved tiny config:

```bash
python3 -m causal_agent_bench run --config configs/provider_pilot_tiny_APPROVED.yaml
```

Do not run anything else.

### 3. Post-run audit

Immediately after run:

- identify run directory
- check incomplete markers
- check metadata
- check trajectory count
- check provider class
- check cost actual vs estimate
- inspect every trajectory manually
- compare scorer verdicts to human judgment manually
- run run-health / summarize-run if available
- run paper asset eligibility
- run claim-evidence matrix
- run evidence safety
- run all-no-run reports

### 4. Scorer sanity review

Create `reports/TINY_PROVIDER_PILOT_SCORER_SANITY.md`.

For each trajectory:

- task id
- clean/intervention
- expected answer
- model final answer
- deterministic scorer result
- human manual judgment
- agreement yes/no
- issue type
- recommended fix

### 5. Evidence classification

Do not promote headline claims.

Allowed classification:

- tiny provider pilot
- preliminary/debug evidence
- can support pipeline sanity only
- cannot support NeurIPS final claims
- cannot support C1–C8 headline claims
- may inform scorer/gold/output fixes

### 6. Tests

Add/update tests for:

- tiny pilot cannot promote claims
- tiny pilot artifacts not paper-eligible by default
- scorer sanity report required
- incomplete provider runs blocked
- cost cap enforcement

### 7. Output

Create:

- `reports/TINY_PROVIDER_PILOT_POSTRUN_AUDIT.md`
- `reports/TINY_PROVIDER_PILOT_SCORER_SANITY.md`

Final response format:

# Tiny Provider Pilot and Post-Run Audit Report

## 1. Executive Summary
## 2. Pre-Live Gate Result
## 3. Run Config
## 4. Run Directory
## 5. Cost / Runtime
## 6. Trajectory Audit
## 7. Scorer Sanity
## 8. Evidence Classification
## 9. Claim Status
## 10. Tests Added/Updated
## 11. Commands Run
## 12. Commands Not Run
## 13. Current Evidence State
## 14. Issues Found
## 15. Next Step

Success condition:

- Tiny provider pilot executed only if approved.
- Every trajectory manually audited.
- No claims promoted.
- Scorer sanity is known.
