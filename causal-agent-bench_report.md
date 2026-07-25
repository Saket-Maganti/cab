# Project Report: causal-agent-bench

## 1. Executive Summary

CAB's prompt pack was found at `/Users/saketmaganti/Projects/causal-agent-bench/CAB_Insane_Uplift_Prompt_Pack`. The autorun created a conservative no-provider-call uplift layer: repo/claim/doc audits, Compact-20 blocked manifests, blank human-review packets, approval-required provider configs, gated runbooks, blocked postrun/analysis artifacts, related-work/novelty docs, release scaffolds, reviewer simulations, and final venue gate. No paid APIs, live providers, credentials, or human labels were used. Final status: `PARTIAL_SUCCESS_BLOCKED_BY_MISSING_INPUTS`.

## 2. Prompt Pack Discovery

- Exact prompt-pack folder path: `/Users/saketmaganti/Projects/causal-agent-bench/CAB_Insane_Uplift_Prompt_Pack`
- Project root path: `/Users/saketmaganti/Projects/causal-agent-bench`
- Number of prompt files discovered: `26`
- Operational prompt files executed: `23`
- Files read only for context: `23_QUICK_START_NEXT_ACTION_PROMPT.md`, `24_LIVE_RUN_APPROVAL_TEMPLATE.md`, `manifest.json`
- Ignored files and why: quick-start/approval templates were context, not operational prompts.

## 3. Execution Order

1. `00_README_ORDER_AND_GATES.md`
2. `01_REPO_REALITY_FREEZE_AND_COMMIT_HYGIENE.md`
3. `02_DOC_SPRAWL_ARCHIVE_AND_PROJECT_SURFACE.md`
4. `03_SINGLE_THESIS_CLAIM_LEDGER_REFOCUS.md`
5. `04_COMPACT20_SLICE_FINALIZATION_GOLD_REPAIR.md`
6. `05_REAL_HUMAN_REVIEW_PACKET_NOT_PROXY.md`
7. `06_C10_INTERVENTION_ISOLATION_VALIDATION.md`
8. `07_3MODEL_COMPACT20_CONFIG_APPROVAL_NO_SECRETS.md`
9. `08_3MODEL_COMPACT20_PRELIVE_PREFLIGHT.md`
10. `09_EXECUTE_3MODEL_COMPACT20_PROVIDER_PILOT_GATED.md`
11. `10_POSTRUN_AUDIT_SCORER_SANITY_EVIDENCE_CLASSIFICATION.md`
12. `11_ACRS_RANK_INSTABILITY_STATS.md`
13. `12_REAL_RESULT_TABLES_AND_MONEY_PLOTS.md`
14. `13_FAILURE_GALLERY_QUALITATIVE_FINDINGS.md`
15. `14_BASELINE_AGENT_ABLATION_UPGRADES.md`
16. `15_SCALE_TO_5MODEL_100TASK_STUDY.md`
17. `16_NATURALISTIC_TRANSFER_MINISTUDY.md`
18. `17_MAIN_500_DESIGN_AND_RUN_GATE.md`
19. `18_PAPER_REWRITE_NEURIPS_DB_DMLR.md`
20. `19_RELATED_WORK_NOVELTY_DEFENSE.md`
21. `20_RELEASE_REPRODUCIBILITY_PACKAGE.md`
22. `21_REVIEWER_SIMULATION_REBUTTAL_PACKET.md`
23. `22_FINAL_SUBMISSION_GATE_VENUE_DECISION.md`

## 4. Prompt-by-Prompt Results

### 00_README_ORDER_AND_GATES.md

- Status: `DONE`
- What was done: Global no-fabrication/no-provider rules recorded.
- Files created/modified: `reports/CAB_AUTORUN_MASTER_STATE.md`, `reports/CAB_AUTORUN_MASTER_STATE.json`
- Commands run: `bounded local file generation; no provider/API calls`
- Evidence status: `ORIENTATION_ONLY`
- Blockers: None

