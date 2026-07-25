# Generation Quality Report

Passed: `True`

## Counts

- Base tasks: 500
- Interventions: 2500
- Instances: 3000

## Distributions

### Domains

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

### Difficulties

- `easy`: 125
- `hard`: 125
- `medium`: 125
- `stress`: 125

### Intervention Families

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

## Statistics

- Average max steps: 6
- Average required tools: 3.75
- Duplicate task IDs: 0
- Duplicate instance IDs: 0

## Intervention Validity Scores

- `pass`: 2000
- `warning`: 1000

| Instance | Score | Family | Notes |
|---|---:|---|---|
| `calendar_email_workflow_easy_005.ambiguous_instruction` | `warning` | `ambiguous_instruction` | final-answer scoring requires explicit audit attention |
| `calendar_email_workflow_easy_005.clean` | `pass` | `clean` | None. |
| `calendar_email_workflow_easy_005.distractor_evidence` | `pass` | `distractor_evidence` | None. |
| `calendar_email_workflow_easy_005.long_horizon_dependency` | `pass` | `long_horizon_dependency` | None. |
| `calendar_email_workflow_easy_005.observation_conflict` | `warning` | `observation_conflict` | intervention validity risk is marked high; final-answer scoring requires explicit audit attention |
| `calendar_email_workflow_easy_005.premature_success_signal` | `pass` | `premature_success_signal` | None. |
| `calendar_email_workflow_easy_009.ambiguous_instruction` | `warning` | `ambiguous_instruction` | final-answer scoring requires explicit audit attention |
| `calendar_email_workflow_easy_009.clean` | `pass` | `clean` | None. |
| `calendar_email_workflow_easy_009.distractor_evidence` | `pass` | `distractor_evidence` | None. |
| `calendar_email_workflow_easy_009.long_horizon_dependency` | `pass` | `long_horizon_dependency` | None. |
| `calendar_email_workflow_easy_009.observation_conflict` | `warning` | `observation_conflict` | intervention validity risk is marked high; final-answer scoring requires explicit audit attention |
| `calendar_email_workflow_easy_009.premature_success_signal` | `pass` | `premature_success_signal` | None. |
| `calendar_email_workflow_easy_010.ambiguous_instruction` | `warning` | `ambiguous_instruction` | final-answer scoring requires explicit audit attention |
| `calendar_email_workflow_easy_010.clean` | `pass` | `clean` | None. |
| `calendar_email_workflow_easy_010.distractor_evidence` | `pass` | `distractor_evidence` | None. |
| `calendar_email_workflow_easy_010.long_horizon_dependency` | `pass` | `long_horizon_dependency` | None. |
| `calendar_email_workflow_easy_010.observation_conflict` | `warning` | `observation_conflict` | intervention validity risk is marked high; final-answer scoring requires explicit audit attention |
| `calendar_email_workflow_easy_010.premature_success_signal` | `pass` | `premature_success_signal` | None. |
| `calendar_email_workflow_easy_016.ambiguous_instruction` | `warning` | `ambiguous_instruction` | final-answer scoring requires explicit audit attention |
| `calendar_email_workflow_easy_016.clean` | `pass` | `clean` | None. |
| ... | ... | ... | 2980 additional instances omitted. |

### Tool Patterns

- `check_calendar`: 17
- `check_calendar -> lookup_policy -> query_spreadsheet`: 12
- `check_calendar -> lookup_policy -> query_spreadsheet -> compare_options -> send_email_draft`: 11
- `check_calendar -> lookup_policy -> query_spreadsheet -> compare_options -> send_email_draft -> verify_fact`: 8
- `check_calendar -> send_email_draft -> verify_fact`: 16
- `check_calendar -> send_email_draft -> verify_fact -> search_database -> read_file`: 10
- `check_calendar -> send_email_draft -> verify_fact -> search_database -> read_file -> query_spreadsheet`: 9
- `compare_options`: 8
- `compare_options -> calculate_price -> verify_fact`: 9
- `compare_options -> calculate_price -> verify_fact -> search_database -> read_file`: 9
- `compare_options -> calculate_price -> verify_fact -> search_database -> read_file -> query_spreadsheet`: 16
- `lookup_policy`: 22

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

- intervention validity risk high for calendar_email_workflow_stress_000.observation_conflict: observation_conflict

## Warning Examples

### high_validity_risk_interventions
- `calendar_email_workflow_stress_000.observation_conflict`
- `spreadsheet_qa_easy_000.observation_conflict`
- `research_assistant_easy_000.observation_conflict`
- `coding_debugging_stress_000.observation_conflict`
- `customer_support_workflow_stress_000.observation_conflict`
### expected_answer_change_interventions
- `travel_planning_stress_000.tool_removal`
- `travel_planning_stress_000.tool_failure`
- `calendar_email_workflow_stress_000.observation_conflict`
- `calendar_email_workflow_stress_000.ambiguous_instruction`
- `file_qa_hard_000.tool_removal`
### long_tool_sequences
- `travel_planning_stress_000`
- `calendar_email_workflow_stress_000`
- `file_qa_hard_000`
- `shopping_comparison_hard_000`
- `coding_debugging_stress_000`
### intervention_instances
- `travel_planning_stress_000.tool_removal`
- `travel_planning_stress_000.tool_failure`
- `travel_planning_stress_000.tool_corruption`
- `travel_planning_stress_000.irrelevant_tools`
- `travel_planning_stress_000.memory_corruption`
