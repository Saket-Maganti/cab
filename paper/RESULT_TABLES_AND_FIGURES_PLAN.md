# Result Tables and Figures Plan

**Global banner for all empirical assets:**

> **BLOCKED UNTIL ELIGIBLE PROVIDER RUNS EXIST**

No table or figure below may be cited as scientific evidence until linked to a paper-eligible run with eligible `.meta.json` sidecars.

---

## Tables

| ID | Name | Claim(s) | Data source | Status |
|----|------|----------|-------------|--------|
| T1 | Dataset statistics | Method | `table1_benchmark_statistics` | Engineering-only OK for draft |
| T2 | Intervention taxonomy summary | C10 method | New static table from taxonomy | Method-only draft OK |
| T3 | Main model results (clean + intervention + ACRS) | C1,C4 | `table2_main_agent_performance` | **BLOCKED UNTIL ELIGIBLE PROVIDER RUNS EXIST** |
| T4 | Clean vs intervention success (paired) | C1 | `paired_clean_vs_intervention` | **BLOCKED UNTIL ELIGIBLE PROVIDER RUNS EXIST** |
| T5 | ACRS ranking table | C4 | `table2` ACRS columns | **BLOCKED UNTIL ELIGIBLE PROVIDER RUNS EXIST** |
| T6 | Per-intervention-family robustness | C2 | `table3_intervention_family_performance` | **BLOCKED UNTIL ELIGIBLE PROVIDER RUNS EXIST** |
| T7 | Failure taxonomy counts | C7,C8 | Derived from trajectories | **BLOCKED UNTIL ELIGIBLE PROVIDER RUNS EXIST** |
| T8 | Human validation agreement | C3,C10 | `table5_human_validation_agreement` | **BLOCKED UNTIL ELIGIBLE PROVIDER RUNS EXIST** |
| T9 | Ablation results | C5,C6 | `table4_ablation_results` | **BLOCKED UNTIL ELIGIBLE PROVIDER RUNS EXIST** |
| T10 | Cost / runtime | Ethics | Run metadata aggregation | **BLOCKED UNTIL ELIGIBLE PROVIDER RUNS EXIST** |
| T11 | Mini-study transfer | Method+empirical | Benchmark design §3 | **BLOCKED UNTIL ELIGIBLE PROVIDER RUNS EXIST** |

---

## Figures

| ID | Name | Claim(s) | File (planned) | Status |
|----|------|----------|----------------|--------|
| F1 | Benchmark overview | Method | `figure1_benchmark_overview` | Placeholder scaffold OK |
| F2 | Clean/intervention pairing | Method | `figure2_intervention_pairing` | Method scaffold OK |
| F3 | Clean vs intervention success bars | C1 | `figure2_clean_vs_intervention_success` | **BLOCKED UNTIL ELIGIBLE PROVIDER RUNS EXIST** |
| F4 | Intervention-family breakdown | C2 | `figure3_intervention_family_breakdown` | **BLOCKED UNTIL ELIGIBLE PROVIDER RUNS EXIST** |
| F5 | ACRS / ranking instability | C4 | `figure4_ranking_instability` | **BLOCKED UNTIL ELIGIBLE PROVIDER RUNS EXIST** |
| F6 | Failure-mode distribution | C7,C8 | `figure5_failure_mode_distribution` | **BLOCKED UNTIL ELIGIBLE PROVIDER RUNS EXIST** |
| F7 | Trajectory vs final disagreement | C3 | `figure6_trajectory_final_disagreement` | **BLOCKED UNTIL ELIGIBLE PROVIDER RUNS EXIST** |
| F8 | Leaderboard (clean vs ACRS) | C4 | New export | **BLOCKED UNTIL ELIGIBLE PROVIDER RUNS EXIST** |
| F9 | Robustness heatmap (model × family) | C1,C2 | New export | **BLOCKED UNTIL ELIGIBLE PROVIDER RUNS EXIST** |
| F10 | Clean/intervention delta plot | C1 | New export | **BLOCKED UNTIL ELIGIBLE PROVIDER RUNS EXIST** |
| F11 | Evidence lifecycle / governance | C9 artifact | `method_figures/evidence_lifecycle.mmd` | Method-only OK |

---

## Export workflow (Stage H only)

```bash
# Only after paper-eligible run verified:
python3 -m causal_agent_bench export-paper-assets --run-dir results/<eligible_run>
python3 scripts/fill_paper_from_run.py --run-dir results/<eligible_run>
```

**Forbidden:** Filling T3–T10, F3–F10 from stub/mock/tiny pilot.

---

## Placeholder metadata requirements

Each eligible asset needs sidecar `.meta.json`:

- `eligible_for_paper_claims: true`
- `scientific_evidence: true`
- `run_dir`, `config_hash`, `dataset_version`
- `placeholder: false`

See `reports/paper_asset_eligibility.md`.
