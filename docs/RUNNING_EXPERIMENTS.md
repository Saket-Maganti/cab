# Running Experiments

This repo now has two related config types:

- Task-generation configs such as `configs/dev_20_tasks.yaml`.
- Experiment-run configs such as `configs/dev_20_run.yaml`.

## Smoke Run

```bash
python -m causal_agent_bench validate-config --config configs/smoke.yaml
python -m causal_agent_bench dry-run --config configs/smoke.yaml
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

## Pilot Runs

Dry-run and cost-estimate provider-backed configs before spending money:

```bash
python -m causal_agent_bench validate-config --config configs/pilot_multi_provider_20.yaml
python -m causal_agent_bench dry-run --config configs/pilot_multi_provider_20.yaml --output-dir results/dry_runs
python -m causal_agent_bench estimate-cost --config configs/pilot_multi_provider_20.yaml
```

Local stub pilots are engineering checks only:

```bash
python -m causal_agent_bench run --config configs/pilot_20_multi_agent.yaml
python -m causal_agent_bench summarize-run --run-dir results/<timestamp>_pilot_20_multi_agent_stub
```

Prompt/scaffold ablation configs live under `configs/ablations/`. The included local-stub variants are for plumbing checks only:

```bash
python -m causal_agent_bench validate-config --config configs/ablations/memory_verification_local_stub.yaml
python -m causal_agent_bench run --config configs/ablations/memory_verification_local_stub.yaml
python -m causal_agent_bench export-ablation-table --run-dir results/<timestamp>_ablation_memory_verification_local_stub
```

See `docs/ABLATIONS.md` before using provider-backed ablation runs as paper evidence.

Commercial API configs require an explicit paid-call gate and preflight budget checks. See [docs/COMMERCIAL_API_RUNS.md](COMMERCIAL_API_RUNS.md).

```bash
export OPENAI_API_KEY=...
export OPENAI_MODEL_ID=...
python -m causal_agent_bench validate-config --config configs/commercial_api_pilot_small_20.yaml
python -m causal_agent_bench estimate-cost --config configs/commercial_api_pilot_small_20.yaml
python -m causal_agent_bench run --config configs/commercial_api_pilot_small_20.yaml
```

For real provider pilots, set API keys and model IDs in the environment. Keys are never printed by the CLI:

```bash
python -m causal_agent_bench list-providers
python -m causal_agent_bench run --config configs/pilot_multi_provider_20.yaml
```

For an OpenAI-compatible hosted or local server, use `provider: openai_compatible` or `provider: local_openai` in `agent_runs`. Set `base_url` in YAML or use `OPENAI_COMPATIBLE_BASE_URL` / `LOCAL_OPENAI_BASE_URL`. Add `cache_dir: results/cache/<run_name>` only when replaying identical prompts is intended; cache hits are logged and charged as zero actual provider cost.

Open-weight/local pilots use separate configs and evidence labels:

```bash
export LOCAL_OPENAI_MODEL_ID="your-model-id"
export LOCAL_OPENAI_BASE_URL="http://localhost:8000/v1"
python -m causal_agent_bench validate-config --config configs/pilot_local_openai_compatible_20.yaml
python -m causal_agent_bench run --config configs/pilot_local_openai_compatible_20.yaml
```

See `docs/OPEN_WEIGHT_LOCAL_MODELS.md` for Ollama, vLLM, LM Studio, and llama.cpp setup. Local runs are stamped `evidence_scope: local_open_weight_unvalidated` and must not be merged with commercial API tables.

Cost models can be configured per agent run with `pricing` or centrally with `cost_models.<provider>.<model>`. Budget caps are `budget_cap_usd` at the run or agent-run level and `task_budget_cap_usd` at the run or agent-run level. See `docs/COST_LATENCY.md`.

## Intervention Audit and Dataset Freeze

```bash
python -m causal_agent_bench audit-interventions --benchmark-dir data/processed/pilot_v0_1
python -m causal_agent_bench freeze-dataset --source-dir data/processed/pilot_v0_1 --version pilot_v0.1
```

The audit writes `intervention_audit_report.json` and `intervention_audit_report.md`, including per-instance `pass`, `warning`, or `fail` validity scores. See `docs/INTERVENTION_AUDIT.md` for the family-level audit guide and report fields.

Freezing validates schemas, reruns quality filters, writes disjoint release splits (`dev`, `pilot`, `validation`, `test`, `heldout_templates`), checks leakage, computes a deterministic `dataset_hash`, and writes `freeze_manifest.json` plus `benchmark_card_snapshot.md`. It fails rather than freezing a dataset whose audit or leakage checks fail. See `docs/DATASET_FREEZE.md`.

Freezing writes a reproducibility bundle; it does not make the dataset scientifically validated.

## Resume

```bash
python -m causal_agent_bench run --config configs/dev_20_run.yaml --resume results/<timestamp>_dev_20
```

Resume skips completed `(agent, instance_id, repeat)` pairs already present in `trajectories.jsonl` and appends missing trajectories.

Resume also checks `config_hash.txt`. If the new config hash differs from the saved hash, the runner aborts instead of silently mixing incompatible trajectories.

Optional flags:

```bash
python -m causal_agent_bench run --config configs/dev_20_run.yaml \
  --resume results/<timestamp>_dev_20 \
  --retry-failed \
  --checkpoint-every 5