### 01_REPO_REALITY_FREEZE_AND_COMMIT_HYGIENE.md

- Status: `DONE`
- What was done: Worktree reality summarized without cleanup/reverts.
- Files created/modified: `reports/REPO_REALITY_FREEZE.md`, `reports/COMMIT_GROUPING_PLAN.md`
- Commands run: `git status --short`
- Evidence status: `REPO_AUDIT_ONLY`
- Blockers: None

### 02_DOC_SPRAWL_ARCHIVE_AND_PROJECT_SURFACE.md

- Status: `PARTIAL`
- What was done: Focused surface created; doc moves skipped to preserve dirty worktree.
- Files created/modified: `docs/CAB_FOCUSED_PROJECT_SURFACE.md`, `docs/archive/no_run_scaffold/ARCHIVE_INDEX.md`, `reports/DOC_SPRAWL_REDUCTION_REPORT.md`
- Commands run: `bounded local file generation; no provider/API calls`
- Evidence status: `DOC_SURFACE_ONLY`
- Blockers: Existing dirty worktree made doc moves unsafe

### 03_SINGLE_THESIS_CLAIM_LEDGER_REFOCUS.md

- Status: `DONE`
- What was done: Single-thesis claim architecture written with unsupported claims preserved.
- Files created/modified: `docs/CLAIM_ARCHITECTURE.md`, `reports/CLAIM_LEDGER_REFOCUS_REPORT.md`
- Commands run: `bounded local file generation; no provider/API calls`
- Evidence status: `CLAIM_GOVERNANCE_ONLY`
- Blockers: None

### 04_COMPACT20_SLICE_FINALIZATION_GOLD_REPAIR.md

- Status: `PARTIAL`
- What was done: Compact-20 candidate manifest materialized but manual review/gold repair remain pending.
- Files created/modified: `data/compact20_reviewed/compact20_reviewed_manifest.json`, `data/compact20_reviewed/compact20_task_quality_report.md`, `data/compact20_reviewed/compact20_gold_repair_report.md`, `data/compact20_reviewed/compact20_exclusion_list.csv`, `data/compact20_reviewed/compact20_readiness.json`
- Commands run: `bounded local file generation; no provider/API calls`
- Evidence status: `STATIC_CANDIDATE_MANIFEST_ONLY`
- Blockers: No real human review

### 05_REAL_HUMAN_REVIEW_PACKET_NOT_PROXY.md

- Status: `DONE`
- What was done: Real human-review packet created with header-only CSVs.
- Files created/modified: `data/human_validation/compact20_real_review/adjudication_template.csv`, `data/human_validation/compact20_real_review/intervention_isolation_review.csv`, `data/human_validation/compact20_real_review/HUMAN_REVIEW_PACKET_STATUS.md`, `data/human_validation/compact20_real_review/README.md`, `data/human_validation/compact20_real_review/gold_policy_review.csv`, `data/human_validation/compact20_real_review/task_clarity_review.csv`, `data/human_validation/compact20_real_review/reviewer_instructions.md`
- Commands run: `bounded local file generation; no provider/API calls`
- Evidence status: `HUMAN_PACKET_BLANK`
- Blockers: None

### 06_C10_INTERVENTION_ISOLATION_VALIDATION.md

- Status: `BLOCKED_OR_DEFERRED`
- What was done: C10 validation blocked explicitly.
- Files created/modified: `reports/C10_VALIDATION_BLOCKED_MISSING_HUMAN_REVIEWS.md`, `reports/C10_INTERVENTION_ISOLATION_VALIDATION.md`, `reports/C10_INTERVENTION_ISOLATION_VALIDATION.csv`, `data/compact20_reviewed/compact20_validated_or_blocked_manifest.json`
- Commands run: `bounded local file generation; no provider/API calls`
- Evidence status: `BLOCKED_MISSING_HUMAN_REVIEWS`
- Blockers: Missing real human reviews

