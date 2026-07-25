# Repository Audit and Upgrade Map

Date: 2026-05-12

Scope: current working tree of `causal-agent-bench`, including uncommitted Phase-2 work. This audit does not treat deterministic smoke, dev, or local-stub runs as scientific evidence.

## Current Architecture

- `src/causal_agent_bench/schemas.py`: Pydantic schemas for tool specs, actions, observations, base tasks, interventions, instances, trajectories, and scores.
- `src/causal_agent_bench/generation/`: deterministic synthetic base-task, intervention, instance, quality-report, split, and human-audit-sample generation.
- `src/causal_agent_bench/tools/`: deterministic simulated tool system. `simulated.py` is the schema-native tool implementation; `mock_tools.py` is legacy task support.
- `src/causal_agent_bench/environment.py`: benchmark environment, max-step handling, intervention patches, trajectory construction.
- `src/causal_agent_bench/agents/`: deterministic baselines, LLM agent loops, provider clients, registry, and adapter aliases.
- `src/causal_agent_bench/runners/`: experiment config validation, execution, metadata, resume, error logging, cost estimates.
- `src/causal_agent_bench/metrics/` and `src/causal_agent_bench/scoring.py`: final success, tool use, recovery, contradiction, memory, stopping, trajectory quality, ACRS, ranking instability.
- `src/causal_agent_bench/analysis/`: result loading, tables, figures, error-case mining, paper asset export.
- `src/causal_agent_bench/phase2.py`: Phase-2 utility plumbing for config validation, dry-runs, intervention audits, dataset freezing, run summaries, and claim-ledger updates.

Known duplication / legacy seams:

- `metrics/components.py` is legacy `BenchmarkTask` metric support; `scoring.py` uses the newer metric modules.
- `tools/mock_tools.py` is legacy `BenchmarkTask` tool support; `tools/simulated.py` and `tools/registry.py` are the newer schema-native path.
- `analysis/reports.py` is a compatibility wrapper around `analysis/report.py`.
- `io.py` and `utils/io.py` overlap; `utils/io.py` re-exports root helpers plus git/UTC utilities.
- `paper/sections/06_experimental_setup.tex` is a legacy wrapper around `06_experiments.tex`.

## CLI Commands and Status

Current CLI surface:

- `validate`: works for sample instances.
- `generate`: works for schema-native generation configs and legacy sample-task config.
- `run`: works for deterministic and local-stub configs; provider-backed runs need keys/model IDs.
- `score`: works on completed run directories with context files.
- `analyze`: works on completed run directories.
- `export-paper-assets`: works and now writes run metadata into tables/figures.
- `doctor`: works; current output reports Python 3.11.9, 18 YAML configs, 20 test modules, and 0 configured provider credentials.
- `list-providers`: works; local stub configured, OpenAI/Anthropic/Gemini/OpenRouter not configured.
- `estimate-cost`: works, but provider-backed configs currently lack pricing, so dollar estimates are unknown except deterministic/local-stub zero-cost paths.
- `validate-config`: works; classifies `sample_tasks.yaml` and `validate_pilot_v0_1.yaml` as `legacy_or_unknown`.
- `dry-run`: works; does not call providers or write run directories.
- `audit-interventions`: works; `pilot_v0.1` passes automated checks with one high-validity-risk warning for observation conflict.
- `freeze-dataset`: implemented; not yet exercised as part of this audit to avoid creating extra frozen artifacts.
- `summarize-run`: works on existing run directories.
- `update-claim-ledger`: works; lists current claims and refuses unsupported `supported` moves.

Commands run during this audit:

- `python3 -m causal_agent_bench --help`: passed.
- `python3 -m causal_agent_bench doctor`: passed.
- `python3 -m causal_agent_bench list-providers`: passed, no real provider configured.
- `python3 scripts/check_paper_placeholders.py --mode draft`: passed with 7 intentional placeholders listed.
- `python3 scripts/check_claim_ledger.py`: passed.
- `python3 -m causal_agent_bench audit-interventions --benchmark-dir data/processed/pilot_v0_1`: passed.
- `python3 -m causal_agent_bench dry-run --config configs/pilot_multi_provider_20.yaml`: passed; plans 360 trajectories.
- `python3 -m ruff check .`: passed.
- `python3 -m pytest --collect-only -q`: collected 100 tests.

## Configs and Status

Detected 18 YAML configs.

Experiment configs:

