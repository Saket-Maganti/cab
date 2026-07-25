# Prompt 01 — Human Review Completion Driver

You are working in `/Users/saketmaganti/Projects/causal-agent-bench`.

You are Codex acting as a human-validation operations lead.

## Task

Drive the project through the real Compact-20 human review gate. Do not fill human annotations yourself. Your job is to inspect, validate, summarize, and produce the exact checklist for humans to complete.

## Current context

The previous autorun created blank human-review packets. C10 is blocked because real human reviews are missing. Provider execution must remain blocked until the review status is known.

## Absolute rules

- Do not fabricate human annotations.
- Do not use AI/proxy labels as human labels.
- Do not call providers.
- Do not run local LLMs.
- Do not run benchmark execution.
- Do not promote C10.
- Do not mark paper assets eligible.

## Inspect

- `data/human_validation/compact20_real_review/task_clarity_review.csv`
- `data/human_validation/compact20_real_review/gold_policy_review.csv`
- `data/human_validation/compact20_real_review/intervention_isolation_review.csv`
- `data/human_validation/compact20_real_review/adjudication_template.csv`
- `data/human_validation/compact20_real_review/reviewer_instructions.md`
- `data/compact20_reviewed/compact20_reviewed_manifest.json`
- `data/compact20_reviewed/compact20_readiness.json`
- `reports/C10_VALIDATION_BLOCKED_MISSING_HUMAN_REVIEWS.md`

## Actions

1. Count review rows in each CSV.
2. Detect whether rows are header-only, proxy-filled, partial human, or complete human.
3. Validate required columns.
4. Validate reviewer IDs are present where rows exist.
5. Validate no row is labeled `ai_proxy_review`, `synthetic_review`, or `not_human_annotation`.
6. Create:

- `reports/HUMAN_REVIEW_COMPLETION_STATUS.md`
- `reports/HUMAN_REVIEW_COMPLETION_STATUS.json`
- `data/human_validation/compact20_real_review/HUMAN_TODO_EXACT_ROWS.csv`

7. The TODO CSV must list every missing review row humans need to fill, with:

- task_id,
- clean_or_intervention,
- intervention_family,
- review_file,
- required_fields,
- reviewer_count_required,
- priority,
- notes.

## Completion thresholds

Minimum:

- all 20 task pairs have task clarity review,
- all 20 task pairs have gold policy review,
- all 20 task pairs have intervention isolation review,
- at least 1 real reviewer per row.

Stronger:

- 2 reviewers per row,
- disagreements flagged for adjudication.

## Commands allowed

Static file inspection only, plus targeted tests if existing.

## Final response format

# Human Review Completion Status

## 1. Executive Summary
## 2. Review Files Checked
## 3. Rows Present
## 4. Rows Missing
## 5. Proxy/Invalid Rows
## 6. Exact Human TODO
## 7. C10 Readiness
## 8. Provider Run Readiness
## 9. Commands Run
## 10. Next Best Action

Final verdict:

- `HUMAN_REVIEW_COMPLETE_READY_FOR_ANALYSIS`
- `HUMAN_REVIEW_PARTIAL_COMPLETE_TODO_CREATED`
- `HUMAN_REVIEW_HEADER_ONLY_TODO_CREATED`
- `HUMAN_REVIEW_INVALID_PROXY_LABELS_FOUND`
