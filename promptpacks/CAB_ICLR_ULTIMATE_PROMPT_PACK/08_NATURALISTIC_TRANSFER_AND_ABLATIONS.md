# Prompt 08 — Naturalistic Transfer and Ablations


## Repository

`/Users/saketmaganti/Projects/causal-agent-bench`

## Hard Resource Envelope

Assume the user has only:

- MacBook Air M4, 16 GB unified memory, 512 GB storage;
- free Kaggle notebooks with two NVIDIA T4 GPUs when available;
- no A100/H100 cluster;
- no guaranteed paid API budget;
- no background compute service;
- limited storage and session duration.

Design every solution around this envelope. Prefer streaming, sharding, quantisation, resumability, compact artifacts, incremental exports, and CPU-safe validation.

## Scientific Integrity Rules

Never:

- fabricate human review;
- fabricate model trajectories;
- fabricate results, costs, timings, tables, plots, or claims;
- tune the benchmark after seeing confirmatory results;
- expose gold answers to agents;
- mark fixture, mock, stub, dry-run, or interrupted outputs as scientific evidence;
- use provider secrets found in the environment;
- commit or push unless explicitly authorised;
- silently delete user work;
- claim ICLR acceptance or submission readiness without evidence.

Always distinguish:

- `DESIGN_ONLY`
- `ENGINEERING_ONLY`
- `FIXTURE_ONLY`
- `HUMAN_INPUT_REQUIRED`
- `EXECUTION_PENDING`
- `PRELIMINARY_REAL_EVIDENCE`
- `AUDITED_REAL_EVIDENCE`
- `PAPER_ELIGIBLE_EVIDENCE`

## Required Working Style

- Inspect before modifying.
- Repair locally fixable defects instead of only reporting them.
- Preserve reversible history.
- Prefer canonical implementations over duplicate layers.
- Record exact commands and exit codes.
- Keep the public surface clean.
- Build fail-closed gates.
- Stop when the stated phase is complete.


## Goal

Establish external validity and isolate causal components of the method.

## Naturalistic Transfer

Run the validated naturalistic set on a resource-feasible subset of models.

Test whether clean success, ACRS, clean-conditioned robustness, recovery, abstention, worst-family robustness, or the full profile predicts realistic success/failure.

Use correlation with uncertainty, held-out regression, leave-one-family-out analysis, leave-one-model-out only if sample size permits, and calibration plots.

## RAAC Ablations

Compare full, light, no observation validation, no contradiction check, no alternate route, no clarification, no abstention, no final verification, retry-only, verification-only, and abstention-only.

Use a power-aware subset when necessary.

## Evaluation Ablations

Compare pooled versus paired, ACRS versus clean-conditioned robustness, automated versus human scoring, all versus validated-only, synthetic versus naturalistic, macro versus micro, and scorer-adjusted versus unadjusted.

## Dataset Ablations

Run template-held-out, domain-held-out, family-held-out, strength, and validity-confidence analyses.

## Resource Priority

Mandatory: transfer, RAAC versus standard, key RAAC ablations, scorer sensitivity.

Optional: exhaustive held-out analyses, all-model full ablations, Main expansion.

## Outputs

Transfer analysis, predictive-validity limitations, ablations, efficiency frontier, failure taxonomy, qualitative examples, and paper eligibility decisions.
