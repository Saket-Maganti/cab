# Scorer Sanity Blocked - No Provider Outputs

## Verdict

Scorer sanity calibration on real provider trajectories is blocked.

## Reason

The current run-health report contains zero paper-eligible provider-backed runs
and no completed tiny provider pilot. Existing runs are engineering, mock,
stub, or interrupted. They are useful for software checks, not for scientific
scorer calibration.

## Required Provider-Pilot Review Table

When a tiny provider pilot exists, create:

- `reports/SCORER_SANITY_TINY_PROVIDER_PILOT.md`
- `reports/SCORER_SANITY_TINY_PROVIDER_PILOT.csv`

Required CSV columns:

```csv
trajectory_id,instance_id,intervention_family,expected_answer,model_final_answer,deterministic_scorer_result,manual_human_judgment,agreement_yes_no,mismatch_category,fix_needed,notes
```

## Allowed Future Scorer Upgrades

Only evidence-supported upgrades are allowed:

- numeric tolerance
- date/time normalization
- list or set matching
- abstention-aware scoring
- structured answer validators
- manual-review-needed flag for ambiguous answers

LLM judging must not become the default required scorer.

## Current Action

No scorer code was changed because there are no real provider outputs to justify
a calibration patch.
