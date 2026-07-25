# Compact Empirical Config Guide

This directory holds compact empirical/provider-pilot configs only after the
corresponding approval exists.

## Current Status

- Tiny provider pilot: dry-run/preflight approved only.
- `configs/provider_pilot_tiny_APPROVED.yaml`: present under `docs/approvals/SELF_AUTHORIZATION_TINY_PROVIDER_PILOT.md`.
- Live provider run: not approved; `allow_paid_calls` must remain `false`.
- Compact-20/50 configs: not created because scorer sanity still requires provider outputs and post-run review.

## Config Requirements

Every compact provider config must include:

- explicit approval metadata,
- `scientific_evidence: false` until post-run audit,
- `evidence_scope: provider_pilot_debug_or_preliminary` for tiny pilot,
- budget cap,
- trajectory cap,
- provider-backed non-oracle agent only,
- no API keys in YAML,
- no local LLM requirement,
- `allow_paid_calls=false` for dry-run,
- `allow_paid_calls=true` only for approved live run.

## Compact Size Limits

- Compact-20: 20 paired intervention items plus clean matches.
- Compact-50: 50 paired intervention items plus clean matches.
- Forbidden in compact configs: `main_200`, `main_500`, broad sweeps.

## Required Predecessor Artifacts

- `reports/TINY_PROVIDER_PILOT_POSTRUN_AUDIT.md` if a tiny pilot ran.
- `reports/SCORER_SANITY_TINY_PROVIDER_PILOT.md` from real provider outputs.
- `reports/GOLD_OUTPUT_TRIAGE_COMPACT_PLAN.md` plus selected-slice triage.
- `reports/HUMAN_VALIDATION_COMPACT_STATUS.md`.