### 07_3MODEL_COMPACT20_CONFIG_APPROVAL_NO_SECRETS.md

- Status: `DONE`
- What was done: Non-runnable 3-model Compact-20 config and approval template created.
- Files created/modified: `configs/compact20_3model_APPROVAL_REQUIRED.yaml`, `docs/approvals/COMPACT20_3MODEL_PILOT_APPROVAL_TEMPLATE.md`, `reports/COMPACT20_3MODEL_CONFIG_SAFETY_REPORT.md`
- Commands run: `bounded local file generation; no provider/API calls`
- Evidence status: `APPROVAL_REQUIRED_CONFIG_ONLY`
- Blockers: None

### 08_3MODEL_COMPACT20_PRELIVE_PREFLIGHT.md

- Status: `BLOCKED_OR_DEFERRED`
- What was done: Prelive preflight blocked; no credential values read or provider calls made.
- Files created/modified: `reports/COMPACT20_3MODEL_PRELIVE_PREFLIGHT.md`, `reports/COMPACT20_3MODEL_COST_ESTIMATE.json`, `reports/COMPACT20_3MODEL_DRY_RUN_PREFLIGHT.json`
- Commands run: `bounded local file generation; no provider/API calls`
- Evidence status: `BLOCKED_NOT_APPROVED`
- Blockers: No explicit live approval, No credential check authorized

### 09_EXECUTE_3MODEL_COMPACT20_PROVIDER_PILOT_GATED.md

- Status: `BLOCKED_OR_DEFERRED`
- What was done: Live provider pilot not executed; runbook created.
- Files created/modified: `reports/COMPACT20_3MODEL_LIVE_RUN_EXECUTION_REPORT.md`, `notebooks/provider_pilot/compact20_3model_provider_pilot_runbook.ipynb`
- Commands run: `bounded local file generation; no provider/API calls`
- Evidence status: `BLOCKED_PRELIVE_NOT_READY`
- Blockers: PRELIVE_READY_FOR_SINGLE_EXECUTION absent

### 10_POSTRUN_AUDIT_SCORER_SANITY_EVIDENCE_CLASSIFICATION.md

- Status: `BLOCKED_OR_DEFERRED`
- What was done: Postrun audit/scorer classification blocked with header-only CSVs.
- Files created/modified: `reports/COMPACT20_3MODEL_POSTRUN_AUDIT.md`, `reports/COMPACT20_3MODEL_TRAJECTORY_REVIEW.csv`, `reports/SCORER_SANITY_COMPACT20_3MODEL.md`, `reports/SCORER_SANITY_COMPACT20_3MODEL.csv`, `reports/COMPACT20_3MODEL_EVIDENCE_CLASSIFICATION.md`
- Commands run: `bounded local file generation; no provider/API calls`
- Evidence status: `BLOCKED_NO_REAL_PROVIDER_RUN`
- Blockers: No real provider run

### 11_ACRS_RANK_INSTABILITY_STATS.md

- Status: `BLOCKED_OR_DEFERRED`
- What was done: ACRS/rank analysis blocked with schema-only files.
- Files created/modified: `analysis/compact20_3model/acrs_summary.csv`, `analysis/compact20_3model/rank_instability.csv`, `analysis/compact20_3model/per_family_degradation.csv`, `analysis/compact20_3model/statistical_summary.md`, `reports/COMPACT20_3MODEL_ANALYSIS_REPORT.md`
- Commands run: `bounded local file generation; no provider/API calls`
- Evidence status: `BLOCKED_NO_AUDITED_REAL_OUTPUTS`
- Blockers: No audited provider outputs

### 12_REAL_RESULT_TABLES_AND_MONEY_PLOTS.md

