# Prompt 04 — Compact-20 Slice Finalization and Gold Repair

You are working in `/Users/saketmaganti/Projects/causal-agent-bench`.

You are Codex acting as a benchmark data curator, task-quality auditor, and gold-output repair engineer.

## Task

Finalize the Compact-20 slice so it is safe to use for the first real pilot. Fix task/gold/scorer issues without running models.

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



## Inspect

- Compact-20 manifest/path
- task schemas
- generated tasks
- intervention definitions
- `docs/GOLD_OUTPUT_POLICY.md`
- gold warning reports
- leakage reports
- high-risk intervention queue
- scorer code
- existing task review CSVs

## Actions

1. Create `data/compact20_reviewed/` if appropriate.
2. Create `compact20_reviewed_manifest.json`, `compact20_task_quality_report.md`, `compact20_gold_repair_report.md`, and `compact20_exclusion_list.csv`.
3. Inspect every candidate pair for clarity, deterministic gold answer, intervention goal preservation, scorer compatibility, leakage risk, and ambiguity.
4. Repair or exclude bad tasks.
5. Ensure exactly 20 reviewed clean/intervention pairs remain, or report why fewer remain.
6. Create `compact20_readiness.json` with paper eligibility false and human validation required.

## Deliverables

- `data/compact20_reviewed/compact20_reviewed_manifest.json`
- `data/compact20_reviewed/compact20_task_quality_report.md`
- `data/compact20_reviewed/compact20_gold_repair_report.md`
- `data/compact20_reviewed/compact20_exclusion_list.csv`
- `data/compact20_reviewed/compact20_readiness.json`

## Tests / Checks

- exactly 20 pairs or explicit blocked status
- no duplicate task IDs
- clean and intervention condition for each pair
- expected answer/gold policy present
- no human-validation claim
- paper eligibility false

## Allowed Commands

- Static inspection commands.
- `git status --short --branch`
- `git diff --stat`
- `python3 scripts/check_evidence_safety.py`
- Targeted fixture-only pytest when needed.

## Final Response Format

# Prompt 04 — Compact-20 Slice Finalization and Gold Repair Report

## 1. Executive Summary
## 2. Files Added
## 3. Files Modified
## 4. Evidence State
## 5. Tests/Checks Run
## 6. Commands Not Run
## 7. Blockers
## 8. Next Best Action

Final verdict must be one of:

- `COMPACT20_REVIEWED_READY_FOR_HUMAN_REVIEW`
- `COMPACT20_BLOCKED_NEEDS_TASK_REPAIR`
- `COMPACT20_INSUFFICIENT_VALID_PAIRS`
