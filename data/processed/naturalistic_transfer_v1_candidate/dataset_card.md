# Dataset Card: naturalistic_transfer_v1_candidate

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

- Base tasks: 80
- Interventions: 400
- Instances: 480
- Quality passed: `False`
- Average max steps: 6.0
- Average required tools: 3.75
- Average interventions per task: 5.0

## Domain Distribution

- `mock_bug_report`: 10
- `mock_calendar_scheduling`: 10
- `mock_customer_escalation`: 10
- `mock_email_thread`: 10
- `mock_incident_postmortem`: 10
- `mock_policy_document`: 10
- `mock_product_database`: 10
- `mock_spreadsheet_ops`: 10

## Intervention Distribution

- `ambiguous_instruction`: 40
- `distractor_evidence`: 40
- `irrelevant_tools`: 40
- `long_horizon_dependency`: 40
- `memory_corruption`: 40
- `observation_conflict`: 40
- `premature_success_signal`: 40
- `tool_corruption`: 40
- `tool_failure`: 40
- `tool_removal`: 40

## Known Limitations

- Tasks are synthetic and template-derived.
- Automated quality checks are necessary but not sufficient for causal validity.
- Human audit is required before moving claims from planned to supported.
- Tool and scoring behavior remain deterministic approximations of real agent environments.
