# CAB Current State — Verified

Generated: 2026-07-23T17:26:12.766551+00:00

Computed from Git, filesystem inventories, canonical split hashes, live result metadata, the human/C10 validator, claim ledger, and paper-asset eligibility validator. No model or provider was called.

## Repository

- Branch: `codex/cab-max-ceiling-preexecution`
- Commit: `dea8e25f0e429ed2054c628fb37d24e7c1c9020e`
- Dirty: `true`
- Modified tracked paths: 117
- Untracked paths: 607
- Session-start user-owned baseline: 115 modified tracked and 566 untracked paths, observed before maximum-ceiling edits.

## Inventory

- Source: 183 files / 64437 lines
- Tests: 135 files / 20151 lines
- Docs and reports: 276 files
- Notebooks: 14
- Result directories indexed: 80
- Status sources found: 47

## Canonical purpose and thesis

- Purpose: Measure tool-using agent robustness under controlled, paired environment and information interventions.
- Thesis: CAB is a controlled-intervention benchmark and methodology for measuring whether successful tool-using behavior survives goal-preserving perturbations. Empirical model-comparison claims remain untested.
- Causal scope: Causal refers to preregistered interventions and paired contrasts; it does not by itself establish broad causal identification about real-world agent populations.
- Current publication ceiling: methodology-and-engineering artifact only; not an empirical paper

## Dataset roles

| Role | Instances | Unique base tasks | Templates | Domains | Status |
|---|---:|---:|---:|---:|---|
| `dev_fixture` | 9 | 3 | 3 | 3 | `FIXTURE_READY` |
| `compact20_pilot` | 30 | 10 | n/a | n/a | `HUMAN_REVIEW_PENDING` |
| `scale100_confirmatory` | 600 | 100 | 12 | 12 | `HUMAN_REVIEW_PENDING` |
| `naturalistic_transfer` | 432 | 72 | 8 | 8 | `HUMAN_REVIEW_PENDING` |
| `main500_confirmatory` | 3000 | 500 | 12 | 12 | `HUMAN_REVIEW_PENDING` |
| `heldout_challenge` | 300 | 50 | 12 | 12 | `HUMAN_REVIEW_PENDING` |

Cross-role base-task overlaps: 0.

## Evidence

- Genuine human rows: 0
- Real provider trajectories: 0
- Real open-model trajectories: 0
- Audited real runs: 0
- Paper-eligible assets: 0
- Supported empirical claims: 0
- Human state: `HUMAN_REVIEW_INCOMPLETE`
- C10: `C10_PENDING`
- All passing fixtures and tests are engineering evidence only.

## Evidence classes

- `DESIGN_ONLY`
- `ENGINEERING_ONLY`
- `FIXTURE_ONLY`
- `HUMAN_INPUT_REQUIRED`
- `EXECUTION_PENDING`
- `PRELIMINARY_REAL_EVIDENCE`
- `AUDITED_REAL_EVIDENCE`
- `PAPER_ELIGIBLE_EVIDENCE`

## Boundary

- No model inference or provider calls were made by this build.
- No human judgments, benchmark outcomes, costs, or runtimes were invented.
- Candidate task packs remain ineligible for scientific execution until genuine review, adjudication, C10, and slice locking complete.
