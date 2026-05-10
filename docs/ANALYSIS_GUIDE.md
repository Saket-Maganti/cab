# Analysis Guide

The analysis layer converts completed run directories into descriptive summaries, paper tables, paper figures, and representative error cases.

## Commands

```bash
python -m causal_agent_bench analyze --run-dir results/<run_dir>
python -m causal_agent_bench export-paper-assets --run-dir results/<run_dir>
```

Equivalent script:

```bash
python scripts/make_paper_assets.py --run-dir results/<run_dir>
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

Global convenience outputs are also written to `figures/` and `tables/`.

## Statistical Summaries

Current summaries include bootstrap confidence intervals for mean success rates, paired clean-vs-intervention comparisons by base task, per-family degradation copied from aggregate scoring, and Spearman clean-vs-ACRS ranking correlation.

These are engineering summaries for audit and paper wiring. They are not final scientific evidence until the planned main runs and validation are complete.
