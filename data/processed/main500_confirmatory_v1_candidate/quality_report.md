# Generation Quality Report

Passed: `True`

## Counts

- Base tasks: 550
- Interventions: 2750
- Instances: 3300

## Distributions

### Domains

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

### Difficulties

- `easy`: 137
- `hard`: 137
- `medium`: 138
- `stress`: 138

### Intervention Families

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

## Statistics

- Average max steps: 6.002
- Average required tools: 3.753
- Duplicate task IDs: 0
- Duplicate instance IDs: 0

## Intervention Validity Scores

- `pass`: 2200
- `warning`: 1100

| Instance | Score | Family | Notes |
|---|---:|---|---|
| `main500_v1__calendar_email_workflow_easy_001.ambiguous_instruction` | `warning` | `ambiguous_instruction` | final-answer scoring requires explicit audit attention |
| `main500_v1__calendar_email_workflow_easy_001.clean` | `pass` | `clean` | None. |
| `main500_v1__calendar_email_workflow_easy_001.distractor_evidence` | `pass` | `distractor_evidence` | None. |
| `main500_v1__calendar_email_workflow_easy_001.long_horizon_dependency` | `pass` | `long_horizon_dependency` | None. |
| `main500_v1__calendar_email_workflow_easy_001.observation_conflict` | `warning` | `observation_conflict` | intervention validity risk is marked high; final-answer scoring requires explicit audit attention |
| `main500_v1__calendar_email_workflow_easy_001.premature_success_signal` | `pass` | `premature_success_signal` | None. |
| `main500_v1__calendar_email_workflow_easy_004.ambiguous_instruction` | `warning` | `ambiguous_instruction` | final-answer scoring requires explicit audit attention |
| `main500_v1__calendar_email_workflow_easy_004.clean` | `pass` | `clean` | None. |
| `main500_v1__calendar_email_workflow_easy_004.distractor_evidence` | `pass` | `distractor_evidence` | None. |
| `main500_v1__calendar_email_workflow_easy_004.long_horizon_dependency` | `pass` | `long_horizon_dependency` | None. |
| `main500_v1__calendar_email_workflow_easy_004.observation_conflict` | `warning` | `observation_conflict` | intervention validity risk is marked high; final-answer scoring requires explicit audit attention |
| `main500_v1__calendar_email_workflow_easy_004.premature_success_signal` | `pass` | `premature_success_signal` | None. |
| `main500_v1__calendar_email_workflow_easy_005.ambiguous_instruction` | `warning` | `ambiguous_instruction` | final-answer scoring requires explicit audit attention |
| `main500_v1__calendar_email_workflow_easy_005.clean` | `pass` | `clean` | None. |
| `main500_v1__calendar_email_workflow_easy_005.distractor_evidence` | `pass` | `distractor_evidence` | None. |
| `main500_v1__calendar_email_workflow_easy_005.long_horizon_dependency` | `pass` | `long_horizon_dependency` | None. |
| `main500_v1__calendar_email_workflow_easy_005.observation_conflict` | `warning` | `observation_conflict` | intervention validity risk is marked high; final-answer scoring requires explicit audit attention |
| `main500_v1__calendar_email_workflow_easy_005.premature_success_signal` | `pass` | `premature_success_signal` | None. |
| `main500_v1__calendar_email_workflow_easy_006.ambiguous_instruction` | `warning` | `ambiguous_instruction` | final-answer scoring requires explicit audit attention |
| `main500_v1__calendar_email_workflow_easy_006.clean` | `pass` | `clean` | None. |
| ... | ... | ... | 3280 additional instances omitted. |

### Tool Patterns

- `check_calendar`: 23
- `check_calendar -> lookup_policy -> query_spreadsheet`: 12
- `check_calendar -> lookup_policy -> query_spreadsheet -> compare_options -> send_email_draft`: 12
- `check_calendar -> lookup_policy -> query_spreadsheet -> compare_options -> send_email_draft -> verify_fact`: 14
- `check_calendar -> send_email_draft -> verify_fact`: 5
- `check_calendar -> send_email_draft -> verify_fact -> search_database -> read_file`: 14
- `check_calendar -> send_email_draft -> verify_fact -> search_database -> read_file -> query_spreadsheet`: 12
- `compare_options`: 14
- `compare_options -> calculate_price -> verify_fact`: 11
- `compare_options -> calculate_price -> verify_fact -> search_database -> read_file`: 7
- `compare_options -> calculate_price -> verify_fact -> search_database -> read_file -> query_spreadsheet`: 14
- `lookup_policy`: 19

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

- intervention validity risk high for main500_v1__calendar_email_workflow_hard_000.observation_conflict: observation_conflict

## Warning Examples

### high_validity_risk_interventions
- `main500_v1__calendar_email_workflow_hard_000.observation_conflict`
- `main500_v1__spreadsheet_qa_easy_000.observation_conflict`
- `main500_v1__research_assistant_hard_000.observation_conflict`
- `main500_v1__coding_debugging_easy_000.observation_conflict`
- `main500_v1__customer_support_workflow_easy_000.observation_conflict`
### expected_answer_change_interventions
- `main500_v1__travel_planning_medium_000.tool_removal`
- `main500_v1__travel_planning_medium_000.tool_failure`
- `main500_v1__calendar_email_workflow_hard_000.observation_conflict`
- `main500_v1__calendar_email_workflow_hard_000.ambiguous_instruction`
- `main500_v1__file_qa_easy_000.tool_removal`
### long_tool_sequences
- `main500_v1__calendar_email_workflow_hard_000`
- `main500_v1__shopping_comparison_stress_000`
- `main500_v1__research_assistant_hard_000`
- `main500_v1__policy_compliance_stress_000`
- `main500_v1__finance_admin_workflow_stress_000`
### intervention_instances
- `main500_v1__travel_planning_medium_000.tool_removal`
- `main500_v1__travel_planning_medium_000.tool_failure`
- `main500_v1__travel_planning_medium_000.tool_corruption`
- `main500_v1__travel_planning_medium_000.irrelevant_tools`
- `main500_v1__travel_planning_medium_000.memory_corruption`
