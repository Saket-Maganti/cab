# Zero-Cost Pilot Audit

**Audit date:** 2026-05-20  
**Auditor:** automated post-run verification (Prompt: Post Zero-Cost Run Verification)

## Verdict

**`dry_run_only`**

No completed zero-cost / local / free-provider experiment run exists under `results/`. The latest zero-cost-related artifact is a **dry-run preflight** only.

## Run directory

| Field | Value |
|---|---|
| **Audited artifact** | `results/dry_runs/20260520T024350Z_pilot_zero_cost_matrix_20` |
| **Intended config** | `configs/pilot_zero_cost_matrix_20.yaml` |
| **Expected real run dir** | `results/<timestamp>_pilot_zero_cost_matrix_20` — **not present** |
| **Nearest completed run** | `results/20260519T053609Z_pilot_20_multi_agent_stub` (stub-only; not zero-cost) |

## Config

- **Config path:** `configs/pilot_zero_cost_matrix_20.yaml`
- **Config hash (dry-run):** `e518104c54e50b3e`
- **cost_mode:** `zero_cost`
- **allow_paid_calls:** `false`
- **scientific_evidence_level:** `preliminary_or_engineering`
- **provider_type:** `mixed_zero_cost`
- **budget.max_total_usd:** `0`
- **Agents (planned):** `direct_tool_local_ollama`, `planner_executor_gemini_free`, `self_check_openrouter_free`

## Dataset

- **Path:** `data/processed/pilot_v0_1/pilot_20_instances.jsonl`
- **Instances (planned):** 120 (20 base tasks × paired clean/intervention)
- **Dataset version:** `pilot_v0.1` (from generation report)
- **Dry-run probe:** `travel_planning_medium_000.clean`

## Agents

| Agent run | Agent | Planned provider | Dry-run provider |
|---|---|---|---|
| `direct_tool_local_ollama` | `direct_tool_agent` | `local_openai` | `local_stub` |
| `planner_executor_gemini_free` | `planner_executor_agent` | `gemini` (free-tier) | `local_stub` |
| `self_check_openrouter_free` | `self_check_agent` | `openrouter` (free-tier) | `local_stub` |

Dry-run simulated **3/3** single-instance trajectories; no full 120-instance run executed.

## Provider/model information

| Agent | Planned model | Configured at dry-run |
|---|---|---|
| local Ollama | `${LOCAL_OPENAI_MODEL_ID:-}` | **Missing** |
| Gemini free | `gemini-2.0-flash` | Model OK; API key **missing** |
| OpenRouter free | `google/gemma-2-9b-it:free` | Model OK; API key **missing** |

No real provider/model telemetry exists because no experiment run completed.

## Paid-call status

| Check | Result |
|---|---|
| Dry-run | **Yes** (`dry_run: true`) |
| Paid calls made | **`false`** |
| `paid_calls_made` in safety block | **`false`** |
| Provider calls replaced with local_stub | **`true`** |
| `scientific_evidence` | **`false`** |
| Monetary spend | **$0.00** (no run) |

## Oracle status

- **Oracle agents in config:** **None**
- **Oracle contamination:** **No** (N/A — no rankings produced)
- Planned agents are non-oracle LLM scaffolds only

## Score/analyze/export status

| Command | Target | Result |
|---|---|---|
| `score` | dry-run dir | **FAIL** — missing `tasks.jsonl` (expected) |
| `score` | stub run `20260519T053609Z_pilot_20_multi_agent_stub` | **PASS** (engineering reference only) |
| `analyze` | stub run | **PASS** — `analysis_report.md` updated |
| `export-paper-assets` | stub run | **FAIL** — `evidence_scope=pilot_stub_engineering_only`; requires `--allow-engineering-only` |
| `score/analyze/export` | zero-cost run | **N/A** — no run directory |

## Generated tables and figures

**From zero-cost run:** **None** (run never started).

**From stub reference run** (not valid zero-cost evidence):

- `score_report.md`, `aggregate_scores.json`, `metrics_v2.*` — all **0% success**, ACRS **null**
- `error_cases/` — 60+ mined cases (stub behavior)
- `paper_assets/` — exists from prior stub export with engineering-only flag

## Key metrics summary

No zero-cost metrics available. Dry-run cost estimate: **$0.00 upper bound**.

Stub reference (do not use for claims): clean/intervention success **0%** all agents; top failure modes `final_answer_failure`, `premature_stop`, `missing_required_tools`.

## Main limitations

1. **No real zero-cost experiment executed** — only dry-run preflight passed
2. Local model ID unset; free-tier API keys unset
3. Dry-run uses `local_stub` — not representative of Ollama/Gemini/OpenRouter behavior
4. Cannot score, rank, or export paper assets from a non-existent run
5. Stub run exists but is `local_stub` engineering-only, not zero-cost provider evidence

## Is this usable as preliminary evidence?

**No.** Dry-run confirms pipeline readiness only. It does not constitute preliminary model behavior evidence.

After a real zero-cost run completes, re-audit with `RUN_DIR=results/<timestamp>_pilot_zero_cost_matrix_20`.

## Is this usable for final NeurIPS claims?

**No.** No artifact-linked non-oracle LLM trajectories exist.

## Is Prompt 67 allowed?

**No.** Prompt 67 (claim ledger / paper sync) requires a valid non-oracle provider-backed run. Verdict `dry_run_only` blocks Prompt 67 per decision rules.
