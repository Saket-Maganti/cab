# Analysis Guide

The analysis layer converts completed run directories into descriptive summaries, paper tables, paper figures, and representative error cases.

## Commands

```bash
python -m causal_agent_bench analyze --run-dir results/<run_dir>
python -m causal_agent_bench export-paper-assets --run-dir results/<run_dir>
python -m causal_agent_bench export-ablation-table --run-dir results/<run_dir>
python -m causal_agent_bench mine-errors --run-dir results/<run_dir>
```

Equivalent script:

```bash
python scripts/make_paper_assets.py --run-dir results/<run_dir>
python scripts/export_ablation_table.py --run-dir results/<run_dir>
python scripts/mine_failure_gallery.py --run-dir results/<run_dir>
```

## Inputs

A run directory should contain:

- `instances.jsonl`
- `trajectories.jsonl`
- `scores.jsonl`
- `aggregate_scores.json`

If scores are missing, the loader will call the deterministic scorer before analysis.

## Outputs

Run-local outputs:

- `analysis_report.md`
- `paper_assets/figures/`
- `paper_assets/tables/`
- `paper_assets/statistical_summary.json`
- `error_cases/`

`paper_assets/tables/table4_ablation_results.*` is filled only for runs whose trajectory metadata includes ablation labels. Otherwise it remains a placeholder. See `docs/ABLATIONS.md` for the prompt/scaffold ablation configs and required reproducibility metadata.

`paper_assets/tables/table6_performance_vs_cost.*` and `paper_assets/tables/table7_robustness_vs_cost.*` summarize estimated cost, latency, model calls, tool calls, and cost-normalized success/ACRS. See `docs/COST_LATENCY.md`.

Global convenience outputs are also written to `figures/` and `tables/`.

`error_cases/` is a failure gallery: it contains one markdown/JSONL file per taxonomy error type, cross-case filters under `error_cases/filters/`, `taxonomy.json`, and `qualitative_examples.md`. These examples are for audit and paper drafting only until human validation is complete.

## Statistical Summaries

Current summaries include bootstrap confidence intervals for mean success rates, paired clean-vs-intervention comparisons by base task, per-family degradation copied from aggregate scoring, and Spearman clean-vs-ACRS ranking correlation.

These are engineering summaries for audit and paper wiring. They are not final scientific evidence until the planned main runs and validation are complete.
