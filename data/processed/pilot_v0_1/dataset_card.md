# Dataset Card: pilot_v0.1

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

- Base tasks: 250
- Interventions: 1250
- Instances: 1500
- Quality passed: `True`
- Average max steps: 6.004
- Average required tools: 3.756
- Average interventions per task: 5.0

## Domain Distribution

- `calendar_email_workflow`: 32
- `coding_debugging`: 31
- `file_spreadsheet_qa`: 31
- `operations_planning`: 31
- `policy_compliance`: 31
- `research_assistant`: 31
- `shopping_comparison`: 31
- `travel_planning`: 32

## Intervention Distribution

- `ambiguous_instruction`: 125
- `distractor_evidence`: 125
- `irrelevant_tools`: 125
- `long_horizon_dependency`: 125
- `memory_corruption`: 125
- `observation_conflict`: 125
- `premature_success_signal`: 125
- `tool_corruption`: 125
- `tool_failure`: 125
- `tool_removal`: 125

## Known Limitations

- Tasks are synthetic and template-derived.
- Automated quality checks are necessary but not sufficient for causal validity.
- Human audit is required before moving claims from planned to supported.
- Tool and scoring behavior remain deterministic approximations of real agent environments.
