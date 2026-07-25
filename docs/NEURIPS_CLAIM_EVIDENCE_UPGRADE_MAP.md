# NeurIPS Claim–Evidence Upgrade Map

**Purpose:** Define exactly what is required to promote each claim from `planned` → `supported`.  
**Current state:** 0 paper-eligible runs · 0 eligible empirical assets · **no promotions**

---

## C1: Clean success overestimates robust competence under intervention

| Field | Value |
|-------|-------|
| **Status** | `planned` / unsupported |
| **Required evidence** | Paired clean/intervention runs, multiple non-oracle agents, CIs showing intervention success < clean |
| **Run scale** | Stage F: main_500 (min Stage D: 100 for pilot claim only) |
| **Models** | ≥3 frontier categories + ≥1 budget model (see model rationale doc) |
| **Human validation** | Optional audit sample for degradation examples |
| **Tables/figures** | `table2_main_agent_performance`, `figure2_clean_vs_intervention_success` |
| **Eligible assets** | `.meta.json` with `eligible_for_paper_claims: true`, non-oracle, complete run |
| **Promotion conditions** | Post-run audit pass · claim-evidence matrix update · ledger `supported` + linked `run_dir` |
| **Forbidden wording until supported** | "agents fail X%", "degradation of Y points", "clean success overestimates" as finding |

---

## C2: Tool failure and memory corruption expose hidden weaknesses

| Field | Value |
|-------|-------|
| **Status** | `planned` |
| **Required evidence** | Family-balanced breakdown: tool_failure + memory_corruption degradation |
| **Run scale** | Stage E–F |
| **Models** | Same minimum set as C1 |
| **Human validation** | Representative trajectories in failure gallery |
| **Tables/figures** | `table3_intervention_family_performance`, `figure3_intervention_family_breakdown` |
| **Promotion conditions** | Per-family N sufficient · isolation audit clear for families cited |
| **Forbidden wording** | "tool failures expose", "memory corruption reveals" without data |

---

## C3: Trajectory metrics detect failures missed by final-answer scoring

| Field | Value |
|-------|-------|
| **Status** | `planned` |
| **Required evidence** | Disagreement cases + **human validation** agreement on labels |
| **Run scale** | Stage C+ trajectories; Stage G annotations |
| **Models** | ≥2 providers |
| **Human validation** | **Required** — 40–60 pilot, 120–200 main; κ reported |
| **Tables/figures** | `figure6_trajectory_final_disagreement`, `table5_human_validation_agreement` |
| **Promotion conditions** | Completed annotations · adjudication · agreement thresholds met |
| **Forbidden wording** | "validators agree", "trajectory metrics catch", "human audit confirms" |

---

## C4: ACRS changes model rankings relative to clean success

| Field | Value |
|-------|-------|
| **Status** | `planned` |
| **Required evidence** | Spearman ρ(clean, ACRS) with CI · ranking instability examples |
| **Run scale** | Stage F (≥5 models) |
| **Models** | **≥5** non-oracle model families |
| **Human validation** | Not required |
| **Tables/figures** | `figure4_ranking_instability`, `table2` ACRS columns |
| **Forbidden wording** | "ACRS changes rankings", "models reorder" |

---

## C5: Recovery ability is separable from planning ability

| Field | Value |
|-------|-------|
| **Status** | `planned` |
| **Required evidence** | Component analysis or scaffold ablation separating recovery vs planning proxies |
| **Run scale** | Stage E–F + ablation cells |
| **Models** | ≥3 |
| **Human validation** | Optional |
| **Tables/figures** | `table4_ablation_results`, component columns in `table2` |
| **Forbidden wording** | "recovery is separable", "planning ≠ recovery" |

---

## C6: Simple self-checking improves some intervention families but not all

| Field | Value |
|-------|-------|
| **Status** | `planned` |
| **Required evidence** | Prompt/scaffold ablation with fixed agents/tasks |
| **Run scale** | Stage D–F ablation matrix |
| **Models** | ≥2 (same agent family, different scaffolds) |
| **Tables/figures** | `table4_ablation_results` |
| **Forbidden wording** | "self-checking improves", "prompting helps robustness" |

---

## C7: Some agents overuse tools even when unnecessary

| Field | Value |
|-------|-------|
| **Status** | `planned` |
| **Required evidence** | irrelevant_tools family: tool-call rate vs success |
| **Run scale** | Stage D+ |
| **Models** | ≥3 |
| **Tables/figures** | `figure5_failure_mode_distribution`, tool-use metrics |
| **Forbidden wording** | "agents overuse tools", "unnecessary tool calls" |

---

## C8: Some agents stop prematurely under misleading success signals

| Field | Value |
|-------|-------|
| **Status** | `planned` |
| **Required evidence** | premature_success_signal family: premature-stop rate |
| **Run scale** | Stage D+ |
| **Models** | ≥3 |
| **Tables/figures** | `figure5`, `error_cases/premature_stopping.md` |
| **Forbidden wording** | "agents stop prematurely", "misleading success" |

---

## C9: Smoke tests reproducible without paid services

| Field | Value |
|-------|-------|
| **Status** | `engineering_only` |
| **Required evidence** | CI/fast-check reproducibility — **not** LLM benchmark results |
| **Run scale** | Engineering smoke only |
| **Promotion** | May remain `engineering_only`; never supports C1–C8 |
| **Forbidden wording** | Using C9 to imply model benchmark conclusions |

---

## C10: Controlled interventions isolate intended skill components

| Field | Value |
|-------|-------|
| **Status** | `planned` |
| **Required evidence** | Expert/human audit: single-factor isolation per intervention |
| **Run scale** | Static dossier + Stage G HV (40–200 items) |
| **Human validation** | **Required** |
| **Tables/figures** | `table5`, intervention validity dossier |
| **Forbidden wording** | "interventions isolate", "validated isolation", "experts confirm" |

---

## Global promotion firewall

1. `paper_eligible_runs > 0`
2. Linked artifacts pass `paper_asset_eligibility` scan
3. `check_evidence_safety.py` exit 0 in submission mode
4. No placeholder language in promoted fragments
5. Advisor sign-off on claim-evidence matrix diff

**Tiny pilot (Stage B, ≤5 trajectories):** may support pipeline/debug claims only — **not** C1–C8 headline claims.
