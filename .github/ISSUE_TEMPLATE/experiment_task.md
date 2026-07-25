---
name: Experiment task
about: Plan or track a benchmark experiment run
title: "[experiment] "
labels: experiment
---

## Experiment ID

(e.g. micro_stub, pilot_20_provider — see `experiments/EXPERIMENT_REGISTRY.md`)

## Config

`configs/...`

## Purpose

## Cost / runtime estimate

```bash
python3 -m causal_agent_bench plan-run --config ...
```

## Evidence level target

- [ ] engineering_only
- [ ] preliminary
- [ ] pilot
- [ ] main

## Approval checklist

- [ ] `allow_paid_calls: false` (zero-cost) OR explicit budget approved
- [ ] No oracle in main comparison
- [ ] Readiness gate passed
- [ ] Run limiter configured for local jobs

## Output artifacts

## Post-run tasks

- [ ] generate-report
- [ ] failure-gallery
- [ ] index-runs
- [ ] claim ledger review (no auto-updates)
