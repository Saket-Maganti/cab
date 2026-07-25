# Dataset Card: web_shadow_v0.1

This is a deterministic synthetic pilot benchmark for CausalAgentBench.
It is not the final NeurIPS-scale dataset and should not be described as a completed scientific benchmark.

## Intended Use

- Local pilot experiments for tool-using agent robustness.
- Human audit calibration of intervention validity.
- Engineering validation of runner, scoring, and analysis code.

## Out-of-Scope Use

- Claims about real-world agent reliability without LLM runs and human validation.
- Evaluation of live web, real email, real booking, or private-data workflows.

## Counts

- Base tasks: 50
- Interventions: 250
- Instances: 300
- Quality passed: `False`
- Average max steps: 5.0
- Average required tools: 2.24
- Average interventions per task: 5.0

## Domain Distribution

- `web_shadow_docs`: 6
- `web_shadow_legal`: 4
- `web_shadow_navigation`: 14
- `web_shadow_pricing`: 4
- `web_shadow_product`: 8
- `web_shadow_search`: 12
- `web_shadow_support`: 2

## Intervention Distribution

- `distractor_evidence`: 25
- `long_horizon_dependency`: 25
- `observation_conflict`: 25
- `tool_corruption`: 25
- `tool_failure`: 25
- `web_broken_link`: 25
- `web_conflicting_page`: 25
- `web_hidden_evidence`: 25
- `web_irrelevant_search_result`: 25
- `web_stale_page`: 25

## Known Limitations

- Tasks are synthetic and template-derived.
- Automated quality checks are necessary but not sufficient for causal validity.
- Human audit is required before moving claims from planned to supported.
- Tool and scoring behavior remain deterministic approximations of real agent environments.
