# First 3-Model Pilot Result Table Schemas

Status: `SCHEMA_ONLY_NO_RESULTS`

All values below are placeholders or field names. No fake numbers are present. Every future value must be filled from a completed, audited, provider-backed run plus the required review artifacts.

Use `TODO_REAL_RESULT` for any cell that requires execution.

## Model Metadata Table

Required columns:

- `model_category`
- `provider_id`
- `model_id`
- `model_release_or_snapshot`
- `deployment_class`
- `pricing_registry_status`
- `temperature`
- `max_tokens`
- `retry_policy`
- `prompt_hash`
- `config_hash`
- `run_id`
- `paper_eligible_after_audit`

Future row template:

| model_category | provider_id | model_id | model_release_or_snapshot | deployment_class | pricing_registry_status | temperature | max_tokens | retry_policy | prompt_hash | config_hash | run_id | paper_eligible_after_audit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| TODO_MODEL_CATEGORY | TODO_PROVIDER | TODO_MODEL | TODO_SNAPSHOT | TODO_DEPLOYMENT_CLASS | TODO_PRICE_STATUS | TODO_REAL_RESULT | TODO_REAL_RESULT | TODO_POLICY | TODO_HASH | TODO_HASH | TODO_RUN_ID | TODO_AFTER_AUDIT |

## Clean Vs Intervention Success Table

Required columns:

- `model_id`
- `family`
- `n_pairs`
- `clean_success_rate`
- `intervention_success_rate`
- `paired_delta`
- `uncertainty_interval`
- `scorer_issue_count`
- `audit_status`

Every result cell remains `TODO_REAL_RESULT` until execution and post-run audit.

## ACRS Table

Required columns:

- `model_id`
- `acrs`
- `acrs_uncertainty_interval`
- `clean_success_rank`
- `acrs_rank`
- `rank_delta`
- `valid_pair_count`
- `excluded_pair_count`
- `audit_status`

Every result cell remains `TODO_REAL_RESULT`.

## Rank Instability Table

Required columns:

- `model_id`
- `clean_success_rank`
- `acrs_rank`
- `rank_delta`
- `rank_change_direction`
- `bootstrap_rank_change_frequency`
- `interpretation_allowed`

`interpretation_allowed` must be `no` until the uncertainty analysis is complete.

## Per-Family Degradation Table

Required columns:

- `model_id`
- `family`
- `n_reviewed_pairs`
- `clean_success_rate`
- `intervention_success_rate`
- `paired_delta`
- `uncertainty_interval`
- `dominant_failure_flags`
- `manual_review_notes_link`

Families expected from the current Compact-20 candidate manifest:

- `tool_removal`
- `tool_failure`
- `memory_corruption`
- `observation_conflict`

## Scorer Sanity Table

Required columns:

- `run_id`
- `model_id`
- `trajectory_count_expected`
- `trajectory_count_scored`
- `missing_scores`
- `malformed_outputs`
- `scorer_issue_flags`
- `manual_sample_review_status`
- `scorer_sanity_verdict`

All count/verdict cells require real run artifacts.

## Manual And C10 Validation Linkage Table

Required columns:

- `candidate_id`
- `clean_instance_id`
- `intervention_instance_id`
- `family`
- `task_review_status`
- `gold_policy_review_status`
- `c10_review_status`
- `reviewer_count`
- `adjudication_status`
- `claim_use_allowed`

`claim_use_allowed` must remain `no` for C10 until the C10 protocol is complete and audited.

## Forbidden Table Practices

- Do not enter illustrative numeric values.
- Do not infer missing results.
- Do not copy local-preliminary values into provider-backed columns.
- Do not mark paper eligibility before post-run audit.
- Do not hide `TODO_REAL_RESULT` placeholders in draft tables.

