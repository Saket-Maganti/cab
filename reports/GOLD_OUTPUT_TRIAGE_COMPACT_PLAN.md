# Gold Output Triage Compact Plan

## Current State

The latest no-run gold-output report found:

- 507 total warnings.
- 507 manual-review queue items.
- 500 answer-changing-without-gold-change warnings.
- Main-benchmark blockers remain for gold-output confidence.

No gold answers were changed in this upgrade.

## Compact Triage Scope

Before any compact 20/50-task benchmark, triage only the selected compact slice.
Do not attempt broad main_500 repair in this phase.

Priority families:

1. `tool_removal`
2. `tool_failure`
3. `memory_corruption`
4. `observation_conflict`
5. `stale_memory`
6. `premature_success_signal`

## Required Columns For Slice Triage

```csv
instance_id,base_task_id,intervention_family,current_expected_answer,should_answer_change,abstention_acceptable,limitation_statement_acceptable,multiple_acceptable_answers,human_review_required,auto_fix_allowed,review_decision,reviewer,review_date,notes
```

## Decision Rules

- Frozen data: document only; do not patch.
- Non-frozen processed data: patch only if unambiguous and covered by a targeted test.
- Ambiguous cases: exclude from compact slice or mark manual-review-needed.
- Any selected `tool_removal` item with answer-changing warning must receive explicit review before use.

## Compact Gate

The compact benchmark is not ready to run until:

- the selected 20/50 items have completed gold triage,
- scorer sanity is completed on real provider outputs, and
- approval exists for provider calls.
