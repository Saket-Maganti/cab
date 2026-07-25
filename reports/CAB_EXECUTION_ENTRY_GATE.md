# CAB Execution Entry Gate

Generated: 2026-07-23T17:26:26.863801+00:00

- Build status: `CAB_MAX_CEILING_PREEXECUTION_BUILD_COMPLETE`
- Workflow state: `HUMAN_REVIEW_INCOMPLETE`
- Pre-execution build complete: `true`
- Scientific execution allowed: `false`
- Paper eligible: `false`
- Evidence class: `ENGINEERING_ONLY`

A build pass certifies repository-controlled logic only. It is not model, human-validity, or paper evidence.

## Unified checks

| Check | Scope | Status | Evidence | Detail |
|---|---|---|---|---|
| `repository_consistency` | build | PASS | `ENGINEERING_ONLY` | branch=codex/cab-max-ceiling-preexecution; commit=dea8e25f0e429ed2054c628fb37d24e7c1c9020e; dirty=True; dirty user work is preserved, not erased |
| `leakage` | build | PASS | `ENGINEERING_ONLY` | reports=4/4; blocker_clusters=0; manual_review_clusters=88; contract/payload/release blockers=0 |
| `schemas` | build | PASS | `ENGINEERING_ONLY` | rows=8760; invalid=0; missing=0 |
| `scorer` | build | PASS | `FIXTURE_ONLY` | name=cab_typed_final_answer; version=2.0.0; answer_contracts=8; fixture=True |
| `metrics` | build | PASS | `FIXTURE_ONLY` | fixture=phase5_matched_family_denominator_fixture_v1; global_clean=0.666667; matched_family_clean=0.5 |
| `human_review` | external | BLOCKED | `HUMAN_INPUT_REQUIRED` | state=HUMAN_REVIEW_INCOMPLETE; genuine_rows=0; review_groups=0/60 |
| `c10` | external | BLOCKED | `HUMAN_INPUT_REQUIRED` | state=C10_PENDING; empty/proxy rows can never pass |
| `slice_integrity` | external | BLOCKED | `HUMAN_INPUT_REQUIRED` | slice_lock_allowed=False; registry_issues=0 |
| `configs` | build | PASS | `ENGINEERING_ONLY` | configs=67; issues=0; warnings=115 |
| `secrets` | build | PASS | `ENGINEERING_ONLY` | errors=0; warnings=0 |
| `provider_approval` | external | BLOCKED | `EXECUTION_PENDING` | no current maximum-ceiling live approval; dry-run defaults remain active |
| `notebooks` | build | PASS | `FIXTURE_ONLY` | validated=9/9; offline fixture execution is validated separately in the validation ledger |
| `provenance` | build | PASS | `ENGINEERING_ONLY` | manifest_template=True; split_registry=True; append_ledger=True; merge_contract=True |
| `paper_claims` | build | PASS | `ENGINEERING_ONLY` | claims=10; unsupported empirical claims promoted=0 |
| `paper_assets` | evidence | BLOCKED | `EXECUTION_PENDING` | paper_eligible_assets=0; zero is the correct pre-execution state |
| `release_status` | build | PASS | `ENGINEERING_ONLY` | release_check_passed=True; errors=0; publication remains gated |

## Study gates

| Study | State | Build ready | Execution ready | Blockers |
|---|---|---:|---:|---|
| `compact20` | `HUMAN_REVIEW_PENDING` | true | false | genuine dual-review, adjudication, C10, and slice lock; explicit live-run approval |
| `scale100` | `EXECUTION_PENDING` | true | false | study-specific human validation and slice lock; audited Compact-20 evidence and preregistered scale decision; explicit live-run approval |
| `naturalistic_transfer` | `HUMAN_REVIEW_PENDING` | true | false | artifact-specific human validity and privacy review; explicit live-run approval |
| `main500` | `EXECUTION_PENDING` | true | false | study-specific human validation and slice lock; audited pilot/confirmatory evidence justifying Main-500; explicit live-run approval |
| `paper_assets` | `EXECUTION_PENDING` | true | false | audited paper-eligible evidence and assets; claim-ledger promotion after audit |

## Exact blockers

### Build blockers

- None.

### Human, external, execution, and evidence blockers

- `human_review`: state=HUMAN_REVIEW_INCOMPLETE; genuine_rows=0; review_groups=0/60
- `c10`: state=C10_PENDING; empty/proxy rows can never pass
- `slice_integrity`: slice_lock_allowed=False; registry_issues=0
- `provider_approval`: no current maximum-ceiling live approval; dry-run defaults remain active
- `paper_assets`: paper_eligible_assets=0; zero is the correct pre-execution state

## Exact next allowed action

Have two independent human reviewers complete the Compact-20 task-clarity, gold-policy, and intervention-isolation packets; do not run models.

Then re-run: `python3 scripts/validate_cab_human_reviews.py --review-dir data/human_validation/compact20_real_review`

## Forbidden now

- `python3 -m causal_agent_bench run ...`
- `make smoke`
- `jupyter nbconvert --execute <live-runner-notebook>`
- `set RUN_LIVE=True before C10, slice lock, and explicit approval`
- `fill or export empirical paper assets from fixture/stub outputs`
