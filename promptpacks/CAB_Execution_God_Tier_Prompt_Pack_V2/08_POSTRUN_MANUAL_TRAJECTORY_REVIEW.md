# Prompt 08 — Postrun Manual Trajectory Review

You are working in `/Users/saketmaganti/Projects/causal-agent-bench`.

You are Codex acting as a trajectory-review coordinator and evidence boundary auditor.

## Task

Prepare and, if human-reviewed rows already exist, analyze manual trajectory review for every provider trajectory.

## Absolute rules

- Do not fabricate manual judgments.
- Do not use AI/proxy judgments as human judgments.
- Do not call providers.
- Do not run local LLMs.
- Do not rerun benchmark.
- Do not promote claims until review/audit pass.

## Actions

1. Create a trajectory review template populated with trajectory metadata but blank human judgment columns:

- `reports/COMPACT20_3MODEL_TRAJECTORY_REVIEW_TODO.csv`

Columns:

- run_dir,
- trajectory_id,
- model_id,
- task_id,
- condition,
- intervention_family,
- expected_answer,
- model_final_answer,
- deterministic_scorer_result,
- human_reviewer_id,
- manual_human_judgment,
- scorer_agrees_with_manual,
- issue_category,
- severity,
- notes,
- recommended_action.

2. If `reports/COMPACT20_3MODEL_TRAJECTORY_REVIEW_COMPLETED.csv` exists, analyze it.

3. Create:

- `reports/COMPACT20_3MODEL_TRAJECTORY_REVIEW_STATUS.md`
- `reports/COMPACT20_3MODEL_TRAJECTORY_REVIEW_ANALYSIS.md` if completed.

## Manual issue categories

- scorer_correct
- model_actually_wrong
- model_actually_correct
- paraphrase_mismatch
- numeric_tolerance_issue
- date_or_time_format_issue
- list_or_set_mismatch
- abstention_correctness_issue
- false_positive_substring_match
- false_negative_strict_match
- gold_policy_issue
- unclear_manual_review_needed

## Final response format

# Compact-20 Manual Trajectory Review Report

## 1. Executive Summary
## 2. Trajectory Count
## 3. Review TODO Created
## 4. Completed Review Status
## 5. Issues Found
## 6. Scorer Risk
## 7. Claim Impact
## 8. Commands Run
## 9. Commands Not Run
## 10. Next Best Action

Final verdict:

- `TRAJECTORY_REVIEW_TODO_READY`
- `TRAJECTORY_REVIEW_COMPLETE_READY_FOR_SCORER_SANITY`
- `TRAJECTORY_REVIEW_BLOCKED_NO_RUN`
