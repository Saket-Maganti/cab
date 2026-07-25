# Generation Quality Report

Passed: `True`

## Counts

- Base tasks: 100
- Interventions: 500
- Instances: 600

## Distributions

### Domains

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

### Difficulties

- `easy`: 25
- `hard`: 25
- `medium`: 25
- `stress`: 25

### Intervention Families

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

## Statistics

- Average max steps: 6
- Average required tools: 3.75
- Duplicate task IDs: 0
- Duplicate instance IDs: 0

## Intervention Validity Scores

- `pass`: 400
- `warning`: 200

| Instance | Score | Family | Notes |
|---|---:|---|---|
| `scale100_v1__calendar_email_workflow_easy_001.ambiguous_instruction` | `warning` | `ambiguous_instruction` | final-answer scoring requires explicit audit attention |
| `scale100_v1__calendar_email_workflow_easy_001.clean` | `pass` | `clean` | None. |
| `scale100_v1__calendar_email_workflow_easy_001.distractor_evidence` | `pass` | `distractor_evidence` | None. |
| `scale100_v1__calendar_email_workflow_easy_001.long_horizon_dependency` | `pass` | `long_horizon_dependency` | None. |
| `scale100_v1__calendar_email_workflow_easy_001.observation_conflict` | `warning` | `observation_conflict` | intervention validity risk is marked high; final-answer scoring requires explicit audit attention |
| `scale100_v1__calendar_email_workflow_easy_001.premature_success_signal` | `pass` | `premature_success_signal` | None. |
| `scale100_v1__calendar_email_workflow_easy_005.ambiguous_instruction` | `warning` | `ambiguous_instruction` | final-answer scoring requires explicit audit attention |
| `scale100_v1__calendar_email_workflow_easy_005.clean` | `pass` | `clean` | None. |
| `scale100_v1__calendar_email_workflow_easy_005.distractor_evidence` | `pass` | `distractor_evidence` | None. |
| `scale100_v1__calendar_email_workflow_easy_005.long_horizon_dependency` | `pass` | `long_horizon_dependency` | None. |
| `scale100_v1__calendar_email_workflow_easy_005.observation_conflict` | `warning` | `observation_conflict` | intervention validity risk is marked high; final-answer scoring requires explicit audit attention |
| `scale100_v1__calendar_email_workflow_easy_005.premature_success_signal` | `pass` | `premature_success_signal` | None. |
| `scale100_v1__calendar_email_workflow_easy_007.ambiguous_instruction` | `warning` | `ambiguous_instruction` | final-answer scoring requires explicit audit attention |
| `scale100_v1__calendar_email_workflow_easy_007.clean` | `pass` | `clean` | None. |
| `scale100_v1__calendar_email_workflow_easy_007.distractor_evidence` | `pass` | `distractor_evidence` | None. |
| `scale100_v1__calendar_email_workflow_easy_007.long_horizon_dependency` | `pass` | `long_horizon_dependency` | None. |
| `scale100_v1__calendar_email_workflow_easy_007.observation_conflict` | `warning` | `observation_conflict` | intervention validity risk is marked high; final-answer scoring requires explicit audit attention |
| `scale100_v1__calendar_email_workflow_easy_007.premature_success_signal` | `pass` | `premature_success_signal` | None. |
| `scale100_v1__calendar_email_workflow_hard_004.ambiguous_instruction` | `warning` | `ambiguous_instruction` | final-answer scoring requires explicit audit attention |
| `scale100_v1__calendar_email_workflow_hard_004.clean` | `pass` | `clean` | None. |
| ... | ... | ... | 580 additional instances omitted. |

### Tool Patterns

- `check_calendar`: 6
- `check_calendar -> lookup_policy -> query_spreadsheet -> compare_options -> send_email_draft`: 1
- `check_calendar -> lookup_policy -> query_spreadsheet -> compare_options -> send_email_draft -> verify_fact`: 4
- `check_calendar -> send_email_draft -> verify_fact`: 3
- `check_calendar -> send_email_draft -> verify_fact -> search_database -> read_file`: 2
- `check_calendar -> send_email_draft -> verify_fact -> search_database -> read_file -> query_spreadsheet`: 1
- `compare_options`: 1
- `compare_options -> calculate_price -> verify_fact`: 6
- `compare_options -> calculate_price -> verify_fact -> search_database -> read_file`: 1
- `lookup_policy`: 4
- `lookup_policy -> search_database -> verify_fact`: 3
- `lookup_policy -> search_database -> verify_fact -> send_email_draft -> read_file`: 2

## Issues

### base_task_issues

None.

### intervention_issues

None.

### instance_issues

None.

### duplicate_instances

None.

### duplicate_tasks

None.

## Warnings

- intervention validity risk high for scale100_v1__calendar_email_workflow_medium_000.observation_conflict: observation_conflict

## Warning Examples

### high_validity_risk_interventions
- `scale100_v1__calendar_email_workflow_medium_000.observation_conflict`
- `scale100_v1__spreadsheet_qa_stress_000.observation_conflict`
- `scale100_v1__research_assistant_stress_000.observation_conflict`
- `scale100_v1__coding_debugging_stress_000.observation_conflict`
- `scale100_v1__customer_support_workflow_medium_000.observation_conflict`
### expected_answer_change_interventions
- `scale100_v1__travel_planning_hard_000.tool_removal`
- `scale100_v1__travel_planning_hard_000.tool_failure`
- `scale100_v1__calendar_email_workflow_medium_000.observation_conflict`
- `scale100_v1__calendar_email_workflow_medium_000.ambiguous_instruction`
- `scale100_v1__file_qa_hard_000.tool_removal`
### long_tool_sequences
- `scale100_v1__travel_planning_hard_000`
- `scale100_v1__file_qa_hard_000`
- `scale100_v1__spreadsheet_qa_stress_000`
- `scale100_v1__shopping_comparison_hard_000`
- `scale100_v1__research_assistant_stress_000`
### intervention_instances
- `scale100_v1__travel_planning_hard_000.tool_removal`
- `scale100_v1__travel_planning_hard_000.tool_failure`
- `scale100_v1__travel_planning_hard_000.tool_corruption`
- `scale100_v1__travel_planning_hard_000.irrelevant_tools`
- `scale100_v1__travel_planning_hard_000.memory_corruption`
