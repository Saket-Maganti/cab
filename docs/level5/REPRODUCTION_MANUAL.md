# Clean-room reproduction

Internal reproduction has three classes. None is an external independent
replication.

## Clean virtual environment

The harness archives a committed revision, builds wheel and source
distributions, creates an empty temporary venv, installs under
`constraints.txt`, runs `cab reproduce`, records hashes and removes the
environment. `PYTHONPATH`, user site packages and active environment variables
are removed.

## Clean checkout

The same `git archive` is extracted into a temporary directory. The fixture is
run with only that archive's `src` on `PYTHONPATH`. The developer worktree is
never used. Manifest, merge and structural graph hashes are compared with the
wheel run.

## Container

When Docker and a local build are available, the harness builds from the clean
source context and runs doctor, migrations, reproduction and public benchmark
compilation with the network disabled. Unavailable cases are `NOT_EXECUTED`.

## Receipt and discrepancies

The receipt records commit, archive, wheel, sdist and lock hashes, Python, OS,
architecture, container digest, commands, exit codes, output hashes, artifacts
and discrepancies. A hash mismatch fails internal reproduction. Commit compact
receipts, not raw build logs.

An external reproducer must work independently, disclose their environment,
sign an attestation and report discrepancies. Only that process may create
`EXTERNAL_INDEPENDENT`.
