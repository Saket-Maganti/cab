# Artifact Evaluation Troubleshooting

## Python version

**Symptom:** `requires Python 3.11+` or import errors on older interpreters.

**Fix:**

```bash
python3 --version   # must be >= 3.11
pyenv install 3.11.9 && pyenv local 3.11.9   # if using pyenv
python3 -m pip install -e ".[dev]"
```

The reproduce script checks version via `python3 scripts/reproduce_artifact.py --check`.

## Missing package / import error

**Symptom:** `ModuleNotFoundError: causal_agent_bench` or missing `pandas`, `pytest`, etc.

**Fix:**

```bash
cd /path/to/causal-agent-bench
python3 -m pip install -e ".[dev]"
export PYTHONPATH=src   # only if you cannot install editable
python3 -m causal_agent_bench --help
```

## Provider key missing

**Symptom:** `api_key_configured: false`, dry-run warnings, or run refuses to start for `openai` / `anthropic` configs.

**Fix (optional API path only):**

```bash
export OPENAI_API_KEY=sk-...
export OPENAI_MODEL_ID=gpt-4o-mini
python3 -m causal_agent_bench list-providers
python3 -m causal_agent_bench validate-config --config configs/pilot_openai_20.yaml
```

The **deterministic path does not need any API keys** (`configs/pilot_20_multi_agent.yaml` uses `provider: local_stub`).

## Rate limit / timeout

**Symptom:** Provider errors mentioning rate limits, 429, or timeouts in `errors.jsonl`.

**Fix:**

- Reduce concurrency (default is sequential per config).
- Increase `retry_count` and `timeout` in the agent run YAML.
- Lower `max_tokens` or use a smaller pilot config (`configs/pilot_openai_20.yaml` vs `main_500`).
- Re-run with `--resume` only after confirming the same `config_hash` in `run_metadata.json`.

## Malformed result / parser failures

**Symptom:** Trajectories show `parser_status: failed`, empty tool calls, or invalid JSON actions.

**Fix:**

1. Inspect `trajectories.jsonl` for `raw_model_output` and `parsed_action`.
2. Confirm the agent uses the canonical JSON protocol ([docs/TOOL_CALL_PROTOCOL.md](../docs/TOOL_CALL_PROTOCOL.md)).
3. For `local_stub`, failures often indicate config/agent mismatch — re-run `validate-config`.
4. For real models, try lowering temperature to `0.0` and switching to a model with stronger JSON tool compliance.

## Missing benchmark / instances file

**Symptom:** `Benchmark file is missing` for `dev_20` or pilot paths.

**Fix:**

```bash
python3 -m causal_agent_bench generate --config configs/dev_20_tasks.yaml
python3 -m causal_agent_bench generate --config configs/generate_pilot_v0_1.yaml
python3 scripts/reproduce_artifact.py --check
```

Pilot-stub uses `data/processed/pilot_v0_1/pilot_20_instances.jsonl` (included in repo when pilot data is present).

## Run directory not found (table2 / figure2)

**Symptom:** `no run directory found; pass --run-dir`.

**Fix:**

```bash
python3 scripts/reproduce_artifact.py --step pilot-stub
python3 scripts/reproduce_artifact.py --step table2 --run-dir results/<timestamp>_pilot_20_multi_agent_stub
```

## Table or figure file missing after export

**Symptom:** `expected file missing: tables/table2_main_agent_performance.csv`.

**Fix:**

```bash
python3 -m causal_agent_bench export-paper-assets --run-dir results/<run_dir>
ls -la tables/ figures/
```

Export requires a completed scored run (`scores.jsonl` non-empty). Re-run scoring if needed:

```bash
python3 -m causal_agent_bench score --run-dir results/<run_dir>
```

## Claim ledger / paper fill rejected stub run

**Symptom:** `fill-paper-from-run` refuses or sets `engineering_only`.

**Expected:** Stub runs must not be cited as scientific evidence. Use a verified non-oracle LLM run for paper claims.

## Still stuck?

```bash
python3 -m causal_agent_bench doctor
python3 scripts/reproduce_artifact.py --check
make release-check
```

Open an issue with: Python version, OS, command run, and the last 20 lines of stderr (redact any API keys).
