# Phase-2 Audit

Date: 2026-05-12

## What Changed

- Added Phase-2 CLI plumbing:
  - `validate-config`
  - `dry-run`
  - `audit-interventions`
  - `freeze-dataset`
  - `summarize-run`
  - `update-claim-ledger`
- Kept existing `doctor`, `list-providers`, and `estimate-cost` commands.
- Added run metadata fields for dataset version, benchmark path, model IDs, and dataset generation config hash when available.
- Added metadata stamping for exported paper tables and figures:
  - run directory
  - config hash
  - dataset version
  - model IDs
  - timestamp
- Added `asset_metadata.json` to run-local paper exports.
- Added `PROJECT_STATUS.md` and `MILESTONES.md`.
- Added tests covering the Phase-2 CLI commands and asset metadata.

## What Remains Risky

- No real provider-backed LLM pilot has been run in this repository.
- Stub/local runs remain engineering-only and cannot support the central scientific claims.
- The deterministic scorer is auditable but still heuristic.
- Intervention quality checks flag issues in the small sample data; pilot/frozen datasets need separate audit.
- Human validation has not been completed.
- Cost estimates are conservative output-token approximations, not provider invoices.
- `freeze-dataset` creates a reproducible copy and manifest, but it does not make the dataset scientifically valid by itself.

## Reviewer-Relevant Notes

- Oracle agents remain documented as sanity-check upper bounds only.
- API keys are read from environment variables and are never printed by provider/status commands.
- `dry-run` explicitly reports that it does not call providers or write result directories.
- `update-claim-ledger` refuses to mark a claim `supported` unless evidence paths exist.

## Verification Commands

```bash
python3 -m causal_agent_bench validate-config --config configs/smoke.yaml
python3 -m causal_agent_bench dry-run --config configs/pilot_20_multi_agent.yaml
python3 -m causal_agent_bench audit-interventions --benchmark-dir data/sample --output-dir /tmp/cab_audit_cli_check
python3 -m causal_agent_bench update-claim-ledger --ledger docs/claim_ledger.json
python3 -m ruff check .
python3 -m pytest -q
```
