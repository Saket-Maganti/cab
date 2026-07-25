# Tiny Provider Dry-Run Readiness Report

Generated: 2026-06-12  
Scope: rerun of the self-authorized tiny provider pilot dry-run/preflight process. No live provider calls were made.

## 1. Executive Summary

Verdict: `DRYRUN_READY`

The self-authorization at `docs/approvals/SELF_AUTHORIZATION_TINY_PROVIDER_PILOT.md` is valid for dry-run/preflight only. The approved config at `configs/provider_pilot_tiny_APPROVED.yaml` is present, valid, budget-capped, trajectory-capped, and live-provider-blocked.

The repo is dry-run-ready only:

- Live provider calls: **not approved**
- Paid calls: **disabled**
- Claim promotion: **forbidden**
- Paper asset eligibility: **unchanged / blocked**

## 2. Approval Validation

Approval source:

- `docs/approvals/SELF_AUTHORIZATION_TINY_PROVIDER_PILOT.md`

Validation result:

- Maximum trajectories: `5` (`<= 5`)
- Maximum estimated provider calls: `30`
- Maximum approved budget: `$5.00`
- Dry-run approval: `Yes`
- Live-run approval: `No`
- Scientific claim promotion allowed: `No`
- Paper claim support allowed: `No`

The config schema does not support a `scientific_claims_allowed` field. The supported safety fields are set instead: `scientific_evidence: false`, `scientific_evidence_level: preliminary_or_engineering`, and `evidence_scope: provider_pilot_debug_or_preliminary`.

## 3. Files Added

No new files were added in this rerun.

Existing required artifacts verified:

- `docs/approvals/SELF_AUTHORIZATION_TINY_PROVIDER_PILOT.md`
- `configs/provider_pilot_tiny_APPROVED.yaml`

## 4. Files Modified

- `reports/TINY_PROVIDER_DRYRUN_READINESS.md`
- `docs/PAPER_METHOD_FIGURES.md` was refreshed by `all-no-run-reports`

No fixture test changes were needed in this rerun.

## 5. Approved Config Summary

Approved config:

- `configs/provider_pilot_tiny_APPROVED.yaml`

Key safety fields:

- `allow_paid_calls: false`
- `approved_for_dry_run: true`
- `approved_for_live_run: false`
- `scientific_evidence: false`
- `scientific_evidence_level: preliminary_or_engineering`
- `evidence_scope: provider_pilot_debug_or_preliminary`
- `max_instances: 5`
- `limits.max_trajectories: 5`
- `limits.stop_after_trajectories: 5`
- `limits.max_api_calls: 30`
- `budget.max_total_usd: 5.0`
- `budget.max_calls: 30`
- API keys in YAML: none

## 6. Cost Estimate

`estimate-run-cost` result:

- Config: `provider_pilot_tiny_APPROVED`
- Trajectories: `5`
- Estimated provider calls: `30`
- Pricing known: `true`
- Estimated cost range: `$0.09` to `$0.2436`
- Budget cap: `$5.00`
- Runnable without approval: `false`, intentionally, because `allow_paid_calls=false`

Dry-run internal preflight estimate:

- Total cost estimate: `$0.014616`
- Budget status: `within_budget`
- Expected max calls: `30`

Both estimates are within the authorized `$5.00` ceiling.

## 7. Dry-Run Status

The repo explicitly documents `dry-run` as no-provider/no-API, and the command completed.

Dry-run output:

- `dry_run: true`
- `would_execute: true`
- `planned_trajectories: 5`
- `paid_calls_made: false`
- `will_call_providers: false`
- `provider_calls_replaced_with_local_stub: true`
- `scientific_evidence: false`

Approved-config preflight result:

- Gate status: `ready_for_dry_run`
- Ready for dry run: `true`
- Ready for live provider run: `false`
- Live run blocked: `true`
- Leakage blockers: `0`
- Answer leakage blockers: `0`
- Blockers: none
- Warnings: none

