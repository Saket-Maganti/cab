# NeurIPS Experiment Matrix

**Status:** Stage A only (no-run) · **No provider runs completed**  
**Rule:** Tiny pilot (≤5 trajectories) **cannot support final NeurIPS claims**

---

## Stage A: No-run readiness (current)

| Field | Value |
|-------|-------|
| **Purpose** | Governance, validity scorecard, paper skeleton |
| **Dataset** | `data/frozen/pilot_v0.1` (inspect only) |
| **Models** | None |
| **Trajectories** | 0 |
| **Runtime / cost** | $0 · minutes |
| **Gates** | None |
| **Outputs** | `all-no-run-reports`, claim matrix, validity dossier |
| **Evidence value** | Infrastructure only |
| **Claims supportable** | None empirical; C9 engineering scaffolding |
| **Post-run checks** | `check_evidence_safety.py`, submission gate = NOT_READY |

**Commands:**

```bash
python3 -m causal_agent_bench all-no-run-reports --output-dir /tmp/cab_stage_a
python3 scripts/check_evidence_safety.py
```

---

## Stage B: Approved tiny provider pilot (≤5 trajectories)

| Field | Value |
|-------|-------|
| **Purpose** | First non-oracle LLM wiring check; metadata validation |
| **Dataset** | `pilot_20_instances.jsonl` capped at 5 |
| **Models** | 1 frontier-category model via env placeholder (`OPENAI_MODEL_ID` etc.) |
| **Trajectories** | ≤5 |
| **Runtime / cost** | Minutes · ≤$5 cap |
| **Gates before run** | Leakage=0 · signed approvals · `*_APPROVED.yaml` · `allow_paid_calls: true` · dry-run |
| **Config** | `configs/provider_pilot_tiny_template.yaml` → approved copy |
| **Outputs** | `run_metadata.json`, trajectories, aggregate_scores (**preliminary only**) |
| **Evidence value** | Pipeline validation — **not** paper-eligible until post-run audit |
| **Claims supportable** | **None headline** — cannot support C1–C8 |
| **Post-run checks** | `POST_PROVIDER_PILOT_CHECKLIST.md`, run health, no auto-promotion |

**Cannot conclude:** degradation %, rankings, family breakdowns, human agreement.

---

## Stage C: 20-task single/multi-provider pilot

| Field | Value |
|-------|-------|
| **Purpose** | Early failure analysis; HV sample export |
| **Dataset** | `pilot_20` frozen split |
| **Models** | 2–3 provider categories |
| **Trajectories** | ~20 × agents |
| **Runtime / cost** | Hours · low–medium USD |
| **Gates** | Stage B audit pass · budget approval |
| **Configs** | `pilot_multi_provider_20.yaml`, `pilot_20_multi_agent.yaml` |
| **Evidence value** | Pilot candidate after audit |
| **Claims supportable** | Preliminary C1/C2 observations only — not submission-grade |
| **Post-run checks** | Eligibility scan, intervention review sample |

---

## Stage D: 100-task intermediate benchmark

| Field | Value |
|-------|-------|
| **Purpose** | Agent comparison; ablation cells; metric calibration |
| **Dataset** | `pilot_100` or `commercial_api_pilot_medium_100` |
| **Models** | ≥3 categories |
| **Trajectories** | ~100 × agents |
| **Runtime / cost** | Hours–days · medium USD |
| **Gates** | Gold triage clear · HR queue reviewed |
| **Configs** | `pilot_100_multi_agent.yaml`, `commercial_api_pilot_medium_100.yaml` |
| **Claims supportable** | Partial C1,C2,C7,C8 with wide CIs — still not main-scale |
| **Post-run checks** | Statistical plan CI requirements |

---

## Stage E: main_200

| Field | Value |
|-------|-------|
| **Purpose** | Main-scale preliminary before full 500 |
| **Dataset** | **Requires frozen main_200** (not ready) |
| **Models** | ≥4 categories |
| **Trajectories** | 200 × agents |
| **Runtime / cost** | Days · substantial USD |
| **Gates** | Main freeze · HV pilot complete · submission gate partial |
| **Configs** | `main_200_run.yaml` |
| **Claims supportable** | C1–C8 candidate if audit passes — still prefer Stage F for NeurIPS |
| **Post-run checks** | Full claim-evidence matrix refresh |

---

## Stage F: main_500 (headline benchmark)

| Field | Value |
|-------|-------|
| **Purpose** | NeurIPS headline empirical evaluation |
| **Dataset** | **Requires frozen main_v0_1_500** (not ready) |
| **Models** | ≥5 categories (frontier + budget + open/local) |
| **Trajectories** | 500 × agents |
| **Runtime / cost** | Days–weeks · $$$ |
| **Gates** | All Stage E gates + main_500 freeze + advisor sign-off |
| **Configs** | `commercial_api_main_500.yaml`, `main_500_multi_provider.yaml` |
| **Claims supportable** | C1–C8 (headline), C4 ranking, ablations C5–C6 |
| **Post-run checks** | `fill-paper-from-run` only after eligibility · camera-ready precheck |

---

## Stage G: Human validation

| Field | Value |
|-------|-------|
| **Purpose** | C3, C10 validity |
| **Dataset** | Stratified sample from Stage C–F runs |
| **Annotators** | 2 + adjudicator per item |
| **Sample sizes** | Pilot 40–60 · Main 120–200 |
| **Gates** | Real trajectories exist · protocol locked |
| **Outputs** | Annotations, agreement summary, Table 5 |
| **Claims supportable** | C3, C10 when κ thresholds met |
| **Post-run checks** | HV artifact eligibility scan |

---

## Stage H: Final paper asset export

| Field | Value |
|-------|-------|
| **Purpose** | Camera-ready tables/figures |
| **Gates** | Stage F complete · Stage G complete · submission gate pass |
| **Outputs** | Eligible tables/, figures/, LaTeX fragments |
| **Commands** | `export-paper-assets`, `fill-paper-from-run` (verified run only) |
| **Forbidden** | Export from stub/mock/tiny pilot for headline claims |

---

## Stage progression diagram

```text
A (now) → B (≤5, debug) → C (20 pilot) → D (100) → E (200) → F (500) → G (HV) → H (export)
          └─ cannot support final claims ─┘                    └─ NeurIPS headline ─┘
```

See `configs/README_NEURIPS_EXPERIMENTS.md`, `docs/MAIN_BENCHMARK_READINESS_PLAN.md`.
