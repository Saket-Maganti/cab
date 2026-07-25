# No API Key Provider Pilot Blocker

Generated: 2026-06-13

Verdict: `PROVIDER_LIVE_PILOT_BLOCKED_NO_API_KEY`

## Summary

The tiny live provider pilot is blocked because `OPENAI_API_KEY` is not available in the environment. The project remains ready for dry-run/preflight work only.

No provider-backed evidence exists. No provider calls were made. No claims can be promoted from the current dry-run, static, stub, or mock artifacts.

## Current State

| Item | Status |
|---|---|
| Tiny provider dry-run | `DRYRUN_READY` |
| Live provider pilot | blocked |
| Blocking credential | `OPENAI_API_KEY` missing |
| Provider-backed scientific runs | `0` |
| Human annotations | `0` |
| Eligible paper assets | `0` |
| C1-C8 / C10 | unsupported |
| Claim promotion | forbidden |
| `allow_paid_calls` | must remain `false` |

## Evidence Boundary

Current artifacts may support only governance and engineering readiness statements:

- dry-run readiness remains valid,
- leakage/static gates can be inspected,
- cost estimates can be reviewed,
- task/gold/intervention review templates can be prepared.

Current artifacts cannot support:

- model performance claims,
- provider-backed evidence claims,
- human-validation claims,
- C1-C8 final claims,
- C10,
- NeurIPS readiness,
- definitive model rankings.

## Why The Live Pilot Is Blocked

The approved tiny config requires an OpenAI provider credential through the environment. The latest validation reported the required environment variable `OPENAI_API_KEY` is not configured.

The approved config also remains locked for no-provider work:

- `allow_paid_calls: false`
- `approval.approved_for_live_run: false`
- `scientific_evidence: false`
- `evidence_scope: provider_pilot_debug_or_preliminary`

This is the correct blocked state while no API key is available.

## If An API Key Becomes Available Later

Use `docs/FUTURE_PROVIDER_API_KEY_CHECKLIST.md`. In short:

1. Keep the API key in the shell environment only.
2. Verify key presence without printing the key value.
3. Re-run evidence safety, config validation, plan, cost estimate, provider preflight, and dry-run.
4. Confirm estimated cost remains below USD 5.00.
5. Set `allow_paid_calls=true` and `approval.approved_for_live_run=true` only at the final live-run moment.
6. Run only the tiny approved provider config.
7. Immediately set `allow_paid_calls=false` when the run finishes or fails.
8. Complete post-run trajectory review and scorer sanity before using the outputs even as preliminary/debug evidence.

Do not promote C1-C8/C10 from the tiny pilot.

## Zero-Cost Alternatives

Use `experiments/NO_API_COMPACT_VALIDATION_PLAN.md` for a no-provider fallback path based on:

- dry-run outputs,
- stub/mock artifacts,
- static task and intervention inspection,
- gold-policy review,
- high-risk intervention queue triage,
- scorer fixture tests,
- no-API manual task review templates.

All zero-cost fallback outputs must be labeled:

- `engineering_only`
- `no_provider_evidence`
- `not_scientific_model_performance`

## Commands Allowed In This Blocked State

```bash
python3 scripts/check_evidence_safety.py
PYTHONPATH=src python3 -m causal_agent_bench all-no-run-reports --output-dir /tmp/cab_no_api_fallback
PYTHONPATH=src python3 -m causal_agent_bench neurips-submission-gate --output-dir /tmp/cab_no_api_fallback/neurips_submission_gate
PYTHONPATH=src python3 -m causal_agent_bench validity-scorecard --output-dir /tmp/cab_no_api_fallback/validity_scorecard
```

## Commands Still Forbidden

- provider live runs,
- `main_200`,
- `main_500`,
- broad sweeps,
- local LLMs outside documented safe stub/mock paths,
- claim promotion,
- paper asset eligibility marking,
- storing API keys in repo files.

Final status: `NO_API_PROVIDER_BLOCKER_DOCUMENTED`
