# CausalAgentBench Project Dossier

Generated for this checkout on 2026-06-02.

This file is a broad project briefing for CausalAgentBench: what the project is, what has been built, what the repository contains, what can be run, approximate runtimes, current evidence status, and the safety gates that matter before any provider-backed or paper-claim work.

## 1. Short Version

CausalAgentBench is a Python research scaffold for evaluating tool-using language agents under controlled causal interventions. The core idea is that final task success can hide why an agent succeeded or failed. The benchmark pairs clean task instances with intervention variants so the project can measure more specific skills: planning, tool choice, tool arguments, observation handling, contradiction recovery, memory use, stopping behavior, and final answer quality.

The repository is currently best described as build-infrastructure-ready, not empirical-paper-ready. It has schemas, generation, runners, metrics, simulated tools, static audits, reporting, release scaffolding, paper scaffolding, and provider-pilot guardrails. It does not yet contain paper-eligible provider-backed evidence, verified human validation, or supported empirical claims for the main paper.

## 2. Current High-Level Status

| Area | Status |
|---|---|
| Package and CLI | Built |
| Synthetic benchmark generation | Built |
| Simulated tools and stub/mock agents | Built |
| Experiment runner and scoring | Built |
| Static no-run governance reports | Built |
| Paper/release scaffolding | Built |
| Frozen pilot dataset | Present |
| Provider-backed pilot evidence | Not present |
| Paper-eligible runs | 0 |
| Eligible empirical paper assets | 0 |
| Supported empirical claims | 0 |
| Human validation annotations | Not present |
| Public/empirical release readiness | Blocked |
| Provider dry-run/live readiness | Blocked in latest no-run dashboard |

Important caveat: the latest audit found that some generated reports read from `results/RUN_INDEX.jsonl`, which currently lists 36 runs, while a live metadata scan sees 60 run directories. That means run-health/dashboard reports can undercount current run directories until the run index is regenerated or the report code live-scans/staleness-checks the results tree.

## 3. What The Project Is

CausalAgentBench is an interventional benchmark for tool-using LLM agents. It creates base tasks and paired interventions that change specific conditions while trying to preserve the underlying task structure. The goal is to diagnose agent robustness, not just measure aggregate accuracy.

The project emphasizes:

- Clean/intervention task pairing.
- Synthetic but structured task generation.
- Simulated tools and controlled environments.
- Trajectory-level diagnostics.
- Metrics for causal robustness, tool use, recovery, contradiction handling, and final answer quality.
- Strict evidence-level labeling so mock, stub, local, interrupted, and preliminary runs cannot be mistaken for paper-ready provider evidence.
- Paper/release guardrails that prevent unsupported empirical claims from entering results, abstract, conclusion, or claim ledger.

## 4. What Has Been Built

Built components include:

- Python package under `src/causal_agent_bench/`.
- CLI entrypoint: `causal-agent-bench` / `python3 -m causal_agent_bench`.
- Pydantic schemas for tasks, interventions, instances, trajectories, and scores.
- Benchmark generators for deterministic synthetic tasks, naturalistic variants, and web-shadow style tasks.
- Task/intervention quality checks.
- Simulated tool environment.
- Agent implementations and registries, including baseline, random, greedy, scripted oracle, mock, stub, LLM adapter, and provider/client scaffolding.
- Experiment runner with config hashing, metadata, limits, resume/status helpers, scoring, analysis, and report generation.
- Metrics modules, including causal robustness and component diagnostics.
- Static dataset audits: benchmark quality, intervention isolation, contamination, leakage, gold output validation, tool schema validation, pair-link validation.
- Safety/governance reports: claim-evidence matrix, paper asset eligibility, run health, release readiness, release blockers, provider preflight, report quality, evidence dashboard, governance OS, advisor packet, readiness war room.
- Leakage repair workflow: repair plan, proposed manifest, manual repair preview, suppression registry validation, reviewed-ops template, and guarded patch applier.
- Paper scaffolding and paper-status docs.
- Human validation packet and dry-run sample generation.
- Release/reproducibility scaffolding.
- CI/test/lint/typecheck configuration.
- Artifact reproduction scripts for deterministic API-free review paths.

