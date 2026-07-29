# CAB CPU Execution Ledger

Measurements are `MEASURED_ON_LOCAL_M4`. Peak RSS is the maximum child-process resident set observed by `getrusage`; `null` means unavailable.

| Run | Command | Seconds | Exit | Expected | Peak RSS MiB | Disk Δ MiB | Status |
|---|---|---:|---:|---:|---:|---:|---|
| CPU-00 | `python3 scripts/check_iclr_preexecution_readiness.py` | 56.003 | 1 | 2 | 1874.3 | 41.50 | UNEXPECTED_FAILURE |

- **CPU-00 note:** - Do not expose private task payloads, answers, intervention labels, or evaluator metadata. / evidence_counts: / - genuine_human_rows: 0 / - real_trajectories: 0 / - audited_real_runs: 0 / - paper_eligible_assets: 0 / - supported_empirical_claims: 0 / scientific_execution_performed: false
| CPU-00-REPAIR-MANIFEST | `env PYTHONPATH=src python3 scripts/build_release_manifest.py` | 0.333 | 0 | 0 | 43.4 | -0.03 | PASS |
| CPU-00-RELEASE-RERUN | `python3 scripts/release_check.py` | 0.180 | 0 | 0 | 24.9 | -0.00 | PASS |
| CPU-00-RERUN | `python3 scripts/check_iclr_preexecution_readiness.py --write-json reports/iclr_preexecution_readiness.json` | 54.831 | 2 | 2 | 1875.4 | -1009.04 | PASS |
| CPU-01 | `make fast-check` | 0.235 | 2 | 0 | 23.1 | -0.04 | UNEXPECTED_FAILURE |

