# 14 Statistical Analysis Audit

## Outputs produced on deterministic pilot

Run analyzed: `results/20260519T053609Z_pilot_20_multi_agent_stub`

Produced files include `analysis_report.md`, `paper_assets/statistical_summary.json`, `paper_assets/stats_summary.json`, `paper_assets/stats_summary.md`, rank instability assets, and paired clean-vs-intervention tables.

`statistical_summary.json` reports:

- bootstrap summaries by agent
- bootstrap summaries by intervention family
- paired clean-vs-intervention comparisons
- effect sizes
- rank correlation between clean success and ACRS
- warnings for multiple comparisons and small sample sizes

## Validity

The analysis code is aligned with the paired design and correctly emits warning metadata. On the fresh stub run, Spearman and Kendall clean-vs-ACRS rank correlations were both 1.0, but this is engineering-only because all providers are local stubs.

## Missing before NeurIPS-quality reporting

- Real provider-backed sample sizes.
- Confidence intervals and paired tests linked to claim-ledger evidence rows.
- Human validation or adjudication for trajectory diagnostics.
- Multiple-comparison framing in paper text.

