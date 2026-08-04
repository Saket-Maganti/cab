# Prompt 02 — Recovery-Aware Agent Controller Build


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

Implement a resource-efficient, model-agnostic algorithmic contribution.

Working name: **Recovery-Aware Agent Control (RAAC)**.

## Design Principles

RAAC must receive no intervention label or gold answer, use observable interaction signals only, support proprietary and open models, use bounded extra calls, improve recovery/clarification/abstention, preserve clean performance where possible, and expose auditable traces.

## State Machine

Implement plan, act, validate observation, detect anomaly, retry, alternate route, contradiction cross-check, clarification, abstention, final verification, and answer states.

Handle tool unavailable, timeout, malformed output, conflicting observations, stale memory, premature success, insufficient evidence, and impossible requests.

## Trust Signals

Build provider-neutral checks for tool errors, missing fields, inconsistent repeated outputs, contradictions, stale timestamps, impossible values, low-evidence completion, and unverifiable success signals.

## Variants

Implement:

- `RAAC_FULL`
- `RAAC_LIGHT`
- `RAAC_VERIFY_ONLY`
- `RAAC_RETRY_ONLY`
- `RAAC_ABSTAIN_ONLY`

Expose maximum extra model calls, tool calls, tokens, time, and cost.

## Baselines

Implement direct answer, standard tool use, ReAct, self-check, retry-only, verification-only, abstention-only, and oracle engineering control.

## Fairness

Provide equal-budget and practical-budget comparisons with matched prompts, tools, models, task packs, and explicit overhead.

## Testing

Fixture-test tool failure recovery, contradictions, stale memory, clarification, valid and false abstention, premature stopping, infinite retry prevention, deterministic traces, and clean no-op behaviour.

## Integration

Integrate into run manifests, Kaggle notebooks, provider/open adapters, result schemas, analysis, and ablation configs.

## Outputs

- controller code and configs;
- fixtures and tests;
- `docs/RAAC_METHOD.md`;
- `docs/RAAC_FAIRNESS_AND_BUDGET_POLICY.md`;
- `experiments/RAAC_ABLATION_PLAN.md`;
- paper-ready pseudocode without results.

## Acceptance Gate

RAAC must be independently useful, bounded, auditable, and benchmark-label blind.
