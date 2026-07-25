# Prompt 5 — main_200 Readiness, Freeze, Multi-Model Pilot Benchmark

You are working in the Causal Agent Bench repository.

You are Cursor Composer acting as a benchmark release engineer, dataset validity lead, provider experiment manager, and statistical analysis reviewer.

## Mission

Move from tiny pilot to a credible `main_200` intermediate benchmark.

This stage should produce Findings/TMLR/COLM-workshop-grade evidence if successful, but still may not be enough for NeurIPS final.

## Starting assumptions

- Tiny provider pilot has passed post-run audit.
- Scorer calibration and gold policy have been addressed.
- Human validation pilot is started or completed.
- main_200 is currently not ready.
- Provider budget approval exists for this stage.
- No final NeurIPS claims should be promoted until evidence is sufficient.

## Absolute rules

Do not:

- run main_200 provider benchmark without budget/live approval
- run if gold-output blockers remain unresolved for main_200
- run if high-risk intervention review blocks main_200
- fabricate results
- promote claims without linked run dirs and statistical analysis
- use oracle/mock as model evidence
- hide failed runs
- run beyond approved budget

Allowed:

- repair split metadata
- create a new frozen main_200 candidate
- run no-run reports
- run provider benchmark only after approval
- run statistical analysis on eligible provider runs
- update claim ledger only through evidence gates

## Tasks

### 1. main_200 readiness audit

Inspect:

- `docs/MAIN_BENCHMARK_READINESS_PLAN.md`
- benchmark quality reports
- split metadata reports
- leakage reports
- gold-output triage reports
- high-risk intervention queue
- human validation reports
- data/processed/main_200
- data/frozen/

Determine exact blockers.

Create `reports/MAIN200_READINESS_AUDIT.md`.

### 2. Fix main_200 blockers

Fix only safe, reviewable issues:

- split metadata
- heldout split metadata
- duplicate IDs
- expected subset overlap calibration
- non-frozen processed gold policy fixes
- high-risk review annotations
- benchmark card metadata

Do not auto-edit frozen data.

### 3. Freeze main_200 candidate

Only if blockers clear:

- create a versioned frozen main_200 dataset
- include hashes
- include manifest
- include dataset card
- include split policy
- include changelog
- include release notes

Create:

- `data/frozen/main_200_v0.1/`
- `docs/MAIN200_FREEZE_REPORT.md`

If blockers remain, stop and report.

### 4. Provider config for main_200

Create config only with approval:

- `configs/main200_PROVIDER_APPROVED.yaml`

Requirements:

- approval metadata
- provider/model list
- budget caps
- trajectory caps
- stop conditions
- `allow_paid_calls: true` only if live approval exists
- no API keys in YAML

### 5. Run main_200 benchmark

Only after live gate passes:

- run ≥3 models if budget allows
- record all run dirs
- monitor cost and failures
- stop on cap breach

Do not run main_500.

### 6. Post-run audit

For each run:

- check incomplete markers
- check provider classification
- check trajectories
- check scorer sanity sample
- run evidence safety
- run run-health
- run paper asset eligibility
- run claim-evidence matrix

### 7. Statistical analysis

Generate:

- clean vs intervention success
- ACRS
- per-intervention breakdown
- confidence intervals
- model ranking preliminary analysis
- failure mode counts
- cost/runtime table

Mark all claims as preliminary unless thresholds pass.

Create:

- `reports/MAIN200_STATISTICAL_ANALYSIS.md`
- `reports/MAIN200_RESULTS_SUMMARY.md`

### 8. Claim gate

Possible candidate claims after main_200:

- C1 preliminary
- C2 preliminary
- C4 preliminary if ≥3 models and enough variance
- C3/C10 only if human validation exists

Do not mark NeurIPS final-ready.

### 9. Tests

Add/update tests for:

- main_200 freeze manifest
- main_200 requires gold/high-risk gates
- provider config requires budget approval
- oracle/mock excluded
- incomplete runs excluded
- main_200 claims remain preliminary

## Final response format

# main_200 Readiness and Benchmark Report

## 1. Executive Summary
## 2. main_200 Readiness Audit
## 3. Fixes Applied
## 4. Freeze Status
## 5. Provider Config
## 6. Run Summary
## 7. Post-Run Audit
## 8. Statistical Results
## 9. Claim Gate
## 10. Tests Added/Updated
## 11. Commands Run
## 12. Commands Not Run
## 13. Evidence State
## 14. Remaining Blockers Before main_500
## 15. Next Step

Success condition:

- main_200 is frozen and/or blockers reported
- if run, provider-backed evidence is audited
- claims remain appropriately preliminary