- Status: `BLOCKED_OR_DEFERRED`
- What was done: Real result tables/plots blocked; schema-only tables created.
- Files created/modified: `paper/FIGURE_CAPTIONS_COMPACT20_REAL.md`, `reports/PAPER_ASSET_ELIGIBILITY_COMPACT20.md`
- Commands run: `bounded local file generation; no provider/API calls`
- Evidence status: `NO_REAL_RESULT_ASSETS_ELIGIBLE`
- Blockers: No analysis CSVs from real outputs

### 13_FAILURE_GALLERY_QUALITATIVE_FINDINGS.md

- Status: `BLOCKED_OR_DEFERRED`
- What was done: Failure gallery blocked with schema-only CSV.
- Files created/modified: `analysis/compact20_3model/failure_gallery.csv`, `paper/FAILURE_GALLERY_COMPACT20.md`, `reports/QUALITATIVE_FINDINGS_COMPACT20.md`
- Commands run: `bounded local file generation; no provider/API calls`
- Evidence status: `BLOCKED_NO_REAL_TRAJECTORIES`
- Blockers: No real trajectories

### 14_BASELINE_AGENT_ABLATION_UPGRADES.md

- Status: `DONE`
- What was done: Baseline/ablation templates created non-runnable.
- Files created/modified: `configs/ablations/*_TEMPLATE_NOT_APPROVED.yaml`, `experiments/ABLATION_DESIGN_FOR_CAB.md`, `reports/BASELINE_AGENT_UPGRADE_REPORT.md`
- Commands run: `bounded local file generation; no provider/API calls`
- Evidence status: `TEMPLATE_ONLY_NO_RUN`
- Blockers: None

### 15_SCALE_TO_5MODEL_100TASK_STUDY.md

- Status: `BLOCKED_OR_DEFERRED`
- What was done: 5-model/100-task design and gated runbook created; blocked by Compact-20.
- Files created/modified: `experiments/5MODEL_100TASK_STUDY_DESIGN.md`, `configs/5model_100task_TEMPLATE_NOT_APPROVED.yaml`, `docs/approvals/5MODEL_100TASK_APPROVAL_TEMPLATE.md`, `reports/5MODEL_100TASK_SCALEUP_READINESS.md`, `notebooks/provider_pilot/5model_100task_provider_runbook.ipynb`
- Commands run: `bounded local file generation; no provider/API calls`
- Evidence status: `SCALEUP_PLAN_ONLY`
- Blockers: Compact-20 real run incomplete

### 16_NATURALISTIC_TRANSFER_MINISTUDY.md

- Status: `PARTIAL`
- What was done: Naturalistic transfer scaffold and runbook created.
- Files created/modified: `experiments/NATURALISTIC_TRANSFER_MINISTUDY_DESIGN.md`, `data/naturalistic_ministudy/README.md`, `data/naturalistic_ministudy/task_template.json`, `data/naturalistic_ministudy/license_and_source_log.md`, `configs/naturalistic_ministudy_TEMPLATE_NOT_APPROVED.yaml`, `reports/NATURALISTIC_MINISTUDY_READINESS.md`, `notebooks/provider_pilot/naturalistic_ministudy_runbook.ipynb`
- Commands run: `bounded local file generation; no provider/API calls`
- Evidence status: `PLAN_ONLY_NO_DATA_NO_RESULTS`
- Blockers: No naturalistic task data materialized

### 17_MAIN_500_DESIGN_AND_RUN_GATE.md

- Status: `BLOCKED_OR_DEFERRED`
- What was done: Main-500 design/run gate created; execution blocked.
- Files created/modified: `experiments/MAIN_500_STUDY_DESIGN.md`, `configs/main_500_multi_provider_TEMPLATE_NOT_APPROVED.yaml`, `docs/approvals/MAIN_500_BUDGET_APPROVAL_TEMPLATE.md`, `reports/MAIN_500_RUN_GATE.md`, `notebooks/provider_pilot/main_500_provider_runbook.ipynb`
- Commands run: `bounded local file generation; no provider/API calls`
- Evidence status: `MAIN500_PLAN_ONLY`
- Blockers: Compact-20 evidence gate incomplete

