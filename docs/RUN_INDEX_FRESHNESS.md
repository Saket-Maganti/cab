# RUN_INDEX Freshness

The persisted run index (`results/RUN_INDEX.jsonl`) is an **inventory aid only**. It does not change evidence classification or paper eligibility.

## Check freshness (safe, no mutations)

```bash
python3 scripts/check_run_index.py
python3 scripts/check_run_index.py --json
```

Exit code `1` means the index is stale (indexed count ≠ live `results/` directories).

## Refresh inventory (optional)

```bash
python3 -m causal_agent_bench index-runs
```

This updates `RUN_INDEX.jsonl` from existing run directories. It must **not** be used to mark runs paper-eligible or to edit run metadata.

## Evidence policy

- Stale index warnings appear in `check_evidence_safety.py`, `run-health`, and the evidence dashboard.
- Mock/stub/local runs remain non-eligible regardless of indexing.
