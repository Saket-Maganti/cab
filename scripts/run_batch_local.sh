#!/usr/bin/env bash
# Local batch runner: plan shards, execute each with resume, then merge.
# Usage:
#   ./scripts/run_batch_local.sh configs/smoke.yaml instance 4
set -euo pipefail

CONFIG="${1:-configs/smoke.yaml}"
SHARD_BY="${2:-instance}"
SHARD_COUNT="${3:-2}"
BATCH_DIR="${4:-}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PLAN_ARGS=(batch-plan --config "$CONFIG" --shard-by "$SHARD_BY" --shard-count "$SHARD_COUNT")
if [[ -n "$BATCH_DIR" ]]; then
  PLAN_ARGS+=(--output-dir "$BATCH_DIR")
fi

python3 -m causal_agent_bench "${PLAN_ARGS[@]}"

if [[ -z "$BATCH_DIR" ]]; then
  RUN_NAME="$(python3 - <<'PY' "$CONFIG"
import sys, yaml
from pathlib import Path
raw = yaml.safe_load(Path(sys.argv[1]).read_text())
print(raw["run_name"])
PY
)"
  BATCH_DIR="results/${RUN_NAME}_batch"
fi

MANIFEST="${BATCH_DIR}/batch_manifest.json"
python3 - <<'PY' "$MANIFEST"
import json, sys
from pathlib import Path
manifest = json.loads(Path(sys.argv[1]).read_text())
for shard in manifest["shards"]:
    print(shard["config_path"])
PY
| while read -r shard_config; do
  echo "==> running shard ${shard_config}"
  python3 -m causal_agent_bench run --config "$shard_config" --checkpoint-every 1 || true
  shard_run="$(dirname "$shard_config")/run"
  latest="$(ls -1dt "${shard_run}"/* 2>/dev/null | head -n 1 || true)"
  if [[ -n "$latest" ]]; then
    python3 -m causal_agent_bench run --config "$shard_config" --resume "$latest" --retry-failed --checkpoint-every 1 || true
  fi
done

python3 -m causal_agent_bench batch-merge --batch-dir "$BATCH_DIR"
python3 -m causal_agent_bench failure-report --run-dir "${BATCH_DIR}/merged/run"
