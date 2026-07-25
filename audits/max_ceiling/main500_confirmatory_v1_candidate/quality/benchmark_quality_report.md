# Benchmark Quality Report

Generated: 2026-07-23T16:50:22.231597+00:00

Static benchmark/data/config inspection only; no agents, providers, local models, or benchmark runs are invoked.

## Verdicts

- Ready for provider pilot quality gate: `True`
- Ready for main empirical claims: `True`
- Ready for release quality label: `False`

These verdicts are conservative static checks. They are not evidence of LLM behavior.

## Summary

- Datasets inspected: 1
- Tasks: 550
- Instances: 3300
- Clean/intervention pairs: 2750
- Overall quality score: 95
- Provider-pilot readiness score: 95
- Main benchmark readiness score: 95
- Release readiness score: 70
- Blockers: 0
- Warnings: 1651
- Informational: 1
- Raw issues: 1652
- Root-cause clusters: 3
- Suppressed/deduplicated symptoms: 1649


## Main benchmark vs provider pilot

Provider-pilot blockers (leakage, tiny caps) are independent of main-benchmark readiness labels below.

### Main benchmark blockers

- (none flagged as main_candidate_not_ready)

### Provider-pilot static quality (no leakage substitute)

- Datasets with static `ready_for_provider_pilot` quality verdict: 1
- Binding provider gate still requires leakage repair + advisor approval (see provider_pilot_preflight).

## Top Root Causes

- rank 1 `bq_root_high_risk_intervention__data_processed_main500_confirmatory_v1_candidate__warning` [warning] high_risk_intervention in data/processed/main500_confirmatory_v1_candidate (1650 symptoms; gate=`must_fix_before_main_benchmark`)
- rank 2 `bq_root_quality_report_warning__data_processed_main500_confirmatory_v1_candidate__warning` [warning] quality_report_warning in data/processed/main500_confirmatory_v1_candidate (1 symptoms; gate=`must_fix_before_main_benchmark`)
- rank 3 `bq_root_quality_report_mentions_warnings__data_processed_main500_confirmatory_v1_candidate__informational` [informational] quality_report_mentions_warnings in data/processed/main500_confirmatory_v1_candidate (1 symptoms; gate=`nice_to_have`)

## Datasets

### `data/processed/main500_confirmatory_v1_candidate`

- Tasks: 550
- Instances: 3300
- Pairs: 2750
- Provider-pilot quality ready: `True`
- Main-claims ready: `True`
- Release quality ready: `False`
- Heldout present: `True`
- Scores: overall `95`, provider `95`, main `95`, release `70`

| Category | Score | Weight | Notes |
|---|---:|---:|---|
| pair_completeness | 100 | 16 | 2750/2750 intervention instances paired |
| intervention_coverage | 100 | 8 | 10 intervention types |
| task_category_balance | 99 | 6 | 12 categories |
| difficulty_balance | 100 | 6 | 4 difficulty levels |
| tool_coverage | 100 | 6 | 27 tool patterns |
| expected_outputs | 100 | 14 | 0 missing expected outputs |
| duplicate_ids | 100 | 14 | 0 duplicate-id issues |
| heldout_split_status | 100 | 12 | heldout_present=True |
| generation_warnings | 86 | 5 | 1 generation warnings |
| high_risk_interventions | 0 | 4 | 1650 high-risk interventions |
| metadata_completeness | 100 | 5 | 0 missing scenario metadata |
| dataset_leakage_risk | 100 | 4 | 0 leakage risks |

**Recommended fixes:**
- Queue high-risk interventions for manual/human isolation review.
- Resolve generation quality warnings or document why they are acceptable.

**Warnings:**
- `high_risk_intervention`: main500_v1__travel_planning_medium_000.memory_corruption needs human review before causal-validity claims
- `high_risk_intervention`: main500_v1__calendar_email_workflow_hard_000.observation_conflict needs human review before causal-validity claims
- `high_risk_intervention`: main500_v1__calendar_email_workflow_hard_000.ambiguous_instruction needs human review before causal-validity claims
- `high_risk_intervention`: main500_v1__calendar_email_workflow_hard_000.long_horizon_dependency needs human review before causal-validity claims
- `high_risk_intervention`: main500_v1__calendar_email_workflow_hard_000.premature_success_signal needs human review before causal-validity claims
- `high_risk_intervention`: main500_v1__calendar_email_workflow_hard_000.distractor_evidence needs human review before causal-validity claims
- `high_risk_intervention`: main500_v1__file_qa_easy_000.memory_corruption needs human review before causal-validity claims
- `high_risk_intervention`: main500_v1__spreadsheet_qa_easy_000.observation_conflict needs human review before causal-validity claims
- `high_risk_intervention`: main500_v1__spreadsheet_qa_easy_000.ambiguous_instruction needs human review before causal-validity claims
- `high_risk_intervention`: main500_v1__spreadsheet_qa_easy_000.long_horizon_dependency needs human review before causal-validity claims
- `high_risk_intervention`: main500_v1__spreadsheet_qa_easy_000.premature_success_signal needs human review before causal-validity claims
- `high_risk_intervention`: main500_v1__spreadsheet_qa_easy_000.distractor_evidence needs human review before causal-validity claims
- `high_risk_intervention`: main500_v1__shopping_comparison_stress_000.memory_corruption needs human review before causal-validity claims
- `high_risk_intervention`: main500_v1__research_assistant_hard_000.observation_conflict needs human review before causal-validity claims
- `high_risk_intervention`: main500_v1__research_assistant_hard_000.ambiguous_instruction needs human review before causal-validity claims
- `high_risk_intervention`: main500_v1__research_assistant_hard_000.long_horizon_dependency needs human review before causal-validity claims
- `high_risk_intervention`: main500_v1__research_assistant_hard_000.premature_success_signal needs human review before causal-validity claims
- `high_risk_intervention`: main500_v1__research_assistant_hard_000.distractor_evidence needs human review before causal-validity claims
- `high_risk_intervention`: main500_v1__policy_compliance_stress_000.memory_corruption needs human review before causal-validity claims
- `high_risk_intervention`: main500_v1__coding_debugging_easy_000.observation_conflict needs human review before causal-validity claims
- ... 1631 more

**Informationals:**
- `quality_report_mentions_warnings`: quality_report.md contains warning/failed language; review details
