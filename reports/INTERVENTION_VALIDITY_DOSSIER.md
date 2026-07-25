# Intervention Validity Dossier (Report Snapshot)

**Canonical source:** [docs/INTERVENTION_VALIDITY_DOSSIER.md](../docs/INTERVENTION_VALIDITY_DOSSIER.md)  
**Generated:** 2026-06-10 (static mirror)

## Status

| Metric | Value |
|--------|-------|
| Intervention families documented | 17 |
| Families requiring human validation | 14 |
| Empirical isolation proven | **no** |
| C3 / C10 | **blocked** |
| Auto-approval of high-risk pairs | **forbidden** |

## High-priority review families

- `long_horizon_dependency`
- `memory_corruption`
- `observation_conflict`
- `tool_failure`
- `tool_removal`
- `premature_success_signal`
- `stopping_recovery` (contradiction/recovery cluster)

## Safe commands

```bash
python3 -m causal_agent_bench high-risk-intervention-queue --output-dir /tmp/cab_hr_queue
python3 -m causal_agent_bench intervention-isolation-audit --output-dir /tmp/cab_isolation
```
