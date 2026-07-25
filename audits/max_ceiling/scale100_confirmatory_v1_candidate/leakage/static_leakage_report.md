# Static Leakage Report

Generated: 2026-07-23T16:50:22.313022+00:00

Static leakage heuristics only; no embeddings, models, providers, or benchmark runs.

This is a static heuristic report, not empirical model evidence.

## Executive Summary

- Datasets scanned: 1
- Raw findings: 6160
- Deduplicated findings: 6070
- Root-cause clusters: 30
- Active clusters (post-suppression): 30
- Suppressed clusters (reviewed registry): 0
- Suppressed/deduplicated symptoms: 6130
- Blockers: 0
- Warnings: 3852
- Blocker clusters: 0
- False-positive candidate clusters: 4
- Needs-review clusters: 0
- Active suppression entries: 0
- Expired suppression entries: 0
- Refused suppression attempts (blocker classes): 0

## Classification Counts

- `clean_intervention_pair_similarity`: 1
- `expected_subset_overlap`: 2
- `instruction_parameter_overlap`: 1
- `needs_manual_review`: 26

## Top True Leakage Blockers

- (none)

## Top Provider-Pilot Leakage Blockers

- (none)

## Top Likely False Positives / Boilerplate Clusters

- `leak_root_58f42543bcd6` clean_intervention_pair_similarity (1500 symptoms, basis=linked_clean_intervention_pair)
- `leak_root_f2b7a2c98b1a` expected_subset_overlap (600 symptoms, basis=subset_family_overlap)
- `leak_root_77cc8c1b74c0` expected_subset_overlap (100 symptoms, basis=subset_family_overlap)
- `leak_root_d6cb356e7097` instruction_parameter_overlap (18 symptoms, basis=instruction_parameter_overlap)

## Top Manual-Review Clusters

- `leak_root_d334a1283ee6` near duplicate prompt across pilot in prompt -> Review whether this is intentional task-family reuse or a duplicate task.
- `leak_root_da29fa28d6fd` near duplicate prompt across pilot in prompt -> Review whether this is intentional task-family reuse or a duplicate task.
- `leak_root_4652ad314ca6` near duplicate prompt across pilot in prompt -> Review whether this is intentional task-family reuse or a duplicate task.
- `leak_root_c4fdadcfb25d` near duplicate prompt across pilot in prompt -> Review whether this is intentional task-family reuse or a duplicate task.
- `leak_root_6a728e541ed1` near duplicate prompt across pilot in prompt -> Review whether this is intentional task-family reuse or a duplicate task.
- `leak_root_7eb6f41f4ff6` near duplicate prompt across pilot in prompt -> Review whether this is intentional task-family reuse or a duplicate task.
- `leak_root_e889c1fd4bdb` near duplicate prompt across pilot in prompt -> Review whether this is intentional task-family reuse or a duplicate task.
- `leak_root_184684890302` near duplicate prompt across pilot in prompt -> Review whether this is intentional task-family reuse or a duplicate task.
- `leak_root_3998251704d2` near duplicate prompt across pilot in prompt -> Review whether this is intentional task-family reuse or a duplicate task.
- `leak_root_6ca078d43e7b` near duplicate prompt across pilot in prompt -> Review whether this is intentional task-family reuse or a duplicate task.
- `leak_root_be7042b73263` near duplicate prompt across pilot in prompt -> Review whether this is intentional task-family reuse or a duplicate task.
- `leak_root_c4287eaf7c65` near duplicate prompt across pilot in prompt -> Review whether this is intentional task-family reuse or a duplicate task.
- `leak_root_d4481646aafc` near duplicate prompt across pilot in prompt -> Review whether this is intentional task-family reuse or a duplicate task.
- `leak_root_da2a69f02aff` near duplicate prompt across pilot in prompt -> Review whether this is intentional task-family reuse or a duplicate task.
- `leak_root_dd41d61d1665` near duplicate prompt across pilot in prompt -> Review whether this is intentional task-family reuse or a duplicate task.
- `leak_root_f2e1df9394e0` near duplicate prompt across pilot in prompt -> Review whether this is intentional task-family reuse or a duplicate task.
- `leak_root_f42d36b45263` near duplicate prompt across pilot in prompt -> Review whether this is intentional task-family reuse or a duplicate task.
- `leak_root_1144b151af29` near duplicate prompt across pilot in prompt -> Review whether this is intentional task-family reuse or a duplicate task.
- `leak_root_26b75f3029bb` near duplicate prompt across pilot in prompt -> Review whether this is intentional task-family reuse or a duplicate task.
- `leak_root_46bc1d8acc06` near duplicate prompt across pilot in prompt -> Review whether this is intentional task-family reuse or a duplicate task.

