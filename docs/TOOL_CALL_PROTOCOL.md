# Tool Call Protocol

CausalAgentBench uses one canonical JSON action protocol for provider-backed agents. The protocol is designed to be provider-agnostic and auditable.

## Action Forms

Tool call:

```json
{"action": "tool_call", "thought": "why this tool is needed", "tool_name": "search_database", "arguments": {"query": "..."}}
```

Final answer:

```json
{"action": "final_answer", "thought": "why the answer is supported or impossible", "final_answer": "answer text", "evidence": ["observation or limitation"], "stop": true}
```

Clarification or uncertainty:

```json
{"action": "clarification", "thought": "why the task is underspecified", "clarification": "question or uncertainty statement", "stop": true}
```

## Parser Outcomes

The parser records a `ToolCallParseResult` for each LLM action. Outcomes include:

- `valid_tool_call`
- `valid_final_answer`
- `clarification`
- `invalid_json`
- `unknown_tool`
- `invalid_argument_schema`
- `multiple_tool_calls`
- `missing_action`
- `repeated_failed_call`
- `final_answer_without_required_evidence`

The parser repairs only formatting wrappers: Markdown JSON fences, prose surrounding a JSON object, and trailing commas. It does not repair semantic errors such as wrong tool names, missing required arguments, invalid argument types, or multiple requested tool calls.

## Trajectory Logging

Each LLM step preserves:

- `raw_model_output`: the raw text returned by the model, when available.
- `parsed_action`: the structured `ToolCallParseResult`.
- `action.metadata.parser_outcome`: a compact outcome label.
- `action.metadata.parser_valid`: whether the action satisfied the protocol.

This is engineering evidence for auditability, not a scientific result by itself.
