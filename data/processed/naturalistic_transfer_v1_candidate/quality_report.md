# Generation Quality Report

Passed: `False`

## Counts

- Base tasks: 80
- Interventions: 400
- Instances: 480

## Distributions

### Domains

- `mock_bug_report`: 10
- `mock_calendar_scheduling`: 10
- `mock_customer_escalation`: 10
- `mock_email_thread`: 10
- `mock_incident_postmortem`: 10
- `mock_policy_document`: 10
- `mock_product_database`: 10
- `mock_spreadsheet_ops`: 10

### Difficulties

- `easy`: 20
- `hard`: 20
- `medium`: 20
- `stress`: 20

### Intervention Families

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

## Statistics

- Average max steps: 6
- Average required tools: 3.75
- Duplicate task IDs: 0
- Duplicate instance IDs: 0

## Intervention Validity Scores

- `fail`: 210
- `pass`: 180
- `warning`: 90

| Instance | Score | Family | Notes |
|---|---:|---|---|
| `naturalistic_v1__natural_mock_bug_report_easy_001.clean` | `pass` | `clean` | None. |
| `naturalistic_v1__natural_mock_bug_report_easy_001.irrelevant_tools` | `pass` | `irrelevant_tools` | None. |
| `naturalistic_v1__natural_mock_bug_report_easy_001.memory_corruption` | `pass` | `memory_corruption` | None. |
| `naturalistic_v1__natural_mock_bug_report_easy_001.tool_corruption` | `pass` | `tool_corruption` | None. |
| `naturalistic_v1__natural_mock_bug_report_easy_001.tool_failure` | `warning` | `tool_failure` | final-answer scoring requires explicit audit attention |
| `naturalistic_v1__natural_mock_bug_report_easy_001.tool_removal` | `warning` | `tool_removal` | final-answer scoring requires explicit audit attention |
| `naturalistic_v1__natural_mock_bug_report_easy_003.clean` | `pass` | `clean` | None. |
| `naturalistic_v1__natural_mock_bug_report_easy_003.irrelevant_tools` | `pass` | `irrelevant_tools` | None. |
| `naturalistic_v1__natural_mock_bug_report_easy_003.memory_corruption` | `pass` | `memory_corruption` | None. |
| `naturalistic_v1__natural_mock_bug_report_easy_003.tool_corruption` | `pass` | `tool_corruption` | None. |
| `naturalistic_v1__natural_mock_bug_report_easy_003.tool_failure` | `warning` | `tool_failure` | final-answer scoring requires explicit audit attention |
| `naturalistic_v1__natural_mock_bug_report_easy_003.tool_removal` | `warning` | `tool_removal` | final-answer scoring requires explicit audit attention |
| `naturalistic_v1__natural_mock_bug_report_easy_004.clean` | `pass` | `clean` | None. |
| `naturalistic_v1__natural_mock_bug_report_easy_004.irrelevant_tools` | `pass` | `irrelevant_tools` | None. |
| `naturalistic_v1__natural_mock_bug_report_easy_004.memory_corruption` | `pass` | `memory_corruption` | None. |
| `naturalistic_v1__natural_mock_bug_report_easy_004.tool_corruption` | `pass` | `tool_corruption` | None. |
| `naturalistic_v1__natural_mock_bug_report_easy_004.tool_failure` | `warning` | `tool_failure` | final-answer scoring requires explicit audit attention |
| `naturalistic_v1__natural_mock_bug_report_easy_004.tool_removal` | `warning` | `tool_removal` | final-answer scoring requires explicit audit attention |
| `naturalistic_v1__natural_mock_bug_report_easy_006.clean` | `pass` | `clean` | None. |
| `naturalistic_v1__natural_mock_bug_report_easy_006.irrelevant_tools` | `pass` | `irrelevant_tools` | None. |
| ... | ... | ... | 460 additional instances omitted. |

### Tool Patterns

- `check_calendar -> read_file -> send_email_draft`: 5
- `check_calendar -> read_file -> send_email_draft -> verify_fact -> search_database`: 2
- `check_calendar -> read_file -> send_email_draft -> verify_fact -> search_database -> query_spreadsheet`: 3
- `read_file`: 15
- `read_file -> lookup_policy -> verify_fact`: 5
- `read_file -> lookup_policy -> verify_fact -> search_database -> query_spreadsheet`: 6
- `read_file -> lookup_policy -> verify_fact -> search_database -> query_spreadsheet -> compare_options`: 2
- `read_file -> lookup_policy -> verify_fact -> send_email_draft -> search_database`: 6
- `read_file -> lookup_policy -> verify_fact -> send_email_draft -> search_database -> query_spreadsheet`: 5
- `read_file -> query_spreadsheet -> compare_options`: 3
- `read_file -> query_spreadsheet -> compare_options -> verify_fact -> search_database`: 2
- `read_file -> query_spreadsheet -> compare_options -> verify_fact -> search_database -> lookup_policy`: 2

## Issues

