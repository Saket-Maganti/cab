# Cost And Latency Tracking

Cost and latency are first-class analysis fields in CausalAgentBench. They are still estimates unless a provider reports token usage and the run config supplies a pricing model.

Do not use deterministic smoke or local-stub rows as scientific cost evidence. Local stubs report zero provider cost only to verify accounting plumbing.

## Per-Call Fields

Each LLM call record stores:

- `prompt_tokens`, `completion_tokens`, and `total_tokens`.
- `estimated_cost_usd`.
- `latency_s`.
- `retries`.
- `provider` and `model`.
- Prompt, response, tool-state, and model-config hashes when available.
- Cache metadata, including zero charged cost for cache hits.

Provider keys stay in environment variables. Cost metadata never includes API key values.

## Per-Trajectory Fields

Each trajectory metadata block stores:

- `estimated_cost_usd`: summed model-call cost for the trajectory.
- `latency_s`: summed model-call latency for the trajectory.
- `model_call_count`: provider/model calls, excluding budget-blocked pseudo-responses.
- `llm_call_count`: all LLM action records, including budget-blocked pseudo-responses.
- `tool_call_count`: simulated benchmark tool calls.
- `prompt_tokens`, `completion_tokens`, `total_tokens`, and `total_retries`.

The score records copy this metadata into `scores.jsonl` so cost-normalized metrics can be recomputed from score artifacts alone.

## Cost Models

Pricing can be supplied directly on an `agent_runs` entry:

```yaml
agent_runs:
  - name: direct_openai
    agent: direct_tool_agent
    provider: openai
    model: ${OPENAI_MODEL_ID}
    pricing:
      input_per_1m_tokens: 1.00
      output_per_1m_tokens: 3.00
```

Or centrally by provider and model:

```yaml
cost_models:
  openai:
    gpt-example:
      input_per_1m_tokens: 1.00
      output_per_1m_tokens: 3.00
```

Agent-level `pricing` overrides `cost_models`. Provider/model cost models can use `*` or `default` as a fallback model key.

## Budget Caps

Budget caps are configured in USD:

- Experiment-level `budget_cap_usd`: max estimated cost for the run.
- Agent-run `budget_cap_usd`: max estimated cost for that agent run.
- Experiment-level or agent-run `task_budget_cap_usd`: max estimated cost for one trajectory.

Run and agent caps are checked before launching a trajectory. Task caps are passed into LLM agents so they can stop before another model call once the cap is reached. A single expensive provider call can still exceed a task cap if the provider only reports cost after the response.

Budget-skipped trajectories are written to `errors.jsonl` with `error_type: BudgetExceededError`; they are not scored as completed results.

## Estimates

Dry-run cost estimates:

```bash
python -m causal_agent_bench estimate-cost --config configs/pilot_multi_provider_20.yaml
```

The estimator reports upper-bound model calls, output tokens, optional input-token estimates, configured budget caps, pricing source, and known estimated cost when a cost model is configured. It is not an invoice.

## Paper Tables

Paper asset export writes:

- `table6_performance_vs_cost.*`: final success, clean/intervention success, average cost, total cost, latency, model calls, tool calls, and cost-normalized success.
- `table7_robustness_vs_cost.*`: ACRS, degradation, cost, latency, and cost-normalized ACRS.

Both tables exclude oracle sanity-check agents by default.
