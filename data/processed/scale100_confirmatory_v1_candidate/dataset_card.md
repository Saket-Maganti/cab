# Dataset Card: scale100_confirmatory_v1_candidate

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

- Base tasks: 100
- Interventions: 500
- Instances: 600
- Quality passed: `True`
- Average max steps: 6.0
- Average required tools: 3.75
- Average interventions per task: 5.0

## Domain Distribution

- `calendar_email_workflow`: 9
- `coding_debugging`: 8
- `customer_support_workflow`: 8
- `data_cleaning_workflow`: 8
- `file_qa`: 9
- `finance_admin_workflow`: 8
- `operations_planning`: 8
- `policy_compliance`: 8
- `research_assistant`: 8
- `shopping_comparison`: 8
- `spreadsheet_qa`: 9
- `travel_planning`: 9

## Intervention Distribution

- `ambiguous_instruction`: 50
- `distractor_evidence`: 50
- `irrelevant_tools`: 50
- `long_horizon_dependency`: 50
- `memory_corruption`: 50
- `observation_conflict`: 50
- `premature_success_signal`: 50
- `tool_corruption`: 50
- `tool_failure`: 50
- `tool_removal`: 50

## Known Limitations

- Tasks are synthetic and template-derived.
- Automated quality checks are necessary but not sufficient for causal validity.
- Human audit is required before moving claims from planned to supported.
- Tool and scoring behavior remain deterministic approximations of real agent environments.
