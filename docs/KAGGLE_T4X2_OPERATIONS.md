# Kaggle T4×2 Operations

The nine notebooks under `notebooks/kaggle/` are the canonical Kaggle lane.
Every notebook defaults `RUN_LIVE=False`; offline fixture validation is
engineering evidence only.

## Default topology

Use independent data parallelism: one model worker on GPU 0 and one on GPU 1,
each receiving a deterministic disjoint shard. Workers keep separate ledgers,
checkpoints, and output chunks. Merge only after completeness, disjointness,
hash, schema, and scorer-version checks pass.

Model parallel placement is optional and may be used only after a single-GPU
preflight demonstrates that the pinned model revision cannot fit. The
single-GPU fallback is a smaller open model or a more aggressive supported
quantisation; provider access is never required for the paper.

## Session contract

Before any future live session:

1. complete genuine review, adjudication, C10, and slice locking;
2. record exact task, split, scorer, policy, code, model, and revision hashes;
3. select `fp16`, 8-bit, or 4-bit from a measured preflight;
4. set an explicit live approval flag;
5. checkpoint each task or small batch and export each completed chunk;
6. resume by completed IDs, rejecting duplicates and corrupt chunks;
7. compress exports and write an integrity summary before session shutdown.

OOM recovery order is: reduce batch size; lower concurrency; enable a supported
quantisation; enable bounded CPU offload; use one GPU; select the documented
fallback. Every memory and runtime value before measurement is
`ESTIMATE_NOT_MEASURED`.

## Model panel

`configs/iclr/model_compatibility_t4x2.yaml` records categories rather than
pretending that a July 2026 model, licence, or memory footprint is immutable.
At run time, pin and revalidate the exact model ID, revision, licence, chat
template, context, tool adapter, measured VRAM, and fallback.

## Validation

```bash
PYTHONPATH=src python3 scripts/validate_kaggle_notebooks.py
PYTHONPATH=src python3 scripts/validate_kaggle_notebooks.py --execute-offline
```

The validator checks inventory, JSON structure, extracted Python syntax,
cell order, safe defaults, paths, secrets, deterministic sharding,
checkpoint/resume, merge, and corruption detection without downloading or
executing a model.
