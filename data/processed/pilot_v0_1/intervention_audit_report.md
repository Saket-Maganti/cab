# Generation Quality Report

Passed: `True`

## Counts

- Base tasks: 250
- Interventions: 1250
- Instances: 1500

## Distributions

### Domains

- `calendar_email_workflow`: 32
- `coding_debugging`: 31
- `file_spreadsheet_qa`: 31
- `operations_planning`: 31
- `policy_compliance`: 31
- `research_assistant`: 31
- `shopping_comparison`: 31
- `travel_planning`: 32

### Difficulties

- `easy`: 62
- `hard`: 62
- `medium`: 63
- `stress`: 63

### Intervention Families

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

## Statistics

- Average max steps: 6.004
- Average required tools: 3.756
- Duplicate task IDs: 0
- Duplicate instance IDs: 0

## Intervention Validity Scores

- `pass`: 1000
- `warning`: 500

| Instance | Score | Family | Notes |
|---|---:|---|---|
| `calendar_email_workflow_easy_000.ambiguous_instruction` | `warning` | `ambiguous_instruction` | final-answer scoring requires explicit audit attention |
| `calendar_email_workflow_easy_000.clean` | `pass` | `clean` | None. |
| `calendar_email_workflow_easy_000.distractor_evidence` | `pass` | `distractor_evidence` | None. |
| `calendar_email_workflow_easy_000.long_horizon_dependency` | `pass` | `long_horizon_dependency` | None. |
| `calendar_email_workflow_easy_000.observation_conflict` | `warning` | `observation_conflict` | intervention validity risk is marked high; final-answer scoring requires explicit audit attention |
| `calendar_email_workflow_easy_000.premature_success_signal` | `pass` | `premature_success_signal` | None. |
| `calendar_email_workflow_easy_009.ambiguous_instruction` | `warning` | `ambiguous_instruction` | final-answer scoring requires explicit audit attention |
| `calendar_email_workflow_easy_009.clean` | `pass` | `clean` | None. |
| `calendar_email_workflow_easy_009.distractor_evidence` | `pass` | `distractor_evidence` | None. |
| `calendar_email_workflow_easy_009.long_horizon_dependency` | `pass` | `long_horizon_dependency` | None. |
| `calendar_email_workflow_easy_009.observation_conflict` | `warning` | `observation_conflict` | intervention validity risk is marked high; final-answer scoring requires explicit audit attention |
| `calendar_email_workflow_easy_009.premature_success_signal` | `pass` | `premature_success_signal` | None. |
| `calendar_email_workflow_easy_012.ambiguous_instruction` | `warning` | `ambiguous_instruction` | final-answer scoring requires explicit audit attention |
| `calendar_email_workflow_easy_012.clean` | `pass` | `clean` | None. |
| `calendar_email_workflow_easy_012.distractor_evidence` | `pass` | `distractor_evidence` | None. |
| `calendar_email_workflow_easy_012.long_horizon_dependency` | `pass` | `long_horizon_dependency` | None. |
| `calendar_email_workflow_easy_012.observation_conflict` | `warning` | `observation_conflict` | intervention validity risk is marked high; final-answer scoring requires explicit audit attention |
| `calendar_email_workflow_easy_012.premature_success_signal` | `pass` | `premature_success_signal` | None. |
| `calendar_email_workflow_easy_015.ambiguous_instruction` | `warning` | `ambiguous_instruction` | final-answer scoring requires explicit audit attention |
| `calendar_email_workflow_easy_015.clean` | `pass` | `clean` | None. |
| ... | ... | ... | 1480 additional instances omitted. |

### Tool Patterns

- `check_calendar`: 14
- `check_calendar -> lookup_policy -> query_spreadsheet`: 7
- `check_calendar -> lookup_policy -> query_spreadsheet -> compare_options -> send_email_draft`: 10
- `check_calendar -> lookup_policy -> query_spreadsheet -> compare_options -> send_email_draft -> verify_fact`: 7
- `check_calendar -> send_email_draft -> verify_fact`: 10
- `check_calendar -> send_email_draft -> verify_fact -> search_database -> read_file`: 7
- `check_calendar -> send_email_draft -> verify_fact -> search_database -> read_file -> query_spreadsheet`: 8
- `compare_options`: 8
- `compare_options -> calculate_price -> verify_fact`: 12
- `compare_options -> calculate_price -> verify_fact -> search_database -> read_file`: 3
- `compare_options -> calculate_price -> verify_fact -> search_database -> read_file -> query_spreadsheet`: 8
- `lookup_policy`: 5

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

- intervention validity risk high for calendar_email_workflow_easy_000.observation_conflict: observation_conflict

## Warning Examples

### high_validity_risk_interventions
- `calendar_email_workflow_easy_000.observation_conflict`
- `shopping_comparison_easy_000.observation_conflict`
- `policy_compliance_hard_000.observation_conflict`
- `operations_planning_medium_000.observation_conflict`
- `calendar_email_workflow_medium_001.observation_conflict`
### expected_answer_change_interventions
- `travel_planning_medium_000.tool_removal`
- `travel_planning_medium_000.tool_failure`
- `calendar_email_workflow_easy_000.observation_conflict`
- `calendar_email_workflow_easy_000.ambiguous_instruction`
- `file_spreadsheet_qa_medium_000.tool_removal`
### long_tool_sequences
- `policy_compliance_hard_000`
- `coding_debugging_stress_000`
- `research_assistant_hard_001`
- `operations_planning_stress_001`
- `calendar_email_workflow_stress_002`
### intervention_instances
- `travel_planning_medium_000.tool_removal`
- `travel_planning_medium_000.tool_failure`
- `travel_planning_medium_000.tool_corruption`
- `travel_planning_medium_000.irrelevant_tools`
- `travel_planning_medium_000.memory_corruption`
