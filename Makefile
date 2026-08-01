PYTHON ?= python3
PIP ?= $(PYTHON) -m pip
CAB_PYTHONPATH ?= src:.
CAB_MAX_CEILING_TESTS := \
	tests/test_typed_final_scorer.py \
	tests/test_phase5_paired_metrics.py \
	tests/test_static_leakage.py \
	tests/test_leakage_suppressions.py \
	tests/test_cab_split_registry.py \
	tests/test_kaggle_notebooks.py \
	tests/test_security_check.py \
	tests/test_claim_ledger.py \
	tests/test_release_check.py
CAB_PRE_RUN_HARDENING_TESTS := \
	tests/test_typed_final_scorer.py \
	tests/test_pre_run_scientific_hardening.py \
	tests/test_kaggle_notebooks.py \
	tests/test_security_check.py \
	tests/test_static_leakage.py

.PHONY: install test test-serial coverage lock audit spell mutate lint typecheck smoke fast-check precommit pre-commit-install build-check security-check artifact-check artifact-smoke artifact-deterministic release-check release-dry-run paper-fill export-leaderboard export-failure-gallery ablation-matrix batch-smoke audit-contamination paper paper-draft paper-check paper-submission-check submission-precheck submission-check help doctor plan-micro audit-configs audit-repo check-claims check-paper check-readiness index-runs check-run-index god-tier-status no-run-reports governance-reports clean-pycache status master-status final-audit max-ceiling-tests max-ceiling-tests-serial split-registry-check kaggle-fixture-check iclr-resource-check max-ceiling-static-gates max-ceiling-ci max-ceiling-ci-serial level5-test level5-hardening-test level5-coverage level5-reproduce level5-check level5-hardening-check level5-sbom pre-run-scientific-check

help:
	@echo "Safe targets: install, test, coverage, lint, typecheck, fast-check, precommit,"
	@echo "  pre-commit-install, doctor, plan-micro, audit-repo, audit-configs, check-claims,"
	@echo "  check-paper, check-readiness, index-runs, check-run-index, god-tier-status,"
	@echo "  no-run-reports, governance-reports, status, master-status, final-audit,"
	@echo "  clean-pycache, security-check, max-ceiling-ci, max-ceiling-ci-serial,"
	@echo "  pre-run-scientific-check"
	@echo "Unsafe (may run models): smoke, paper-fill, ablation-matrix --execute"

install:
	$(PIP) install -e ".[dev]"

test:
	$(PYTHON) -m pytest

# Serial run for interactive debugging (pdb/breakpoint, readable -s output).
test-serial:
	$(PYTHON) -m pytest -n0

# Provider-free regression slice for correctness and release-critical surfaces.
max-ceiling-tests:
	PYTHONPATH=$(CAB_PYTHONPATH) $(PYTHON) -m pytest -q $(CAB_MAX_CEILING_TESTS)

# Deterministic fallback for hosts where pytest-xdist is unavailable or undesirable.
max-ceiling-tests-serial:
	PYTHONPATH=$(CAB_PYTHONPATH) $(PYTHON) -m pytest -q -o addopts="" $(CAB_MAX_CEILING_TESTS)

split-registry-check:
	PYTHONPATH=$(CAB_PYTHONPATH) $(PYTHON) scripts/generate_cab_split_registry.py --check

kaggle-fixture-check:
	PYTHONPATH=$(CAB_PYTHONPATH) $(PYTHON) scripts/validate_kaggle_notebooks.py --execute-offline

iclr-resource-check:
	PYTHONPATH=$(CAB_PYTHONPATH) $(PYTHON) scripts/cab_resource_preflight.py --worker-mode low_memory --bootstrap-mode pilot --output /tmp/cab_resource_preflight.json

max-ceiling-static-gates: split-registry-check kaggle-fixture-check
	PYTHONPATH=$(CAB_PYTHONPATH) $(PYTHON) scripts/security_check.py
	PYTHONPATH=$(CAB_PYTHONPATH) $(PYTHON) scripts/check_claim_ledger.py --mode draft
	PYTHONPATH=$(CAB_PYTHONPATH) $(PYTHON) scripts/release_check.py

