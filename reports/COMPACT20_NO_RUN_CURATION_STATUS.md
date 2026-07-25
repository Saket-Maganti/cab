# Compact-20 No-Run Curation Status

Status: `COMPACT20_NO_RUN_CURATION_READY_FOR_MANUAL_REVIEW`

Labels: `engineering_only`, `manual_review_pending`, `no_provider_evidence`.

## What Exists

- Selection criteria: `docs/COMPACT20_SELECTION_CRITERIA.md`
- Candidate manifest: `data/human_validation/no_api_task_review/compact20_candidate_manifest.json`
- Human-readable manifest: `data/human_validation/no_api_task_review/compact20_candidate_manifest.md`
- Task review CSV: `data/human_validation/no_api_task_review/compact20_task_review.csv`
- Gold-policy review CSV: `data/human_validation/no_api_task_review/compact20_gold_policy_review.csv`
- Exclusion log: `data/human_validation/no_api_task_review/compact20_exclusion_log.csv`
- Config plan: `configs/COMPACT20_CONFIG_PLAN_NO_RUN.md`

## What Does Not Exist

- Provider outputs: `0`
- Model outputs: `0`
- Completed Compact-20 human annotations: `0`
- Paper-eligible assets: `0`
- Supported C1-C8/C10 claims: `0`

## Remaining Before Future Execution

1. Complete task review and gold-policy review for all selected candidates.
2. Exclude ambiguous or non-isolated rows.
3. Confirm no frozen-data edits are required.
4. Prepare an approved non-template config with `allow_paid_calls` changed only after explicit live approval.
5. Run provider preflight and post-run audits later.

