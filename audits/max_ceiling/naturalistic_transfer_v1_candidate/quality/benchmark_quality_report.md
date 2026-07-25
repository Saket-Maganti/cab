# Benchmark Quality Report

Generated: 2026-07-23T16:50:21.753954+00:00

Static benchmark/data/config inspection only; no agents, providers, local models, or benchmark runs are invoked.

## Verdicts

- Ready for provider pilot quality gate: `True`
- Ready for main empirical claims: `True`
- Ready for release quality label: `False`

These verdicts are conservative static checks. They are not evidence of LLM behavior.

## Summary

- Datasets inspected: 1
- Tasks: 80
- Instances: 480
- Clean/intervention pairs: 400
- Overall quality score: 95
- Provider-pilot readiness score: 95
- Main benchmark readiness score: 95
- Release readiness score: 70
- Blockers: 0
- Warnings: 241
- Informational: 1
- Raw issues: 242
- Root-cause clusters: 3
- Suppressed/deduplicated symptoms: 239


## Main benchmark vs provider pilot

Provider-pilot blockers (leakage, tiny caps) are independent of main-benchmark readiness labels below.

### Main benchmark blockers

- (none flagged as main_candidate_not_ready)

### Provider-pilot static quality (no leakage substitute)

- Datasets with static `ready_for_provider_pilot` quality verdict: 1
- Binding provider gate still requires leakage repair + advisor approval (see provider_pilot_preflight).

## Top Root Causes

- rank 1 `bq_root_high_risk_intervention__data_processed_naturalistic_transfer_v1_candidate__warning` [warning] high_risk_intervention in data/processed/naturalistic_transfer_v1_candidate (240 symptoms; gate=`must_fix_before_main_benchmark`)
- rank 2 `bq_root_quality_report_warning__data_processed_naturalistic_transfer_v1_candidate__warning` [warning] quality_report_warning in data/processed/naturalistic_transfer_v1_candidate (1 symptoms; gate=`must_fix_before_main_benchmark`)
- rank 3 `bq_root_quality_report_mentions_warnings__data_processed_naturalistic_transfer_v1_candidate__informational` [informational] quality_report_mentions_warnings in data/processed/naturalistic_transfer_v1_candidate (1 symptoms; gate=`nice_to_have`)

## Datasets

### `data/processed/naturalistic_transfer_v1_candidate`

- Tasks: 80
- Instances: 480
- Pairs: 400
- Provider-pilot quality ready: `True`
- Main-claims ready: `True`
- Release quality ready: `False`
- Heldout present: `True`
- Scores: overall `95`, provider `95`, main `95`, release `70`

| Category | Score | Weight | Notes |
|---|---:|---:|---|
| pair_completeness | 100 | 16 | 400/400 intervention instances paired |
| intervention_coverage | 100 | 8 | 10 intervention types |
| task_category_balance | 100 | 6 | 8 categories |
| difficulty_balance | 100 | 6 | 4 difficulty levels |
| tool_coverage | 100 | 6 | 17 tool patterns |
| expected_outputs | 100 | 14 | 0 missing expected outputs |
| duplicate_ids | 100 | 14 | 0 duplicate-id issues |
| heldout_split_status | 100 | 12 | heldout_present=True |
| generation_warnings | 86 | 5 | 1 generation warnings |
| high_risk_interventions | 0 | 4 | 240 high-risk interventions |
| metadata_completeness | 100 | 5 | 0 missing scenario metadata |
| dataset_leakage_risk | 100 | 4 | 0 leakage risks |

**Recommended fixes:**
- Queue high-risk interventions for manual/human isolation review.
- Resolve generation quality warnings or document why they are acceptable.

**Warnings:**
- `high_risk_intervention`: naturalistic_v1__natural_mock_email_thread_medium_000.memory_corruption needs human review before causal-validity claims
- `high_risk_intervention`: naturalistic_v1__natural_mock_calendar_scheduling_medium_000.observation_conflict needs human review before causal-validity claims
- `high_risk_intervention`: naturalistic_v1__natural_mock_calendar_scheduling_medium_000.ambiguous_instruction needs human review before causal-validity claims
- `high_risk_intervention`: naturalistic_v1__natural_mock_calendar_scheduling_medium_000.long_horizon_dependency needs human review before causal-validity claims
- `high_risk_intervention`: naturalistic_v1__natural_mock_calendar_scheduling_medium_000.premature_success_signal needs human review before causal-validity claims
- `high_risk_intervention`: naturalistic_v1__natural_mock_calendar_scheduling_medium_000.distractor_evidence needs human review before causal-validity claims
- `high_risk_intervention`: naturalistic_v1__natural_mock_spreadsheet_ops_hard_000.memory_corruption needs human review before causal-validity claims
- `high_risk_intervention`: naturalistic_v1__natural_mock_policy_document_easy_000.observation_conflict needs human review before causal-validity claims
- `high_risk_intervention`: naturalistic_v1__natural_mock_policy_document_easy_000.ambiguous_instruction needs human review before causal-validity claims
- `high_risk_intervention`: naturalistic_v1__natural_mock_policy_document_easy_000.long_horizon_dependency needs human review before causal-validity claims
- `high_risk_intervention`: naturalistic_v1__natural_mock_policy_document_easy_000.premature_success_signal needs human review before causal-validity claims
- `high_risk_intervention`: naturalistic_v1__natural_mock_policy_document_easy_000.distractor_evidence needs human review before causal-validity claims
- `high_risk_intervention`: naturalistic_v1__natural_mock_bug_report_stress_000.memory_corruption needs human review before causal-validity claims
- `high_risk_intervention`: naturalistic_v1__natural_mock_product_database_medium_000.observation_conflict needs human review before causal-validity claims
- `high_risk_intervention`: naturalistic_v1__natural_mock_product_database_medium_000.ambiguous_instruction needs human review before causal-validity claims
- `high_risk_intervention`: naturalistic_v1__natural_mock_product_database_medium_000.long_horizon_dependency needs human review before causal-validity claims
- `high_risk_intervention`: naturalistic_v1__natural_mock_product_database_medium_000.premature_success_signal needs human review before causal-validity claims
- `high_risk_intervention`: naturalistic_v1__natural_mock_product_database_medium_000.distractor_evidence needs human review before causal-validity claims
- `high_risk_intervention`: naturalistic_v1__natural_mock_customer_escalation_stress_000.memory_corruption needs human review before causal-validity claims
- `high_risk_intervention`: naturalistic_v1__natural_mock_incident_postmortem_easy_000.observation_conflict needs human review before causal-validity claims
- ... 221 more

**Informationals:**
- `quality_report_mentions_warnings`: quality_report.md contains warning/failed language; review details