## Root-Cause Summary

- rank 1 `leak_root_d334a1283ee6` [warning] near duplicate prompt across pilot in prompt (540 symptoms) -> Review whether this is intentional task-family reuse or a duplicate task.
- rank 2 `leak_root_da29fa28d6fd` [warning] near duplicate prompt across pilot in prompt (540 symptoms) -> Review whether this is intentional task-family reuse or a duplicate task.
- rank 3 `leak_root_4652ad314ca6` [warning] near duplicate prompt across pilot in prompt (360 symptoms) -> Review whether this is intentional task-family reuse or a duplicate task.
- rank 4 `leak_root_c4fdadcfb25d` [warning] near duplicate prompt across pilot in prompt (360 symptoms) -> Review whether this is intentional task-family reuse or a duplicate task.
- rank 5 `leak_root_6a728e541ed1` [warning] near duplicate prompt across pilot in prompt (216 symptoms) -> Review whether this is intentional task-family reuse or a duplicate task.
- rank 6 `leak_root_7eb6f41f4ff6` [warning] near duplicate prompt across pilot in prompt (216 symptoms) -> Review whether this is intentional task-family reuse or a duplicate task.
- rank 7 `leak_root_e889c1fd4bdb` [warning] near duplicate prompt across pilot in prompt (216 symptoms) -> Review whether this is intentional task-family reuse or a duplicate task.
- rank 8 `leak_root_184684890302` [warning] near duplicate prompt across pilot in prompt (108 symptoms) -> Review whether this is intentional task-family reuse or a duplicate task.
- rank 9 `leak_root_3998251704d2` [warning] near duplicate prompt across pilot in prompt (108 symptoms) -> Review whether this is intentional task-family reuse or a duplicate task.
- rank 10 `leak_root_6ca078d43e7b` [warning] near duplicate prompt across pilot in prompt (108 symptoms) -> Review whether this is intentional task-family reuse or a duplicate task.
- rank 11 `leak_root_be7042b73263` [warning] near duplicate prompt across pilot in prompt (108 symptoms) -> Review whether this is intentional task-family reuse or a duplicate task.
- rank 12 `leak_root_c4287eaf7c65` [warning] near duplicate prompt across pilot in prompt (108 symptoms) -> Review whether this is intentional task-family reuse or a duplicate task.
- rank 13 `leak_root_d4481646aafc` [warning] near duplicate prompt across pilot in prompt (108 symptoms) -> Review whether this is intentional task-family reuse or a duplicate task.
- rank 14 `leak_root_da2a69f02aff` [warning] near duplicate prompt across pilot in prompt (108 symptoms) -> Review whether this is intentional task-family reuse or a duplicate task.
- rank 15 `leak_root_dd41d61d1665` [warning] near duplicate prompt across pilot in prompt (108 symptoms) -> Review whether this is intentional task-family reuse or a duplicate task.
- rank 16 `leak_root_f2e1df9394e0` [warning] near duplicate prompt across pilot in prompt (108 symptoms) -> Review whether this is intentional task-family reuse or a duplicate task.
- rank 17 `leak_root_f42d36b45263` [warning] near duplicate prompt across pilot in prompt (108 symptoms) -> Review whether this is intentional task-family reuse or a duplicate task.
- rank 18 `leak_root_1144b151af29` [warning] near duplicate prompt across pilot in prompt (36 symptoms) -> Review whether this is intentional task-family reuse or a duplicate task.
- rank 19 `leak_root_26b75f3029bb` [warning] near duplicate prompt across pilot in prompt (36 symptoms) -> Review whether this is intentional task-family reuse or a duplicate task.
- rank 20 `leak_root_46bc1d8acc06` [warning] near duplicate prompt across pilot in prompt (36 symptoms) -> Review whether this is intentional task-family reuse or a duplicate task.

## Top Main-Benchmark Leakage Blockers

