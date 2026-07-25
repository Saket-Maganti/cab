# Static Leakage Report

Generated: 2026-07-23T16:50:22.324635+00:00

Static leakage heuristics only; no embeddings, models, providers, or benchmark runs.

This is a static heuristic report, not empirical model evidence.

## Executive Summary

- Datasets scanned: 1
- Raw findings: 4278
- Deduplicated findings: 4053
- Root-cause clusters: 41
- Active clusters (post-suppression): 41
- Suppressed clusters (reviewed registry): 0
- Suppressed/deduplicated symptoms: 4237
- Blockers: 0
- Warnings: 2304
- Blocker clusters: 0
- False-positive candidate clusters: 5
- Needs-review clusters: 9
- Active suppression entries: 0
- Expired suppression entries: 0
- Refused suppression attempts (blocker classes): 0

## Classification Counts

- `clean_intervention_pair_similarity`: 2
- `expected_subset_overlap`: 2
- `instruction_parameter_overlap`: 1
- `needs_manual_review`: 27
- `same_family_protected_split_overlap`: 9

## Top True Leakage Blockers

- (none)

## Top Provider-Pilot Leakage Blockers

- (none)

## Top Likely False Positives / Boilerplate Clusters

- `leak_root_58f42543bcd6` clean_intervention_pair_similarity (1080 symptoms, basis=linked_clean_intervention_pair)
- `leak_root_f2b7a2c98b1a` expected_subset_overlap (432 symptoms, basis=subset_family_overlap)
- `leak_root_74d5bb2a373e` clean_intervention_pair_similarity (120 symptoms, basis=linked_clean_intervention_pair)
- `leak_root_77cc8c1b74c0` expected_subset_overlap (72 symptoms, basis=subset_family_overlap)
- `leak_root_d6cb356e7097` instruction_parameter_overlap (45 symptoms, basis=instruction_parameter_overlap)

## Top Manual-Review Clusters

