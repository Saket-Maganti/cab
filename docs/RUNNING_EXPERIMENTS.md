# Running Experiments

This repo now has two related config types:

- Task-generation configs such as `configs/dev_20_tasks.yaml`.
- Experiment-run configs such as `configs/dev_20_run.yaml`.

## Smoke Run

```bash
python -m causal_agent_bench run --config configs/smoke.yaml
```

This creates a timestamped directory:

```text
results/<timestamp>_smoke/
  config.yaml
  config_hash.txt
  run_metadata.json
  trajectories.jsonl
  errors.jsonl
  scores.jsonl
  aggregate_scores.json
  aggregate_scores.csv
  score_report.md
```

The smoke config uses synthetic instances from `data/sample/instances.jsonl` and deterministic baseline agents. It is an engineering check, not a scientific result.

## Generate and Run Dev Benchmark

```bash
python -m causal_agent_bench generate --config configs/dev_20_tasks.yaml
python -m causal_agent_bench validate data/processed/dev_20/instances.jsonl --schema instances
python -m causal_agent_bench run --config configs/dev_20_run.yaml
```

`configs/dev_20_run.yaml` points to `benchmark_dir: data/processed/dev_20`, so the runner loads `data/processed/dev_20/instances.jsonl`.

## Resume

```bash
python -m causal_agent_bench run --config configs/dev_20_run.yaml --resume results/<timestamp>_dev_20
```

Resume skips completed `(agent, instance_id, repeat)` pairs already present in `trajectories.jsonl` and appends missing trajectories.

Resume also checks `config_hash.txt`. If the new config hash differs from the saved hash, the runner aborts instead of silently mixing incompatible trajectories.

## Scoring

Runs score automatically by default. To re-score:

```bash
python -m causal_agent_bench score --run-dir results/<timestamp>_dev_20
```

Set `auto_score: false` in a run config when debugging runner failures and scoring should be delayed.

## Current Limitations

- Progress reporting is intentionally simple.
- Resume only checks completed trajectory keys; it does not verify that the resumed config is identical.
- Deterministic baseline results are useful for reproducibility checks but should not be reported as model leaderboard results.
