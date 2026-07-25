# Batch and Sharded Runs

Cloud-agnostic utilities for larger experiments: shard planning, resumable execution, shard merge, and failure reports. No vendor-specific SDKs are required.

## Sharding

Plan shards from any experiment config:

```bash
python -m causal_agent_bench batch-plan \
  --config configs/smoke.yaml \
  --shard-by instance \
  --shard-count 4 \
  --output-dir results/smoke_batch
```

`--shard-by` options:

| Mode | Partitions |
| --- | --- |
| `instance` | Instance IDs across shards (round-robin) |
| `agent` | Agent runs across shards |
| `intervention_family` | Intervention families (`clean` plus each family) |

Outputs:

```text
results/<run_name>_batch/
  batch_manifest.json
  batch_plan.md
  shards/shard_000/config.yaml
  shards/shard_000/instances.jsonl
  shards/shard_000/shard_manifest.json
  ...
```

Run one shard (on any machine):

```bash
python -m causal_agent_bench run --config results/smoke_batch/shards/shard_000/config.yaml
```

## Resume, retry, and checkpoints

Resume skips completed `(agent, instance_id, repeat)` keys in `trajectories.jsonl`:

```bash
python -m causal_agent_bench run --config <config> --resume results/<run_dir>
```

Retry retriable failures (errors without trajectories, `retriable: true`):

```bash
python -m causal_agent_bench run --config <config> --resume results/<run_dir> --retry-failed
```

Checkpoint progress after every *N* trajectories (default `1`):

```bash
python -m causal_agent_bench run --config <config> --checkpoint-every 5
```

`checkpoint.json` records `completed`, `total`, `errors`, and `progress_fraction`.

## Merge shards

After all shards finish:

```bash
python -m causal_agent_bench batch-merge --batch-dir results/smoke_batch
```

Merge:

- Combines shard `trajectories.jsonl` and `errors.jsonl`
- Verifies **no duplicate** keys
- Verifies **no missing** expected keys from `batch_manifest.json`
- Rejects unexpected extra keys (use `--no-strict` to override)
- Writes `merged/run/` plus `merge_report.json` and `failure_report.md`
- Scores the merged run by default (`--no-score` to skip)

## Failure reports

For any run directory:

```bash
python -m causal_agent_bench failure-report --run-dir results/<run_dir>
```

Writes `failure_report.json` and `failure_report.md` with error counts by type/agent, missing pairs, duplicates, and completion rate.

## Local and SLURM scripts

- `scripts/run_batch_local.sh` — plan, run each shard with resume/retry, merge
- `scripts/slurm_batch_template.sh` — SLURM array template (`#SBATCH --array=0-3`)

Example:

```bash
chmod +x scripts/run_batch_local.sh
./scripts/run_batch_local.sh configs/smoke.yaml instance 2
```

## CI

`.github/workflows/batch_smoke.yml` runs shard plan, two shard executes, merge, and failure-report on `configs/smoke.yaml`.

## Scope

Shard and smoke runs using `local_stub` or deterministic agents are **engineering checks only**. Link merged runs to config hashes, seeds, model IDs, prompt hashes, scorer versions, and git commits before any paper claim.
