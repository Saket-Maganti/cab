# CAB Execution God-Tier Prompt Pack V2 — Order and Stop Rules

Project root:

`/Users/saketmaganti/Projects/causal-agent-bench`

## Why this pack exists

The previous uplift pack created a safe launch path, but it ended with:

`PARTIAL_SUCCESS_BLOCKED_BY_MISSING_INPUTS`

The project still lacks the things that actually raise research value:

- real human review,
- C10 intervention-isolation validation,
- approved live provider execution,
- audited provider trajectories,
- scorer sanity,
- ACRS/rank-instability results,
- real paper tables/plots.

This pack is designed to move CAB from **organized scaffold** to **real evidence machine**.

## Global evidence rules

Every prompt must obey:

- Do not fabricate provider outputs.
- Do not fabricate human annotations.
- Do not treat proxy/AI review as human review.
- Do not promote C1-C8/C10 without evidence.
- Do not mark paper assets eligible before audit.
- Do not store API keys in the repo.
- Do not print API keys.
- Do not leave `allow_paid_calls=true`.
- Do not run broad sweeps unless the prompt explicitly allows it.
- Do not run Main-500 until Compact-20 and 5-model/100-task gates pass.

## Execution order

### Phase 1 — Real human review
1. `01_HUMAN_REVIEW_COMPLETION_DRIVER.md`
2. `02_COMPACT20_REPAIR_FROM_HUMAN_REVIEW.md`
3. `03_C10_VALIDATION_AND_SLICE_LOCK.md`

### Phase 2 — Approval + preflight
4. `04_LIVE_RUN_APPROVAL_FINALIZER.md`
5. `05_COMPACT20_3MODEL_PREFLIGHT_STRICT.md`

### Phase 3 — First real evidence
6. `06_EXECUTE_COMPACT20_3MODEL_ONCE.md`
7. `07_LOCK_IMPORT_AND_RUN_INDEX_RECONCILIATION.md`
8. `08_POSTRUN_MANUAL_TRAJECTORY_REVIEW.md`
9. `09_SCORER_SANITY_AND_GOLD_POLICY_REPAIR.md`

### Phase 4 — Turn evidence into science
10. `10_ACRS_RANK_INSTABILITY_REAL_ANALYSIS.md`
11. `11_REAL_TABLES_FIGURES_AND_MONEY_PLOT.md`
12. `12_FAILURE_GALLERY_AND_FINDING_EXTRACTION.md`
13. `13_CLAIM_LEDGER_PROMOTION_GATE.md`

### Phase 5 — First ceiling jump
14. `14_EXECUTE_5MODEL_100TASK_AFTER_COMPACT20.md`
15. `15_CROSS_RUN_META_ANALYSIS_AND_POWER_CHECK.md`
16. `16_NATURALISTIC_TRANSFER_EXECUTION_GATE.md`

### Phase 6 — Paper-grade release
17. `17_NEURIPS_DB_PAPER_INTEGRATION_FROM_REAL_RESULTS.md`
18. `18_DMLR_DATASET_BENCHMARK_RELEASE_PACKAGE.md`
19. `19_FINAL_REVIEWER_SIMULATION_AFTER_EVIDENCE.md`
20. `20_GOD_TIER_FINAL_GATE_AND_NEXT_EXECUTION_DECISION.md`

## Definition of “god-tier” for this repo

Not hype. It means:

1. real runs,
2. real validation,
3. real audited tables,
4. real release package,
5. no unsupported claims,
6. enough evidence to survive serious reviewer attack.

## Mandatory stop conditions

Stop immediately if:

- human review is absent,
- approval is ambiguous,
- credentials are missing,
- cost estimate exceeds cap,
- config contains secrets,
- run output is incomplete,
- scorer sanity fails,
- C10 isolation fails,
- claims are unsupported,
- a generated table contains stub/mock data.

## Final state this pack is aiming for

Minimum strong state:

`COMPACT20_REAL_EVIDENCE_COMPLETE_PRELIMINARY`

High state:

`5MODEL_100TASK_EVIDENCE_COMPLETE`

Ceiling state:

`NEURIPS_DB_DMLR_CANDIDATE_PENDING_FINAL_POLISH`
