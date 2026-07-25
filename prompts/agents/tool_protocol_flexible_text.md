# Flexible Text Tool-Call Protocol

Prompt version: `tool_protocol_flexible_text_v1`

You may include one short sentence of prose before or after the action, but the response must contain exactly one parseable JSON action object.

Tool call JSON object:

```json
{"action": "tool_call", "thought": "why this tool is needed", "tool_name": "search_database", "arguments": {"query": "..."}}
```

Final answer JSON object:

```json
{"action": "final_answer", "thought": "why the answer is supported or impossible", "final_answer": "answer text", "evidence": ["observation or limitation"], "stop": true}
```

Clarification or uncertainty JSON object:

```json
{"action": "clarification", "thought": "why the task is underspecified", "clarification": "question or uncertainty statement", "stop": true}
```

Protocol rules:
- Use exactly one of `tool_call`, `final_answer`, or `clarification`.
- Use only tool names from the available tool list.
- Do not call two tools in one response.
