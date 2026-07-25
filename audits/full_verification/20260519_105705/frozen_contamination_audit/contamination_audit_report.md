# Contamination and Memorization Audit

Passed: `True`
Dataset version: `pilot_v0.1`
Benchmark dir: `data/frozen/pilot_v0.1`
Splits path: `data/frozen/pilot_v0.1/splits.json`
Audited at: `2026-05-19T05:34:44.608775+00:00`

## Summary

- Base tasks: 250
- Instances: 1500
- Errors: 0
- Warnings: 102

## Contamination risks

- Public task instructions and tool schemas may appear in pretraining corpora.
- Models may memorize template variants seen during method development on pilot splits.
- Repeated submissions on the held-out test split enable adaptive overfitting.
- Oracle or hidden-metadata exposure inflates scores without realistic agent skill.
- Near-duplicate instructions across splits reduce effective held-out size.

## Mitigations

- Use disjoint release splits (`release_disjoint_v1`) and report the eval split explicitly.
- Assign per-task template fingerprints and audit cross-split template collisions.
- Embed canary strings on hidden splits and scan public splits for leakage.
- Run prompt-leakage checks before agent evaluation exports.
- Exclude oracle agents from leaderboard rows; label engineering-only runs.
- Version datasets with `dataset_hash` and freeze manifests before headline claims.

## Remaining limitations

- Synthetic tasks are not a proxy for live web or enterprise tool environments.
- Canary and near-duplicate checks are heuristic; they do not prove absence of memorization.
- Tool descriptions are shared across tasks and may still correlate with public documentation.
- Human validation is still required before strong robustness claims.

## Fingerprinting

- Unique template fingerprints: 250
- Cross-split template collisions: 0

## Canaries

- Expected hidden canaries: 75
- Stored on tasks: 0
- Missing assignments: 50
- Leaks into public splits: 0

## Near duplicates

- Threshold (Jaccard): 0.85
- Cross-split pairs flagged: 100

## Prompt leakage

- Instances checked: 1500
- Findings: 1
- Truncated findings: 0

## Findings

