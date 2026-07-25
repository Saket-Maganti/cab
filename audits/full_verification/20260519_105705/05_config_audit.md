# 05 Config Audit

All YAML files under `configs/` parsed. Built-in config validation was used instead of adding a separate `scripts/validate_configs.py` because `python3 -m causal_agent_bench validate-config` already performs structured validation.

## Summary table

| Config group | Purpose | Valid? | Uses oracle? | Uses provider? | Risks |
|---|---|---:|---:|---:|---|
| `smoke.yaml`, `dev_20_run.yaml`, `main_200_run.yaml`, `baseline_suite_local_stub.yaml`, `human_validation_sample.yaml` | local/stub and sanity-check experiments | yes | yes | no | oracle must stay sanity-check only |
| `pilot_20_multi_agent.yaml`, ablation local-stub configs, web-shadow stub configs | deterministic local/stub experiments | yes | no | local stub | engineering-only evidence |
| `generate_*` configs | dataset generation | yes | no | no | generated dataset changes need version/changelog/card updates |
| `pilot_multi_provider_20.yaml`, `pilot_openai_20.yaml`, `pilot_anthropic_20.yaml`, `pilot_gemini_20.yaml`, `pilot_openrouter_20.yaml`, commercial API configs | real provider pilots/main candidates | structurally yes | no | yes | not ready: missing model IDs/API keys/pricing; paid calls disabled or unavailable |
| `main_local_openai_compatible_100.yaml`, `pilot_local_openai_compatible_20.yaml` | local OpenAI-compatible runs | structurally yes | no | local OpenAI-compatible | model IDs unset |
| `mini_study_*_stub.yaml` | mini-study candidates | structurally yes | no | local stub | referenced generated mini-study datasets are missing |
| `ablation_matrix_local_stub.yaml` | ablation matrix expansion | yes after validator fix | no | local stub | local engineering-only |

## Fixes applied

- `src/causal_agent_bench/phase2.py`: fixed provider-readiness cost estimation for loaded experiment configs.
- `src/causal_agent_bench/phase2.py`: added ablation-matrix validation support to `validate_config_file`.
- `configs/web_shadow_api_stub.yaml` and `configs/web_shadow_web_stub.yaml`: changed stale `benchmark_path` to `benchmark_dir`.

## Serious config errors remaining

No parser-level errors remain. Provider configs are intentionally not ready in this environment.

