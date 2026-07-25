# Provider Pilot Preparation Status

**Generated:** 2026-06-12 (static/no-run + dry-run readiness)  
**Scope:** Preparation only — no provider execution, no claim promotion.

## Current state

| Item | Status |
|---|---|
| Provider pilot dry-run/preflight | **Ready** (`configs/provider_pilot_tiny_APPROVED.yaml`) |
| Provider pilot live execution | **Blocked** (`approved_for_live_run: false`; `allow_paid_calls: false`) |
| Paper-eligible runs | **0** |
| Eligible paper assets | **0** |
| Claims C1–C8 / C10 | planned / unsupported |
| Claim C9 | engineering_only |
| APPROVED config in repo | Present only for self-authorized dry-run/preflight |
| True leakage blockers | **0** (verified by latest `all-no-run-reports`) |

## Template status (`configs/provider_pilot_tiny_template.yaml`)

| Check | Value |
|---|---|
| TEMPLATE ONLY / DO NOT RUN | Header + `template_only: true` |
| `allow_paid_calls` | `false` |
| `scientific_evidence` | `false` |
| `evidence_scope` | `provider_pilot_pending_verification` |
| `approval.*` | all false |
| Caps | ≤ 5 instances/trajectories; budget ≤ $5 |
| Provider-backed agent | `direct_tool_agent` + env model placeholder |
| API keys in YAML | **None** |

Preflight gate (template, no leakage reports): `template_safe_but_not_runnable`.

## Approved dry-run config status (`configs/provider_pilot_tiny_APPROVED.yaml`)

| Check | Value |
|---|---|
| Approval source | `docs/approvals/SELF_AUTHORIZATION_TINY_PROVIDER_PILOT.md` |
| Dry-run approval | `true` |
| Live-run approval | `false` |
| `allow_paid_calls` | `false` |
| `scientific_evidence` | `false` |
| `evidence_scope` | `provider_pilot_debug_or_preliminary` |
| Caps | 5 trajectories; 30 estimated provider calls; budget ≤ $5 |
| API keys in YAML | **None** |

Preflight gate (approved config): `ready_for_dry_run`.

## Approval checklist

Completed for dry-run/preflight:

1. Self-authorization saved in `docs/approvals/SELF_AUTHORIZATION_TINY_PROVIDER_PILOT.md`
2. Template copied to `configs/provider_pilot_tiny_APPROVED.yaml`
3. Approval fields populated for dry-run only

Still required for live execution:

1. Explicit live-run approval (`Live-run approval: Yes`)
2. Enable the live-run approval marker
3. Enable paid calls only in the approved live-run copy
4. Final cost estimate reviewed against budget cap

## Leakage gate

- Binding gate for dry-run: `blocker_cluster_count == 0` for true answer leakage
- See `answer_leakage_repair.md` from latest report bundle

## Cost estimate summary (approved dry-run config, indicative)

Run:

```bash
python3 -m causal_agent_bench estimate-run-cost \
  --config configs/provider_pilot_tiny_APPROVED.yaml \
  --output-dir /tmp/cab_tiny_provider_approved_cost
```

Latest approved-config estimate:

- `runnable_without_approval: false`
- `allow_paid_calls: false`
- estimated high cost: `$0.2436`
- trajectories: `5`
- estimated provider calls: `30`
- budget cap: `$5.00`

## Expected runtime (indicative)

| Phase | Duration |
|---|---|
| `all-no-run-reports` | ~1–2 min |
| `validate-config` / `plan-run` | seconds |
| Dry-run (when allowed) | ~30s–2 min (no API) |
| Live tiny pilot (future) | ~10–30 min + API latency |

## Dry-run steps

See `docs/PROVIDER_PILOT_DRY_RUN_CHECKLIST.md`.

Gate required: `ready_for_dry_run` on **APPROVED** config with leakage clear.

## Live-run conditions

All of:

- `ready_for_live_run` preflight gate
- live-run approval marker + `approval_date` + `advisor_approval_id`
- paid calls enabled **only** in APPROVED copy
- Dry-run completed and reviewed
- Budget owner sign-off for live spend

## Post-run checks (after any future live run)

See `docs/POST_PROVIDER_PILOT_CHECKLIST.md`:

- `INCOMPLETE_RUN.json` absent
- Metadata / provider classification / trajectories / scores / actual cost
- `run-health`, `validate-paper-assets`, `claim-evidence`, `check_evidence_safety.py`
- No C3/C10 without human validation
- No `--promote-to-supported` until eligibility passes

## Dry-run/preflight commands now allowed

```bash
python3 -m causal_agent_bench validate-config --config configs/provider_pilot_tiny_APPROVED.yaml
python3 -m causal_agent_bench plan-run --config configs/provider_pilot_tiny_APPROVED.yaml
python3 -m causal_agent_bench estimate-run-cost --config configs/provider_pilot_tiny_APPROVED.yaml \
  --output-dir /tmp/cab_tiny_provider_approved_cost
python3 -m causal_agent_bench dry-run --config configs/provider_pilot_tiny_APPROVED.yaml
```

## Commands not to run now

- `run --config ...` (any provider config)
- Provider APIs / `run-llm-judge`
- `make smoke` / broad `make test`
- Claim promotion / `fill-paper-from-run --promote-to-supported`
- Enabling paid calls

## Safe validation bundle

```bash
python3 scripts/check_evidence_safety.py
python3 -m causal_agent_bench validate-config --config configs/provider_pilot_tiny_APPROVED.yaml
python3 -m causal_agent_bench plan-run --config configs/provider_pilot_tiny_APPROVED.yaml
python3 -m causal_agent_bench estimate-run-cost --config configs/provider_pilot_tiny_APPROVED.yaml \
  --output-dir /tmp/cab_godtier_provider_prep/cost_estimate
python3 -m causal_agent_bench all-no-run-reports --config configs/provider_pilot_tiny_APPROVED.yaml \
  --output-dir /tmp/cab_godtier_provider_prep
```
