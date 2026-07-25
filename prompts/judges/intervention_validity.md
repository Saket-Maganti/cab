Prompt version: {prompt_version}

You are judging intervention validity for CausalAgentBench. Return only JSON with:

```json
{"label": "yes|no|unclear|not_applicable", "rationale": "short reason", "confidence": 0.0}
```

Use `yes` if the intervention preserves the high-level user goal and isolates the stated changed factor. Use `no` if it changes multiple factors, silently changes ground truth, or changes the task goal. Use `not_applicable` for clean instances.

Item:

```json
{item_json}
```
