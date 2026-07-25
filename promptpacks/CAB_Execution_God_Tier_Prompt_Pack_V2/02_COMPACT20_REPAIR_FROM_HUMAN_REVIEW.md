# Prompt 02 — Compact-20 Repair from Human Review

You are working in `/Users/saketmaganti/Projects/causal-agent-bench`.

You are Codex acting as a benchmark curator and gold-policy repair engineer.

## Task

Use completed real human reviews to repair or exclude bad Compact-20 items. If human review is missing, block.

## Absolute rules

- Do not fabricate reviews.
- Do not edit human review rows.
- Do not run providers/local LLMs.
- Do not run benchmark trajectories.
- Do not hide excluded tasks.
- Do not force exactly 20 if valid reviewed items are fewer.
- Do not mark final paper eligibility.

## Preconditions

Proceed only if `reports/HUMAN_REVIEW_COMPLETION_STATUS.md` says:

`HUMAN_REVIEW_COMPLETE_READY_FOR_ANALYSIS`

Otherwise create a blocked report and stop.

## Inspect

- human review CSVs
- Compact-20 manifest
- gold repair report
- exclusion list
- scorer code/policies
- task schemas
- intervention taxonomy

## Actions

1. Join human review rows to Compact-20 manifest.
2. Identify tasks with:

- unclear task wording,
- unclear expected answer,
- gold answer disputed,
- intervention does not preserve goal,
- intervention does not isolate factor,
- required abstention unclear,
- scorer incompatible,
- high disagreement.

3. Create repaired derivative slice:

- `data/compact20_locked/compact20_locked_manifest.json`
- `data/compact20_locked/compact20_locked_tasks.jsonl` if supported
- `data/compact20_locked/compact20_locked_exclusions.csv`
- `reports/COMPACT20_HUMAN_REVIEW_REPAIR_REPORT.md`

4. If fewer than 20 valid pairs remain, choose one of:

- replenish from candidate pool if available and review exists,
- block and request additional human review,
- create `compactN_locked` with honest N.

5. Write machine-readable readiness:

- `data/compact20_locked/compact20_locked_readiness.json`

Fields:

```json
{
  "slice_name": "compact20_locked",
  "human_reviewed": true,
  "task_pairs_total": null,
  "paper_eligible": false,
  "ready_for_c10_analysis": true,
  "ready_for_provider_pilot": false,
  "known_blockers": []
}
```

## Tests/checks

Add/update tests:

- locked slice uses only human-reviewed tasks,
- excluded tasks are not present,
- no proxy reviews accepted,
- every kept intervention has pass/fail status,
- paper eligibility false.

## Final response format

# Compact-20 Human-Review Repair Report

## 1. Executive Summary
## 2. Input Review Status
## 3. Tasks Kept
## 4. Tasks Repaired
## 5. Tasks Excluded
## 6. Locked Slice
## 7. Remaining Issues
## 8. Tests Run
## 9. Commands Not Run
## 10. Next Best Action

Final verdict:

- `COMPACT20_LOCKED_READY_FOR_C10`
- `COMPACT20_BLOCKED_MISSING_HUMAN_REVIEW`
- `COMPACT20_BLOCKED_TOO_FEW_VALID_PAIRS`
- `COMPACT20_LOCKED_WITH_SMALLER_N`
