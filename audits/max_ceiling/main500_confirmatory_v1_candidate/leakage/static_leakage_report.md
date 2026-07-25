# Static Leakage Report

Generated: 2026-07-23T16:50:35.445965+00:00

Static leakage heuristics only; no embeddings, models, providers, or benchmark runs.

This is a static heuristic report, not empirical model evidence.

## Executive Summary

- Datasets scanned: 1
- Raw findings: 120778
- Deduplicated findings: 120318
- Root-cause clusters: 102
- Active clusters (post-suppression): 102
- Suppressed clusters (reviewed registry): 0
- Suppressed/deduplicated symptoms: 120676
- Blockers: 0
- Warnings: 111276
- Blocker clusters: 0
- False-positive candidate clusters: 5
- Needs-review clusters: 39
- Active suppression entries: 0
- Expired suppression entries: 0
- Refused suppression attempts (blocker classes): 0

## Classification Counts

- `clean_intervention_pair_similarity`: 2
- `expected_subset_overlap`: 2
- `instruction_parameter_overlap`: 1
- `needs_manual_review`: 58
- `same_family_protected_split_overlap`: 39

## Top True Leakage Blockers

- (none)

## Top Provider-Pilot Leakage Blockers

- (none)

## Top Likely False Positives / Boilerplate Clusters

- `leak_root_58f42543bcd6` clean_intervention_pair_similarity (7500 symptoms, basis=linked_clean_intervention_pair)
- `leak_root_74d5bb2a373e` clean_intervention_pair_similarity (750 symptoms, basis=linked_clean_intervention_pair)
- `leak_root_f2b7a2c98b1a` expected_subset_overlap (600 symptoms, basis=subset_family_overlap)
- `leak_root_77cc8c1b74c0` expected_subset_overlap (100 symptoms, basis=subset_family_overlap)
- `leak_root_d6cb356e7097` instruction_parameter_overlap (92 symptoms, basis=instruction_parameter_overlap)

## Top Manual-Review Clusters

- `leak_root_c198e8e9b960` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_73301ee7ac39` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_caca5f5e29f6` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_eb3c2a344524` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_9526337d8267` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_30373ac02387` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_73f619a2c88c` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_30592cf643e4` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_7ca10f0fa9ff` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_6191435be12d` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_e592bff2c4f1` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_0d2fe0f62b97` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_8a0964980289` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_e77c32e21abd` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_04956a54127f` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_238ea8ad5c60` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_5e567c7816ec` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_6c30b822fc91` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_6213d01c0584` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_bb4b2ba0e8ff` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.

## Root-Cause Summary

- rank 1 `leak_root_c198e8e9b960` [needs_review] near duplicate prompt across heldout / pilot in prompt (972 symptoms) -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- rank 2 `leak_root_73301ee7ac39` [needs_review] near duplicate prompt across heldout / pilot in prompt (936 symptoms) -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- rank 3 `leak_root_caca5f5e29f6` [needs_review] near duplicate prompt across heldout / pilot in prompt (864 symptoms) -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- rank 4 `leak_root_eb3c2a344524` [needs_review] near duplicate prompt across heldout / pilot in prompt (864 symptoms) -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- rank 5 `leak_root_9526337d8267` [needs_review] near duplicate prompt across heldout / pilot in prompt (792 symptoms) -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- rank 6 `leak_root_30373ac02387` [needs_review] near duplicate prompt across heldout / pilot in prompt (648 symptoms) -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- rank 7 `leak_root_73f619a2c88c` [needs_review] near duplicate prompt across heldout / pilot in prompt (648 symptoms) -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- rank 8 `leak_root_30592cf643e4` [needs_review] near duplicate prompt across heldout / pilot in prompt (612 symptoms) -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- rank 9 `leak_root_7ca10f0fa9ff` [needs_review] near duplicate prompt across heldout / pilot in prompt (576 symptoms) -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- rank 10 `leak_root_6191435be12d` [needs_review] near duplicate prompt across heldout / pilot in prompt (540 symptoms) -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- rank 11 `leak_root_e592bff2c4f1` [needs_review] near duplicate prompt across heldout / pilot in prompt (540 symptoms) -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- rank 12 `leak_root_0d2fe0f62b97` [needs_review] near duplicate prompt across heldout / pilot in prompt (504 symptoms) -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- rank 13 `leak_root_8a0964980289` [needs_review] near duplicate prompt across heldout / pilot in prompt (504 symptoms) -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- rank 14 `leak_root_e77c32e21abd` [needs_review] near duplicate prompt across heldout / pilot in prompt (504 symptoms) -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- rank 15 `leak_root_04956a54127f` [needs_review] near duplicate prompt across heldout / pilot in prompt (468 symptoms) -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- rank 16 `leak_root_238ea8ad5c60` [needs_review] near duplicate prompt across heldout / pilot in prompt (468 symptoms) -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- rank 17 `leak_root_5e567c7816ec` [needs_review] near duplicate prompt across heldout / pilot in prompt (468 symptoms) -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- rank 18 `leak_root_6c30b822fc91` [needs_review] near duplicate prompt across heldout / pilot in prompt (468 symptoms) -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- rank 19 `leak_root_6213d01c0584` [needs_review] near duplicate prompt across heldout / pilot in prompt (432 symptoms) -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- rank 20 `leak_root_bb4b2ba0e8ff` [needs_review] near duplicate prompt across heldout / pilot in prompt (432 symptoms) -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.

## Top Main-Benchmark Leakage Blockers

- `leak_root_c198e8e9b960` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_73301ee7ac39` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_caca5f5e29f6` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_eb3c2a344524` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_9526337d8267` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_30373ac02387` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_73f619a2c88c` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_30592cf643e4` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_7ca10f0fa9ff` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_6191435be12d` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.