## 5. What Is Not Yet Built Or Not Yet Proven

Not yet available:

- Completed provider-backed non-oracle pilot on a frozen split.
- Paper-eligible provider-backed run artifacts.
- Human validation annotation files and agreement tables.
- Main 500-task multi-provider experiment.
- Supported C1-C8 or C10 empirical claims.
- Submission-ready empirical results.
- Fully clean dataset release state.
- Fully passing latest no-run report-quality bundle.
- Public release readiness.

The existing smoke, stub, mock, local, and interrupted outputs are engineering or preliminary checks. They must not be used as scientific evidence for main empirical claims.

## 6. Repository Inventory

Approximate inventory for this checkout:

| Item | Count |
|---|---:|
| Python modules under `src/causal_agent_bench` | 159 |
| Pytest files | 97 |
| YAML configs | 75 |
| Markdown docs under `docs/` | 92 |
| Python scripts under `scripts/` | 45 |
| Processed dataset directories | 5 |
| Frozen dataset directories | 1 |
| Result directories | 62 |

The worktree is currently dirty with many modified and untracked files. Treat status/readiness reports as describing this local checkout, not necessarily a clean release branch.

## 7. Main Directory Map

| Path | Purpose |
|---|---|
| `src/causal_agent_bench/` | Main Python package |
| `configs/` | Generation, run, provider, mock, stub, local, ablation, and diagnostic YAML configs |
| `data/` | Sample, processed, frozen, human-validation, and web-shadow data |
| `results/` | Generated run outputs and run indices |
| `docs/` | Project documentation hub |
| `paper/` | Paper planning and LaTeX/paper coordination assets |
| `scripts/` | Standalone checks, reproduction, release, status, and paper helpers |
| `tests/` | Pytest suite |
| `reports/` | Generated or checked-in report artifacts |
| `artifact/` | Reviewer artifact reproduction path |
| `experiments/` | Experiment plans, gates, and decision documents |
| `figures/` | Generated or placeholder figures |
| `tables/` | Generated or placeholder tables |
| `release/` | Release manifest and reproducibility planning |
| `handoff/` | Advisor/co-author handoff material |
| `reviews/` | Mock reviews, rebuttal prep, and review matrices |
| `audits/` | Audit snapshots and consistency reports |
| `benchmark_specs/` | Task template registry and benchmark specs |

## 8. Core Python Architecture

| Module/Package | Role |
|---|---|
| `cli.py` | Main command dispatch |
| `schemas.py` | Data schemas |
| `task.py`, `intervention.py` | Core task/intervention models |
| `generation/` | Task generation, templates, naturalistic/web-shadow generators, quality checks |
| `agents/` | Baseline agents, LLM adapters, mock/stub behavior, tool protocol |
| `tools/` | Simulated/mock/web-snapshot tool implementations |
| `environment.py` | Execution environment |
| `runners/` | Experiment execution, config parsing, limits, run metadata, status, reporting |
| `metrics/` | Causal robustness and component metrics |
| `analysis/` | Tables, figures, leaderboard, failure gallery, paper assets |
| `safety/` | No-run reports, evidence governance, leakage, release, provider preflight |
| `claim_ledger.py` | Claim status and promotion guardrails |
| `release/` | Release manifest and command planning |
| `contamination/` and `audit/` | Dataset contamination and intervention audits |

## 9. Data And Dataset Contents

Current instance/base/intervention counts:

| Dataset path | Base tasks | Interventions | Instances |
|---|---:|---:|---:|
| `data/sample` | 3 | 6 | 9 |
| `data/processed/dev_20` | 20 | 60 | 80 |
| `data/processed/main_200` | 200 | 1000 | 1200 |
| `data/processed/main_v0_1_500` | 500 | 2500 | 3000 |
| `data/processed/pilot_v0_1` | 250 | 1250 | 1500 |
| `data/processed/web_shadow_25` | 50 | 250 | 300 |
| `data/frozen/pilot_v0.1` | 250 | 1250 | 1500 |

Dataset directories typically contain:

