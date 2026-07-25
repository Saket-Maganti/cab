# Repository Audit: Causal Agent Bench

Audit date: 2026-05-20  
Repository root: `/Users/saketmaganti/codexprojects/causal-agent-bench`  
Audit mode: safe inspection only. No model calls, no paid API calls, no benchmark runs, no source-code edits.

## 1. Repository Overview

Project name: `CausalAgentBench` / `causal-agent-bench`.

Paper-facing title in `README.md` and `paper/latexpaper/main.tex`: `When Agent Success Is Not Agent Skill: A Causal Benchmark for Tool-Using LLM Agents`.

Main goal: build a controlled benchmark for tool-using LLM agents where clean task success is compared against paired intervention variants. The benchmark is intended to measure robustness and component skills such as planning, tool selection, argument quality, recovery, contradiction handling, memory verification, stopping behavior, and final-answer quality.

What the code appears to implement:

- Synthetic benchmark generation with clean and intervention instances: `src/causal_agent_bench/generation/`.
- Pydantic schemas and validation: `src/causal_agent_bench/schemas.py`, `src/causal_agent_bench/validation.py`.
- Simulated tools and benchmark environment: `src/causal_agent_bench/tools/`, `src/causal_agent_bench/environment.py`.
- Deterministic baseline agents, stub LLM agents, mock failure-mode agents, and provider-backed agent adapters: `src/causal_agent_bench/agents/`.
- Experiment runner, resume/checkpointing, limits, run status, interruption marking, batch/shard support, cost gates, and run indexing: `src/causal_agent_bench/runners/`.
- Scoring and metrics, including ACRS and trajectory metrics: `src/causal_agent_bench/scoring.py`, `src/causal_agent_bench/metrics/`.
- Analysis, paper-asset export, failure galleries, leaderboard export, human-validation export, and paper filling: `src/causal_agent_bench/analysis/`, `scripts/`.
- Paper draft and claim/evidence governance: `paper/latexpaper/`, `docs/claim_ledger.json`, `docs/CLAIM_LEDGER.md`, `paper/EVIDENCE_GAP_MAP.md`.

Whether it matches a causal agent benchmark paper: yes at the framework and paper-scaffold level. The repo, docs, configs, metrics, and LaTeX draft match the stated paper idea. It does not yet match a completed empirical benchmark paper, because current local artifacts repeatedly mark C1-C8 and C10 as planned, human validation is not complete, and no verified provider-backed pilot/main results were found.

Key repo self-assessment:

- `README.md` says this is an "initial research scaffold and deterministic prototype" and that smoke/dev outputs are engineering checks, not scientific results.
- `MASTER_STATUS.md` classifies the repo as `build_infrastructure_ready`, with empirical claims still planned.
- `PROJECT_HEALTH.md` says science is blocked until provider pilot plus human validation.
- `paper/PAPER_STATUS.md` says results, human validation, and ablations remain blocked.

## 2. Current Repo Structure

Important top-level files:

- `README.md`: project overview, install, safe demos, run warnings, provider-pilot notes, zero-cost strategy.
- `pyproject.toml`: package metadata and dependencies, Python `>=3.11`.
- `.python-version`: `3.11.9`.
- `Makefile`: safe checks, paper checks, run shortcuts, release checks.
- `MASTER_STATUS.md` and `MASTER_STATUS.json`: generated project status and evidence map.
- `PROJECT_HEALTH.md`, `PROJECT_STATUS.md`, `NEXT_DECISION.md`, `BLOCKED_ITEMS.md`: project management/status.
- `LICENSE`, `DATA_LICENSE.md`, `CITATION.cff`, `.env.example`, `CONTRIBUTING.md`.

Core package:

