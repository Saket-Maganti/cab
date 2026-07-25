# 15 Paper Claims Audit

## Commands

- `python3 scripts/check_paper_placeholders.py --mode draft`
- `python3 scripts/check_claim_ledger.py`
- `python3 scripts/check_paper_claims.py --list-ids`

## Placeholder status

Draft placeholder check exits successfully in draft mode but still detects unresolved placeholders:

- `paper/generated/00_abstract.tex`: `[N]`, `[M]`, `[K]`, `[X]`, `[rho]`
- `paper/generated/01_introduction_snippet.tex`: `[domains]`, `[main finding placeholder]`
- `paper/generated/03_benchmark_stats_table.tex`: `[N]`, `[M]`, `[domains]`

## Claim table

| Claim ID | Status | Evidence path | Safe? | Required next action |
|---|---|---|---:|---|
| C1 | planned | none | no | run real non-oracle provider experiments |
| C2 | planned | none | no | run real non-oracle provider experiments |
| C3 | planned | none | no | run real non-oracle provider experiments |
| C4 | planned | none | no | run real non-oracle provider experiments |
| C5 | planned | none | no | run real non-oracle provider experiments |
| C6 | planned | none | no | run real non-oracle provider experiments |
| C7 | planned | none | no | run real non-oracle provider experiments |
| C8 | planned | none | no | run real non-oracle provider experiments |
| C9 | engineering_only | smoke/local test evidence | yes, as engineering-only | keep scoped to reproducibility/smoke tests |
| C10 | planned | none | no | run real non-oracle provider experiments |

## Verdict

No scientific empirical paper claim is currently supported. Generated paper text must stay scaffold/planned language until evidence paths point to real provider-backed artifacts.

