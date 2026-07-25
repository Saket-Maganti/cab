# Evidence Gap Map

**Source of truth** for what evidence exists vs what is required. All claims C1–C8, C10 are **planned** unless noted.

## C1 — Clean success overestimates robust competence

| Field | Value |
|---|---|
| **Claim text** | Clean success overestimates robust competence under intervention. |
| **Required artifact** | `tables/table2_main_agent_performance.csv`, `figures/figure2_clean_vs_intervention_success.png` |
| **Minimum evidence** | ≥3 non-oracle agents, pilot split, paired clean/intervention, CIs |
| **Strong evidence** | Main frozen split, ≥5 agents, bootstrap CIs, failure gallery examples |
| **Current evidence** | Placeholder tables; stub/mock runs (engineering only) |
| **Status** | **planned** |
| **Next experiment** | Provider pilot 20-task multi-agent |
| **Config** | `configs/pilot_multi_provider_20.yaml` |
| **Script** | `python3 -m causal_agent_bench run --config configs/pilot_multi_provider_20.yaml` |
| **Est. runtime** | ~1–2 h (provider dependent) |
| **Est. cost** | ~$15–40 (budget approval required) |
| **Human validation** | Optional for examples |
| **Allowed wording now** | "We **plan** to test whether clean success overestimates…" |
| **Forbidden wording now** | "Clean success overestimates…", "We show…", "significant gap" |

## C2 — Tool failure and memory corruption expose weaknesses

| Field | Value |
|---|---|
| **Required artifact** | `tables/table3_*`, `figures/figure3_*` |
| **Minimum evidence** | Family-stratified degradation on tool_failure + memory_corruption |
| **Strong evidence** | Main split + representative trajectories per family |
| **Current evidence** | None (scientific) |
| **Status** | **planned** |
| **Next experiment** | Same pilot + family breakdown analysis |
| **Config** | `configs/pilot_multi_provider_20.yaml` |
| **Est. runtime / cost** | Included in pilot |
| **Human validation** | Recommended for memory-corruption examples |
| **Allowed now** | "Intervention families **target** tool failure and memory corruption…" |
| **Forbidden now** | "Tool failure **exposes** weaknesses in frontier models" |

## C3 — Trajectory metrics detect hidden failures

| Field | Value |
|---|---|
| **Required artifact** | `figures/figure6_*`, `tables/table5_*`, error cases |
| **Minimum evidence** | Disagreement cases + human audit agreement on subset |
| **Strong evidence** | κ > threshold on n≥100 stratified sample |
| **Current evidence** | Mock diagnostic (detector wiring only) |
| **Status** | **planned** |
| **Next experiment** | Provider pilot + human validation export |
| **Config** | Pilot run + `export-human-validation` |
| **Est. runtime** | Pilot + 2–3 days annotation |
| **Human validation** | **Required** |
| **Allowed now** | "Trajectory diagnostics are **designed** to detect…"; mock validation **engineering only** |
| **Forbidden now** | "Trajectory metrics **detect** failures missed by…" |

## C4 — ACRS changes rankings

| Field | Value |
|---|---|
| **Required artifact** | `figures/figure4_*`, table2 ACRS column |
| **Minimum evidence** | ≥4 agents, Spearman ρ clean vs ACRS reported with CI |
| **Current evidence** | None |
| **Status** | **planned** |
| **Next experiment** | Pilot with ≥4 agent configs |
| **Config** | `configs/pilot_multi_provider_20.yaml` |
| **Allowed now** | "ACRS **may** reorder agents relative to clean success (to be tested)" |
| **Forbidden now** | "ACRS **changes** rankings" |

## C5 — Recovery separable from planning

| Field | Value |
|---|---|
| **Required artifact** | `tables/table4_*`, component metrics |
| **Minimum evidence** | Ablation or component analysis on pilot |
| **Current evidence** | None |
| **Status** | **planned** |
| **Next experiment** | Ablation matrix execute (post-pilot) |
| **Config** | `configs/ablations/*` |
| **Allowed now** | "We **hypothesize** recovery is separable…" |
| **Forbidden now** | "Recovery **is** separable" |

## C6 — Self-checking helps selectively

| Field | Value |
|---|---|
| **Required artifact** | `tables/table4_*` |
| **Minimum evidence** | Scaffold ablation on ≥2 families |
| **Status** | **planned** |
| **Next experiment** | Ablation after pilot baseline |
| **Forbidden now** | "Self-checking **improves**…" |

## C7 — Tool overuse

| Field | Value |
|---|---|
| **Required artifact** | table2 unnecessary_tool_rate, fig5 |
| **Minimum evidence** | irrelevant_tools family, real agents |
| **Status** | **planned** |
| **Mock evidence** | `mock_tool_overuser` — **engineering only** (Phase 9 E2E demo) |
| **Forbidden now** | "Agents **overuse** tools" (general) |

## C8 — Premature stopping

| Field | Value |
|---|---|
| **Required artifact** | fig5, premature_stop cases |
| **Minimum evidence** | premature_success_signal family on real agents |
| **Status** | **planned** |
| **Mock evidence** | `mock_premature_stop` — **engineering only** |
| **Forbidden now** | "Agents **stop prematurely** under…" |

## C9 — Smoke reproducibility

| Field | Value |
|---|---|
| **Status** | **engineering_only** |
| **Current evidence** | README, repro scripts, CI |
| **Allowed now** | "Smoke tests are reproducible without paid services (engineering validation)" |
| **Forbidden now** | Using C9 to support C1–C8 |

## C10 — Interventions isolate components

| Field | Value |
|---|---|
| **Required artifact** | `table5`, intervention audit + human agreement |
| **Minimum evidence** | Automated audit pass + expert/human sample validation |
| **Current evidence** | Automated isolation audit pass (pilot_v0_1) — **not sufficient alone** |
| **Status** | **planned** |
| **Next experiment** | Human validation on intervention validity items |
| **Human validation** | **Required** |
| **Allowed now** | "Interventions are **designed** to isolate…; audited automatically; human audit **planned**" |
| **Forbidden now** | "Interventions **isolate** skill components" (unqualified) |

## Quick reference commands

```bash
python3 scripts/check_claim_ledger.py --mode draft
python3 -m causal_agent_bench command-plan --experiment provider_pilot
python3 -m causal_agent_bench export-human-validation --run-dir results/<run_dir>
```
