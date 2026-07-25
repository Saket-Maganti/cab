# Generated Files Policy

What is source-controlled vs generated, and what must never be committed.

## Source-controlled (canonical)

| Path | Purpose |
|---|---|
| `src/` | Python package source |
| `configs/` | Experiment and generation YAML |
| `docs/` | Documentation (except large generated audits if optional) |
| `paper/sections/`, `paper/main.tex` | Paper source |
| `paper/figures/*_placeholder.png` | Schematic placeholders (labeled NOT EMPIRICAL) |
| `benchmark_specs/` | Task template registry |
| `scripts/` | CLI helpers and validators |
| `tests/` | Test suite |
| `data/frozen/` | Frozen benchmark snapshots (when released) |
| `data/sample/` | Tiny sample data for smoke tests |
| `handoff/` | Advisor/co-author packets |
| `.env.example` | Env template (no secrets) |

## Generated locally (do not commit unless small audit snapshot)

| Path | Generator | Commit? |
|---|---|---|
| `results/*/` | `causal_agent_bench run` | **No** (gitignored) |
| `results/dry_runs/` | `dry-run` | No |
| `results/cache/` | Runner cache | No |
| `PROJECT_STATUS.md`, `.json` | `generate_project_status.py` | Optional (small; useful for handoff) |
| `audits/repo_consistency/` | `audit_repo_consistency.py` | Optional audit snapshot |
| `audits/config_consistency/` | `audit_configs.py` | Optional audit snapshot |
| `audits/build_phase_*/` | Build mode snapshots | Optional |
| `environment/env_report.json` | `capture-env` | Optional |
| `release/release_manifest.json` | `build-release-manifest` | Optional for releases |
| `paper/*.aux`, `*.log`, `*.pdf` | LaTeX build | PDF optional; aux/log no |
| `figures/`, `tables/` (repo root) | `export-paper-assets` | **No** until verified pilot |
| `__pycache__/`, `.pytest_cache/` | Python | No |

## Ignored by default (`.gitignore`)

- `.env`, `.env.*` (except `.env.example`)
- `results/*/` (keeps `results/.gitkeep`)
- Secrets: `*.pem`, `*.key`, `credentials.json`, `secrets.json`
- Provider telemetry: `**/raw_provider_responses/`, `**/provider_logs/`
- Build artifacts: `dist/`, `*.egg-info/`, LaTeX intermediates

## Results directory

- Each run: `results/<timestamp>_<run_name>/`
- Must include `run_metadata.json`, trajectories, optional `INCOMPLETE_RUN.json`
- Interrupted runs stay on disk but are **not** scientific evidence
- Index: `results/run_index.json` via `index-runs`

## Audits directory

- Build-phase snapshots document engineering progress
- Consistency audits are regenerable; commit only when sharing a frozen review point

## Release manifests

- `release/release_manifest.json` — bundle hash for reproducibility
- Commit when cutting a release tag; regenerate before submission

## Placeholder figures

- `paper/figures/*_placeholder.png` + `.meta.json` with `"placeholder": true`
- Schematic only — never substitute for empirical figures in submission

## Human annotations

- Export packets from `export-human-validation`
- Store under `data/human_validation/` or external storage
- Do not commit PII; use anonymized IDs only

## Secrets / env

- Never commit `.env`, API keys, or provider logs
- Use `.env.example` for variable names only
- Run `make security-check` before release

## What can be committed if small and useful

- `PROJECT_STATUS.md` / `.json` after `generate_project_status.py`
- Audit markdown/json from consistency scripts
- Frozen dataset manifests under `data/frozen/`
- Placeholder figure PNGs (already labeled)

## What should never be committed

- Raw provider responses or API keys
- Unlabeled mock/stub runs presented as main results
- Filled paper placeholders without linked run provenance
- Large result directories or provider telemetry

See also [REPO_MAP.md](REPO_MAP.md), [EVIDENCE_LEVEL_POLICY.md](EVIDENCE_LEVEL_POLICY.md).
