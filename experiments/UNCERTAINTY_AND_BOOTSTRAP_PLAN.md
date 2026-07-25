# Uncertainty And Bootstrap Plan

Status: no-execution plan.

## Bootstrap Unit

Resample base-task pairs, not individual clean/intervention rows. This preserves pairing.

## Recommended Intervals

- 95% percentile bootstrap for pilot reports.
- BCa intervals for final reports if stable.
- Wilson intervals for simple success-rate cards.
- Rank-correlation CIs by resampling paired task IDs.

## Small-Sample Policy

When `n < 20` per family, report estimates as exploratory and avoid family-level claims. When clean success is zero, ACRS is undefined and the report should use absolute rates and qualitative failure analysis instead.

## Missing Data

Missing trajectories must be reported as incomplete. Do not impute missing provider trajectories for scientific claims.
