# Kaggle CPU operations

Nine generated notebooks under `notebooks/kaggle_cpu/`. They run on Kaggle **CPU**
sessions. None of them downloads or executes a model.

Genuine open-model inference happens only in the T4x2 notebooks
(`notebooks/kaggle/`), and a CPU fixture run is never model evidence.

## The two lanes

| lane | accelerator | what it is for |
| --- | --- | --- |
| CPU | Kaggle CPU | verification, audit, merge, scoring, analysis, bootstrap, release |
| T4x2 | Kaggle dual T4 | genuine open-model inference |

## The notebooks

| notebook | needs | purpose |
| --- | --- | --- |
| `CAB_CPU_00_INPUT_AND_ENVIRONMENT_PREFLIGHT` | repository bundle | find and verify the input, record the environment |
| `CAB_CPU_01_C10_SLICE_AND_AUTHORIZATION_AUDIT` | repository bundle | independently re-verify C10, the slice lock and the authorization |
| `CAB_CPU_02_PROVIDER_FREE_FULL_VALIDATION` | repository bundle | run the CPU-safe validation gates |
| `CAB_CPU_03_COMPACT20_POSTRUN_MERGE_SCORE_AUDIT` | Compact-20 output | merge, score, audit, analyse |
| `CAB_CPU_04_SCALE100_POSTRUN_MERGE_SCORE_AUDIT` | Scale-100 output | same, for Scale-100 |
| `CAB_CPU_05_RAAC_BASELINE_ABLATION_ANALYSIS` | RAAC output | equal-budget comparison and ablations |
| `CAB_CPU_06_NATURALISTIC_POSTRUN_ANALYSIS` | naturalistic output | transfer and predictive validity |
| `CAB_CPU_07_FINAL_BOOTSTRAP_PAPER_RELEASE` | audited eligible evidence | 10,000-replicate bootstrap, paper assets, release |
| `CAB_CPU_08_FAILURE_RECOVERY_AND_ARCHIVE_REPAIR` | partial output | inventory, quarantine, deterministic resume plan |

Notebooks 03–08 refuse a repository bundle. There is no fixture fallback: a run
that did not happen is reported as missing, never simulated.

## Building and attaching the input

```bash
python3 scripts/build_kaggle_input_bundles.py --bundle-type cpu-preexecution
```

This writes a deterministic ZIP under `dist/kaggle_inputs/`. Upload it as a
private Kaggle dataset. **Name the dataset and the file whatever you like** —
see [Kaggle input auto-discovery](KAGGLE_INPUT_AUTODISCOVERY.md).

The bundle carries public commitments, code, configs and the reviewed-slice
artifacts. It carries no reviewer identity, no private mapping, no qualification
source or key, no Stage-2 plaintext and no credentials; the builder refuses to
bundle anything the repository ignores.

## Running order

First CPU session — an independent reproducibility check:

1. `CAB_CPU_00_INPUT_AND_ENVIRONMENT_PREFLIGHT`
2. `CAB_CPU_01_C10_SLICE_AND_AUTHORIZATION_AUDIT`
3. `CAB_CPU_02_PROVIDER_FREE_FULL_VALIDATION`

Then the T4x2 fixture session, the measured model preflight, and only then the
Compact-20 live run. See [KAGGLE_T4X2_OPERATIONS.md](KAGGLE_T4X2_OPERATIONS.md).

After a live run returns an output archive, run `CAB_CPU_03`.

## Output

Every notebook writes to `/kaggle/working/cab_outputs/<lane>/` and packages it as

```text
CAB_<LANE>_OUTPUT_<content_hash>.zip
```

carrying the output manifest, the input archive SHA-256, the input bundle type,
the code commit, the environment, the steps executed, start and end timestamps,
the success state, logs, outputs and every member hash. No secrets.

On failure it still writes `CAB_<LANE>_FAILURE_BUNDLE_<content_hash>.zip` with
diagnostics and resume state. A partial run is never reported as a success.

You may rename any output ZIP; the post-run notebooks find it by content.

## Regenerating and validating

Notebooks are generated, never hand-edited:

```bash
python3 scripts/build_kaggle_cpu_notebooks.py
python3 scripts/validate_kaggle_cpu_notebooks.py --execute-offline
```

`--execute-offline` runs the repository-bundle lanes against a real bundle whose
archive has been given a **random** name, which is how filename independence is
proven rather than asserted. Static validation additionally refuses a notebook
that carries committed output, imports a model library into a CPU lane, or
matches an input by filename.
