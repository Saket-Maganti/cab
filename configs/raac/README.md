# RAAC configuration registry

These files are design and execution templates, not empirical evidence.

- `raac_light.yaml` and `raac_full.yaml` mirror the contracts enforced in
  `causal_agent_bench.raac.policy`.
- `ablations.yaml` and `baselines.yaml` enumerate the frozen treatment arms.
- `equal_budget.yaml` freezes the shared resource ceiling for equal-budget
  comparisons.
- `analysis_TEMPLATE.yaml` enables RAAC treatment, overhead, and clean-tradeoff
  analysis without exporting paper assets.
- `kaggle_t4x2_matrix.yaml` freezes the standard/LIGHT/FULL arms, all six
  ablations, both budget modes, and the required compute-contract fields used
  by the governed baselines/ablations notebook.
- `kaggle_t4x2_raac_TEMPLATE_NOT_APPROVED.yaml` is fail-closed:
  `template_only: true`, no paid calls, zero budget, and no live approval.

For an experiment runner config, copy only the nested `raac:` block into the
run-level config or an individual `agent_runs` entry. Per-agent configuration
takes precedence over the run-level default.
