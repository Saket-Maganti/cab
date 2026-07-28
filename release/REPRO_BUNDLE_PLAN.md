# Reproducibility Bundle Plan

Generated: `2026-07-28T04:30:02.531093+00:00`

## Included (future public release)

### source_code
- `src/causal_agent_bench/`
- `pyproject.toml`
- `Makefile`

### configs
- `configs/5model_100task_TEMPLATE_NOT_APPROVED.yaml`
- `configs/ablation_interventions.yaml`
- `configs/ablation_matrix_local_stub.yaml`
- `configs/ablations/abstention_aware_TEMPLATE_NOT_APPROVED.yaml`
- `configs/ablations/action_protocol_local_stub.yaml`
- `configs/ablations/contradiction_resolution_local_stub.yaml`
- `configs/ablations/direct_answer_TEMPLATE_NOT_APPROVED.yaml`
- `configs/ablations/direct_vs_react_local_stub.yaml`
- `configs/ablations/explicit_plan_local_stub.yaml`
- `configs/ablations/function_calling_TEMPLATE_NOT_APPROVED.yaml`
- `configs/ablations/memory_verification_local_stub.yaml`
- `configs/ablations/oracle_stub_engineering_TEMPLATE_NOT_APPROVED.yaml`
- `configs/ablations/react_tool_TEMPLATE_NOT_APPROVED.yaml`
- `configs/ablations/recovery_aware_TEMPLATE_NOT_APPROVED.yaml`
- `configs/ablations/self_check_TEMPLATE_NOT_APPROVED.yaml`
- ... 90 more

### synthetic_datasets
- `data/frozen/pilot_v0.1/`
- `data/sample/`

### benchmark_specs
- `benchmark_specs/TASK_TEMPLATE_REGISTRY.md`
- `benchmark_specs/causal_agent_bench_v0.md`
- `benchmark_specs/generation_rules.md`
- `benchmark_specs/intervention_families.yaml`
- `benchmark_specs/task_domains.yaml`
- `benchmark_specs/task_template_registry.json`

### docs
- `docs/ABLATIONS.md`
- `docs/ACRS_FORMALIZATION_AND_LIMITATIONS.md`
- `docs/ACRS_METRIC_SUITE_V2.md`
- `docs/ADVISOR_REVIEW_GUIDE.md`
- `docs/ANALYSIS_GUIDE.md`
- `docs/BASELINE_AGENTS.md`
- `docs/BASELINE_AGENT_DEFINITIONS.md`
- `docs/BATCH_RUNS.md`
- `docs/BENCHMARK_ARTIFACT_MANIFEST.md`
- `docs/BENCHMARK_CARD.md`
- `docs/BENCHMARK_TAXONOMY.md`
- `docs/BENCHMARK_THEORY_OF_CHANGE.md`
- `docs/C10_INTERVENTION_ISOLATION_VALIDATION_PROTOCOL.md`
- `docs/CAB_FOCUSED_PROJECT_SURFACE.md`
- `docs/CLAIM_ARCHITECTURE.md`
- ... 25 more

### paper
- `paper/01_introduction_v9.md`
- `paper/02_benchmark_v9.md`
- `paper/02_related_work_v9.md`
- `paper/03_experiments_v9.md`
- `paper/04_results_v9.md`
- `paper/05_limitations_v9.md`
- `paper/06_ethics_reproducibility_v9.md`
- `paper/CLAIM_SAFE_ABSTRACT_TEMPLATES.md`
- `paper/COMPACT_EMPIRICAL_PAPER_BLUEPRINT.md`
- `paper/CONTRIBUTION_MAP.md`
- `paper/DMLR_OUTLINE_V2.md`
- `paper/EVIDENCE_GAP_MAP.md`
- `paper/FAILURE_GALLERY_COMPACT20.md`
- `paper/FIGURE_CAPTIONS_COMPACT20_REAL.md`
- `paper/FIGURE_TABLE_SPEC_NO_RUN.md`
- ... 45 more

### analysis_scripts
- `scripts/reproduce_artifact.py`
- `scripts/run_fast_checks.py`
- `scripts/check_submission_readiness.py`

### release_metadata
- `release/release_manifest.json`
- `CITATION.cff`
- `LICENSE`

## Excluded

### Sensitive
- `.env`
- `credentials.json`
- `**/*api_key*`
- `**/*secret*`

### Large
- `results/**`
- `figures/*.png`
- `figures/*.pdf`
- `data/processed/main_v0_1_500/**`

### General patterns
- `.env`
- `.env.*`
- `**/secrets/**`
- `results/**/trajectories.jsonl`
- `results/**/INCOMPLETE_RUN.json`
- `audits/full_verification/**`
- `**/__pycache__/**`
- `**/.pytest_cache/**`
- `**/*.pyc`

## Repro commands

```bash
pip install -e '.[dev]'
```
```bash
make fast-check
```
```bash
python3 scripts/reproduce_artifact.py --all-deterministic
```
```bash
python3 -m causal_agent_bench audit-interventions --benchmark-dir data/frozen/pilot_v0.1
```
```bash
python3 scripts/audit_intervention_isolation.py --dataset data/frozen/pilot_v0.1/instances.jsonl
```

## Required future artifacts

- Complete provider pilot run metadata (not trajectories in bundle)
- Human validation annotation export
- Frozen main_v0.1 dataset manifest
- Updated claim ledger with supported claims only after main experiment
