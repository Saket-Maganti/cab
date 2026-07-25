# CAB Kaggle T4×2 Notebook Readiness

> Canonical maximum-ceiling artifact. Regenerate with `python3 scripts/generate_cab_max_ceiling_reports.py`.

Generated: 2026-07-23T17:23:44.726749+00:00

## Notebook inventory

1. `notebooks/kaggle/CAB_T4X2_00_ENVIRONMENT_PREFLIGHT.ipynb`
2. `notebooks/kaggle/CAB_T4X2_01_OFFLINE_FIXTURE_SMOKE.ipynb`
3. `notebooks/kaggle/CAB_T4X2_02_COMPACT20_OPEN_MODEL_RUNNER.ipynb`
4. `notebooks/kaggle/CAB_T4X2_03_SCALE100_OPEN_MODEL_RUNNER.ipynb`
5. `notebooks/kaggle/CAB_T4X2_04_MAIN500_OPEN_MODEL_RUNNER.ipynb`
6. `notebooks/kaggle/CAB_T4X2_05_BASELINES_AND_ABLATIONS.ipynb`
7. `notebooks/kaggle/CAB_T4X2_06_MERGE_AUDIT_AND_RESCORE.ipynb`
8. `notebooks/kaggle/CAB_T4X2_07_FAILURE_RECOVERY.ipynb`
9. `notebooks/kaggle/CAB_T4X2_08_NATURALISTIC_TRANSFER_RUNNER.ipynb`

## Safety and parallel strategy

- `RUN_LIVE = False` is literal and default in every notebook.
- Live activation requires an explicit confirmation plus a separate approval marker.
- Worker 0 uses GPU 0 and worker 1 uses GPU 1 with deterministic, non-overlapping data-parallel shards and separate append-safe outputs.
- Single-GPU fallback, fp16, optional 4-bit loading, optional supported two-GPU placement, actionable OOM/preflight failure, checkpoint/resume, deterministic merge, and integrity manifests are present.
- Opening or Run All cannot start model inference under default settings.

## Offline validation

- Static command: `/Library/Frameworks/Python.framework/Versions/3.11/bin/python3 scripts/validate_kaggle_notebooks.py`
- Static result: `PASS`; exit `0`; 0.072 seconds.
- Offline command: `/Library/Frameworks/Python.framework/Versions/3.11/bin/python3 scripts/validate_kaggle_notebooks.py --execute-offline`
- Offline result: `PASS`; exit `0`; 0.191 seconds.
- Expected offline result: 9 notebook executions and 72 fixture receipts.
- Evidence class: `FIXTURE_ONLY`; `scientific_execution_performed=false`.

## External risks

- Kaggle image, CUDA/driver, package, network, disk, and quota drift.
- Model snapshot/license/access changes and third-party chat-template behavior.
- Actual T4 VRAM/throughput/OOM behavior is unmeasured.
- Live input hashes, human gate, approval, and model revisions must be pinned.

## First notebook later

`notebooks/kaggle/CAB_T4X2_00_ENVIRONMENT_PREFLIGHT.ipynb`, after genuine review, C10, slice lock, and explicit execution approval. Keep `RUN_LIVE=False` for the first Kaggle fixture session.
