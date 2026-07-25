# 03 Test Report

## Collection and final status

- `python3 -m pytest --collect-only -q`: 245 tests collected.
- Initial full run: 239 passed, 1 skipped, 5 failed.
- Final full run after fixes: `244 passed, 1 skipped in 62.87s`.

## Initial failures

| Failure | Category | Root cause | Action |
|---|---|---|---|
| `test_camera_ready_precheck_passes_on_scaffold` | generated asset/release check | expected canonical paper asset missing | regenerated paper assets from existing engineering-only stub run |
| `test_release_dry_run_cli` | release metadata | stale bundle hash | refreshed `release/release_manifest.json` using release check |
| `test_camera_ready_precheck_cli_json` | generated asset/release check | same missing asset class | regenerated assets |
| `test_freeze_dataset_hash_is_deterministic_for_same_source` | deterministic regression | contamination audit reports were included in stable dataset hash inputs despite timestamp/path fields | patched mutable audit report exclusions |
| `test_release_check_passes_on_repository_manifest` | release metadata | stale bundle hash | refreshed manifest hash |

## Additional targeted fixes validated

- `tests/test_cli.py::test_freeze_dataset_hash_is_deterministic_for_same_source`: passed.
- `tests/test_commercial_api_runs.py tests/test_cli.py::test_estimate_cost_runs_on_pilot_config tests/test_cli.py::test_validate_config_reports_missing_api_key_safely`: 8 passed.
- `scripts/check_paper_assets.py --mode draft`: passed with warnings about unfilled evidence mapping and generated unresolved refs.
- `scripts/release_check.py --write-bundle-hash`: passed.

## Tests still worth adding later

- Dedicated schema validation for `human_audit_sample.jsonl`.
- Stronger sentence-level citation relevance checks.
- Clean-checkout release verification after the current dirty worktree is resolved.