- **CPU-01 note:** File "<REPO>/scripts/run_fast_checks.py", line 30, in main / run([py, "-m", "ruff", "check", "."], label="ruff lint") / File "<REPO>/scripts/run_fast_checks.py", line 24, in run / subprocess.run(cmd, cwd=ROOT, check=True, env=env) / File "/Library/Frameworks/Python.framework/Versions/3.11/lib/python3.11/subprocess.py", line 571, in run / raise CalledProcessError(retcode, process.args, / subprocess.CalledProcessError: Command '['/Library/Frameworks/Python.framework/Versions/3.11/bin/python3', '-m', 'ruff', 'check', '.']' returned non-zero exit status 1. / make: *** [fast-check] Error 1
| CPU-01-RUFF-RERUN | `python3 -m ruff check scripts/run_and_record_cpu_stage.py` | 0.124 | 1 | 0 | 19.4 | -0.02 | UNEXPECTED_FAILURE |

- **CPU-01-RUFF-RERUN note:** 13 | | from datetime import UTC, datetime / 14 | | from pathlib import Path / | |________________________^ / | / help: Organize imports / Found 1 error. / [*] 1 fixable with the `--fix` option.
| CPU-01-RUFF-RERUN-2 | `python3 -m ruff check scripts/run_and_record_cpu_stage.py` | 0.125 | 0 | 0 | 19.0 | -0.02 | PASS |
| CPU-01-RERUN | `make fast-check` | 63.760 | 0 | 0 | 620.2 | -5.72 | PASS |
| CPU-02 | `python3 -m pytest -q -n0 tests/test_intervention_validity_profile.py tests/test_phase5_paired_metrics.py tests/test_cab_phase2_phase3_gate.py tests/test_max_ceiling_gate.py tests/test_iclr_preexecution_gate.py tests/test_protected_heldout_contamination.py tests/test_cab_split_registry.py tests/test_release_check.py tests/test_raac.py tests/test_cab_human_review_gate.py tests/test_human_agreement_analysis.py tests/test_manipulation_checks.py tests/test_private_candidate_materialization.py tests/test_iclr_dataset_audit.py tests/test_iclr_resources.py tests/test_iclr_analysis.py tests/test_paper_assets.py` | 68.955 | 0 | 0 | 2562.7 | -18.00 | PASS |
| CPU-03-RUFF | `python3 -m ruff check .` | 0.159 | 0 | 0 | 19.4 | -0.01 | PASS |
| CPU-03-MYPY | `python3 -m mypy` | 0.345 | 0 | 0 | 62.2 | -0.03 | PASS |
| CPU-03-CODESPELL | `python3 -m codespell .` | 0.124 | 1 | 1 | 14.3 | -0.01 | PASS |

- **CPU-03-CODESPELL note:** Optional codespell module is not installed and is not part of CI; command fail-closed state recorded.
| CPU-03-DIFF-CHECK | `git diff --check` | 0.016 | 0 | 0 | 10.8 | -0.00 | PASS |
| CPU-03-INSTALL-CODESPELL | `python3 -m pip install 'codespell>=2.3'` | 0.402 | 0 | 0 | 56.0 | -0.07 | PASS |
| CPU-03-CODESPELL-RERUN | `python3 -m codespell .` | 0.123 | 1 | 0 | 14.3 | -0.01 | UNEXPECTED_FAILURE |

- **CPU-03-CODESPELL-RERUN note:** /Library/Frameworks/Python.framework/Versions/3.11/bin/python3: No module named codespell
| CPU-03-CODESPELL-CLI | `codespell .` | 0.563 | 0 | 0 | 37.5 | 0.09 | PASS |
| CPU-04 | `python3 scripts/validate_tracked_structured_data.py` | 1.006 | 0 | 0 | 233.6 | -0.14 | PASS |
| CPU-04-CONFIG-SCHEMAS | `python3 scripts/audit_configs.py` | 0.196 | 0 | 0 | 19.0 | -0.02 | PASS |
| CPU-04-SPLIT-SCHEMAS | `env PYTHONPATH=src python3 scripts/generate_cab_split_registry.py --check` | 0.677 | 0 | 0 | 159.0 | 0.59 | PASS |
| CPU-05-SECURITY | `python3 scripts/security_check.py` | 14.236 | 0 | 0 | 178.6 | -0.65 | PASS |
| CPU-05-LEAKAGE | `env PYTHONPATH=src python3 scripts/cab_leakage_gate.py` | 30.566 | 0 | 0 | 833.5 | -2.77 | PASS |
| CPU-05-RELEASE | `python3 scripts/release_check.py` | 0.239 | 0 | 0 | 23.9 | 0.54 | PASS |
| CPU-05-HELDOUT | `python3 -m pytest -q -n0 tests/test_protected_heldout_contamination.py tests/test_security_check.py tests/test_release_check.py` | 29.063 | 0 | 0 | 313.4 | 3.25 | PASS |
| CPU-06 | `python3 scripts/validate_cab_human_reviews.py --review-dir data/human_validation/compact20_real_review` | 1.115 | 2 | 2 | 195.7 | -0.16 | PASS |
| CPU-06-PACKET-CONSISTENCY | `python3 -m pytest -q -n0 tests/test_cab_human_review_gate.py tests/test_human_agreement_analysis.py tests/test_manipulation_checks.py` | 2.242 | 0 | 0 | 330.7 | 9.51 | PASS |
| CPU-07 | `env PYTHONPATH=.:src python3 scripts/validate_iclr_private_candidates.py --write-json reports/CAB_CPU_PRIVATE_CANDIDATE_AUDIT.json` | 13.371 | 0 | 0 | 175.9 | -1.38 | PASS |
| CPU-07-TESTS | `python3 -m pytest -q -n0 tests/test_private_candidate_materialization.py tests/test_iclr_dataset_audit.py tests/test_protected_heldout_contamination.py` | 1.711 | 0 | 0 | 225.3 | -0.29 | PASS |
| CPU-08 | `env PYTHONPATH=src python3 scripts/cab_resource_preflight.py --output reports/CAB_CPU_M4_RESOURCE_PREFLIGHT.json` | 0.323 | 0 | 0 | 29.0 | -0.04 | PASS |
| CPU-09 | `env PYTHONPATH=src python3 scripts/validate_kaggle_notebooks.py --execute-offline` | 0.452 | 0 | 0 | 44.2 | -0.09 | PASS |
| CPU-10 | `python3 -m pytest -q -n0 tests/test_phase5_paired_metrics.py tests/test_raac.py tests/test_iclr_analysis.py tests/test_iclr_resources.py tests/test_paper_assets.py tests/test_human_agreement_analysis.py` | 5.260 | 0 | 0 | 359.7 | -4.55 | PASS |
| CPU-10-BOOTSTRAP-1000 | `python3 -c 'from tests.test_phase5_paired_metrics import _paired_rows; from causal_agent_bench.metrics.causal_robustness import agent_robustness; from causal_agent_bench.metrics.statistics import clustered_paired_bootstrap; pairs=agent_robustness(_paired_rows([(1,0),(1,1),(0,0),(1,1)]))["agent_a"]["pair_outcomes"]; result=clustered_paired_bootstrap(pairs,seed=20260728,n_boot=1000); assert result["n_boot"] == 1000; print("FIXTURE_ONLY bootstrap_replicates=1000 cluster_count=", result["cluster_count"])'` | 0.255 | 1 | 0 | 43.8 | -0.07 | UNEXPECTED_FAILURE |

- **CPU-10-BOOTSTRAP-1000 note:** Traceback (most recent call last): / File "<string>", line 1, in <module> / File "<REPO>/tests/test_phase5_paired_metrics.py", line 9, in <module> / from causal_agent_bench.metrics.causal_robustness import ( / ModuleNotFoundError: No module named 'causal_agent_bench'
| CPU-10-BOOTSTRAP-1000-RERUN | `env PYTHONPATH=src:. python3 -c 'from tests.test_phase5_paired_metrics import _paired_rows; from causal_agent_bench.metrics.causal_robustness import agent_robustness; from causal_agent_bench.metrics.statistics import clustered_paired_bootstrap; pairs=agent_robustness(_paired_rows([(1,0),(1,1),(0,0),(1,1)]))["agent_a"]["pair_outcomes"]; result=clustered_paired_bootstrap(pairs,seed=20260728,n_boot=1000); assert result["n_boot"] == 1000; print("FIXTURE_ONLY bootstrap_replicates=1000 cluster_count=", result["cluster_count"])'` | 0.344 | 1 | 0 | 63.2 | 0.12 | UNEXPECTED_FAILURE |

- **CPU-10-BOOTSTRAP-1000-RERUN note:** Traceback (most recent call last): / File "<string>", line 1, in <module> / KeyError: 'n_boot'
| CPU-10-BOOTSTRAP-1000-RERUN-2 | `env PYTHONPATH=src:. python3 -c 'from tests.test_phase5_paired_metrics import _paired_rows; from causal_agent_bench.metrics.causal_robustness import agent_robustness; from causal_agent_bench.metrics.statistics import clustered_paired_bootstrap; pairs=agent_robustness(_paired_rows([(1,0),(1,1),(0,0),(1,1)]))["agent_a"]["pair_outcomes"]; result=clustered_paired_bootstrap(pairs,seed=20260728,n_boot=1000); assert result["n_boot_requested"] == 1000; print("FIXTURE_ONLY bootstrap_replicates=1000 valid=", result["n_boot_valid"])'` | 0.337 | 1 | 0 | 63.0 | -0.02 | UNEXPECTED_FAILURE |

- **CPU-10-BOOTSTRAP-1000-RERUN-2 note:** Traceback (most recent call last): / File "<string>", line 1, in <module> / KeyError: 'n_boot_valid'
| CPU-10-BOOTSTRAP-1000-RERUN-3 | `env PYTHONPATH=src:. python3 -c 'from tests.test_phase5_paired_metrics import _paired_rows; from causal_agent_bench.metrics.causal_robustness import agent_robustness; from causal_agent_bench.metrics.statistics import clustered_paired_bootstrap; pairs=agent_robustness(_paired_rows([(1,0),(1,1),(0,0),(1,1)]))["agent_a"]["pair_outcomes"]; result=clustered_paired_bootstrap(pairs,seed=20260728,n_boot=1000); assert result["n_boot_requested"] == 1000 and min(result["n_boot_valid_by_metric"].values()) == 1000; print("FIXTURE_ONLY bootstrap_replicates=1000 cluster_count=", result["cluster_count"])'` | 0.333 | 1 | 0 | 62.9 | -0.01 | UNEXPECTED_FAILURE |

- **CPU-10-BOOTSTRAP-1000-RERUN-3 note:** Traceback (most recent call last): / File "<string>", line 1, in <module> / AssertionError
| CPU-10-BOOTSTRAP-1000-RERUN-4 | `env PYTHONPATH=src:. python3 -c 'from tests.test_phase5_paired_metrics import _paired_rows; from causal_agent_bench.metrics.causal_robustness import agent_robustness; from causal_agent_bench.metrics.statistics import clustered_paired_bootstrap; pairs=agent_robustness(_paired_rows([(1,0),(1,1),(0,0),(1,1)]))["agent_a"]["pair_outcomes"]; result=clustered_paired_bootstrap(pairs,seed=20260728,n_boot=1000); assert result["n_boot_requested"] == 1000 and result["state"] == "ok"; print("FIXTURE_ONLY bootstrap_replicates=1000 cluster_count=", result["cluster_count"], "valid_by_metric=", result["n_boot_valid_by_metric"])'` | 0.351 | 0 | 0 | 62.6 | -0.03 | PASS |
| CPU-11-PAPER | `make paper` | 2.191 | 0 | 0 | 52.2 | -0.12 | PASS |
| CPU-11-CLAIMS | `python3 scripts/check_claim_ledger.py --mode draft` | 0.269 | 0 | 0 | 51.0 | -0.01 | PASS |
| CPU-11-ASSETS | `python3 scripts/validate_paper_assets.py --mode draft` | 0.181 | 0 | 1 | 17.4 | -0.00 | UNEXPECTED_FAILURE |

- **CPU-11-ASSETS note:** - WARNING: paper/latexpaper/generated/00_abstract.tex:1: placeholder marker in paper / - WARNING: paper/latexpaper/generated/01_introduction_snippet.tex:1: placeholder marker in paper / - WARNING: paper/latexpaper/generated/01_introduction_snippet.tex:2: placeholder marker in paper / - WARNING: paper/latexpaper/generated/03_benchmark_stats_table.tex:9: placeholder marker in paper / - WARNING: paper/latexpaper/generated/03_benchmark_stats_table.tex:10: placeholder marker in paper / - WARNING: paper/latexpaper/generated/03_benchmark_stats_table.tex:11: placeholder marker in paper / - WARNING: paper/latexpaper/sections/09_ablations.tex:10: placeholder marker in paper / Paper asset validation passed with 7 warning(s)
| CPU-11-ASSETS-RERUN | `python3 scripts/validate_paper_assets.py --mode draft` | 0.178 | 0 | 0 | 17.5 | -0.02 | PASS |
| CPU-12 | `python3 -m pytest -q -n4 -m 'not provider and not model and not local_run'` | 176.326 | 0 | 0 | 6675.4 | -7865.12 | PASS |
| CPU-13-MANIFEST | `env PYTHONPATH=src python3 scripts/build_release_manifest.py` | 0.401 | 0 | 0 | 44.6 | -0.11 | PASS |
| CPU-13-RELEASE | `make release-check` | 13.948 | 0 | 0 | 221.7 | 9.70 | PASS |
| CPU-13-ARTIFACT | `make artifact-check` | 0.139 | 2 | 0 | 18.7 | -0.02 | UNEXPECTED_FAILURE |

- **CPU-13-ARTIFACT note:** python3 scripts/reproduce_artifact.py --check / Prerequisite check failed: / - causal_agent_bench not importable; run: python -m pip install -e ".[dev]" / make: *** [artifact-check] Error 1
| CPU-13-PAPER | `make paper-check` | 0.819 | 0 | 0 | 52.4 | -0.00 | PASS |
| CPU-13-TESTS | `python3 -m pytest -q -n0 tests/test_release_check.py tests/test_reproducibility_manifest.py tests/test_security_check.py tests/test_claim_ledger.py tests/test_paper_assets.py` | 31.834 | 0 | 0 | 471.2 | 1017.46 | PASS |
| CPU-13-INSTALL-DEV | `python3 -m pip install -e '.[dev]'` | 2.342 | 0 | 0 | 89.2 | -0.21 | PASS |
| CPU-13-ARTIFACT-RERUN | `make artifact-check` | 0.153 | 0 | 0 | 18.7 | -0.01 | PASS |
| CPU-14 | `python3 scripts/check_iclr_preexecution_readiness.py --write-json reports/iclr_preexecution_readiness_final.json` | 52.853 | 2 | 2 | 3191.8 | -0.62 | PASS |
| CPU-13-FINAL-SECURITY | `python3 scripts/security_check.py` | 13.595 | 0 | 0 | 221.7 | 0.01 | PASS |
| CPU-13-FINAL-RELEASE | `python3 scripts/release_check.py` | 0.167 | 0 | 0 | 21.4 | -0.02 | PASS |
| CPU-13-FINAL-MANIFEST-2 | `env PYTHONPATH=src python3 scripts/build_release_manifest.py` | 0.267 | 0 | 0 | 43.8 | -0.03 | PASS |
| CPU-13-FINAL-RELEASE-2 | `python3 scripts/release_check.py` | 0.168 | 0 | 0 | 21.4 | -0.03 | PASS |
| CPU-14-FINAL-RERUN | `python3 scripts/check_iclr_preexecution_readiness.py --write-json reports/iclr_preexecution_readiness_final.json` | 53.185 | 2 | 2 | 2674.6 | -35.16 | PASS |

Full command logs are retained outside the repository under `/tmp/cab_cpu_execution_logs` for this execution session.
