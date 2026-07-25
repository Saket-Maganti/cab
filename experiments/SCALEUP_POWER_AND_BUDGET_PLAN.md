# Scale-Up Power And Budget Plan

Status: planning only. No cost was incurred.

## Minimum Model Count

- Compact-20: 3 models for pipeline shape, not ranking claims.
- 100-task: 5 models for preliminary ranking-instability analysis.
- Main-500: 5 or more models, with model families documented.

## Minimum Trajectory Count

Each task pair has clean and intervention conditions. Planned trajectory count is:

```text
tasks x 2 conditions x models x repeats
```

Compact-20 with 3 models and 1 repeat is 120 trajectories. Main-500 with 5 models and 1 repeat is 5,000 trajectories.

## Confidence Interval Behavior

Compact-20 CIs will be wide and mostly diagnostic. A 100-task pilot should narrow per-family estimates for common families. Main-500 is justified only when the goal is stable per-family and ranking claims.

## Stop/Go Gates

- Stop if human review finds isolation failures in primary families.
- Stop if scorer sanity fails on sampled trajectories.
- Stop if provider metadata is incomplete.
- Go to Main-500 only after preregistration, budget approval, and release plan freeze.
