Prompt version: {prompt_version}

You are judging final-answer correctness for CausalAgentBench. Return only JSON with:

```json
{"label": "yes|no|unclear|not_applicable", "rationale": "short reason", "confidence": 0.0}
```

Use `yes` only if the final answer is supported by the task evidence and expected label. Use `no` if it is unsupported, contradictory, or wrong. Use `unclear` when the packet lacks enough evidence.

Item:

```json
{item_json}
```