- `src/causal_agent_bench/cli.py`: central argparse CLI with commands for generation, runs, scoring, analysis, run management, paper export, human validation, release, and provider readiness.
- `src/causal_agent_bench/schemas.py`: benchmark/task/trajectory/score schemas.
- `src/causal_agent_bench/environment.py`: local simulated execution environment.
- `src/causal_agent_bench/scoring.py`: scoring entry point.
- `src/causal_agent_bench/trajectory.py`: trajectory export helpers.
- `src/causal_agent_bench/claim_ledger.py`: claim-ledger support.

Benchmark generation:

- `src/causal_agent_bench/generation/base_tasks.py`
- `src/causal_agent_bench/generation/instances.py`
- `src/causal_agent_bench/generation/interventions.py`
- `src/causal_agent_bench/generation/templates.py`
- `src/causal_agent_bench/generation/quality_checks.py`
- `src/causal_agent_bench/generation/naturalistic.py`
- `src/causal_agent_bench/generation/web_shadow.py`

Agent scripts:

- `src/causal_agent_bench/agents/registry.py`: lists registered agents and aliases.
- `src/causal_agent_bench/agents/random_tool_agent.py`
- `src/causal_agent_bench/agents/scripted_oracle_agent.py`
- `src/causal_agent_bench/agents/greedy_tool_agent.py`
- `src/causal_agent_bench/agents/react_stub_agent.py`
- `src/causal_agent_bench/agents/planner_executor_stub_agent.py`
- `src/causal_agent_bench/agents/mock_behavior_agent.py`: deterministic engineering-only failure modes.
- `src/causal_agent_bench/agents/llm_agents.py`: direct, ReAct-style, planner-executor, self-checking, recovery, memory-verifying LLM agents.
- `src/causal_agent_bench/agents/llm_clients.py`: local stub and provider client plumbing.
- `src/causal_agent_bench/agents/llm_adapters.py`: provider-specific adapters.
- `prompts/agents/`: prompt templates and ablation addenda.
- `prompts/judges/`: optional judge prompts.

Benchmark/run scripts:

- `scripts/run_fast_checks.py`
- `scripts/check_pilot_readiness.py`
- `scripts/check_zero_cost_readiness.py`
- `scripts/run_ablation_matrix.py`
- `scripts/run_batch_local.sh`
- `scripts/reproduce_artifact.py`
- `scripts/slurm_batch_template.sh`
- `scripts/audit_repo_consistency.py`
- `scripts/audit_configs.py`
- `scripts/audit_intervention_isolation.py`
- `scripts/audit_contamination.py`
- `scripts/check_experiment_state.py`

Config files:

- Smoke/dev/main: `configs/smoke.yaml`, `configs/dev_20_run.yaml`, `configs/main_200_run.yaml`, `configs/main_500_multi_provider.yaml`.
- Generation configs: `configs/generate_pilot_v0_1.yaml`, `configs/generate_main_v0_1_500.yaml`, `configs/generate_web_shadow_25.yaml`, `configs/generate_mini_study_template_40.yaml`, `configs/generate_mini_study_naturalistic_40.yaml`.
- Mock/stub configs: `configs/pilot_stub_micro_3.yaml`, `configs/pilot_mock_agents_10.yaml`, `configs/pilot_mock_diagnostic_micro.yaml`, `configs/baseline_suite_local_stub.yaml`.
- Provider configs: `configs/pilot_openai_20.yaml`, `configs/pilot_anthropic_20.yaml`, `configs/pilot_gemini_20.yaml`, `configs/pilot_openrouter_20.yaml`, `configs/pilot_multi_provider_20.yaml`.
- Zero-cost/local configs: `configs/pilot_free_local_20.yaml`, `configs/pilot_free_local_fast_10.yaml`, `configs/pilot_free_local_micro_3.yaml`, `configs/pilot_zero_cost_matrix_20.yaml`.
- Commercial configs: `configs/commercial_api_pilot_small_20.yaml`, `configs/commercial_api_pilot_medium_100.yaml`, `configs/commercial_api_main_500.yaml`.
- Provider/pricing registries: `configs/providers.yaml`, `configs/model_pricing.yaml`.
- Ablation configs: `configs/ablation_matrix_local_stub.yaml`, `configs/ablations/`.

