# CAB Release Candidate

This is a no-provider, pre-execution release surface. Live provider outputs,
human annotations, and paper-eligible results are not included.

- `release_manifest.json` is the canonical, hash-covered inventory.
- `RELEASE_READINESS_V2.md` records the evidence blockers.
- `../docs/DATASET_VERSIONING_AND_RELEASE_POLICY.md` controls immutable freezes.
- `../docs/HELDOUT_RELEASE_GOVERNANCE.md` controls protected confirmatory and
  challenge material.
- `../docs/SECURITY_AND_PRIVACY.md`, `../DATA_LICENSE.md`, and `../LICENSE`
  control sensitive data and redistribution.

Validate with `make max-ceiling-ci-serial`. This command executes provider-free
tests and fixture notebooks only; it does not authorize a model run or release.