- `base_tasks.jsonl`
- `interventions.jsonl`
- `instances.jsonl`
- `generation_report.json`
- `quality_report.md`
- optional split files such as `splits.json`, `pilot_*`, `dev_*`, `heldout_*`, `test_*`, and `validation_*`
- optional dataset/intervention/contamination audit reports
- optional human audit samples

The frozen pilot dataset exists under `data/frozen/pilot_v0.1`, but current reports still block provider-pilot readiness because of leakage, evidence, and config/readiness issues.

## 10. Config Families

There are 75 YAML configs in this checkout. Latest config-profile summary:

| Profile | Count |
|---|---:|
| mock diagnostic | 36 |
| unknown/needs review | 16 |
| provider pilot template | 8 |
| local preliminary | 7 |
| commercial API | 3 |
| ablation | 2 |
| smoke engineering | 2 |
| oracle sanity | 1 |

Important config examples:

| Config | Purpose | Run risk |
|---|---|---|
| `configs/smoke.yaml` | Smoke runner config | Starts a run; not strict no-run |
| `configs/pilot_stub_micro_3.yaml` | Tiny local stub pipeline check | No provider cost; bounded |
| `configs/pilot_mock_agents_10.yaml` | Deterministic mock agent check | No provider cost |
| `configs/pilot_mock_diagnostic_micro.yaml` | Mock diagnostic micro check | No provider cost |
| `configs/pilot_free_local_micro_3.yaml` | Tiny local OpenAI-compatible/Ollama style run | Local compute; can take minutes |
| `configs/pilot_free_local_fast_10.yaml` | Larger local-model fast run | Local compute; can take tens of minutes |
| `configs/provider_pilot_tiny_template.yaml` | Provider pilot template | Template only; must not run directly |
| `configs/provider_pilot_tiny_APPROVED.yaml` | Intended approved copy name | Create only after advisor approval |
| `configs/pilot_openai_20.yaml` | OpenAI pilot | Paid/provider, approval required |
| `configs/pilot_anthropic_20.yaml` | Anthropic pilot | Paid/provider, approval required |
| `configs/pilot_gemini_20.yaml` | Gemini pilot | Provider, approval required |
| `configs/pilot_openrouter_20.yaml` | OpenRouter pilot | Provider, approval required |
| `configs/pilot_multi_provider_20.yaml` | Multi-provider pilot | Paid/provider, approval required |
| `configs/main_500_multi_provider.yaml` | Future larger main run | Not ready |
| `configs/commercial_api_main_500.yaml` | Main commercial API run | Paid/main scale, not approved |

## 11. Installation

Requires Python 3.11 or newer.

```bash
python3 -m pip install -e ".[dev]"
```

Optional docs dependencies:

```bash
python3 -m pip install -e ".[docs]"
```

Source-only use:

```bash
export PYTHONPATH=src
```

Provider runs require API keys in environment variables, never in YAML:

| Provider | API key env var | Model env var |
|---|---|---|
| OpenAI | `OPENAI_API_KEY` | `OPENAI_MODEL_ID` |
| Anthropic | `ANTHROPIC_API_KEY` | `ANTHROPIC_MODEL_ID` |
| Gemini | `GOOGLE_API_KEY` or `GEMINI_API_KEY` | `GEMINI_MODEL_ID` |
| OpenRouter | `OPENROUTER_API_KEY` | `OPENROUTER_MODEL_ID` |
| OpenAI-compatible | `OPENAI_COMPATIBLE_API_KEY` | `OPENAI_COMPATIBLE_MODEL_ID` |
| Local OpenAI-compatible | optional `LOCAL_OPENAI_API_KEY` | `LOCAL_OPENAI_MODEL_ID` |

## 12. Main CLI Surface

The CLI is:

```bash
python3 -m causal_agent_bench --help
causal-agent-bench --help
```

Major command groups:

