# Budget Approval Form — Tiny Provider Pilot

## Cost review (static estimate)

Complete **before** any live provider command:

```bash
python3 -m causal_agent_bench estimate-run-cost \
  --config configs/provider_pilot_tiny_APPROVED.yaml \
  --output-dir /tmp/cab_provider_cost_review
```

Review `run_cost_estimate.md` for:

- [ ] Low/high token assumptions and estimated model calls
- [ ] `pricing_known` status (unknown pricing is **not** zero cost)
- [ ] Budget cap vs estimated high cost
- [ ] Rate-limit risk and expected runtime range
- [ ] `not_runnable_without_approval` is true until live approval

## Budget cap

| Field | Approved value |
|---|---|
| `budget_cap_usd` / `budget.max_total_usd` | ≤ 5.00 |
| `budget.max_calls` | ≤ 40 |
| `task_budget_cap_usd` | ≤ 0.75 |
| Stop conditions | `stop_after_trajectories`, `max_runtime_minutes`, `max_steps` present |

## Required YAML (APPROVED copy only)

```yaml
approval:
  budget_approved: true
  max_budget_usd: 5.0
```

## Signatures

| Role | Name | Date |
|---|---|---|
| Budget owner | __________________ | __________ |

Live spend still requires `approved_for_live_run: true` and `allow_paid_calls: true` in the **APPROVED** copy only.
