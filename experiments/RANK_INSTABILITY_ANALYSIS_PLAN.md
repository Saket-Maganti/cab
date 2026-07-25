# Rank Instability Analysis Plan

Status: no-execution plan.

## Question

Do model rankings by clean success differ from rankings by robustness under controlled interventions?

## Metrics

- clean-success rank,
- ACRS rank,
- intervention-success rank,
- Spearman correlation,
- Kendall correlation,
- rank delta per model,
- tied-rank sensitivity.

## Requirements

- at least 5 non-oracle models for headline rank-instability claims,
- complete paired task coverage for each model,
- confidence intervals from task-level bootstrap,
- scorer sanity and C10 validation complete,
- ties handled with average-rank or stable documented tie policy.

## Reporting

Report rank movement with uncertainty. Do not call a rank reversal meaningful if confidence intervals overlap heavily or if the sample is Compact-20 only.
