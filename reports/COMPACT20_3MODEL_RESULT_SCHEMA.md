# Compact-20 3-Model Future Result Schema

This schema describes future results only. No rows are present now.

Required fields:

- `run_id`
- `model`
- `provider`
- `task_id`
- `clean_instance_id`
- `intervention_instance_id`
- `intervention_type`
- `clean_success`
- `intervention_success`
- `paired_delta`
- `acrs`
- `confidence_interval`
- `trajectory_path`
- `scorer_issue_flags`
- `human_validation_status`
- `c10_status`
- `evidence_scope`
- `paper_asset_eligibility`
- `claim_ids_potentially_relevant`
- `post_run_audit_status`

No future row may be paper-eligible unless post-run audit, scorer sanity, human-validation requirements, and claim-ledger gates allow it.

