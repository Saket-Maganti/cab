You are working in the Causal Agent Bench repository.

You are Codex acting as an experiment planner, budget estimator, runbook author, and evidence-governance auditor.

Task:
Prepare a future 3-model Compact-20 pilot plan without executing any model/provider/local LLM runs.

Current reality:
- No OpenAI API key is available now.
- Provider-backed evidence is 0.
- The first real evidence later should be 3 models × Compact-20, not main_500.
- This task is planning only.

Absolute rules:
- Do not call providers.
- Do not run local LLMs.
- Do not run benchmark commands.
- Do not set allow_paid_calls=true.
- Do not create an executable live config unless it is clearly marked template/not approved/not runnable.
- Do not fabricate costs/results.
- Do not promote claims.

Inspect:
- configs/provider_pilot_tiny_APPROVED.yaml
- configs/README_COMPACT_EMPIRICAL.md
- experiments/COMPACT_EMPIRICAL_BENCHMARK_PLAN.md
- docs/FUTURE_PROVIDER_API_KEY_CHECKLIST.md
- data/human_validation/no_api_task_review/compact20_candidate_manifest.* if present
- docs/COMPACT20_SELECTION_CRITERIA.md if present
- docs/CLAIM_TRIAGE_NO_RUN.md

Tasks:

1. Create future pilot runbook:
   - experiments/FUTURE_3MODEL_COMPACT20_PILOT_RUNBOOK_NO_EXECUTION.md

Include:
- prerequisites
- API key/environment handling
- model/provider options
- exact gate sequence
- budget caps
- trajectory count
- what to run later
- what not to run
- post-run audit
- scorer sanity
- claim restrictions

2. Create non-runnable config template:
   - configs/compact20_3model_TEMPLATE_NOT_APPROVED.yaml

Must include:
- `allow_paid_calls: false`
- `approved_for_live_run: false`
- `template_only: true`
- `not_runnable_without_approval: true`
- no API keys
- placeholder provider/model list
- compact20 slice path placeholder
- budget cap placeholder
- evidence scope preliminary only
- scientific claims false

3. Create budget/runtime planning sheet:
   - experiments/COMPACT20_3MODEL_BUDGET_RUNTIME_PLAN.md

Use ranges only unless repo estimate tool already has static known estimates. Do not invent exact costs. Include:
- 3 models
- 20 paired items
- clean + intervention count
- possible call multiplier
- low/high estimate placeholders
- approval thresholds
- stop conditions

4. Create future result schema:
   - reports/COMPACT20_3MODEL_RESULT_SCHEMA.md

Define required fields for future results:
- model
- provider
- task_id
- intervention_type
- clean success
- intervention success
- ACRS
- confidence interval
- scorer issue flags
- human validation status
- evidence scope
- eligibility status

5. Add/update tests:
- template not runnable
- allow_paid_calls false
- no API keys in template
- no claim support from template
- compact20 future schema exists

Allowed commands:
- static inspection
- targeted fixture tests
- py_compile if code changed

Final response:

# Future 3-Model Compact-20 No-Execution Plan Report

## 1. Executive Summary
## 2. Files Added
## 3. Files Modified
## 4. Future Pilot Design
## 5. Config Template Safety
## 6. Budget/Runtime Plan
## 7. Future Result Schema
## 8. Tests Added/Updated
## 9. Commands Run
## 10. Commands Not Run
Confirm no provider/model/local LLM/benchmark runs.
## 11. Evidence State
## 12. Remaining Blockers
## 13. Next Best Action

Final verdict:
FUTURE_3MODEL_PILOT_PLAN_READY
