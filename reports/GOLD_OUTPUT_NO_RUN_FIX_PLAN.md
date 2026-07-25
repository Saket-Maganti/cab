# Gold Output No-Run Fix Plan

Labels: `engineering_only`, `manual_review_pending`, `no_provider_evidence`.

## Verdict

Do not apply broad gold-output fixes now. The current state is a manual-review blocker, not an automated repair queue.

## Plan

1. Use `docs/GOLD_POLICY_DECISION_MATRIX.md` for family-level policy.
2. Limit first triage to the Compact-20 candidate manifest.
3. For every candidate, complete `compact20_gold_policy_review.csv`.
4. Exclude ambiguous rows rather than patching them.
5. Document frozen-data issues without editing frozen files.
6. Patch non-frozen processed data only after human review, an explicit rationale, and a targeted fixture test.

## Code Patch Policy

No code patch is required from the aggregate warning count alone. If later review finds a deterministic generator bug, patch the generator or validation rule behind tests; do not hand-edit frozen artifacts.

## Current Blockers

- 507 gold-output warnings remain queued for manual review.
- 500 answer-changing-without-gold-change warnings need special attention.
- C1-C8 and C10 remain unsupported.

