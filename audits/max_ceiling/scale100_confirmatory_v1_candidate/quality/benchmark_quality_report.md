# Benchmark Quality Report

Generated: 2026-07-23T16:50:21.795851+00:00

Static benchmark/data/config inspection only; no agents, providers, local models, or benchmark runs are invoked.

## Verdicts

- Ready for provider pilot quality gate: `True`
- Ready for main empirical claims: `False`
- Ready for release quality label: `False`

These verdicts are conservative static checks. They are not evidence of LLM behavior.

## Summary

- Datasets inspected: 1
- Tasks: 100
- Instances: 600
- Clean/intervention pairs: 500
- Overall quality score: 83
- Provider-pilot readiness score: 49
- Main benchmark readiness score: 49
- Release readiness score: 49
- Blockers: 1
- Warnings: 302
- Informational: 1
- Raw issues: 304
- Root-cause clusters: 5
- Suppressed/deduplicated symptoms: 299


## Main benchmark vs provider pilot

Provider-pilot blockers (leakage, tiny caps) are independent of main-benchmark readiness labels below.

### Main benchmark blockers

- `data/processed/scale100_confirmatory_v1_candidate`: **main_candidate_not_ready** — heldout=None, split_metadata=True, protected_split_risks=0

### Provider-pilot static quality (no leakage substitute)

- Datasets with static `ready_for_provider_pilot` quality verdict: 0
- Binding provider gate still requires leakage repair + advisor approval (see provider_pilot_preflight).

## Top Root Causes

- rank 1 `bq_root_main_candidate_not_ready__data_processed_scale100_confirmatory_v1_candidate__blocker` [blocker] main_candidate_not_ready in data/processed/scale100_confirmatory_v1_candidate (1 symptoms; gate=`must_fix_before_provider_pilot`)
- rank 2 `bq_root_high_risk_intervention__data_processed_scale100_confirmatory_v1_candidate__warning` [warning] high_risk_intervention in data/processed/scale100_confirmatory_v1_candidate (300 symptoms; gate=`must_fix_before_main_benchmark`)
- rank 3 `bq_root_missing_heldout_split__data_processed_scale100_confirmatory_v1_candidate__warning` [warning] missing_heldout_split in data/processed/scale100_confirmatory_v1_candidate (1 symptoms; gate=`must_fix_before_main_benchmark`)
- rank 4 `bq_root_quality_report_warning__data_processed_scale100_confirmatory_v1_candidate__warning` [warning] quality_report_warning in data/processed/scale100_confirmatory_v1_candidate (1 symptoms; gate=`must_fix_before_main_benchmark`)
- rank 5 `bq_root_quality_report_mentions_warnings__data_processed_scale100_confirmatory_v1_candidate__informational` [informational] quality_report_mentions_warnings in data/processed/scale100_confirmatory_v1_candidate (1 symptoms; gate=`nice_to_have`)

## Datasets

### `data/processed/scale100_confirmatory_v1_candidate`

- Tasks: 100
- Instances: 600
- Pairs: 500
- Provider-pilot quality ready: `True`
- Main-claims ready: `False`
- Release quality ready: `False`
- Heldout present: `False`
- Scores: overall `83`, provider `49`, main `49`, release `49`

| Category | Score | Weight | Notes |
|---|---:|---:|---|
| pair_completeness | 100 | 16 | 500/500 intervention instances paired |
| intervention_coverage | 100 | 8 | 10 intervention types |
| task_category_balance | 96 | 6 | 12 categories |
| difficulty_balance | 100 | 6 | 4 difficulty levels |
| tool_coverage | 100 | 6 | 27 tool patterns |
| expected_outputs | 100 | 14 | 0 missing expected outputs |
| duplicate_ids | 100 | 14 | 0 duplicate-id issues |
| heldout_split_status | 0 | 12 | heldout_present=False |
| generation_warnings | 86 | 5 | 1 generation warnings |
| high_risk_interventions | 0 | 4 | 300 high-risk interventions |
| metadata_completeness | 100 | 5 | 0 missing scenario metadata |
| dataset_leakage_risk | 100 | 4 | 0 leakage risks |

**Top blockers:**
- `main_candidate_not_ready`: Dataset name/config suggests a main candidate but heldout/split/pairing metadata is insufficient

**Recommended fixes:**
- Queue high-risk interventions for manual/human isolation review.
- Add a non-empty heldout/test split before main benchmark claims.
- Resolve generation quality warnings or document why they are acceptable.
- Do not call this dataset main-ready until split and pairing metadata are sufficient.

**Blockers:**
- `main_candidate_not_ready`: Dataset name/config suggests a main candidate but heldout/split/pairing metadata is insufficient

**Warnings:**
- `high_risk_intervention`: scale100_v1__travel_planning_hard_000.memory_corruption needs human review before causal-validity claims
- `high_risk_intervention`: scale100_v1__calendar_email_workflow_medium_000.observation_conflict needs human review before causal-validity claims
- `high_risk_intervention`: scale100_v1__calendar_email_workflow_medium_000.ambiguous_instruction needs human review before causal-validity claims
- `high_risk_intervention`: scale100_v1__calendar_email_workflow_medium_000.long_horizon_dependency needs human review before causal-validity claims
- `high_risk_intervention`: scale100_v1__calendar_email_workflow_medium_000.premature_success_signal needs human review before causal-validity claims
- `high_risk_intervention`: scale100_v1__calendar_email_workflow_medium_000.distractor_evidence needs human review before causal-validity claims
- `high_risk_intervention`: scale100_v1__file_qa_hard_000.memory_corruption needs human review before causal-validity claims
- `high_risk_intervention`: scale100_v1__spreadsheet_qa_stress_000.observation_conflict needs human review before causal-validity claims
- `high_risk_intervention`: scale100_v1__spreadsheet_qa_stress_000.ambiguous_instruction needs human review before causal-validity claims
- `high_risk_intervention`: scale100_v1__spreadsheet_qa_stress_000.long_horizon_dependency needs human review before causal-validity claims
- `high_risk_intervention`: scale100_v1__spreadsheet_qa_stress_000.premature_success_signal needs human review before causal-validity claims
- `high_risk_intervention`: scale100_v1__spreadsheet_qa_stress_000.distractor_evidence needs human review before causal-validity claims
- `high_risk_intervention`: scale100_v1__shopping_comparison_hard_000.memory_corruption needs human review before causal-validity claims
- `high_risk_intervention`: scale100_v1__research_assistant_stress_000.observation_conflict needs human review before causal-validity claims
- `high_risk_intervention`: scale100_v1__research_assistant_stress_000.ambiguous_instruction needs human review before causal-validity claims
- `high_risk_intervention`: scale100_v1__research_assistant_stress_000.long_horizon_dependency needs human review before causal-validity claims
- `high_risk_intervention`: scale100_v1__research_assistant_stress_000.premature_success_signal needs human review before causal-validity claims
- `high_risk_intervention`: scale100_v1__research_assistant_stress_000.distractor_evidence needs human review before causal-validity claims
- `high_risk_intervention`: scale100_v1__policy_compliance_medium_000.memory_corruption needs human review before causal-validity claims
- `high_risk_intervention`: scale100_v1__coding_debugging_stress_000.observation_conflict needs human review before causal-validity claims
- ... 282 more

**Informationals:**
- `quality_report_mentions_warnings`: quality_report.md contains warning/failed language; review details
