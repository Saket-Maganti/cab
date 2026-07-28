# RAAC ablation plan

Status: `DESIGN_ONLY`; execution is pending. This document freezes treatment
arms and analysis rules without making result claims.

## Primary treatment arms

1. standard tool use;
2. `RAAC_LIGHT`;
3. `RAAC_FULL` on the preregistered feasible subset.

Direct answer, ReAct-style, and self-check are method baselines. The oracle
engineering-only wrapper is a plumbing upper control, not a behavioral
baseline and not paper evidence.

## Component ablations

| Arm | Frozen change | Diagnostic question |
|---|---|---|
| `VERIFY_ONLY` | Remove retry, alternate route, cross-check, and clarification | Does verification alone account for recovery? |
| `RETRY_ONLY` | Retain same-tool retry only | Are gains only repeated attempts? |
| `ABSTAIN_ONLY` | Abstain at the first observable anomaly | Does indiscriminate caution inflate apparent robustness? |
| `NO_CROSS_CHECK` | Remove independent contradiction checks | Are conflict-resolution effects cross-check dependent? |
| `NO_ALTERNATE_ROUTE` | Remove alternate tools/routes | Is route diversity necessary after persistent failure? |
| `NO_FINAL_VERIFY` | Remove the final verification stage | Does final verification prevent premature success? |

## Outcomes

Primary analysis uses paired final success and paired degradation under the
repository's frozen inference protocol. RAAC-specific secondary outcomes are:

- recovery success per recovery opportunity;
- contradiction resolution per verification opportunity;
- correct and false abstention with separate denominators;
- premature-success verification;
- clean success and clean false-abstention trade-off;
- realized model, tool, token, latency, and wall-clock overhead.

Opportunity flags come from observable trace signals. Treatment-effect scoring
may use evaluator labels after execution, but controller inputs must remain
blind to them.

## Comparison sequence

1. Run fixture-only policy invariants.
2. Freeze code, configs, task slice, model revision, prompts, and scorer.
3. Run equal-budget standard tool use versus LIGHT.
4. Run practical-budget standard, LIGHT, and feasible FULL subset.
5. Run ablations on the frozen preregistered subset only.
6. Audit merge completeness, traces, opportunity denominators, and evidence
   classes before any treatment analysis.
7. Report null effects, clean regressions, false abstention, and overhead.

No arm or task may be selected using observed model performance. Any post hoc
subset is labeled exploratory.

## Statistical reporting

Use paired differences at the base-task level with the frozen clustered or
paired bootstrap procedure. Report effect estimates, uncertainty intervals,
pair counts, opportunity counts, clean-side trade-offs, and realized overhead.
Do not claim a RAAC improvement from fixture output, unpaired aggregates, or an
opportunity denominator below the preregistered threshold.
