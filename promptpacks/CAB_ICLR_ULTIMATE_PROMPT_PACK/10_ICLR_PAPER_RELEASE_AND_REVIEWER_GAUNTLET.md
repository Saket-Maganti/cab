# Prompt 10 — ICLR Paper, Release, and Reviewer Gauntlet


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

No final empirical claims before audited evidence.

## Goal

Produce a concise method-first ICLR paper and anonymous reproducibility package.

## Framing

The paper identity is intervention validity + paired robustness inference + RAAC + naturalistic transfer. The benchmark is the testbed.

## Structure

1. motivation and thesis;
2. problem setup;
3. intervention validity;
4. paired inference;
5. RAAC;
6. benchmark/human validation;
7. Scale-100 results;
8. transfer/ablations;
9. limitations/conclusion.

Keep infrastructure in appendices.

## Figures

Use eligible evidence only for motivation, framework, clean versus robust rank, transitions, family heatmap, RAAC effect/cost, transfer, and scorer sanity.

## Abstracts

Maintain no-evidence, pilot, confirmatory, and final versions.

## Reproducibility

Include anonymous repo, environment lock, hashes, prompts, tools, model snapshots, manifests, trajectories where permitted, scorer, analysis, seeds, CPU reproduction, Kaggle notebooks, cards, licences, ethics, and limitations.

## Reviewer Gauntlet

Simulate benchmark, causal-methodology, statistics, agent-systems, reproducibility, and sceptical generalist reviewers. Each must score, state confidence, identify fatal concerns, required experiments, wording issues, and rebuttal difficulty.

## Submission Gate

ICLR requires strong validity, scorer agreement, Scale-100, diverse models, transfer, substantive RAAC or equivalent method value, sensitivity robustness, and novelty beyond infrastructure.

Otherwise recommend NeurIPS Datasets & Benchmarks, DMLR, or further experiments.

## Outputs

Paper, supplement, anonymous artifact, reproducibility checklist, reviewer simulations, rebuttal risk map, venue decision, and final handoff.