Note: the requested `all-no-run-reports --output-dir ...` command uses its default config internally, so its bundled `provider_pilot_preflight.json` reflects the template as `template_safe_but_not_runnable`. The approved config was verified separately with `provider-pilot-preflight --config configs/provider_pilot_tiny_APPROVED.yaml`.

## 8. Tests Added/Updated

No fixture tests were changed in this rerun. Existing dry-run readiness tests were rerun and passed:

```bash
PYTHONPATH=src python3 -m pytest tests/test_provider_pilot_preflight.py tests/test_godtier_provider_prep.py tests/test_mega_cleanup.py tests/test_compact_empirical_upgrade.py tests/test_god_tier_status.py -q
```

Result: `41 passed`

## 9. Commands Run

```bash
python3 scripts/check_evidence_safety.py
PYTHONPATH=src python3 -m causal_agent_bench validate-config --config configs/provider_pilot_tiny_APPROVED.yaml
PYTHONPATH=src python3 -m causal_agent_bench plan-run --config configs/provider_pilot_tiny_APPROVED.yaml
PYTHONPATH=src python3 -m causal_agent_bench estimate-run-cost --config configs/provider_pilot_tiny_APPROVED.yaml --output-dir /tmp/cab_tiny_provider_approved_cost
PYTHONPATH=src python3 -m causal_agent_bench all-no-run-reports --output-dir /tmp/cab_tiny_provider_dryrun_ready
PYTHONPATH=src python3 -m causal_agent_bench dry-run --config configs/provider_pilot_tiny_APPROVED.yaml --output-dir /tmp/cab_tiny_provider_approved_dryrun_rerun
PYTHONPATH=src python3 -m causal_agent_bench provider-pilot-preflight --config configs/provider_pilot_tiny_APPROVED.yaml --output-dir /tmp/cab_tiny_provider_approved_preflight_rerun
PYTHONPATH=src python3 -m pytest tests/test_provider_pilot_preflight.py tests/test_godtier_provider_prep.py tests/test_mega_cleanup.py tests/test_compact_empirical_upgrade.py tests/test_god_tier_status.py -q
```

`validate-config` returned `valid: true`. It also correctly reported live-run blockers because `allow_paid_calls=false` and no provider key is configured.

## 10. Commands Not Run

Not run:

```bash
PYTHONPATH=src python3 -m causal_agent_bench run --config configs/provider_pilot_tiny_APPROVED.yaml
```

Also not run:

- live providers
- provider API calls
- `run-llm-judge`
- main benchmark configs
- `main_200`
- `main_500`
- broad sweeps
- local LLM runs
- claim promotion
- paper asset eligibility marking

Confirmed:

- No live provider calls
- No claim promotion
- No fake evidence
- No `allow_paid_calls=true`
- No assets marked eligible
- No frozen data edited

## 11. Current Evidence State

Current evidence state remains non-empirical:

- Eligible paper runs: `0`
- Eligible paper assets: `0`
- Supported empirical claims: `0`
- C9: `engineering_only`
- C1-C8/C10: planned/unsupported
- Provider pilot execution: dry-run-ready, live blocked

## 12. Remaining Blockers Before Live Tiny Pilot

- Change self-authorization to explicitly say `Live-run approval: Yes`.
- Enable the live-run approval marker only after live approval.
- Enable paid calls only in the approved live-run copy.
- Configure provider API credentials via environment variables only.
- Re-run evidence safety, validate-config, plan-run, estimate-run-cost, preflight, and dry-run.
- Review cost estimate against the `$5.00` cap.
- After any future live run, manually inspect all trajectories and complete post-run scorer/evidence reports.

## 13. Next Best Action

Review the refreshed no-provider dry-run report under:

```text
/tmp/cab_tiny_provider_approved_dryrun_rerun
```

If it looks acceptable, the next decision is whether to issue a separate explicit live-run authorization. Until then, the repo is dry-run-ready only.

Final verdict: `DRYRUN_READY`
