# Error Case Notes — Post-Provider-Pilot Audit

**Audit ID:** `20260519_no_real_provider_pilot`  
**Run directory:** *none*  
**Verdict:** **invalid** — primary failure is absence of a real provider pilot

---

## Primary failure: pilot never executed

The post-provider-pilot audit cannot proceed because **no paid provider run directory** exists under `results/`. Prompt 66 assumes `results/<timestamp>_pilot_multi_provider_20` with real trajectories, provider telemetry, and scoreable artifacts.

### Evidence

| Check | Result |
|---|---|
| Provider-backed runs in `results/` | **0 / 24** metadata files |
| `results/*pilot_multi_provider*` (non–dry-run) | **0 directories** |
| Dry-run `paid_calls_made` | **false** (latest: `20260519T063727Z`) |
| `run_allowed` at cost gate | **false** |

### Root causes (preflight blockers)

1. **No explicit paid-call approval** in operator session
2. **`allow_paid_calls: false`** in `configs/pilot_multi_provider_20.yaml`
3. **API keys unset:** `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `OPENROUTER_API_KEY`
4. **Model IDs unset:** `OPENAI_MODEL_ID`, `ANTHROPIC_MODEL_ID`, `OPENROUTER_MODEL_ID`

These are configuration/approval failures, not runtime agent failures — because the run never started.

---

## Secondary: dry-run is not a scoreable run

Attempting post-run scoring on the dry-run directory fails:

```text
score --run-dir results/dry_runs/20260519T063727Z_pilot_multi_provider_20
→ FileNotFoundError: tasks.jsonl
```

Dry-run artifacts (`dry_run_report.json`, `simulations.jsonl`, per-agent trajectory JSON) are **preflight simulations** using `local_stub`, not provider-backed experiment evidence.

### Dry-run safety flags (correct behavior)

- `provider_calls_replaced_with_local_stub: true`
- `scientific_evidence: false`
- `will_call_providers: false`
- 3/3 single-instance simulations OK (engineering check only)

---

## Tertiary: stub pilot is not a substitute

Nearest completed 120-instance run: `results/20260519T053609Z_pilot_20_multi_agent_stub`

| Issue | Detail |
|---|---|
| Provider | `local_stub` only (`uses_paid_providers: false`) |
| Deployment class | `pilot_stub_engineering_only` |
| Clean/intervention success | **0%** all agents (expected for deterministic stub) |
| ACRS | **null** (no successes to aggregate) |
| Scientific scope | `engineering_only_local_stub` |

**Do not treat stub zero-success tables as agent failure modes or intervention effects.** They reflect stub behavior, not model competence.

### Stub run score report excerpt

All five agents (including `greedy_tool_agent`, `react_stub_agent`):

- Clean success: 0.000
- Intervention success: 0.000
- ACRS: NA

All intervention families: final success 0.000, trajectory faithfulness 0.000.

These are **not** error cases for a provider pilot — they are expected engineering outputs.

---

## Failed provider API calls

**N/A** — zero provider API calls were made in any candidate directory.

---

## Missing metadata (would block valid audit even if partial run existed)

For a real provider pilot, the following would be required and are currently absent:

- Real `model_id` per agent run in `run_metadata.json`
- Actual token usage and cost in trajectories
- Provider latency distributions
- `errors.jsonl` from paid provider retries/timeouts
- Score/analyze/export-paper-assets outputs linked to provider run ID

---

## Oracle exclusion confirmation

- Planned config excludes `scripted_oracle_agent` ✓
- No provider trajectories to rank ✓
- Stub run includes deterministic baselines — not oracles, not provider models

---

## Implications for error-case analysis (C3, C7, C8)

Claims depending on error-case mining (**C3** trajectory/final disagreement, **C7** tool overuse, **C8** premature stopping) **cannot** be supported until:

1. Real provider trajectories exist
2. `analyze` generates `error_cases/` from non-stub behavior
3. Human validation sample is drawn (for C3)

---

## Next step

Resolve preflight blockers and execute the paid pilot per [`runs/RUNBOOK_TINY_PROVIDER_PILOT.md`](../../../runs/RUNBOOK_TINY_PROVIDER_PILOT.md), then re-run Prompt 66.

```bash
# After approval + credentials + allow_paid_calls: true
python3 scripts/check_pilot_readiness.py --config configs/pilot_multi_provider_20.yaml --require paid_pilot_ready
python3 -m causal_agent_bench run --config configs/pilot_multi_provider_20.yaml
```