max-ceiling-ci: max-ceiling-tests max-ceiling-static-gates

max-ceiling-ci-serial: max-ceiling-tests-serial max-ceiling-static-gates

level5-test:
	$(PYTHON) -m pytest -q -n4 tests/test_level5_*.py

level5-hardening-test:
	$(PYTHON) -m pytest -q -n2 tests/test_level5_hardening_*.py

level5-coverage:
	$(PYTHON) -m pytest -n0 -q tests/test_level5_*.py \
		--cov=causal_agent_bench.level5 --cov-report=json:/tmp/cab-level5-coverage.json \
		--cov-fail-under=0
	$(PYTHON) scripts/check_level5_coverage.py /tmp/cab-level5-coverage.json

level5-reproduce:
	$(PYTHON) -m causal_agent_bench reproduce --workdir /tmp/cab_level5_reproduction

level5-check:
	$(PYTHON) -m causal_agent_bench level5 check

level5-hardening-check:
	$(PYTHON) -m causal_agent_bench level5 hardening-check

level5-sbom:
	$(PYTHON) scripts/generate_level5_sbom.py
	$(PYTHON) scripts/generate_dependency_licenses.py

pre-run-scientific-check:
	PYTHONPATH=$(CAB_PYTHONPATH) $(PYTHON) -m pytest -q -n0 $(CAB_PRE_RUN_HARDENING_TESTS)
	PYTHONPATH=$(CAB_PYTHONPATH) $(PYTHON) -m causal_agent_bench level5 hardening-check
	PYTHONPATH=$(CAB_PYTHONPATH) $(PYTHON) -m causal_agent_bench benchmark reachability-check
	PYTHONPATH=$(CAB_PYTHONPATH) $(PYTHON) -m causal_agent_bench pre-run scientific-check
	PYTHONPATH=$(CAB_PYTHONPATH) $(PYTHON) scripts/validate_iclr_private_candidates.py --public-only
	PYTHONPATH=$(CAB_PYTHONPATH) $(PYTHON) scripts/validate_kaggle_notebooks.py
	PYTHONPATH=$(CAB_PYTHONPATH) $(PYTHON) scripts/security_check.py

coverage:
	$(PYTHON) -m pytest --cov=causal_agent_bench --cov-report=term-missing --cov-report=html --cov-report=xml

pre-commit-install:
	$(PYTHON) -m pre_commit install --install-hooks

# Regenerate the pinned runtime lockfile (needs pip-tools: pip install pip-tools).
lock:
	$(PYTHON) -m piptools compile --quiet --output-file=constraints.txt pyproject.toml

# Scan the pinned runtime deps for known CVEs (needs pip-audit: pip install pip-audit).
audit:
	$(PYTHON) -m pip_audit --requirement constraints.txt

# Mutation-test the correctness core (needs mutmut: pip install mutmut). Slow, opt-in.
mutate:
	$(PYTHON) -m mutmut run

# Spell-check prose + code (config + ignore list in [tool.codespell]).
spell:
	codespell

fast-check:
	$(PYTHON) scripts/run_fast_checks.py

precommit:
	bash scripts/precommit_fast.sh

doctor:
	$(PYTHON) -m causal_agent_bench doctor

plan-micro:
	$(PYTHON) -m causal_agent_bench plan-run --config configs/pilot_stub_micro_3.yaml

audit-configs:
	$(PYTHON) scripts/audit_configs.py

audit-repo:
	$(PYTHON) scripts/audit_repo_consistency.py

check-claims:
	$(PYTHON) scripts/check_claim_ledger.py

check-paper:
	$(PYTHON) scripts/check_paper_placeholders.py --mode draft
	$(PYTHON) scripts/check_paper_section_contract.py --mode draft
	$(PYTHON) scripts/validate_paper_assets.py --mode draft || true
	$(PYTHON) scripts/lint_paper_claims.py --mode draft || true

check-readiness:
	$(PYTHON) scripts/check_submission_readiness.py || true

index-runs:
	$(PYTHON) -m causal_agent_bench index-runs --results-root results

check-run-index:
	$(PYTHON) scripts/check_run_index.py

god-tier-status:
	$(PYTHON) scripts/god_tier_status.py