- `configs/smoke.yaml`: valid, 9 instances, deterministic agents.
- `configs/dev_20_run.yaml`: valid, 80 instances, includes oracle; for dev only.
- `configs/main_200_run.yaml`: valid, 1200 instances, includes oracle; not suitable as main ranking config without separating oracle.
- `configs/ablation_interventions.yaml`: valid, 80 instances, deterministic non-oracle scaffolds.
- `configs/human_validation_sample.yaml`: valid, 80 instances, includes oracle; should be treated as validation sampling/scaffold only.
- `configs/pilot_20_multi_agent.yaml`: valid local-stub/deterministic pilot, 120 instances, engineering-only.
- `configs/pilot_budget_limited.yaml`: valid local-stub/deterministic pilot, 120 instances, engineering-only.
- `configs/pilot_multi_provider_20.yaml`: valid, 120 instances, 3 provider-backed agents, but no keys/model IDs configured locally.
- `configs/pilot_openai_20.yaml`: valid, 120 instances, OpenAI-only, blocked by missing key/model ID.
- `configs/pilot_anthropic_20.yaml`: valid, 120 instances, Anthropic-only, blocked by missing key/model ID.
- `configs/pilot_openrouter_20.yaml`: valid, 120 instances, OpenRouter-only, blocked by missing key/model ID.
- `configs/pilot_100_multi_agent.yaml`: valid, 600 instances, blocked by missing provider setup and budget approval.
- `configs/pilot_200_multi_agent.yaml`: valid, 1200 instances, blocked by missing provider setup and budget approval.

Generation configs:

- `configs/dev_20_tasks.yaml`: valid generation config, 20 base tasks.
- `configs/main_200_tasks.yaml`: valid generation config, 200 base tasks.
- `configs/generate_pilot_v0_1.yaml`: valid generation config, 250 base tasks.

Legacy or untyped configs:

- `configs/sample_tasks.yaml`: legacy sample-task generation config.
- `configs/validate_pilot_v0_1.yaml`: validation spec, not currently validated by a typed config model.

## Dataset Generation Status

Sample data:

- `data/sample/base_tasks.jsonl`: 3 records.
- `data/sample/interventions.jsonl`: 6 records.
- `data/sample/instances.jsonl`: 9 records.
- `data/sample/mock_knowledge_base.json`: synthetic mock data.

Generated data:

- `data/processed/dev_20`: 20 base tasks, 60 interventions, 80 instances, quality passed.
- `data/processed/main_200`: 200 base tasks, 1000 interventions, 1200 instances, quality passed.
- `data/processed/pilot_v0_1`: 250 base tasks, 1250 interventions, 1500 instances, quality passed.
- `pilot_v0_1` split files exist:
  - dev / pilot_20: 120 instances.
  - pilot_100: 600 instances.
  - pilot: 1200 instances.
  - heldout: 300 instances.
  - human audit sample: 100 rows.

Audit result for `pilot_v0.1`:

- Automated check passed.
- One warning remains: high intervention-validity risk for an `observation_conflict` intervention. This is expected to need human/expert audit before claim support.

## Agent Adapters Status

Deterministic agents:

- `random_tool_agent`: lower-bound deterministic baseline.
- `scripted_oracle_agent`: uses hidden/gold task information; sanity-check upper bound only.
- `greedy_tool_agent`: weak keyword baseline.
- `react_stub_agent`: deterministic ReAct-style baseline.
- `planner_executor_stub_agent`: deterministic planner-executor baseline.

LLM agent styles:

- `direct_tool_agent`: one-step-at-a-time ReAct-style LLM loop.
- `planner_executor_agent`: plan then execute/revise loop.
- `self_check_agent`: LLM loop with verification before final answer.

Provider clients:

- `local_stub`: configured, deterministic, zero-cost engineering path.
- `openai`: implemented, not configured locally.
- `anthropic`: implemented, not configured locally.
- `gemini`: implemented, not configured locally.
- `openrouter`: implemented, not configured locally.

Risks:

- Provider adapters are mostly unverified without live keys.
- Model IDs expand from environment variables and are currently empty in provider dry-run output.
- Budget caps are present in configs but not enforced as a hard runtime stop.
- Provider-specific API surface may drift; adapters need small real calls before pilot trust.

## Tool Environment Status

Implemented deterministic schema-native tools:

- `search_database`
- `lookup_policy`
- `check_calendar`
- `read_file`
- `query_spreadsheet`
- `calculate_price`
- `compare_options`
- `send_email_draft`
- `book_stub`
- `verify_fact`

Safety status:

- No live web, real email, real booking, private data access, or shell execution benchmark tool is enabled.
- `send_email_draft` and `book_stub` are local stubs.
- Tool failure/corruption/partial-output intervention patches are supported.

Risk:

- Some legacy `mock_tools.py` behavior exists for old `BenchmarkTask` paths and should be consolidated later.

## Scoring and Metrics Status

Implemented:

- Final binary/partial success.
- Required-tool recall, precision, unnecessary calls, missing required tools, invalid calls.
- Argument validity and argument errors.
- Tool-error recovery and repeated failed calls.
- Contradiction detection/resolution.
- Memory use/verification/blind trust.
- Premature stop, max-step failure, correct stop.
- Trajectory efficiency and faithfulness.
- ACRS and per-family degradation.
- Clean-vs-ACRS ranking instability with Spearman and Kendall.

Risks:

- Many detectors are heuristic and keyword/template dependent.
- No human validation yet for final-answer labels or trajectory diagnostics.
- ACRS is undefined when clean success is zero; reports need clean and intervention rates next to ACRS.
- Ranking instability is uninformative for all-zero stub pilots.