- `leak_root_40fefd80d7c2` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_e942372b806e` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_23030c6ed93e` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_7ae0d5dfe7cf` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_3fbcc1b7a83a` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_87d7f3789360` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_ba27bb4562f8` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_c96c2c8778fb` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_ed5653721af7` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_169948be24ff` near duplicate prompt across pilot in prompt -> Review whether this is intentional task-family reuse or a duplicate task.
- `leak_root_9dcb7f752e43` near duplicate prompt across pilot in prompt -> Review whether this is intentional task-family reuse or a duplicate task.
- `leak_root_5cffb89f2db4` near duplicate prompt across pilot in prompt -> Review whether this is intentional task-family reuse or a duplicate task.
- `leak_root_8dcfce7a7be2` near duplicate prompt across pilot in prompt -> Review whether this is intentional task-family reuse or a duplicate task.
- `leak_root_93bd6921804c` near duplicate prompt across pilot in prompt -> Review whether this is intentional task-family reuse or a duplicate task.
- `leak_root_b9e1ea6cb4cb` near duplicate prompt across pilot in prompt -> Review whether this is intentional task-family reuse or a duplicate task.
- `leak_root_083f1de86c66` near duplicate prompt across pilot in prompt -> Review whether this is intentional task-family reuse or a duplicate task.
- `leak_root_371aa501d5b2` near duplicate prompt across pilot in prompt -> Review whether this is intentional task-family reuse or a duplicate task.
- `leak_root_41bb8b11947a` near duplicate prompt across pilot in prompt -> Review whether this is intentional task-family reuse or a duplicate task.
- `leak_root_50db44b91327` near duplicate prompt across pilot in prompt -> Review whether this is intentional task-family reuse or a duplicate task.
- `leak_root_fb1b8f301862` near duplicate prompt across pilot in prompt -> Review whether this is intentional task-family reuse or a duplicate task.

## Root-Cause Summary

- rank 1 `leak_root_40fefd80d7c2` [needs_review] near duplicate prompt across heldout / pilot in prompt (144 symptoms) -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- rank 2 `leak_root_e942372b806e` [needs_review] near duplicate prompt across heldout / pilot in prompt (108 symptoms) -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- rank 3 `leak_root_23030c6ed93e` [needs_review] near duplicate prompt across heldout / pilot in prompt (72 symptoms) -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- rank 4 `leak_root_7ae0d5dfe7cf` [needs_review] near duplicate prompt across heldout / pilot in prompt (72 symptoms) -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- rank 5 `leak_root_3fbcc1b7a83a` [needs_review] near duplicate prompt across heldout / pilot in prompt (36 symptoms) -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- rank 6 `leak_root_87d7f3789360` [needs_review] near duplicate prompt across heldout / pilot in prompt (36 symptoms) -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- rank 7 `leak_root_ba27bb4562f8` [needs_review] near duplicate prompt across heldout / pilot in prompt (36 symptoms) -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- rank 8 `leak_root_c96c2c8778fb` [needs_review] near duplicate prompt across heldout / pilot in prompt (36 symptoms) -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- rank 9 `leak_root_ed5653721af7` [needs_review] near duplicate prompt across heldout / pilot in prompt (36 symptoms) -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- rank 10 `leak_root_169948be24ff` [warning] near duplicate prompt across pilot in prompt (216 symptoms) -> Review whether this is intentional task-family reuse or a duplicate task.
- rank 11 `leak_root_9dcb7f752e43` [warning] near duplicate prompt across pilot in prompt (144 symptoms) -> Review whether this is intentional task-family reuse or a duplicate task.
- rank 12 `leak_root_5cffb89f2db4` [warning] near duplicate prompt across pilot in prompt (108 symptoms) -> Review whether this is intentional task-family reuse or a duplicate task.
- rank 13 `leak_root_8dcfce7a7be2` [warning] near duplicate prompt across pilot in prompt (108 symptoms) -> Review whether this is intentional task-family reuse or a duplicate task.
- rank 14 `leak_root_93bd6921804c` [warning] near duplicate prompt across pilot in prompt (108 symptoms) -> Review whether this is intentional task-family reuse or a duplicate task.
- rank 15 `leak_root_b9e1ea6cb4cb` [warning] near duplicate prompt across pilot in prompt (108 symptoms) -> Review whether this is intentional task-family reuse or a duplicate task.
- rank 16 `leak_root_083f1de86c66` [warning] near duplicate prompt across pilot in prompt (72 symptoms) -> Review whether this is intentional task-family reuse or a duplicate task.
- rank 17 `leak_root_371aa501d5b2` [warning] near duplicate prompt across pilot in prompt (72 symptoms) -> Review whether this is intentional task-family reuse or a duplicate task.
- rank 18 `leak_root_41bb8b11947a` [warning] near duplicate prompt across pilot in prompt (72 symptoms) -> Review whether this is intentional task-family reuse or a duplicate task.
- rank 19 `leak_root_50db44b91327` [warning] near duplicate prompt across pilot in prompt (72 symptoms) -> Review whether this is intentional task-family reuse or a duplicate task.
- rank 20 `leak_root_fb1b8f301862` [warning] near duplicate prompt across pilot in prompt (72 symptoms) -> Review whether this is intentional task-family reuse or a duplicate task.

## Top Main-Benchmark Leakage Blockers

- `leak_root_40fefd80d7c2` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_e942372b806e` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_23030c6ed93e` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_7ae0d5dfe7cf` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_3fbcc1b7a83a` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_87d7f3789360` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_ba27bb4562f8` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_c96c2c8778fb` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_ed5653721af7` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_169948be24ff` near duplicate prompt across pilot in prompt -> Review whether this is intentional task-family reuse or a duplicate task.

## Manual Review Queue

