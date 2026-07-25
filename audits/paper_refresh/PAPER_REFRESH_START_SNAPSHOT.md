# Paper Refresh — Start Snapshot

**Generated:** 2026-05-20 (safe paper refresh after build phases 2–9)

## Paper files found

| Path | Role |
|---|---|
| `paper/main.tex` | Root document |
| `paper/sections/00_abstract.tex` … `12_conclusion.tex` | Section sources |
| `paper/sections/checklist.tex` | NeurIPS checklist draft |
| `paper/generated/*.tex` | Placeholder / fill-paper fragments |
| `paper/references.bib` | Bibliography |

## Placeholder count (draft mode)

- `[N]`, `[M]`, `[K]`, `[X]`, `[rho]`, `[domains]`, `[main finding placeholder]` — **8 unresolved** (check_paper_placeholders.py)
- Results section: structured TODOs only
- Mini-study table: `[todo]` rows

## Claim status

| Claim | Status |
|---|---|
| C1–C8 | **planned** |
| C9 | **engineering_only** |
| C10 | **planned** |

## Evidence status

- **Classification:** `build_infrastructure_ready` (MASTER_STATUS)
- **Provider pilot:** not complete for paper claims
- **Human validation:** not complete
- **Phase 9 mock demo:** engineering-only (`mock_diagnostic_only`)

## Build-phase artifacts available (not empirical evidence)

- Run management: plan-run, run-status, mark-interrupted, index-runs, limits
- Reports: generate-report, failure-gallery, analysis export
- Audits: repo/config consistency, intervention isolation, evidence safety
- Policies: EVIDENCE_LEVEL_POLICY, DO_NOT_OVERCLAIM, PRE_EXPERIMENT_FREEZE
- Release: release manifest, repro bundle plan, capture-env
- Demo: `demo/ENGINEERING_DEMO_BUNDLE.md` (mock micro E2E)
- Human validation: export protocol, form schema (no annotations)

## Stale sections (pre-refresh)

| Section | Issue |
|---|---|
| Experimental Setup | Missing run-management, evidence guards, mock diagnostic E2E |
| Benchmark Design | Missing task registry, freeze policy, isolation audit refs |
| Ethics/Repro | Missing release manifest, evidence-level enforcement tooling |
| Checklist | Pre-dates Phase 7–9 infrastructure |
| PAPER_SYNC_MAP | Paths outdated; missing demo bundle refs |
| Introduction | References old evidence mapping path |

## Pre-edit checks

```
check_claim_ledger.py → valid
check_paper_placeholders.py --mode draft → pass (8 placeholders)
lint_paper_claims.py --mode draft → pass (22 warnings)
validate_paper_assets.py --mode draft → pass (6 warnings)
```
