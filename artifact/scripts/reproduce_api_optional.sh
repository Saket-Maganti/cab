#!/usr/bin/env bash
# Optional API-backed preflight and pilot (requires keys; costs may apply).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
PYTHON="${PYTHON:-python3}"
echo "==> Optional API path"
echo "    Ensure OPENAI_API_KEY and OPENAI_MODEL_ID are set if using pilot_openai_20.yaml"
"$PYTHON" scripts/reproduce_artifact.py --step api-preflight "$@"
if [[ "${RUN_API_PILOT:-0}" == "1" ]]; then
  "$PYTHON" scripts/reproduce_artifact.py --step api-pilot "$@"
fi