| Group | Representative commands |
|---|---|
| Validate/generate | `validate`, `validate-config`, `generate`, `freeze-dataset` |
| Run/inspect | `run`, `dry-run`, `plan-run`, `run-status`, `monitor`, `mark-interrupted`, `index-runs`, `summarize-run` |
| Scoring/analysis | `score`, `analyze`, `generate-report`, `compare-runs`, `failure-gallery`, `mine-errors` |
| Paper/assets | `export-paper-assets`, `export-ablation-table`, `fill-paper-from-run`, `validate-paper-assets` |
| Provider planning | `list-providers`, `estimate-cost`, `estimate-run-cost`, `provider-pilot-preflight`, `harden-provider-pilot-config` |
| Human validation | `export-human-validation`, `summarize-human-validation`, `human-validation-packet`, `human-validation-dry-run-sample` |
| Safety/no-run | `run-health`, `claim-evidence`, `paper-todo-inventory`, `benchmark-quality`, `intervention-isolation-audit`, `static-leakage-check`, `report-quality-check`, `evidence-dashboard`, `release-readiness`, `release-blockers`, `all-no-run-reports` |
| Repair/governance | `leakage-repair-plan`, `manual-repair-preview`, `reviewed-ops-template`, `apply-leakage-patch`, `leakage-suppression-registry`, `readiness-war-room`, `governance-os`, `next-action-plan` |
| Release/repro | `build-release-manifest`, `plan-repro-bundle`, `capture-env`, `reproducibility-manifest` |

## 13. What Can Be Run And How Long It Takes

Use this table as a practical guide. Times are documented estimates and vary by machine, Python environment, dataset size, provider latency, and whether pytest-xdist is installed.

### Safe Static/No-Run Commands

These do not start benchmark execution, local LLMs, or provider calls.

| Command | Purpose | Typical time |
|---|---|---:|
| `python3 -m causal_agent_bench --help` | Show CLI commands | <1s |
| `python3 -m causal_agent_bench validate-config --config <cfg>` | Validate YAML config | ~2s |
| `python3 -m causal_agent_bench plan-run --config <cfg>` | Estimate trajectories/cost/risk | ~5s |
| `python3 -m causal_agent_bench estimate-cost --config <cfg>` | Estimate provider cost | ~5s |
| `python3 -m causal_agent_bench dry-run --config <cfg> --output-dir results/dry_runs` | Validate/simulate plan without providers | ~30s |
| `python3 -m causal_agent_bench audit-dataset --config <cfg>` | Static dataset quality audit | ~10s |
| `python3 -m causal_agent_bench audit-interventions --benchmark-dir <dir>` | Static intervention checks | ~30s |
| `python3 -m causal_agent_bench audit-contamination --benchmark-dir <dir>` | Contamination/near-duplicate checks | ~60s |
| `python3 -m causal_agent_bench index-runs` | Build run index | ~5s |
| `python3 -m causal_agent_bench run-status --latest` | Inspect latest run | ~2s |
| `python3 -m causal_agent_bench summarize-run --run-dir <dir>` | Summarize run artifacts | ~5s |
| `python3 scripts/check_evidence_safety.py` | Verify claim/evidence guardrails | ~5s |
| `python3 -m causal_agent_bench all-no-run-reports --output-dir /tmp/cab_no_run_reports` | Generate full static governance report bundle | Usually seconds to a few minutes |

### Make Targets

| Command | Purpose | Typical time | Notes |
|---|---|---:|---|
| `make install` | Editable install with dev deps | Varies | Network/package install |
| `make fast-check` | Fast project checks | ~40-60s | No model runs by design |
| `make doctor` | Health checks | ~10s | Safe |
| `make plan-micro` | Plan stub micro config | ~5s | Safe |
| `make audit-repo` | Repo consistency audit | ~20s | Safe |
| `make audit-configs` | Config audit | ~5s | Safe |
| `make check-claims` | Claim ledger check | ~5s | Safe |
| `make check-paper` | Draft paper checks | ~15s | Safe but may report expected blockers |
| `make release-check` | Security/release checks | ~30s plus environment | Safe static checks |
| `make test` | Full pytest suite | Varies | Not strict no-run; can include run-starting tests |
| `make smoke` | Smoke run | Varies | Starts runner; not strict no-run |

### Deterministic Stub/Mock Runs