Data/result folders:

- `data/processed/pilot_v0_1/`: generated pilot dataset.
- `data/processed/main_v0_1_500/`: candidate main dataset.
- `data/processed/web_shadow_25/`: optional static web-shadow dataset.
- `data/frozen/pilot_v0.1/`: frozen pilot bundle with manifests/audits.
- `results/`: local run artifacts and run index.
- `results/RUN_INDEX.jsonl`, `results/run_index.json`: indexed run state.
- `figures/`, `tables/`: global paper-asset folders, currently populated from engineering/stub outputs or placeholders.
- `data/human_validation/`: only `README.md` found; no completed annotations found.

Paper folders:

- `paper/latexpaper/main.tex`
- `paper/latexpaper/main.pdf`
- `paper/latexpaper/sections/`
- `paper/latexpaper/generated/`
- `paper/PAPER_STATUS.md`
- `paper/PAPER_SYNC_MAP.md`
- `paper/EVIDENCE_GAP_MAP.md`
- `paper/REVIEWER_PACKET.md`

Test folders:

- `tests/`: 59 Python test files found.
- Safe collection result: `python3 -m pytest --collect-only -q` collected 347 tests in 3.37 seconds.
- Not verified: full test execution.

Export scripts:

- `scripts/export_paper_assets.py`
- `scripts/make_paper_assets.py`
- `scripts/fill_paper_from_run.py`
- `scripts/export_leaderboard.py`
- `scripts/export_failure_gallery.py`
- `scripts/export_ablation_table.py`
- `scripts/generate_placeholder_figures.py`
- `scripts/sample_human_validation.py`
- `scripts/analyze_human_validation.py`
- `scripts/build_release_manifest.py`

## 3. Git and Environment Status

Git:

- Current branch: `main`.
- Uncommitted changes: yes.
- `git status --porcelain=v1 | wc -l` reported 425 status entries.
- `git status --short --branch` showed many modified tracked files, many untracked files, and deletions of the old `paper/main.*`, `paper/sections/*`, and `paper/references.bib` paths. Current LaTeX appears to live under `paper/latexpaper/`.
- Because the tree is heavily dirty, this audit cannot tell which changes are intended, generated, or temporary. Not verified.

Python/environment:

- `python --version` failed because the pyenv shim points to a missing local version:
  - `.python-version`: `3.11.9`
  - error said pyenv version `3.11.9` is not installed and only `3.10.13` was available to pyenv.
- `python3 --version` succeeded: `Python 3.11.9`.
- `python3` path from `which`: `/Library/Frameworks/Python.framework/Versions/3.11/bin/python3`.
- `python3 -c "import causal_agent_bench; print(causal_agent_bench.__name__)"` succeeded.
- `python3 -m pytest --collect-only -q` succeeded and collected 347 tests.
- Not verified: full test pass, `make fast-check`, `make doctor`, actual paper build, actual provider availability.

Dependency files found:

- `.python-version`
- `pyproject.toml`

Dependency files not found by inspected patterns:

- No `requirements.txt`.
- No lockfile such as `poetry.lock` or `Pipfile.lock`.
- No `environment.yml` or `environment.yaml`.

Installed relevant packages from `pip3 list`:

| Package | Version |
|---|---:|
| matplotlib | 3.10.8 |
| numpy | 2.4.4 |
| pandas | 2.3.3 |
| pydantic | 2.12.5 |
| pytest | 9.0.2 |
| PyYAML | 6.0.3 |
| rich | 14.3.3 |
| ruff | 0.15.8 |
| scipy | 1.17.1 |
| typer | 0.24.1 |

Obvious environment problems:

- The plain `python` command is broken under pyenv in this repo, even though README examples sometimes use `python`. Prefer `python3` or fix pyenv.
- The repo requires Python `>=3.11`, so pyenv's reported `3.10.13` fallback would not satisfy `pyproject.toml`.
- No dependency lockfile was found, which weakens reproducibility.

