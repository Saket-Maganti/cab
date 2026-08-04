# Prompt 07 — Scale-100 Confirmatory Execution


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

Require audited Compact-20, frozen scorer and protocol, validated/locked Scale-100, frozen model panel/budgets, preregistered analysis, and no model-output-based task selection.

## Goal

Execute the primary ICLR experiment.

## Recommended Design

Use roughly 100 distinct base tasks, clean/intervention, 5–7 diverse models, standard and RAAC policies, repeats based on measured stochasticity, and family-balanced analysis.

Use Kaggle T4×2 for open models and optional budget-gated provider lanes. Avoid a full Cartesian expansion if power analysis shows it is unnecessary.

## Required Analyses

Clean success, intervention success, clean-conditioned robustness, paired degradation, transitions, family and worst-family robustness, RAAC improvement, clean-performance cost, token/tool/runtime overhead, rank distributions, scorer sensitivity, and model-by-family interaction.

## Freeze

Freeze tasks, prompts, scorer, contracts, model versions, budgets, repeats, exclusions, endpoints, and analysis code before execution.

## Failure Handling

Separate infrastructure from model failures. No unplanned retries.

## Outputs

Complete trajectories, manifests, merge audit, scorer-sanity sample, primary analysis, gated paper assets, and null-result report.

## Go/No-Go

Proceed to naturalistic transfer if the benchmark remains valid, regardless of whether desired rank changes appear.