- `leak_root_40fefd80d7c2` near duplicate prompt across heldout / pilot in prompt
- `leak_root_e942372b806e` near duplicate prompt across heldout / pilot in prompt
- `leak_root_23030c6ed93e` near duplicate prompt across heldout / pilot in prompt
- `leak_root_7ae0d5dfe7cf` near duplicate prompt across heldout / pilot in prompt
- `leak_root_3fbcc1b7a83a` near duplicate prompt across heldout / pilot in prompt
- `leak_root_87d7f3789360` near duplicate prompt across heldout / pilot in prompt
- `leak_root_ba27bb4562f8` near duplicate prompt across heldout / pilot in prompt
- `leak_root_c96c2c8778fb` near duplicate prompt across heldout / pilot in prompt
- `leak_root_ed5653721af7` near duplicate prompt across heldout / pilot in prompt
- `leak_root_169948be24ff` near duplicate prompt across pilot in prompt
- `leak_root_9dcb7f752e43` near duplicate prompt across pilot in prompt
- `leak_root_5cffb89f2db4` near duplicate prompt across pilot in prompt
- `leak_root_8dcfce7a7be2` near duplicate prompt across pilot in prompt
- `leak_root_93bd6921804c` near duplicate prompt across pilot in prompt
- `leak_root_b9e1ea6cb4cb` near duplicate prompt across pilot in prompt
- `leak_root_083f1de86c66` near duplicate prompt across pilot in prompt
- `leak_root_371aa501d5b2` near duplicate prompt across pilot in prompt
- `leak_root_41bb8b11947a` near duplicate prompt across pilot in prompt
- `leak_root_50db44b91327` near duplicate prompt across pilot in prompt
- `leak_root_fb1b8f301862` near duplicate prompt across pilot in prompt

## False-Positive Candidates

- `leak_root_58f42543bcd6` near duplicate prompt across pilot in prompt
- `leak_root_f2b7a2c98b1a` duplicate instance id across pilot / pilot_100 in instance_ids
- `leak_root_74d5bb2a373e` near duplicate prompt across heldout in prompt
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

- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_policy_document_hard_002.premature_success_signal::naturalistic_v1__natural_mock_policy_document_hard_002.distractor_evidence` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_product_database_easy_009.ambiguous_instruction::naturalistic_v1__natural_mock_product_database_easy_009.premature_success_signal` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_incident_postmortem_medium_007.distractor_evidence` `duplicate_instance_id`: naturalistic_v1__natural_mock_incident_postmortem_medium_007.distractor_evidence appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_product_database_medium_001.ambiguous_instruction::naturalistic_v1__natural_mock_product_database_medium_001.long_horizon_dependency` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_email_thread_easy_007.tool_corruption::naturalistic_v1__natural_mock_email_thread_easy_007.irrelevant_tools` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_spreadsheet_ops_easy_007.tool_failure::naturalistic_v1__natural_mock_spreadsheet_ops_easy_007.memory_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_spreadsheet_ops_easy_007.tool_removal::naturalistic_v1__natural_mock_spreadsheet_ops_easy_007.tool_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_incident_postmortem_medium_002.ambiguous_instruction` `duplicate_instance_id`: naturalistic_v1__natural_mock_incident_postmortem_medium_002.ambiguous_instruction appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_calendar_scheduling_medium_004.observation_conflict::naturalistic_v1__natural_mock_calendar_scheduling_medium_004.long_horizon_dependency` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_customer_escalation_stress_009.tool_removal::naturalistic_v1__natural_mock_customer_escalation_stress_009.tool_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_policy_document_easy_000.ambiguous_instruction::naturalistic_v1__natural_mock_policy_document_easy_000.long_horizon_dependency` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_policy_document_stress_007.observation_conflict::naturalistic_v1__natural_mock_policy_document_stress_007.ambiguous_instruction` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_bug_report_medium_005.tool_removal::naturalistic_v1__natural_mock_bug_report_medium_005.tool_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_bug_report_easy_001.tool_failure` `duplicate_instance_id`: naturalistic_v1__natural_mock_bug_report_easy_001.tool_failure appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_customer_escalation_hard_007.clean` `duplicate_instance_id`: naturalistic_v1__natural_mock_customer_escalation_hard_007.clean appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_spreadsheet_ops_easy_007.irrelevant_tools` `duplicate_instance_id`: naturalistic_v1__natural_mock_spreadsheet_ops_easy_007.irrelevant_tools appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_product_database_easy_008.long_horizon_dependency` `duplicate_instance_id`: naturalistic_v1__natural_mock_product_database_easy_008.long_horizon_dependency appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_customer_escalation_hard_007.clean::naturalistic_v1__natural_mock_customer_escalation_hard_007.tool_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_email_thread_medium_000.tool_corruption::naturalistic_v1__natural_mock_email_thread_medium_000.memory_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_policy_document_hard_008.ambiguous_instruction::naturalistic_v1__natural_mock_policy_document_hard_008.premature_success_signal` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_spreadsheet_ops_medium_002.tool_failure::naturalistic_v1__natural_mock_spreadsheet_ops_medium_002.memory_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_calendar_scheduling_hard_009.long_horizon_dependency::naturalistic_v1__natural_mock_calendar_scheduling_hard_009.premature_success_signal` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_product_database_stress_002.ambiguous_instruction` `duplicate_instance_id`: naturalistic_v1__natural_mock_product_database_stress_002.ambiguous_instruction appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_policy_document_stress_005.long_horizon_dependency` `duplicate_instance_id`: naturalistic_v1__natural_mock_policy_document_stress_005.long_horizon_dependency appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_bug_report_easy_001.tool_failure::naturalistic_v1__natural_mock_bug_report_easy_001.tool_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_customer_escalation_stress_005.tool_removal::naturalistic_v1__natural_mock_customer_escalation_stress_005.memory_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_email_thread_hard_005.tool_removal::naturalistic_v1__natural_mock_email_thread_hard_005.tool_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_incident_postmortem_hard_009.clean::naturalistic_v1__natural_mock_incident_postmortem_hard_009.distractor_evidence` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_incident_postmortem_medium_002.observation_conflict` `duplicate_instance_id`: naturalistic_v1__natural_mock_incident_postmortem_medium_002.observation_conflict appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_spreadsheet_ops_medium_006.clean::naturalistic_v1__natural_mock_spreadsheet_ops_medium_006.irrelevant_tools` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_bug_report_easy_001.tool_corruption` `duplicate_instance_id`: naturalistic_v1__natural_mock_bug_report_easy_001.tool_corruption appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_incident_postmortem_stress_004.observation_conflict::naturalistic_v1__natural_mock_incident_postmortem_stress_004.long_horizon_dependency` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_customer_escalation_hard_006.irrelevant_tools` `duplicate_instance_id`: naturalistic_v1__natural_mock_customer_escalation_hard_006.irrelevant_tools appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_policy_document_hard_001.clean::naturalistic_v1__natural_mock_policy_document_hard_001.observation_conflict` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_customer_escalation_stress_005.tool_failure::naturalistic_v1__natural_mock_customer_escalation_stress_005.irrelevant_tools` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_calendar_scheduling_medium_001.observation_conflict::naturalistic_v1__natural_mock_calendar_scheduling_medium_001.distractor_evidence` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_email_thread_stress_004.tool_removal` `duplicate_instance_id`: naturalistic_v1__natural_mock_email_thread_stress_004.tool_removal appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_email_thread_stress_006.tool_corruption` `duplicate_instance_id`: naturalistic_v1__natural_mock_email_thread_stress_006.tool_corruption appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_incident_postmortem_stress_005.long_horizon_dependency::naturalistic_v1__natural_mock_incident_postmortem_stress_005.distractor_evidence` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_calendar_scheduling_medium_008.ambiguous_instruction` `duplicate_instance_id`: naturalistic_v1__natural_mock_calendar_scheduling_medium_008.ambiguous_instruction appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_calendar_scheduling_medium_007.observation_conflict::naturalistic_v1__natural_mock_calendar_scheduling_medium_007.premature_success_signal` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_bug_report_easy_001.tool_failure::naturalistic_v1__natural_mock_bug_report_easy_001.memory_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_calendar_scheduling_stress_003.ambiguous_instruction::naturalistic_v1__natural_mock_calendar_scheduling_stress_003.long_horizon_dependency` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_bug_report_medium_008.tool_corruption::naturalistic_v1__natural_mock_bug_report_medium_008.memory_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_customer_escalation_medium_008.tool_corruption::naturalistic_v1__natural_mock_customer_escalation_medium_008.memory_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_calendar_scheduling_medium_000.clean` `instruction_parameter_overlap`: Expected output token `2026-07-14` also appears in the task instruction as a declared parameter (not treated as a provider-pilot leakage blocker).
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_policy_document_hard_006.observation_conflict::naturalistic_v1__natural_mock_policy_document_hard_006.distractor_evidence` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_bug_report_stress_007.clean::naturalistic_v1__natural_mock_bug_report_stress_007.memory_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_email_thread_easy_003.memory_corruption` `duplicate_instance_id`: naturalistic_v1__natural_mock_email_thread_easy_003.memory_corruption appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_policy_document_stress_005.clean::naturalistic_v1__natural_mock_policy_document_stress_005.distractor_evidence` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_spreadsheet_ops_stress_004.clean::naturalistic_v1__natural_mock_spreadsheet_ops_stress_004.memory_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_policy_document_easy_003.long_horizon_dependency::naturalistic_v1__natural_mock_policy_document_easy_003.premature_success_signal` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_calendar_scheduling_medium_000.observation_conflict::naturalistic_v1__natural_mock_calendar_scheduling_medium_000.long_horizon_dependency` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_spreadsheet_ops_hard_000.tool_removal::naturalistic_v1__natural_mock_spreadsheet_ops_hard_000.tool_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_incident_postmortem_hard_001.premature_success_signal` `duplicate_instance_id`: naturalistic_v1__natural_mock_incident_postmortem_hard_001.premature_success_signal appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_product_database_easy_003` `duplicate_task_id`: naturalistic_v1__natural_mock_product_database_easy_003 appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_bug_report_easy_003.memory_corruption` `duplicate_instance_id`: naturalistic_v1__natural_mock_bug_report_easy_003.memory_corruption appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_bug_report_medium_008.clean::naturalistic_v1__natural_mock_bug_report_medium_008.tool_removal` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_incident_postmortem_easy_006.ambiguous_instruction::naturalistic_v1__natural_mock_incident_postmortem_easy_006.premature_success_signal` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_incident_postmortem_hard_009.clean::naturalistic_v1__natural_mock_incident_postmortem_hard_009.premature_success_signal` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_calendar_scheduling_stress_003.clean` `instruction_parameter_overlap`: Expected output token `2026-07-14` also appears in the task instruction as a declared parameter (not treated as a provider-pilot leakage blocker).
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_incident_postmortem_stress_004.clean::naturalistic_v1__natural_mock_incident_postmortem_stress_004.observation_conflict` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_spreadsheet_ops_easy_003.tool_removal` `duplicate_instance_id`: naturalistic_v1__natural_mock_spreadsheet_ops_easy_003.tool_removal appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_email_thread_medium_009.clean::naturalistic_v1__natural_mock_email_thread_medium_009.irrelevant_tools` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_customer_escalation_easy_001.tool_removal` `duplicate_instance_id`: naturalistic_v1__natural_mock_customer_escalation_easy_001.tool_removal appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_product_database_easy_007.observation_conflict::naturalistic_v1__natural_mock_product_database_easy_007.premature_success_signal` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_email_thread_medium_001.tool_failure::naturalistic_v1__natural_mock_email_thread_medium_001.tool_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_incident_postmortem_stress_005.clean::naturalistic_v1__natural_mock_incident_postmortem_stress_005.observation_conflict` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_spreadsheet_ops_medium_006.tool_corruption::naturalistic_v1__natural_mock_spreadsheet_ops_medium_006.irrelevant_tools` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_bug_report_medium_005.tool_corruption::naturalistic_v1__natural_mock_bug_report_medium_005.memory_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_policy_document_easy_000.long_horizon_dependency` `duplicate_instance_id`: naturalistic_v1__natural_mock_policy_document_easy_000.long_horizon_dependency appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_bug_report_stress_002` `duplicate_task_id`: naturalistic_v1__natural_mock_bug_report_stress_002 appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_customer_escalation_stress_005.tool_failure::naturalistic_v1__natural_mock_customer_escalation_stress_005.memory_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_bug_report_hard_009.tool_corruption::naturalistic_v1__natural_mock_bug_report_hard_009.irrelevant_tools` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_calendar_scheduling_hard_002.observation_conflict::naturalistic_v1__natural_mock_calendar_scheduling_hard_002.distractor_evidence` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_product_database_easy_006.long_horizon_dependency` `duplicate_instance_id`: naturalistic_v1__natural_mock_product_database_easy_006.long_horizon_dependency appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_bug_report_easy_003` `duplicate_task_id`: naturalistic_v1__natural_mock_bug_report_easy_003 appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_customer_escalation_medium_004.clean::naturalistic_v1__natural_mock_customer_escalation_medium_004.memory_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_incident_postmortem_stress_004.clean::naturalistic_v1__natural_mock_incident_postmortem_stress_004.premature_success_signal` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_spreadsheet_ops_stress_001.clean::naturalistic_v1__natural_mock_spreadsheet_ops_stress_001.irrelevant_tools` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_email_thread_hard_005.irrelevant_tools::naturalistic_v1__natural_mock_email_thread_hard_005.memory_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_spreadsheet_ops_medium_006.clean::naturalistic_v1__natural_mock_spreadsheet_ops_medium_006.memory_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_incident_postmortem_stress_008.ambiguous_instruction` `duplicate_instance_id`: naturalistic_v1__natural_mock_incident_postmortem_stress_008.ambiguous_instruction appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_email_thread_easy_007.tool_failure` `duplicate_instance_id`: naturalistic_v1__natural_mock_email_thread_easy_007.tool_failure appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_product_database_easy_003.clean::naturalistic_v1__natural_mock_product_database_easy_003.observation_conflict` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_email_thread_hard_002.tool_failure::naturalistic_v1__natural_mock_email_thread_hard_002.tool_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_customer_escalation_hard_003.irrelevant_tools` `duplicate_instance_id`: naturalistic_v1__natural_mock_customer_escalation_hard_003.irrelevant_tools appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_spreadsheet_ops_hard_008.irrelevant_tools::naturalistic_v1__natural_mock_spreadsheet_ops_hard_008.memory_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_incident_postmortem_hard_009.ambiguous_instruction::naturalistic_v1__natural_mock_incident_postmortem_hard_009.long_horizon_dependency` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_policy_document_hard_002.observation_conflict` `duplicate_instance_id`: naturalistic_v1__natural_mock_policy_document_hard_002.observation_conflict appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_spreadsheet_ops_stress_001.tool_failure::naturalistic_v1__natural_mock_spreadsheet_ops_stress_001.irrelevant_tools` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_bug_report_stress_000.tool_failure::naturalistic_v1__natural_mock_bug_report_stress_000.irrelevant_tools` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_email_thread_hard_002.tool_removal` `duplicate_instance_id`: naturalistic_v1__natural_mock_email_thread_hard_002.tool_removal appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_incident_postmortem_stress_008.observation_conflict::naturalistic_v1__natural_mock_incident_postmortem_stress_008.distractor_evidence` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_product_database_easy_003.observation_conflict` `duplicate_instance_id`: naturalistic_v1__natural_mock_product_database_easy_003.observation_conflict appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_calendar_scheduling_hard_009.ambiguous_instruction::naturalistic_v1__natural_mock_calendar_scheduling_hard_009.premature_success_signal` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_product_database_easy_006.distractor_evidence` `duplicate_instance_id`: naturalistic_v1__natural_mock_product_database_easy_006.distractor_evidence appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_email_thread_hard_008.irrelevant_tools::naturalistic_v1__natural_mock_email_thread_hard_008.memory_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_product_database_easy_009.long_horizon_dependency::naturalistic_v1__natural_mock_product_database_easy_009.distractor_evidence` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/naturalistic_transfer_v1_candidate` `naturalistic_v1__natural_mock_calendar_scheduling_medium_008.ambiguous_instruction::naturalistic_v1__natural_mock_calendar_scheduling_medium_008.long_horizon_dependency` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- Raw finding examples capped at 100; full raw findings are in JSON only.
