# Future 3-Model Compact-20 Pilot Runbook, No Execution

Labels: `engineering_only`, `manual_review_pending`, `no_provider_evidence`.

## Prerequisites

1. Complete Compact-20 task and gold-policy review.
2. Complete C10 packet setup and decide whether C10 review precedes or follows provider outputs.
3. Confirm provider key availability without printing secrets.
4. Obtain explicit live-run approval.
5. Create an approved config from the template with budget and provider choices reviewed.

## API Key Handling

Keys must live in the environment only. No API keys, key-shaped placeholders, or secret fields belong in repo YAML.

## Candidate Model/Provider Options

Use placeholders until approval. The future run should compare three models/providers chosen for cost, capability diversity, and reproducibility constraints.

## Gate Sequence

1. Evidence safety check.
2. Config validation.
3. Cost estimate from static registry if available.
4. Provider preflight with `allow_paid_calls: false`.
5. Human approval to temporarily unlock the live config.
6. Execute only the approved Compact-20 run.
7. Lock `allow_paid_calls` back to false.
8. Run post-run audit, scorer sanity, and claim-ledger checks.

## Budget And Trajectory Limits

Use conservative caps. Stop on cost overrun, provider errors, malformed trajectories, scorer sanity failures, or unexpected claim promotion.

## What Not To Run

Do not run main_200, main_500, broad sweeps, local LLMs, or unapproved providers.

## Claim Restrictions

Even a successful 3-model Compact-20 supports only preliminary compact evidence after audit. It does not make NeurIPS D&B ready by itself.

