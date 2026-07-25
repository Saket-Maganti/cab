# CAB Verification Commands

> Canonical maximum-ceiling artifact. Regenerate with `python3 scripts/generate_cab_max_ceiling_reports.py`.

Generated: 2026-07-23T17:26:33.054498+00:00

All commands ran from the repository root. A pass is engineering evidence, not benchmark evidence. Expected nonzero human/execution gates prove fail-closed behavior.

| ID | Lane | Command | Exit | Elapsed (s) | Outcome | Evidence class |
|---|---|---|---:|---:|---|---|
| `package_imports` | fast | `/Library/Frameworks/Python.framework/Versions/3.11/bin/python3 scripts/check_package_import.py` | 0 | 10.831 | `PASS` | `ENGINEERING_ONLY` |
| `cli_help` | fast | `/Library/Frameworks/Python.framework/Versions/3.11/bin/python3 -m causal_agent_bench --help` | 0 | 0.191 | `PASS` | `ENGINEERING_ONLY` |
| `full_test_collection` | fast | `/Library/Frameworks/Python.framework/Versions/3.11/bin/python3 -m pytest --collect-only -q -n0` | 0 | 2.091 | `PASS` | `ENGINEERING_ONLY` |
| `ruff` | fast | `/Library/Frameworks/Python.framework/Versions/3.11/bin/python3 -m ruff check .` | 0 | 0.071 | `PASS` | `ENGINEERING_ONLY` |
| `mypy` | fast | `/Library/Frameworks/Python.framework/Versions/3.11/bin/python3 -m mypy` | 0 | 0.218 | `PASS` | `ENGINEERING_ONLY` |
| `focused_contract_tests` | fast | `/Library/Frameworks/Python.framework/Versions/3.11/bin/python3 -m pytest -q -n0 tests/test_typed_final_scorer.py tests/test_scorer_robustness_fixture_only.py tests/test_phase5_paired_metrics.py tests/test_statistical_reporting.py tests/test_max_ceiling_generation_contract.py tests/test_cab_split_registry.py tests/test_run_manifest_v2.py tests/test_cab_human_review_gate.py tests/test_kaggle_notebooks.py tests/test_max_ceiling_gate.py tests/test_cab_phase2_phase3_gate.py tests/test_phase15_paper_plumbing.py` | 0 | 64.228 | `PASS` | `FIXTURE_ONLY` |
| `typed_scorer_fixture` | fast | `/Library/Frameworks/Python.framework/Versions/3.11/bin/python3 -c 'import json; from causal_agent_bench.metrics.typed_final_answer import typed_scorer_fixture_self_check as f; r=f(); print(json.dumps(r, sort_keys=True)); raise SystemExit(0 if r.get('"'"'status'"'"') == '"'"'PASS'"'"' else 1)'` | 0 | 0.113 | `PASS` | `FIXTURE_ONLY` |
| `paired_metrics_fixture` | fast | `/Library/Frameworks/Python.framework/Versions/3.11/bin/python3 -c 'import json; from causal_agent_bench.metrics.causal_robustness import paired_metrics_fixture_self_check as f; r=f(); print(json.dumps(r, sort_keys=True)); raise SystemExit(0 if r.get('"'"'passed'"'"') else 1)'` | 0 | 0.109 | `PASS` | `FIXTURE_ONLY` |
| `canonical_split_registry` | fast | `/Library/Frameworks/Python.framework/Versions/3.11/bin/python3 -c 'from causal_agent_bench.safety.split_registry import validate_canonical_split_registry as v; r=v('"'"'.'"'"'); print('"'"'\n'"'"'.join(r) if r else '"'"'SPLIT_REGISTRY_PASS'"'"'); raise SystemExit(1 if r else 0)'` | 0 | 0.558 | `PASS` | `ENGINEERING_ONLY` |
| `leakage_and_task_contract_gate` | fast | `/Library/Frameworks/Python.framework/Versions/3.11/bin/python3 scripts/cab_leakage_gate.py` | 0 | 29.973 | `PASS` | `ENGINEERING_ONLY` |
| `claim_ledger` | fast | `/Library/Frameworks/Python.framework/Versions/3.11/bin/python3 scripts/check_claim_ledger.py --mode draft` | 0 | 0.169 | `PASS` | `ENGINEERING_ONLY` |
| `config_audit` | fast | `/Library/Frameworks/Python.framework/Versions/3.11/bin/python3 scripts/audit_configs.py` | 0 | 0.096 | `PASS` | `ENGINEERING_ONLY` |
| `git_diff_check` | fast | `git diff --check` | 0 | 0.033 | `PASS` | `ENGINEERING_ONLY` |
| `human_review_c10` | medium | `/Library/Frameworks/Python.framework/Versions/3.11/bin/python3 scripts/validate_cab_human_reviews.py` | 2 | 0.159 | `EXPECTED_BLOCKED` | `HUMAN_INPUT_REQUIRED` |
| `kaggle_notebooks_static` | medium | `/Library/Frameworks/Python.framework/Versions/3.11/bin/python3 scripts/validate_kaggle_notebooks.py` | 0 | 0.072 | `PASS` | `FIXTURE_ONLY` |
| `kaggle_notebooks_offline_fixture` | medium | `/Library/Frameworks/Python.framework/Versions/3.11/bin/python3 scripts/validate_kaggle_notebooks.py --execute-offline` | 0 | 0.191 | `PASS` | `FIXTURE_ONLY` |
| `evidence_safety` | medium | `/Library/Frameworks/Python.framework/Versions/3.11/bin/python3 scripts/check_evidence_safety.py --mode submission` | 0 | 0.796 | `PASS` | `ENGINEERING_ONLY` |
| `paper_placeholders_draft` | medium | `/Library/Frameworks/Python.framework/Versions/3.11/bin/python3 scripts/check_paper_placeholders.py --mode draft` | 0 | 0.029 | `PASS` | `ENGINEERING_ONLY` |
| `paper_section_contract` | medium | `/Library/Frameworks/Python.framework/Versions/3.11/bin/python3 scripts/check_paper_section_contract.py --mode draft` | 0 | 0.03 | `PASS` | `ENGINEERING_ONLY` |
| `paper_assets_draft` | medium | `/Library/Frameworks/Python.framework/Versions/3.11/bin/python3 scripts/check_paper_assets.py --mode draft` | 0 | 0.026 | `PASS` | `ENGINEERING_ONLY` |
| `bibliography` | medium | `/Library/Frameworks/Python.framework/Versions/3.11/bin/python3 scripts/check_bibliography.py --all-sections` | 0 | 0.023 | `PASS` | `ENGINEERING_ONLY` |
| `reviewer_proofing` | medium | `/Library/Frameworks/Python.framework/Versions/3.11/bin/python3 scripts/check_reviewer_proofing.py` | 0 | 0.022 | `PASS` | `ENGINEERING_ONLY` |
| `paper_draft_compile` | medium | `make paper-draft` | 0 | 2.283 | `PASS` | `ENGINEERING_ONLY` |
| `repository_consistency` | medium | `/Library/Frameworks/Python.framework/Versions/3.11/bin/python3 scripts/audit_repo_consistency.py` | 0 | 14.66 | `PASS` | `ENGINEERING_ONLY` |
| `security_scan` | medium | `/Library/Frameworks/Python.framework/Versions/3.11/bin/python3 scripts/security_check.py` | 0 | 13.6 | `PASS` | `ENGINEERING_ONLY` |
| `full_provider_free_tests` | full | `/Library/Frameworks/Python.framework/Versions/3.11/bin/python3 -m pytest -q -n0 -m 'not model and not provider and not local_run'` | 0 | 283.303 | `PASS` | `ENGINEERING_ONLY` |
| `release_manifest_refresh` | medium | `/Library/Frameworks/Python.framework/Versions/3.11/bin/python3 scripts/build_release_manifest.py` | 0 | 0.141 | `PASS` | `ENGINEERING_ONLY` |
| `release_validation` | medium | `/Library/Frameworks/Python.framework/Versions/3.11/bin/python3 scripts/release_check.py` | 0 | 0.058 | `PASS` | `ENGINEERING_ONLY` |
| `unified_build_gate` | full | `/Library/Frameworks/Python.framework/Versions/3.11/bin/python3 scripts/cab_max_ceiling_gate.py --scope build` | 0 | 48.877 | `PASS` | `ENGINEERING_ONLY` |
| `unified_execution_gate_fail_closed` | full | `/Library/Frameworks/Python.framework/Versions/3.11/bin/python3 scripts/cab_max_ceiling_gate.py --scope execution --no-write` | 2 | 49.084 | `EXPECTED_BLOCKED` | `EXECUTION_PENDING` |

## Summary

- Commands: 30
- Passes: 28
- Expected blocked prerequisites: 2
- Failures: 0
- Timeouts: 0
- Build validation passed: `True`
- Unified build status: `CAB_MAX_CEILING_PREEXECUTION_BUILD_COMPLETE`

## Reproduce

```bash
PYTHONPATH=src:. python3 scripts/run_cab_max_ceiling_validation.py --lane all
```

Serial pytest fallback is embedded with `-n0`; no xdist worker is required.
