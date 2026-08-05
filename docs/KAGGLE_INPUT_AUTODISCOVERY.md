# Kaggle input auto-discovery

Every CAB Kaggle notebook finds its input by looking **inside** the attached
archive. Nothing depends on what the ZIP or the Kaggle dataset is called.

You may rename the ZIP. You may rename the dataset. You may nest it. You may
attach unrelated archives alongside it. None of that changes discovery.

## Why this exists

Matching an input by filename — `*/pyproject.toml`, or an expected
`CAB_..._INPUT_<hash>.zip` — breaks the moment anyone renames anything, and it
breaks in a way that looks like a scientific failure rather than a naming one.
Kaggle renames things routinely: the dataset slug is chosen by the uploader, and
the browser may append ` (1)` to a download.

## How a bundle is identified

`src/causal_agent_bench/kaggle_input_discovery.py` is the single implementation.
The notebooks inline its source verbatim at generation time, so a notebook and
its tests can never disagree about how discovery works.

1. `/kaggle/input` is walked to a bounded depth. Both `.zip` archives
   (case-insensitively) and plain directories are considered.
2. Each candidate's member names are read **without extracting**.
3. A weighted sentinel set scores the candidate:

   | sentinel | weight |
   | --- | --- |
   | `CAB_KAGGLE_INPUT_MANIFEST.json` | 6 |
   | `reports/reviewer_ready_v2/ACTIVE_PATH_REGISTRY.json` | 5 |
   | `reports/reviewer_ready_v2/SCIENTIFIC_FREEZE_V2.json` | 5 |
   | `src/causal_agent_bench/` | 4 |
   | `environment/kaggle_environment.json` | 3 |
   | `configs/`, `scripts/`, `data/manifests/` | 2 each |
   | `pyproject.toml` | 1 |

   A single weak sentinel is never enough: the selection threshold is 8, so
   `pyproject.toml` alone (weight 1) cannot select a random archive.
4. Output bundles are classified the same way, from `CAB_KAGGLE_OUTPUT_MANIFEST.json`,
   `run_manifest.json` and `execution_authorization.json`, and the *study* is read
   from manifest content — never from the filename. An archive naming two studies
   is `UNKNOWN_BUNDLE`, not a guess.
5. The unique highest-scoring candidate wins. Byte-identical copies are not an
   ambiguity. Two different bundles scoring equally is
   `FAIL_CLOSED_AMBIGUOUS_KAGGLE_INPUT`, printed with a candidate table.
6. The winner is extracted into a **hash-named** directory under
   `/kaggle/working`, so re-running reuses it and two bundles can never
   overwrite each other.
7. The logical root is located by sentinel files, so any wrapping folder name —
   or no wrapping folder at all — works.
8. Every member hash in `CAB_KAGGLE_INPUT_MANIFEST.json` is re-verified.

## Refused before extraction

- absolute-path members (`/etc/passwd`)
- path traversal (`../`)
- symlinks, devices and other non-regular members
- expansion beyond 4 GiB, or a compression ratio above 200:1
- truncated or unreadable archives

## Overriding discovery

Set `CAB_KAGGLE_INPUT_PATH` to an exact archive or directory. The override is
still validated: pointing it at the wrong bundle type is an error, not an
instruction.

## Ambiguity

When two valid bundles differ, the notebook stops and prints:

```text
FAIL_CLOSED_AMBIGUOUS_KAGGLE_INPUT
  path | type | score | members | sha256 | problems
```

Detach the one you do not want, or set `CAB_KAGGLE_INPUT_PATH`. Discovery will
not choose between two sets of inputs on your behalf.

## Tests

`tests/test_kaggle_input_autodiscovery.py` builds bundles with **randomly
generated** filenames on every run, so a test cannot pass because an archive
happened to be called the expected thing. It covers expected names, random
names, spaces, Unicode, uppercase `.ZIP`, nested dataset folders, arbitrary
archive roots, no root at all, unrelated archives, identical copies, conflicting
bundles, traversal, absolute paths, symlinks, zip bombs, truncation, plain
directories, output/input confusion in both directions, and the override.
