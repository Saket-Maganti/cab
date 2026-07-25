# ACRS Formalization And Limitations

Status: metric specification, not a result.

## Definition

For an agent `a` over paired task set `T`:

```text
clean_success(a) = mean success on clean tasks
intervention_success(a) = mean success on paired intervention tasks
ACRS(a) = intervention_success(a) / clean_success(a)
```

ACRS is undefined when `clean_success(a) = 0`.

## Companion Metrics

- absolute degradation = `clean_success - intervention_success`
- relative degradation = `1 - ACRS`
- per-family ACRS = family intervention success divided by clean success
- macro-family ACRS = unweighted mean across family ACRS values
- micro-family ACRS = pooled intervention success divided by clean success
- worst-family robustness = minimum valid per-family ACRS
- recovery score = recovery behavior rate on recoverable failures
- abstention correctness = correct uncertainty/refusal when evidence is insufficient

## Interpretation

High ACRS means intervention success is close to clean success. It does not necessarily mean the agent is strong. An agent with poor clean and intervention success can have a high ACRS. Report ACRS only with clean success, intervention success, `n`, confidence intervals, and validity status.

## Limitations

- Undefined when clean success is zero.
- Sensitive to small denominators and small paired samples.
- Cannot distinguish robust success from uniformly poor performance.
- Cannot validate intervention isolation.
- Cannot replace human review for ambiguity, abstention, or scorer disagreement.
- Does not by itself prove causality.

## Claim Boundary

Until Compact-20 has real provider trajectories, real human review, scorer sanity, and C10 validation, ACRS remains a planned metric.
