# CAB V3 Statistical Analysis Plan

Status: no-execution plan. Do not compute or report results from this document.

## Primary Analyses

- paired clean vs intervention success by base task,
- ACRS and absolute/relative degradation by agent,
- per-family ACRS and degradation,
- macro-family and micro-family robustness,
- rank shift between clean success and ACRS,
- scorer-adjusted success only after manual review exists.

## Tests

- Paired binary success: McNemar or paired bootstrap.
- Continuous/aggregate degradation: paired bootstrap and paired permutation where appropriate.
- Family comparisons: exploratory unless preregistered and corrected.
- Multiple comparisons: Holm for confirmatory families; Benjamini-Hochberg for exploratory tables.

## Minimum N For Claims

| scale | allowed claims |
|---|---|
| Compact-20 | pipeline readiness, task-review completion, no headline model ranking |
| 100-task | directional pilot with wide CIs, limited family claims |
| Main-500 | headline claims if preregistered, complete, and validated |

## Null Results

Null results must be reported as informative when powered. Underpowered nulls must be labeled inconclusive.

## Incomplete Runs

Incomplete, interrupted, mock, stub, dry-run, and proxy-review artifacts are excluded from scientific estimates.
