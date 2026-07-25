# Prompt 05 — Compact-20 3-Model Strict Preflight

You are working in `/Users/saketmaganti/Projects/causal-agent-bench`.

You are Codex acting as a pre-live execution gatekeeper.

## Task

Run strict preflight for the approved 3-model Compact-20 provider pilot. Do not execute live providers.

## Absolute rules

- Do not call providers.
- Do not run `causal_agent_bench run`.
- Do not run local LLMs.
- Do not set `allow_paid_calls=true`.
- Do not print API keys.
- Do not store credentials.
- Do not promote claims.

## Preconditions

- `configs/compact20_3model_APPROVED.yaml` exists.
- `docs/approvals/COMPACT20_3MODEL_LIVE_APPROVAL.md` exists and is unambiguous.
- `allow_paid_calls=false`.
- locked Compact-20 slice exists.
- no severe C10 blocker.

## Checks

1. Evidence safety.
2. Config validation.
3. Plan-run.
4. Estimate-run-cost.
5. Dry-run/preflight.
6. Secret scan.
7. Environment credential presence check without printing value.

Credential check must report only:

- `OPENAI_API_KEY_PRESENT=true/false`
- other provider env present true/false

Never print values.

## Allowed commands

```bash
python3 scripts/check_evidence_safety.py

PYTHONPATH=src python3 -m causal_agent_bench validate-config --config configs/compact20_3model_APPROVED.yaml

PYTHONPATH=src python3 -m causal_agent_bench plan-run --config configs/compact20_3model_APPROVED.yaml

PYTHONPATH=src python3 -m causal_agent_bench estimate-run-cost --config configs/compact20_3model_APPROVED.yaml --output-dir /tmp/cab_compact20_3model_cost

PYTHONPATH=src python3 -m causal_agent_bench dry-run --config configs/compact20_3model_APPROVED.yaml --output-dir /tmp/cab_compact20_3model_dryrun
```

If any command would make provider calls, do not run it.

## Create

- `reports/COMPACT20_3MODEL_STRICT_PREFLIGHT.md`
- `reports/COMPACT20_3MODEL_PREFLIGHT_COST.json`
- `reports/COMPACT20_3MODEL_PREFLIGHT_GATE.json`

## Final response format

# Compact-20 3-Model Strict Preflight Report

## 1. Executive Summary
## 2. Approval Check
## 3. Config Check
## 4. Credential Presence
## 5. Cost Estimate
## 6. Dry-Run Status
## 7. Evidence Safety
## 8. Blockers
## 9. Commands Run
## 10. Commands Not Run
## 11. Next Best Action

Final verdict:

- `PREFLIGHT_READY_FOR_SINGLE_LIVE_RUN`
- `PREFLIGHT_BLOCKED_MISSING_CREDENTIALS`
- `PREFLIGHT_BLOCKED_COST_OR_CONFIG`
- `PREFLIGHT_BLOCKED_APPROVAL_OR_SLICE`
