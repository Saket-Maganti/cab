# CAB Pre-Run Validation Ledger

Status: `PASS_PROVIDER_FREE`
Final state: `CAB_PRE_RUN_SCIENTIFIC_HARDENING_COMPLETE`
Scientific execution performed: `false`
Provider/model calls performed: `0`

## Definitive checks

| Surface | Command | Result |
|---|---|---|
| Combined scientific slice | `python3 -m pytest -q -n4 tests/test_typed_final_scorer.py tests/test_pre_run_scientific_hardening.py tests/test_manipulation_checks.py tests/test_private_candidate_materialization.py tests/test_cab_split_registry.py tests/test_iclr_resources.py tests/test_static_leakage.py tests/test_claim_ledger.py tests/test_human_validation_protocol.py tests/test_benchmark_manifest.py tests/test_benchmark_quality.py tests/test_level5_benchmark_execution.py` | PASS — 123 passed in 3.77 s |
| Full provider-free suite | `python3 -m pytest -q -n4 -m 'not provider and not model and not local_run'` | PASS — 1,187 passed, 1 skipped in 163.41 s |
| Frozen hardening gate | `python3 -m causal_agent_bench pre-run scientific-check` | PASS — 18/18 checks; required blockers retained |
| Level-5 hardening | `python3 -m causal_agent_bench level5 hardening-check` | PASS — zero critical unresolved issues |
| Reachability | `python3 -m causal_agent_bench benchmark reachability-check` | PASS — 20/20; collection hash `c7b5c8d2be711cc9d29c87ed225cddf134221099a841a9ff2fbde9ec84b825d6` |
| Private/public v2 validation | `python3 scripts/validate_iclr_private_candidates.py` and `--public-only` | PASS — zero issues in both modes |
| Offline notebooks | `python3 scripts/validate_kaggle_notebooks.py --execute-offline` | PASS — 9/9 notebooks, 72 fixture receipts, no live inference |
| Ruff | `python3 -m ruff check .` | PASS |
| Mypy | `python3 -m mypy` | PASS — 234 source files |
| Codespell | `codespell` | PASS |
| Structured data | repository-tracked/unignored JSON, JSONL, YAML parse check | PASS — 168 JSON, 129 JSONL, 124 YAML files |
| Security | `python3 scripts/security_check.py` | PASS |
| Evidence safety | `python3 scripts/check_evidence_safety.py` | PASS — no unsafe evidence promotion; persisted run-index staleness noted as non-blocking fixture inventory only |
| Split registry | `python3 scripts/generate_cab_split_registry.py --check` | PASS — zero issues |
| Documentation | `mkdocs build --strict` | PASS |
| Package build | `python3 -m build --outdir <temporary-directory>` | PASS — wheel and sdist |
| Package metadata | `python3 -m twine check <temporary-directory>/*` | PASS |
| Clean import | fresh venv, wheel installed with `--no-deps` | PASS — package version 0.1.0 |
| CLI smoke | `python3 -m causal_agent_bench --help` | PASS |
| Release dry run | `python3 scripts/release_dry_run.py --skip-tests` | PASS — release and draft camera-ready precheck; full tests recorded separately above |
| Release inventory | `python3 scripts/release_check.py` | PASS — 745 files; bundle hash `82604e560b4cdbff33b892718c0fc20bdccb43a7fef606af37ecb3f4ad117c2f` |

The first full-suite attempt exposed seven stale integration references in the
legacy split registry, release inventory, Compact manipulation fixture, and
small assignment fixture. Those references were repaired; the definitive full
rerun above is green. Deterministic Scale and transfer assignment artifacts were
regenerated twice with identical hashes before validation.

## Evidence boundary

All nine genuine-evidence counters remain zero. The expected external gates are
`HUMAN_VALIDATION_REQUIRED` and `LIVE_EVIDENCE_REQUIRED`; validation does not
clear or weaken either gate.
