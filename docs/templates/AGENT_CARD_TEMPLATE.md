# Agent Card Template

Copy and fill for each agent configuration evaluated.

| Field | Value |
|---|---|
| **Agent name** | e.g., `direct_tool_react` |
| **Agent class** | e.g., `DirectToolAgent` |
| **Provider / model** | e.g., `openai` / `gpt-4.1-mini` or `mock_behavior_agent` |
| **Prompt template** | Path + hash, e.g., `prompts/direct_tool.md` |
| **Tools exposed** | List from benchmark instance or config |
| **Date** | YYYY-MM-DD |
| **Config** | e.g., `configs/pilot_multi_provider_20.yaml` |
| **Config hash** | From `run_metadata.json` |
| **Sampling** | temperature, max_tokens, top_p |
| **Cost (USD)** | Total or per-trajectory |
| **Latency (s)** | Median / p95 |
| **Known limitations** | e.g., JSON parse failures, no vision |
| **Evidence level** | stub / mock / local_preliminary / provider_pilot / main |
| **Allowed claims** | Per [EVIDENCE_LEVEL_POLICY.md](../EVIDENCE_LEVEL_POLICY.md) |

**Note:** Mock/stub agents → `engineering_only` / `not_real_llm_behavior` only.
