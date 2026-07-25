# Main experiment readiness checklist

## Infrastructure (this build)

- [x] Micro/stub/mock configs
- [x] Run limiter + plan-run warnings
- [x] run-status / mark-interrupted / monitor / index-runs
- [x] Incomplete-run score/analyze/export guards
- [x] Fast checks (`make fast-check`)
- [ ] Completed 500-instance generation freeze validated for eval split
- [ ] Multi-provider pilot with paid budget approval
- [ ] Human validation sample annotated
- [ ] Statistical analysis on held-out split

## Before main claims

1. Frozen dataset + contamination audit clean
2. Completed non-oracle provider run at target scale
3. Cost/accounting audit
4. Human validation on diagnostic sample
5. Claim ledger review — no Prompt 67 until checklist green

## Safe commands today

```bash
make fast-check
python3 -m causal_agent_bench plan-run --config configs/pilot_stub_micro_3.yaml
python3 -m causal_agent_bench run --config configs/pilot_stub_micro_3.yaml   # stub only, seconds
```

Do **not** run full `pilot_free_local_20.yaml` or `main_500` without explicit time budget.
