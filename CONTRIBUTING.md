# Contributing to CausalAgentBench

Thank you for helping improve the benchmark and evaluation package. This project prioritizes **honest evidence** over premature claims.

## Before you start

- Read [docs/ONBOARDING.md](docs/ONBOARDING.md) and [docs/EVIDENCE_LEVEL_POLICY.md](docs/EVIDENCE_LEVEL_POLICY.md)
- Run `make fast-check` before opening a PR

## Coding style

- Python 3.11+; type hints encouraged
- Match existing patterns in `src/causal_agent_bench/`
- Lint: `python -m ruff check .`
- Tests: `python -m pytest tests/`

## Test expectations

- Add tests for new CLI commands, validators, and scoring logic
- **No paid API calls in tests**
- **No Ollama/long model runs in CI**
- Use mock/stub agents for trajectory tests

## Secrets

- Never commit `.env`, API keys, or credentials
- Use `.env.example` as template only

## No fake results

- Do not fill paper placeholders with invented numbers
- Do not mark claims C1–C8/C10 as `supported` without evidence paths
- Placeholder figures must be labeled `PLACEHOLDER — NOT EMPIRICAL RESULT`

## Evidence-level rules

- Declare evidence level in PR description for any run-related change
- Stub/mock/dry-run → `engineering_only` only
- See [docs/claim_ledger.json](docs/claim_ledger.json)

## Claim-ledger rules

- Status changes require `linked_run_dirs` + `current_evidence_paths`
- Run `python3 scripts/check_claim_ledger.py --mode draft`
- Submission mode stricter — do not bypass

## Config naming

`{scope}_{variant}_{size}.yaml` — e.g., `pilot_stub_micro_3.yaml`

- `allow_paid_calls: false` by default
- Document new configs in [experiments/COMMAND_PLANS.md](experiments/COMMAND_PLANS.md) if experiment-facing

## Dataset versioning

- Processed builds: mutable under `data/processed/`
- Frozen releases: immutable under `data/frozen/`
- See [docs/DATASET_VERSIONING_AND_RELEASE_POLICY.md](docs/DATASET_VERSIONING_AND_RELEASE_POLICY.md)

## Documentation requirements

- User-facing changes → update `docs/` and link from [docs/README.md](docs/README.md)
- New scripts → mention in README or docs hub
- Paper-impacting changes → update [paper/PAPER_SYNC_MAP.md](paper/PAPER_SYNC_MAP.md) if relevant

## Pull request checklist

See [.github/pull_request_template.md](.github/pull_request_template.md).

## Questions

Open an issue or discuss with maintainers before large architectural changes or paid experiment configs.
