# Interrupted and micro runs

## Status conventions

Incomplete runs should have:

- `INCOMPLETE_RUN.json` / `INCOMPLETE_RUN.md`
- `RUN_STATUS.md` (optional legacy)
- `checkpoint.json` with `"status": "incomplete"`

Mark via CLI:

```bash
python3 -m causal_agent_bench mark-interrupted --run-dir results/<run_dir> --reason "user stopped long local run"
```

## Inspect status

```bash
python3 -m causal_agent_bench run-status --run-dir results/<run_dir>
python3 -m causal_agent_bench run-status --latest
python3 -m causal_agent_bench monitor --latest
```

## Resume

Same config hash required (or `--force-resume`):

```bash
python3 -m causal_agent_bench run --config configs/pilot_free_local_fast_10.yaml --resume results/<run_dir>
```

## Scoring incomplete runs

Refused by default:

```bash
python3 -m causal_agent_bench score --run-dir results/<run_dir>          # fails if incomplete
python3 -m causal_agent_bench score --run-dir results/<run_dir> --allow-incomplete  # preliminary only
```

Never use incomplete outputs for C1–C8/C10 claim updates.

## What counts as evidence

| Run type | Evidence |
|----------|----------|
| dry-run | none |
| stub/mock | engineering only |
| interrupted local | none (until completed) |
| completed local Ollama | preliminary non-oracle |
| completed paid provider | pilot candidate (with validation) |
