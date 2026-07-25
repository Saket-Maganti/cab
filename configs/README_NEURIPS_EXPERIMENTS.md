# NeurIPS Experiment Configs

**Do not run paid configs without signed approval and `allow_paid_calls: true`.**

## Stage → config mapping

| Stage | Config(s) | Paid? | Paper-eligible? |
|-------|-----------|-------|-----------------|
| A | (no run) | No | No |
| B | `provider_pilot_tiny_template.yaml` → `*_APPROVED.yaml` | Yes (≤$5) | No (until audit) |
| C | `pilot_multi_provider_20.yaml`, `pilot_20_multi_agent.yaml` | Yes | After audit |
| D | `pilot_100_multi_agent.yaml`, `commercial_api_pilot_medium_100.yaml` | Yes | After audit |
| E | `main_200_run.yaml` + `main_200_tasks.yaml` | Yes | After main freeze + audit |
| F | `commercial_api_main_500.yaml`, `main_500_multi_provider.yaml` | Yes $$$ | After main freeze + audit |
| G | `human_validation_sample.yaml` | No | Annotations only |
| Engineering | `pilot_mock_diagnostic_micro.yaml`, `pilot_stub_micro_3.yaml` | No | **Never** for empirical claims |

## Safe planning commands (no run)

```bash
python3 -m causal_agent_bench validate-config --config configs/provider_pilot_tiny_template.yaml
python3 -m causal_agent_bench plan-run --config configs/provider_pilot_tiny_template.yaml
python3 -m causal_agent_bench estimate-run-cost --config configs/provider_pilot_tiny_template.yaml --output-dir /tmp/cab_cost
```

## Provider registry

Model IDs are **environment placeholders** — see `configs/providers.yaml`. Do not treat template defaults as final NeurIPS model choices.

## Evidence labels in configs

- `scientific_evidence: false` by default
- `evidence_scope: provider_pilot_pending_verification` on template
- `template_only: true` on tiny template
