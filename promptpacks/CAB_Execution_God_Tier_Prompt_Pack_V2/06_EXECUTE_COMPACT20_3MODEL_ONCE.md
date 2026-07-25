# Prompt 06 — Execute Compact-20 3-Model Once

You are working in `/Users/saketmaganti/Projects/causal-agent-bench`.

You are Codex acting as the live provider execution lead.

## Task

Execute exactly one approved Compact-20 3-model provider pilot.

## Extreme caution

This is the first real evidence run. Do not broaden it. Do not add extra experiments.

## Absolute rules

- Execute only if preflight verdict is `PREFLIGHT_READY_FOR_SINGLE_LIVE_RUN`.
- Do not run Main-200.
- Do not run Main-500.
- Do not run Compact-50.
- Do not run broad sweeps.
- Do not run local LLMs unless they are one of the approved 3 models.
- Do not exceed budget.
- Do not exceed trajectory cap.
- Do not print API keys.
- Do not store API keys.
- Do not promote claims.
- Do not mark paper assets eligible.
- Always lock `allow_paid_calls=false` after run/failure.

## Required steps

1. Re-check:

```bash
python3 scripts/check_evidence_safety.py
```

2. Temporarily set in `configs/compact20_3model_APPROVED.yaml`:

```yaml
allow_paid_calls: true
approved_for_live_run: true
```

3. Run exactly:

```bash
PYTHONPATH=src python3 -m causal_agent_bench run --config configs/compact20_3model_APPROVED.yaml
```

4. Immediately lock config:

```yaml
allow_paid_calls: false
approved_for_live_run: false
completed_and_locked: true
```

5. Identify run directory.

6. Create:

- `reports/COMPACT20_3MODEL_LIVE_EXECUTION.md`
- `reports/COMPACT20_3MODEL_LIVE_EXECUTION.json`

## If failure occurs

Lock config, create:

- `reports/COMPACT20_3MODEL_LIVE_EXECUTION_FAILED.md`

Do not retry unless failure is clearly non-provider and budget impact is zero. If retry would call provider again, stop and ask for approval.

## Final response format

# Compact-20 3-Model Live Execution Report

## 1. Executive Summary
## 2. Gate Confirmation
## 3. Command Run
## 4. Run Directory
## 5. Trajectory Count
## 6. Cost and Runtime
## 7. Failures/Incomplete Items
## 8. Config Lock Confirmation
## 9. Commands Not Run
## 10. Evidence Classification
## 11. Next Best Action

Final verdict:

- `LIVE_RUN_COMPLETE_PENDING_AUDIT`
- `LIVE_RUN_FAILED_LOCKED`
- `LIVE_RUN_BLOCKED_NO_EXECUTION`
