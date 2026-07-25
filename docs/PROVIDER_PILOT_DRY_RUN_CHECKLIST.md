# Provider Pilot Dry-Run Checklist

**No API calls in dry-run.** This checklist does **not** approve live spend or claim promotion.

## Preconditions

- [ ] True leakage blockers = **0** (`static_leakage_report.json` / `answer_leakage_repair.md`)
- [ ] `configs/provider_pilot_tiny_APPROVED.yaml` exists (copy from template; template unchanged)
- [ ] **No** API keys in YAML (env vars only)
- [ ] Advisor form signed (`docs/approvals/ADVISOR_APPROVAL_FORM.md`)
- [ ] Budget form signed (`docs/approvals/BUDGET_APPROVAL_FORM.md`)
- [ ] Approval block in APPROVED yaml:
  - `advisor_approved: true`
  - `budget_approved: true`
  - `approved_for_dry_run: true`
  - `approved_for_live_run: false`
  - `allow_paid_calls: false` (template and dry-run phase)

## Static validation (safe)

```bash
python3 scripts/check_evidence_safety.py
python3 -m causal_agent_bench all-no-run-reports --output-dir /tmp/cab_pre_dry_run
python3 -m causal_agent_bench validate-config --config configs/provider_pilot_tiny_APPROVED.yaml
python3 -m causal_agent_bench plan-run --config configs/provider_pilot_tiny_APPROVED.yaml
python3 -m causal_agent_bench estimate-run-cost --config configs/provider_pilot_tiny_APPROVED.yaml \
  --output-dir /tmp/cab_dry_run_cost
```

- [ ] Provider preflight gate = `ready_for_dry_run` (not `ready_for_live_run`)
- [ ] Cost estimate reviewed; `not_runnable_without_approval` acknowledged

## Dry-run command (when gate permits)

```bash
python3 -m causal_agent_bench dry-run --config configs/provider_pilot_tiny_APPROVED.yaml
```

## Expected artifacts (planning only)

- Trajectory/instance plan (no provider responses)
- Cost bound summary
- No new paper-eligible run metadata

## Post-dry-run review

- [ ] Plan matches caps (≤ 5 trajectories/instances)
- [ ] Model/provider resolved in plan output
- [ ] Still **no** claim promotion; C1–C8/C10 remain blocked
- [ ] Live-run forms still unsigned → keep `allow_paid_calls: false`

## Forbidden before live approval

- `python3 -m causal_agent_bench run --config ...`
- `run-llm-judge`
- `fill-paper-from-run --promote-to-supported`

See `docs/POST_PROVIDER_PILOT_CHECKLIST.md` after any future live run.
