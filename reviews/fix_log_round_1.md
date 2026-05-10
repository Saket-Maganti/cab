# Fix Log Round 1

## Code Fixes

- Removed schema-native oracle leakage from `planner_executor_stub_agent`.
  - File: `src/causal_agent_bench/agents/planner_executor_stub_agent.py`
  - Test: `tests/test_agents.py::test_planner_executor_does_not_use_schema_gold_sequence`
- Added resume config-hash validation.
  - File: `src/causal_agent_bench/runners/experiment.py`
  - Test: `tests/test_experiment_runner.py::test_resume_rejects_config_hash_mismatch`

## Documentation Fixes

- Updated `README.md` so smoke scoring points to timestamped run directories and the dev workflow is explicit.
- Expanded `docs/INTERVENTIONS.md` with realistic analogues, expected robust behavior, a "not just random perturbation" explanation, and realism limitations.
- Expanded `docs/METRICS.md` to state that ACRS is only a summary metric and binary metrics are heuristic indicators.
- Updated `docs/BASELINE_AGENTS.md` to separate oracle, legacy metadata behavior, and minimum paper-grade baselines.
- Updated `docs/RUNNING_EXPERIMENTS.md` to document resume config-hash checks.
- Updated `docs/CLAIM_LEDGER.md` C9 with the config-hash fix.

## Paper Fixes

- Downgraded unsupported abstract language from "we find" to planned-test language.
- Changed contribution bullet from "we evaluate and show" to "we provide an experimental protocol to evaluate and test."
- Added a paragraph explaining why paired interventions differ from ordinary perturbations.
- Added a synthetic-environment justification paragraph.
- Added an ACRS insufficiency paragraph.
- Strengthened the baseline/oracle warning in experimental setup.

## Verification

Commands run after fixes:

```bash
pytest tests/test_agents.py::test_planner_executor_does_not_use_schema_gold_sequence tests/test_experiment_runner.py::test_resume_rejects_config_hash_mismatch
python3 -m ruff check src/causal_agent_bench/agents/planner_executor_stub_agent.py src/causal_agent_bench/runners/experiment.py tests/test_agents.py tests/test_experiment_runner.py
```

Full verification is recorded in the final assistant response for this prompt.

Additional full verification run:

```bash
python3 -m ruff check .
pytest
python3 -m causal_agent_bench generate --config configs/dev_20_tasks.yaml
python3 -m causal_agent_bench run --config configs/dev_20_run.yaml
python3 -m causal_agent_bench analyze --run-dir results/20260510T165955Z_dev_20
cd paper && pdflatex -interaction=nonstopmode main.tex && bibtex main && pdflatex -interaction=nonstopmode main.tex && pdflatex -interaction=nonstopmode main.tex
```

The local `python` shim still points to a missing pyenv `3.11`, so verification used `python3`.
