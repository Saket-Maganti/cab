# Prompt 3 — Scorer Calibration, Gold Policy, and Gold-Output Warning Triage

You are working in the Causal Agent Bench repository.

You are Cursor Composer acting as a benchmark validity reviewer, scoring-system auditor, and gold-policy designer.

## Mission

Fix the two largest validity risks before any main benchmark:

1. The deterministic scorer may be brittle on real LLM prose.
2. Gold-output warnings, especially answer-changing interventions such as tool_removal, may invalidate intervention success metrics.

## Starting assumptions

- Tiny provider pilot has been run and audited, or if not, this prompt must stop after static triage.
- There are gold-output warnings, including answer-changing interventions without gold changes.
- No human validation claims exist yet.
- Main benchmark is not ready.
- No claims should be promoted.

## Absolute rules

Do not:

- fabricate human judgments
- fabricate gold answers
- auto-fix ambiguous gold cases
- mark empirical assets eligible
- promote claims
- run providers unless explicitly approved in a later prompt
- edit frozen data automatically
- suppress warnings without rationale

Allowed:

- manually review tiny pilot outputs
- create scorer calibration reports
- improve scorer only with tests
- create manual-review queues
- patch non-frozen processed data only if unambiguous and documented
- define gold-policy rules
- run fixture-only tests
- run no-run reports

## Tasks

### 1. Scorer calibration from tiny pilot

If tiny provider outputs exist:

For every trajectory:

- compare deterministic scorer to manual human judgment
- classify mismatch:
  - paraphrase mismatch
  - unit/format mismatch
  - partial answer mismatch
  - abstention correctness mismatch
  - irrelevant final-answer mismatch
  - hallucinated correct substring
  - false positive
  - false negative

Create:

- `reports/SCORER_CALIBRATION_TINY_PILOT.md`
- `reports/SCORER_CALIBRATION_TINY_PILOT.csv`

If no provider outputs exist, create `reports/SCORER_CALIBRATION_BLOCKED_NO_PROVIDER_OUTPUTS.md` and stop after static gold triage.

### 2. Improve scorer safely

Inspect scorer code.

Improve only if evidence supports it.

Possible improvements:

- exact normalized answer match
- numeric tolerance
- date/time normalization
- list/set matching
- abstention-aware scoring
- structured answer schemas
- domain-specific validators
- optional human-review flag for ambiguous cases

Do not add LLM judge as a required scorer.

Any scoring change must include fixture tests and a migration note.

### 3. Gold policy document

Create/update `docs/GOLD_OUTPUT_POLICY.md`.

It must define for each intervention family:

- whether expected final answer should remain same
- whether expected final answer should become abstention / limitation-aware
- whether multiple acceptable answers are allowed
- whether scoring requires structured validator
- when human review is mandatory

Special attention:

- `tool_removal`
- `tool_failure`
- `observation_conflict`
- `memory_corruption`
- `premature_success_signal`
- `stale_memory`

### 4. Gold-output warning triage

Inspect gold-output warning reports/CSVs.

Create:

- `reports/GOLD_OUTPUT_TRIAGE_PLAN.md`
- `reports/GOLD_OUTPUT_MANUAL_REVIEW_PRIORITIZED.csv`

Group by:

- intervention type
- dataset
- blocker vs warning
- pilot vs main impact
- answer-changing without gold change
- suggested action
- whether safe to auto-fix
- required reviewer question

Do not auto-fix ambiguous cases.

### 5. Patch safe cases

For non-frozen processed data only:

If a gold issue is unambiguous and policy-defined, create patch.

If not, leave manual-review item.

For frozen data, never patch automatically. Create a new candidate version instead.

### 6. Update validity scorecard

Ensure scorecard reflects:

- scorer calibration status
- gold-output policy status
- remaining gold warning count
- main benchmark readiness impact

### 7. Tests

Add/update tests for:

- scorer handles real pilot paraphrase cases if available
- abstention-aware scoring
- no hallucinated substring false positives
- gold policy blocks auto-fix for ambiguous cases
- gold triage creates prioritized CSV
- validity scorecard worsens if gold warnings remain

### 8. Safe validation

Run:

```bash
python3 scripts/check_evidence_safety.py
python3 -m causal_agent_bench all-no-run-reports --output-dir /tmp/cab_scorer_gold_policy
python3 -m causal_agent_bench validity-scorecard --output-dir /tmp/cab_scorer_gold_policy/validity_scorecard
```

Run targeted fixture-only tests.

## Final response format

# Scorer Calibration and Gold Policy Report

## 1. Executive Summary
## 2. Provider Output Availability
## 3. Scorer Calibration Findings
## 4. Scorer Changes
## 5. Gold Policy
## 6. Gold-Output Triage
## 7. Safe Patches
## 8. Remaining Manual Review
## 9. Validity Scorecard Impact
## 10. Tests Added/Updated
## 11. Commands Run
## 12. Commands Not Run
## 13. Evidence State
## 14. Remaining Blockers
## 15. Next Step

Success condition:

- scorer risk is quantified
- gold policy is documented
- high-priority gold warnings are resolved or queued
- no fake results or unsupported claims
