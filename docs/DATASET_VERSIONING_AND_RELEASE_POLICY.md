# Dataset Versioning and Release Policy

## Version naming

- **Processed builds:** `data/processed/<slug>/` (e.g., `pilot_v0_1`, `main_v0_1_500`) — mutable during development.
- **Frozen releases:** `data/frozen/<version>/` (e.g., `pilot_v0.1`) — immutable after freeze.
- **Version slug rules:** lowercase, semver-like (`v0.1`, `v0.1_500`), no spaces.

## Freeze rules

1. Run `audit-interventions` and `audit_intervention_isolation` — must pass for release candidate.
2. Run `audit-contamination` on splits.
3. Write `freeze_manifest.json` with file hashes, generation config hash, seed, timestamp.
4. Copy processed → frozen via `freeze-dataset` CLI; never edit frozen files in place.

## Mutation rules

| Location | Editable? | Action |
|---|---|---|
| `data/processed/` | Yes (dev) | Regenerate with new config; bump generation report |
| `data/frozen/` | No | Create new version directory |
| `data/sample/` | Rarely | Smoke tests only |

## Hash requirements

Every frozen manifest must record SHA-256 for:

- `base_tasks.jsonl`, `interventions.jsonl`, `instances.jsonl`
- `splits.json`, `generation_report.json`
- Audit reports bundled at freeze time

## Changelog requirements

- Update `CHANGELOG.md` on freeze with version, task counts, audit summary.
- Update `docs/DATASET_CARD.md` with version pointer.

## Split plan

| Split | Purpose | Leaderboard? |
|---|---|---|
| dev | Generator tuning | No |
| validation | Prompt/scorer calibration | No |
| test | Primary reported metrics | Yes (when active) |
| held-out templates | Template generalization | No (hidden IDs) |

## Human audit sample

- `human_audit_sample.jsonl` must link to frozen version ID.
- Annotations reference `instance_id` + frozen manifest hash.

## Deprecation

1. Mark deprecated in `DATASET_CARD.md` and `release_manifest.json`.
2. Keep frozen directory read-only for reproducibility.
3. Do not delete without archival notice (Zenodo/README).

## Citation

Use `CITATION.cff` + dataset version string:

> CausalAgentBench pilot v0.1 (frozen), manifest hash `…`, accessed YYYY-MM-DD.

## Preventing silent changes

- CI validates sample schema; release check validates frozen manifest.
- Paper experiments must cite `dataset_version` from `run_metadata.json`.
- `git_dirty=true` in release manifest warns against uncommitted local changes.
