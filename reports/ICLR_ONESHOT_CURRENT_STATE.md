# ICLR One-Shot Current State

Captured provider-free on 2026-07-28 after implementation and final local
validation, before the publication commit.

## Verified state

The CAB ICLR pre-execution build is complete. The unified gate reaches:

```text
HUMAN_VALIDATION_REQUIRED
build_complete: true
```

This is the intended no-execution ceiling. Scientific execution, slice
locking, paper-result generation, and empirical claims remain blocked.

## Prompt 1 blockers

The initial four-test reproduction failed in 64.03 seconds because publicly
exposed held-out artifacts still carried protected scientific roles, one test
duplicated an obsolete state list, and the release inventory/hash were stale.

The final state repairs those failures:

- exposed v1 Scale, naturalistic, Main, and held-out material is permanently
  public-development or `CONTAMINATED_NOT_CONFIRMATORY`;
- a public contamination registry records permanent invalidation;
- three v2 roles use public commitment manifests and ignored private roots;
- `METHODOLOGY_READY` and the ICLR states are canonical enum values;
- the release inventory and bundle hash are current.

Deleting files or rewriting Git history would not restore scientific secrecy.
No destructive history rewrite was performed.

## Split and dataset state

The canonical registry passes with 9 roles and 0 cross-role overlaps.

| Protected role | Base tasks | Interventions | Instances | State |
|---|---:|---:|---:|---|
| Scale-100 v2 | 100 | 500 | 600 | `HUMAN_INPUT_REQUIRED` |
| naturalistic transfer v2 | 60 | 300 | 360 | `HUMAN_INPUT_REQUIRED` |
| held-out challenge v2 | 50 | 250 | 300 | private payload authoring pending |

Scale and naturalistic private candidates pass static diversity, canonical
answer-contract, manipulation-check, provenance, licence, privacy, injection,
and public-surface leakage checks. No private v2 file is tracked, and the
public scan found zero private payload fragments.

These are candidates, not confirmatory datasets. Human review, adjudication,
C10, and slice locking remain mandatory.

## RAAC

Recovery-Aware Agent Control is implemented with 12 typed states, 16
observable anomaly signals, 13 policies, 6 ablations, and 5 baseline wrappers.
Its compute contracts are bounded, traces are auditable and resumable, and
agent-facing policy inputs exclude intervention labels, gold, answers, and
evaluator metadata. No RAAC improvement is claimed.

## Human and evidence state

- Compact-20 candidates: 20
- Required independent reviewers: 2 per candidate
- Genuine human rows: 0
- Complete review groups: 0
- Human review: `HUMAN_REVIEW_INCOMPLETE`
- C10: `C10_PENDING`
- Slice lock allowed: false
- Real trajectories: 0
- Audited real runs: 0
- Paper-eligible assets: 0
- Supported empirical claims: 0

## Resource and paper state

All nine Kaggle notebooks pass offline fixture execution and refuse live
activation by default. The M4 lane provides serial, low-memory, four-worker,
and adaptive modes plus streaming, deterministic bootstrap sharding, disk
estimates, and non-destructive cleanup plans.

The method-first paper includes intervention validity, paired inference, RAAC,
naturalistic transfer, limitations, ethics, and reproducibility. A 14-page
draft compiles, but seven result placeholders remain deliberately visible.

## Validation

| Check | Result |
|---|---|
| Consolidated focused tests | 145 passed in 69.05 s |
| Complete provider-free suite | 1,091 passed, 1 skipped in 171.32 s |
| Ruff | pass |
| mypy | pass across 205 source files |
| JSON/YAML parsing | 15 JSON and 102 YAML files |
| Kaggle offline fixtures | 9/9 notebooks; 72 receipts |
| Private candidate aggregate validator | pass |
| Security and release checks | pass |
| Canonical split and protected commitment checks | pass |
| Draft paper checks and LaTeX build | pass |
| Unexpected blockers | 0 |

## Exact next action

Complete the blank Compact-20 review packet with two independent, qualified
human reviewers; do not run models.

Machine-readable details are in
`reports/ICLR_ONESHOT_CURRENT_STATE.json`.
