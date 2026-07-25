# CLI Reference

Safe vs unsafe command taxonomy for CausalAgentBench. **Default: no paid API calls.**

Run `python3 -m causal_agent_bench --help` for the full list.

---

## Setup / checks

| Command | Purpose | Safe? | Calls models? | Costs money? | Example |
|---|---|---|---|---|---|
| `doctor` | Repository health checks | Yes | No | No | `python3 -m causal_agent_bench doctor` |
| `list-providers` | Show provider env status | Yes | No | No | `python3 -m causal_agent_bench list-providers` |
| `capture-env` | Write environment report | Yes | No | No | `python3 -m causal_agent_bench capture-env` |
| `validate` | Validate JSONL schema | Yes | No | No | `python3 -m causal_agent_bench validate data/sample/instances.jsonl --schema instances` |

## Config / dataset validation

| Command | Purpose | Safe? | Calls models? | Costs money? | Example |
|---|---|---|---|---|---|
| `validate-config` | Validate YAML config | Yes | No | No | `python3 -m causal_agent_bench validate-config --config configs/pilot_stub_micro_3.yaml` |
| `dry-run` | Simulate config locally | Yes | No | No | `python3 -m causal_agent_bench dry-run --config configs/smoke.yaml` |
| `audit-dataset` | Dataset quality audit | Yes | No | No | `python3 -m causal_agent_bench audit-dataset --config configs/pilot_stub_micro_3.yaml` |
| `audit-interventions` | Intervention quality audit | Yes | No | No | `python3 -m causal_agent_bench audit-interventions --benchmark-dir data/frozen/pilot_v0.1` |
| `audit-contamination` | Contamination/canary audit | Yes | No | No | `python3 -m causal_agent_bench audit-contamination --benchmark-dir data/frozen/pilot_v0.1` |
| `freeze-dataset` | Copy dataset to frozen dir | Yes | No | No | `python3 -m causal_agent_bench freeze-dataset --source-dir data/processed/pilot_v0_1 --version pilot_v0.1` |

## Planning

| Command | Purpose | Safe? | Calls models? | Costs money? | Example |
|---|---|---|---|---|---|
| `plan-run` | Estimate trajectories/cost | Yes | No | No | `python3 -m causal_agent_bench plan-run --config configs/pilot_stub_micro_3.yaml` |
| `estimate-cost` | Budget estimate JSON | Yes | No | No | `python3 -m causal_agent_bench estimate-cost --config configs/pilot_multi_provider_20.yaml` |
| `batch-plan` | Shard experiment plan | Yes | No | No | `python3 -m causal_agent_bench batch-plan --config configs/pilot_stub_micro_3.yaml --shard-by instance --shard-count 2` |
| `command-plan` | Print safe command blocks | Yes | No | No | `python3 -m causal_agent_bench command-plan --experiment micro_stub` |

## Running

| Command | Purpose | Safe? | Calls models? | Costs money? | Example |
|---|---|---|---|---|---|
| `run` | Execute experiment | **Conditional** | Often | Maybe | Stub only: `run --config configs/pilot_stub_micro_3.yaml` |
| `generate` | Generate benchmark data | Yes | No | No | `python3 -m causal_agent_bench generate --config configs/generate_pilot_v0_1.yaml` |
| `ablation-matrix` | Plan/execute ablation grid | Plan: Yes | If `--execute` | If paid config | Plan-only default |

**Unsafe without approval:** `run` with OpenAI/Anthropic/OpenRouter/Gemini/Ollama configs.

## Run management

| Command | Purpose | Safe? | Calls models? | Costs money? | Example |
|---|---|---|---|---|---|
| `run-status` | Inspect run progress | Yes | No | No | `python3 -m causal_agent_bench run-status --latest` |
| `monitor` | Watch run progress | Yes | No | No | `python3 -m causal_agent_bench monitor --latest` |
| `mark-interrupted` | Label incomplete run | Yes | No | No | `python3 -m causal_agent_bench mark-interrupted --run-dir results/<dir>` |
| `index-runs` | Build results index | Yes | No | No | `python3 -m causal_agent_bench index-runs` |
| `summarize-run` | Run directory summary | Yes | No | No | `python3 -m causal_agent_bench summarize-run --run-dir results/<dir>` |
| `compare-runs` | Compare two runs | Yes | No | No | `python3 -m causal_agent_bench compare-runs --latest` |
| `failure-report` | Error/missing pair report | Yes | No | No | `python3 -m causal_agent_bench failure-report --run-dir results/<dir>` |