- `leak_root_d334a1283ee6` near duplicate prompt across pilot in prompt -> Review whether this is intentional task-family reuse or a duplicate task.
- `leak_root_da29fa28d6fd` near duplicate prompt across pilot in prompt -> Review whether this is intentional task-family reuse or a duplicate task.
- `leak_root_4652ad314ca6` near duplicate prompt across pilot in prompt -> Review whether this is intentional task-family reuse or a duplicate task.
- `leak_root_c4fdadcfb25d` near duplicate prompt across pilot in prompt -> Review whether this is intentional task-family reuse or a duplicate task.
- `leak_root_6a728e541ed1` near duplicate prompt across pilot in prompt -> Review whether this is intentional task-family reuse or a duplicate task.
- `leak_root_7eb6f41f4ff6` near duplicate prompt across pilot in prompt -> Review whether this is intentional task-family reuse or a duplicate task.
- `leak_root_e889c1fd4bdb` near duplicate prompt across pilot in prompt -> Review whether this is intentional task-family reuse or a duplicate task.
- `leak_root_184684890302` near duplicate prompt across pilot in prompt -> Review whether this is intentional task-family reuse or a duplicate task.
- `leak_root_3998251704d2` near duplicate prompt across pilot in prompt -> Review whether this is intentional task-family reuse or a duplicate task.
- `leak_root_6ca078d43e7b` near duplicate prompt across pilot in prompt -> Review whether this is intentional task-family reuse or a duplicate task.

## Manual Review Queue

- `leak_root_d334a1283ee6` near duplicate prompt across pilot in prompt
- `leak_root_da29fa28d6fd` near duplicate prompt across pilot in prompt
- `leak_root_4652ad314ca6` near duplicate prompt across pilot in prompt
- `leak_root_c4fdadcfb25d` near duplicate prompt across pilot in prompt
- `leak_root_6a728e541ed1` near duplicate prompt across pilot in prompt
- `leak_root_7eb6f41f4ff6` near duplicate prompt across pilot in prompt
- `leak_root_e889c1fd4bdb` near duplicate prompt across pilot in prompt
- `leak_root_184684890302` near duplicate prompt across pilot in prompt
- `leak_root_3998251704d2` near duplicate prompt across pilot in prompt
- `leak_root_6ca078d43e7b` near duplicate prompt across pilot in prompt
- `leak_root_be7042b73263` near duplicate prompt across pilot in prompt
- `leak_root_c4287eaf7c65` near duplicate prompt across pilot in prompt
- `leak_root_d4481646aafc` near duplicate prompt across pilot in prompt
- `leak_root_da2a69f02aff` near duplicate prompt across pilot in prompt
- `leak_root_dd41d61d1665` near duplicate prompt across pilot in prompt
- `leak_root_f2e1df9394e0` near duplicate prompt across pilot in prompt
- `leak_root_f42d36b45263` near duplicate prompt across pilot in prompt
- `leak_root_1144b151af29` near duplicate prompt across pilot in prompt
- `leak_root_26b75f3029bb` near duplicate prompt across pilot in prompt
- `leak_root_46bc1d8acc06` near duplicate prompt across pilot in prompt

## False-Positive Candidates

- `leak_root_58f42543bcd6` near duplicate prompt across pilot in prompt
- `leak_root_f2b7a2c98b1a` duplicate instance id across pilot / pilot_100 in instance_ids
- `leak_root_77cc8c1b74c0` duplicate task id across pilot / pilot_100 in task_ids
- `leak_root_d6cb356e7097` instruction parameter overlap in prompt

## Active Suppressions

- (none)

## Next Actions

- Fix provider-pilot split, answer leakage, and visible hidden-metadata blockers first.
- Review near-duplicate clusters before editing large batches.
- Use raw findings in JSON for traceability; do not manually triage the raw flood first.
- Suppressions are advisory metadata only; never use them to hide blocker-risk findings.

## Capped Raw Finding Examples

- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__research_assistant_easy_003.clean` `duplicate_instance_id`: scale100_v1__research_assistant_easy_003.clean appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__calendar_email_workflow_medium_008.observation_conflict::scale100_v1__calendar_email_workflow_medium_008.ambiguous_instruction` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__shopping_comparison_medium_007.tool_removal::scale100_v1__shopping_comparison_medium_007.irrelevant_tools` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__policy_compliance_easy_007.irrelevant_tools` `duplicate_instance_id`: scale100_v1__policy_compliance_easy_007.irrelevant_tools appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__finance_admin_workflow_medium_000.clean::scale100_v1__finance_admin_workflow_medium_000.tool_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__research_assistant_stress_000.observation_conflict::scale100_v1__research_assistant_stress_000.long_horizon_dependency` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__spreadsheet_qa_easy_001.observation_conflict::scale100_v1__spreadsheet_qa_easy_001.distractor_evidence` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__customer_support_workflow_medium_000` `duplicate_task_id`: scale100_v1__customer_support_workflow_medium_000 appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__policy_compliance_hard_001.tool_corruption::scale100_v1__policy_compliance_hard_001.irrelevant_tools` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__research_assistant_easy_002.observation_conflict::scale100_v1__research_assistant_easy_002.distractor_evidence` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__calendar_email_workflow_medium_008` `duplicate_task_id`: scale100_v1__calendar_email_workflow_medium_008 appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__travel_planning_hard_000.clean::scale100_v1__travel_planning_hard_000.tool_removal` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__coding_debugging_medium_005.observation_conflict::scale100_v1__coding_debugging_medium_005.distractor_evidence` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__policy_compliance_easy_005.clean::scale100_v1__policy_compliance_easy_005.tool_failure` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__shopping_comparison_medium_006.tool_removal::scale100_v1__shopping_comparison_medium_006.irrelevant_tools` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__file_qa_stress_005.memory_corruption` `duplicate_instance_id`: scale100_v1__file_qa_stress_005.memory_corruption appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__file_qa_stress_005.tool_corruption` `duplicate_instance_id`: scale100_v1__file_qa_stress_005.tool_corruption appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__shopping_comparison_medium_003.tool_corruption::scale100_v1__shopping_comparison_medium_003.irrelevant_tools` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__coding_debugging_stress_006.ambiguous_instruction::scale100_v1__coding_debugging_stress_006.distractor_evidence` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__finance_admin_workflow_easy_004.tool_failure::scale100_v1__finance_admin_workflow_easy_004.tool_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__file_qa_hard_007.memory_corruption` `duplicate_instance_id`: scale100_v1__file_qa_hard_007.memory_corruption appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__travel_planning_hard_003.tool_removal` `duplicate_instance_id`: scale100_v1__travel_planning_hard_003.tool_removal appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__shopping_comparison_medium_007.irrelevant_tools` `duplicate_instance_id`: scale100_v1__shopping_comparison_medium_007.irrelevant_tools appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__finance_admin_workflow_stress_001.memory_corruption` `duplicate_instance_id`: scale100_v1__finance_admin_workflow_stress_001.memory_corruption appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__data_cleaning_workflow_stress_007.clean::scale100_v1__data_cleaning_workflow_stress_007.premature_success_signal` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__spreadsheet_qa_easy_004.observation_conflict` `duplicate_instance_id`: scale100_v1__spreadsheet_qa_easy_004.observation_conflict appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__policy_compliance_stress_004.tool_removal::scale100_v1__policy_compliance_stress_004.tool_failure` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__data_cleaning_workflow_hard_001.premature_success_signal::scale100_v1__data_cleaning_workflow_hard_001.distractor_evidence` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__data_cleaning_workflow_medium_003.long_horizon_dependency` `duplicate_instance_id`: scale100_v1__data_cleaning_workflow_medium_003.long_horizon_dependency appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__file_qa_hard_003.tool_failure` `duplicate_instance_id`: scale100_v1__file_qa_hard_003.tool_failure appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__operations_planning_stress_001.tool_corruption` `duplicate_instance_id`: scale100_v1__operations_planning_stress_001.tool_corruption appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__policy_compliance_stress_004.tool_failure::scale100_v1__policy_compliance_stress_004.memory_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__research_assistant_easy_003.long_horizon_dependency::scale100_v1__research_assistant_easy_003.premature_success_signal` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__customer_support_workflow_medium_000.clean::scale100_v1__customer_support_workflow_medium_000.long_horizon_dependency` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__spreadsheet_qa_easy_001.ambiguous_instruction::scale100_v1__spreadsheet_qa_easy_001.premature_success_signal` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__spreadsheet_qa_easy_004.ambiguous_instruction` `duplicate_instance_id`: scale100_v1__spreadsheet_qa_easy_004.ambiguous_instruction appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__data_cleaning_workflow_hard_001.ambiguous_instruction::scale100_v1__data_cleaning_workflow_hard_001.distractor_evidence` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__research_assistant_stress_000.clean::scale100_v1__research_assistant_stress_000.ambiguous_instruction` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__coding_debugging_hard_004.ambiguous_instruction::scale100_v1__coding_debugging_hard_004.long_horizon_dependency` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__file_qa_medium_008.clean::scale100_v1__file_qa_medium_008.irrelevant_tools` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__file_qa_hard_000.tool_removal::scale100_v1__file_qa_hard_000.irrelevant_tools` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__data_cleaning_workflow_medium_003.clean` `duplicate_instance_id`: scale100_v1__data_cleaning_workflow_medium_003.clean appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__shopping_comparison_medium_007.memory_corruption` `duplicate_instance_id`: scale100_v1__shopping_comparison_medium_007.memory_corruption appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__travel_planning_hard_003.irrelevant_tools` `duplicate_instance_id`: scale100_v1__travel_planning_hard_003.irrelevant_tools appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__travel_planning_hard_001.tool_removal::scale100_v1__travel_planning_hard_001.tool_failure` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__operations_planning_stress_003.clean::scale100_v1__operations_planning_stress_003.tool_removal` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__file_qa_medium_001.tool_removal::scale100_v1__file_qa_medium_001.irrelevant_tools` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__policy_compliance_stress_004` `duplicate_task_id`: scale100_v1__policy_compliance_stress_004 appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__coding_debugging_hard_007.clean::scale100_v1__coding_debugging_hard_007.long_horizon_dependency` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__coding_debugging_stress_000.clean::scale100_v1__coding_debugging_stress_000.premature_success_signal` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__travel_planning_hard_001` `duplicate_task_id`: scale100_v1__travel_planning_hard_001 appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__calendar_email_workflow_easy_005.distractor_evidence` `duplicate_instance_id`: scale100_v1__calendar_email_workflow_easy_005.distractor_evidence appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__spreadsheet_qa_stress_006` `duplicate_task_id`: scale100_v1__spreadsheet_qa_stress_006 appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__research_assistant_hard_004.distractor_evidence` `duplicate_instance_id`: scale100_v1__research_assistant_hard_004.distractor_evidence appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__customer_support_workflow_easy_001.long_horizon_dependency` `duplicate_instance_id`: scale100_v1__customer_support_workflow_easy_001.long_horizon_dependency appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__calendar_email_workflow_easy_005.long_horizon_dependency::scale100_v1__calendar_email_workflow_easy_005.premature_success_signal` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__spreadsheet_qa_easy_001` `duplicate_task_id`: scale100_v1__spreadsheet_qa_easy_001 appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__file_qa_medium_006.tool_corruption` `duplicate_instance_id`: scale100_v1__file_qa_medium_006.tool_corruption appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__customer_support_workflow_medium_003.observation_conflict::scale100_v1__customer_support_workflow_medium_003.distractor_evidence` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__file_qa_stress_005.tool_failure` `duplicate_instance_id`: scale100_v1__file_qa_stress_005.tool_failure appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__finance_admin_workflow_stress_003.tool_removal::scale100_v1__finance_admin_workflow_stress_003.tool_failure` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__file_qa_medium_008.tool_corruption::scale100_v1__file_qa_medium_008.irrelevant_tools` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__policy_compliance_medium_000.tool_corruption::scale100_v1__policy_compliance_medium_000.memory_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__travel_planning_easy_007.clean::scale100_v1__travel_planning_easy_007.memory_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__customer_support_workflow_medium_003.observation_conflict::scale100_v1__customer_support_workflow_medium_003.ambiguous_instruction` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__travel_planning_hard_000.irrelevant_tools` `duplicate_instance_id`: scale100_v1__travel_planning_hard_000.irrelevant_tools appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__spreadsheet_qa_stress_000.observation_conflict::scale100_v1__spreadsheet_qa_stress_000.distractor_evidence` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__finance_admin_workflow_stress_003.tool_removal::scale100_v1__finance_admin_workflow_stress_003.memory_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__calendar_email_workflow_easy_001.long_horizon_dependency::scale100_v1__calendar_email_workflow_easy_001.premature_success_signal` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__calendar_email_workflow_medium_002.long_horizon_dependency::scale100_v1__calendar_email_workflow_medium_002.distractor_evidence` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__operations_planning_stress_003.tool_removal::scale100_v1__operations_planning_stress_003.memory_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__travel_planning_hard_001.irrelevant_tools::scale100_v1__travel_planning_hard_001.memory_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__operations_planning_hard_006.tool_corruption::scale100_v1__operations_planning_hard_006.irrelevant_tools` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__spreadsheet_qa_stress_008.observation_conflict::scale100_v1__spreadsheet_qa_stress_008.premature_success_signal` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__operations_planning_stress_001.tool_removal` `duplicate_instance_id`: scale100_v1__operations_planning_stress_001.tool_removal appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__spreadsheet_qa_stress_006.ambiguous_instruction::scale100_v1__spreadsheet_qa_stress_006.long_horizon_dependency` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__policy_compliance_medium_002.tool_failure::scale100_v1__policy_compliance_medium_002.tool_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__data_cleaning_workflow_stress_007.ambiguous_instruction::scale100_v1__data_cleaning_workflow_stress_007.long_horizon_dependency` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__file_qa_medium_004.tool_corruption::scale100_v1__file_qa_medium_004.irrelevant_tools` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__coding_debugging_easy_002.ambiguous_instruction::scale100_v1__coding_debugging_easy_002.long_horizon_dependency` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__operations_planning_stress_001.tool_corruption::scale100_v1__operations_planning_stress_001.irrelevant_tools` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__coding_debugging_stress_006.observation_conflict` `duplicate_instance_id`: scale100_v1__coding_debugging_stress_006.observation_conflict appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__shopping_comparison_medium_001.tool_corruption::scale100_v1__shopping_comparison_medium_001.irrelevant_tools` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__travel_planning_medium_005.tool_failure::scale100_v1__travel_planning_medium_005.tool_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__operations_planning_easy_000.tool_removal::scale100_v1__operations_planning_easy_000.irrelevant_tools` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__calendar_email_workflow_hard_006.ambiguous_instruction` `duplicate_instance_id`: scale100_v1__calendar_email_workflow_hard_006.ambiguous_instruction appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__policy_compliance_stress_006.tool_removal::scale100_v1__policy_compliance_stress_006.irrelevant_tools` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__file_qa_medium_008` `duplicate_task_id`: scale100_v1__file_qa_medium_008 appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__operations_planning_easy_007.tool_removal::scale100_v1__operations_planning_easy_007.memory_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__data_cleaning_workflow_stress_002.clean::scale100_v1__data_cleaning_workflow_stress_002.long_horizon_dependency` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__customer_support_workflow_medium_004.ambiguous_instruction::scale100_v1__customer_support_workflow_medium_004.premature_success_signal` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__shopping_comparison_medium_003.irrelevant_tools::scale100_v1__shopping_comparison_medium_003.memory_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__shopping_comparison_medium_005.tool_removal::scale100_v1__shopping_comparison_medium_005.memory_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__policy_compliance_stress_006` `duplicate_task_id`: scale100_v1__policy_compliance_stress_006 appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__coding_debugging_stress_001.ambiguous_instruction::scale100_v1__coding_debugging_stress_001.distractor_evidence` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__calendar_email_workflow_medium_000.long_horizon_dependency` `duplicate_instance_id`: scale100_v1__calendar_email_workflow_medium_000.long_horizon_dependency appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__spreadsheet_qa_easy_005.long_horizon_dependency` `duplicate_instance_id`: scale100_v1__spreadsheet_qa_easy_005.long_horizon_dependency appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__coding_debugging_stress_001.long_horizon_dependency::scale100_v1__coding_debugging_stress_001.distractor_evidence` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__spreadsheet_qa_stress_000.long_horizon_dependency::scale100_v1__spreadsheet_qa_stress_000.premature_success_signal` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/scale100_confirmatory_v1_candidate` `scale100_v1__data_cleaning_workflow_hard_001.clean` `duplicate_instance_id`: scale100_v1__data_cleaning_workflow_hard_001.clean appears in multiple splits inside a declared subset family: pilot, pilot_100.
- Raw finding examples capped at 100; full raw findings are in JSON only.
