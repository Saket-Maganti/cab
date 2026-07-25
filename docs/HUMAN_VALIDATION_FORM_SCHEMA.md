# Human Validation Form Schema

This document defines the annotation fields used by `export-human-validation`. The export is a template for human review; blank label fields do not represent completed validation.

## Files

The exporter writes equivalent CSV and JSONL rows:

- `annotation_export.csv`
- `annotation_export.jsonl`

Each row is one annotator assignment for one sampled item. If `--annotators-per-item 2` is used, each item appears twice with different `annotator_slot` values.

## Identifier Fields

| Field | Type | Required | Description |
|---|---|---:|---|
| `annotation_id` | string | yes | Stable assignment id, usually `<item_id>.a<slot>`. |
| `annotator_slot` | integer | yes | Planned annotator slot, starting at 1. |
| `annotator_id` | string | no | Human annotator identifier or pseudonym. Do not use private personal data. |
| `item_id` | string | yes | Stable hash for the sampled run, instance, agent, and repeat. |
| `run_id` | string | yes | Run identifier from trajectory or score metadata. |
| `instance_id` | string | yes | Benchmark instance id. |
| `base_task_id` | string | yes | Base task id. |
| `agent_name` | string | yes | Agent run name. |
| `model_name` | string | no | Provider/model id when available. |

## Stratification Fields

| Field | Description |
|---|---|
| `domain` | Task domain. |
| `difficulty` | Task difficulty. |
| `condition` | `clean` or `intervention`. |
| `intervention_family` | Intervention family, or blank/`clean` for clean instances. |
| `expected_final_answer_change` | Whether the final answer is expected to change: `yes`, `no`, or `unclear`. |
| `outcome` | Automated outcome bucket such as `success`, `failure`, or `final_success_trajectory_failure`. |
| `error_taxonomy_label` | Automated error-case label, or `none`. |

## Evidence Fields

| Field | Description |
|---|---|
| `user_instruction` | User-facing task instruction. |
| `success_criteria` | JSON-encoded list of success criteria. |
| `expected_final_answer` | JSON-encoded expected final answer. |
| `intervention_description` | Intervention description, if any. |
| `changed_factor` | Intended target factor for the intervention. |
| `expected_robust_behavior` | Expected robust behavior under the intervention. |
| `final_answer` | Agent final answer. |
| `tool_calls` | Comma-separated tool names observed in the trajectory summary. |
| `terminated_reason` | Runner termination reason. |
| `score_details` | JSON-encoded automated metrics relevant to annotation. |
| `annotation_instructions` | Short reminder for allowed labels. |

## Annotation Labels

Allowed values for each label are:

- `yes`
- `no`
- `unclear`
- `not_applicable`

Leave a label blank only if the row has not yet been annotated.

| Field | Meaning |
|---|---|
| `task_understandable` | Whether the task is clear enough to evaluate. |
| `goal_preserved` | Whether the intervention preserves the high-level user goal. |
| `changed_factor_isolated` | Whether only the intended factor changed. |
| `expected_robust_behavior_reasonable` | Whether the expected robust behavior is reasonable for the intervention. |
| `final_answer_label_correct` | Whether the expected answer/scoring label is correct. |
| `trajectory_tool_misuse` | Whether the trajectory shows unavailable, irrelevant, malformed, or unsupported tool use. |
| `trajectory_showed_recovery` | Whether the agent recovered from a failure or limitation when one occurred. |
| `trajectory_detected_contradiction` | Whether the agent noticed relevant contradictory evidence. |
| `trajectory_stopped_prematurely` | Whether the agent stopped before satisfying success criteria. |
| `error_taxonomy_label_correct` | Whether the automated error taxonomy label matches the trajectory. |

## Adjudication Fields

Each annotation dimension has a matching adjudication field:

```text
adjudicated_<dimension>
```

For example:

- `adjudicated_task_understandable`
- `adjudicated_goal_preserved`
- `adjudicated_error_taxonomy_label_correct`

Use the same allowed values as annotation labels. Fill adjudicated labels only after reviewing annotator disagreements.

## Notes And Flags

| Field | Type | Description |
|---|---|---|
| `disagreement_flag` | string | Optional `yes`/`no` or free-text flag. |
| `annotator_notes` | string | Annotator rationale, uncertainty, or task-quality concern. |
| `adjudication_notes` | string | Adjudicator rationale and final decision explanation. |

## Minimal Valid Completed Row

A completed first-pass row should include:

- all identifier fields,
- `annotator_id`,
- one allowed value for every applicable annotation label,
- `annotator_notes` when any label is `unclear` or `no`.

Rows with blank labels are treated as incomplete by the agreement report.
