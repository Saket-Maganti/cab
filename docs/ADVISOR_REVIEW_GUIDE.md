# Advisor Review Guide

This guide is for professor/advisor review before any provider spend.

## Review Before Provider Spend

Review these no-run artifacts first:

- `reports/repair_plan/repair_plan.md`
- `reports/benchmark_cards/benchmark_card.md`
- `reports/gold_outputs/gold_output_validation.md`
- `reports/tool_schemas/tool_schema_validation.md`
- `reports/static_leakage/static_leakage_report.md`
- `reports/provider_pilot_preflight/provider_pilot_preflight.md`
- `reports/advisor_review/advisor_review_packet.md`
- `reports/paper_readiness/paper_readiness_map.md`

## Advisory Reports

These reports support planning and method transparency, but do not approve
provider runs by themselves:

- benchmark/dataset/intervention/limitations cards
- benchmark manifest
- config profiles
- paper readiness map
- advisor review packet

## Blocker Reports

Treat blockers in these reports as stop signs before provider spend:

- repair plan
- provider pilot preflight
- gold output validation
- tool schema validation
- static leakage report
- intervention isolation audit
- config metadata lint

## Method Claims Only

The following reports can support method claims about what has been specified or
statically checked:

- intervention taxonomy
- benchmark cards
- method appendix
- method figure scaffolds
- config profile report
- benchmark manifest

They cannot support empirical claims.

## Empirical Claims Not Allowed Yet

Current evidence state remains:

- paper-eligible runs: 0
- eligible paper assets: 0
- C1-C8: planned / unsupported
- C9: engineering_only
- C10: planned / unsupported

## Safe Commands

```bash
python3 -m pytest tests/test_safety_reports.py tests/test_cli.py tests/test_claim_ledger.py tests/test_provider_pilot_readiness.py -q
python3 -m pytest tests/test_benchmark_quality.py tests/test_intervention_isolation.py tests/test_synthetic_metric_fixtures.py tests/test_human_validation_protocol.py tests/test_run_cost_estimator.py tests/test_method_figure_scaffolds.py tests/test_release_readiness_report.py tests/test_dataset_issue_triage.py tests/test_provider_pilot_preflight.py tests/test_human_validation_sampler.py tests/test_method_appendix.py tests/test_evidence_dashboard.py tests/test_config_metadata_lint.py -q
python3 -m pytest tests/test_repair_plan.py tests/test_benchmark_cards.py tests/test_gold_output_validation.py tests/test_tool_schema_validation.py tests/test_static_leakage.py tests/test_benchmark_manifest.py tests/test_config_profiles.py tests/test_advisor_review_packet.py tests/test_paper_readiness_map.py -q
python3 scripts/check_evidence_safety.py
python3 -m causal_agent_bench all-no-run-reports --output-dir /tmp/cab_advanced_upgrade_reports
```

## Forbidden Commands

Do not run benchmarks, providers, local LLM jobs, broad test lanes, or claim
promotion commands during advisor review. In particular, do not run:

```bash
python3 -m causal_agent_bench run --config ...
make smoke
make test
python3 -m causal_agent_bench run-llm-judge ...
python3 -m causal_agent_bench fill-paper-from-run --promote-to-supported ...
python3 -m causal_agent_bench update-claim-ledger --promote-to-supported ...
```

## Decision Options

The advisor should choose one option explicitly:

- approve tiny provider dry-run
- request dataset fixes first
- request human-validation protocol changes
- defer provider spend

Approval must be recorded outside the template config and then copied into an
approved config file only after review.
