# Local CPU execution ledger

- Recorded: `2026-08-05T18:36:09.843261+00:00`
- Commit: `23b6f9f7e509502cd9c70e5f3b1e5cf313b1e50e`
- Worktree clean at start: `False`
- Host: `macOS-26.5.2-arm64-arm-64bit`, 10 CPUs, pytest workers `4`
- Gates: **13/15 passed**
- Regressions introduced here: **none**
- Failing for reasons that predate this work: `['max_ceiling_validation', 'leakage_gate']`
- Model or provider invoked: `False`
- Genuine model trajectories: `0`

| Gate | Result | Seconds | What it checks |
| --- | --- | ---: | --- |
| `fast_check` | pass | 65.3 | the repository's own fast pre-commit gate |
| `ruff` | pass | 0.1 | lint the whole tree |
| `mypy` | pass | 0.2 | type-check the whole tree |
| `codespell` | pass | 0.7 | spelling in prose and identifiers |
| `pytest_full` | pass | 178.9 | the complete provider-free test suite, bounded to 4 workers |
| `max_ceiling_validation` | **FAIL (1)** — pre-existing | 592.6 | the recorded provider-free validation ledger, every lane |
| `structured_data` | pass | 0.9 | every tracked JSON, YAML, CSV and notebook parses |
| `security_check` | pass | 14.6 | no secret or private material is tracked |
| `leakage_gate` | **FAIL (1)** — pre-existing | 28.2 | no held-out material reachable from public files |
| `release_check` | pass | 0.1 | release inventory and packaging invariants |
| `kaggle_notebooks_static` | pass | 0.1 | T4x2 notebooks: valid JSON, no stale outputs, no filename dependence |
| `kaggle_notebooks_offline` | pass | 0.3 | T4x2 notebooks actually executed offline against fixtures |
| `kaggle_cpu_notebooks_static` | pass | 0.1 | CPU notebooks match their generator and carry no committed output |
| `kaggle_cpu_notebooks_offline` | pass | 0.6 | CPU notebooks executed offline against a randomly renamed bundle |
| `kaggle_arbitrary_name_probe` | pass | 2.3 | the real bundle is found by content under hostile names and shapes |

## Failed gates

### `max_ceiling_validation`

Pre-existing. Reproduced unchanged at `22dbff07056492bdeaa02fb82a75110282bf1f4c`, before any commit in this line of work.

its unified_build_gate check inherits the leakage blockers above, and additionally reads the production review workspace, which correctly reports HUMAN_REVIEW_INCOMPLETE because this review was imported under a separate origin that production gates refuse by design.

```text
[PASS] typed_scorer_fixture rc=0 elapsed=0.116s
[PASS] paired_metrics_fixture rc=0 elapsed=0.147s
[PASS] canonical_split_registry rc=0 elapsed=0.557s
[FAIL] leakage_and_task_contract_gate rc=1 elapsed=28.105s
[PASS] claim_ledger rc=0 elapsed=0.182s
[PASS] config_audit rc=0 elapsed=0.100s
[PASS] git_diff_check rc=0 elapsed=0.043s
[EXPECTED_BLOCKED] human_review_c10 rc=2 elapsed=1.031s
[PASS] kaggle_notebooks_static rc=0 elapsed=0.080s
[PASS] kaggle_notebooks_offline_fixture rc=0 elapsed=0.304s
[PASS] evidence_safety rc=0 elapsed=0.728s
[PASS] paper_placeholders_draft rc=0 elapsed=0.031s
[PASS] paper_section_contract rc=0 elapsed=0.031s
[PASS] paper_assets_draft rc=0 elapsed=0.037s
[PASS] bibliography rc=0 elapsed=0.024s
[PASS] reviewer_proofing rc=0 elapsed=0.024s
[PASS] paper_draft_compile rc=0 elapsed=2.345s
[PASS] repository_consistency rc=0 elapsed=15.950s
[PASS] security_scan rc=0 elapsed=14.460s
[PASS] release_manifest_refresh rc=0 elapsed=0.169s
[PASS] release_validation rc=0 elapsed=0.079s
[PASS] full_provider_free_tests rc=0 elapsed=360.606s
[FAIL] unified_build_gate rc=1 elapsed=50.854s
[EXPECTED_BLOCKED] unified_execution_gate_fail_closed rc=2 elapsed=50.328s
```

### `leakage_gate`

Pre-existing. Reproduced unchanged at `22dbff07056492bdeaa02fb82a75110282bf1f4c`, before any commit in this line of work.

task_intervention_lint reports contract blockers on the public development splits (compact20_pilot 3, scale100 600, naturalistic 432, main500 3000, contaminated held-out 300). Identical counts at the starting commit and at its parent.

```text
status: LEAKAGE_GATE_BLOCKED
run_eligible_under_phase2_phase3: false
internal_blocker_count: 5
output: audits/max_ceiling/leakage_gate/CAB_PHASE2_PHASE3_GATE.json
BLOCKER: task_intervention_lint / compact20_pilot: 3 contract blocker(s)
BLOCKER: task_intervention_lint / scale100_public_development_v1: 600 contract blocker(s)
BLOCKER: task_intervention_lint / naturalistic_public_development_v1: 432 contract blocker(s)
BLOCKER: task_intervention_lint / main500_public_development_v1: 3000 contract blocker(s)
BLOCKER: task_intervention_lint / heldout_challenge_v1_contaminated: 300 contract blocker(s)
```

