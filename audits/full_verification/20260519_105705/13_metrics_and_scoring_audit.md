# 13 Metrics and Scoring Audit

## Implemented metric behavior

Scoring computes final success, clean/intervention success, ACRS, intervention degradation, tool-use diagnostics, invalid tool calls, argument validity, recovery, repeated failures, contradiction/memory diagnostics, stopping behavior, trajectory efficiency, and aggregate summaries.

ACRS behavior observed in code/tests:

- `ACRS = intervention_success_rate / clean_success_rate`
- If clean success is zero or undefined, ACRS is undefined rather than infinite or fabricated.
- Per-family breakdowns are exported.
- Clean/intervention pairing is preserved by base task.

## Tests

The full suite includes tests for ACRS edge cases, ranking instability, metrics v2 undefined ACRS, statistical outputs, and scoring/report exports. Final suite status: `244 passed, 1 skipped`.

## Risks

- ACRS is not scientifically meaningful for only local stubs or oracle sanity checks.
- Small per-family sample sizes trigger warnings in the deterministic pilot statistical summary.
- Oracle results must remain excluded from realistic model ranking and claim support.

