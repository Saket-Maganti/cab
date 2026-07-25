#!/usr/bin/env bash
# Fast local pre-commit checks — no model runs.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/mpl}"

echo "==> make fast-check"
make fast-check

echo "==> claim ledger"
python3 scripts/check_claim_ledger.py

echo "==> evidence safety"
python3 scripts/check_evidence_safety.py

echo "==> paper placeholders (draft)"
python3 scripts/check_paper_placeholders.py --mode draft

echo "==> lint paper claims (draft)"
python3 scripts/lint_paper_claims.py --mode draft || true

echo "==> paper assets (draft)"
python3 scripts/validate_paper_assets.py --mode draft || true

echo "precommit_fast: OK"
