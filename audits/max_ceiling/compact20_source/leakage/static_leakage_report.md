# Static Leakage Report

Generated: 2026-07-23T16:50:24.927910+00:00

Static leakage heuristics only; no embeddings, models, providers, or benchmark runs.

This is a static heuristic report, not empirical model evidence.

## Executive Summary

- Datasets scanned: 1
- Raw findings: 38878
- Deduplicated findings: 38718
- Root-cause clusters: 110
- Active clusters (post-suppression): 110
- Suppressed clusters (reviewed registry): 0
- Suppressed/deduplicated symptoms: 38768
- Blockers: 0
- Warnings: 34236
- Blocker clusters: 0
- False-positive candidate clusters: 8
- Needs-review clusters: 40
- Active suppression entries: 0
- Expired suppression entries: 0
- Refused suppression attempts (blocker classes): 0

## Classification Counts

- `clean_intervention_pair_similarity`: 3
- `expected_subset_overlap`: 4
- `instruction_parameter_overlap`: 1
- `needs_manual_review`: 62
- `same_family_protected_split_overlap`: 40

## Top True Leakage Blockers

- (none)

## Top Provider-Pilot Leakage Blockers

- (none)

## Top Likely False Positives / Boilerplate Clusters

- `leak_root_58f42543bcd6` clean_intervention_pair_similarity (2700 symptoms, basis=linked_clean_intervention_pair)
- `leak_root_74d5bb2a373e` clean_intervention_pair_similarity (750 symptoms, basis=linked_clean_intervention_pair)
- `leak_root_f2b7a2c98b1a` expected_subset_overlap (480 symptoms, basis=subset_family_overlap)
- `leak_root_2e0126635287` clean_intervention_pair_similarity (300 symptoms, basis=linked_clean_intervention_pair)
- `leak_root_2107ecd9653a` expected_subset_overlap (120 symptoms, basis=subset_family_overlap)
- `leak_root_77cc8c1b74c0` expected_subset_overlap (80 symptoms, basis=subset_family_overlap)
- `leak_root_d6cb356e7097` instruction_parameter_overlap (32 symptoms, basis=instruction_parameter_overlap)
- `leak_root_6e02ac3ee729` expected_subset_overlap (20 symptoms, basis=subset_family_overlap)

## Top Manual-Review Clusters

