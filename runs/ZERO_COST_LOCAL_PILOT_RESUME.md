# Zero-cost local pilot — configs, status, and resume

Infrastructure for Ollama / local OpenAI-compatible zero-cost pilots. **Preliminary/engineering evidence only** — not for final paper claims.

## Configs

| Config | Instances | Agents | Max steps | Purpose |
|--------|-----------|--------|-----------|---------|
| `configs/pilot_free_local_20.yaml` | 120 (full pilot slice) | 3 local | 8 | Full local pilot (long) |
| `configs/pilot_free_local_fast_10.yaml` | 10 (`max_instances`) | 1 local | 4 | Fast smoke / preliminary local run |

Both configs enforce:

- `cost_mode: zero_cost`
- `allow_paid_calls: false`
- `budget.max_total_usd: 0`
- `scientific_evidence_level: preliminary_or_engineering`
- `provider: local_openai` → Ollama at `http://localhost:11434/v1`
- Model: `qwen2.5:7b-instruct` (or `${LOCAL_OPENAI_MODEL_ID}`)
- No oracle agents

## Environment

```bash
export LOCAL_OPENAI_BASE_URL=http://localhost:11434/v1
export LOCAL_OPENAI_MODEL_ID=qwen2.5:7b-instruct
```

Ensure Ollama is running: `curl -s http://localhost:11434/api/tags`

## Preflight (required before any real run)

```bash
python3 scripts/check_zero_cost_readiness.py \
  --config configs/pilot_free_local_fast_10.yaml \
  --require zero_cost_ready
```

Do not bypass the readiness gate.

## Start a new run

```bash
python3 -m causal_agent_bench run \
  --config configs/pilot_free_local_fast_10.yaml \
  --checkpoint-every 1
```

`--checkpoint-every 1` (default) writes `checkpoint.json` after each completed trajectory for safe resume.

## Resume an interrupted run

1. Confirm `RUN_STATUS.md` in the run directory shows `incomplete` / `local_interrupted`.
2. **Do not edit** the config used for the original run (resume rejects config-hash mismatch).
3. Re-run readiness, then resume:

```bash
RUN_DIR=results/<timestamp>_pilot_free_local_fast_10

python3 scripts/check_zero_cost_readiness.py \
  --config configs/pilot_free_local_fast_10.yaml \
  --require zero_cost_ready

python3 -m causal_agent_bench run \
  --config configs/pilot_free_local_fast_10.yaml \
  --resume "$RUN_DIR" \
  --checkpoint-every 1
```

Optional: `--retry-failed` to retry retriable failures with no trajectory.

## Mark interrupted / incomplete runs

When stopping a run manually:

1. Send `SIGTERM` to the `causal_agent_bench run` process (do not delete artifacts).
2. Add or update `RUN_STATUS.md` in the run directory with:
   - `status: incomplete` / `local_interrupted`
   - completed vs total trajectories
   - `scientific_evidence: false`
3. Extend `checkpoint.json` with:

```json
{
  "status": "incomplete",
  "interruption_reason": "local_interrupted"
}
```

**Do not** score, analyze, or export interrupted runs as scientific evidence.

## Interrupted run directories (current)

| Run directory | Progress | Status |
|---------------|----------|--------|
| `results/20260520T030034Z_pilot_free_local_20` | 21 / 360 | incomplete / local_interrupted |
| `results/20260520T034642Z_pilot_free_local_fast_10` | 3 / 10 | incomplete / local_interrupted |

## After a **completed** run only

Only when `checkpoint.json` shows `completed == total` and no `incomplete` status:

```bash
RUN_DIR=results/<completed_run_dir>

python3 -m causal_agent_bench score --run-dir "$RUN_DIR"
python3 -m causal_agent_bench analyze --run-dir "$RUN_DIR"
```

Treat outputs as **preliminary non-oracle evidence** only. Do not update C1–C8/C10 claims or run Prompt 67 for final NeurIPS wording.

## Safe stop

```bash
# Find process
pgrep -fl "causal_agent_bench run"

# Graceful stop (replace PID)
kill -TERM <python_pid>
```

Wait a few seconds; verify the process exited before updating `RUN_STATUS.md`.
