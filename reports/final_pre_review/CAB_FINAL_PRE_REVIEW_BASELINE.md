# CAB Final Pre-Review Baseline

The audit began from upstream `main` at `715d981cf68eb2741dd6e05b097b08445f87accf`, with zero
ahead/behind divergence. Pre-existing user-owned modifications to status,
audit, environment, and paper-eligibility artifacts and untracked prompt packs
were recorded and excluded from task commits.

The inherited state was `CAB_PRE_RUN_SCIENTIFIC_HARDENING_COMPLETE`, with
`HUMAN_VALIDATION_REQUIRED`, `LIVE_EVIDENCE_REQUIRED`,
`CAB_LEVEL5_COMPLETE=false`, and all nine genuine-evidence counters at zero.

Residual defects were substantive: reviewer evidence was declared rather than
fully inspectable, the packet exposed gold and scorer material in one stage,
recovery used bare tool names, reachability was static only, runners trusted an
approved-looking path, model count inflated effective sample size, and the
the prior near-certain Scale power value lacked a defensible hierarchical estimand.
