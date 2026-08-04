# Prompt 01 — ICLR Contribution and Theory Build


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

Strengthen CAB from a benchmark package into a general evaluation methodology suitable for an ICLR paper.

## Formal Problem Definition

Define base task distribution, clean condition, intervention operator, intended factor, preserved invariances, answer-contract transformation, agent policy, outcome variables, scorer, matched unit, and robustness profile.

Separate controlled intervention, causal motivation, and formal causal identification.

## Intervention Validity Profile

Design and implement a profile containing manipulation success, goal preservation, invariance preservation, solvability, answer-contract validity, scorer compatibility, realism, ambiguity, reviewer agreement, and exclusion reason.

## Paired Robustness Framework

Formalise clean-conditioned robustness, paired absolute degradation, transition probabilities, recovery, abstention, family macro robustness, worst-family robustness, and rank uncertainty.

Add property tests for identity, monotonicity where appropriate, denominator instability, missing pairs, repeated clean runs, clustering, ties, and scorer perturbations.

## Optional Formal Result

Investigate only genuinely useful propositions, such as:

- bias of pooled versus matched robustness;
- instability of ratio metrics under low clean success;
- relationships between transition probabilities and degradation;
- rank reversal under intervention-family mixture shift.

Include a result only with correct assumptions and a complete proof.

## Research Questions and Hypotheses

Freeze RQ1–RQ10 covering competence, rankings, failure heterogeneity, recovery, abstention, validity, scorer reliability, transfer, method improvement, and scale.

For each hypothesis, document metric, study, evidence threshold, null interpretation, and allowed wording.

## Reviewer Attack Map

Address “only a benchmark”, “not causal”, “synthetic”, “trivial ratio”, “scorer artifact”, “more compute”, “unstable ranking”, “obvious interventions”, “post-hoc tuning”, and “weak transfer”.

## Outputs

- `docs/ICLR_FORMAL_PROBLEM_SETUP.md`
- `docs/INTERVENTION_VALIDITY_PROFILE.md`
- `docs/PAIRED_ROBUSTNESS_INFERENCE.md`
- `docs/ICLR_RESEARCH_QUESTIONS_AND_HYPOTHESES.md`
- `docs/ICLR_NULL_RESULT_POLICY.md`
- `reviews/ICLR_REVIEWER_ATTACK_MATRIX.md`
- tested code for any new estimators.

## Acceptance Gate

The paper must be describable as a methodology contribution rather than merely a task collection.
