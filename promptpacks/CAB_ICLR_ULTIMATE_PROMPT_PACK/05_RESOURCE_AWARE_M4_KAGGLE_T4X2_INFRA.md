# Prompt 05 — M4 Mac and Kaggle T4×2 Resource-Aware Infrastructure


## Repository

`/Users/saketmaganti/Projects/causal-agent-bench`

## Hard Resource Envelope

Assume the user has only:

- MacBook Air M4, 16 GB unified memory, 512 GB storage;
- free Kaggle notebooks with two NVIDIA T4 GPUs when available;
- no A100/H100 cluster;
- no guaranteed paid API budget;
- no background compute service;
- limited storage and session duration.

Design every solution around this envelope. Prefer streaming, sharding, quantisation, resumability, compact artifacts, incremental exports, and CPU-safe validation.

## Scientific Integrity Rules

Never:

- fabricate human review;
- fabricate model trajectories;
- fabricate results, costs, timings, tables, plots, or claims;
- tune the benchmark after seeing confirmatory results;
- expose gold answers to agents;
- mark fixture, mock, stub, dry-run, or interrupted outputs as scientific evidence;
- use provider secrets found in the environment;
- commit or push unless explicitly authorised;
- silently delete user work;
- claim ICLR acceptance or submission readiness without evidence.

Always distinguish:

- `DESIGN_ONLY`
- `ENGINEERING_ONLY`
- `FIXTURE_ONLY`
- `HUMAN_INPUT_REQUIRED`
- `EXECUTION_PENDING`
- `PRELIMINARY_REAL_EVIDENCE`
- `AUDITED_REAL_EVIDENCE`
- `PAPER_ELIGIBLE_EVIDENCE`

## Required Working Style

- Inspect before modifying.
- Repair locally fixable defects instead of only reporting them.
- Preserve reversible history.
- Prefer canonical implementations over duplicate layers.
- Record exact commands and exit codes.
- Keep the public surface clean.
- Build fail-closed gates.
- Stop when the stated phase is complete.


## Goal

Make every future experiment runnable with the user's actual hardware.

## Mac Lane

Optimise serial/limited-parallel tests, memory-aware bootstrap, streaming JSONL, compressed artifacts, bounded workers, disk reports, safe cleanup, chunked analysis, and low-memory mode.

Do not plan large-model inference locally.

## Kaggle T4×2 Lane

Build/harden notebooks for preflight, fixture smoke, Compact-20, Scale-100, RAAC/ablations, transfer, merge/rescore, and failure recovery.

## Parallel Strategy

Default to one independent worker per T4 with deterministic disjoint shards, separate checkpoints, immutable hashes, and strict merge.

Support single-GPU fallback, 4-bit quantisation, fp16, safe optional CPU offload, and optional two-GPU placement where supported.

## Model Eligibility Registry

Record parameter count, quantisation, expected VRAM, context, chat template, tool support, T4 fit confidence, fallback, and licence. Keep it configurable.

## Session Survival

Checkpoint frequently, export each chunk, detect prior chunks, prevent duplicates, create session manifests, verify hashes, support manual download, and write concise status.

## Storage Budget

Estimate model cache, trajectories, scores, checkpoints, figures, and exports. Add safe cache cleanup, compression, regenerable-intermediate policy, and raw evidence retention.

## Runtime Calibration

Before full runs, execute a tiny approved smoke and measure load time, seconds per trajectory, and peak VRAM. Initial estimates must say `ESTIMATE_NOT_MEASURED`.

## No Secrets

Provider keys must never enter Kaggle notebooks.

## Outputs

- validated notebooks;
- model eligibility registry;
- disk and runtime estimators;
- checkpoint/merge utilities;
- `CAB_ICLR_RESOURCE_AND_RUNTIME_PLAN.md`;
- `docs/M4_LOW_MEMORY_WORKFLOW.md`;
- `docs/KAGGLE_T4X2_OPERATIONS.md`.

## Acceptance Gate

All notebooks pass fixture execution, default live flags are false, and resume/merge tests pass.