```

`--retry-failed` re-attempts retriable error rows that have no trajectory. `--checkpoint-every` writes `checkpoint.json` frequently for long runs.

## Batch sharding and merge

For parallel execution without cloud-specific code, see [docs/BATCH_RUNS.md](BATCH_RUNS.md).

```bash
python -m causal_agent_bench batch-plan --config configs/smoke.yaml --shard-by instance --shard-count 4
python -m causal_agent_bench run --config results/smoke_batch/shards/shard_000/config.yaml
python -m causal_agent_bench batch-merge --batch-dir results/smoke_batch
python -m causal_agent_bench failure-report --run-dir results/smoke_batch/merged/run
```

## Scoring

Runs score automatically by default. To re-score:

```bash
python -m causal_agent_bench score --run-dir results/<timestamp>_dev_20
```

Set `auto_score: false` in a run config when debugging runner failures and scoring should be delayed.

## Analysis and Paper Assets

```bash
python -m causal_agent_bench analyze --run-dir results/<run_dir>
python -m causal_agent_bench export-paper-assets --run-dir results/<run_dir>
```

Paper assets include run directory, config hash, dataset version, model IDs, and timestamp metadata.
Table exports also include seed, scorer version, and git commit when available; ablation rows include prompt hashes and prompt file references.
Cost exports include `table6_performance_vs_cost.*` and `table7_robustness_vs_cost.*`.

## Human Validation

```bash
python -m causal_agent_bench export-human-validation --run-dir results/<run_dir> --output-dir results/<run_dir>/human_validation --sample-size 100
python -m causal_agent_bench summarize-human-validation --annotations results/<run_dir>/human_validation/annotation_export.csv --output-dir results/<run_dir>/human_validation/summary
```

The exporter writes CSV/JSONL annotation packets and a static HTML aid. The summarizer computes percent agreement, Cohen's kappa, nominal Krippendorff's alpha, disagreement examples, and Table 5 files. These artifacts are still validation workflow outputs; claims require completed annotations, adjudication, and claim-ledger updates. See `docs/HUMAN_VALIDATION_PROTOCOL.md`, `docs/HUMAN_VALIDATION_GUIDELINES.md`, `docs/HUMAN_VALIDATION_FORM_SCHEMA.md`, and `docs/HUMAN_VALIDATION_PILOT_PLAN.md`.

## Optional LLM Judge Calibration

```bash
python -m causal_agent_bench run-llm-judge --run-dir results/<run_dir> --config configs/judge_fake_smoke.yaml --output-dir results/<run_dir>/llm_judge
python -m causal_agent_bench calibrate-llm-judge --judge-labels results/<run_dir>/llm_judge/judge_labels.jsonl --human-annotations results/<run_dir>/human_validation/annotation_export.csv --output-dir results/<run_dir>/llm_judge/calibration
```

LLM judge labels are optional diagnostics. They are written separately from deterministic scores and human labels, and they cannot be reported as ground truth without human calibration and claim-ledger evidence. See `docs/LLM_JUDGE_PROTOCOL.md` and `docs/LLM_JUDGE_RISKS.md`.

## Current Limitations

- Progress reporting is intentionally simple.
- Resume checks config hashes, but does not deeply validate partially written trajectory payloads.
- Deterministic baseline results are useful for reproducibility checks but should not be reported as model leaderboard results.
- Dry-run cost estimates are conservative approximations, not invoices.
- Cost-normalized metrics require configured pricing and provider-reported token usage; unknown costs remain explicit rather than guessed.
