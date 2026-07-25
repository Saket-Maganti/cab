# 01 Project Inventory

## Discovered assets

| Area | Present? | Looks complete? | Risks |
|---|---:|---:|---|
| `src/` | yes | mostly | Large dirty changes pre-existed; minimal audit fixes applied in `phase2.py`. |
| `tests/` | yes | yes | Full suite passes, but clean-checkout status was not established. |
| `configs/` | yes | mixed | Provider configs are structurally valid but not ready without model IDs/API keys/pricing. |
| `data/` | yes | yes for sample/pilot/main/web-shadow | Human audit sample files have no dedicated schema validation command. |
| `docs/` | yes | broad | Some docs describe planned studies; must stay clearly scoped. |
| `paper/` | yes | scaffold | Placeholder tokens remain in generated paper snippets. |
| `scripts/` | yes | broad | Paper/claim/security/release checks are available and were used. |
| `figures/` | yes | generated | Existing/global assets are engineering-only unless tied to eligible run evidence. |
| `tables/` | yes | generated | Same engineering-only caveat. |
| `results/` | yes | mixed | No real provider-backed scientific result directories found. |
| `benchmark_specs/` | no | no | No directory found; equivalent specs appear in docs/configs/data. |
| `reviews/` | yes | partial | Review planning docs present. |

## Entry points and scripts

CLI entry point: `python3 -m causal_agent_bench`.

Subcommands discovered include `validate`, `generate`, `run`, `score`, `analyze`, `export-paper-assets`, `doctor`, `list-providers`, `estimate-cost`, `validate-config`, `dry-run`, `audit-contamination`, `audit-interventions`, `freeze-dataset`, `summarize-run`, `update-claim-ledger`, and paper/result export helpers.

Important scripts discovered: `check_paper_placeholders.py`, `check_claim_ledger.py`, `check_paper_claims.py`, `check_bibliography.py`, `check_citation_todos.py`, `security_check.py`, `release_check.py`, `release_dry_run.py`, `reproduce_artifact.py`, `camera_ready_precheck.py`.

## Duplicate or generated files

Generated outputs are committed or present under `figures/`, `tables/`, `paper/generated/`, `results/`, `data/processed/`, and `data/frozen/`. This is acceptable for an artifact repository, but all generated scientific assets need explicit run provenance.

