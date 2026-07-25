# Dry Run Report

This report validates plumbing only. It does not call paid providers and is not scientific evidence.

- Config: `configs/pilot_multi_provider_20.yaml`
- Run name: `pilot_multi_provider_20`
- Benchmark: `/Users/saketmaganti/codexprojects/causal-agent-bench/data/processed/pilot_v0_1/dev_instances.jsonl`
- Planned trajectories: `360`
- Simulated trajectories: `3`
- Tool schemas valid: `True`
- Provider calls made: `False`

## Simulations

- `direct_tool_openai`: ok, steps=2, stop=final_answer
- `planner_executor_anthropic`: ok, steps=2, stop=final_answer
- `self_check_openrouter`: ok, steps=2, stop=final_answer

## Config Issues

- error: Model is empty for paid provider 'openai'. Fix: Set the model field or the corresponding *_MODEL_ID environment variable.
- warning: API key is not configured for provider 'openai'. Fix: Set one of ['OPENAI_API_KEY'] before running paid provider experiments.
- warning: Pricing is not configured; cost estimates will be unknown. Fix: Add input_per_1m_tokens/output_per_1m_tokens if you want numeric cost bounds.
- error: Model is empty for paid provider 'anthropic'. Fix: Set the model field or the corresponding *_MODEL_ID environment variable.
- warning: API key is not configured for provider 'anthropic'. Fix: Set one of ['ANTHROPIC_API_KEY'] before running paid provider experiments.
- warning: Pricing is not configured; cost estimates will be unknown. Fix: Add input_per_1m_tokens/output_per_1m_tokens if you want numeric cost bounds.
- error: Model is empty for paid provider 'openrouter'. Fix: Set the model field or the corresponding *_MODEL_ID environment variable.
- warning: API key is not configured for provider 'openrouter'. Fix: Set one of ['OPENROUTER_API_KEY'] before running paid provider experiments.
- warning: Pricing is not configured; cost estimates will be unknown. Fix: Add input_per_1m_tokens/output_per_1m_tokens if you want numeric cost bounds.
- error: Commercial API providers are configured but allow_paid_calls is false. Fix: Set allow_paid_calls: true explicitly before running paid provider experiments.
