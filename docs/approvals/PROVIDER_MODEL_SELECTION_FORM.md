# Provider / Model Selection Form

Record selections in the APPROVED config (never commit API keys).

| Field | Selection |
|---|---|
| Provider family | openai / anthropic / gemini / openrouter |
| Model ID | env var only, e.g. `${OPENAI_MODEL_ID}` |
| Temperature | 0.0 (pilot default) |
| Max output tokens | ≤ 512 |
| Retry / timeout | per template |

## Checklist

- [ ] Model placeholder resolved (no `PLACEHOLDER_SET_BEFORE_RUN` at live run)
- [ ] Provider is real API family (not local/mock/stub/oracle)
- [ ] Agent is `direct_tool_agent` (no oracle/mock/stub agents in provider pilot config)
- [ ] Pricing registry path reviewed (`configs/model_pricing.yaml`)

## Risk acknowledgement

- [ ] Rate limits may extend runtime beyond static estimate
- [ ] Pilot output is **not** paper-eligible until post-run audit passes

Advisor signature (optional cross-check): __________________  Date: __________