### 18_PAPER_REWRITE_NEURIPS_DB_DMLR.md

- Status: `PARTIAL`
- What was done: Claim-safe paper rewrite scaffolds created without result claims.
- Files created/modified: `paper/PAPER_NARRATIVE_PLAN.md`, `paper/PAPER_CLAIM_TO_EVIDENCE_MAP.md`, `paper/*_v9.md`
- Commands run: `bounded local file generation; no provider/API calls`
- Evidence status: `PAPER_SCAFFOLD_NO_RESULTS`
- Blockers: No real result evidence for results section

### 19_RELATED_WORK_NOVELTY_DEFENSE.md

- Status: `DONE`
- What was done: Related work matrix and novelty boundary created from primary-source lookups.
- Files created/modified: `paper/RELATED_WORK_MATRIX.md`, `docs/NOVELTY_BOUNDARY_AND_REVIEWER_DEFENSE.md`, `reports/RELATED_WORK_AUDIT.md`, `paper/02_related_work_v9.md`
- Commands run: `web search primary sources for agent benchmarks`
- Evidence status: `RELATED_WORK_AUDIT_ONLY`
- Blockers: None

### 20_RELEASE_REPRODUCIBILITY_PACKAGE.md

- Status: `PARTIAL`
- What was done: Release/reproducibility docs and manifest created; no provider results included.
- Files created/modified: `REPRODUCIBILITY.md`, `ARTIFACT_EVALUATION_CHECKLIST.md`, `DATA_CARD_CAB.md`, `MODEL_CARD_EVALUATION_SUBJECTS.md`, `docs/INSTALL_AND_RUN.md`, `docs/REPRODUCE_COMPACT20_RESULTS.md`, `docs/REPRODUCE_MAIN_RESULTS.md`, `release/MANIFEST.json`, `release/README.md`, `release/EXCLUDED_FILES.md`
- Commands run: `bounded local file generation; no provider/API calls`
- Evidence status: `RELEASE_PACKAGE_NO_RESULTS`
- Blockers: No real results for reproduction

### 21_REVIEWER_SIMULATION_REBUTTAL_PACKET.md

- Status: `DONE`
- What was done: Simulated reviews and rebuttal matrix created with realistic limitations.
- Files created/modified: `reviews/SIMULATED_REVIEW_R1_SUPPORTIVE.md`, `reviews/SIMULATED_REVIEW_R2_SKEPTICAL.md`, `reviews/SIMULATED_REVIEW_R3_DOMAIN_EXPERT.md`, `reviews/REBUTTAL_PREEMPTION_MATRIX.md`, `reports/REVIEWER_SIMULATION_SUMMARY.md`
- Commands run: `bounded local file generation; no provider/API calls`
- Evidence status: `REVIEWER_SIMULATION_NO_RUN`
- Blockers: None

### 22_FINAL_SUBMISSION_GATE_VENUE_DECISION.md

- Status: `DONE`
- What was done: Final venue gate recommends not submitting as main paper.
- Files created/modified: `reports/FINAL_SUBMISSION_GATE.md`, `reports/VENUE_DECISION_MATRIX.md`, `paper/SUBMISSION_READINESS_CHECKLIST.md`
- Commands run: `bounded local file generation; no provider/API calls`
- Evidence status: `FINAL_GATE_NOT_SUBMITTABLE`
- Blockers: None

## 5. Code and Artifact Changes

Created no-run governance reports, Compact-20 review/blocked manifests, provider approval templates, gated provider notebooks, paper/release/reviewer documents, and final gate artifacts.

## 6. Tests, Audits, and Validation

