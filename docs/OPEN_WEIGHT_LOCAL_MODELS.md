# Open-Weight and Local Model Runs

This guide covers running CausalAgentBench agents against open-weight models served through an **OpenAI-compatible HTTP API** on your machine or LAN.

Use `provider: local_openai` in experiment configs. This is separate from:

- `local_stub` — deterministic engineering stub, not a model baseline.
- `openai`, `anthropic`, `gemini`, `openrouter` — commercial API providers.
- `openai_compatible` — generic remote/self-hosted endpoint that may still require an API key.

Local runs are labeled `local_open_weight_unvalidated` in run metadata and paper tables. Do not merge them with commercial API leaderboards without explicit justification.

## Supported local servers

Any server that implements `POST /v1/chat/completions` (or `POST /chat/completions` under a `/v1` base URL) should work, including:

| Stack | Typical base URL | Notes |
| --- | --- | --- |
| vLLM | `http://localhost:8000/v1` | `python -m vllm.entrypoints.openai.api_server --model <id>` |
| llama.cpp server | `http://localhost:8080/v1` | `llama-server -m <gguf> --port 8080` |
| Ollama | `http://localhost:11434/v1` | `ollama serve` then use the Ollama model tag as `model` |
| LM Studio | `http://localhost:1234/v1` | Enable the local server in LM Studio settings |

The repo normalizes `base_url` to a chat-completions endpoint automatically.

## Quick start

1. Start your local server and confirm the model is loaded.
2. Export environment variables (never put secrets in YAML):

```bash
export LOCAL_OPENAI_MODEL_ID="your-model-id-or-ollama-tag"
export LOCAL_OPENAI_BASE_URL="http://localhost:8000/v1"   # optional; this is the default
# export LOCAL_OPENAI_API_KEY="optional-if-server-requires-auth"
```

3. Validate and dry-run:

```bash
python -m causal_agent_bench list-providers
python -m causal_agent_bench validate-config --config configs/pilot_local_openai_compatible_20.yaml
python -m causal_agent_bench dry-run --config configs/pilot_local_openai_compatible_20.yaml
```

4. Run the pilot or larger local config:

```bash
python -m causal_agent_bench run --config configs/pilot_local_openai_compatible_20.yaml
python -m causal_agent_bench run --config configs/main_local_openai_compatible_100.yaml
```

5. Summarize and export assets:

```bash
python -m causal_agent_bench summarize-run --run-dir results/<timestamp>_pilot_local_openai_compatible_20
python -m causal_agent_bench export-paper-assets --run-dir results/<timestamp>_pilot_local_openai_compatible_20
```

Check `run_metadata.json` for `evidence_scope: local_open_weight_unvalidated` and table column `evidence_scope` in exported CSVs.

## Example configs

- `configs/pilot_local_openai_compatible_20.yaml` — 20-instance pilot on `pilot_20_instances.jsonl`
- `configs/main_local_openai_compatible_100.yaml` — 100-instance run on `pilot_100_instances.jsonl`

Both configs set `budget_cap_usd: 0.0` because local inference is not billed through the repo's paid-provider cost model. Optional `cache_dir` enables deterministic replay of identical prompts during debugging.

## Setting base URL and model ID

**Per-run (YAML):**

```yaml
agent_runs:
  - name: direct_tool_local_openai
    agent: direct_tool_agent
    provider: local_openai
    model: "${LOCAL_OPENAI_MODEL_ID:-}"
    base_url: "${LOCAL_OPENAI_BASE_URL:-http://localhost:11434/v1}"
```

**Environment (preferred for secrets and machine-specific paths):**

| Variable | Purpose |
| --- | --- |
| `LOCAL_OPENAI_MODEL_ID` | Model name/tag passed to the server (`llama-3.1-8b`, `qwen2.5:7b`, etc.) |
| `LOCAL_OPENAI_BASE_URL` | API root, e.g. `http://localhost:8000/v1` |
| `LOCAL_OPENAI_API_KEY` | Only if your server requires Bearer auth |

**Remote self-hosted GPU (same provider):** set `LOCAL_OPENAI_BASE_URL` to your LAN or tunnel URL. Results remain `local_open_weight_unvalidated` unless you switch to a commercial provider.

## Ollama example

```bash
ollama serve
export LOCAL_OPENAI_MODEL_ID="qwen2.5:7b"
export LOCAL_OPENAI_BASE_URL="http://localhost:11434/v1"
python -m causal_agent_bench run --config configs/pilot_local_openai_compatible_20.yaml
```

## vLLM example

```bash
python -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Meta-Llama-3.1-8B-Instruct \
  --port 8000
export LOCAL_OPENAI_MODEL_ID="meta-llama/Meta-Llama-3.1-8B-Instruct"
export LOCAL_OPENAI_BASE_URL="http://localhost:8000/v1"
python -m causal_agent_bench run --config configs/pilot_local_openai_compatible_20.yaml
```

## Known limitations

- **Not scientific evidence by default.** Local runs are reproducibility and cost-control tooling until human validation and frozen-dataset experiments are complete.
- **JSON tool protocol.** Agents request JSON responses; smaller local models may omit tools or return invalid JSON more often than frontier APIs.
- **Hardware variance.** Latency, quantization, and batching affect trajectories; compare local models only with matched server settings.
- **No automatic cost.** `estimated_cost_usd` is usually empty unless you add custom `pricing` in the config.
- **Separate from commercial APIs.** Mixed runs (local + OpenAI/Anthropic/etc.) get `mixed_local_and_api_do_not_merge` — do not pool scores across deployment classes.
- **Oracle agents.** `scripted_oracle_agent` and similar sanity-check baselines are upper bounds, not realistic open-weight baselines.

## When to use `openai_compatible` instead

Use `provider: openai_compatible` for a **remote** OpenAI-compatible host that is not your local open-weight stack (e.g. a paid inference proxy). Use `provider: local_openai` when the intent is an open-weight/local deployment so labeling stays correct.

See also `docs/RUNNING_EXPERIMENTS.md`, `docs/COST_LATENCY.md`, and `docs/BASELINE_AGENTS.md`.