no-run-reports:
	$(PYTHON) -m causal_agent_bench all-no-run-reports --output-dir /tmp/cab_no_run_reports

governance-reports: no-run-reports

status:
	$(PYTHON) scripts/generate_project_status.py

master-status:
	$(PYTHON) scripts/generate_master_status.py

final-audit:
	$(PYTHON) scripts/final_build_phase_audit.py || true

clean-pycache:
	find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -prune -exec rm -rf {} + 2>/dev/null || true

build-check: fast-check
	$(PYTHON) -m causal_agent_bench index-runs --results-root results

lint:
	$(PYTHON) -m ruff check .

typecheck:
	$(PYTHON) -m mypy

smoke:
	$(PYTHON) -m causal_agent_bench --help
	$(PYTHON) -m causal_agent_bench validate data/sample/instances.jsonl --schema instances
	$(PYTHON) -m causal_agent_bench run --config configs/smoke.yaml

artifact-check:
	$(PYTHON) scripts/reproduce_artifact.py --check

artifact-smoke:
	$(PYTHON) scripts/reproduce_artifact.py --step install
	$(PYTHON) scripts/reproduce_artifact.py --step smoke

artifact-deterministic:
	$(PYTHON) scripts/reproduce_artifact.py --all-deterministic

security-check:
	$(PYTHON) scripts/security_check.py

release-check: security-check
	$(PYTHON) scripts/release_check.py

release-dry-run:
	$(PYTHON) scripts/release_dry_run.py

submission-precheck:
	$(PYTHON) scripts/camera_ready_precheck.py --mode draft

submission-check:
	$(PYTHON) scripts/camera_ready_precheck.py --mode submission

paper-fill:
	@test -n "$(RUN_DIR)" || (echo "Set RUN_DIR=results/<timestamp>_<run_name>"; exit 1)
	$(PYTHON) scripts/fill_paper_from_run.py --run-dir $(RUN_DIR) $(PAPER_FILL_FLAGS)

export-leaderboard:
	@test -n "$(RUN_DIR)" || (echo "Set RUN_DIR=results/<timestamp>_<run_name>"; exit 1)
	$(PYTHON) -m causal_agent_bench export-leaderboard --run-dir $(RUN_DIR) $(if $(EVAL_SPLIT),--eval-split $(EVAL_SPLIT),) $(if $(SPLITS_PATH),--splits-path $(SPLITS_PATH),)

audit-contamination:
	@test -n "$(BENCHMARK_DIR)" || (echo "Set BENCHMARK_DIR=data/frozen/pilot_v0.1"; exit 1)
	$(PYTHON) -m causal_agent_bench audit-contamination --benchmark-dir $(BENCHMARK_DIR)

export-failure-gallery:
	$(PYTHON) -m causal_agent_bench export-failure-gallery $(if $(RUN_DIR),--run-dir $(RUN_DIR),)

ablation-matrix:
	$(PYTHON) -m causal_agent_bench ablation-matrix $(if $(MATRIX_CONFIG),--config $(MATRIX_CONFIG),) $(if $(EXECUTE),--execute,) $(if $(MATRIX_OUTPUT_DIR),--output-dir $(MATRIX_OUTPUT_DIR),)

batch-smoke:
	$(PYTHON) -m pytest tests/test_batch_runner.py -q

paper: paper-draft

paper-draft: paper-check
	cd paper/latexpaper && pdflatex -interaction=nonstopmode main.tex
	cd paper/latexpaper && bibtex main
	cd paper/latexpaper && pdflatex -interaction=nonstopmode main.tex
	cd paper/latexpaper && pdflatex -interaction=nonstopmode main.tex

paper-check:
	$(PYTHON) scripts/check_paper_placeholders.py --mode draft
	$(PYTHON) scripts/check_paper_section_contract.py --mode draft
	$(PYTHON) scripts/check_bibliography.py
	$(PYTHON) scripts/check_reviewer_proofing.py
	$(PYTHON) scripts/check_claim_ledger.py --mode draft

paper-submission-check: submission-check
	$(PYTHON) scripts/check_paper_placeholders.py --mode submission
	$(PYTHON) scripts/check_paper_section_contract.py --mode submission
