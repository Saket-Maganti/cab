# Post-Provider-Pilot Audit

**Audit ID:** `20260519_no_real_provider_pilot`  
**Audit date:** 2026-05-19  
**Final verdict:** **invalid** — no real non-oracle provider-backed pilot run exists

---

## Run directory

**Requested target:** latest provider-backed run under `results/`  
**Found:** **none**

| Candidate | Path | Classification |
|---|---|---|
| Closest real run (stub) | `results/20260519T053609Z_pilot_20_multi_agent_stub` | Engineering-only; `local_stub`; not provider-backed |
| Latest dry-run | `results/dry_runs/20260519T063727Z_pilot_multi_provider_20` | Dry-run simulation; `paid_calls_made: false`; not scoreable |
| Smoke runs (24 total) | `results/*_smoke` | Deterministic baseline; no LLM providers |

Automated scan of 24 non–dry-run `run_metadata.json` files: **`uses_paid_providers: false` for all**.

---

## Run classification (intended pilot config)

Config prepared but **not executed:** `configs/pilot_multi_provider_20.yaml`

| Dimension | Status |
|---|---|
| Provider-backed | **No** — run never started |
| Non-oracle | Config excludes oracle; N/A until run exists |
| Complete / partial | **N/A** — zero trajectories from paid providers |
| Dry-run vs real | Only dry-run artifacts exist |
| Agents (planned) | 3: `direct_tool_openai`, `planner_executor_anthropic`, `self_check_openrouter` |
| Instances (planned) | 120 (20 base tasks × paired clean/intervention) |
| Domains | travel, scheduling, research (from pilot_v0.1 dataset) |
| Intervention families | 9 (+ clean baseline) |
| Cost | **$0 actual** (no paid calls) |
| Latency | N/A |
| Error rate | N/A |
| Retry rate | N/A |

---

## Metadata verification

| Field | Status |
|---|---|
| Config copy/hash | Dry-run only: `804da0651e5dfacd` at `results/dry_runs/.../config.yaml` |
| Dataset version | `pilot_v0.1` (frozen/processed paths present) |
| Git commit | Working tree dirty; HEAD `dea8e25` at stub run time |
| Provider/model ID | **Missing** — model env vars unset at dry-run |
| Prompt hash | Dry-run logged 11 prompt hashes; no real-run linkage |
| Sampling settings | Config: temperature 0.0, max_tokens 700–900, retry_count 0 |
| Retry policy | Provider retry_count 0 in pilot config |
| Cost/latency/timestamp | No real-run timestamps or provider telemetry |
| Scorer version | Stub run scored locally; not applicable to provider pilot |

---

## Post-run commands (not executed — no valid run dir)

```bash
# BLOCKED: no results/<timestamp>_pilot_multi_provider_20 directory exists
python3 -m causal_agent_bench score --run-dir results/<run_dir>
python3 -m causal_agent_bench analyze --run-dir results/<run_dir>
python3 -m causal_agent_bench export-paper-assets --run-dir results/<run_dir>
```

Dry-run directory fails `score` (missing `tasks.jsonl`, `trajectories.jsonl`).

---

## Performance artifacts

| Artifact | Provider pilot | Nearest stub run |
|---|---|---|
| Main performance table | **Missing** | All agents 0% clean/intervention success |
| Intervention breakdown | **Missing** | All families 0% (engineering stub) |
| Ranking instability | **Missing** | ACRS null (no successes) |
| Error cases | **Missing** | N/A |
| ACRS / CIs | **Missing** | N/A |
| Per-family metrics | **Missing** | Present but zero-valued in stub |

Stub metrics are **not** usable for provider-pilot or scientific claims.

---

## Oracle exclusion

- Planned pilot config: **no oracle agents**
- No provider run trajectories to audit
- Stub run includes non-LLM baselines (`greedy_tool_agent`, `react_stub_agent`) — not oracles, but not provider-backed either

---

## Claim ledger impact

**No claim rows may be upgraded.** All main claims (C1–C8, C10) remain `planned`. C9 remains `engineering_only`.

See `CLAIM_UPDATE_RECOMMENDATIONS.md` for per-claim guidance.

---

## Blockers to valid pilot

1. No explicit paid-call approval in session
2. `allow_paid_calls: false` in config
3. API keys unset (OpenAI, Anthropic, OpenRouter)
4. Model IDs unset
5. Real `run` command never executed

---

## Next step

Execute Prompt 65 paid pilot per [`runs/RUNBOOK_TINY_PROVIDER_PILOT.md`](../../../runs/RUNBOOK_TINY_PROVIDER_PILOT.md), then re-run this audit (Prompt 66) against `results/<timestamp>_pilot_multi_provider_20`.
