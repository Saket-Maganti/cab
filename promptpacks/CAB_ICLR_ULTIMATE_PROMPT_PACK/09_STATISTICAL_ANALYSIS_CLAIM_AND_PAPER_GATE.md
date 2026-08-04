# Prompt 09 — Statistical Analysis, Claim Gate, and Evidence Promotion


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

Convert audited trajectories into defensible evidence.

## Evidence Ingestion

Accept only runs passing hashes, completion, merge integrity, scorer versioning, human requirements, evidence classification, and raw trajectory preservation.

## Primary Analysis

Compute paired outcomes, clean-conditioned robustness, transitions, family macro/micro, worst-family, RAAC effects, clean trade-off, rank distributions, uncertainty, and transfer.

## Statistical Models

Use task-cluster bootstrap, family-stratified bootstrap, paired binary tests, mixed-effects logistic regression where justified, interactions, multiplicity correction, effect sizes, and scorer-error sensitivity.

## Rank Claims

Require rank probability, pairwise superiority probability, uncertainty, task-composition sensitivity, and scorer-disagreement sensitivity.

## Claim Ledger

Store claim ID, wording, evidence paths, study, effect, interval, checks, limitations, and state: unsupported, preliminary, audited, paper eligible, or rejected.

## Null Results

Report honestly if clean success predicts robustness or RAAC fails. Do not search indefinitely for favourable subsets.

## Paper Asset Gate

Every asset must record study ID, code revision, data hash, scorer version, and command.

## Outputs

Main analysis, claim ledger, robustness checks, null report, asset manifest, and ICLR go/no-go recommendation.
