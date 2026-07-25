# Prompt 6 — main_500 Multi-Provider Benchmark, Ablations, and Full Evidence Generation

You are working in the Causal Agent Bench repository.

You are Cursor Composer acting as a NeurIPS benchmark execution lead, statistical analysis lead, artifact release engineer, and claim-evidence auditor.

## Mission

Produce the full empirical evidence needed for a serious NeurIPS Evaluations/Datasets submission.

This is the expensive, real benchmark stage.

## Starting assumptions

- main_200 completed or its blockers were resolved.
- scorer calibration is acceptable.
- gold-output policy is resolved for main benchmark.
- human validation pilot exists or is in progress.
- main_v0_1_500 / main_500 is not yet ready.
- Budget and provider approval must be explicit.
- This stage may cost real money.

## Absolute rules

Do not:

- run main_500 without explicit budget/live approval
- exceed budget
- include oracle/mock in model rankings
- fabricate results
- promote claims without evidence
- run if main_500 quality gates fail
- ignore invalid human validation
- hide incomplete runs
- manually mark paper assets eligible

Allowed:

- freeze main_500 only after gates pass
- run multi-provider benchmark after approval
- run ablations after approval
- run statistical analysis
- promote claims only through claim-evidence matrix
- generate paper assets only from eligible runs

## Tasks

### 1. main_500 readiness audit

Inspect:

- `data/processed/main_v0_1_500`
- main benchmark readiness plan
- leakage reports
- split metadata
- high-risk review queue
- gold-output triage
- human validation status
- scorer calibration
- main_200 lessons

Create `reports/MAIN500_READINESS_AUDIT.md`.

### 2. Resolve main_500 blockers

Fix or review:

- split/heldout metadata
- leakage/manual review clusters
- high-risk intervention queue for selected main families
- gold-output policy and warnings
- duplicate/near-duplicate issues
- dataset card metadata
- benchmark manifest

If blockers remain, stop.

### 3. Freeze main_500

Create:

- `data/frozen/main_500_v1.0/`
- dataset manifest
- hashes
- split metadata
- changelog
- benchmark card
- release notes

### 4. Multi-provider model plan

Minimum target:

- ≥5 models
- ≥3 provider/model categories
- at least one frontier category
- at least one budget category
- optionally one open/local category if feasible
- oracle/mock excluded from rankings

Create `configs/main500_multi_provider_APPROVED.yaml` only with budget/live approval.

### 5. Run full benchmark

Only after all gates pass:

- run full main_500 benchmark
- monitor cost
- record run dirs
- stop on failures/cost cap
- do not silently retry without metadata

### 6. Ablation runs

Run approved ablations:

- no-tool baseline
- random-tool baseline
- memory-blind
- contradiction-blind
- recovery-disabled
- no-final-verifier
- tool-error ablation
- intervention-family ablation
- metric ablation

If budget insufficient, run prioritized subset and document missing ablations.

### 7. Statistical analysis

Execute:

- paired clean/intervention comparisons
- bootstrap CIs
- per-family analysis
- model ranking stability
- Spearman correlation clean vs ACRS
- effect sizes
- multiple comparison caution
- cost/runtime
- scorer sensitivity
- template-level effective sample size analysis

Create:

- `reports/MAIN500_STATISTICAL_ANALYSIS.md`
- `reports/MAIN500_RESULTS_SUMMARY.md`
- `reports/MODEL_RANKING_STABILITY.md`
- `reports/ABLATION_RESULTS.md`
- `reports/SCORER_SENSITIVITY_ANALYSIS.md`
- `reports/TEMPLATE_EFFECTIVE_SAMPLE_SIZE.md`

### 8. Claim promotion

Promote claims only if evidence supports them.

Potential claims:

- C1: clean success overstates robustness
- C2: intervention family breakdown
- C4: model rankings change under intervention
- C5–C8: ablations/diagnostics if evidence supports them
- C3/C10 only with human validation

Every promoted claim must link:

- run dirs
- tables/figures
- statistical report
- validation artifacts if required

### 9. Paper asset generation

Generate only eligible assets:

- tables
- figures
- CSV summaries
- JSON summaries
- appendix artifacts

Run asset eligibility scanner.

Do not mark placeholders eligible.

### 10. Tests

Add/update tests for:

- main_500 frozen manifest
- multi-provider minimum requirements
- oracle/mock exclusion
- incomplete run exclusion
- claim promotion requires evidence
- paper asset eligibility requires provider runs
- statistical analysis includes CIs
- ablation results cannot be fabricated

## Final response format

# main_500 Multi-Provider Benchmark Report

## 1. Executive Summary
## 2. main_500 Readiness
## 3. Dataset Freeze
## 4. Provider/Model Set
## 5. Benchmark Runs
## 6. Ablation Runs
## 7. Statistical Analysis
## 8. Human Validation Dependencies
## 9. Claim Promotion
## 10. Paper Assets
## 11. Tests Added/Updated
## 12. Commands Run
## 13. Commands Not Run
## 14. Current Evidence State
## 15. Remaining NeurIPS Blockers
## 16. Next Step

Success condition:

- main_500 results exist and are audited, or blockers are explicit
- claims promoted only with evidence
- eligible paper assets generated only from real runs
