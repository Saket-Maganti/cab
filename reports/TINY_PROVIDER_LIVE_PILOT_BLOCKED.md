# Tiny Provider Live Pilot Blocked

Generated: 2026-06-13

Final verdict: `LIVE_PILOT_BLOCKED`

## Executive Summary

The tiny live provider pilot was **not run**. The repo remains dry-run/preflight-ready, but the live gate does not pass.

Blocking conditions:

- The self-authorization file is internally contradictory: it contains `Live-run approval: Yes`, but its final authorization statement still says only dry-run/preflight is authorized and live paid provider calls are not authorized.
- `configs/provider_pilot_tiny_APPROVED.yaml` still has `approval.approved_for_live_run: false`.
- Provider credentials are not available in the environment: `OPENAI_API_KEY` is missing.
- `validate-config`, `estimate-run-cost`, and `dry-run` all report live execution remains blocked while `allow_paid_calls=false` and the provider key is missing.

No provider API call was made. No paid call was made. The config was not changed to `allow_paid_calls=true`.

## Inspected Files

- `docs/approvals/SELF_AUTHORIZATION_TINY_PROVIDER_PILOT.md`
- `configs/provider_pilot_tiny_APPROVED.yaml`
- `reports/TINY_PROVIDER_DRYRUN_READINESS.md`
- `PROVIDER_PILOT_PREPARATION_STATUS.md`
- `docs/COMMAND_AND_RUNTIME_GUIDE.md`

## Live Approval Validation

`docs/approvals/SELF_AUTHORIZATION_TINY_PROVIDER_PILOT.md` contains:

- `Live-run approval: Yes`

However, the same file also contains:

- `I authorize only the dry-run/preflight preparation stage at this time.`
- `I do not authorize live paid provider calls yet.`

This is not unambiguous live authorization. Under the strict gate, live execution is blocked until the authorization statement is corrected to match the live approval marker.

## Config Gate

Config: `configs/provider_pilot_tiny_APPROVED.yaml`

Observed safety fields:

- `allow_paid_calls: false`
- `approval.approved_for_live_run: false`
- `max_instances: 5`
- `limits.max_trajectories: 5`
- `limits.stop_after_trajectories: 5`
- `budget_cap_usd: 5.0`
- `budget.max_total_usd: 5.0`
- `budget.max_calls: 30`
- `scientific_evidence: false`
- `scientific_evidence_level: preliminary_or_engineering`
- `evidence_scope: provider_pilot_debug_or_preliminary`
- API keys in YAML: none detected by secret-pattern scan

The config is still suitable for dry-run/preflight only. It is not live-run-ready.

## Pre-Live Validation Results

Commands completed without provider calls:

```bash
python3 scripts/check_evidence_safety.py
PYTHONPATH=src python3 -m causal_agent_bench validate-config --config configs/provider_pilot_tiny_APPROVED.yaml
PYTHONPATH=src python3 -m causal_agent_bench plan-run --config configs/provider_pilot_tiny_APPROVED.yaml
PYTHONPATH=src python3 -m causal_agent_bench estimate-run-cost --config configs/provider_pilot_tiny_APPROVED.yaml --output-dir /tmp/cab_tiny_provider_live_cost
PYTHONPATH=src python3 -m causal_agent_bench dry-run --config configs/provider_pilot_tiny_APPROVED.yaml --output-dir /tmp/cab_tiny_provider_live_prerun_dryrun
PYTHONPATH=src python3 -m causal_agent_bench provider-pilot-preflight --config configs/provider_pilot_tiny_APPROVED.yaml --output-dir /tmp/cab_tiny_provider_live_preflight
```

Key results:

- Evidence safety: OK; C1-C8/C10 mock support remains blocked.
- `validate-config`: `valid: true`, `ready_to_run: false`.
- `validate-config` warning: provider key missing for `openai`; required env var is `OPENAI_API_KEY`.
- `validate-config` error: commercial provider configured while `allow_paid_calls=false`.
- `plan-run`: expected trajectories `5`; allow paid calls `False`; evidence level `preliminary_or_engineering`.
- `estimate-run-cost`: estimated high cost `$0.2436`, within the `$5.00` cap, but `runnable_without_approval: false`.
- `dry-run`: `dry_run: true`, `planned_trajectories: 5`, `paid_calls_made: false`, `will_call_providers: false`.
- `dry-run` provider readiness: `run_allowed: false`; blocked by `allow_paid_calls=false` and missing provider key.
- `provider-pilot-preflight`: `ready_for_dry_run: true`, `ready_for_live_provider_run: false`.
- Leakage gate: `must_fix_before_provider_pilot: 0`, `answer_leakage_blockers: 0`.

## Gate Matrix

| Gate | Status | Evidence |
|---|---:|---|
| Approval file explicitly has `Live-run approval: Yes` | pass-narrowly | Marker present |
| Approval is unambiguous | fail | Final authorization still says dry-run only and no live paid calls |
| Maximum live trajectories <= 5 | pass | Config cap is 5 |
| Maximum live budget <= USD 5.00 | pass | Config cap is `$5.00` |
| Approved config exists | pass | `configs/provider_pilot_tiny_APPROVED.yaml` |
| No API keys in YAML | pass | No secret-pattern match |
| Provider credentials only through env vars | fail | Required env var `OPENAI_API_KEY` is missing |
| Leakage blockers are 0 | pass | Static preflight reports 0 |
| Cost estimate within approved budget | pass | High estimate `$0.2436` |
| Dry-run/preflight passed | pass for dry-run | Ready for dry-run, not live |
| Scientific claims disabled | pass | `scientific_evidence: false` |
| Evidence scope preliminary/debug | pass | `provider_pilot_debug_or_preliminary` |
| Config live approval marker | fail | `approval.approved_for_live_run: false` |

## Provider Run Summary

No provider run was started. Therefore:

- Run directory: none
- Trajectory count: 0 live provider trajectories created
- Provider/model category: planned `openai` / `gpt-4o-mini`, not executed
- Runtime: not applicable
- Estimated cost: `$0.09` to `$0.2436`; dry-run internal upper bound `$0.014616`
- Actual cost: `$0.00` from this blocked attempt
- Failure status: blocked before live execution

## Evidence Classification

Current evidence remains unchanged:

- Provider-backed scientific runs: `0`
- Tiny live provider evidence: `0`
- Eligible paper assets: `0`
- Supported empirical claims: `0`
- C1-C8: unsupported
- C10: unsupported
- C9: engineering-only

The blocked validation can support only governance status: the repo is still dry-run/preflight-ready but live-pilot-blocked.

## Commands Not Run

Not run:

- `PYTHONPATH=src python3 -m causal_agent_bench run --config configs/provider_pilot_tiny_APPROVED.yaml`
- `main_200`
- `main_500`
- Compact-20
- Compact-50
- Broad sweeps
- Local LLMs
- `run-llm-judge`
- Claim promotion commands
- Paper asset eligibility marking

## Required Fixes Before Reconsidering Live Run

1. Make the self-authorization unambiguous: remove or update the dry-run-only/no-live-paid-call statements if live paid calls are truly authorized.
2. Provide provider credentials through environment variables only, specifically `OPENAI_API_KEY` for the current config.
3. Re-run the full no-provider gate suite.
4. Only if every gate passes, set `allow_paid_calls=true` and `approval.approved_for_live_run=true` immediately before the single tiny run.
5. After the live run finishes or fails, immediately set `allow_paid_calls=false`.

Final verdict: `LIVE_PILOT_BLOCKED`
