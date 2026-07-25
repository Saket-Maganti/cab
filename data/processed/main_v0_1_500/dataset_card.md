# Dataset Card: main_v0.1_500_candidate

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

- Base tasks: 500
- Interventions: 2500
- Instances: 3000
- Quality passed: `True`
- Average max steps: 6.0
- Average required tools: 3.75
- Average interventions per task: 5.0

## Domain Distribution

- `calendar_email_workflow`: 42
- `coding_debugging`: 42
- `customer_support_workflow`: 41
- `data_cleaning_workflow`: 41
- `file_qa`: 42
- `finance_admin_workflow`: 41
- `operations_planning`: 41
- `policy_compliance`: 42
- `research_assistant`: 42
- `shopping_comparison`: 42
- `spreadsheet_qa`: 42
- `travel_planning`: 42

## Intervention Distribution

- `ambiguous_instruction`: 250
- `distractor_evidence`: 250
- `irrelevant_tools`: 250
- `long_horizon_dependency`: 250
- `memory_corruption`: 250
- `observation_conflict`: 250
- `premature_success_signal`: 250
- `tool_corruption`: 250
- `tool_failure`: 250
- `tool_removal`: 250

## Known Limitations

- Tasks are synthetic and template-derived.
- Automated quality checks are necessary but not sufficient for causal validity.
- Human audit is required before moving claims from planned to supported.
- Tool and scoring behavior remain deterministic approximations of real agent environments.
