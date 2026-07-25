# Tiny Real Provider Pilot Runbook

**Status:** Prepared — **not executed** (no paid API calls in current session)  
**Prepared:** 2026-05-19  
**Readiness verdict:** `cost_estimate_ready` (not `paid_pilot_ready`)

This runbook describes the first tiny **non-oracle**, **provider-backed** pilot for CausalAgentBench. Dry-run and cost estimation have passed; a real run requires explicit human cost approval and configured credentials.

---

## Pilot scope

| Item | Value |
|---|---|
| Base tasks | **20** (`data/processed/pilot_v0_1/pilot_20_base_tasks.jsonl`) |
| Instances | **120** paired clean/intervention (`pilot_20_instances.jsonl`) |
| Agents | **3** non-oracle provider-backed agents |
| Providers | OpenAI, Anthropic, OpenRouter |
| Max steps | 8 per instance |
| Repeats | 1 |
| Planned trajectories | **360** (120 × 3) |
| Tools | Deterministic simulated tools only (no live web, email, or bookings) |
| Data | Synthetic benchmark data only — no private data |

### Agents (no oracle)

| Agent run ID | Agent | Provider | Model env var |
|---|---|---|---|
| `direct_tool_openai` | `direct_tool_agent` | `openai` | `OPENAI_MODEL_ID` |
| `planner_executor_anthropic` | `planner_executor_agent` | `anthropic` | `ANTHROPIC_MODEL_ID` |
| `self_check_openrouter` | `self_check_agent` | `openrouter` | `OPENROUTER_MODEL_ID` |

**Oracle exclusion:** `scripted_oracle_agent` is **not** in this config. Config schema rejects oracle + paid provider combinations.

---

## Config and dataset

| Field | Path / value |
|---|---|
| **Run config** | `configs/pilot_multi_provider_20.yaml` |
| **Dataset** | `data/processed/pilot_v0_1/pilot_20_instances.jsonl` |
| **Provider registry** | `configs/providers.yaml` |
| **Pricing registry** | `configs/model_pricing.yaml` |
| **Output parent** | `results/` (timestamped subdir created at run time) |
| **Seed** | `2027` |
| **`allow_paid_calls`** | `false` (must set `true` only after explicit approval) |

### Budget and cost (preflight 2026-05-19)

| Field | Value |
|---|---|
| Run budget cap | **$75.00 USD** |
| Per-agent cap | **$25.00 USD** each |
| Per-task cap | **$2.00 USD** |
| Max API calls (run) | **2,880** |
| **Estimated cost (upper bound)** | **$44.26 USD** |
| Budget status | `within_budget` |
| Pricing source | `configs/model_pricing.yaml` (user-configurable defaults) |

Conservative token upper bounds: **5.95M input** / **2.40M output** tokens.

---

## Preflight (must pass before any paid run)

Run from repository root:

```bash
python3 -m pytest -q
python3 scripts/check_pilot_readiness.py --config configs/pilot_multi_provider_20.yaml
python3 -m causal_agent_bench dry-run --config configs/pilot_multi_provider_20.yaml --output-dir results/dry_runs
python3 -m causal_agent_bench estimate-cost --config configs/pilot_multi_provider_20.yaml
python3 -m causal_agent_bench validate-config --config configs/pilot_multi_provider_20.yaml
python3 -m causal_agent_bench list-providers
```

### Preflight results (2026-05-19)

| Check | Result |
|---|---|
| Tests | **272 passed**, 1 skipped |
| Readiness | **`cost_estimate_ready`** |
| Dry-run | **PASS** — `paid_calls_made: false`, 3/3 simulations OK |
| Latest dry-run dir | `results/dry_runs/20260519T063727Z_pilot_multi_provider_20` |
| Cost vs budget | **$44.26 ≤ $75.00** |
| `run_allowed` | **false** (expected until keys + approval) |

### Abort conditions — stop and do not run if any apply

1. Tests fail
2. Readiness below `cost_estimate_ready`
3. Dry-run fails or `paid_calls_made` is not `false` in dry-run report
4. `estimate-cost` upper bound **exceeds** `budget.max_total_usd` ($75)
5. **Model IDs missing** (`OPENAI_MODEL_ID`, `ANTHROPIC_MODEL_ID`, `OPENROUTER_MODEL_ID`)
6. **API keys missing** (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `OPENROUTER_API_KEY`)
7. **`allow_paid_calls: false`** in config (or no explicit human cost approval)
8. Oracle agent appears in config
9. User has not explicitly approved the estimated cost (~$44 upper bound)
10. Would overwrite an existing in-progress provider run without a new timestamped directory