These are engineering checks only. They do not provide scientific evidence.

| Command | Purpose | Typical time |
|---|---|---:|
| `python3 -m causal_agent_bench run --config configs/pilot_stub_micro_3.yaml` | Tiny local stub run | seconds to ~5m |
| `python3 -m causal_agent_bench run --config configs/pilot_mock_agents_10.yaml` | Mock-agent diagnostic run | seconds |
| `python3 -m causal_agent_bench run --config configs/pilot_mock_diagnostic_micro.yaml` | Mock diagnostic micro run | ~5-10m in command map |

### Local LLM / Zero-Cost Runs

These may use local compute or free-tier providers. They are preliminary only and should not support main paper claims.

| Command/config | Purpose | Typical time |
|---|---|---:|
| `configs/pilot_free_local_micro_3.yaml` | Tiny local LLM run | minutes to 30-60m+ depending model/server |
| `configs/pilot_free_local_fast_10.yaml` | Local fast 10 trajectory run | tens of minutes |
| `configs/pilot_free_local_20.yaml` | Local 20 trajectory pilot | can take hours |
| `configs/pilot_openrouter_free_20.yaml` | OpenRouter free-tier pilot | provider/free-tier latency and rate limits |
| `configs/pilot_gemini_free_20.yaml` | Gemini free-tier pilot | provider/free-tier latency and rate limits |
| `configs/pilot_zero_cost_matrix_20.yaml` | Mixed zero-cost matrix | potentially long; preliminary only |

### Provider/Paid Runs

Do not run these until leakage blockers, config approval, budget review, dry-run, and advisor signoff are complete.

| Command/config | Purpose | Cost/time expectation |
|---|---|---|
| `configs/provider_pilot_tiny_template.yaml` | Template for tiny provider pilot | Template only; do not run directly |
| Approved copy of provider pilot template | Tiny provider-backed pilot | Latest estimate: low $0.09, high $0.2436 for template assumptions |
| `configs/pilot_openai_20.yaml` | OpenAI pilot | Paid/provider, approval required |
| `configs/pilot_anthropic_20.yaml` | Anthropic pilot | Paid/provider, approval required |
| `configs/pilot_gemini_20.yaml` | Gemini pilot | Provider, approval required |
| `configs/pilot_openrouter_20.yaml` | OpenRouter pilot | Provider, approval required |
| `configs/pilot_multi_provider_20.yaml` | Multi-provider pilot | Paid/provider, approval required |
| `configs/commercial_api_main_500.yaml` | Main commercial run | Main scale, not ready |

## 14. Strict No-Run Validation Lane

Use this lane before merge, before provider prep, or when you need confidence without starting experiments:

```bash
python3 scripts/check_evidence_safety.py
python3 -m causal_agent_bench all-no-run-reports --output-dir /tmp/cab_no_run_reports
python3 -m pytest tests/test_leakage_repair_applier.py tests/test_leakage_suppressions.py tests/test_manual_repair_preview.py tests/test_static_leakage.py tests/test_leakage_repair_planner.py tests/test_evidence_dashboard.py tests/test_report_quality_check.py -q
```

Latest local result for the fixture-only safety lane:

```text
77 passed in 2.77s
```

Do not substitute a broad marker expression such as `pytest -m "not integration and not local_run"` for the strict lane unless the marker coverage has been separately audited.

## 15. Commands To Avoid Without Explicit Approval

Avoid these unless the project owner explicitly intends to start runs or provider calls:

- `python3 -m causal_agent_bench run --config ...` on provider configs.
- `python3 -m causal_agent_bench run --config configs/commercial_api_main_500.yaml`.
- `python3 -m causal_agent_bench run --config configs/pilot_multi_provider_20.yaml`.
- `python3 -m causal_agent_bench run --config configs/pilot_openai_20.yaml`.
- `python3 -m causal_agent_bench run --config configs/pilot_free_local_20.yaml` unless a long local run is intended.
- `make smoke` in strict no-run contexts.
- `make test` in strict no-run contexts.
- `run-llm-judge` before provider/model approval.
- `fill-paper-from-run` before verified eligible evidence.
- `update-claim-ledger --promote-to-supported` before strict run/artifact eligibility checks.
- Any command that uses API keys or could create paid provider traffic.

