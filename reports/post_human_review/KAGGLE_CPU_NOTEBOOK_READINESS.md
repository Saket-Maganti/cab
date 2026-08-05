# Kaggle CPU notebook readiness

Everything needed to run the three CPU pre-execution notebooks is built,
verified and on disk. The remote run did **not** happen: Kaggle's Notebooks API
rejects this account's token. The blocker is recorded below rather than worked
around, and no remote result is claimed anywhere in this repository.

## State

| item | state |
| --- | --- |
| CPU input bundle | built, deterministic, content-verified |
| T4x2 input bundle | built, deterministic, content-verified |
| Notebooks CPU 00–08 | generated, static-validated, executed offline |
| Notebooks T4x2 00–08 | static-validated, executed offline |
| Arbitrary-name discovery | 16/16 cases pass against the real bundle |
| Kaggle authentication (datasets) | works |
| Kaggle authentication (notebooks/kernels) | **HTTP 401 — blocked** |
| Remote CPU 00 / 01 / 02 | **not run** |
| Genuine model trajectories | 0 |

## The blocker

The same API token authenticates successfully against Kaggle's datasets service
and is rejected by its notebooks service:

```text
dataset_list(mine)  -> ok
kernels_list(mine)  -> 401 Unauthorized
                       https://api.kaggle.com/v1/kernels.KernelsApiService/ListKernels
```

Facts that narrow it down:

- The failure is not the client version. It reproduces identically on the
  installed `kaggle` 2.1.0 and on a clean 2.2.2 installed in a throwaway
  virtualenv.
- It is not a permissions question about *this account's* kernels. A read-only
  public kernel search fails with the same 401, so the token is not reaching the
  kernels service at all.
- It is not a network or repository problem. Dataset calls over the same
  connection, with the same credentials, succeed.

The usual cause is that the Kaggle account has not completed **phone
verification**, which Kaggle requires before the Notebooks API — and notebook
creation generally — becomes available. Regenerating the API token after
verifying will produce a token the kernels service accepts.

This is an account-side action that needs the owner signed in to Kaggle, so it
is not something this session can perform.

## Unblocking, then running

1. Sign in to Kaggle → **Settings** → **Phone Verification**, and complete it.
2. **Settings** → **API** → *Expire API Token*, then *Create New API Token*.
   Save the downloaded `kaggle.json` to `~/.kaggle/kaggle.json` with mode `600`.
3. Confirm the kernels service now answers:

```bash
python3 -c "from kaggle.api.kaggle_api_extended import KaggleApi; a=KaggleApi(); a.authenticate(); print(len(a.kernels_list(mine=True, page_size=1)), 'ok')"
```

4. Rebuild the input bundle so it binds the current commit:

```bash
python3 scripts/build_kaggle_input_bundles.py --bundle-type cpu-preexecution
```

5. Upload it as a **private** dataset. The dataset slug and the ZIP filename are
   free choices — the notebooks locate the bundle by inspecting its contents, and
   this is tested against spaces, Unicode, uppercase `.ZIP`, `" (1)"` suffixes,
   nested dataset directories and unrelated archives sitting beside it.

```bash
kaggle datasets init -p dist/kaggle_inputs
kaggle datasets create -p dist/kaggle_inputs --dir-mode zip
```

6. Create one CPU notebook per lane, attach the dataset, leave the accelerator
   on **None**, and run in this order:

```text
CAB_CPU_00_INPUT_AND_ENVIRONMENT_PREFLIGHT
CAB_CPU_01_C10_SLICE_AND_AUTHORIZATION_AUDIT
CAB_CPU_02_PROVIDER_FREE_FULL_VALIDATION
```

7. Download each output archive and verify it against its own manifest before
   trusting anything in it.

Internet must stay **off** for these three lanes. They install nothing and
contact nothing; a session that needed the network would be a finding.

## What the three lanes prove

- **CPU 00** — the attached bundle is the intended one: it is located by content,
  every declared member re-hashes, and the environment is recorded.
- **CPU 01** — C10, the exclusion register, the reviewed-slice lock and the
  execution authorization are re-derived on a machine that never held the private
  material. It checks that the qualification claim is backed by the scored
  submissions, that the reviewer-declaration waiver is disclosed at every link,
  and that the answer key is nowhere in the bundle.
- **CPU 02** — the provider-free validation gates run against the bundle rather
  than against this working tree.

## Bundles as built

| bundle | filename | sha256 | bytes |
| --- | --- | --- | --- |
| cpu-preexecution | `CAB_KAGGLE_CPU_PREEXECUTION_INPUT_a07d72ae30d9bfb1.zip` | `7fdb57def2cd766c6b5be919d0e3bb795ea5fbd9e8403253754b43544efb5bd0` | 2350338 |
| compact20-t4x2 | `CAB_KAGGLE_COMPACT20_T4X2_INPUT_e09d9e8d6e31477b.zip` | `d6372c091b20c54fbb8092e811eb3985b4e9affc0a3879b006cf7b3e85bfd080` | 1897723 |

Both are under `dist/kaggle_inputs/`, which the repository ignores; only their
manifests are tracked. Neither carries reviewer identities, private mappings,
the qualification source or key, Stage-2 plaintext, or any credential.

## Not authorized by any of this

Live open-model execution remains blocked and unauthorized. `RUN_LIVE` stays
unset, the T4x2 runners refuse without an approval receipt, and the count of
genuine model trajectories is zero.