## 4. Benchmark Pipeline Status

| Capability | Status | Evidence | Notes |
|---|---|---|---|
| Task generation | implemented | `src/causal_agent_bench/generation/instances.py`, `configs/generate_pilot_v0_1.yaml`, `data/processed/pilot_v0_1/generation_report.json` | Pilot and main candidate datasets exist. |
| Agent execution | implemented | `src/causal_agent_bench/runners/experiment.py`, `src/causal_agent_bench/runners/execution.py`, CLI `run` in `src/causal_agent_bench/cli.py` | Real provider execution is opt-in and gated. Not run during audit. |
| Mock/local agents | implemented | `src/causal_agent_bench/agents/mock_behavior_agent.py`, `src/causal_agent_bench/agents/llm_clients.py`, `configs/pilot_mock_diagnostic_micro.yaml` | Mock/stub/local paths are explicit engineering paths. |
| Scoring | implemented | `src/causal_agent_bench/scoring.py`, `src/causal_agent_bench/metrics/`, CLI `score` | Completion guards prevent default scoring of incomplete runs. |
| Analysis | implemented | `src/causal_agent_bench/analysis/report.py`, `tables.py`, `figures.py`, `statistics.py`, `error_analysis.py` | Analysis assets exist but are mostly engineering-only or placeholder. |
| Export of paper assets | implemented with guards | `src/causal_agent_bench/analysis/paper_assets.py`, `scripts/export_paper_assets.py`, `scripts/fill_paper_from_run.py` | Existing global assets are not paper-claim eligible per metadata. |
| Run index | implemented | `src/causal_agent_bench/runners/index_runs.py`, `results/RUN_INDEX.jsonl` | 36 indexed runs found. |
| Resume support | implemented | CLI `--resume`, `src/causal_agent_bench/runners/resume.py`, `tests/test_experiment_runner.py`, `tests/test_run_management.py` | Config hash mismatch is tested. |
| Interruption detection | implemented | `src/causal_agent_bench/runners/mark_interrupted.py`, `src/causal_agent_bench/runners/run_completion.py`, `docs/INTERRUPTED_AND_MICRO_RUNS.md` | Two interrupted local runs are indexed. |
| Completion guards | implemented | `src/causal_agent_bench/runners/run_completion.py`, calls from scoring/analysis/export | `assert_complete_for_pipeline` blocks incomplete runs by default. |
| Limits on trajectories/runtime | implemented | `src/causal_agent_bench/runners/limits.py`, CLI `--max-trajectories`, `--max-runtime-minutes`, `--stop-after-trajectories` | Config `limits:` blocks exist. |
| Tests for run management | implemented | `tests/test_run_management.py`, `tests/test_batch_runner.py`, `tests/test_experiment_runner.py` | Collect-only passed. Full tests not run. |

Additional pipeline details:

- Paid-call policy is implemented in `src/causal_agent_bench/runners/commercial.py`.
- Zero-cost checks are implemented in `src/causal_agent_bench/runners/zero_cost.py` and `scripts/check_zero_cost_readiness.py`.
- Batch support exists in `src/causal_agent_bench/runners/batch.py`.
- Human-validation export and summarization exist in `src/causal_agent_bench/analysis/human_validation.py`, but actual annotations were not found.

## 5. Results and Run State

Run index:

- `results/RUN_INDEX.jsonl` has 36 entries.
- All inspected index entries have `scientific_evidence: false`.
- No verified completed paid-provider pilot was found.
- No verified completed main experiment was found.

Completed engineering runs:

