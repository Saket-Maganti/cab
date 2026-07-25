# Agent Card Example — mock_tool_overuser

**⚠️ NOT A REAL LLM — mock diagnostic agent only**

| Field | Value |
|---|---|
| **Agent name** | `mock_tool_overuser` |
| **Agent type** | `mock_behavior_agent` |
| **Real LLM?** | **No** — deterministic scripted behavior |
| **Mock behavior** | `tool_overuser` |
| **Provider** | none (null) |
| **Model** | none |
| **Tools available** | Same simulated tool suite as benchmark instances |
| **Behavior mode** | Script executes predetermined tool-call patterns including excessive tool use |
| **Temperature / tokens** | N/A (no LLM calls) |

## Intended use

- Validate trajectory diagnostic detectors (tool overuse, invalid calls, etc.)
- Exercise scoring pipeline on known failure patterns
- Engineering-only micro runs (`pilot_mock_diagnostic_micro.yaml`)

## Not intended for

- Representing real LLM agent capabilities
- Paper results tables or figures
- Claim ledger promotion (C1–C8)
- Leaderboard or model comparison

## Limitations

- Single scripted behavior; does not explore agent diversity
- No adaptation to instance content beyond mock script
- Metrics reflect mock script, not model competence

## Claim restrictions

| Allowed | Forbidden |
|---|---|
| "Mock agent exercised tool_overuser script" | "Agents overuse tools on benchmark" |
| "Detector flagged excessive_tool_overuse cases" | "Frontier models fail tool selection" |
| Engineering-only pipeline validation | Any generalization to LLMs |

See [RUN_CARD_EXAMPLE.md](RUN_CARD_EXAMPLE.md) and [docs/DO_NOT_OVERCLAIM.md](../docs/DO_NOT_OVERCLAIM.md).