| Severity | Category | Task / Instance | Detail |
|---|---|---|---|
| warning | canary_missing | `hidden_splits` | 75 hidden tasks lack metadata.contamination_canary |
| warning | near_duplicate_instruction | `travel_planning_medium_000|travel_planning_medium_004` | Instruction Jaccard 0.917 between dev and validation |
| warning | near_duplicate_instruction | `travel_planning_medium_000|travel_planning_medium_006` | Instruction Jaccard 0.917 between dev and test |
| warning | near_duplicate_instruction | `travel_planning_medium_000|travel_planning_medium_007` | Instruction Jaccard 0.917 between dev and test |
| warning | near_duplicate_instruction | `travel_planning_medium_000|travel_planning_medium_009` | Instruction Jaccard 0.917 between dev and pilot |
| warning | near_duplicate_instruction | `travel_planning_medium_000|travel_planning_medium_010` | Instruction Jaccard 0.917 between dev and pilot |
| warning | near_duplicate_instruction | `travel_planning_medium_000|travel_planning_medium_012` | Instruction Jaccard 0.917 between dev and pilot |
| warning | near_duplicate_instruction | `travel_planning_medium_000|travel_planning_medium_015` | Instruction Jaccard 0.917 between dev and pilot |
| warning | near_duplicate_instruction | `travel_planning_medium_000|travel_planning_medium_021` | Instruction Jaccard 0.917 between dev and pilot |
| warning | near_duplicate_instruction | `travel_planning_medium_000|travel_planning_medium_022` | Instruction Jaccard 0.917 between dev and pilot |
| warning | near_duplicate_instruction | `travel_planning_medium_000|travel_planning_medium_029` | Instruction Jaccard 0.917 between dev and heldout_templates |
| warning | near_duplicate_instruction | `calendar_email_workflow_easy_000|calendar_email_workflow_easy_009` | Instruction Jaccard 0.920 between dev and pilot |
| warning | near_duplicate_instruction | `calendar_email_workflow_easy_000|calendar_email_workflow_easy_012` | Instruction Jaccard 0.920 between dev and pilot |
| warning | near_duplicate_instruction | `calendar_email_workflow_easy_000|calendar_email_workflow_easy_015` | Instruction Jaccard 0.920 between dev and pilot |
| warning | near_duplicate_instruction | `calendar_email_workflow_easy_000|calendar_email_workflow_easy_016` | Instruction Jaccard 0.920 between dev and pilot |
| warning | near_duplicate_instruction | `calendar_email_workflow_easy_000|calendar_email_workflow_easy_020` | Instruction Jaccard 0.920 between dev and pilot |
| warning | near_duplicate_instruction | `calendar_email_workflow_easy_000|calendar_email_workflow_easy_021` | Instruction Jaccard 0.920 between dev and pilot |
| warning | near_duplicate_instruction | `file_spreadsheet_qa_medium_000|file_spreadsheet_qa_medium_003` | Instruction Jaccard 0.913 between dev and validation |
| warning | near_duplicate_instruction | `file_spreadsheet_qa_medium_000|file_spreadsheet_qa_medium_004` | Instruction Jaccard 0.913 between dev and validation |
| warning | near_duplicate_instruction | `file_spreadsheet_qa_medium_000|file_spreadsheet_qa_medium_016` | Instruction Jaccard 0.913 between dev and pilot |
| warning | near_duplicate_instruction | `file_spreadsheet_qa_medium_000|file_spreadsheet_qa_medium_018` | Instruction Jaccard 0.913 between dev and pilot |
| warning | near_duplicate_instruction | `file_spreadsheet_qa_medium_000|file_spreadsheet_qa_medium_019` | Instruction Jaccard 0.913 between dev and pilot |
| warning | near_duplicate_instruction | `file_spreadsheet_qa_medium_000|file_spreadsheet_qa_medium_027` | Instruction Jaccard 0.913 between dev and heldout_templates |
| warning | near_duplicate_instruction | `shopping_comparison_easy_000|shopping_comparison_easy_006` | Instruction Jaccard 0.909 between dev and test |
| warning | near_duplicate_instruction | `shopping_comparison_easy_000|shopping_comparison_easy_009` | Instruction Jaccard 0.909 between dev and pilot |
| warning | near_duplicate_instruction | `shopping_comparison_easy_000|shopping_comparison_easy_011` | Instruction Jaccard 0.909 between dev and pilot |
| warning | near_duplicate_instruction | `shopping_comparison_easy_000|shopping_comparison_easy_012` | Instruction Jaccard 0.909 between dev and pilot |
| warning | near_duplicate_instruction | `shopping_comparison_easy_000|shopping_comparison_easy_015` | Instruction Jaccard 0.909 between dev and pilot |
| warning | near_duplicate_instruction | `shopping_comparison_easy_000|shopping_comparison_easy_023` | Instruction Jaccard 0.909 between dev and pilot |
| warning | near_duplicate_instruction | `shopping_comparison_easy_000|shopping_comparison_easy_028` | Instruction Jaccard 0.909 between dev and heldout_templates |
| warning | near_duplicate_instruction | `research_assistant_easy_000|research_assistant_easy_005` | Instruction Jaccard 0.909 between dev and validation |
| warning | near_duplicate_instruction | `research_assistant_easy_000|research_assistant_easy_009` | Instruction Jaccard 0.909 between dev and pilot |
| warning | near_duplicate_instruction | `research_assistant_easy_000|research_assistant_easy_010` | Instruction Jaccard 0.909 between dev and pilot |
| warning | near_duplicate_instruction | `research_assistant_easy_000|research_assistant_easy_013` | Instruction Jaccard 0.909 between dev and pilot |
| warning | near_duplicate_instruction | `research_assistant_easy_000|research_assistant_easy_016` | Instruction Jaccard 0.909 between dev and pilot |
| warning | near_duplicate_instruction | `research_assistant_easy_000|research_assistant_easy_020` | Instruction Jaccard 0.909 between dev and pilot |
| warning | near_duplicate_instruction | `research_assistant_easy_000|research_assistant_easy_021` | Instruction Jaccard 0.909 between dev and pilot |
| warning | near_duplicate_instruction | `research_assistant_easy_000|research_assistant_easy_024` | Instruction Jaccard 0.909 between dev and pilot |
| warning | near_duplicate_instruction | `policy_compliance_hard_000|policy_compliance_hard_009` | Instruction Jaccard 0.923 between dev and pilot |
| warning | near_duplicate_instruction | `policy_compliance_hard_000|policy_compliance_hard_010` | Instruction Jaccard 0.923 between dev and pilot |
| warning | near_duplicate_instruction | `policy_compliance_hard_000|policy_compliance_hard_015` | Instruction Jaccard 0.923 between dev and pilot |
| warning | near_duplicate_instruction | `policy_compliance_hard_000|policy_compliance_hard_018` | Instruction Jaccard 0.923 between dev and pilot |
| warning | near_duplicate_instruction | `policy_compliance_hard_000|policy_compliance_hard_021` | Instruction Jaccard 0.923 between dev and pilot |
| warning | near_duplicate_instruction | `policy_compliance_hard_000|policy_compliance_hard_024` | Instruction Jaccard 0.923 between dev and pilot |
| warning | near_duplicate_instruction | `policy_compliance_hard_000|policy_compliance_hard_025` | Instruction Jaccard 0.923 between dev and heldout_templates |
| warning | near_duplicate_instruction | `policy_compliance_hard_000|policy_compliance_hard_026` | Instruction Jaccard 0.923 between dev and heldout_templates |
| warning | near_duplicate_instruction | `policy_compliance_hard_000|policy_compliance_hard_027` | Instruction Jaccard 0.923 between dev and heldout_templates |
| warning | near_duplicate_instruction | `policy_compliance_hard_000|policy_compliance_hard_028` | Instruction Jaccard 0.923 between dev and heldout_templates |
| warning | near_duplicate_instruction | `coding_debugging_stress_000|coding_debugging_stress_002` | Instruction Jaccard 0.905 between dev and validation |
| warning | near_duplicate_instruction | `coding_debugging_stress_000|coding_debugging_stress_004` | Instruction Jaccard 0.905 between dev and validation |
| warning | near_duplicate_instruction | `coding_debugging_stress_000|coding_debugging_stress_006` | Instruction Jaccard 0.905 between dev and test |
| warning | near_duplicate_instruction | `coding_debugging_stress_000|coding_debugging_stress_010` | Instruction Jaccard 0.905 between dev and pilot |
| warning | near_duplicate_instruction | `coding_debugging_stress_000|coding_debugging_stress_018` | Instruction Jaccard 0.905 between dev and pilot |
| warning | near_duplicate_instruction | `coding_debugging_stress_000|coding_debugging_stress_022` | Instruction Jaccard 0.905 between dev and pilot |
| warning | near_duplicate_instruction | `coding_debugging_stress_000|coding_debugging_stress_025` | Instruction Jaccard 0.905 between dev and heldout_templates |
| warning | near_duplicate_instruction | `operations_planning_medium_000|operations_planning_medium_007` | Instruction Jaccard 0.920 between dev and test |
| warning | near_duplicate_instruction | `operations_planning_medium_000|operations_planning_medium_014` | Instruction Jaccard 0.920 between dev and pilot |
| warning | near_duplicate_instruction | `operations_planning_medium_000|operations_planning_medium_020` | Instruction Jaccard 0.920 between dev and pilot |
| warning | near_duplicate_instruction | `operations_planning_medium_000|operations_planning_medium_021` | Instruction Jaccard 0.920 between dev and pilot |
| warning | near_duplicate_instruction | `operations_planning_medium_000|operations_planning_medium_024` | Instruction Jaccard 0.920 between dev and pilot |
| warning | near_duplicate_instruction | `operations_planning_medium_000|operations_planning_medium_029` | Instruction Jaccard 0.920 between dev and heldout_templates |
| warning | near_duplicate_instruction | `travel_planning_medium_001|travel_planning_medium_004` | Instruction Jaccard 0.917 between dev and validation |
| warning | near_duplicate_instruction | `travel_planning_medium_001|travel_planning_medium_006` | Instruction Jaccard 0.917 between dev and test |
| warning | near_duplicate_instruction | `travel_planning_medium_001|travel_planning_medium_007` | Instruction Jaccard 0.917 between dev and test |
| warning | near_duplicate_instruction | `travel_planning_medium_001|travel_planning_medium_009` | Instruction Jaccard 0.917 between dev and pilot |
| warning | near_duplicate_instruction | `travel_planning_medium_001|travel_planning_medium_010` | Instruction Jaccard 0.917 between dev and pilot |
| warning | near_duplicate_instruction | `travel_planning_medium_001|travel_planning_medium_012` | Instruction Jaccard 0.917 between dev and pilot |
| warning | near_duplicate_instruction | `travel_planning_medium_001|travel_planning_medium_015` | Instruction Jaccard 0.917 between dev and pilot |
| warning | near_duplicate_instruction | `travel_planning_medium_001|travel_planning_medium_021` | Instruction Jaccard 0.917 between dev and pilot |
| warning | near_duplicate_instruction | `travel_planning_medium_001|travel_planning_medium_022` | Instruction Jaccard 0.917 between dev and pilot |
| warning | near_duplicate_instruction | `travel_planning_medium_001|travel_planning_medium_029` | Instruction Jaccard 0.917 between dev and heldout_templates |
| warning | near_duplicate_instruction | `calendar_email_workflow_medium_001|calendar_email_workflow_medium_005` | Instruction Jaccard 0.926 between dev and validation |
| warning | near_duplicate_instruction | `calendar_email_workflow_medium_001|calendar_email_workflow_medium_011` | Instruction Jaccard 0.926 between dev and pilot |
| warning | near_duplicate_instruction | `calendar_email_workflow_medium_001|calendar_email_workflow_medium_017` | Instruction Jaccard 0.926 between dev and pilot |
| warning | near_duplicate_instruction | `calendar_email_workflow_medium_001|calendar_email_workflow_medium_019` | Instruction Jaccard 0.926 between dev and pilot |
| warning | near_duplicate_instruction | `calendar_email_workflow_medium_001|calendar_email_workflow_medium_023` | Instruction Jaccard 0.926 between dev and pilot |
| warning | near_duplicate_instruction | `calendar_email_workflow_medium_001|calendar_email_workflow_medium_025` | Instruction Jaccard 0.926 between dev and heldout_templates |
| warning | near_duplicate_instruction | `calendar_email_workflow_medium_001|calendar_email_workflow_medium_026` | Instruction Jaccard 0.926 between dev and heldout_templates |
| warning | near_duplicate_instruction | `calendar_email_workflow_medium_001|calendar_email_workflow_medium_028` | Instruction Jaccard 0.926 between dev and heldout_templates |
| warning | near_duplicate_instruction | `calendar_email_workflow_medium_001|calendar_email_workflow_medium_031` | Instruction Jaccard 0.926 between dev and heldout_templates |
| warning | near_duplicate_instruction | `file_spreadsheet_qa_medium_001|file_spreadsheet_qa_medium_003` | Instruction Jaccard 0.913 between dev and validation |
| warning | near_duplicate_instruction | `file_spreadsheet_qa_medium_001|file_spreadsheet_qa_medium_004` | Instruction Jaccard 0.913 between dev and validation |
| warning | near_duplicate_instruction | `file_spreadsheet_qa_medium_001|file_spreadsheet_qa_medium_016` | Instruction Jaccard 0.913 between dev and pilot |
| warning | near_duplicate_instruction | `file_spreadsheet_qa_medium_001|file_spreadsheet_qa_medium_018` | Instruction Jaccard 0.913 between dev and pilot |
| warning | near_duplicate_instruction | `file_spreadsheet_qa_medium_001|file_spreadsheet_qa_medium_019` | Instruction Jaccard 0.913 between dev and pilot |
| warning | near_duplicate_instruction | `file_spreadsheet_qa_medium_001|file_spreadsheet_qa_medium_027` | Instruction Jaccard 0.913 between dev and heldout_templates |
| warning | near_duplicate_instruction | `shopping_comparison_medium_001|shopping_comparison_medium_003` | Instruction Jaccard 0.917 between dev and validation |
| warning | near_duplicate_instruction | `shopping_comparison_medium_001|shopping_comparison_medium_007` | Instruction Jaccard 0.917 between dev and test |
| warning | near_duplicate_instruction | `shopping_comparison_medium_001|shopping_comparison_medium_010` | Instruction Jaccard 0.917 between dev and pilot |
| warning | near_duplicate_instruction | `shopping_comparison_medium_001|shopping_comparison_medium_013` | Instruction Jaccard 0.917 between dev and pilot |
| warning | near_duplicate_instruction | `shopping_comparison_medium_001|shopping_comparison_medium_014` | Instruction Jaccard 0.917 between dev and pilot |
| warning | near_duplicate_instruction | `shopping_comparison_medium_001|shopping_comparison_medium_016` | Instruction Jaccard 0.917 between dev and pilot |
| warning | near_duplicate_instruction | `shopping_comparison_medium_001|shopping_comparison_medium_017` | Instruction Jaccard 0.917 between dev and pilot |
| warning | near_duplicate_instruction | `shopping_comparison_medium_001|shopping_comparison_medium_018` | Instruction Jaccard 0.917 between dev and pilot |
| warning | near_duplicate_instruction | `shopping_comparison_medium_001|shopping_comparison_medium_024` | Instruction Jaccard 0.917 between dev and pilot |
| warning | near_duplicate_instruction | `shopping_comparison_medium_001|shopping_comparison_medium_026` | Instruction Jaccard 0.917 between dev and heldout_templates |
| warning | near_duplicate_instruction | `research_assistant_hard_001|research_assistant_hard_003` | Instruction Jaccard 0.926 between dev and validation |
| warning | near_duplicate_instruction | `research_assistant_hard_001|research_assistant_hard_007` | Instruction Jaccard 0.926 between dev and test |
| warning | near_duplicate_instruction | `research_assistant_hard_001|research_assistant_hard_011` | Instruction Jaccard 0.926 between dev and pilot |
| warning | near_duplicate_instruction | `research_assistant_hard_001|research_assistant_hard_012` | Instruction Jaccard 0.926 between dev and pilot |
| warning | near_duplicate_instruction | `research_assistant_hard_001|research_assistant_hard_014` | Instruction Jaccard 0.926 between dev and pilot |
| warning | intervention_expected_behavior_exposed | `llm_tool_agents` | intervention_expected_behavior is included in LLM agent task context by design; do not use for blind model ranking without scaffold ablation |
