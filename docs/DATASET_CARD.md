# Dataset Card: CausalAgentBench

**Dataset name:** CausalAgentBench synthetic instances
**Release:** `0.1.0-rc1`
**Example frozen bundle:** `pilot_v0.1` → `data/frozen/pilot_v0.1/freeze_manifest.json`

## Intended Use

Controlled research on tool-using agents under **paired clean and intervention** conditions: pipeline testing, metric development, intervention auditing, and reproducibility checks. Supports JSONL schemas (`BaseTask`, `InterventionSpec`, `BenchmarkInstance`).

## Out-of-Scope Use

- Leaderboards from development/stub runs.
- Claims about real-world reliability without non-synthetic evaluation.
- Fine-tuning on public instances without disclosure and held-out evaluation.
- Live actions (email, bookings, payments, authenticated APIs, live web).

## Data Construction

| Stage | Output |
|-------|--------|
| Generate | `base_tasks.jsonl`, `interventions.jsonl`, `instances.jsonl`, `generation_report.json`, `quality_report.md`, `splits.json` |
| Quality check | Flags missing answers, multi-factor patches, impossible step budgets, duplicate instances |
| Freeze | Copies to `data/frozen/<version>/`, disjoint splits, `dataset_hash`, `benchmark_card_snapshot.md` |

**Generators:** `src/causal_agent_bench/generation/`
**Configs:** `configs/generate_pilot_v0_1.yaml`, `configs/generate_main_v0_1_500.yaml`, optional mini-study/web-shadow configs.

**Splits (frozen policy):** `dev`, `pilot`, `validation`, `test`, `heldout_templates` — disjoint by base task ID (`docs/DATASET_FREEZE.md`).

## Synthetic Data Policy

- 100% synthetic template/naturalistic/web-snapshot content in default releases.
- Deterministic given `seed` + config hash.
- No PII, no proprietary documents, no model-generated labels in the default generator.
- `hidden_ground_truth` is for scoring and oracle sanity checks — not shown to evaluated agents.
- Users must not commit API keys, `.env` files, or private corpora.

## Intervention Families

10 core families + 5 optional web-shadow families (see `docs/INTERVENTION_CARD.md`). Default pilot freeze uses balanced sampling across core families.

## Scoring Methodology

Instances are scored after agent trajectories are collected. Default heuristic scorer checks answer fragments, tool coverage, recovery, and robustness metrics. See `docs/METRICS.md` and `docs/METRIC_CARD_ACRS.md`. Scorer version is stamped in `ScoreRecord.metadata.scorer`.

## Validation Status

| Check | Status |
|-------|--------|
| JSONL schema validation | Pass (tooling) |
| Generation quality report | Pass for frozen `pilot_v0.1` |
| Split leakage checks | Pass for frozen `pilot_v0.1` |
| Human task-quality audit | Pilot sample exported; **annotations incomplete** |
| Intervention validity (human) | **Incomplete** |
| Production LLM trajectories on frozen split | **Not complete** |

`quality_passed` in `freeze_manifest.json` reflects automated checks only.

## Known Failure Modes

- Template wording overlap with gold answers.
- Domain imbalance in small pilots.
- `gold_tool_sequence` may not be unique.
- Intervention patches may change answerability despite single-factor design intent.
- Large `instances.jsonl` embed full `base_task` copies — version skew if tasks are edited in place.

## Contamination Risk

| Risk | Severity | Notes |
|------|----------|-------|
| Train on public instances | High | Report exposure; use held-out templates for final eval |
| Prompt leakage from papers/repos | Medium | Document prompt hashes |
| Repeated template seeds across papers | Medium | Cite `dataset_hash` and `benchmark_version` |
| Oracle trajectories in shared logs | Low | Label as upper bound only |

## Maintenance Plan

- Bump `benchmark_version` in generation configs for each dataset release.
- Archive `freeze_manifest.json` + git tag (e.g. `dataset-pilot_v0.1`).
- Document schema changes in CHANGELOG.
- Add human validation completion reports to frozen bundles when available.
- Future: DOI + external hosting mirror of frozen JSONL.

## License

**MIT** (same as repository `LICENSE`). Attribution: cite repository version, `dataset_hash`, and paper when available.