- `python3 -m pytest -q tests/test_cab_insane_autorun_artifacts.py`: PASS, `4 passed`.
- `python3 scripts/check_evidence_safety.py`: PASS, C1-C8/C10 mock support blocked.
- `python3 scripts/check_claim_ledger.py`: PASS.
- `python3 -m pytest -q tests/test_first_3model_pilot_no_run.py tests/test_tiny_provider_pilot_governance.py tests/test_provider_pilot_preflight.py tests/test_no_api_fallback_governance.py tests/test_cab_insane_autorun_artifacts.py`: PASS, `41 passed`.
- Validation supports no scientific claims; it supports only no-run/governance readiness.

## 7. Kaggle / GPU / Colab Runbooks Prepared

| Project | Notebook/runbook path | Purpose | Platform | Accelerator | Estimated runtime | Import command |
| --- | --- | --- | --- | --- | ---: | --- |
| causal-agent-bench | `notebooks/provider_pilot/compact20_3model_provider_pilot_runbook.ipynb` | Provider/API runbook | local approved provider machine | CPU/network | See notebook runtime table | Postrun audit/evidence safety commands |
| causal-agent-bench | `notebooks/provider_pilot/naturalistic_ministudy_runbook.ipynb` | Provider/API runbook | local approved provider machine | CPU/network | See notebook runtime table | Postrun audit/evidence safety commands |
| causal-agent-bench | `notebooks/provider_pilot/main_500_provider_runbook.ipynb` | Provider/API runbook | local approved provider machine | CPU/network | See notebook runtime table | Postrun audit/evidence safety commands |
| causal-agent-bench | `notebooks/provider_pilot/5model_100task_provider_runbook.ipynb` | Provider/API runbook | local approved provider machine | CPU/network | See notebook runtime table | Postrun audit/evidence safety commands |

## 8. Evidence and Results

### Real Evidence Created

No provider-backed scientific evidence. Real local outputs are governance, configs, templates, blocked reports, and tests.

### Existing Evidence Reused

Existing no-run manifests, dry-run/smoke artifacts, candidate manifests, and docs were reused as context.

### Planned / Deferred / Not Yet Real Evidence

Compact-20 live provider pilot, human validation, C10 validation, postrun audit, ACRS/rank instability, real result tables/plots, scale-up, naturalistic mini-study, and Main-500.

## 9. Paper / Submission Readiness

Current paper level: no-run/blocked scaffold. Claims are not supported. Figure/table readiness is schema-only. Release readiness is partial. Realistic current venue level: not submittable as main paper; possible workshop/no-run methods discussion after cleanup. Highest possible after completion: NeurIPS D&B/DMLR candidate if real runs, validation, and release gates pass.

## 10. What Went Well

- Provider/API execution stayed blocked.
- Blank human review and approval artifacts are explicit.
- Claim architecture keeps unsupported claims unsupported.
- Related-work and reviewer-risk surfaces were updated.

## 11. What Failed or Was Blocked

- No explicit provider approval
- No live provider/API credentials checked or used
- No real Compact-20 provider run
- No real human validation
- C10 intervention isolation blocked
- Postrun audit/scorer sanity unavailable
- ACRS/tables/plots/failure gallery blocked
- Main-500 and scale-up blocked

## 12. What More Can Be Done

1. Complete real Compact-20 human review.
2. Obtain explicit provider/budget approval.
3. Run exactly one gated Compact-20 provider pilot.
4. Perform postrun audit/scorer sanity/evidence classification.
5. Only then generate ACRS, tables, plots, and paper claims.

## 13. Potential / Ceiling

Best case: a strong benchmark/evaluation paper around paired intervention stress tests and rank instability. Highest targets after completion: NeurIPS D&B or DMLR; current blockers are evidence, validation, and release completeness.

## 14. Final Verdict

PARTIAL_SUCCESS_BLOCKED_BY_MISSING_INPUTS

The project has a safer, clearer launch path, but no live evidence was created and scientific claims remain unsafe.