## 16. Output Artifacts From Runs

A normal run writes a timestamped directory under `results/`, usually with:

- copied `config.yaml`
- config hash
- metadata files such as `run_metadata.json` or `metadata.json`
- trajectories, often `trajectories.jsonl`
- scores, often `scores.jsonl` or `aggregate_scores.json`
- checkpoint/progress files
- errors if any
- generated reports
- optional paper assets
- optional `INCOMPLETE_RUN.json` if interrupted

Run outputs are evidence only if metadata, provider classification, completion state, sidecars, and claim/evidence guards all pass.

## 17. Current Evidence State

Latest no-run evidence summaries:

| Item | Current value |
|---|---:|
| Paper-eligible runs | 0 |
| Eligible paper assets | 0 |
| Claim count | 10 |
| Supported claims | 0 |
| C1-C8 | planned |
| C9 | engineering_only |
| C10 | planned |
| Claims promoted by dashboard | false |

Latest run-health report from `RUN_INDEX`:

| Classification | Count |
|---|---:|
| stub_engineering | 30 |
| mock_diagnostic | 2 |
| interrupted | 2 |
| complete_engineering_only | 2 |

Important stale-index warning: the evidence safety script live-scanned 60 indexed runs, but the generated run-health report based on `results/RUN_INDEX.jsonl` saw 36. Regenerate/index or fix report staleness before trusting final inventory counts.

## 18. Current Paper Asset State

Latest paper asset eligibility:

| Item | Count |
|---|---:|
| Total paper assets scanned | 74 |
| Eligible assets | 0 |
| Flagged assets | 74 |
| Engineering-only | 9 |
| Missing metadata | 43 |
| Placeholder | 21 |
| Unsafe for results section | 1 |

Interpretation: the repo has tables/figures/paper assets, but none are eligible for empirical claims.

## 19. Current Leakage And Dataset State

Latest static leakage summary:

| Item | Count |
|---|---:|
| Datasets scanned | 7 |
| Raw findings | 210217 |
| Issues after suppression/grouping | 209295 |
| Clusters | 345 |
| Active clusters | 345 |
| Blocker clusters | 6 |
| Warning clusters | 200 |
| Blocker symptoms | 187 |
| Warning symptoms | 188619 |
| Active suppressions | 0 |

Cluster classifications:

| Classification | Count |
|---|---:|
| answer_leakage | 6 |
| split_metadata_issue | 25 |
| same_family_protected_split_overlap | 103 |
| needs_manual_review | 200 |
| expected_subset_overlap | 4 |
| clean_intervention_pair_similarity | 7 |

Leakage repair plan:

| Item | Count |
|---|---:|
| Clusters | 345 |
| Must fix before provider pilot | 6 |
| Candidate auto patches | 0 |
| Manual review operations | 345 |
| Unsafe operations | 0 |

Interpretation: provider-pilot readiness is blocked until the 6 answer-leakage clusters are manually reviewed and repaired or explicitly accepted through the proper governance path.

## 20. Current Provider Pilot Gate

Latest provider pilot state:

| Item | Status |
|---|---|
| Template status | `template_safe_but_not_runnable` |
| Approved copy exists/approved | No |
| `allow_paid_calls` in template | false |
| Advisor approval | false |
| Budget approval | false |
| Dry-run readiness | blocked by dashboard |
| Live-run readiness | blocked |
| Leakage gate | blocked |
| Model placeholder | unresolved |
| Latest tiny-template cost estimate | low $0.09, high $0.2436 |

Required next step before provider work: review and repair leakage blockers, then create an approved copy of the template only after advisor approval.

## 21. Current Release And Report Quality State

Release readiness summary:

| Item | Status |
|---|---|
| Ready for empirical paper submission | false |
| Ready for provider pilot | false |
| Ready for public release | false |
| Ready for internal advisor review | true in release report, but dashboard says not ready because of evidence/leakage/readiness blockers |
| Git dirty | true |
| Paper-eligible runs | 0 |
| Eligible assets | 0 |

