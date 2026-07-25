#!/usr/bin/env bash
# API-free artifact reproduction path (engineering-only outputs).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
PYTHON="${PYTHON:-python3}"
echo "==> CausalAgentBench deterministic artifact path"
echo "    ENGINEERING-ONLY: not scientific evidence."
"$PYTHON" scripts/reproduce_artifact.py --all-deterministic "$@"
