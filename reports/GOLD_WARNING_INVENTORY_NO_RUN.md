# Gold Warning Inventory, No-Run

This inventory summarizes the existing no-run warning surface. It does not edit frozen data, apply fixes, or create evidence.

Labels: `engineering_only`, `manual_review_pending`, `no_provider_evidence`.

## Source Snapshot

- Source report: `reports/GOLD_OUTPUT_TRIAGE_COMPACT_PLAN.md`
- Total warnings: 507
- Manual-review queue items: 507
- Answer-changing-without-gold-change warnings: 500
- Main-benchmark blocker: gold-output confidence remains unresolved

## Inventory

| Warning type | Count | Families affected | Severity | Manual review required | Auto-fix allowed | Frozen data affected | Recommended action |
|---|---:|---|---|---|---|---|---|
| answer-changing-without-gold-change | 500 | primarily `tool_removal`; review also for `tool_failure`, `observation_conflict`, `stale_memory`, `premature_success_signal` | high | yes | no for ambiguous or frozen rows | possible, must inspect selected slice | Review only selected Compact-20/50 rows before any provider run. |
| other gold-output warnings | 7 | not fully expanded in static summary | medium | yes | no until classified | possible | Keep in manual queue; do not patch from aggregate report alone. |
| unresolved manual-review queue | 507 | all queued warning rows | high | yes | no | possible | Treat compact benchmark execution as blocked until selected rows are reviewed. |

## Interpretation

The warning count is not a result. It is a data-quality blocker. The safest path is compact-slice triage: select candidate pairs, review those pairs manually, exclude ambiguous cases, and leave broad main_500 repair for later.

