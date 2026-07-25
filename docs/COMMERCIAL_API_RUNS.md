# Commercial API Agent Runs

This guide covers safe, repeatable runs against paid model APIs (`openai`, `anthropic`, `gemini`, `openrouter`).

Commercial runs are labeled `commercial_api_pilot_unvalidated` or `commercial_api_experiment_unvalidated` in metadata and paper tables. They are not submission evidence until human validation and claim-ledger updates are complete.

## Required config gate

Every commercial config must set:

```yaml
allow_paid_calls: true
```

The runner refuses to start if a paid provider is configured without this explicit flag. No interactive confirmation is required (CI-safe).

## Example configs

| Config | Scope |
| --- | --- |
| `configs/commercial_api_pilot_small_20.yaml` | Small pilot (20 instances, OpenAI) |
| `configs/commercial_api_pilot_medium_100.yaml` | Medium pilot (100 instances, multi-provider) |
| `configs/commercial_api_main_500.yaml` | Main-scale template (`main_v0_1_500/pilot_instances.jsonl`) |
| `configs/commercial_api_ablation_20.yaml` | Paid ablation pair (memory verification) |

## Workflow

```bash
export OPENAI_API_KEY=...
export OPENAI_MODEL_ID=gpt-4.1-mini
# optional: ANTHROPIC_API_KEY, GEMINI_API_KEY, OPENROUTER_API_KEY, etc.

python -m causal_agent_bench validate-config --config configs/commercial_api_pilot_small_20.yaml
python -m causal_agent_bench estimate-cost --config configs/commercial_api_pilot_small_20.yaml
python -m causal_agent_bench dry-run --config configs/commercial_api_pilot_small_20.yaml
python -m causal_agent_bench run --config configs/commercial_api_pilot_small_20.yaml
python -m causal_agent_bench summarize-run --run-dir results/<timestamp>_commercial_api_pilot_small_20
```

## Budget controls

- `budget_cap_usd`: run-level cap checked before each trajectory and at config validation.
- `agent_runs[].budget_cap_usd`: per-agent cap during execution.
- `task_budget_cap_usd`: per-trajectory cap inside LLM agents.

If the conservative preflight estimate from `estimate-cost` exceeds `budget_cap_usd`, `validate-config` and `run` both fail before provider calls.

During execution, run/agent caps skip remaining trajectories with `BudgetExceededError` in `errors.jsonl`.

Configure `cost_models` (or per-agent `pricing`) so estimates are meaningful:

```yaml
cost_models:
  openai:
    default:
      input_per_1m_tokens: 2.50
      output_per_1m_tokens: 10.00
```

Optional `extra.input_tokens_per_call_estimate` improves the upper-bound token estimate.

## Result metadata

`run_metadata.json` / `metadata.json` include:

- `allow_paid_calls`, `uses_paid_providers`, `evidence_scope`
- `provider_runs[]`: provider, model ID, API version, run date, sampling parameters, retries
- `cost_estimate_preflight_usd` and full `cost_estimate_preflight`
- `actual_estimated_cost_usd` and `prompt_hashes` after the run completes

Each trajectory stores provider/model, sampling parameters, per-call prompt hashes, retries, latency, and `estimated_cost_usd` (actual billed usage when the provider reports tokens).

## Redaction

- API keys stay in environment variables only.
- Saved `config.yaml` redacts secret-like keys and never writes environment dumps.
- Metadata and trajectory exports do not include `environment` / `environ` dumps or raw API keys.

## Limitations

- Cost fields are estimates unless provider token usage and pricing are configured.
- Preflight estimates are conservative upper bounds, not invoices.
- Do not compare commercial API runs directly to `local_open_weight_unvalidated` or `pilot_stub_engineering_only` rows without relabeling.
- Oracle agents remain sanity-check upper bounds, not deployable baselines.

See also `docs/COST_LATENCY.md`, `docs/RUNNING_EXPERIMENTS.md`, and `docs/OPEN_WEIGHT_LOCAL_MODELS.md`.