## Analysis and Paper Asset Status

Implemented:

- Loading run results from trajectories/scores/instances.
- Tables for benchmark stats, main performance, family performance, ablations placeholder, human validation placeholder, paired comparisons, ranking instability.
- Figures for benchmark schematic, clean vs intervention, family breakdown, ranking instability, failure modes, trajectory/final disagreement, error-case taxonomy.
- Error-case mining categories for final/trajectory disagreement, clean success/intervention failure, recovery failures, memory blind trust, observation conflict, premature success/stopping, irrelevant-tool overuse, invalid arguments, max-step failure, unstated uncertainty, corruption misses.
- Paper assets include run directory, config hash, dataset version, model IDs, and timestamp metadata.

Risks:

- Global `figures/` and `tables/` currently reflect a local-stub engineering run; they must be regenerated from a real run before paper use.
- Some existing legacy `results/` directories lack modern metadata files such as `errors.jsonl` or aggregate scores.
- Run artifacts are ignored by git except `.gitkeep`, but local disk contains 33 MB of ignored results.

## Claim Ledger Status

- `docs/CLAIM_LEDGER.md` and `docs/claim_ledger.json` exist.
- `python3 scripts/check_claim_ledger.py` passes.
- C1-C8 and C10 remain `planned`.
- C9 is `engineering_only`.
- No main scientific claim is supported.
- `update-claim-ledger` refuses to mark a claim supported unless evidence paths exist.

## Paper Placeholder Status

Draft placeholder check passes and reports 7 intended blockers:

- `[N]`, `[M]`, `[K]`, `[X]`, `[rho]`
- `[domains]`
- `[main finding placeholder]`
- ablation `not yet run` marker in the results section

Submission check is expected to fail until real evidence exists. Citation TODO stubs have been replaced with real citation keys where BibTeX entries exist.

## Test Coverage Gaps

Current health:

- `python3 -m ruff check .`: passed.
- `python3 -m pytest --collect-only -q`: 100 tests collected.
- Previous full run after Phase 2: 99 passed, 1 skipped.

Gaps:

- Provider integration tests are skipped unless keys/model IDs are present.
- No test currently confirms budget caps stop a run.
- No live-provider contract tests with tiny request fixtures.
- Human validation workflow is not tested end-to-end.
- Dataset freeze command has CLI tests, but frozen release policy is not yet tested against all generated split files.
- Metrics need human-labeled calibration tests.
- Config model for `validate_pilot_v0_1.yaml` is missing.
- Legacy/new path equivalence is not tested for duplicated modules.

## Security/API-Key Risks

Good:

- API keys are read from environment variables.
- `doctor` reports only counts, not values.
- `list-providers` prints env var names and configured status only.
- No key-like literal was found in source/config/docs outside env-var names.

Risks:

- Provider request errors could include provider-returned response bodies. Current HTTP error body truncation should be reviewed before real runs.
- Provider model IDs are empty if env vars are unset; dry-run detects this but `validate-config` does not fail it.
- Budget caps are advisory today.
- Prompt and response logs may contain sensitive model outputs if future tasks include sensitive data. Current benchmark should remain synthetic.

## Top 20 Fixes in Priority Order

1. Configure one low-cost provider/model and run a 1-2 instance live smoke before the 20-task pilot.
2. Add hard validation that provider-backed configs require non-empty model IDs before `run`.
3. Add runtime budget-cap enforcement using accumulated estimated cost where pricing exists.
4. Add pricing entries to provider pilot configs or require a cost-policy file.
5. Add deterministic non-oracle baselines to the provider-backed pilot comparison config, while excluding oracle from realistic ranking.
6. Add tiny provider contract tests gated by environment variables and capped to one task.
7. Add redaction tests for provider error bodies and trajectory metadata.
8. Add typed validation support for `configs/validate_pilot_v0_1.yaml`.
9. Add a command that validates all configs in one pass and marks legacy/unknown configs explicitly.
10. Consolidate or clearly deprecate `mock_tools.py` vs `simulated.py`.
11. Consolidate or clearly deprecate `metrics/components.py` vs schema-native metrics.
12. Add human-audit protocol docs and a machine-readable audit result schema.
13. Add tests that frozen datasets contain every expected split and manifest hash.
14. Re-run asset export only from known run directories and avoid committing global stub figures as evidence.
15. Add CI that runs lint, tests, doctor, claim-ledger check, and paper draft check.
16. Add a real provider-backed 20-base-task pilot with 3 LLM agent styles and 2 deterministic non-oracle baselines.
17. Mine and manually inspect error cases from the 20-task pilot before scaling.
18. Run a 100-base-task multi-provider pilot only after budget/cost controls are enforced.
19. Complete human/expert validation before supporting C3 or C10.
20. Freeze benchmark v1.0 only after intervention audit warnings are resolved or explicitly documented.

## Fixes Made During This Audit

No code fixes were made during this audit. The only deliverables created are this audit map and its machine-readable JSON companion.
