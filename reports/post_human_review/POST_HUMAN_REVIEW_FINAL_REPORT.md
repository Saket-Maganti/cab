# Post-human-review final report

Generated `2026-08-05T18:46:53.426383+00:00` at commit `50487b6f29b2f54665e09aa03860028b416e67fe`.

## Status

- `HUMAN_REVIEW_COMPLETE`
- `QUALIFICATION_GENUINE_AND_VERIFIED`
- `REVIEWER_DECLARATION_WAIVER_DISCLOSED`
- `C10_PASS`
- `COMPACT20_SLICE_LOCKED`
- `COMPACT20_EXECUTION_AUTHORIZED`
- `LOCAL_CPU_VALIDATION_COMPLETE_WITH_PREEXISTING_BLOCKERS`
- `KAGGLE_CPU_RUNBOOKS_READY`

- `KAGGLE_CPU_PREFLIGHT_COMPLETE` — **not claimed**. The remote CPU notebooks were not executed. Kaggle's notebooks API rejects this account's token with HTTP 401 while the datasets API accepts it; see KAGGLE_CPU_NOTEBOOK_READINESS.md. No remote result is claimed.
- Genuine model trajectories: **0**.

## The review

| | Reviewer A | Reviewer B |
| --- | --- | --- |
| Stage-1 rows | 20 | 20 |
| Stage-2 rows | 20 | 20 |
| Qualification | 4/5 | 4/5 |

- Stage-1 gated agreement: **1.0**, 3 adjudicated dimension(s).
- Stage-2 agreement: **0.9222**, 14 disputed dimension(s).
- Agreement uses adjudicated values: `False`.
- Included **20**, excluded **0**, unresolved **0**.

## Provenance, stated plainly

- Qualification: `GENUINE_VERIFIED_SUBMISSIONS`, threshold `0.8`, scored against the private answer key. The key is not disclosed and per-item correctness is not published.
- Reviewer declarations: `COORDINATOR_WAIVER`. No declaration file was collected and none is asserted.
- Artifact origin: `MANUAL_OFFLINE_REVIEW_IMPORT_V1`, import epoch `v3`.
- Superseded epochs quarantined: 2 (edited: `False`, deleted: `False`).

## Gates

| gate | value |
| --- | --- |
| C10 | `PASS` — `C10_MECHANICS_PASS_WITH_COORDINATOR_DECLARATION_WAIVER` |
| C10 receipt | `370f9970854767c40c440e91c502da8e34da73349ce235d3a5e55fab9c6ea36d` |
| Scientific freeze | `ca9a8552104bb6270b9a604b8915653efcafe60efd67c16d2d305f38b1e4f746` |
| Exclusion register | `5ff8c8c0115b0d974454fd338422ab6c33b6ffc76ed976fed2e2d9a99d9cc878` |
| Reviewed slice lock | `86ee7eabdc789c8a6241dfe46b73bd6864a76d7f907845b76d43c765b0bd8c2d` |
| Pair-content digest | `e663525f8272db7bcb454c63bb279fd0ec3d7f6ec1a877fad9434a18f2acda2d` |
| Execution authorization | `ec9cc1bdd8a4adacd1d1f794549108bd0d4bd9f7874ff152b787db9bbdf07874` |
| Authorized study | `compact20_reviewed_pilot` |
| Paid providers authorized | `False` |

## Local CPU validation

**13/15** gates passed (`{'passed': 1695, 'skipped': 1}`, 4 pytest workers).

- Regressions introduced by this work: **none**.
- Still failing for reasons that predate it: `['max_ceiling_validation', 'leakage_gate']`. Both are the task-intervention contract blockers on the public development splits, reproduced unchanged at `22dbff0`. They are a separate body of work and were not papered over here.

## Kaggle

- Arbitrary-name discovery: **16** cases, passed `True`.
- Datasets API: `OK`. Notebooks API: `HTTP_401_UNAUTHORIZED`.
- Remote CPU 00/01/02: `NOT_RUN` / `NOT_RUN` / `NOT_RUN`.

| bundle | sha256 | bytes |
| --- | --- | ---: |
| `compact20-t4x2` | `57872bad4c5671346339e7049e3d1bc246d6ef9c91535a28134cd531568a778d` | 1908193 |
| `cpu-preexecution` | `a56ca6f7659725dd5fdd6fe7b11f672a56a39dd3011d5d0d55168517a9b8108f` | 2385596 |

## What this does not authorize

Live open-model execution. The Compact-20 pilot is authorized; Scale-100, Main-500, the naturalistic transfer study and the RAAC ablation are not, and none is implied by this one. No model or provider was invoked anywhere in this chain.
