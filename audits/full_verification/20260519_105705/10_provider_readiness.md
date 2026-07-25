# 10 Provider Readiness

## Commands

- `python3 -m causal_agent_bench list-providers`
- `python3 -m causal_agent_bench estimate-cost --config configs/pilot_multi_provider_20.yaml`
- `python3 -m causal_agent_bench dry-run --config configs/pilot_multi_provider_20.yaml --output-dir audits/full_verification/20260519_105705/dry_runs`
- `python3 -m causal_agent_bench validate-config --config configs/commercial_api_pilot_small_20.yaml`

## Status

Configured providers:

- `local_stub`: configured
- `local_openai`: configured

Not configured:

- `openai`
- `anthropic`
- `gemini`
- `openrouter`
- generic external `openai_compatible`

## Pilot readiness result

`configs/pilot_multi_provider_20.yaml` dry-run succeeded without paid calls and without printing API keys, but the config is not ready for a real provider pilot:

- external model ID fields are empty
- external API keys are missing
- pricing is incomplete, so cost upper bound is unknown
- paid calls are not safely enabled

## Fix applied

`src/causal_agent_bench/phase2.py` now uses the loaded experiment config for budget/cost readiness checks instead of calling a path-only estimator with a config object.

## Decision

No paid provider run was executed. This is correct for the current environment.

