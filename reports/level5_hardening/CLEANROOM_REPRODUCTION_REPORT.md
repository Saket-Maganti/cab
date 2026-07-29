# CAB Level-5 clean-room reproduction report

Captured on 2026-07-29 from committed source
`1a810a0f059d18e65d4dae2ee3c2fabda7e08fe1`.

## Result

State: `CAB_INTERNAL_CLEANROOM_REPRODUCTION_READY`.

The committed Git archive built both package formats, installed the wheel into
an empty virtual environment, and reproduced the public fixture from both that
environment and a clean source checkout. All expected artifact hashes agreed
and the discrepancy list was empty.

| Measurement | Result |
|---|---|
| Clean environment | `INTERNAL_CLEAN_ENVIRONMENT`, passed |
| Clean checkout | `INTERNAL_CLEAN_CHECKOUT`, passed |
| Wheel SHA-256 | `c3af559abb90bd716a1e2fe9d9dc96a6c8939d4458b5608259c1e6e421bc3b47` |
| Source distribution SHA-256 | `ea150fa6ef1fa710a53031958ad73d53a7d15b83eeb1e820092ee2c83f530f9c` |
| Manifest hash | `b92acb55375da001ff76dbc3d8eb864565618dc9c8480b40cd6b50372ad69d42` |
| Merge digest | `db0dbb3ff7bfb10f238bcf0c561ea943d2bcf6ba49dafc869f413354e581e84b` |
| Evidence graph hash | `2855eadfe9e6369fb97ed8d3d8a89c814d52e15f13700c6bd9df304b93c991c2` |
| Receipt hash | `9f2abe803d6cbb37de51d58ee35efc63bcc44a1995f69099c162cd1d4d3d529c` |
| Discrepancies | 0 |

## Honest boundary

The local Docker client existed, but the Docker daemon was unavailable. The
container image build failed before a container could execute, so
`INTERNAL_CONTAINER` is recorded as `NOT_EXECUTED`; it is not counted as a
pass. External independent reproduction is also `NOT_EXECUTED`.

This is internal fixture reproduction, not scientific replication. The
machine-readable command, exit-code, stdout/stderr hash, artifact, platform,
and classification details are in `CLEANROOM_REPRODUCTION_REPORT.json`.
