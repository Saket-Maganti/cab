Prompt version: {prompt_version}

You are judging contradiction handling. Return only JSON with:

```json
{"label": "yes|no|unclear|not_applicable", "rationale": "short reason", "confidence": 0.0}
```

Use `yes` when the trajectory detects and resolves or acknowledges conflicting evidence. Use `no` when it ignores a relevant contradiction. Use `not_applicable` when no contradiction is present.

Item:

```json
{item_json}
```
