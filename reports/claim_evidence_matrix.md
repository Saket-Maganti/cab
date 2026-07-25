# Claim–evidence matrix

Generated: 2026-05-20T08:27:04.490699+00:00

Eligible scientific runs in index: 0

Conservative matrix: C1–C8 and C10 require verified non-mock complete provider/main evidence.

## C1: Clean success overestimates robust competence under intervention.
- Status: **planned** (ledger: `planned`)
- Blocking: Run final non-oracle pilot, Compute uncertainty, Audit task/intervention validity
- Eligible artifacts: (none)
- Ineligible: tables/table2_main_agent_performance.csv, figures/figure2_clean_vs_intervention_success.png
- May appear in: limitations/future_work_only

## C2: Tool failure and memory corruption expose hidden weaknesses.
- Status: **planned** (ledger: `planned`)
- Blocking: Run family-balanced benchmark, Add memory-corruption audit subset, No verified complete provider/main scientific evidence
- Eligible artifacts: (none)
- Ineligible: figures/figure3_intervention_family_breakdown.png, tables/table3_intervention_family_performance.csv
- May appear in: limitations/future_work_only

## C3: Trajectory metrics detect failures missed by final-answer scoring.
- Status: **planned** (ledger: `planned`)
- Blocking: Run human validation subset, Calibrate deterministic trajectory diagnostics, No verified complete provider/main scientific evidence
- Eligible artifacts: (none)
- Ineligible: figures/figure6_trajectory_final_disagreement.png, results/<run_dir>/error_cases/ (missing)
- May appear in: limitations/future_work_only

## C4: ACRS changes model rankings relative to clean success.
- Status: **planned** (ledger: `planned`)
- Blocking: Run enough agents/models for ranking analysis, No verified complete provider/main scientific evidence
- Eligible artifacts: (none)
- Ineligible: figures/figure4_ranking_instability.png, tables/table2_main_agent_performance.csv
- May appear in: limitations/future_work_only

## C5: Recovery ability is separable from planning ability.
- Status: **planned** (ledger: `planned`)
- Blocking: Define planning proxy, Run scaffold ablation, No verified complete provider/main scientific evidence
- Eligible artifacts: (none)
- Ineligible: tables/table2_main_agent_performance.csv, tables/table4_ablation_results.csv
- May appear in: limitations/future_work_only

## C6: Simple self-checking improves some intervention families but not all.
- Status: **planned** (ledger: `planned`)
- Blocking: Implement scaffold conditions, Run ablation config, No verified complete provider/main scientific evidence
- Eligible artifacts: (none)
- Ineligible: tables/table4_ablation_results.csv
- May appear in: limitations/future_work_only

## C7: Some agents overuse tools even when unnecessary.
- Status: **planned** (ledger: `planned`)
- Blocking: Run irrelevant-tools family with non-oracle agents, No verified complete provider/main scientific evidence
- Eligible artifacts: (none)
- Ineligible: tables/table2_main_agent_performance.csv, figures/figure5_failure_mode_distribution.png
- May appear in: limitations/future_work_only

## C8: Some agents stop prematurely under misleading success signals.
- Status: **planned** (ledger: `planned`)
- Blocking: Run premature-success-signal family, Audit examples, No verified complete provider/main scientific evidence
- Eligible artifacts: (none)
- Ineligible: figures/figure5_failure_mode_distribution.png, results/<run_dir>/error_cases/premature_stopping.md (missing)
- May appear in: limitations/future_work_only

## C9: CausalAgentBench smoke tests are reproducible without paid services.
- Status: **engineering_only** (ledger: `engineering_only`)
- Blocking: Repeat in clean CI environment, Run real provider-backed pilot before using non-oracle LLM observations as scientific evidence, No verified complete provider/main scientific evidence
- Eligible artifacts: (none)
- Ineligible: docs/REPRODUCIBILITY.md, docs/RUNNING_EXPERIMENTS.md
- May appear in: introduction, limitations/future_work_only, ethics/reproducibility

## C10: Controlled interventions isolate intended skill components.
- Status: **planned** (ledger: `planned`)
- Blocking: Create annotation protocol, Run expert audit, No verified complete provider/main scientific evidence
- Eligible artifacts: (none)
- Ineligible: tables/table5_human_validation_agreement.csv, docs/INTERVENTIONS.md
- May appear in: limitations/future_work_only
