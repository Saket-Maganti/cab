# Zero-cost strategy

## Goals

- Develop and test the benchmark **without paid API spend**
- Keep claims honest: zero-cost outputs are **preliminary/engineering** until validated provider runs exist

## Tiers

1. **Stub/mock (seconds)** — `local_stub`, `mock_behavior_agent` configs
2. **Micro local (minutes)** — Ollama with `max_instances: 3` and limits
3. **Fast local (tens of minutes)** — 5–10 instances, one agent
4. **Full local (hours)** — defer until resources/time available
5. **Free-tier APIs** — optional; still preliminary; watch quotas

## Required gates

```bash
python3 scripts/check_zero_cost_readiness.py --config <config> --require zero_cost_ready
```

Configs must set:

- `cost_mode: zero_cost`
- `allow_paid_calls: false`
- `budget.max_total_usd: 0`
- `scientific_evidence_level: preliminary_or_engineering`

## Not allowed for final claims

- Dry-runs
- Stub/mock-only rankings
- Interrupted runs
- Oracle-only comparisons as deployable baselines

## When resources are available

1. Complete a bounded local run (micro → fast → full)
2. Re-run post-run verification audit
3. Optionally run small paid pilot with explicit budget approval
4. Only then consider claim-ledger updates (not Prompt 67 for NeurIPS-scale wording)