- Multiple `smoke` runs with 45 trajectories, e.g. `results/20260520T025720Z_smoke`.
- Multiple `dev_20` runs with 400 trajectories, e.g. `results/20260510T110807Z_dev_20`.
- Stub pilot runs:
  - `results/20260511T162146Z_pilot_20_multi_agent_stub`: 600 trajectories, complete, engineering-only.
  - `results/20260519T053609Z_pilot_20_multi_agent_stub`: 600 trajectories, complete, `evidence_level: pilot_stub_engineering_only`.
- Mock diagnostic micro runs:
  - `results/20260520T063119Z_pilot_mock_diagnostic_micro`: 3 trajectories, complete.
  - `results/20260520T072032Z_pilot_mock_diagnostic_micro`: 3 trajectories, complete, `provider_type: mock`, `not_real_llm_behavior: true` in metadata.

Incomplete/interrupted runs:

- `results/20260520T030034Z_pilot_free_local_20`
  - `status: interrupted`
  - `completion_state: incomplete`
  - `completed_trajectories: 21`
  - `expected_trajectories: 360`
  - `provider_type: local`
  - `interruption_reason: user stopped long local run`
  - `scientific_evidence: false`
- `results/20260520T034642Z_pilot_free_local_fast_10`
  - `status: interrupted`
  - `completion_state: incomplete`
  - `completed_trajectories: 3`
  - `expected_trajectories: 10`
  - `provider_type: local`
  - `interruption_reason: user stopped long local run`
  - `scientific_evidence: false`

Mock runs:

- `configs/pilot_mock_diagnostic_micro.yaml` uses `mock_behavior_agent` with `mock_behavior: tool_overuser`, `max_instances: 3`, `max_trajectories: 3`, `allow_paid_calls: false`, and `cost_mode: zero_cost`.
- Metadata for `results/20260520T072032Z_pilot_mock_diagnostic_micro/run_metadata.json` explicitly says `not_real_llm_behavior: true`, `deployment_class: mock_diagnostic_only`, `scientific_evidence: false`.

Pilot runs:

- Stub pilot runs are complete but engineering-only.
- Local Ollama pilot attempts are interrupted/incomplete.
- Provider pilot results were not found.
- `MASTER_STATUS.md` lists "provider_pilot: 30 runs" in its evidence map, but the inspected `RUN_INDEX.jsonl` entries are smoke/dev/stub/local/mock with `scientific_evidence: false`. This classification should be reviewed before using it in any paper or advisor update.

Are results paper-ready?

- No. Existing runs are smoke/dev/stub/mock/interrupted and explicitly not scientific evidence.
- Global tables under `tables/` have paper-like filenames, but metadata marks them ineligible for paper claims. Example: `tables/table2_main_agent_performance.meta.json` has `eligible_for_paper_claims: false`, `engineering_only: true`, `evidence_scope: pilot_stub_engineering_only`.
- `tables/table5_human_validation_agreement.md` is a placeholder: "Human validation agreement | not yet run".
- `tables/table4_ablation_placeholder_or_results.md` is a placeholder: "Ablation results | not yet run".

Do available results support paper claims?

- No for C1-C8 and C10.
- C9 is engineering-only: smoke/mock/stub reproducibility and pipeline checks.
- This conclusion matches `docs/CLAIM_LEDGER.md`, `paper/EVIDENCE_GAP_MAP.md`, and `paper/PAPER_STATUS.md`.

## 6. Paper State

Paper files found:

- `paper/latexpaper/main.tex`
- `paper/latexpaper/main.pdf`
- `paper/latexpaper/references.bib`
- `paper/latexpaper/sections/*.tex`
- `paper/latexpaper/generated/*.tex`
- `paper/PAPER_STATUS.md`
- `paper/PAPER_SYNC_MAP.md`
- `paper/EVIDENCE_GAP_MAP.md`

Last modified dates from `ls -lT`:

- `paper/latexpaper/main.tex`: May 11 22:02:02 2026.
- `paper/latexpaper/main.pdf`: May 20 13:24:06 2026.
- Many section files under `paper/latexpaper/sections/` were modified on May 20, 2026 between about 08:02 and 13:24.
- Generated snippets under `paper/latexpaper/generated/` were modified on May 19 and May 20, 2026.