Release blocker report:

| Issue | Severity |
|---|---|
| 6 leakage clusters must be fixed before provider pilot | blocker |
| Benchmark quality not ready for release | blocker |
| 5806 dataset triage issues | warning |
| 97 config metadata lint issues | warning |
| 74 paper assets flagged | warning |
| No eligible paper assets | warning |
| No lockfile detected | warning |
| Unfrozen datasets exist | warning |

Report quality summary:

| Item | Count |
|---|---:|
| JSON reports | 45 |
| Markdown reports | 49 |
| Raw issues observed | 242788 |
| Clustered issues | 6747 |
| Blockers | 1 |
| Warnings | 11 |

The report-quality blocker is that `readiness_war_room/what_if_unlock_plan.json` is valid JSON but a top-level array, while the checker expects a top-level object and labels it not parseable.

## 22. Current Benchmark Quality And Tool State

Benchmark quality summary:

| Item | Count/Score |
|---|---:|
| Total tasks | 1273 |
| Total instances | 7589 |
| Clean/intervention pairs | 6316 |
| Blockers | 2 |
| Warnings | 5159 |
| Overall quality score | 95 |
| Provider pilot readiness score | 60 |
| Main benchmark readiness score | 60 |
| Release readiness score | 60 |

Benchmark quality blockers:

- `data/processed/main_200` is not main-candidate ready.
- `data/processed/main_v0_1_500` is not main-candidate ready.

Intervention isolation summary:

| Item | Count/Score |
|---|---:|
| Total pairs | 1250 |
| Blockers | 0 |
| Warnings | 125 |
| Isolation score | 82 |
| Likely isolated pairs | 1125 |
| Multi-factor pairs | 125 |

Tool schema validation:

| Item | Count |
|---|---:|
| Datasets scanned | 7 |
| Blockers | 67 |
| Warnings | 7589 |
| Root causes | 5835 |

Gold output validation:

| Item | Count |
|---|---:|
| Blockers | 0 |
| Warnings | 507 |

## 23. Paper And Claim Guardrails

The claim ledger contains C1-C10. Current statuses:

- C1-C8: planned.
- C9: engineering_only.
- C10: planned.

Unsupported empirical claims must not enter:

- abstract
- introduction
- results
- human validation
- ablations
- conclusion

Method-only sections are safe to work on:

- motivation
- benchmark design
- intervention taxonomy
- metrics definitions
- experimental setup as planned work
- limitations
- ethics
- reproducibility procedures

Claim promotion requires eligible real provider evidence, complete metadata, eligible paper assets, and the claim-specific promotion workflow. Manual force flags are not safe for paper claims.

## 24. Provider Pilot Workflow

Before any provider run:

1. Run strict no-run reports.
2. Review static leakage output.
3. Repair the 6 answer-leakage blocker clusters.
4. Rerun no-run reports.
5. Copy `configs/provider_pilot_tiny_template.yaml` to an approved config name.
6. Get written advisor approval for provider, model, budget, and scope.
7. Set API keys/model IDs through environment variables only.
8. Run `validate-config`, `dry-run`, and `estimate-cost` on the approved copy.
9. Confirm budget and trajectory caps.
10. Only then run the approved provider config.

After a provider run:

1. Confirm there is no `INCOMPLETE_RUN.json`.
2. Confirm run metadata is complete.
3. Confirm non-oracle, non-mock, non-stub provider-backed agent classification.
4. Confirm trajectories and scores exist.
5. Run `run-health`.
6. Export paper assets only through guarded commands.
7. Run `check_evidence_safety.py`.
8. Run claim-evidence reports.
9. Do not promote claims until artifacts and metadata are verified.
10. Do not promote C3/C10 without human validation evidence.

## 25. Testing And Quality Gates

Project tooling includes:

- pytest
- pytest-xdist by default via `addopts = "-n auto"`
- coverage with branch coverage and `fail_under = 73`
- ruff
- mypy over the full package with known override debt
- codespell
- optional pip-audit
- optional mutmut for mutation testing of metrics/hashing
- pre-commit helper scripts

