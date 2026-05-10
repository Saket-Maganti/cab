# Baseline Agents

These agents are benchmark controls, not claims about frontier agent performance.

| Agent | Purpose | Uses hidden information? | Limitations |
|---|---|---:|---|
| `random_tool_agent` | Lower-bound baseline that randomly chooses an available tool or stops. | No | Often stops early and uses shallow default arguments. |
| `scripted_oracle_agent` | Upper-bound sanity check that follows gold tool metadata and expected answers when available. | Yes | Not a realistic agent; exclude from model capability claims. |
| `greedy_tool_agent` | Weak realistic baseline using keyword heuristics from the user instruction. | No | No deep planning, no robust observation interpretation. |
| `react_stub_agent` | Deterministic ReAct-style thought/action/observation baseline. | No | Rule-based thoughts; no language-model reasoning. |
| `planner_executor_stub_agent` | Deterministic plan-then-execute baseline with simple error revision. | Partially, only for legacy `BenchmarkTask` compatibility when gold sequences are present | For schema-native `BenchmarkInstance` runs, it uses keyword-derived plans rather than gold tool sequences; still far weaker than an LLM planner. |

## LLM Adapter Placeholders

The repository also defines interface placeholders for:

- `openai_chat_agent`
- `anthropic_agent`
- `gemini_agent`
- `local_hf_chat_agent`

These adapters intentionally do not require provider SDKs yet. They accept configuration concepts such as system prompt, user instruction, tool specs, observation history, max steps, temperature, and seed, but raise clear errors until real implementations are added. API keys must be read from environment variables in future work and must never be committed.

## Reporting Guidance

- Report oracle results separately from non-oracle baselines.
- Exclude `scripted_oracle_agent` from any claim about realistic agent capability or model ranking.
- Mark legacy `BenchmarkTask` compatibility runs separately, because some legacy stubs may use expected-behavior metadata for smoke-test continuity.
- Use `random_tool_agent` only as a floor.
- Treat stub agents as engineering baselines for validating benchmark mechanics.
- Do not use any baseline smoke result as a scientific model ranking.

## Minimum Baseline Set For Paper Claims

A credible paper experiment should include:

- at least one random or degenerate floor,
- at least one weak heuristic baseline,
- at least one scaffolded non-oracle baseline,
- at least two LLM-backed agents or agent configurations,
- the oracle baseline reported in a separate sanity-check table only.
