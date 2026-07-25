# CAB Insane Uplift Prompt Pack — Order and Gates

## Mission

Move Causal Agent Bench from **pure scaffold / C9-only engineering evidence** to a paper-grade benchmark with real agent runs, human validation, audited ACRS/rank-instability results, release artifacts, and an honest NeurIPS D&B / DMLR submission gate.

## Current Known Reality

- Root path: `/Users/saketmaganti/Projects/causal-agent-bench`
- Current state from external audit: scaffold-heavy, no real provider-backed evidence, no human validation, every scientific claim planned except C9 engineering-only.
- The strongest paper thesis is not “we built infrastructure”; it is:  
  **success-only leaderboards can mismeasure tool-using LLM-agent capability because controlled perturbations reveal hidden brittleness, degradation profiles, and ranking instability.**

## Global Rules

## Global Evidence Rules

- Do not fabricate results, human annotations, provider outputs, costs, or reviewer labels.
- Do not promote C1-C8/C10 unless the required real evidence exists and the evidence-safety checks pass.
- C9 may remain `engineering_only`; stub/mock/dry-run outputs can only support pipeline wiring.
- Do not mark paper assets eligible manually.
- Do not store API keys, tokens, or secrets in YAML, Markdown, JSON, logs, CSVs, or repo files.
- Provider credentials must be checked only through environment presence checks without printing values.
- Do not leave `allow_paid_calls=true` after any live run.
- Do not run providers, local LLMs, `causal_agent_bench run`, `main_200`, `main_500`, Compact-50, or broad sweeps unless the prompt explicitly allows it and every gate passes.
- Always distinguish `engineering_only`, `zero_cost_local_preliminary`, `provider_pilot_preliminary`, `paper_candidate_pending_audit`, and `paper_eligible`.


## Phase Order

### Phase A — Stop scaffold bleed
1. `01_REPO_REALITY_FREEZE_AND_COMMIT_HYGIENE.md`
2. `02_DOC_SPRAWL_ARCHIVE_AND_PROJECT_SURFACE.md`
3. `03_SINGLE_THESIS_CLAIM_LEDGER_REFOCUS.md`

### Phase B — Make Compact-20 scientifically runnable
4. `04_COMPACT20_SLICE_FINALIZATION_GOLD_REPAIR.md`
5. `05_REAL_HUMAN_REVIEW_PACKET_NOT_PROXY.md`
6. `06_C10_INTERVENTION_ISOLATION_VALIDATION.md`

### Phase C — First real evidence
7. `07_3MODEL_COMPACT20_CONFIG_APPROVAL_NO_SECRETS.md`
8. `08_3MODEL_COMPACT20_PRELIVE_PREFLIGHT.md`
9. `09_EXECUTE_3MODEL_COMPACT20_PROVIDER_PILOT_GATED.md`
10. `10_POSTRUN_AUDIT_SCORER_SANITY_EVIDENCE_CLASSIFICATION.md`

### Phase D — Paper hook from real results
11. `11_ACRS_RANK_INSTABILITY_STATS.md`
12. `12_REAL_RESULT_TABLES_AND_MONEY_PLOTS.md`
13. `13_FAILURE_GALLERY_QUALITATIVE_FINDINGS.md`

### Phase E — Uplift ceiling
14. `14_BASELINE_AGENT_ABLATION_UPGRADES.md`
15. `15_SCALE_TO_5MODEL_100TASK_STUDY.md`
16. `16_NATURALISTIC_TRANSFER_MINISTUDY.md`
17. `17_MAIN_500_DESIGN_AND_RUN_GATE.md`

### Phase F — Paper/release/submission
18. `18_PAPER_REWRITE_NEURIPS_DB_DMLR.md`
19. `19_RELATED_WORK_NOVELTY_DEFENSE.md`
20. `20_RELEASE_REPRODUCIBILITY_PACKAGE.md`
21. `21_REVIEWER_SIMULATION_REBUTTAL_PACKET.md`
22. `22_FINAL_SUBMISSION_GATE_VENUE_DECISION.md`

## Fast Start

Use `23_QUICK_START_NEXT_ACTION_PROMPT.md` if you want Codex to begin immediately without running providers.

## Stop Rule

If a prompt discovers that the required evidence, approval, credentials, or human review is missing, it must create a blocker report and stop. Partial honest progress is better than fake completion.
