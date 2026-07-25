# CAB No-Run Build Prompt Pack

This prompt pack is for the current reality of Causal Agent Bench:

- Strong infrastructure, but no real empirical evidence yet.
- No OpenAI API key is available.
- Live provider runs are blocked.
- Provider-backed evidence remains 0.
- Human annotations remain 0.
- Paper-eligible assets remain 0.
- NeurIPS Datasets & Benchmarks is not currently reachable without real runs and validation.
- The next phase is build/cleanup/curation only, not model execution.

## Non-negotiable rule

Do **not** execute provider/model/benchmark runs yet.

Across all prompts:

- Do not call providers.
- Do not run local LLMs.
- Do not run `causal_agent_bench run`.
- Do not run main_200.
- Do not run main_500.
- Do not run Compact-20 or Compact-50 as a model benchmark.
- Do not fabricate results.
- Do not fabricate annotations.
- Do not promote C1-C8/C10 claims.
- Do not mark paper assets eligible.
- Do not set `allow_paid_calls=true`.
- Do not store API keys in repo files.
- Keep all no-API outputs labeled `engineering_only`, `manual_review_pending`, and `no_provider_evidence`.

Allowed:

- Static inspection.
- File cleanup planning.
- Prompt/docs/paper editing.
- Manual-review packet preparation.
- Data-quality triage plans.
- Targeted fixture-only tests.
- `py_compile` / lint-like checks.
- No-provider evidence-safety checks if already safe in the repo.

## Recommended order

1. `01_reframe_claims_and_project_scope.md`
2. `02_gold_policy_and_data_quality_no_run.md`
3. `03_compact20_slice_curation_no_run.md`
4. `04_manual_validation_c10_packet.md`
5. `05_paper_skeleton_money_figure_specs.md`
6. `06_related_work_positioning.md`
7. `07_doc_bloat_freeze_and_archive_plan.md`
8. `08_future_3model_pilot_plan_no_execution.md`
9. `09_reviewer_defense_and_submission_strategy.md`
10. `10_final_no_run_build_gate.md`

## What “done” means for this pack

At the end, the repo should be cleaner and more paper-directed, but still honest:

- One sharp thesis.
- Causal overclaim reduced or defended carefully.
- Compact-20 manual slice prepared.
- Gold-policy issues triaged.
- C10/intervention-isolation manual validation packet ready.
- Paper skeleton rewritten around what will later be tested.
- Future 3-model pilot planned but not executed.
- No real evidence claimed.
- NeurIPS gate remains NOT_READY until real provider/model outputs and human validation exist.
