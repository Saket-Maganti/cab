# Command Map

Find the right command by **intent**. For full CLI details see [CLI_REFERENCE.md](CLI_REFERENCE.md).

Status key: **safe** = no model calls · **heavy** = may run models locally · **paid** = may cost API money

---

## I want to check project health

| Command | Status | Runtime | Models? | Cost? |
|---|---|---|---|---|
| `make fast-check` | safe | ~60s | No | $0 |
| `make doctor` | safe | ~10s | No | $0 |
| `python3 scripts/generate_master_status.py` | safe | ~5s | No | $0 |
| `python3 scripts/final_build_phase_audit.py` | safe | ~60s | No | $0 |
| `python3 scripts/check_submission_readiness.py` | safe | ~10s | No | $0 |
| `make audit-repo` | safe | ~20s | No | $0 |
| `make audit-configs` | safe | ~5s | No | $0 |

---

## I want to plan a run

| Command | Status | Runtime | Models? | Cost? |
|---|---|---|---|---|
| `make plan-micro` | safe | ~5s | No | $0 |
| `python3 -m causal_agent_bench plan-run --config <cfg>` | safe | ~5s | No | $0 |
| `python3 -m causal_agent_bench estimate-cost --config <cfg>` | safe | ~5s | No | $0 |
| `python3 -m causal_agent_bench dry-run --config <cfg>` | safe | ~30s | No | $0 |
| `python3 -m causal_agent_bench validate-config --config <cfg>` | safe | ~2s | No | $0 |

---

## I want to run a tiny safe experiment

| Command | Status | Runtime | Models? | Cost? |
|---|---|---|---|---|
| `run --config configs/pilot_mock_diagnostic_micro.yaml` | heavy | ~5–10m | Mock only | $0 |
| `run --config configs/pilot_stub_micro_3.yaml` | heavy | ~5m | Stub only | $0 |
| `run --config configs/pilot_free_local_micro_3.yaml` | heavy | 30–60m+ | Local LLM | $0* |

\*Uses local compute. Not default build-mode path. See [SAFE_NEXT_RUN_DECISION_TREE.md](https://github.com/Saket-Maganti/causal-agent-bench/blob/main/experiments/SAFE_NEXT_RUN_DECISION_TREE.md).

**Before any run:** [PRE_EXPERIMENT_FREEZE_CHECKLIST.md](https://github.com/Saket-Maganti/causal-agent-bench/blob/main/experiments/PRE_EXPERIMENT_FREEZE_CHECKLIST.md)

---

## I want to inspect a run

| Command | Status | Runtime | Models? | Cost? |
|---|---|---|---|---|
| `python3 -m causal_agent_bench index-runs` | safe | ~5s | No | $0 |
| `python3 -m causal_agent_bench run-status --latest` | safe | ~2s | No | $0 |
| `python3 -m causal_agent_bench summarize-run --run-dir <dir>` | safe | ~5s | No | $0 |
| `python3 -m causal_agent_bench monitor --latest` | safe | varies | No | $0 |

---

## I want to mark a run interrupted

| Command | Status | Runtime | Models? | Cost? |
|---|---|---|---|---|
| `python3 -m causal_agent_bench mark-interrupted --run-dir <dir>` | safe | ~2s | No | $0 |

---

## I want to generate reports

| Command | Status | Runtime | Models? | Cost? |
|---|---|---|---|---|
| `python3 -m causal_agent_bench score --run-dir <dir>` | safe* | ~30s | No | $0 |
| `python3 -m causal_agent_bench analyze --run-dir <dir>` | safe* | ~30s | No | $0 |
| `python3 -m causal_agent_bench generate-report --latest` | safe* | ~30s | No | $0 |

\*Do not treat mock/stub/interrupted runs as scientific evidence.

---

## I want to audit data

| Command | Status | Runtime | Models? | Cost? |
|---|---|---|---|---|
| `python3 -m causal_agent_bench audit-dataset --config <cfg>` | safe | ~10s | No | $0 |
| `python3 -m causal_agent_bench audit-interventions --benchmark-dir <dir>` | safe | ~30s | No | $0 |
| `python3 -m causal_agent_bench audit-contamination --benchmark-dir <dir>` | safe | ~60s | No | $0 |
| `python3 scripts/audit_intervention_isolation.py` | safe | ~30s | No | $0 |

---

## I want to check paper readiness

| Command | Status | Runtime | Models? | Cost? |
|---|---|---|---|---|
| `make check-paper` | safe | ~15s | No | $0 |
| `python3 scripts/check_paper_section_contract.py --mode draft` | safe | ~2s | No | $0 |
| `python3 scripts/lint_paper_claims.py --mode draft` | safe | ~5s | No | $0 |
| `python3 scripts/check_paper_placeholders.py --mode draft` | safe | ~5s | No | $0 |
| `python3 scripts/validate_paper_assets.py --mode draft` | safe | ~5s | No | $0 |

---

## I want to prepare release artifacts

| Command | Status | Runtime | Models? | Cost? |
|---|---|---|---|---|
| `python3 -m causal_agent_bench build-release-manifest` | safe | ~10s | No | $0 |
| `python3 -m causal_agent_bench plan-repro-bundle` | safe | ~5s | No | $0 |
| `python3 -m causal_agent_bench capture-env` | safe | ~5s | No | $0 |
| `make release-check` | safe | ~30s | No | $0 |

---

## I want governance / god-tier status (no models)

| Command | Status | Runtime | Models? | Cost? |
|---|---|---|---|---|
| `python3 scripts/god_tier_status.py` | safe | ~2s | No | $0 |
| `make god-tier-status` | safe | ~2s | No | $0 |
| `python3 -m causal_agent_bench all-no-run-reports --output-dir /tmp/cab_*` | safe | ~1–2m | No | $0 |
| `python3 -m causal_agent_bench all-safety-reports` | safe | ~30s | No | $0 |
| `python3 scripts/check_run_index.py` | safe | ~2s | No | $0 |
| `python3 scripts/check_evidence_safety.py` | safe | ~5s | No | $0 |
| `make no-run-reports` | safe | ~1–2m | No | $0 |

See [NO_RUN_REPORTS_GUIDE.md](NO_RUN_REPORTS_GUIDE.md), [GOD_TIER_MANIFEST.md](https://github.com/Saket-Maganti/causal-agent-bench/blob/main/GOD_TIER_MANIFEST.md), [reports/INDEX.md](https://github.com/Saket-Maganti/causal-agent-bench/blob/main/reports/INDEX.md).

---

## I want to avoid overclaiming

| Command | Status | Runtime | Models? | Cost? |
|---|---|---|---|---|
| Read [DO_NOT_OVERCLAIM.md](DO_NOT_OVERCLAIM.md) | safe | — | No | $0 |
| `python3 scripts/check_evidence_safety.py` | safe | ~5s | No | $0 |
| `python3 scripts/check_claim_ledger.py` | safe | ~5s | No | $0 |

---

## Forbidden without explicit approval

- `run` with OpenAI / Anthropic / OpenRouter / Gemini configs
- `run --config configs/commercial_api_main_500.yaml`
- `fill-paper-from-run` without verified pilot
- `export-paper-assets` without `--allow-engineering-only` on stub/mock runs

See [MASTER_STATUS.md](https://github.com/Saket-Maganti/causal-agent-bench/blob/main/MASTER_STATUS.md).
