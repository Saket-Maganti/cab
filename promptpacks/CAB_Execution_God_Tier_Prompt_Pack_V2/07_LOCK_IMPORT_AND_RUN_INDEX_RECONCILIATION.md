# Prompt 07 — Lock, Import, and Run Index Reconciliation

You are working in `/Users/saketmaganti/Projects/causal-agent-bench`.

You are Codex acting as a run-integrity auditor.

## Task

After the live Compact-20 run, lock the run, reconcile run index, and create immutable metadata for audit.

## Absolute rules

- Do not run new provider/model calls.
- Do not alter raw trajectory outputs.
- Do not delete failed trajectories.
- Do not fabricate missing metadata.
- Do not promote claims.

## Preconditions

- live execution report exists,
- run directory exists,
- config is locked with `allow_paid_calls=false`.

## Actions

1. Identify raw run directory.
2. Compute file hashes for config, run metadata, trajectory outputs, scorer outputs if present.
3. Create:

- `reports/COMPACT20_RUN_INDEX_RECONCILIATION.md`
- `reports/COMPACT20_RUN_FILE_MANIFEST.json`
- `runs/compact20_3model_LOCKED_METADATA.json` or equivalent safe location.

4. Verify no more than approved trajectories, all expected conditions/models present, run status classified, and no paid calls left enabled.

5. Run safe index checker if exists:

```bash
python3 scripts/check_run_index.py
```

## Final response format

# Compact-20 Run Lock and Index Report

## 1. Executive Summary
## 2. Run Directory
## 3. File Manifest
## 4. Trajectory Completeness
## 5. Config Lock
## 6. Run Index Status
## 7. Issues Found
## 8. Commands Run
## 9. Commands Not Run
## 10. Next Best Action

Final verdict:

- `RUN_LOCKED_READY_FOR_POSTRUN_AUDIT`
- `RUN_LOCK_BLOCKED_MISSING_RUN_DIR`
- `RUN_LOCK_FAILED_INCOMPLETE_OR_UNSAFE`
