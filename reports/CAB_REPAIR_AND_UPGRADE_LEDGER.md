# CAB Repair and Upgrade Ledger

> Canonical maximum-ceiling artifact. Regenerate with `python3 scripts/generate_cab_max_ceiling_reports.py`.

Generated: 2026-07-23T17:23:44.726749+00:00

Build status: `CAB_MAX_CEILING_PREEXECUTION_BUILD_COMPLETE`.

| Workstream | Actual repair | State | Evidence class |
|---|---|---|---|
| Checkpoint/truth | Created pointer-only checkpoint branch; derived state from live artifacts. | `complete` | `ENGINEERING_ONLY` |
| Split contamination | Namespaced generated IDs and hashed six incompatible study roles. | `complete` | `ENGINEERING_ONLY` |
| Gold leakage | Separated visible payload checks from hidden evaluator policies; added fail-closed leakage gate. | `complete` | `ENGINEERING_ONLY` |
| Naturalistic artifact leakage | Removed direct incident-answer cue and added provenance/license/privacy/injection metadata. | `complete` | `ENGINEERING_ONLY` |
| Answer semantics | Implemented eight typed answer contracts and strict gold/scorer policies. | `complete` | `DESIGN_ONLY` |
| Production scoring | Replaced unsafe default substring scoring with typed scorer v2 and adversarial conformance fixtures. | `complete` | `FIXTURE_ONLY` |
| Scorer provenance | Added name/version/config/policy hashes, code revision, intervention, and repeat metadata. | `complete` | `ENGINEERING_ONLY` |
| Matched metrics | Added explicit pair ledger, exact family clean denominators, duplicate/incomplete rejection. | `complete` | `FIXTURE_ONLY` |
| Statistical inference | Added paired/clustered/stratified bootstrap, paired binary tests, effects, rank uncertainty, corrections, sensitivity. | `complete` | `FIXTURE_ONLY` |
| Dataset ceiling | Materialized Scale-100, naturalistic-80, Main-500 + heldout-50 candidate packs without model outcomes. | `complete` | `DESIGN_ONLY` |
| Human validity/C10 | Added genuine-row-only dual-review, adjudication, agreement, C10, and slice-lock gate. | `complete; input pending` | `HUMAN_INPUT_REQUIRED` |
| Run provenance | Added strict manifest v2, hash-chained append ledger, dedup/conflict/completeness merge checks. | `complete` | `FIXTURE_ONLY` |
| T4×2 mechanics | Added nine guarded notebooks with deterministic two-worker sharding, fallback, resume, merge, integrity. | `complete` | `FIXTURE_ONLY` |
| Evidence state | Separated design, engineering, fixture, human, pending, preliminary, audited, and paper evidence. | `complete` | `ENGINEERING_ONLY` |
| Paper plumbing | Kept claims/assets fail-closed and added eligibility-aware analysis coverage. | `complete` | `ENGINEERING_ONLY` |
| Release/governance | Added active/archive/deprecation and provider-free CI surface. | `complete` | `ENGINEERING_ONLY` |
| Final handoff | Generated exact authoritative reports, handbook, verification ledger, and `cabv2.md`. | `complete` | `ENGINEERING_ONLY` |

## Logical commit plan (not executed)

1. `contracts-scorer`: answer policies, schema integration, scorer, tests.
2. `paired-statistics`: matched metrics, inference utilities, tests.
3. `dataset-leakage`: generation policies, candidate packs, split registry, audits.
4. `human-provenance`: C10 gate, manifest v2, ledger/merge tests.
5. `kaggle`: fixture mechanics, generator, validator, nine notebooks.
6. `ci-governance-paper`: provider-free gates, paper refusal, release surface.
7. `audit-handoff`: current state, reports, handbook, `cabv2.md`.

Suggested commands only after user review:

```bash
git add <paths-for-one-group>
git commit -m '<group message>'
```

No files were staged, committed, or pushed by this task.

## Preserved user work

The current worktree remains dirty with 724 status entries. No destructive cleanup or broad revert was performed.
