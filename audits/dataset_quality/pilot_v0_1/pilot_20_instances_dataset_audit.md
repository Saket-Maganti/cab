# Dataset quality audit

- **Dataset:** `/Users/saketmaganti/codexprojects/causal-agent-bench/data/processed/pilot_v0_1/pilot_20_instances.jsonl`
- **Instances:** 120
- **Base tasks:** 20
- **Clean / intervention:** 20 / 100
- **Avg required tools:** 3.25
- **Avg max steps:** 5.45

## Domain distribution
- calendar_email_workflow: 18
- coding_debugging: 12
- file_spreadsheet_qa: 18
- operations_planning: 12
- policy_compliance: 12
- research_assistant: 12
- shopping_comparison: 18
- travel_planning: 18

## Intervention families
- ambiguous_instruction: 10
- clean: 20
- distractor_evidence: 10
- irrelevant_tools: 10
- long_horizon_dependency: 10
- memory_corruption: 10
- observation_conflict: 10
- premature_success_signal: 10
- tool_corruption: 10
- tool_failure: 10
- tool_removal: 10

## Warnings
- 552 near-duplicate instruction pair(s) detected.
- 120 instance(s) missing difficulty/domain metadata.
- 120 instance(s) with hidden-ground-truth exposure risk.
- none