## Scoring / analysis

| Command | Purpose | Safe? | Calls models? | Costs money? | Example |
|---|---|---|---|---|---|
| `score` | Score trajectories | Yes* | No | No | `python3 -m causal_agent_bench score --run-dir results/<dir>` |
| `analyze` | Analysis report | Yes* | No | No | `python3 -m causal_agent_bench analyze --run-dir results/<dir>` |
| `mine-errors` | Failure taxonomy gallery | Yes* | No | No | `python3 -m causal_agent_bench mine-errors --run-dir results/<dir>` |

\*Do not treat incomplete/mock/stub runs as scientific evidence. Use `--allow-incomplete` only for engineering.

## Reports

| Command | Purpose | Safe? | Calls models? | Costs money? | Example |
|---|---|---|---|---|---|
| `generate-report` | HTML/MD run report | Yes | No | No | `python3 -m causal_agent_bench generate-report --latest` |
| `failure-gallery` | Failure gallery MD/JSON | Yes | No | No | `python3 -m causal_agent_bench failure-gallery --latest` |
| `export-failure-gallery` | Doc-level failure gallery | Yes | No | No | `python3 -m causal_agent_bench export-failure-gallery` |

## Audits (scripts)

| Script | Purpose | Safe? |
|---|---|---|
| `scripts/audit_repo_consistency.py` | Link/CLI/claim consistency | Yes |
| `scripts/audit_configs.py` | YAML config audit | Yes |
| `scripts/check_evidence_safety.py` | Evidence overclaim guard | Yes |
| `scripts/check_claim_ledger.py` | Claim ledger rules | Yes |
| `scripts/check_paper_section_contract.py` | Paper section-to-claim guard | Yes |
| `scripts/check_submission_readiness.py` | Submission gate | Yes |

## Paper / release checks

| Command / script | Purpose | Safe? | Example |
|---|---|---|---|
| `export-paper-assets` | Export tables/figures | Yes* | Engineering runs need `--allow-engineering-only` |
| `fill-paper-from-run` | Fill paper fragments | Yes* | Verified pilot only |
| `update-claim-ledger` | Update claim links | Yes | `python3 -m causal_agent_bench update-claim-ledger --claim-id C1 --status planned` |
| `build-release-manifest` | Release manifest | Yes | `python3 -m causal_agent_bench build-release-manifest` |
| `plan-repro-bundle` | Repro bundle plan | Yes | `python3 -m causal_agent_bench plan-repro-bundle` |
| `scripts/validate_paper_assets.py` | Paper asset validator | Yes | `--mode draft` |
| `scripts/lint_paper_claims.py` | Claim wording linter | Yes | `--mode draft` |
| `scripts/check_paper_section_contract.py` | Section evidence contract | Yes | `--mode draft` |

## Human validation

| Command | Purpose | Safe? | Example |
|---|---|---|---|
| `export-human-validation` | Sample annotation packet | Yes | `--run-dir results/<verified_pilot>` |
| `summarize-human-validation` | Agreement summary | Yes | `--annotations path/to.csv` |
| `run-llm-judge` | Optional judge labels | **Conditional** | May cost if paid judge config |
| `calibrate-llm-judge` | Judge vs human calibration | Yes | Requires human annotations |

---

## Makefile shortcuts (safe)

```bash
make fast-check      # ~40s, no model runs
make doctor          # repo health
make plan-micro      # plan stub micro config
make audit-repo      # link/CLI consistency
make audit-configs   # YAML audit
make check-readiness # submission gate
make check-claims    # claim ledger
make check-paper     # draft paper checks
make index-runs      # refresh results index
```

See [EVIDENCE_LEVEL_POLICY.md](EVIDENCE_LEVEL_POLICY.md) and [ONBOARDING.md](ONBOARDING.md).
