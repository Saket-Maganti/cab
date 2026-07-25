# Reproducibility Commands With Provider Template

Status: template only. Do not run without explicit approval.

```bash
export OPENAI_API_KEY="set-in-shell-only"
python3 -m causal_agent_bench provider-pilot-preflight --config configs/compact20_3model_APPROVAL_REQUIRED.yaml
# RESULT_REQUIRED: only after approval, human review, C10, budget, and credentials gates.
```

Credentials must be environment-only. Never store API keys in YAML, Markdown, JSON, CSV, or logs.
