# 09 Agent Audit

| Agent/class | Type | Uses hidden data? | Realistic? | Safe for model ranking? | Notes |
|---|---|---:|---:|---:|---|
| `RandomToolAgent` | local baseline | no | weak baseline | yes, as baseline | deterministic enough for engineering comparisons |
| `GreedyToolAgent` | local baseline | no | weak baseline | yes, as baseline | no provider metadata needed |
| `ScriptedOracleAgent` | oracle | yes | no | no | sanity-check/upper-bound only; must be excluded from realistic ranking |
| `ReActStyleStubAgent` | local stub | no | no | engineering only | useful for pipeline validation |
| `PlannerExecutorStubAgent` | local stub | no | no | engineering only | useful for pipeline validation |
| Direct/planner/self-check local-stub LLM agents | local-provider simulations | no | no | engineering only | provider recorded as `local_stub` |
| OpenAI/Anthropic/Gemini/OpenRouter/local-compatible adapters | provider-backed LLM agents | no intended hidden access | yes when configured | yes, if metadata complete | blocked here by missing provider setup |

## Metadata and safety

Provider-backed LLM paths include provider/model IDs, prompt hashes/files, temperature, max tokens, retry counts, token/cost/latency fields, and redaction helpers. API keys are looked up from environment and must not be printed or stored.

## Required claim guardrail

Any result containing `ScriptedOracleAgent` is a sanity check or upper bound only. It cannot support claims about real LLM agent skill.

