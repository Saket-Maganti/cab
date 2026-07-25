# Dataset Card: main500_confirmatory_v1_candidate

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

- Base tasks: 550
- Interventions: 2750
- Instances: 3300
- Quality passed: `True`
- Average max steps: 6.002
- Average required tools: 3.753
- Average interventions per task: 5.0

## Domain Distribution

- `calendar_email_workflow`: 46
- `coding_debugging`: 46
- `customer_support_workflow`: 46
- `data_cleaning_workflow`: 45
- `file_qa`: 46
- `finance_admin_workflow`: 45
- `operations_planning`: 46
- `policy_compliance`: 46
- `research_assistant`: 46
- `shopping_comparison`: 46
- `spreadsheet_qa`: 46
- `travel_planning`: 46

## Intervention Distribution

- `ambiguous_instruction`: 275
- `distractor_evidence`: 275
- `irrelevant_tools`: 275
- `long_horizon_dependency`: 275
- `memory_corruption`: 275
- `observation_conflict`: 275
- `premature_success_signal`: 275
- `tool_corruption`: 275
- `tool_failure`: 275
- `tool_removal`: 275

## Known Limitations

- Tasks are synthetic and template-derived.
- Automated quality checks are necessary but not sufficient for causal validity.
- Human audit is required before moving claims from planned to supported.
- Tool and scoring behavior remain deterministic approximations of real agent environments.
