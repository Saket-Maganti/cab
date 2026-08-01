# Command and Runtime Guide

Honest command reference for **Causal Agent Bench** at the current evidence state:

- **0** paper-eligible runs
- **0** eligible empirical paper assets
- **C1–C8 / C10:** planned / unsupported
- **C9:** engineering_only
- **Provider pilot:** dry-run/preflight ready after self-authorization; live provider execution still blocked

Authoritative status: [CURRENT_PROJECT_STATE.md](https://github.com/Saket-Maganti/cab/blob/main/CURRENT_PROJECT_STATE.md).
V2 is the sole future scientific path; Main-500 and v1 scientific execution are
superseded and fail closed.

See also: [COMMAND_MAP.md](COMMAND_MAP.md), [NO_RUN_REPORTS_GUIDE.md](NO_RUN_REPORTS_GUIDE.md), [DO_NOT_OVERCLAIM.md](DO_NOT_OVERCLAIM.md), [RUN_INDEX_FRESHNESS.md](RUN_INDEX_FRESHNESS.md).

---

## Safe no-run commands (recommended default)

| Command | Runtime | Cost | Can support paper claims? |
|---|---|---|---|
| `python3 scripts/check_evidence_safety.py` | ~5s | $0 | No — governance only |
| `python3 -m causal_agent_bench all-no-run-reports --output-dir /tmp/cab_reports` | ~1–2 min | $0 | No — planning/governance |
| `python3 -m causal_agent_bench validate-config --config configs/provider_pilot_tiny_template.yaml` | ~2s | $0 | No — template not runnable |
| `python3 -m causal_agent_bench plan-run --config <cfg>` | ~5s | $0 | No |
| `python3 -m causal_agent_bench estimate-run-cost --config <cfg>` | ~5s | $0 | No — indicative only |
| `make fast-check` | ~60s | $0 | No |
| `python3 scripts/reproduce_artifact.py --all-deterministic` | varies | $0 | C9 engineering_only only |
| `cab benchmark reachability-check` | ~2s | $0 | No — static design audit |
| `cab pre-run scientific-check` | ~2s | $0 | No — hardening gate only |
| `cab plan resources --study scale100 --scenario planned` | <2s | $0 | No — prospective plan |

**Never use these outputs to fill Results/Abstract empirical sentences.**

---

## Planning commands (no models)

Use before any spend:

1. `all-no-run-reports` → advisor packet, paper readiness map, leakage repair, preflight
2. `validate-config` / `plan-run` / `estimate-run-cost` on `configs/provider_pilot_tiny_APPROVED.yaml` after dry-run self-authorization
3. Review `handoff/ADVISOR_REVIEW_BUNDLE_INDEX.md` and `reports/advisor_review/`

---

## Stub / mock engineering commands (heavy, $0 API)

| Command | Runtime | Models? | Claims? |
|---|---|---|---|
| `run --config configs/pilot_mock_diagnostic_micro.yaml` | ~5–10m | Mock | **No** — diagnostics only |
| `run --config configs/pilot_stub_micro_3.yaml` | ~5m | Stub | **No** |
| `dry-run --config <cfg>` | ~30s | None | **No** |

Mock/stub runs must **not** be indexed as paper-eligible or used in tables/figures for C1–C8/C10.

---

## Local LLM commands (heavy, compute risk)

| Command | GPU | Risk |
|---|---|---|
| `run --config configs/pilot_free_local_micro_3.yaml` | Optional | Local weights; long runtime; not provider pilot |
| `run --config configs/pilot_local_openai_compatible_20.yaml` | Optional | Requires local server; still not approved for claims |

- Treat as **engineering experiments** until advisor + dataset gates clear.
- Do not set `allow_paid_calls=true`.
- Results stay **ineligible** for empirical paper claims unless explicitly reclassified (not current state).

---

## Provider commands (dry-run approved; live still unsafe)

| Step | Command | Requirement |
|---|---|---|
| Preflight (no-run) | `provider-pilot-preflight` via `all-no-run-reports` | Leakage blockers = 0 |
| Config hardening | Review `provider_pilot_config_hardening` report | Template stays `allow_paid_calls: false` |
| Approved copy | `configs/provider_pilot_tiny_APPROVED.yaml` | Self-authorized for dry-run/preflight only |
| Dry-run | `dry-run --config ..._APPROVED.yaml` | Allowed; no API/provider calls |
| Live run | `run --config ..._APPROVED.yaml` | **Not approved**; requires explicit live approval and paid-call enablement |

**Do not run** `configs/commercial_api_*.yaml`, `main_500_multi_provider.yaml`, or any config with paid calls enabled until explicit approval.

---

## Budget and cost guidance

- Tiny approved-config estimate: see `run_cost_estimate.json` from `all-no-run-reports --config configs/provider_pilot_tiny_APPROVED.yaml` (indicative, not measured).
- Pilot 20 multi-provider configs can be **$100s+** — blocked at current stage.
- Always run `estimate-run-cost` before APPROVED configs.
- Stop conditions and caps must be in the APPROVED YAML.

---

## What can vs cannot support paper claims

| Activity | C9 engineering | C1–C8 / C10 empirical |
|---|---|---|
| `check_evidence_safety.py` | Indirect guard | Blocks overclaim |
| Deterministic artifact reproduce | Yes (if CI path) | No |
| Mock/stub runs | No | No |
| Local LLM runs | No | No |
| Provider pilot (future) | No | Only after eligible runs + human validation |

---

## Unsafe commands (current repo state)

- `run` on any provider/commercial config before explicit live-run approval
- `fill-paper-from-run --promote-to-supported`
- `update-claim-ledger --promote-to-supported`
- `index-runs` then treating engineering dirs as paper-eligible
- `make smoke` / broad `pytest` as a substitute for advisor review (OK for dev, not evidence)

---

## GPU / no-GPU guidance

- **No-run lane:** CPU only.
- **Mock/stub:** CPU sufficient.
- **Local LLM:** GPU optional; expect 30–60+ minutes for small pilots.
- **Provider APIs:** No local GPU required.

---

## Expected runtimes (indicative)

| Lane | Typical duration |
|---|---|
| `all-no-run-reports` | 1–2 minutes |
| `fast-check` | ~1 minute |
| Mock micro pilot | 5–10 minutes |
| Provider tiny dry-run | ~30s–2 min, no API/provider calls |
| Full main 500 | days + significant cost — **not approved** |

---

## Advisor-first workflow

1. Read `PROJECT_FULL_CURRENT_AUDIT_FOR_OPUS.md`
2. Run `all-no-run-reports` → share `advisor_review/` + `publication_readiness/`
3. Fix true leakage → rerun reports
4. Self-authorization creates dry-run-only APPROVED config
5. Dry-run/preflight → explicit live approval → tiny live pilot
6. Only then discuss empirical paper sections
