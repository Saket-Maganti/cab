# Compact Slice Data-Quality Checklist

Use this checklist for Compact-20/50 manual review before any provider/model run.

Labels: `engineering_only`, `manual_review_pending`, `no_provider_evidence`.

| Area | Current no-run status | Required before execution |
|---|---|---|
| Leakage | Static leakage docs exist; selected slice still needs row-level confirmation | Verify no prompt/gold leakage in each selected pair. |
| Duplicate or near-duplicate tasks | Not manually cleared for Compact-20 | Mark duplicate risk and exclude redundant pairs. |
| Gold-output consistency | 507 warnings exist; selected rows unresolved | Complete gold-policy review for every selected intervention. |
| Task clarity | No completed human review for Compact-20 | Human reviewer marks instruction clarity. |
| Intervention isolation | C10 unsupported | Reviewer checks target factor, non-target invariants, and goal preservation. |
| Answer-change policy | Family policy exists, but selected rows unresolved | Decide same/change/abstain/cannot-determine for each selected row. |
| Abstention policy | Allowed for several families when evidence is unavailable or conflicting | Record when abstention is acceptable. |
| Exclusion policy | Ambiguous rows must be excluded | Maintain `compact20_exclusion_log.csv`. |
| Frozen-data immutability | Frozen data must not be patched in no-run phase | Document issues only; patch non-frozen data later with review and tests. |

## Gate

Compact execution remains blocked until selected rows have completed task review, gold-policy review, exclusion decisions, and approval for provider calls.

