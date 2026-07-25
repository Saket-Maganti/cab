You are working in the Causal Agent Bench repository.

You are Codex acting as a benchmark data-quality auditor, gold-policy reviewer, intervention-validity reviewer, and no-run evidence-governance enforcer.

Task:
Tackle the gold-output and data-quality problems without executing provider/model/benchmark runs.

Current reality:
- Gold-output warnings exist, including answer-changing-without-gold-change cases.
- High-risk intervention queue exists.
- Provider evidence is 0.
- The goal is to clean and prepare the compact slice, not run models.

Absolute rules:
- Do not call providers.
- Do not run local LLMs.
- Do not run any benchmark/model/provider command.
- Do not run main_200/main_500/Compact-20/Compact-50.
- Do not edit frozen data directly.
- Do not auto-fix ambiguous gold answers.
- Do not fabricate gold answers.
- Do not fabricate annotations.
- Do not promote claims.

Inspect:
- docs/GOLD_OUTPUT_POLICY.md
- reports/GOLD_OUTPUT_TRIAGE_COMPACT_PLAN.md
- reports/gold-output reports
- reports/high-risk intervention queue reports
- data/frozen/
- data/processed/
- benchmark generation scripts
- intervention taxonomy/spec docs
- tests covering gold policy or intervention data

Tasks:

1. Create a gold-warning inventory:
   - reports/GOLD_WARNING_INVENTORY_NO_RUN.md
   - reports/gold_warning_inventory_no_run.csv

For each warning type, summarize:
- count
- intervention families affected
- severity
- whether manual review is required
- whether auto-fix is allowed
- whether frozen data is affected
- recommended action

2. Create a compact-slice data-quality checklist:
   - docs/COMPACT_SLICE_DATA_QUALITY_CHECKLIST.md

It must include:
- leakage status
- duplicate/near-duplicate status
- gold-output consistency
- task clarity
- intervention isolation
- answer-change policy
- abstention policy
- exclusion policy
- frozen-data immutability rule

3. Create a gold policy decision matrix:
   - docs/GOLD_POLICY_DECISION_MATRIX.md

For each family:
- tool_removal
- tool_failure
- memory_corruption
- observation_conflict
- stale_memory
- premature_success_signal
- any other repo-defined families

Define:
- should gold remain same?
- should gold change?
- when is abstention acceptable?
- when is “cannot determine” acceptable?
- when should item be excluded?
- when human review is mandatory?

4. Create a no-run gold-fix plan:
   - reports/GOLD_OUTPUT_NO_RUN_FIX_PLAN.md

Do not apply fixes unless unambiguous and non-frozen. If code patches are needed, propose them but keep them behind tests and explicit human review.

5. Add/update tests:
- gold policy matrix exists
- answer-changing interventions require review
- ambiguous gold cases cannot be auto-fixed
- frozen data cannot be modified
- no-API/no-run outputs cannot support empirical claims

Allowed commands:
- static inspection
- targeted fixture-only tests
- py_compile if code changed
- evidence safety check if already safe

Final response:

# CAB Gold Policy/Data Quality No-Run Report

## 1. Executive Summary
## 2. Files Added
## 3. Files Modified
## 4. Gold Warning Inventory
## 5. High-Risk Intervention Summary
## 6. Gold Policy Decision Matrix
## 7. Fix Plan
## 8. Tests Added/Updated
## 9. Commands Run
## 10. Commands Not Run
Confirm no provider/model/local LLM/benchmark runs.
## 11. Evidence State
## 12. Remaining Blockers
## 13. Next Best Action

Final verdict:
NO_RUN_GOLD_POLICY_TRIAGE_COMPLETE
