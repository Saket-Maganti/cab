# 20 Reproducibility Audit

## What is reproducible now

- Editable install works with `python3`.
- Full tests pass: `244 passed, 1 skipped`.
- Pilot dataset generation is byte-for-byte reproducible for `configs/generate_pilot_v0_1.yaml`.
- Deterministic local-stub run/score/analyze/export pipeline completes with 600 trajectories and 0 errors.
- Run metadata records config hash, dataset version, git commit, package version, Python version, providers, model IDs, and engineering-only scope.
- Claim ledger validation passes.
- Security check passes.

## What is not reproducible as science yet

- No real provider-backed pilot exists.
- No main experiment exists.
- No human validation result exists.
- Paper placeholders remain.
- Claim ledger has no supported scientific empirical claims.

## Package risks

- Dependency pinning/lock-file reproducibility was not proven.
- Clean-checkout artifact reproduction was not proven because the worktree began dirty.
- Bare `python` pyenv issue should be fixed or documented.

