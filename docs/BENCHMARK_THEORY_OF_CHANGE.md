# Benchmark Theory of Change

Status: no-execution methodology upgrade. This document is not evidence.

## Core Claim Shape

CAB studies whether success-only evaluation can hide brittleness in tool-using LLM agents. The benchmark pairs a clean task with a controlled intervention task that preserves the high-level goal while changing one stress factor, such as tool availability, tool reliability, memory correctness, observation consistency, or ambiguity. A run becomes scientific evidence only after provider-backed trajectories, scorer sanity checks, human review, and C10 intervention-isolation validation exist.

## Definitions

- Clean task: the unperturbed task instance with a user goal, available tools, hidden ground truth, success criteria, and expected evidence.
- Intervention task: the paired instance produced by changing one intended factor while preserving the user goal and the non-target task state.
- Intervention family: a reusable class of perturbations with shared target factor, invariants, expected failure mode, and review questions.
- Goal preservation: the clean and intervention tasks still ask for the same practical outcome, even when the valid response may change to a limitation, uncertainty statement, or recovery behavior.
- Intervention isolation: only the intended factor changes; unrelated task difficulty, hidden answer, tool schema, and scoring policy do not drift.
- Robustness degradation: the paired loss in success or trajectory quality under intervention relative to clean.
- ACRS: Agent Causal Robustness Score, defined as intervention success divided by clean success when clean success is nonzero.

## Theory of Change

1. Clean success measures whether an agent can solve nominal tool-use tasks.
2. Controlled interventions test whether the same apparent skill survives targeted stress.
3. Paired clean/intervention design reduces cross-task confounding compared with unrelated stress-test tasks.
4. Per-family reporting identifies which operational factors create brittleness.
5. Ranking by clean success and ranking by robustness may diverge; if validated and powered, that divergence is the scientific hook.

## What CAB Can Support After Evidence Exists

- Agents can be compared on clean success, intervention success, ACRS, degradation, and per-family failure profiles.
- Ranking instability can be reported when enough non-oracle agents and paired tasks exist.
- Null results can be useful: they may show a family is too weak, a scorer is insensitive, or a model class is robust to that stressor.

## What CAB Cannot Yet Prove

- It cannot claim causal inference until C10 human isolation validation and assumptions pass.
- It cannot claim real-world transfer from scaffold or synthetic tasks alone.
- It cannot claim provider or model ranking without provider-backed trajectories.
- It cannot claim human agreement, paper eligibility, or ACRS findings from proxy labels, mock runs, or dry-runs.

## Why Clean Success Alone Is Insufficient

Clean success can reward agents that follow the happy path but fail after tool errors, stale memory, conflicting evidence, or ambiguous instructions. Operationally, a brittle agent with high clean success may be less deployable than a slightly weaker clean agent that recovers, verifies, or abstains when evidence is unsafe.

## When Rank Instability Is Meaningful

Rank instability is meaningful only when:

- the same task pairs are used for all compared agents,
- each agent has enough paired trajectories,
- scorer validity and human review gates pass,
- uncertainty intervals are reported, and
- tied ranks and incomplete runs are handled conservatively.

Before that, rank-shift analysis is a design target, not a result.
