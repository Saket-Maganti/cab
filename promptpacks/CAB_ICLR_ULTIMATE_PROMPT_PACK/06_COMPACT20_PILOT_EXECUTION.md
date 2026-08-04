# Prompt 06 — Compact-20 Pilot Execution


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


## Preconditions

Require completed human review, resolved adjudication, C10 pass, locked/hash-verified Compact-20, leakage pass, scorer/metric pass, Kaggle fixture pass, and explicit approval.

## Goal

Run a small audited pilot to validate the scientific pipeline. This is not the final ICLR experiment.

## Design

Use 3–4 model categories, standard policy, RAAC light/full, clean/intervention, low-temperature settings, and only necessary repeats. Prefer T4-compatible open models; providers are optional and budget-gated.

## Order

CPU preflight, Kaggle preflight, one-task live smoke, schema/scoring/checkpoint verification, first half, download/audit, second half, merge, offline rescore, human scorer-sanity sample, paired analysis.

## Questions

Assess intervention behaviour, scorer errors, RAAC trace validity, runtime, VRAM, failure rates, infrastructure errors, and Scale-100 go/no-go.

## Stop Conditions

Stop for hash mismatch, leakage, excessive scorer disagreement, contaminated infrastructure failures, hidden labels, merge failure, or exceeded resource cap.

## Outputs

Immutable trajectories, manifests, ledgers, merge audit, scorer packet, pilot report, calibrated runtime plan, and Scale-100 decision.

## Claim Policy

Pilot results are preliminary and cannot support headline ICLR claims.
