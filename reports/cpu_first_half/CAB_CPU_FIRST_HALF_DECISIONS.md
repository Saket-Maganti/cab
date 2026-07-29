# CAB CPU First-Half Decisions

## Prospective decisions

1. Preserve the registered C10 thresholds and evidence contract.
2. Treat blank, fixture, proxy, AI-assisted, synthetic, and metadata-only rows
   as zero genuine evidence.
3. Stop empirical execution at CPU-H2 because Compact-20 genuine review
   coverage is `0/20`.
4. Do not freeze Compact-20, choose/drop models, import shards, merge,
   rescore, audit trajectories, bootstrap, rank, or decide Scale progression.
5. Preserve the Compact decision alternatives exactly as registered:
   `PROCEED_TO_SCALE`, `REPAIR_AND_VERSION`, `REDUCE_MODEL_PANEL`,
   `REPORT_INFORMATIVE_NULL`, `STOP_CURRENT_THESIS`, or
   `INSUFFICIENT_AUDIT_EVIDENCE`.

## Current decision

```text
CAB_CPU_FIRST_HALF_PARTIAL_GENUINE_INPUTS_MISSING
HUMAN_VALIDATION_REQUIRED
```

This is a blocker state, not an empirical null and not a failed build.

## Exact next action

Collect genuine Compact-20 review/adjudication under the canonical protocol,
then run:

```bash
python3 scripts/validate_cab_human_reviews.py
```
