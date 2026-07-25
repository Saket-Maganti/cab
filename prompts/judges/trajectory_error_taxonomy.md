Prompt version: {prompt_version}

You are judging whether the automated trajectory error taxonomy label is correct. Return only JSON with:

```json
{"label": "yes|no|unclear|not_applicable", "rationale": "short reason", "confidence": 0.0}
```

Use `yes` if the taxonomy label matches the trajectory evidence. Use `no` if the label does not match. Use `not_applicable` if no error label is present.

Item:

```json
{item_json}
```
