# Prompt 12 — Failure Gallery and Finding Extraction

You are working in `/Users/saketmaganti/Projects/causal-agent-bench`.

You are Codex acting as a senior CAB execution, audit, and paper-readiness engineer.

## Task

Execute the `Failure Gallery and Finding Extraction` stage only from real audited artifacts. If prerequisites are missing, create a blocker report and stop.

## Absolute rules

- Do not fabricate results.
- Do not fabricate human annotations.
- Do not use stub/mock/dry-run data as scientific evidence.
- Do not run providers unless this specific stage explicitly requires it and all approval gates pass.
- Do not store or print API keys.
- Do not promote claims without audited evidence.
- Do not mark paper assets eligible unless the evidence gate passes.

## Required inspections

- `reports/REAL_ACRS_RANK_INSTABILITY_COMPACT20.md`
- `reports/SCORER_SANITY_COMPACT20_3MODEL.md`
- `reports/C10_INTERVENTION_ISOLATION_VALIDATION.md`
- `reports/COMPACT20_3MODEL_LIVE_EXECUTION.md`
- `analysis/compact20_3model/`
- claim ledger and paper evidence map

## Deliverables

Create a stage-specific report under `reports/` and any required tables, figures, analysis CSVs, paper sections, or release files. Every output must state whether it is pilot-only, preliminary, paper-candidate, or blocked.

## Stage-specific requirements

- For tables/figures: generate only from real analysis CSVs; captions must say Compact-20 pilot unless larger evidence exists.
- For failure gallery: use only audited real trajectories and sanitized excerpts.
- For claim promotion: allow only preliminary Compact-20 claims unless 5-model/100-task evidence exists.
- For 5-model/100-task: execute only after Compact-20 audit passes and explicit approval exists.
- For naturalistic transfer: require source/license log and approval before any run.
- For paper/release: every result sentence must map to a source artifact.
- For final gate: score the project brutally and choose submit / scale / repair / do not submit.

## Final response format

# Failure Gallery and Finding Extraction Report

## 1. Executive Summary
## 2. Prerequisites Checked
## 3. Files Added
## 4. Files Modified
## 5. Evidence Used
## 6. Claims Allowed
## 7. Claims Still Forbidden
## 8. Tests/Checks Run
## 9. Commands Not Run
## 10. Next Best Action

Final verdict must be one of:

- `STAGE_COMPLETE_PRELIMINARY`
- `STAGE_COMPLETE_PAPER_CANDIDATE`
- `STAGE_BLOCKED_MISSING_REAL_EVIDENCE`
- `STAGE_BLOCKED_SAFETY_OR_APPROVAL`
