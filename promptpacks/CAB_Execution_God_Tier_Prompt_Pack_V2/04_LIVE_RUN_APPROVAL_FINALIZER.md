# Prompt 04 — Live Run Approval Finalizer

You are working in `/Users/saketmaganti/Projects/causal-agent-bench`.

You are Codex acting as a live provider approval auditor and config safety engineer.

## Task

Finalize approval for the first 3-model Compact-20 live run, but do not execute it.

## Absolute rules

- Do not call providers.
- Do not run benchmark execution.
- Do not set `allow_paid_calls=true`.
- Do not store API keys.
- Do not print API keys.
- Do not fabricate approval.
- Do not proceed on ambiguous approval.

## Preconditions

Proceed only if:

- C10 has passed at least `preliminary_supported_compact20_only`, or the approval explicitly accepts C10 pending status,
- locked Compact-20 slice exists,
- exact model list is chosen,
- exact budget cap is stated,
- exact trajectory cap is stated.

## Required approval document

Create or validate:

- `docs/approvals/COMPACT20_3MODEL_LIVE_APPROVAL.md`

It must include:

- authorizing person,
- exact run config path,
- exact model IDs or provider aliases,
- exact max trajectories,
- exact max provider calls,
- exact max USD budget,
- live-run approval: Yes,
- no claim promotion until audit,
- no paper eligibility until audit,
- API keys environment-only,
- date/signature.

If approval is absent or ambiguous, create:

- `reports/COMPACT20_LIVE_APPROVAL_BLOCKED.md`

and stop.

## Config creation

If approval is valid, create:

- `configs/compact20_3model_APPROVED.yaml`

from the approval-required config.

Config must include:

- locked slice path,
- model list,
- budget cap,
- trajectory cap,
- `allow_paid_calls: false`,
- `approved_for_live_run: false` until final execution,
- `scientific_claims_allowed: false`,
- `paper_asset_eligibility: false`,
- no secret fields.

## Tests/checks

- no secrets,
- approval unambiguous,
- config trajectory count <= approved cap,
- budget <= approved budget,
- no paid calls enabled,
- evidence safety passes.

## Final response format

# Compact-20 Live Approval Finalizer Report

## 1. Executive Summary
## 2. Approval Document
## 3. Locked Slice
## 4. Model List
## 5. Budget and Trajectory Cap
## 6. Approved Config
## 7. Safety Checks
## 8. Commands Run
## 9. Commands Not Run
## 10. Next Best Action

Final verdict:

- `LIVE_APPROVAL_VALID_CONFIG_READY_PREFLIGHT`
- `LIVE_APPROVAL_BLOCKED_MISSING_OR_AMBIGUOUS`
- `LIVE_APPROVAL_BLOCKED_C10_OR_SLICE`
- `LIVE_APPROVAL_BLOCKED_CONFIG_SAFETY`