Current sections included by `paper/latexpaper/main.tex`:

- `sections/00_abstract`
- `sections/01_introduction`
- `sections/02_related_work`
- `sections/03_benchmark_design`
- `sections/04_interventional_framework`
- `sections/05_metrics`
- `sections/06_experiments`
- `sections/07_results`
- `sections/08_human_validation`
- `sections/09_ablations`
- `sections/10_limitations`
- `sections/11_ethics_reproducibility`
- `sections/12_conclusion`
- `sections/checklist`

Missing or placeholder content:

- Numeric placeholders remain in abstract/stats/result text according to `paper/PAPER_STATUS.md`.
- `paper/latexpaper/generated/07_results.tex` states the Results section is a structured placeholder and that no final scientific results are claimed.
- `paper/latexpaper/generated/08_human_validation.tex` states human validation is not complete.
- `paper/latexpaper/generated/09_ablations.tex` states no ablation result is claimed.
- `paper/latexpaper/sections/03_benchmark_design.tex` contains a TODO for a mini-study comparison table.
- `paper/latexpaper/sections/11_ethics_reproducibility.tex` contains a compensation placeholder.

Whether tables/figures are linked:

- Tables are partially linked through generated LaTeX, e.g. `paper/latexpaper/generated/03_benchmark_stats_table.tex`.
- Results text references Tables 2-5 and Figures 2-6, but these are placeholders until verified runs exist.
- No `\includegraphics` references were found in the inspected paper files with the search pattern used. Figures exist under `figures/`, but figure inclusion in the LaTeX draft was not verified as complete.
- `paper/latexpaper/main.pdf` exists, but this audit did not rebuild it. Not verified.

Whether claims are supported by experiments:

- C1-C8 and C10: not supported, planned.
- C9: engineering-only.
- This is documented in `docs/CLAIM_LEDGER.md` and `paper/EVIDENCE_GAP_MAP.md`.

Limitations/reproducibility sections:

- Limitations exist: `paper/latexpaper/sections/10_limitations.tex`.
- Ethics/reproducibility exists: `paper/latexpaper/sections/11_ethics_reproducibility.tex`.
- Related docs exist: `docs/ETHICS_AND_LIMITATIONS.md`, `docs/REPRODUCIBILITY.md`, `docs/EVIDENCE_LEVEL_POLICY.md`, `docs/DO_NOT_OVERCLAIM.md`, `docs/SECURITY_AND_PRIVACY.md`.

## 7. Low-Compute Improvement Opportunities

| Rank | Opportunity | Impact on paper quality | Implementation difficulty | Compute requirement | Why it helps |
|---:|---|---|---|---|---|
| 1 | Create a claim-evidence matrix generated from `results/RUN_INDEX.jsonl`, `docs/claim_ledger.json`, and table metadata | Very high | Medium | None/low | Prevents accidental overclaiming and shows exactly which claims are blocked. |
| 2 | Add a run-health report that flags incomplete, stub, mock, oracle-only, or engineering-only runs | Very high | Low/medium | None | Makes advisor/reviewer discussions cleaner and reduces risk of using bad results. |
| 3 | Validate all global `tables/` and `figures/` metadata before paper use | High | Low | None | Existing assets look paper-ready by filename but are engineering-only by metadata. |
| 4 | Expand deterministic mock-agent failure modes and expected metric assertions | High | Medium | Seconds | Strengthens confidence that trajectory metrics detect intended failure categories. |
| 5 | Add deterministic synthetic failure-case fixtures for C3/C7/C8 | High | Medium | Seconds | Lets paper discuss detector validation without implying real LLM evidence. |
| 6 | Generate an "engineering appendix" from mock/stub runs only | Medium/high | Medium | None/low | Uses existing assets honestly while keeping scientific claims separate. |
| 7 | Add unit tests for paper-fill refusal paths and asset eligibility labels | High | Low | Seconds | Protects against filling the paper from mock/stub/interrupted runs. |
| 8 | Add tests that the run index does not classify smoke/dev as provider pilots | High | Low | Seconds | Current `MASTER_STATUS.md` wording appears potentially misleading. |
| 9 | Improve human-validation dry-run packet examples from existing complete stub/mock runs | Medium | Low | None | Helps advisor review annotation design before any real annotation study. |
| 10 | Generate placeholder figures/tables with large visible "engineering only" labels | Medium | Low | None/low | Reduces temptation to use polished stub figures as empirical evidence. |
| 11 | Add deterministic web-shadow micro fixtures and compare API vs web interface outputs | Medium | Medium | Seconds/minutes | Supports external-validity discussion without live web or paid calls. |
| 12 | Add a reproducibility report that records `python` vs `python3` behavior | Medium | Low | None | Documents the current pyenv mismatch and improves reviewer setup. |
| 13 | Add a "paper TODO inventory" generated from LaTeX and docs | Medium | Low | None | Makes remaining paper work explicit and trackable. |
| 14 | Add a no-provider smoke notebook or static report | Low/medium | Medium | None | Helpful for demos, less central than claim/evidence integrity. |

