# CausalAgentBench v0 Spec

## Unit of Evaluation

One agent trajectory on one `BenchmarkTask`.

## Pairing

Clean tasks use `intervention = null`. Intervened tasks set `clean_task_id` to the base task id.

## Output Artifacts

- `tasks.jsonl`
- `trajectories.jsonl`
- `metadata.json`
- `scores.json`
- `analysis_report.md`
- `paper_assets/`
