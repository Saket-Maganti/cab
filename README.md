# CausalAgentBench

**When Agent Success Is Not Agent Skill: A Causal Benchmark for Tool-Using LLM Agents**

[![CI](https://github.com/Saket-Maganti/causal-agent-bench/actions/workflows/ci.yml/badge.svg)](https://github.com/Saket-Maganti/causal-agent-bench/actions/workflows/ci.yml)
[![Python 3.11–3.13](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)](pyproject.toml)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Checked with mypy](https://img.shields.io/badge/mypy-checked-2a6db2.svg)](https://mypy-lang.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

<!-- Badge repo path assumes github.com/Saket-Maganti/causal-agent-bench; update if the remote differs. -->

> Current authoritative state: [CURRENT_PROJECT_STATE.md](CURRENT_PROJECT_STATE.md).
> Final pre-review hardening is complete; genuine human validation and live
> evidence are still required.

CausalAgentBench is a Python research package for studying tool-using language agents under controlled interventions. The motivation is that final task success can hide why an agent succeeded or failed: planning, tool selection, tool arguments, observation interpretation, memory use, contradiction handling, recovery, stopping behavior, and final answer quality are different skills. The benchmark pairs clean task instances with targeted intervention variants so those skills can be measured more explicitly.

This repository is an initial research scaffold and deterministic prototype. It is not a completed benchmark, and smoke/dev outputs are engineering checks rather than scientific results.

| | |
|---|---|
| **Status** | `CAB_FINAL_PRE_REVIEW_HARDENING_COMPLETE` · `COMPACT20_REVIEW_PACKET_EVIDENCE_VERIFIABLE` — [CURRENT_PROJECT_STATE.md](CURRENT_PROJECT_STATE.md) |
| **Health** | [PROJECT_HEALTH.md](PROJECT_HEALTH.md) |
| **Python** | 3.11+ · pinned runtime: `constraints.txt` (`make lock`) |
| **Final pre-review gate** | `cab final-pre-review check` (provider-free, no model runs) |
| **God-tier status** | `make god-tier-status` or `python3 scripts/god_tier_status.py` |
| **Paid calls** | Disabled by default (`allow_paid_calls: false`) |
| **Evidence** | [docs/EVIDENCE_LEVEL_POLICY.md](docs/EVIDENCE_LEVEL_POLICY.md) · [docs/DO_NOT_OVERCLAIM.md](docs/DO_NOT_OVERCLAIM.md) |
| **Safety reports** | `all-safety-reports` → [reports/INDEX.md](reports/INDEX.md) · full bundle: `all-no-run-reports` |
| **Project status** | `make status` → [PROJECT_STATUS.md](PROJECT_STATUS.md) |

## CAB Research OS

The Level-5 foundation adds a transactional experiment registry, governed
benchmark factory, resumable execution OS, content-addressed artifacts,
reliability laboratory, human-review service, protected-evaluator contracts,
public SDK/plugins, evidence graph, certification and an honest maturity gate.

```bash
cab env doctor
cab registry init
cab benchmark validate --spec examples/level5/public_fixture/authoring.yaml
cab run --dry-run
cab reproduce --workdir /tmp/cab_level5_reproduction
cab level5 check
```

See the [Research OS architecture](docs/level5/CAB_RESEARCH_OS_ARCHITECTURE.md),
[capability matrix](docs/level5/CAB_LEVEL5_CAPABILITY_MATRIX.md) and
[Level-5 quickstart](docs/level5/QUICKSTART.md). Fixture demonstrations are
engineering validation only. Genuine human review, live model evidence,
independent reproduction and external evaluator/community pilots remain
mandatory for `CAB_LEVEL5_COMPLETE`.

### Compact-20 reviewer-ready V2

The active review packet is `compact20-review-ready-v2`. Its unit of evaluation
is an explicit **pair**: a clean instance plus an intervention instance produced
by applying exactly one executable environment operator to it. Intervention
family is deconfounded from the required response type, the four anchors are
controlled repetitions of real objectives, abstention requires proved route
exhaustion, and no general-purpose artifact reader exists in the scientific
route. Stage-2 material is encrypted with a key that must live outside the
repository.

```bash
export CAB_STAGE2_KEY_PATH="$HOME/.cab/keys/stage2_review_ready_v2.key"
python3 scripts/cab_review_ready_v2.py validate-private-packet
python3 scripts/cab_review_ready_v2.py fixture-e2e
```

Every earlier Compact packet is retired and rejected in code at ingestion, C10,
slice lock and execution authorization. See the
[human review runbook](docs/HUMAN_REVIEW_READY_V2_RUNBOOK.md) and the
[V2 scientific design](docs/COMPACT20_V2_SCIENTIFIC_DESIGN.md).

Compact-20 is a pilot, not a confirmatory design. No genuine human review has
occurred, C10 is `C10_PENDING_GENUINE_REVIEW`, and model execution is blocked.

## Quick safe demo

No model runs — planning and audits only:

```bash
make fast-check
python3 -m causal_agent_bench plan-run --config configs/pilot_stub_micro_3.yaml
python3 -m causal_agent_bench audit-dataset --config configs/pilot_stub_micro_3.yaml
python3 scripts/generate_master_status.py
python3 scripts/check_submission_readiness.py
python3 -m causal_agent_bench all-safety-reports   # run health, paper assets, claims, TODOs, env
python3 scripts/god_tier_status.py                 # one-screen god-tier banner (no models)
python3 scripts/check_run_index.py                 # RUN_INDEX freshness (inventory only)
```

**Master status:** [MASTER_STATUS.md](MASTER_STATUS.md) · **Demo bundle:** [demo/ENGINEERING_DEMO_BUNDLE.md](demo/ENGINEERING_DEMO_BUNDLE.md) · **Next decision:** [NEXT_DECISION.md](NEXT_DECISION.md)

## Quickstart (reviewers)

See [docs/QUICKSTART.md](docs/QUICKSTART.md) and [artifact/README.md](artifact/README.md) for install → smoke → pilot-stub → table/figure reproduction. One-shot API-free path:

```bash
python3 scripts/reproduce_artifact.py --all-deterministic
```

## Security and privacy

- Copy [`.env.example`](.env.example) to `.env` (gitignored); never commit API keys.
- Default tools are **simulated** (email drafts only, booking stub, no live web). See [docs/SECURITY_AND_PRIVACY.md](docs/SECURITY_AND_PRIVACY.md).
- Run `make security-check` before release. Licenses: [LICENSE](LICENSE) (code), [DATA_LICENSE.md](DATA_LICENSE.md) (synthetic data), [CITATION.cff](CITATION.cff).

## Installation

Requires Python 3.11+.

```bash
cd causal-agent-bench
pip install -e ".[dev]"
```

If your shell's `python` points to a missing pyenv version, either install the local version or use `python3`:

```bash
pyenv install 3.11.9
pyenv local 3.11.9
# or
python3 -m pip install -e ".[dev]"
```

For source-only use without installation:

```bash
export PYTHONPATH=src
```

## Smoke Run

```bash
python -m causal_agent_bench --help
python -m causal_agent_bench validate-config --config configs/smoke.yaml
python -m causal_agent_bench validate data/sample/instances.jsonl --schema instances
python -m causal_agent_bench dry-run --config configs/smoke.yaml --output-dir results/dry_runs
python -m causal_agent_bench run --config configs/smoke.yaml
python -m causal_agent_bench doctor
```

The dry run writes `dry_run_report.json` and `dry_run_report.md` under `results/dry_runs/`.
The smoke run creates a timestamped directory such as `results/<timestamp>_smoke/`.

## Benchmark Generation

```bash
python -m causal_agent_bench generate --config configs/dev_20_tasks.yaml
python -m causal_agent_bench validate data/processed/dev_20/instances.jsonl --schema instances
python -m causal_agent_bench generate --config configs/generate_main_v0_1_500.yaml
python -m causal_agent_bench validate data/processed/main_v0_1_500/instances.jsonl --schema instances
```

The generator writes `base_tasks.jsonl`, `interventions.jsonl`, `instances.jsonl`, `generation_report.json`, and `quality_report.md`.
The `main_v0.1_500_candidate` config creates a deterministic synthetic candidate dataset with
500 base tasks and 2,500 intervention instances; it is still a candidate artifact until human audit
and real provider-backed experiments are complete.

## Experiment Run

```bash
python -m causal_agent_bench run --config configs/dev_20_run.yaml
```

This creates `results/<timestamp>_dev_20/` with config, config hash, metadata, trajectories, errors, scores, aggregate tables, and a score report.

## LLM Pilot Runs

LLM-backed agents are config-driven and optional. Default tests and smoke runs do not require API keys.

**Provider readiness gate (run before any paid pilot):**

```bash
python3 -m causal_agent_bench list-providers
python3 -m causal_agent_bench validate-config --config configs/pilot_multi_provider_20.yaml
python3 -m causal_agent_bench dry-run --config configs/pilot_multi_provider_20.yaml --output-dir results/dry_runs
python3 -m causal_agent_bench estimate-cost --config configs/pilot_multi_provider_20.yaml
python3 scripts/check_pilot_readiness.py --config configs/pilot_multi_provider_20.yaml
```

The readiness checker reports one of: `not_ready`, `dry_run_ready`, `cost_estimate_ready`, or `paid_pilot_ready`. It never prints API key values. Paid provider runs require explicit `allow_paid_calls: true` in the config **and** your review of `estimate-cost` output. Until provider-backed run artifacts exist under `results/`, do not treat outputs as scientific evidence or mark claim-ledger rows as supported.

### Provider and model environment variables

Copy [`.env.example`](.env.example) to `.env` (gitignored). Set keys and model IDs via environment variables only — never in YAML:

| Provider | API key env var(s) | Model ID env var |
|---|---|---|
| OpenAI | `OPENAI_API_KEY` | `OPENAI_MODEL_ID` |
| Anthropic | `ANTHROPIC_API_KEY` | `ANTHROPIC_MODEL_ID` |
| Gemini | `GOOGLE_API_KEY` or `GEMINI_API_KEY` | `GEMINI_MODEL_ID` |
| OpenRouter | `OPENROUTER_API_KEY` | `OPENROUTER_MODEL_ID` |
| OpenAI-compatible | `OPENAI_COMPATIBLE_API_KEY` | `OPENAI_COMPATIBLE_MODEL_ID` |
| Local open-weight | optional `LOCAL_OPENAI_API_KEY` | `LOCAL_OPENAI_MODEL_ID` |

Pilot configs reference model IDs as `${OPENAI_MODEL_ID:-}` style env-var placeholders. Prompt template filenames and versions are logged via `agent_runs[].extra.prompt_file` and `extra.prompt_version`; trajectory metadata records prompt hashes automatically.

```bash
python3 -m causal_agent_bench list-providers
python3 -m causal_agent_bench validate-config --config configs/pilot_multi_provider_20.yaml
python3 -m causal_agent_bench dry-run --config configs/pilot_multi_provider_20.yaml --output-dir results/dry_runs
python3 -m causal_agent_bench estimate-cost --config configs/pilot_multi_provider_20.yaml
OPENAI_MODEL_ID=<MODEL_ID> python -m causal_agent_bench run --config configs/pilot_openai_20.yaml
```

Provider API keys are read from environment variables such as `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `GEMINI_API_KEY`, and `OPENROUTER_API_KEY`. The runner logs whether providers are configured, but never prints or saves key values.

Provider pilot examples currently include:

- `configs/pilot_openai_20.yaml`
- `configs/pilot_anthropic_20.yaml`
- `configs/pilot_gemini_20.yaml`
- `configs/pilot_openrouter_20.yaml`
- `configs/pilot_multi_provider_20.yaml`
- `configs/pilot_local_openai_compatible_20.yaml` and `configs/main_local_openai_compatible_100.yaml` for open-weight/local OpenAI-compatible servers (see [docs/OPEN_WEIGHT_LOCAL_MODELS.md](docs/OPEN_WEIGHT_LOCAL_MODELS.md))
- `configs/commercial_api_pilot_small_20.yaml`, `configs/commercial_api_pilot_medium_100.yaml`, `configs/commercial_api_main_500.yaml`, and `configs/commercial_api_ablation_20.yaml` for paid API runs (see [docs/COMMERCIAL_API_RUNS.md](docs/COMMERCIAL_API_RUNS.md); requires `allow_paid_calls: true`)
- `configs/generate_mini_study_template_40.yaml` and `configs/generate_mini_study_naturalistic_40.yaml` for the synthetic-to-realistic external-validity mini-study (see [docs/MINI_STUDY_EXTERNAL_VALIDITY.md](docs/MINI_STUDY_EXTERNAL_VALIDITY.md))
- `configs/generate_web_shadow_25.yaml` for the optional static web snapshot study without live browsing (see [docs/WEB_SHADOW_STUDY.md](docs/WEB_SHADOW_STUDY.md))
- `configs/main_500_multi_provider.yaml` as a future larger-run template; generate or freeze that dataset path before running it.

Supported provider names are `openai`, `anthropic`, `gemini`, `openrouter`, `openai_compatible`, `local_openai`, and `local_stub`. For OpenAI-compatible hosted endpoints, set `base_url` in an `agent_runs` entry or `OPENAI_COMPATIBLE_BASE_URL`; for local open-weight servers, use `provider: local_openai` with `LOCAL_OPENAI_BASE_URL` if the server is not at `http://localhost:8000/v1/chat/completions`. Local runs are labeled `local_open_weight_unvalidated` in metadata and paper tables and must not be merged with commercial API results.

Provider-backed runs log prompt hashes, response hashes, tool-state hashes, latency, token usage, retry counts, model-call counts, tool-call counts, estimated cost when pricing is configured, and provider error classes. Add `cache_dir` to an agent run to enable response caching keyed by provider, model, prompt hash, tool state hash, model config hash, and seed. The cache stores responses and hashes only; it never stores API keys. Cost models, budget caps, and cost-normalized tables are documented in [docs/COST_LATENCY.md](docs/COST_LATENCY.md).

## Zero-cost experiments

Run preliminary experiments **without monetary spend** using local models or free-tier API routes. These configs set `cost_mode: zero_cost`, `allow_paid_calls: false`, `budget.max_total_usd: 0`, and `scientific_evidence_level: preliminary_or_engineering`. Results are labeled preliminary in run metadata and **must not** support main paper claims (C1–C8, C10).

| Config | Path | Providers |
|--------|------|-----------|
| Local Ollama / llama.cpp / vLLM | `configs/pilot_free_local_20.yaml` | `local_openai` |
| OpenRouter free models | `configs/pilot_openrouter_free_20.yaml` | `openrouter` (free-tier) |
| Gemini free tier | `configs/pilot_gemini_free_20.yaml` | `gemini` (free-tier) |
| Mixed zero-cost matrix | `configs/pilot_zero_cost_matrix_20.yaml` | local + gemini + openrouter |

Preflight (no paid calls):

```bash
python3 scripts/check_zero_cost_readiness.py --config configs/pilot_zero_cost_matrix_20.yaml
python3 -m causal_agent_bench dry-run --config configs/pilot_zero_cost_matrix_20.yaml --output-dir results/dry_runs
python3 -m causal_agent_bench estimate-cost --config configs/pilot_zero_cost_matrix_20.yaml
```

**Local Ollama path** — start Ollama, pull a model, then:

```bash
ollama serve
export LOCAL_OPENAI_BASE_URL=http://localhost:11434/v1
export LOCAL_OPENAI_MODEL_ID=qwen2.5:7b
python3 -m causal_agent_bench run --config configs/pilot_free_local_20.yaml
```

**OpenRouter free-model path** — uses zero pricing + `extra.free_tier: true`; requires `OPENROUTER_API_KEY` but no spend on free routes:

```bash
export OPENROUTER_API_KEY=...
export OPENROUTER_MODEL_ID=google/gemma-2-9b-it:free
python3 -m causal_agent_bench run --config configs/pilot_openrouter_free_20.yaml
```

**Gemini free-tier path** — requires `GOOGLE_API_KEY` or `GEMINI_API_KEY`; agent runs use zero pricing when `free_tier: true`:

```bash
export GEMINI_API_KEY=...
export GEMINI_MODEL_ID=gemini-2.0-flash
python3 -m causal_agent_bench run --config configs/pilot_gemini_free_20.yaml
```

Limitations: zero-cost runs are **preliminary engineering/pilot observations** only — smaller models, free-tier rate limits, no human validation, and no NeurIPS-scale statistical power. To upgrade to a paid provider pilot later, use `configs/pilot_multi_provider_20.yaml` with explicit cost approval and `allow_paid_calls: true` (see [runs/RUNBOOK_TINY_PROVIDER_PILOT.md](runs/RUNBOOK_TINY_PROVIDER_PILOT.md)).

### Fast zero-cost development (no long runs)

Prefer **stub/mock micro configs** (seconds) over full local pilots (hours):

| Config | Instances | Notes |
|--------|-----------|-------|
| `configs/pilot_stub_micro_3.yaml` | 3 | `local_stub`, fastest |
| `configs/pilot_mock_agents_10.yaml` | 10 | deterministic mock agent |
| `configs/pilot_free_local_micro_3.yaml` | 3 | Ollama, bounded limits |

```bash
make fast-check
python3 -m causal_agent_bench plan-run --config configs/pilot_stub_micro_3.yaml
python3 -m causal_agent_bench run-status --latest
python3 -m causal_agent_bench mark-interrupted --run-dir results/<run_dir> --reason "stopped"
python3 -m causal_agent_bench run --config configs/pilot_stub_micro_3.yaml   # stub only
```

See [docs/RUN_LIMITS_AND_FAST_LOCAL_RUNS.md](docs/RUN_LIMITS_AND_FAST_LOCAL_RUNS.md), [docs/INTERRUPTED_AND_MICRO_RUNS.md](docs/INTERRUPTED_AND_MICRO_RUNS.md), [runs/ZERO_COST_LOCAL_PILOT_RESUME.md](runs/ZERO_COST_LOCAL_PILOT_RESUME.md).

### Reports, comparison, and audits (no model runs required)

```bash
python3 -m causal_agent_bench generate-report --run-dir results/<run_dir>
python3 -m causal_agent_bench generate-report --latest
python3 -m causal_agent_bench compare-runs --run-dir results/A --run-dir results/B
python3 -m causal_agent_bench compare-runs --latest
python3 -m causal_agent_bench failure-gallery --run-dir results/<run_dir>
python3 -m causal_agent_bench failure-gallery --latest
python3 -m causal_agent_bench audit-dataset --dataset data/processed/pilot_v0_1/pilot_20_instances.jsonl
python3 -m causal_agent_bench audit-dataset --config configs/pilot_stub_micro_3.yaml
python3 scripts/validate_paper_assets.py --mode draft
python3 scripts/check_submission_readiness.py
make fast-check
```

**Evidence levels:** dry-run/stub/mock/interrupted → engineering or preliminary only. Completed local Ollama → preliminary only. Provider pilots → review required before claim updates. **No final C1–C8/C10 claims yet.**

### Benchmark quality & reviewer package (Phase 3)

| Doc | Purpose |
|---|---|
| [docs/BENCHMARK_TAXONOMY.md](docs/BENCHMARK_TAXONOMY.md) | Skills, domains, intervention families |
| [docs/FAILURE_TAXONOMY.md](docs/FAILURE_TAXONOMY.md) | Failure IDs and annotation guidance |
| [docs/EVIDENCE_LEVEL_POLICY.md](docs/EVIDENCE_LEVEL_POLICY.md) | Allowed claims per evidence level |
| [paper/REVIEWER_PACKET.md](paper/REVIEWER_PACKET.md) | Reviewer/co-author FAQ (no results) |
| [scripts/audit_intervention_isolation.py](scripts/audit_intervention_isolation.py) | Single-factor isolation audit |
| [experiments/MAIN_EXPERIMENT_GATE.md](experiments/MAIN_EXPERIMENT_GATE.md) | GO/NO-GO before main run |
| [docs/NEURIPS_ARTIFACT_CHECKLIST.md](docs/NEURIPS_ARTIFACT_CHECKLIST.md) | Artifact badge checklist |

Mock diagnostic (seconds, no API; **engineering_only / not_real_llm_behavior**):

```bash
python3 -m causal_agent_bench plan-run --config configs/pilot_mock_diagnostic_micro.yaml
python3 -m causal_agent_bench run --config configs/pilot_mock_diagnostic_micro.yaml
python3 scripts/audit_intervention_isolation.py --dataset data/processed/pilot_v0_1/instances.jsonl
```

### Advisor handoff & paper package (Phase 5)

| Resource | Purpose |
|---|---|
| [handoff/ADVISOR_HANDOFF_PACKET.md](handoff/ADVISOR_HANDOFF_PACKET.md) | Professor/co-author briefing |
| [handoff/ONE_PAGE_PROJECT_BRIEF.md](handoff/ONE_PAGE_PROJECT_BRIEF.md) | One-page summary |
| [paper/EVIDENCE_GAP_MAP.md](paper/EVIDENCE_GAP_MAP.md) | C1–C10 evidence requirements |
| [paper/CONTRIBUTION_MAP.md](paper/CONTRIBUTION_MAP.md) | Contribution ↔ evidence status |
| [reviews/MOCK_REVIEW_SUMMARY.md](reviews/MOCK_REVIEW_SUMMARY.md) | Simulated review synthesis |
| [paper/PAPER_STATUS.md](paper/PAPER_STATUS.md) | Paper status and blockers |
| [paper/latexpaper/](paper/latexpaper/) | LaTeX source (upload to Overleaf) |

```bash
python3 scripts/lint_paper_claims.py --mode draft
```

### Project operations (Phase 4–7)

| Resource | Purpose |
|---|---|
| [docs/CLI_REFERENCE.md](docs/CLI_REFERENCE.md) | Safe vs unsafe commands |
| [PROJECT_STATUS.md](PROJECT_STATUS.md) | Current snapshot (`make status`) |
| [handoff/PROFESSOR_READY_CHECKLIST.md](handoff/PROFESSOR_READY_CHECKLIST.md) | Advisor meeting gate |
| [experiments/COMMAND_PLANS.md](experiments/COMMAND_PLANS.md) | Safe command blocks per experiment stage |
| [release/release_manifest.md](release/release_manifest.md) | Release inventory + hashes |
| [docs/TECH_DEBT_REGISTER.md](docs/TECH_DEBT_REGISTER.md) | Tech debt tracker |

**Safe Makefile targets:**

```bash
make fast-check      # ~40s, no model runs
make doctor          # repo health
make plan-micro      # plan stub micro config
make audit-repo      # link/CLI consistency audit
make audit-configs   # YAML config audit
make check-readiness # submission gate
make status          # PROJECT_STATUS.md
make master-status   # MASTER_STATUS.md
make final-audit     # pre-experiment freeze audit
make precommit       # fast local gate
```

LLM agents must return one canonical JSON action: `tool_call`, `final_answer`, or `clarification`. The parser logs raw model output and parsed action records in each trajectory; see [docs/TOOL_CALL_PROTOCOL.md](docs/TOOL_CALL_PROTOCOL.md).

## Pilot Experiment Status

Current local pilot status is engineering-only. The repository can generate `pilot_v0.1`, run a 20-base-task stub/deterministic pilot, score it, and export analysis assets. No real provider-backed LLM pilot has been run unless a local `results/<run_dir>/run_metadata.json` records configured providers and model IDs.

Reproduce the local stub pilot:

```bash
python -m causal_agent_bench generate --config configs/generate_pilot_v0_1.yaml
python -m causal_agent_bench audit-interventions --benchmark-dir data/processed/pilot_v0_1
python -m causal_agent_bench dry-run --config configs/pilot_20_multi_agent.yaml --output-dir results/dry_runs
python -m causal_agent_bench run --config configs/pilot_20_multi_agent.yaml
python -m causal_agent_bench summarize-run --run-dir results/<timestamp>_pilot_20_multi_agent_stub
python -m causal_agent_bench analyze --run-dir results/<timestamp>_pilot_20_multi_agent_stub
python -m causal_agent_bench export-paper-assets --run-dir results/<timestamp>_pilot_20_multi_agent_stub
```

Run a real 20-task provider pilot after setting keys and model IDs:

```bash
python -m causal_agent_bench list-providers
python -m causal_agent_bench validate-config --config configs/pilot_multi_provider_20.yaml
python -m causal_agent_bench dry-run --config configs/pilot_multi_provider_20.yaml --output-dir results/dry_runs
python -m causal_agent_bench estimate-cost --config configs/pilot_multi_provider_20.yaml
python -m causal_agent_bench run --config configs/pilot_multi_provider_20.yaml
```

For a 100-base-task pilot, inspect cost and budget first:

```bash
python -m causal_agent_bench validate-config --config configs/pilot_100_multi_agent.yaml
python -m causal_agent_bench dry-run --config configs/pilot_100_multi_agent.yaml --output-dir results/dry_runs
python -m causal_agent_bench estimate-cost --config configs/pilot_100_multi_agent.yaml
```

## Scoring

Runs score automatically by default. To re-score:

```bash
python -m causal_agent_bench score --run-dir results/<timestamp>_dev_20
```

## Analysis

```bash
python -m causal_agent_bench analyze --run-dir results/<timestamp>_dev_20
python -m causal_agent_bench export-paper-assets --run-dir results/<timestamp>_dev_20
python -m causal_agent_bench export-ablation-table --run-dir results/<timestamp>_dev_20
python scripts/check_paper_placeholders.py --mode draft
python scripts/check_claim_ledger.py
```

Analysis exports paper-oriented figures, tables, statistical summaries, and error cases.
Exported figures and tables include run directory, config hash, seed, dataset version, model IDs, scorer version, git commit, and timestamp metadata when available. Run-local exports also write `paper_assets/asset_metadata.json`. Prompt/scaffold ablations are documented in [docs/ABLATIONS.md](docs/ABLATIONS.md); local-stub ablation configs and zero-cost local-stub cost tables are engineering checks only.

## Phase-2 Utility Commands

```bash
python -m causal_agent_bench validate-config --config configs/smoke.yaml
python -m causal_agent_bench validate results/<run_dir>/trajectories.jsonl --schema trajectories_v2
python -m causal_agent_bench dry-run --config configs/pilot_20_multi_agent.yaml --output-dir results/dry_runs
python -m causal_agent_bench audit-interventions --benchmark-dir data/processed/pilot_v0_1
python -m causal_agent_bench audit-contamination --benchmark-dir data/frozen/pilot_v0.1
python -m causal_agent_bench freeze-dataset --source-dir data/processed/pilot_v0_1 --version pilot_v0.1
python -m causal_agent_bench export-human-validation --run-dir results/<run_dir> --output-dir results/<run_dir>/human_validation
python -m causal_agent_bench summarize-human-validation --annotations results/<run_dir>/human_validation/annotation_export.csv
python -m causal_agent_bench run-llm-judge --run-dir results/<run_dir> --config configs/judge_fake_smoke.yaml
python -m causal_agent_bench calibrate-llm-judge --judge-labels results/<run_dir>/llm_judge/judge_labels.jsonl --human-annotations results/<run_dir>/human_validation/annotation_export.csv
python -m causal_agent_bench export-ablation-table --run-dir results/<run_dir>
python -m causal_agent_bench export-leaderboard --run-dir results/<run_dir>
python -m causal_agent_bench export-leaderboard --run-dir results/<run_dir> --eval-split test --splits-path data/frozen/pilot_v0.1/splits.json
python -m causal_agent_bench export-failure-gallery
python -m causal_agent_bench export-failure-gallery --run-dir results/<run_dir>
python -m causal_agent_bench summarize-run --run-dir results/<run_dir>
python -m causal_agent_bench update-claim-ledger --ledger docs/claim_ledger.json
python -m causal_agent_bench update-claim-ledger --run-dir results/<timestamp>_<run_name>
python scripts/check_claim_ledger.py
python scripts/check_paper_claims.py --list-ids
```

`audit-interventions` writes `intervention_audit_report.json` and `intervention_audit_report.md`. These reports include per-instance intervention validity scores (`pass`, `warning`, `fail`) and checks for goal preservation, required-tool stability, ground-truth/scoring alignment, patch isolation, expected behavior metadata, and family-specific severity ranges. See [docs/INTERVENTION_AUDIT.md](docs/INTERVENTION_AUDIT.md).

`freeze-dataset` validates schemas, reruns quality filters, writes disjoint release splits, checks leakage, computes a deterministic dataset hash, and emits `freeze_manifest.json` plus `benchmark_card_snapshot.md`. See [docs/DATASET_FREEZE.md](docs/DATASET_FREEZE.md).

`export-leaderboard` writes versioned JSON/CSV/Markdown leaderboard exports with oracle agents excluded, split-aware metrics, provenance fields, and contamination warnings. See [docs/LEADERBOARD_PROTOCOL.md](docs/LEADERBOARD_PROTOCOL.md) and [docs/SPLIT_PROTOCOL.md](docs/SPLIT_PROTOCOL.md).

`audit-contamination` fingerprints task templates, checks hidden-split canaries, flags near-duplicate instructions across splits, and scans agent-visible prompts for hidden ground-truth or intervention-metadata leakage. See [docs/MODEL_CONTAMINATION.md](docs/MODEL_CONTAMINATION.md) and [docs/PUBLIC_VS_HIDDEN_SPLITS.md](docs/PUBLIC_VS_HIDDEN_SPLITS.md).

`export-failure-gallery` writes [docs/FAILURE_GALLERY.md](docs/FAILURE_GALLERY.md) and paper-ready shortened examples under `paper/latexpaper/generated/`. Pass `--run-dir` to mine from scored trajectories; without a run dir, it emits illustrative scaffold panels only (not scientific evidence).

`export-human-validation` samples scored trajectories across domains, difficulties, intervention families, agents, and outcomes, then writes CSV/JSONL annotation packets plus an optional static HTML aid. `summarize-human-validation` computes agreement, adjudication summaries, disagreement examples, and Table 5 artifacts. See [docs/HUMAN_VALIDATION_PROTOCOL.md](docs/HUMAN_VALIDATION_PROTOCOL.md), [docs/HUMAN_VALIDATION_GUIDELINES.md](docs/HUMAN_VALIDATION_GUIDELINES.md), [docs/HUMAN_VALIDATION_FORM_SCHEMA.md](docs/HUMAN_VALIDATION_FORM_SCHEMA.md), and [docs/HUMAN_VALIDATION_PILOT_PLAN.md](docs/HUMAN_VALIDATION_PILOT_PLAN.md).

`run-llm-judge` writes optional judge labels to separate artifacts and never overwrites deterministic scores or human labels by default. `calibrate-llm-judge` compares judge labels against completed human annotations before any paper use. See [docs/LLM_JUDGE_PROTOCOL.md](docs/LLM_JUDGE_PROTOCOL.md) and [docs/LLM_JUDGE_RISKS.md](docs/LLM_JUDGE_RISKS.md).

`freeze-dataset` creates a reproducibility bundle; it does not turn a dataset into final scientific evidence. `update-claim-ledger` should be used conservatively and refuses unsupported moves to `supported`.

Trajectory logs use a v2-compatible schema with raw model output, parsed actions, tool calls,
observations, parser status, recovery/contradiction/memory markers, and cost metadata. See
`docs/TRAJECTORY_SCHEMA_V2.md` for field definitions and the migration path for older logs.

## Repository Structure

```text
src/causal_agent_bench/   Python package
tests/                    Pytest suite
configs/                  YAML configs
data/raw/                 Raw or source data placeholders
data/processed/           Generated benchmark JSONL
data/sample/              Small sample task files and mock data
benchmark_specs/          Benchmark version specs
docs/                     Benchmark cards, metrics, interventions, reproducibility, ethics
paper/                    Paper scaffold and LaTeX source
reviews/                  Internal review and fix logs
results/                  Local run outputs, ignored except .gitkeep
figures/                  Generated paper figure templates
tables/                   Generated paper table templates
```

## Release package (`0.1.0-rc1`)

This repository ships a **research-scaffold release** with cards, a manifest, and a preflight script. It is not a NeurIPS camera-ready benchmark drop.

| Artifact | Path |
|----------|------|
| Release manifest | [release/release_manifest.json](release/release_manifest.json) |
| Benchmark card | [docs/BENCHMARK_CARD.md](docs/BENCHMARK_CARD.md) |
| Dataset card | [docs/DATASET_CARD.md](docs/DATASET_CARD.md) |
| ACRS metric card | [docs/METRIC_CARD_ACRS.md](docs/METRIC_CARD_ACRS.md) |
| Intervention card | [docs/INTERVENTION_CARD.md](docs/INTERVENTION_CARD.md) |
| Reproducibility | [docs/REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md) |
| Ethics and limitations | [docs/ETHICS_AND_LIMITATIONS.md](docs/ETHICS_AND_LIMITATIONS.md) |
| Default frozen pilot | [data/frozen/pilot_v0.1/freeze_manifest.json](data/frozen/pilot_v0.1/freeze_manifest.json) |

```bash
make release-check
# optional: pin bundle hash after intentional manifest changes
python3 scripts/release_check.py --write-bundle-hash
```

**License:** MIT ([LICENSE](LICENSE)).
**Validation:** automated schema/quality/leakage checks pass on the frozen pilot; human validation and validated LLM runs are **not complete**. Do not cite stub/smoke runs as scientific evidence (see [docs/CLAIM_LEDGER.md](docs/CLAIM_LEDGER.md)).

**Paper results:** after a verified run exists, use [docs/PAPER_RESULTS_FILL.md](docs/PAPER_RESULTS_FILL.md) and `fill-paper-from-run` (or `make paper-fill RUN_DIR=...`).

**Reviewer proofing:** NeurIPS ED-track attack matrix and submission fix list in [reviews/reviewer_attack_response_matrix.md](reviews/reviewer_attack_response_matrix.md) (index: [docs/REVIEWER_PROOFING.md](docs/REVIEWER_PROOFING.md)).

**Camera-ready precheck:** [docs/submission_checklist.md](docs/submission_checklist.md) · `make submission-precheck` (draft) · `make submission-check` (strict) · `make release-dry-run`

## Current Status

Implemented:

- Pydantic schemas and validation utilities.
- Deterministic synthetic task/intervention generation.
- Deterministic simulated tool environment.
- Baseline deterministic agents and LLM adapter interfaces.
- Metrics, scoring, experiment runner, resume checks, and analysis assets.
- Human-validation export and agreement-report tooling.
- Benchmark card, dataset card, metric/intervention cards, release manifest, `make release-check`, claim ledger, reproducibility docs, and paper scaffold.

Not yet complete:

- Real LLM-backed agent runs.
- Completed human validation annotations and adjudication.
- Full related-work review for all recent agent benchmarks.
- Final NeurIPS-scale experiments.

## Citation

Citation metadata is not final. Use this placeholder until a release DOI or paper exists:

```bibtex
@misc{causalagentbench2027,
  title = {When Agent Success Is Not Agent Skill: A Causal Benchmark for Tool-Using LLM Agents},
  author = {CausalAgentBench Contributors},
  year = {2027},
  note = {Research scaffold; citation metadata to be updated before publication}
}
```

## Limitations

- Default tasks are synthetic and template-generated.
- Default scoring is deterministic and heuristic.
- Oracle baselines are sanity checks, not realistic agents.
- Smoke/dev runs should not be cited as scientific evidence.
- Controlled interventions require human or expert audit before strong causal claims.

The claim ledger in [docs/CLAIM_LEDGER.md](docs/CLAIM_LEDGER.md) is the source of truth for which claims are planned, engineering-only, supported, or weakened.