Best immediate low-compute wins:

1. Run-health report.
2. Asset eligibility validator/report.
3. Claim-evidence matrix.
4. Mock failure-case expansion with tests.
5. Paper TODO inventory.

## 8. Risks / Weaknesses

Major scientific risks:

- No verified provider-backed pilot results were found.
- No completed main 500-task experiment was found.
- No completed human-validation annotations or agreement statistics were found.
- C1-C8 and C10 are not supported by current results.
- Existing paper tables/figures are not eligible for final paper claims.

Paper risks:

- `paper/latexpaper/generated/07_results.tex` is explicitly placeholder-only.
- `paper/latexpaper/generated/08_human_validation.tex` is placeholder-only.
- `paper/latexpaper/generated/09_ablations.tex` is placeholder-only.
- The abstract and benchmark stats still contain numeric placeholders according to `paper/PAPER_STATUS.md`.
- Figure files exist in `figures/`, but LaTeX figure linkage was not verified as complete.
- Old `paper/main.tex`, `paper/main.pdf`, and old `paper/sections/*` paths appear deleted in git status while new `paper/latexpaper/` is untracked. This is probably intentional migration, but it is risky until committed/cleaned.

Reproducibility risks:

- The `python` command fails because of pyenv, despite README commands that sometimes use `python`.
- No dependency lockfile was found.
- The git tree has 425 uncommitted status entries, making reproducibility and review difficult.
- Full tests were not run. Only collection was verified.
- Paper PDF was not rebuilt during audit. Not verified.

Results/run-management risks:

- `MASTER_STATUS.md` lists `provider_pilot: 30 runs`, but inspected run metadata does not show verified provider-pilot evidence. This classification should be fixed or clarified.
- Two local Ollama runs are interrupted and must not support claims.
- Stub/mock runs are useful, but their tables can look paper-ready unless metadata is checked.
- `results/cache/` exists; cache behavior and contents were not audited. Not verified.

Benchmark-definition risks:

- `data/processed/pilot_v0_1/quality_report.md` reports 500 warning-level intervention-validity cases out of 1500 instances.
- One explicit pilot warning: `calendar_email_workflow_easy_000.observation_conflict` marked high validity risk.
- `data/processed/main_v0_1_500/generation_report.json` has `heldout_split_size: 0`, so the main candidate currently lacks a heldout split in that generation report.
- Human/expert audit is required for C10 but not complete.

Command/environment risks:

- Full provider readiness was not verified. No API keys or model IDs were inspected.
- No paid run should be started until `allow_paid_calls`, budget, provider keys, and advisor approval are explicitly in place.
- Long local runs can be interrupted, as current results demonstrate.

