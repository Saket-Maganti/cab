# Canonical Tool-Call Protocol

Return exactly one JSON object. Do not wrap it in Markdown, prose, XML, or multiple objects.

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

Protocol rules:
- Use exactly one of `tool_call`, `final_answer`, or `clarification`.
- For tool calls, use only `tool_name` values from the available tool list.
- `arguments` must be a JSON object that satisfies the selected tool schema.
- Do not call two tools in one response.
- Do not finalize until required evidence appears in the observation history or the task is impossible.
- If evidence is missing, failing, corrupted, or contradictory, call a relevant tool or use the clarification/uncertainty form.
