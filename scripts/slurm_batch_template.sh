#!/bin/bash
#SBATCH --job-name=cab-batch
#SBATCH --array=0-3
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=04:00:00
#SBATCH --output=logs/cab-batch-%A_%a.out
#
# Template for sharded CausalAgentBench runs on SLURM.
# 1. Plan shards once on the login node:
#      python -m causal_agent_bench batch-plan --config configs/pilot_20_multi_agent.yaml \
#        --shard-by instance --shard-count 4 --output-dir results/pilot_batch
# 2. Submit this script with matching array size.
#
# Customize CONFIG, BATCH_DIR, and SHARD_COUNT before submitting.

set -euo pipefail

CONFIG="${CONFIG:-configs/smoke.yaml}"
BATCH_DIR="${BATCH_DIR:-results/smoke_batch}"
SHARD_COUNT="${SHARD_COUNT:-4}"

ROOT="${SLURM_SUBMIT_DIR:-$(pwd)}"
cd "$ROOT"

if [[ ! -f "${BATCH_DIR}/batch_manifest.json" ]]; then
  python -m causal_agent_bench batch-plan \
    --config "$CONFIG" \
    --shard-by instance \
    --shard-count "$SHARD_COUNT" \
    --output-dir "$BATCH_DIR"
fi

SHARD_INDEX="${SLURM_ARRAY_TASK_ID:-0}"
SHARD_CONFIG="${BATCH_DIR}/shards/shard_$(printf '%03d' "${SHARD_INDEX}")/config.yaml"

python -m causal_agent_bench run --config "$SHARD_CONFIG" --checkpoint-every 1

SHARD_RUN_ROOT="$(dirname "$SHARD_CONFIG")/run"
LATEST_RUN="$(ls -1dt "${SHARD_RUN_ROOT}"/* 2>/dev/null | head -n 1 || true)"
if [[ -n "$LATEST_RUN" ]]; then
  python -m causal_agent_bench run \
    --config "$SHARD_CONFIG" \
    --resume "$LATEST_RUN" \
    --retry-failed \
    --checkpoint-every 1
fi

# Merge only from the last array task to avoid races (or run merge manually afterward).
if [[ "${SHARD_INDEX}" -eq $((SHARD_COUNT - 1)) ]]; then
  python -m causal_agent_bench batch-merge --batch-dir "$BATCH_DIR"
  python -m causal_agent_bench failure-report --run-dir "${BATCH_DIR}/merged/run"
fi
