You are working in the Causal Agent Bench repository.

You are Codex acting as a compact benchmark curator, data-quality auditor, and no-run evidence-governance enforcer.

Task:
Curate a Compact-20 slice for future manual review and later provider execution, but do not execute model/provider/benchmark runs.

Current reality:
- No API key is available.
- Provider evidence is 0.
- The project needs a clean Compact-20 before any future run.
- Compact-20 must be designed for high information value, not scale.

Absolute rules:
- Do not call providers.
- Do not run local LLMs.
- Do not run benchmark/model/provider commands.
- Do not run dry-run unless explicitly safe and necessary; prefer no execution.
- Do not fabricate task quality judgments.
- Do not fabricate annotations.
- Do not promote claims.
- Do not mark assets eligible.
- Do not modify frozen data.

Inspect:
- experiments/COMPACT_EMPIRICAL_BENCHMARK_PLAN.md
- experiments/NO_API_COMPACT_VALIDATION_PLAN.md
- data/human_validation/no_api_task_review/
- docs/GOLD_POLICY_DECISION_MATRIX.md if present
- docs/COMPACT_SLICE_DATA_QUALITY_CHECKLIST.md if present
- reports/gold warning reports
- reports/high-risk intervention queue reports
- benchmark data manifests
- data/frozen/
- data/processed/
- intervention taxonomy files

Tasks:

1. Create Compact-20 selection criteria:
   - docs/COMPACT20_SELECTION_CRITERIA.md

Criteria:
- 20 paired items if available
- include clean + intervention pair references
- cover at least 4 families:
  - tool_removal
  - tool_failure
  - memory_corruption
  - observation_conflict
- maximize template/domain diversity
- include a controlled number of high-risk/gold-warning cases for review
- avoid duplicate/near-duplicate tasks
- prefer items with clear expected answer policy
- label all as no_run_manual_review_pending

2. Build a Compact-20 candidate manifest without running models:
   - data/human_validation/no_api_task_review/compact20_candidate_manifest.json
   - data/human_validation/no_api_task_review/compact20_candidate_manifest.md

If the exact data paths are unclear, create a manifest schema plus “candidate discovery blocked” status rather than guessing.

3. Create manual review CSVs:
   - data/human_validation/no_api_task_review/compact20_task_review.csv
   - data/human_validation/no_api_task_review/compact20_gold_policy_review.csv
   - data/human_validation/no_api_task_review/compact20_exclusion_log.csv

Reviewer fields must remain blank/TODO.

4. Create a “do not run yet” compact benchmark config plan:
   - configs/COMPACT20_CONFIG_PLAN_NO_RUN.md

This is not an executable config unless the repo already supports no-run planning safely. It must describe future fields:
- dataset slice path
- model/provider list placeholder
- budget cap placeholder
- trajectory cap
- evidence scope
- claim restrictions
- required preflight gates

5. Create status report:
   - reports/COMPACT20_NO_RUN_CURATION_STATUS.md

Must clearly state:
- curated or blocked
- no provider evidence
- no model outputs
- no human annotations unless already filled by user
- no claims supported
- what remains before future execution

6. Add/update tests:
- Compact-20 candidate manifest exists or blocked status exists
- reviewer fields not auto-filled
- no-run manifest cannot be used as results
- no paper asset eligibility from Compact-20 curation
- no provider keys in config plan

Allowed commands:
- static inspection
- targeted fixture-only tests
- py_compile if code changed

Final response:

# CAB Compact-20 No-Run Curation Report

## 1. Executive Summary
## 2. Files Added
## 3. Files Modified
## 4. Selection Criteria
## 5. Candidate Manifest
## 6. Manual Review CSVs
## 7. Config Plan
## 8. Tests Added/Updated
## 9. Commands Run
## 10. Commands Not Run
Confirm no provider/model/local LLM/benchmark runs.
## 11. Evidence State
## 12. Remaining Blockers
## 13. Next Best Action

Final verdict:
COMPACT20_NO_RUN_CURATION_READY
