# Human Review Instructions for Saket / Reviewers

Use this file outside Codex to complete the required human review.

## Goal

CAB cannot move from scaffold to evidence until real humans review Compact-20 task quality, gold policy, and intervention isolation.

## Files to fill

Inside:

`data/human_validation/compact20_real_review/`

Fill:

1. `task_clarity_review.csv`
2. `gold_policy_review.csv`
3. `intervention_isolation_review.csv`

Do not fill proxy files. Do not label AI-generated review as human.

## Reviewer identity

Each row must include reviewer_id, review_date, task_id, clear pass/fail fields, and notes.

Reviewer IDs can be simple: `saket`, `reviewer_2`, `reviewer_3`.

## What to judge

### Task clarity

Ask whether the task is understandable, the success criterion is clear, and the required answer is unambiguous.

### Gold policy

Ask whether the expected answer is correct, whether answer should change under intervention, whether abstention is acceptable, and whether scorer likely matches valid answers.

### Intervention isolation

Ask whether the intervention preserves the original goal, changes only the intended factor, avoids making the task impossible, and avoids extra confounds.

## Recommended labels

Use simple values: `pass`, `fail`, `unclear`, `exclude`, `needs_adjudication`.

## Minimum useful review

At least one real reviewer for every Compact-20 pair.

## Stronger review

Two reviewers per pair plus adjudication for disagreements.

## Do not do this

- Do not copy AI/proxy labels.
- Do not mark rows human-reviewed if you did not inspect them.
- Do not mark everything pass without notes.
- Do not change model outputs.
- Do not create fake timestamps.

## After review

Run the next Codex prompt:

`01_HUMAN_REVIEW_COMPLETION_DRIVER.md`

Then continue the pack.
