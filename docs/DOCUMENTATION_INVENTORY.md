# Documentation Inventory

Labels: `engineering_only`, `manual_review_pending`, `no_provider_evidence`.

This pass inspected top-level markdown, `docs/`, `reports/`, `paper/`, and `experiments/` at a planning level. The CSV companion lists the highest-risk public, paper, evidence, and meta-governance documents touched by the no-run prompt pack. A full delete/move pass is intentionally deferred.

## Inventory Summary

| Category | Recommendation | Reason |
|---|---|---|
| Evidence and claim gates | Keep public | They prevent overclaiming and keep blockers visible. |
| Paper skeleton and strategy | Keep internal until evidence exists | They are useful authoring scaffolds but not results. |
| Manual review packets | Keep internal | They prepare validation but contain no completed annotations. |
| Future runbooks and templates | Keep internal | They are not approved live configs. |
| "God-tier" or war-room branding | Archive from public release later | It reads as process theater to reviewers. |
| Old audits and mock reviews | Keep internal or archive after results | Useful history, but noisy in a release bundle. |

## Reference Risk

Do not delete or move files until a link/reference check has been run. Many docs cross-link to claim ledgers, submission gates, runbooks, and reports.

