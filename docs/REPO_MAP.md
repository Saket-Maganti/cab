# Repository Map

Guide for contributors, advisors, and future you.

## Top-level directories

| Path | Purpose |
|---|---|
| `src/causal_agent_bench/` | Python package (CLI, agents, scoring, generation) |
| `configs/` | Experiment and generation YAML configs |
| `data/` | Sample, processed, and frozen datasets |
| `results/` | Run outputs (gitignored patterns; index at `results/run_index.json`) |
| `docs/` | Documentation hub — start at [index.md](index.md) |
| `paper/` | Paper coordination docs + `latexpaper/` LaTeX bundle |
| `scripts/` | Standalone validation and utility scripts |
| `experiments/` | Command plans, gates, registry |
| `reviews/` | Internal reviews, mock reviews, rebuttal prep |
| `release/` | Release manifest, repro bundle plan |
| `handoff/` | Advisor/co-author packets and demo scripts |
| `benchmark_specs/` | Template registry, domain specs |
| `audits/` | Build-phase snapshots and audit reports |
| `tests/` | Pytest suite |
| `artifact/` | NeurIPS-style artifact reproduction |
| `environment/` | Captured env reports (generated) |

## Key Python modules

| Module | Role |
|---|---|
| `cli.py` | CLI entrypoint |
| `generation/` | Benchmark generation, quality checks |
| `runners/` | Experiment execution, limits, reports |
| `agents/` | Agent implementations including `mock_behavior_agent` |
| `scoring.py` | Trajectory scoring |
| `metrics/` | ACRS, tool use, recovery, contradiction |
| `phase2.py` | Audit, freeze, dry-run |
| `release/` | Manifest, command plans, env capture |
| `claim_ledger.py` | Claim validation helpers |

## `configs/`

- `smoke.yaml`, `pilot_stub_micro_3.yaml` — safe engineering configs
- `pilot_mock_diagnostic_*.yaml` — mock agents (seconds, no API)
- `pilot_multi_provider_20.yaml` — provider pilot (**requires approval**)
- `main_500_multi_provider.yaml` — main experiment (**gate NO-GO**)
- `generate_*.yaml` — dataset generation

Naming: `{scope}_{variant}_{size}.yaml`

## `data/`

| Path | Mutable? | Purpose |
|---|---|---|
| `data/sample/` | Rarely | Smoke validation |
| `data/processed/` | Yes (dev) | Generated builds |
| `data/frozen/` | **No** | Immutable release candidates |

## `results/`

Generated per run: `config.yaml`, `run_metadata.json`, `trajectories.jsonl`, `scores.jsonl`, optional `INCOMPLETE_RUN.json`.

**Do not commit** large trajectory files or secrets. Index via `index-runs`.

## `docs/`

Navigation hub: [docs/index.md](index.md). Diagrams: `docs/diagrams/`.

## `paper/`

- Coordination: `PAPER_STATUS.md`, `PAPER_SYNC_MAP.md`, `CONTRIBUTION_MAP.md`, `EVIDENCE_GAP_MAP.md`, `REVIEWER_PACKET.md`
- `latexpaper/` — self-contained LaTeX bundle (`main.tex`, `sections/`, `generated/`, `figures/`, `references.bib`)
- `figures/` — Placeholder schematics + future exports
- Planning: `EVIDENCE_GAP_MAP.md`, `CONTRIBUTION_MAP.md`, etc.

## `scripts/`

Validation: `check_claim_ledger.py`, `check_submission_readiness.py`, `lint_paper_claims.py`, `validate_paper_assets.py`.

Generation: `generate_placeholder_figures.py` (schematic only).

## Generated vs source-controlled

| Generated (often gitignored or regenerated) | Source-controlled |
|---|---|
| `results/*/` | `configs/`, `src/`, `docs/` |
| `environment/env_report.*` | `data/frozen/` |
| `release/release_manifest.json` (regenerated) | `benchmark_specs/` |
| `paper/latexpaper/figures/*_placeholder.png` | `paper/latexpaper/sections/` |
| `audits/intervention_isolation/` reports | `handoff/`, `reviews/` |

## Do not commit

- `.env`, API keys, credentials
- `results/**/trajectories.jsonl` at scale (unless release policy says otherwise)
- Incomplete runs presented as final evidence
- Fake filled placeholders in paper

See [ONBOARDING.md](ONBOARDING.md), [CONTRIBUTING.md](https://github.com/Saket-Maganti/causal-agent-bench/blob/main/CONTRIBUTING.md).