## Manual Review Queue

- `leak_root_c198e8e9b960` near duplicate prompt across heldout / pilot in prompt
- `leak_root_73301ee7ac39` near duplicate prompt across heldout / pilot in prompt
- `leak_root_caca5f5e29f6` near duplicate prompt across heldout / pilot in prompt
- `leak_root_eb3c2a344524` near duplicate prompt across heldout / pilot in prompt
- `leak_root_9526337d8267` near duplicate prompt across heldout / pilot in prompt
- `leak_root_30373ac02387` near duplicate prompt across heldout / pilot in prompt
- `leak_root_73f619a2c88c` near duplicate prompt across heldout / pilot in prompt
- `leak_root_30592cf643e4` near duplicate prompt across heldout / pilot in prompt
- `leak_root_7ca10f0fa9ff` near duplicate prompt across heldout / pilot in prompt
- `leak_root_6191435be12d` near duplicate prompt across heldout / pilot in prompt
- `leak_root_e592bff2c4f1` near duplicate prompt across heldout / pilot in prompt
- `leak_root_0d2fe0f62b97` near duplicate prompt across heldout / pilot in prompt
- `leak_root_8a0964980289` near duplicate prompt across heldout / pilot in prompt
- `leak_root_e77c32e21abd` near duplicate prompt across heldout / pilot in prompt
- `leak_root_04956a54127f` near duplicate prompt across heldout / pilot in prompt
- `leak_root_238ea8ad5c60` near duplicate prompt across heldout / pilot in prompt
- `leak_root_5e567c7816ec` near duplicate prompt across heldout / pilot in prompt
- `leak_root_6c30b822fc91` near duplicate prompt across heldout / pilot in prompt
- `leak_root_6213d01c0584` near duplicate prompt across heldout / pilot in prompt
- `leak_root_bb4b2ba0e8ff` near duplicate prompt across heldout / pilot in prompt

## False-Positive Candidates

- `leak_root_58f42543bcd6` near duplicate prompt across pilot in prompt
- `leak_root_74d5bb2a373e` near duplicate prompt across heldout in prompt
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

- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__spreadsheet_qa_medium_011.ambiguous_instruction::main500_v1__spreadsheet_qa_medium_011.distractor_evidence` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__policy_compliance_easy_028.tool_removal::main500_v1__policy_compliance_easy_028.memory_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__data_cleaning_workflow_medium_021.clean::main500_v1__data_cleaning_workflow_medium_021.ambiguous_instruction` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__operations_planning_medium_013.tool_failure::main500_v1__operations_planning_medium_013.irrelevant_tools` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__travel_planning_medium_008.tool_corruption::main500_v1__travel_planning_medium_008.memory_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__travel_planning_stress_007.tool_removal::main500_v1__travel_planning_stress_007.tool_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__policy_compliance_hard_025.clean::main500_v1__policy_compliance_hard_025.memory_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__shopping_comparison_hard_042.irrelevant_tools::main500_v1__shopping_comparison_hard_042.memory_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__spreadsheet_qa_easy_026.ambiguous_instruction::main500_v1__spreadsheet_qa_easy_026.premature_success_signal` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__file_qa_easy_038.tool_removal::main500_v1__file_qa_easy_038.irrelevant_tools` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__operations_planning_medium_045.tool_removal::main500_v1__operations_planning_medium_045.tool_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__file_qa_easy_038.tool_corruption::main500_v1__file_qa_easy_038.memory_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__spreadsheet_qa_stress_041.clean::main500_v1__spreadsheet_qa_stress_041.distractor_evidence` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__calendar_email_workflow_hard_021.observation_conflict::main500_v1__calendar_email_workflow_hard_021.ambiguous_instruction` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__finance_admin_workflow_easy_041.tool_corruption::main500_v1__finance_admin_workflow_easy_041.memory_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__finance_admin_workflow_medium_017.tool_removal::main500_v1__finance_admin_workflow_medium_017.tool_failure` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__travel_planning_medium_000` `duplicate_task_id`: main500_v1__travel_planning_medium_000 appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__file_qa_hard_039.clean::main500_v1__file_qa_hard_039.tool_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__customer_support_workflow_medium_032.ambiguous_instruction::main500_v1__customer_support_workflow_medium_032.long_horizon_dependency` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__spreadsheet_qa_medium_008.clean::main500_v1__spreadsheet_qa_medium_008.ambiguous_instruction` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__customer_support_workflow_hard_026.long_horizon_dependency::main500_v1__customer_support_workflow_hard_026.premature_success_signal` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__data_cleaning_workflow_stress_010.ambiguous_instruction::main500_v1__data_cleaning_workflow_stress_010.long_horizon_dependency` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__research_assistant_easy_039.observation_conflict::main500_v1__research_assistant_easy_039.ambiguous_instruction` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__operations_planning_medium_029.clean::main500_v1__operations_planning_medium_029.tool_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__spreadsheet_qa_medium_006.ambiguous_instruction` `duplicate_instance_id`: main500_v1__spreadsheet_qa_medium_006.ambiguous_instruction appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__travel_planning_stress_014.tool_removal::main500_v1__travel_planning_stress_014.tool_failure` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__coding_debugging_hard_040.clean::main500_v1__coding_debugging_hard_040.premature_success_signal` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__operations_planning_stress_031.clean::main500_v1__operations_planning_stress_031.tool_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__policy_compliance_easy_042.tool_corruption::main500_v1__policy_compliance_easy_042.memory_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__file_qa_medium_008.memory_corruption` `duplicate_instance_id`: main500_v1__file_qa_medium_008.memory_corruption appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__file_qa_medium_040.tool_corruption::main500_v1__file_qa_medium_040.irrelevant_tools` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__customer_support_workflow_easy_041.clean::main500_v1__customer_support_workflow_easy_041.observation_conflict` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__coding_debugging_hard_040.ambiguous_instruction::main500_v1__coding_debugging_hard_040.premature_success_signal` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__research_assistant_medium_035.clean::main500_v1__research_assistant_medium_035.distractor_evidence` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__shopping_comparison_hard_024.tool_corruption::main500_v1__shopping_comparison_hard_024.memory_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__travel_planning_stress_025.tool_removal::main500_v1__travel_planning_stress_025.tool_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__research_assistant_hard_002.ambiguous_instruction::main500_v1__research_assistant_hard_002.premature_success_signal` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__coding_debugging_medium_025.clean::main500_v1__coding_debugging_medium_025.observation_conflict` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__finance_admin_workflow_easy_021.clean::main500_v1__finance_admin_workflow_easy_021.tool_removal` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__spreadsheet_qa_medium_022.clean::main500_v1__spreadsheet_qa_medium_022.premature_success_signal` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__calendar_email_workflow_easy_007.distractor_evidence` `duplicate_instance_id`: main500_v1__calendar_email_workflow_easy_007.distractor_evidence appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__file_qa_easy_024.clean::main500_v1__file_qa_easy_024.tool_failure` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__spreadsheet_qa_hard_038.clean::main500_v1__spreadsheet_qa_hard_038.ambiguous_instruction` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__policy_compliance_stress_000` `duplicate_task_id`: main500_v1__policy_compliance_stress_000 appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__coding_debugging_stress_026.ambiguous_instruction::main500_v1__coding_debugging_stress_026.long_horizon_dependency` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__data_cleaning_workflow_stress_032.observation_conflict::main500_v1__data_cleaning_workflow_stress_032.long_horizon_dependency` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__finance_admin_workflow_easy_007.tool_failure::main500_v1__finance_admin_workflow_easy_007.memory_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__file_qa_stress_011.tool_failure::main500_v1__file_qa_stress_011.irrelevant_tools` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__operations_planning_easy_027.irrelevant_tools::main500_v1__operations_planning_easy_027.memory_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__spreadsheet_qa_easy_019.clean::main500_v1__spreadsheet_qa_easy_019.distractor_evidence` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__file_qa_hard_044.tool_removal::main500_v1__file_qa_hard_044.tool_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__finance_admin_workflow_stress_038.clean::main500_v1__finance_admin_workflow_stress_038.tool_failure` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__finance_admin_workflow_stress_000.tool_failure::main500_v1__finance_admin_workflow_stress_000.memory_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__coding_debugging_easy_042.long_horizon_dependency::main500_v1__coding_debugging_easy_042.distractor_evidence` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__spreadsheet_qa_easy_020.observation_conflict::main500_v1__spreadsheet_qa_easy_020.long_horizon_dependency` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__travel_planning_stress_025.tool_removal::main500_v1__travel_planning_stress_025.tool_failure` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__shopping_comparison_medium_010.tool_removal::main500_v1__shopping_comparison_medium_010.irrelevant_tools` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__coding_debugging_easy_002.clean::main500_v1__coding_debugging_easy_002.premature_success_signal` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__coding_debugging_hard_036.ambiguous_instruction::main500_v1__coding_debugging_hard_036.long_horizon_dependency` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__operations_planning_stress_009.tool_corruption::main500_v1__operations_planning_stress_009.irrelevant_tools` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__spreadsheet_qa_hard_001.clean::main500_v1__spreadsheet_qa_hard_001.distractor_evidence` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__travel_planning_stress_027.irrelevant_tools::main500_v1__travel_planning_stress_027.memory_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__file_qa_easy_023.clean::main500_v1__file_qa_easy_023.memory_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__travel_planning_medium_039.tool_corruption::main500_v1__travel_planning_medium_039.irrelevant_tools` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__spreadsheet_qa_hard_024.observation_conflict::main500_v1__spreadsheet_qa_hard_024.distractor_evidence` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__customer_support_workflow_hard_002.ambiguous_instruction::main500_v1__customer_support_workflow_hard_002.long_horizon_dependency` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__shopping_comparison_hard_024.clean::main500_v1__shopping_comparison_hard_024.tool_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__research_assistant_medium_017.clean::main500_v1__research_assistant_medium_017.long_horizon_dependency` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__operations_planning_medium_030.tool_corruption::main500_v1__operations_planning_medium_030.irrelevant_tools` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__policy_compliance_hard_015.tool_failure::main500_v1__policy_compliance_hard_015.memory_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__finance_admin_workflow_stress_002.tool_removal::main500_v1__finance_admin_workflow_stress_002.irrelevant_tools` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__travel_planning_medium_039.clean::main500_v1__travel_planning_medium_039.irrelevant_tools` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__calendar_email_workflow_stress_008.observation_conflict::main500_v1__calendar_email_workflow_stress_008.long_horizon_dependency` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__calendar_email_workflow_medium_037.ambiguous_instruction::main500_v1__calendar_email_workflow_medium_037.premature_success_signal` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__coding_debugging_stress_020.observation_conflict::main500_v1__coding_debugging_stress_020.distractor_evidence` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__research_assistant_easy_001.ambiguous_instruction::main500_v1__research_assistant_easy_001.distractor_evidence` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__file_qa_hard_039.tool_failure::main500_v1__file_qa_hard_039.memory_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__data_cleaning_workflow_easy_024.ambiguous_instruction::main500_v1__data_cleaning_workflow_easy_024.long_horizon_dependency` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__data_cleaning_workflow_hard_013.clean::main500_v1__data_cleaning_workflow_hard_013.observation_conflict` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__policy_compliance_easy_042.clean::main500_v1__policy_compliance_easy_042.tool_removal` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__data_cleaning_workflow_stress_038.clean::main500_v1__data_cleaning_workflow_stress_038.distractor_evidence` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__calendar_email_workflow_hard_032.observation_conflict::main500_v1__calendar_email_workflow_hard_032.premature_success_signal` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__data_cleaning_workflow_easy_039.observation_conflict::main500_v1__data_cleaning_workflow_easy_039.ambiguous_instruction` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__file_qa_hard_032.tool_removal::main500_v1__file_qa_hard_032.tool_failure` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__data_cleaning_workflow_easy_039.clean::main500_v1__data_cleaning_workflow_easy_039.ambiguous_instruction` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__data_cleaning_workflow_medium_020.long_horizon_dependency::main500_v1__data_cleaning_workflow_medium_020.distractor_evidence` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__customer_support_workflow_stress_016.clean::main500_v1__customer_support_workflow_stress_016.long_horizon_dependency` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__shopping_comparison_stress_002.tool_failure::main500_v1__shopping_comparison_stress_002.tool_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__file_qa_medium_041.tool_removal::main500_v1__file_qa_medium_041.irrelevant_tools` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__spreadsheet_qa_stress_005.long_horizon_dependency` `duplicate_instance_id`: main500_v1__spreadsheet_qa_stress_005.long_horizon_dependency appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__calendar_email_workflow_easy_007.clean::main500_v1__calendar_email_workflow_easy_007.premature_success_signal` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__data_cleaning_workflow_stress_038.clean::main500_v1__data_cleaning_workflow_stress_038.premature_success_signal` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__policy_compliance_medium_039.clean::main500_v1__policy_compliance_medium_039.tool_removal` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__operations_planning_medium_000.clean::main500_v1__operations_planning_medium_000.tool_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__research_assistant_stress_022.ambiguous_instruction::main500_v1__research_assistant_stress_022.long_horizon_dependency` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__finance_admin_workflow_easy_037.tool_failure::main500_v1__finance_admin_workflow_easy_037.irrelevant_tools` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__operations_planning_medium_044.tool_removal::main500_v1__operations_planning_medium_044.tool_failure` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__operations_planning_medium_013.tool_failure::main500_v1__operations_planning_medium_013.tool_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__coding_debugging_easy_024.clean::main500_v1__coding_debugging_easy_024.premature_success_signal` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/main500_confirmatory_v1_candidate` `main500_v1__travel_planning_medium_020.tool_removal::main500_v1__travel_planning_medium_020.tool_failure` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- Raw finding examples capped at 100; full raw findings are in JSON only.