**Current blockers (2026-05-19):** items 5, 6, 7, and 9.

---

## Pre-run setup (human operator)

1. Copy [`.env.example`](../.env.example) to `.env` (gitignored). **Never commit keys.**
2. Export credentials in the shell (values not logged by this repo's CLI):

```bash
export OPENAI_API_KEY=...
export ANTHROPIC_API_KEY=...
export OPENROUTER_API_KEY=...
export OPENAI_MODEL_ID=...          # e.g. gpt-4o-mini
export ANTHROPIC_MODEL_ID=...       # e.g. claude-3-5-sonnet-latest
export OPENROUTER_MODEL_ID=...      # e.g. openai/gpt-4o-mini
```

3. Re-verify gates:

```bash
python3 scripts/check_pilot_readiness.py --config configs/pilot_multi_provider_20.yaml --require paid_pilot_ready
python3 -m causal_agent_bench estimate-cost --config configs/pilot_multi_provider_20.yaml
```

4. **Explicitly approve** the cost upper bound (~$44 USD conservative estimate).
5. Edit `configs/pilot_multi_provider_20.yaml`: set `allow_paid_calls: true` (commit only if intentional; prefer local override copy).
6. Confirm no oracle agents and no live-web tools in config.

---

## Execute paid pilot (only after approval)

```bash
python3 -m causal_agent_bench run --config configs/pilot_multi_provider_20.yaml
```

Expected outputs under `results/<timestamp>_pilot_multi_provider_20/`:

- `config.yaml` (redacted), `config_hash.txt`
- `run_metadata.json`, `metadata.json`
- `instances.jsonl`, `trajectories.jsonl`, `errors.jsonl`
- `scores.jsonl`, `aggregate_scores.json`, `aggregate_summary.json` (if `auto_score: true`)
- Provider/model IDs, prompt hashes, token usage, cost estimates in trajectory metadata
- **No API keys** in any artifact

Record the run directory path:

```bash
export RUN_DIR=results/<timestamp>_pilot_multi_provider_20
```

---

## Post-run validation (required before any claim updates)

```bash
python3 -m causal_agent_bench summarize-run --run-dir "$RUN_DIR"
python3 -m causal_agent_bench score --run-dir "$RUN_DIR"
python3 -m causal_agent_bench analyze --run-dir "$RUN_DIR"
python3 -m causal_agent_bench export-paper-assets --run-dir "$RUN_DIR"
python3 scripts/check_claim_ledger.py
python3 scripts/check_paper_placeholders.py --mode draft
```

### Post-run audit artifact

Create after a real run completes:

```text
audits/provider_pilot/<run_id>/PILOT_AUDIT.md
```

Use `<run_id>` = timestamped run folder name (e.g. `20260519T120000Z_pilot_multi_provider_20`).

Audit must document:

- Provider/model metadata per agent run
- Actual vs estimated cost, latency, errors, failed calls
- Instance and trajectory counts
- Oracle exclusion confirmation
- Whether scores and analysis assets were generated
- Whether results are sufficient for **pilot-level** claims only (not NeurIPS-scale claims)

### Claim ledger policy

- Do **not** mark main scientific claims as `supported` until audit passes and evidence paths exist in `docs/claim_ledger.json`.
- Pilot results may support **cautious pilot observations** only after Prompt 66 post-pilot audit.
- Do **not** run `fill-paper-from-run` or update paper placeholders until audit approves.

---

## Rollback / abort during run

- Stop the process (Ctrl+C). Partial results remain in `$RUN_DIR`; do not delete without archiving.
- Do not re-run with the same `resume_dir` unless config hash is unchanged.
- If budget exceeded mid-run, check `errors.jsonl` for `BudgetExceededError` entries.

---

## Next step after successful pilot

Run **Prompt 66 — Post-Provider-Pilot Audit** (`66_POST_PROVIDER_PILOT_AUDIT.md`) against `$RUN_DIR`.

---

## References

- Provider env vars: [README.md](../README.md), [`.env.example`](../.env.example)
- Commercial API policy: [docs/COMMERCIAL_API_RUNS.md](../docs/COMMERCIAL_API_RUNS.md)
- Cost/budget: [docs/COST_LATENCY.md](../docs/COST_LATENCY.md)
- Claim ledger: [docs/claim_ledger.json](../docs/claim_ledger.json)
