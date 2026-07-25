# CAB Paired Metric and Statistical Audit

> Canonical maximum-ceiling artifact. Regenerate with `python3 scripts/generate_cab_max_ceiling_reports.py`.

Generated: 2026-07-23T17:23:44.726749+00:00

## Matched unit

`(model, base_task_id, intervention_id_or_family, repeat_id)`

Clean and intervention rows are joined by exact base task and repeat. Missing rows, duplicate repeats, and malformed units are retained with an invalid-pair reason and excluded from paired endpoints; they are never averaged silently.

## Pair outcomes

Clean/intervention success, success→success, success→failure, failure→success, failure→failure, absolute and conditional degradation, recovery, abstention correctness, invalid reason, and completeness state are materialized per pair.

## Metric suite

- Clean/intervention success and paired absolute/relative degradation.
- ACRS ratio with explicit zero/near-zero denominator suppression.
- Conditional robustness among clean successes.
- Macro, micro, family, and worst-family robustness.
- Transition profiles, recovery, correct/false abstention.
- Rank shift, Spearman/Kendall correlation, rank bootstrap/probability.
- Scorer-error sensitivity analysis.

## Inference and dependence

Paired bootstrap, cluster bootstrap by base task, stratified bootstrap by family, paired binary tests, confidence intervals, effect sizes, multiple-comparison correction, rank bootstrap, and scorer sensitivity are available. Reports expose intervention-pair, base-task, template, domain, family, and clustering-unit counts to prevent pseudoreplication.

## Frozen analysis plan

- Primary: paired degradation; conditional robustness; family macro robustness; rank uncertainty/change.
- Secondary: recovery; abstention; tool-family profiles; error taxonomy; scorer-adjusted analysis.
- Exploratory: anything defined after viewing outcomes, explicitly labeled.

## Exact family-denominator fixture

- Check: `phase5_matched_family_denominator_fixture_v1`
- Global clean rate: `None`
- Exact family-matched clean rate: `None`
- Passed: `True`
- Command: `/Library/Frameworks/Python.framework/Versions/3.11/bin/python3 -c 'import json; from causal_agent_bench.metrics.causal_robustness import paired_metrics_fixture_self_check as f; r=f(); print(json.dumps(r, sort_keys=True)); raise SystemExit(0 if r.get('"'"'passed'"'"') else 1)'`
- Exit code / elapsed: `0` / `0.109` seconds
- Evidence class: `FIXTURE_ONLY`; no empirical effect or ranking is asserted.
