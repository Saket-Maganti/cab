# Ablations V3 No-Execution Readme

These configs are templates or local stubs only. Do not run them without the relevant provider, human-review, C10, budget, and evidence gates.

Required safety fields for future executable configs:

- `allow_paid_calls: false` until explicit approval,
- `approved_for_live_run: false` until explicit approval,
- `scientific_claims_allowed: false` until post-run audit,
- `paper_asset_eligibility: false` until paper gate,
- env-only credentials, never keys in config.
