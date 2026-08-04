# Prompt 03 — Intervention Validity and Human Study Build


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

Make intervention validation rigorous enough for an ICLR methods paper. Do not perform or fabricate review.

## Review Dimensions

Create independent packets for task clarity, clean gold correctness, intended-factor presence, goal preservation, invariance preservation, solvability, answer-contract correctness, scorer compatibility, realism, ambiguity, and exclusion.

## Reviewer Structure

Design for two independent reviewers per Compact-20 item, two or three for Scale-100 where feasible, separate adjudication, blinded model identity/output, qualification examples, expertise documentation, conflict declarations, and privacy-safe reviewer IDs.

## Agreement

Implement raw agreement, Cohen's kappa, Krippendorff's alpha where appropriate, prevalence-sensitive diagnostics, adjudication rate, exclusion rate, family validity, and reviewer confidence. Block analysis when data is insufficient.

## Manipulation Checks

Each intervention must verify the intended condition occurred. Implement deterministic checks where possible and human checks where needed.

## C10

C10 must require genuine rows, valid reviewer IDs, full coverage, thresholds, resolved adjudication, and rejection of proxy/AI/header-only files.

## Human Time Plan

Optimise for limited resources using Compact-20 first, reviewer training, time-per-item estimates, adjudication reserve, and staged Scale-100 review without compromising validity.

## Ethics

Prepare consent, data handling, compensation disclosure, expertise disclosure, privacy, and limitations.

## Outputs

- blank review packets;
- reviewer guide;
- qualification examples;
- adjudication form;
- validators;
- agreement code;
- C10 engine;
- `docs/ICLR_HUMAN_VALIDATION_PROTOCOL.md`;
- `docs/HUMAN_REVIEW_RESOURCE_PLAN.md`.

## Acceptance Gate

No scientific run before genuine review, adjudication, C10, leakage checks, and slice lock.
