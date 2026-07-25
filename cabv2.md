# CAB v2 Authoritative Handoff

> Canonical maximum-ceiling artifact. Regenerate with `python3 scripts/generate_cab_max_ceiling_reports.py`.

Generated: 2026-07-23T17:23:44.726749+00:00

## Project purpose

Measure tool-using agent robustness under controlled, paired environment and information interventions.

## Strongest thesis and ceiling

CAB is a controlled-intervention benchmark and methodology for measuring whether successful tool-using behavior survives goal-preserving perturbations. Empirical model-comparison claims remain untested.

Current ceiling: methodology-and-engineering artifact only; not an empirical paper. A strong benchmark-paper ceiling requires human validity and audited multi-model evidence; a main-track stretch requires an additional substantive contribution.

## Evolution

The repository evolved from a broad engineering scaffold and V3 no-execution upgrade into one canonical pre-execution surface: typed policies/scoring, matched statistics, hashed study roles, genuine-human C10, strict run provenance, and guarded T4×2 notebooks. No V4 handoff or `cabv1.md` is present, so V4 is not treated as verified.

## Verified repository state

- Branch/commit: `codex/cab-max-ceiling-preexecution` / `dea8e25f0e429ed2054c628fb37d24e7c1c9020e`
- Build status: `CAB_MAX_CEILING_PREEXECUTION_BUILD_COMPLETE`
- Workflow state: `HUMAN_REVIEW_INCOMPLETE`
- Validation passed: `True`
- Cross-role overlap: 0
- Static leakage blocker clusters: 0

## Systems repaired or implemented

- Eight answer contracts; typed scorer `cab_typed_final_answer` v2.0.0.
- Exact matched-pair/family metrics, dependence-aware inference, rank uncertainty.
- Scale-100, naturalistic transfer, Main-500 + challenge candidate architecture.
- Canonical split hashes and leakage/task-contract gates.
- Genuine-row-only human/C10/adjudication/slice-lock gate.
- Manifest v2, hash-chained ledger, checkpoint/resume, merge invariants.
- Nine Kaggle T4×2 notebooks and offline fixture integrity validation.
- Provider-free CI, paper-evidence refusal, release/governance surface.

## Evidence and claim state

- Genuine human rows: 0
- Real provider trajectories: 0
- Real open-model trajectories: 0
- Audited real runs: 0
- Paper-eligible assets: 0
- Supported empirical claims: 0
- Human review: `HUMAN_REVIEW_INCOMPLETE`
- C10: `C10_PENDING`
- Compact-20: candidate/review packet exists; no scientific run.
- Scale-100: candidate architecture exists; human/freeze/execution pending.
- Naturalistic transfer: candidate architecture/provenance exists; review pending.
- Main-500: candidate + heldout architecture exists; justification/execution pending.
- Paper: scaffold only; empirical assets/claims blocked.
- Release: engineering candidate only; hidden/challenge data policy remains binding.

## `cabv1.md` disposition

`cabv1.md` was not found. Therefore no text is silently reconstructed.

- Confirmed independently: V3-era engineering scaffold exists; C9-style fixture reproducibility is engineering only.
- Corrected: all live run/test/human/asset counts are repository-derived, not copied from historical status prose.
- Superseded: old next-action and scorer/metric descriptions are replaced by the current state, entry gate, typed scorer, and matched metrics.
- Invalidated if previously asserted: any nonzero genuine-human, real-provider, real-open-model, audited, paper-eligible, C10-pass, or submission-ready state.

## Blockers

- `human_review`: state=HUMAN_REVIEW_INCOMPLETE; genuine_rows=0; review_groups=0/60
- `c10`: state=C10_PENDING; empty/proxy rows can never pass
- `slice_integrity`: slice_lock_allowed=False; registry_issues=0
- `provider_approval`: no current maximum-ceiling live approval; dry-run defaults remain active
- `paper_assets`: paper_eligible_assets=0; zero is the correct pre-execution state

## Exact next step

Have two independent human reviewers complete the Compact-20 task-clarity, gold-policy, and intervention-isolation packets; do not run models.

After genuine rows are entered:

```bash
python3 scripts/validate_cab_human_reviews.py --review-dir data/human_validation/compact20_real_review
```

Do not skip to model/provider execution.
Do not run models until genuine human review, C10, slice lock, and explicit execution approval all pass.

## Authoritative paths

- `reports/CAB_CURRENT_STATE_VERIFIED.json`
- `reports/CAB_EXECUTION_ENTRY_GATE.md`
- `reports/CAB_MAX_CEILING_FORENSIC_AUDIT.md`
- `reports/CAB_VERIFICATION_COMMANDS.md`
- `CAB_COMPLETE_EXECUTION_AND_RUN_HANDBOOK.md`

## No-execution stop rule

Further scaffold-only version cycles now have diminishing returns. The next scientifically meaningful phase is real human validation, followed by approved fixture preflight and Compact-20 execution in handbook order.