### base_task_issues
- `naturalistic_v1__natural_mock_email_thread_medium_000`: email workflow must explicitly forbid real sending
- `naturalistic_v1__natural_mock_calendar_scheduling_medium_000`: email workflow must explicitly forbid real sending
- `naturalistic_v1__natural_mock_spreadsheet_ops_hard_000`: instruction may imply live booking
- `naturalistic_v1__natural_mock_email_thread_medium_001`: email workflow must explicitly forbid real sending
- `naturalistic_v1__natural_mock_calendar_scheduling_medium_001`: email workflow must explicitly forbid real sending
- `naturalistic_v1__natural_mock_spreadsheet_ops_stress_001`: instruction may imply live booking
- `naturalistic_v1__natural_mock_policy_document_hard_001`: instruction may imply live booking
- `naturalistic_v1__natural_mock_email_thread_hard_002`: email workflow must explicitly forbid real sending
- `naturalistic_v1__natural_mock_calendar_scheduling_hard_002`: email workflow must explicitly forbid real sending
- `naturalistic_v1__natural_mock_spreadsheet_ops_medium_002`: instruction may imply live booking
- `naturalistic_v1__natural_mock_email_thread_easy_003`: email workflow must explicitly forbid real sending
- `naturalistic_v1__natural_mock_calendar_scheduling_stress_003`: email workflow must explicitly forbid real sending
- `naturalistic_v1__natural_mock_spreadsheet_ops_easy_003`: instruction may imply live booking
- `naturalistic_v1__natural_mock_policy_document_easy_003`: instruction may imply live booking
- `naturalistic_v1__natural_mock_email_thread_stress_004`: email workflow must explicitly forbid real sending
- `naturalistic_v1__natural_mock_calendar_scheduling_medium_004`: email workflow must explicitly forbid real sending
- `naturalistic_v1__natural_mock_spreadsheet_ops_stress_004`: instruction may imply live booking
- `naturalistic_v1__natural_mock_email_thread_hard_005`: email workflow must explicitly forbid real sending
- `naturalistic_v1__natural_mock_calendar_scheduling_stress_005`: email workflow must explicitly forbid real sending
- `naturalistic_v1__natural_mock_spreadsheet_ops_easy_005`: instruction may imply live booking
- `naturalistic_v1__natural_mock_policy_document_stress_005`: instruction may imply live booking
- `naturalistic_v1__natural_mock_email_thread_stress_006`: email workflow must explicitly forbid real sending
- `naturalistic_v1__natural_mock_calendar_scheduling_stress_006`: email workflow must explicitly forbid real sending
- `naturalistic_v1__natural_mock_spreadsheet_ops_medium_006`: instruction may imply live booking
- `naturalistic_v1__natural_mock_email_thread_easy_007`: email workflow must explicitly forbid real sending
- `naturalistic_v1__natural_mock_calendar_scheduling_medium_007`: email workflow must explicitly forbid real sending
- `naturalistic_v1__natural_mock_spreadsheet_ops_easy_007`: instruction may imply live booking
- `naturalistic_v1__natural_mock_policy_document_stress_007`: instruction may imply live booking
- `naturalistic_v1__natural_mock_email_thread_hard_008`: email workflow must explicitly forbid real sending
- `naturalistic_v1__natural_mock_calendar_scheduling_medium_008`: email workflow must explicitly forbid real sending
- `naturalistic_v1__natural_mock_spreadsheet_ops_hard_008`: instruction may imply live booking
- `naturalistic_v1__natural_mock_email_thread_medium_009`: email workflow must explicitly forbid real sending
- `naturalistic_v1__natural_mock_calendar_scheduling_hard_009`: email workflow must explicitly forbid real sending
- `naturalistic_v1__natural_mock_spreadsheet_ops_medium_009`: instruction may imply live booking
- `naturalistic_v1__natural_mock_policy_document_hard_009`: instruction may imply live booking

### intervention_issues

None.

### instance_issues

None.

### duplicate_instances

None.

### duplicate_tasks

None.

## Warnings

- intervention validity risk high for naturalistic_v1__natural_mock_calendar_scheduling_medium_000.observation_conflict: observation_conflict

## Warning Examples

### high_validity_risk_interventions
- `naturalistic_v1__natural_mock_calendar_scheduling_medium_000.observation_conflict`
- `naturalistic_v1__natural_mock_policy_document_easy_000.observation_conflict`
- `naturalistic_v1__natural_mock_product_database_medium_000.observation_conflict`
- `naturalistic_v1__natural_mock_incident_postmortem_easy_000.observation_conflict`
- `naturalistic_v1__natural_mock_calendar_scheduling_medium_001.observation_conflict`
### expected_answer_change_interventions
- `naturalistic_v1__natural_mock_email_thread_medium_000.tool_removal`
- `naturalistic_v1__natural_mock_email_thread_medium_000.tool_failure`
- `naturalistic_v1__natural_mock_calendar_scheduling_medium_000.observation_conflict`
- `naturalistic_v1__natural_mock_calendar_scheduling_medium_000.ambiguous_instruction`
- `naturalistic_v1__natural_mock_spreadsheet_ops_hard_000.tool_removal`
### long_tool_sequences
- `naturalistic_v1__natural_mock_spreadsheet_ops_hard_000`
- `naturalistic_v1__natural_mock_bug_report_stress_000`
- `naturalistic_v1__natural_mock_customer_escalation_stress_000`
- `naturalistic_v1__natural_mock_spreadsheet_ops_stress_001`
- `naturalistic_v1__natural_mock_policy_document_hard_001`
### intervention_instances
- `naturalistic_v1__natural_mock_email_thread_medium_000.tool_removal`
- `naturalistic_v1__natural_mock_email_thread_medium_000.tool_failure`
- `naturalistic_v1__natural_mock_email_thread_medium_000.tool_corruption`
- `naturalistic_v1__natural_mock_email_thread_medium_000.irrelevant_tools`
- `naturalistic_v1__natural_mock_email_thread_medium_000.memory_corruption`
