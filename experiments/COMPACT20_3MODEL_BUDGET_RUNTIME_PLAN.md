# Compact-20 3-Model Budget And Runtime Plan

Labels: `engineering_only`, `manual_review_pending`, `no_provider_evidence`.

## Scope

- 3 models
- 20 paired items
- clean plus intervention condition per item
- possible call multiplier from retries, tools, and scorer checks

## Cost Planning

Use ranges until approved providers and pricing registry entries are selected. Do not invent exact costs. A future plan should provide low/high estimates, maximum spend, stop conditions, and approval thresholds.

## Runtime Planning

Runtime depends on provider latency, tool trajectory length, retries, and post-run audit. Plan for staged execution with a tiny smoke subset before the full approved Compact-20.

## Stop Conditions

- budget cap reached,
- malformed trajectories,
- provider or rate-limit errors,
- scorer sanity failure,
- unexpected data leakage or gold-policy issue,
- any attempt to promote claims automatically.

