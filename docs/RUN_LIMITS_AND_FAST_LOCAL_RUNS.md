# Run limits and fast local runs

Use **micro/stub/mock configs** for development. Avoid full pilot slices unless you have hours and explicit intent.

## Recommended configs

| Config | Trajectories | Provider | Typical time |
|--------|--------------|----------|--------------|
| `configs/pilot_stub_micro_3.yaml` | 3 | local_stub | seconds |
| `configs/pilot_mock_agents_10.yaml` | 10 | mock (no LLM) | seconds |
| `configs/pilot_free_local_micro_3.yaml` | 3 | Ollama | minutes |
| `configs/pilot_free_local_fast_10.yaml` | 10 | Ollama | tens of minutes |

## Limits block

```yaml
limits:
  max_trajectories: 3
  max_runtime_minutes: 5
  stop_after_trajectories: 3
  max_steps_per_instance: 3
  max_output_tokens: 256
```

CLI overrides: `--max-trajectories`, `--max-runtime-minutes`, `--stop-after-trajectories`.

Limiter-stopped runs are **incomplete** and must not support final claims.

## Preflight

```bash
python3 -m causal_agent_bench plan-run --config configs/pilot_stub_micro_3.yaml
python3 scripts/check_zero_cost_readiness.py --config configs/pilot_free_local_micro_3.yaml --require zero_cost_ready
```

## Safe stop

```bash
pgrep -fl "causal_agent_bench run"
kill -TERM <pid>
python3 -m causal_agent_bench mark-interrupted --run-dir results/<run_dir> --reason "user stopped"
```