Common commands:

```bash
make fast-check
make lint
make typecheck
make coverage
make precommit
python3 -m pytest tests/test_some_file.py -q
```

Be careful with broad tests in strict no-run contexts. Some tests may start local experiment execution.

## 26. Security, Privacy, And Cost Safety

Rules:

- Keep API keys in `.env` or environment variables only.
- Never commit API keys.
- Never put secrets in YAML configs.
- Provider runs must require explicit `allow_paid_calls: true`.
- Template configs should remain `allow_paid_calls: false`.
- Simulated tools are the default safe path.
- Local open-weight runs are not commercial-provider evidence.
- Free-tier or local runs are preliminary engineering evidence unless later validated under the evidence policy.
- Incomplete/interrupted runs cannot support paper claims.
- Mock/stub/oracle sanity runs cannot support C1-C8 or C10.

## 27. Important Existing Docs

Start here:

- `README.md`
- `docs/README.md`
- `docs/QUICKSTART.md`
- `docs/COMMAND_MAP.md`
- `docs/CLI_REFERENCE.md`
- `docs/REPO_MAP.md`
- `docs/NO_RUN_VALIDATION.md`
- `docs/RUN_LIMITS_AND_FAST_LOCAL_RUNS.md`
- `docs/PROVIDER_PILOT_READINESS_PACKET.md`
- `docs/POST_PROVIDER_PILOT_CHECKLIST.md`
- `docs/EVIDENCE_LEVEL_POLICY.md`
- `docs/DO_NOT_OVERCLAIM.md`
- `docs/DATASET_REPAIR_WORKFLOW.md`
- `docs/LEAKAGE_REPAIR_APPLY_GUIDE.md`
- `docs/REPRODUCIBILITY.md`
- `docs/SECURITY_AND_PRIVACY.md`
- `MASTER_STATUS.md`
- `PROJECT_STATUS.md`

## 28. Recommended Next Actions

Ranked by provider-pilot readiness, paper impact, safety risk, and difficulty:

1. Fix stale run inventory handling or regenerate and validate `results/RUN_INDEX.jsonl`.
2. Manually repair the 6 answer-leakage clusters.
3. Add or fix missing tool schema definitions referenced by datasets.
4. Fix the report-quality object/list mismatch for `what_if_unlock_plan.json`.
5. Cap or cluster large Markdown reports that dump raw issue detail.
6. Resolve main-candidate benchmark quality blockers for `main_200` and `main_v0_1_500`.
7. Review split metadata and same-family protected split overlap clusters.
8. Fix provider-looking configs that lack budget or trajectory caps.
9. Regenerate `all-no-run-reports` and rerun the fixture-only safety lane.
10. Prepare advisor review packet only after leakage/evidence/report blockers are clean.

## 29. Practical Operating Modes

Use these modes to choose the right command set:

| Mode | Use when | Commands |
|---|---|---|
| Static/no-run | You want safety/readiness without execution | `check_evidence_safety.py`, `all-no-run-reports`, named fixture pytest lane |
| Planning | You want to know what a run would do | `plan-run`, `dry-run`, `estimate-cost`, `validate-config` |
| Stub/mock engineering | You want runner/scoring smoke confidence | `run` on stub/mock micro configs |
| Local preliminary | You want local LLM behavior without paid API calls | zero-cost/local configs with strict limits |
| Provider pilot | You want real provider evidence | only after advisor approval and blocker cleanup |
| Paper/release | You want publication artifacts | only use guarded exports and claim checks |

## 30. Bottom Line

This repository is a serious benchmark scaffold with a lot of infrastructure already built. It can generate datasets, run agents, score trajectories, produce reports, and enforce evidence safety. The safe immediate work is static/no-run validation, dataset leakage repair, tool schema cleanup, and provider-pilot preparation.

It is not yet safe to run live provider pilots from the template, not safe to promote empirical claims, and not ready for an empirical paper or public release. The next real unlock is manual dataset repair, especially the 6 answer-leakage blocker clusters, followed by a fresh no-run audit.
