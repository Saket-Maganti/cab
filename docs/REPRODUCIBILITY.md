# Reproducibility

## Determinism

- Task generation accepts a fixed seed.
- Tools operate only on task-local mock data.
- Runs save config hash, seed, timestamp, and git commit when available.
- Trajectories are saved as JSONL.
- Schema-native experiment runs write the original config, a stable config hash, run metadata, trajectories, errors, scores, aggregate tables, and a score report into a timestamped run directory.

## Commands

```bash
pip install -e ".[dev]"
pytest
python -m causal_agent_bench generate --config configs/dev_20_tasks.yaml
python -m causal_agent_bench run --config configs/dev_20_run.yaml
python -m causal_agent_bench score --run-dir results/<timestamp>_dev_20
python -m causal_agent_bench analyze --run-dir results/<timestamp>_dev_20
```

For the smallest local check:

```bash
python -m causal_agent_bench run --config configs/smoke.yaml
```

## Run Metadata

Each schema-native run records:

- timestamp,
- git commit when available,
- Python version,
- package version,
- seed,
- config hash,
- number of instances,
- agent list,
- basic machine information.

## Paper Claims

Every result in the paper must point to:

- a claim ID in `docs/CLAIM_LEDGER.md`,
- a run config,
- a run directory,
- generated scores and analysis assets,
- the scorer version or commit,
- any human-validation protocol used.

Development artifacts such as `results/20260510T110807Z_dev_20` may be used to test scripts, but they should not be cited as final scientific evidence.

## Resume

```bash
python -m causal_agent_bench run --config configs/dev_20_run.yaml --resume results/<timestamp>_dev_20
```

## TODO

Add pinned lockfiles, CI artifacts, container images, and archived final-run artifacts for camera-ready experiments.