## 9. Recommended Next Actions

Immediate fixes, 1-2 hours:

- Fix local Python command consistency: either install/configure pyenv `3.11.9` or update docs/scripts to consistently use the working `python3`.
- Add or run a safe run-health summary over `results/RUN_INDEX.jsonl` that clearly separates complete engineering runs, interrupted runs, mock/stub runs, local preliminary runs, and provider pilots.
- Audit and correct the `MASTER_STATUS.md` evidence-map label that appears to count non-provider smoke/dev runs as `provider_pilot`.
- Add a visible paper-asset eligibility summary for `tables/` and `figures/`, especially Table 2, Table 4, and Table 5.
- Create a concise paper TODO inventory from `paper/latexpaper/` showing all placeholders, TODOs, missing figure links, and blocked claims.
- Keep the current report and any future audit outputs separate from source changes until the dirty tree is intentionally reviewed.

Medium fixes, 1 day:

- Add tests that prevent `fill-paper-from-run` and `export-paper-assets` from silently promoting mock/stub/interrupted assets.
- Expand `mock_behavior_agent` coverage with deterministic fixtures for premature stopping, contradiction blindness, memory blindness, argument sloppiness, recovery weakness, and tool overuse.
- Create deterministic failure-case datasets for C3/C7/C8 and assert expected metric values.
- Improve `docs/CLAIM_LEDGER.md` and `paper/EVIDENCE_GAP_MAP.md` with a generated artifact path table.
- Add a reproducibility/environment report that captures `python`, `python3`, dependency versions, and package import status.
- Review `data/processed/main_v0_1_500/generation_report.json` heldout split status before calling it a main benchmark candidate.

Paper-impact fixes, 2-3 days:

- Prepare, but do not yet run, a provider pilot packet: freeze checklist, cost estimate, dry run, model IDs, budget cap, and advisor approval notes.
- Export a human-validation sample from the first verified non-stub pilot once it exists, then collect/adjudicate enough annotations to support C3/C10.
- Fill paper from a verified non-oracle run only after the claim ledger allows it.
- Replace placeholder Results/Human Validation/Ablations content with cautious pilot evidence only after verified artifacts exist.
- If no provider budget is approved, reframe the paper as a benchmark proposal/infrastructure artifact rather than an empirical benchmark paper.

## 10. Summary for ChatGPT

Current repo maturity:

- Strong infrastructure scaffold.
- Runnable for safe imports and test collection with `python3`.
- Rich docs, configs, audits, run management, metrics, paper scaffolding, and deterministic mock/stub demos.
- Not yet a completed empirical benchmark.

Whether it is runnable:

- `python3` works and package import succeeds.
- `pytest --collect-only` succeeds with 347 tests collected.
- `python` is broken in this checkout due to pyenv `3.11.9` mismatch.
- Full test suite, paper build, and actual provider/local model runs were not verified.

Top 5 missing pieces:

1. Completed provider-backed pilot on a frozen split.
2. Human-validation annotations and agreement statistics.
3. Main-scale experiment results.
4. Supported claim-ledger links for C1-C8 and C10.
5. Final paper result tables/figures populated from verified non-oracle runs.

Top 5 low-compute upgrades:

1. Generated run-health report from `results/RUN_INDEX.jsonl`.
2. Generated claim-evidence matrix from claim ledger plus run/table metadata.
3. Paper asset eligibility validator for `tables/` and `figures/`.
4. Expanded deterministic mock failure fixtures and metric assertions.
5. Paper TODO/placeholder inventory with blocked-claim mapping.

What ChatGPT should help with next:

1. Cleanly summarize the run index and fix misleading evidence labels.
2. Build a low-compute claim-evidence report.
3. Harden paper asset guards so engineering-only outputs cannot be mistaken for results.
4. Expand deterministic mock diagnostics and tests.
5. Prepare a provider-pilot readiness packet for advisor approval, without running paid calls.