- `leak_root_c6e5a8fdd8a1` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_85edc49ecb36` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_a0eb6d662fa7` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_806510e72afa` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_9526337d8267` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_5d5a0bb12817` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_30592cf643e4` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_6c30b822fc91` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_ab76f0498c06` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_0873f0d969a1` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_d3a85556962c` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_5e567c7816ec` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_73f619a2c88c` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_7f6f450c6c5f` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_bb4b2ba0e8ff` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_e592bff2c4f1` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_769395dae2ca` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_04956a54127f` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_4f0346c496e3` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_6024a4927cb1` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.

## Root-Cause Summary

- rank 1 `leak_root_c6e5a8fdd8a1` [needs_review] near duplicate prompt across heldout / pilot in prompt (1008 symptoms) -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- rank 2 `leak_root_85edc49ecb36` [needs_review] near duplicate prompt across heldout / pilot in prompt (864 symptoms) -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- rank 3 `leak_root_a0eb6d662fa7` [needs_review] near duplicate prompt across heldout / pilot in prompt (720 symptoms) -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- rank 4 `leak_root_806510e72afa` [needs_review] near duplicate prompt across heldout / pilot in prompt (576 symptoms) -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- rank 5 `leak_root_9526337d8267` [needs_review] near duplicate prompt across heldout / pilot in prompt (576 symptoms) -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- rank 6 `leak_root_5d5a0bb12817` [needs_review] near duplicate prompt across heldout / pilot in prompt (540 symptoms) -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- rank 7 `leak_root_30592cf643e4` [needs_review] near duplicate prompt across heldout / pilot in prompt (432 symptoms) -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- rank 8 `leak_root_6c30b822fc91` [needs_review] near duplicate prompt across heldout / pilot in prompt (432 symptoms) -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- rank 9 `leak_root_ab76f0498c06` [needs_review] near duplicate prompt across heldout / pilot in prompt (432 symptoms) -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- rank 10 `leak_root_0873f0d969a1` [needs_review] near duplicate prompt across heldout / pilot in prompt (360 symptoms) -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- rank 11 `leak_root_d3a85556962c` [needs_review] near duplicate prompt across heldout / pilot in prompt (360 symptoms) -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- rank 12 `leak_root_5e567c7816ec` [needs_review] near duplicate prompt across heldout / pilot in prompt (324 symptoms) -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- rank 13 `leak_root_73f619a2c88c` [needs_review] near duplicate prompt across heldout / pilot in prompt (324 symptoms) -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- rank 14 `leak_root_7f6f450c6c5f` [needs_review] near duplicate prompt across heldout / pilot in prompt (324 symptoms) -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- rank 15 `leak_root_bb4b2ba0e8ff` [needs_review] near duplicate prompt across heldout / pilot in prompt (324 symptoms) -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- rank 16 `leak_root_e592bff2c4f1` [needs_review] near duplicate prompt across heldout / pilot in prompt (324 symptoms) -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- rank 17 `leak_root_769395dae2ca` [needs_review] near duplicate prompt across heldout / pilot in prompt (288 symptoms) -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- rank 18 `leak_root_04956a54127f` [needs_review] near duplicate prompt across heldout / pilot in prompt (216 symptoms) -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- rank 19 `leak_root_4f0346c496e3` [needs_review] near duplicate prompt across heldout / pilot in prompt (216 symptoms) -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- rank 20 `leak_root_6024a4927cb1` [needs_review] near duplicate prompt across heldout / pilot in prompt (216 symptoms) -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.

## Top Main-Benchmark Leakage Blockers

- `leak_root_c6e5a8fdd8a1` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_85edc49ecb36` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_a0eb6d662fa7` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_806510e72afa` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_9526337d8267` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_5d5a0bb12817` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_30592cf643e4` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_6c30b822fc91` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_ab76f0498c06` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.
- `leak_root_0873f0d969a1` near duplicate prompt across heldout / pilot in prompt -> Inspect representative pairs. If overlap is family scaffolding, document via the suppression registry. If real leakage exists across the heldout/pilot boundary within the family, move or rewrite one side before main benchmark planning.

## Manual Review Queue

- `leak_root_c6e5a8fdd8a1` near duplicate prompt across heldout / pilot in prompt
- `leak_root_85edc49ecb36` near duplicate prompt across heldout / pilot in prompt
- `leak_root_a0eb6d662fa7` near duplicate prompt across heldout / pilot in prompt
- `leak_root_806510e72afa` near duplicate prompt across heldout / pilot in prompt
- `leak_root_9526337d8267` near duplicate prompt across heldout / pilot in prompt
- `leak_root_5d5a0bb12817` near duplicate prompt across heldout / pilot in prompt
- `leak_root_30592cf643e4` near duplicate prompt across heldout / pilot in prompt
- `leak_root_6c30b822fc91` near duplicate prompt across heldout / pilot in prompt
- `leak_root_ab76f0498c06` near duplicate prompt across heldout / pilot in prompt
- `leak_root_0873f0d969a1` near duplicate prompt across heldout / pilot in prompt
- `leak_root_d3a85556962c` near duplicate prompt across heldout / pilot in prompt
- `leak_root_5e567c7816ec` near duplicate prompt across heldout / pilot in prompt
- `leak_root_73f619a2c88c` near duplicate prompt across heldout / pilot in prompt
- `leak_root_7f6f450c6c5f` near duplicate prompt across heldout / pilot in prompt
- `leak_root_bb4b2ba0e8ff` near duplicate prompt across heldout / pilot in prompt
- `leak_root_e592bff2c4f1` near duplicate prompt across heldout / pilot in prompt
- `leak_root_769395dae2ca` near duplicate prompt across heldout / pilot in prompt
- `leak_root_04956a54127f` near duplicate prompt across heldout / pilot in prompt
- `leak_root_4f0346c496e3` near duplicate prompt across heldout / pilot in prompt
- `leak_root_6024a4927cb1` near duplicate prompt across heldout / pilot in prompt

## False-Positive Candidates

- `leak_root_58f42543bcd6` near duplicate prompt across pilot in prompt
- `leak_root_74d5bb2a373e` near duplicate prompt across heldout in prompt
- `leak_root_f2b7a2c98b1a` duplicate instance id across pilot / pilot_100 in instance_ids
- `leak_root_2e0126635287` near duplicate prompt across dev in prompt
- `leak_root_2107ecd9653a` duplicate instance id across dev / pilot in instance_ids
- `leak_root_77cc8c1b74c0` duplicate task id across pilot / pilot_100 in task_ids
- `leak_root_d6cb356e7097` instruction parameter overlap in prompt
- `leak_root_6e02ac3ee729` duplicate task id across dev / pilot in task_ids

## Active Suppressions

- (none)

## Next Actions

- Fix provider-pilot split, answer leakage, and visible hidden-metadata blockers first.
- Review near-duplicate clusters before editing large batches.
- Use raw findings in JSON for traceability; do not manually triage the raw flood first.
- Suppressions are advisory metadata only; never use them to hide blocker-risk findings.

## Capped Raw Finding Examples

- `informational` `data/processed/pilot_v0_1` `coding_debugging_medium_001.tool_removal::coding_debugging_medium_001.tool_failure` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `travel_planning_easy_027.tool_removal::travel_planning_easy_027.tool_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `policy_compliance_easy_001.clean` `duplicate_instance_id`: policy_compliance_easy_001.clean appears in multiple splits inside a declared subset family: dev, pilot, pilot_100, pilot_20.
- `informational` `data/processed/pilot_v0_1` `calendar_email_workflow_easy_016.clean::calendar_email_workflow_easy_016.ambiguous_instruction` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `shopping_comparison_easy_028.long_horizon_dependency::shopping_comparison_easy_028.distractor_evidence` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `research_assistant_easy_000.clean` `duplicate_instance_id`: research_assistant_easy_000.clean appears in multiple splits inside a declared subset family: dev, pilot, pilot_100, pilot_20.
- `informational` `data/processed/pilot_v0_1` `operations_planning_stress_003.long_horizon_dependency` `duplicate_instance_id`: operations_planning_stress_003.long_horizon_dependency appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/pilot_v0_1` `travel_planning_medium_012.tool_failure::travel_planning_medium_012.irrelevant_tools` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `research_assistant_stress_008.tool_removal::research_assistant_stress_008.tool_failure` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `coding_debugging_hard_008` `duplicate_task_id`: coding_debugging_hard_008 appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/pilot_v0_1` `policy_compliance_stress_023.clean::policy_compliance_stress_023.observation_conflict` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `calendar_email_workflow_hard_013.clean::calendar_email_workflow_hard_013.premature_success_signal` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `calendar_email_workflow_stress_007.clean::calendar_email_workflow_stress_007.premature_success_signal` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `file_spreadsheet_qa_hard_029.tool_failure::file_spreadsheet_qa_hard_029.irrelevant_tools` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `file_spreadsheet_qa_stress_028.tool_removal::file_spreadsheet_qa_stress_028.tool_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `shopping_comparison_stress_025.clean::shopping_comparison_stress_025.distractor_evidence` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `policy_compliance_hard_028.long_horizon_dependency::policy_compliance_hard_028.premature_success_signal` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `research_assistant_hard_029.irrelevant_tools::research_assistant_hard_029.memory_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `operations_planning_easy_017.observation_conflict::operations_planning_easy_017.ambiguous_instruction` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `travel_planning_easy_018.clean::travel_planning_easy_018.memory_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `travel_planning_medium_004.tool_corruption` `duplicate_instance_id`: travel_planning_medium_004.tool_corruption appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/pilot_v0_1` `policy_compliance_hard_000.clean::policy_compliance_hard_000.ambiguous_instruction` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `operations_planning_hard_011.observation_conflict` `duplicate_instance_id`: operations_planning_hard_011.observation_conflict appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/pilot_v0_1` `operations_planning_stress_028.ambiguous_instruction::operations_planning_stress_028.long_horizon_dependency` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `operations_planning_hard_023.ambiguous_instruction::operations_planning_hard_023.distractor_evidence` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `calendar_email_workflow_easy_016.clean` `instruction_parameter_overlap`: Expected output token `2026-06-03` also appears in the task instruction as a declared parameter (not treated as a provider-pilot leakage blocker).
- `informational` `data/processed/pilot_v0_1` `operations_planning_stress_003.distractor_evidence` `duplicate_instance_id`: operations_planning_stress_003.distractor_evidence appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/pilot_v0_1` `operations_planning_hard_023.clean::operations_planning_hard_023.long_horizon_dependency` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `calendar_email_workflow_medium_017.observation_conflict::calendar_email_workflow_medium_017.distractor_evidence` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `policy_compliance_hard_009.distractor_evidence` `duplicate_instance_id`: policy_compliance_hard_009.distractor_evidence appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/pilot_v0_1` `shopping_comparison_medium_010.long_horizon_dependency::shopping_comparison_medium_010.premature_success_signal` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `research_assistant_easy_010.memory_corruption` `duplicate_instance_id`: research_assistant_easy_010.memory_corruption appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/pilot_v0_1` `operations_planning_hard_022.clean::operations_planning_hard_022.observation_conflict` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `file_spreadsheet_qa_easy_007.tool_failure::file_spreadsheet_qa_easy_007.irrelevant_tools` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `operations_planning_medium_024.observation_conflict::operations_planning_medium_024.premature_success_signal` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `operations_planning_medium_007.long_horizon_dependency::operations_planning_medium_007.distractor_evidence` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `travel_planning_easy_011.tool_failure::travel_planning_easy_011.irrelevant_tools` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `calendar_email_workflow_stress_006.clean::calendar_email_workflow_stress_006.observation_conflict` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `travel_planning_hard_008.tool_failure::travel_planning_hard_008.tool_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `file_spreadsheet_qa_medium_003.tool_removal::file_spreadsheet_qa_medium_003.memory_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `policy_compliance_hard_000.long_horizon_dependency::policy_compliance_hard_000.premature_success_signal` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `operations_planning_hard_013.long_horizon_dependency::operations_planning_hard_013.distractor_evidence` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `coding_debugging_hard_026.clean::coding_debugging_hard_026.irrelevant_tools` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `research_assistant_easy_009.clean::research_assistant_easy_009.tool_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `calendar_email_workflow_hard_027.observation_conflict::calendar_email_workflow_hard_027.ambiguous_instruction` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `shopping_comparison_medium_003.observation_conflict::shopping_comparison_medium_003.long_horizon_dependency` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `operations_planning_medium_007.ambiguous_instruction::operations_planning_medium_007.long_horizon_dependency` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `file_spreadsheet_qa_hard_020.tool_removal::file_spreadsheet_qa_hard_020.tool_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `operations_planning_easy_002.premature_success_signal::operations_planning_easy_002.distractor_evidence` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `file_spreadsheet_qa_easy_013.tool_failure::file_spreadsheet_qa_easy_013.irrelevant_tools` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `research_assistant_easy_010.tool_removal::research_assistant_easy_010.memory_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `policy_compliance_stress_020.long_horizon_dependency::policy_compliance_stress_020.premature_success_signal` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `calendar_email_workflow_hard_024.long_horizon_dependency::calendar_email_workflow_hard_024.premature_success_signal` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `shopping_comparison_easy_011.observation_conflict::shopping_comparison_easy_011.ambiguous_instruction` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `policy_compliance_stress_011.premature_success_signal` `duplicate_instance_id`: policy_compliance_stress_011.premature_success_signal appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/pilot_v0_1` `shopping_comparison_easy_011.clean::shopping_comparison_easy_011.ambiguous_instruction` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `calendar_email_workflow_medium_005.observation_conflict::calendar_email_workflow_medium_005.distractor_evidence` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `calendar_email_workflow_hard_004.distractor_evidence` `duplicate_instance_id`: calendar_email_workflow_hard_004.distractor_evidence appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/pilot_v0_1` `shopping_comparison_easy_011.clean::shopping_comparison_easy_011.long_horizon_dependency` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `coding_debugging_medium_019.tool_failure::coding_debugging_medium_019.irrelevant_tools` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `operations_planning_hard_016.observation_conflict::operations_planning_hard_016.premature_success_signal` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `calendar_email_workflow_easy_012.observation_conflict::calendar_email_workflow_easy_012.premature_success_signal` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `calendar_email_workflow_easy_009` `duplicate_task_id`: calendar_email_workflow_easy_009 appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/pilot_v0_1` `calendar_email_workflow_easy_020.ambiguous_instruction::calendar_email_workflow_easy_020.distractor_evidence` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `travel_planning_medium_010.tool_removal::travel_planning_medium_010.irrelevant_tools` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `shopping_comparison_easy_011.ambiguous_instruction` `duplicate_instance_id`: shopping_comparison_easy_011.ambiguous_instruction appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/pilot_v0_1` `coding_debugging_stress_010.tool_removal::coding_debugging_stress_010.irrelevant_tools` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `research_assistant_hard_003.clean::research_assistant_hard_003.tool_failure` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `operations_planning_hard_022.clean::operations_planning_hard_022.distractor_evidence` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `calendar_email_workflow_stress_029.clean` `instruction_parameter_overlap`: Expected output token `2026-06-03` also appears in the task instruction as a declared parameter (not treated as a provider-pilot leakage blocker).
- `informational` `data/processed/pilot_v0_1` `operations_planning_medium_014.observation_conflict::operations_planning_medium_014.distractor_evidence` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `shopping_comparison_easy_009.ambiguous_instruction` `duplicate_instance_id`: shopping_comparison_easy_009.ambiguous_instruction appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/pilot_v0_1` `policy_compliance_easy_019.observation_conflict::policy_compliance_easy_019.distractor_evidence` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `shopping_comparison_stress_027.observation_conflict::shopping_comparison_stress_027.ambiguous_instruction` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `travel_planning_easy_017.clean::travel_planning_easy_017.memory_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `travel_planning_stress_024.tool_removal::travel_planning_stress_024.irrelevant_tools` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `research_assistant_hard_011.clean` `duplicate_instance_id`: research_assistant_hard_011.clean appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/pilot_v0_1` `research_assistant_hard_026.tool_failure::research_assistant_hard_026.irrelevant_tools` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `travel_planning_medium_007.memory_corruption` `duplicate_instance_id`: travel_planning_medium_007.memory_corruption appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/pilot_v0_1` `shopping_comparison_easy_015.clean::shopping_comparison_easy_015.long_horizon_dependency` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `travel_planning_medium_010.tool_removal::travel_planning_medium_010.memory_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `research_assistant_easy_016.tool_corruption::research_assistant_easy_016.memory_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `policy_compliance_hard_018.clean::policy_compliance_hard_018.observation_conflict` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `coding_debugging_easy_005.tool_failure::coding_debugging_easy_005.memory_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `travel_planning_easy_003.tool_corruption` `duplicate_instance_id`: travel_planning_easy_003.tool_corruption appears in multiple splits inside a declared subset family: pilot, pilot_100.
- `informational` `data/processed/pilot_v0_1` `calendar_email_workflow_hard_022.observation_conflict::calendar_email_workflow_hard_022.long_horizon_dependency` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `coding_debugging_hard_009.clean::coding_debugging_hard_009.tool_failure` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `coding_debugging_easy_014.tool_removal::coding_debugging_easy_014.irrelevant_tools` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `policy_compliance_hard_026.long_horizon_dependency::policy_compliance_hard_026.distractor_evidence` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `shopping_comparison_stress_004.clean::shopping_comparison_stress_004.long_horizon_dependency` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `travel_planning_medium_010.clean::travel_planning_medium_010.tool_removal` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `policy_compliance_medium_012.ambiguous_instruction::policy_compliance_medium_012.premature_success_signal` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `operations_planning_easy_026.long_horizon_dependency::operations_planning_easy_026.premature_success_signal` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `policy_compliance_stress_020.long_horizon_dependency::policy_compliance_stress_020.distractor_evidence` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `policy_compliance_stress_016.clean::policy_compliance_stress_016.observation_conflict` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `travel_planning_medium_009.tool_failure::travel_planning_medium_009.irrelevant_tools` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `coding_debugging_easy_028.tool_failure::coding_debugging_easy_028.memory_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `file_spreadsheet_qa_medium_004.tool_failure::file_spreadsheet_qa_medium_004.irrelevant_tools` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `policy_compliance_easy_030.clean::policy_compliance_easy_030.ambiguous_instruction` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- `informational` `data/processed/pilot_v0_1` `travel_planning_medium_012.tool_corruption::travel_planning_medium_012.memory_corruption` `near_duplicate_prompt`: Prompt token overlap is 1.00; task-specific overlap is 1.00.
- Raw finding examples capped at 100; full raw findings are in JSON only.
