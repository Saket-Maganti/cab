# Run Card Template

Summary card for any experiment run directory.

| Field | Value |
|---|---|
| **Run ID** | Directory name |
| **Run name** | From config |
| **Started** | UTC timestamp |
| **Git commit** | |
| **Config path** | |
| **Config hash** | |
| **Benchmark path** | |
| **Dataset version** | |
| **Agents** | |
| **Instances** | n |
| **Trajectories** | completed / expected |
| **Status** | See [EXPERIMENT_STATE_MACHINE.md](../EXPERIMENT_STATE_MACHINE.md) |
| **Evidence scope** | |
| **Scientific evidence flag** | true/false |
| **Scorer version** | |
| **Artifacts** | scores.jsonl, report.md, … |
| **Evidence level** | |
| **Allowed claims** | |
| **Blockers** | INCOMPLETE_RUN, missing scores, etc. |

Generate metadata:

```bash
python3 -m causal_agent_bench run-status --run-dir results/<run_dir>
python3 scripts/check_experiment_state.py --run-dir results/<run_dir>
python3 -m causal_agent_bench generate-report --run-dir results/<run_dir>
```
