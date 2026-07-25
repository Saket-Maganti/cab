# Prompting And Scaffolding Ablations

This guide documents the ablation scaffold for testing whether simple prompting and tool-use instructions improve robustness.

These configs are experiment wiring, not final evidence. The local-stub variants under `configs/ablations/` exercise reproducibility, prompt hashing, table export, and scorer plumbing. Provider-backed ablations must cite the run directory, `config.yaml`, config hash, seed, model IDs, prompt hashes, scorer version, and git commit before any paper claim can use them.

## Factors

Each pair holds the base agent, benchmark, provider, model, seed, and run settings fixed, then changes one intended factor.

| Pair | Reference | Treatment | Config |
| --- | --- | --- | --- |
| Direct vs ReAct-style prompting | direct base prompt | ReAct-style addendum | `configs/ablations/direct_vs_react_local_stub.yaml` |
| Explicit plan | no explicit planning scaffold | planning addendum | `configs/ablations/explicit_plan_local_stub.yaml` |
| Self-check before final answer | no self-check scaffold | self-check addendum | `configs/ablations/self_check_local_stub.yaml` |
| Memory verification | no memory-verification scaffold | memory-verification addendum | `configs/ablations/memory_verification_local_stub.yaml` |
| Tool-failure recovery | no recovery scaffold | recovery addendum | `configs/ablations/tool_failure_recovery_local_stub.yaml` |
| Contradiction resolution | no contradiction scaffold | contradiction-resolution addendum | `configs/ablations/contradiction_resolution_local_stub.yaml` |
| Uncertainty and abstention | no abstention scaffold | uncertainty addendum | `configs/ablations/uncertainty_abstention_local_stub.yaml` |
| Step budget reminder | no budget reminder | budget addendum plus runner reminder flag | `configs/ablations/step_budget_reminder_local_stub.yaml` |
| Tool descriptions | detailed tool schemas | short tool summaries | `configs/ablations/tool_description_detail_local_stub.yaml` |
| Action protocol | JSON-only action object | flexible text with one parseable JSON action | `configs/ablations/action_protocol_local_stub.yaml` |

Prompt fragments live in `prompts/agents/ablations/`. The shared baseline prompt is `prompts/agents/ablations/base_tool_agent.md`, and the minimal common safety layer is `prompts/agents/system_safety_ablation_minimal.md`.

## Running

Validate every local-stub ablation config:

```bash
for config in configs/ablations/*_local_stub.yaml; do
  python -m causal_agent_bench validate-config --config "$config"
done
```

Run one ablation smoke check:

```bash
python -m causal_agent_bench run --config configs/ablations/memory_verification_local_stub.yaml
```

Export the ablation table from a completed run:

```bash
python -m causal_agent_bench export-ablation-table --run-dir results/<run_dir>
python scripts/export_ablation_table.py --run-dir results/<run_dir>
```

The broader paper asset exporter also writes Table 4:

```bash
python -m causal_agent_bench export-paper-assets --run-dir results/<run_dir>
```

## Logged Metadata

Each ablation trajectory stores:

- `ablation`: `pair_id`, `factor`, `level`, and `comparison_role`.
- `prompt_version_hash`: hash of the effective prompt, safety prompt, tool protocol, action protocol, tool-description mode, budget reminder flag, and ablation metadata.
- `prompt_template_hash`: hash of the base prompt and addendum text.
- `prompt_files`: base prompt, addendum, safety prompt, and tool protocol files.
- `action_protocol`, `tool_description_mode`, and `step_budget_reminder`.
- Provider/model, token usage, latency, estimated cost, seed, run key, and max steps when available.

Provider keys stay outside config files and must be supplied through environment variables only.

## Table 4

`table4_ablation_results` fills only when at least one trajectory includes ablation metadata. Otherwise it remains a placeholder that says the ablation has not been run.

The table reports:

- Success rate, clean success reference, intervention success reference, ACRS, absolute degradation, and relative degradation.
- Cost, latency, tool overuse, required-tool recall, and trajectory faithfulness.
- One overall row per ablation level plus intervention-family rows when intervention families are present.
- Deltas against the `comparison_role: reference` row within each pair and intervention family.
- Reproducibility columns: run directory, config hash, seed, model IDs, prompt hashes, scorer version, git commit, dataset version, and timestamp when available.

Do not interpret local-stub rows as scientific support for a prompting claim. They are engineering checks for the ablation machinery.

## Ablation matrix runner

For systematic sweeps without hand-editing one YAML per cell, use the matrix config format and runner.

Matrix factors (each cell sets one level per factor):

- `prompt_style` (`direct`, `react`)
- `self_check` (`off`, `on`)
- `memory_verification` (`off`, `on`)
- `recovery_instruction` (`off`, `on`)
- `contradiction_instruction` (`off`, `on`)
- `uncertainty_instruction` (`off`, `on`)

`base_model` holds provider, model, temperature, token limits, and budget caps. Example: `configs/ablation_matrix_local_stub.yaml`.

Expansion strategies:

- `baseline_plus_one` — baseline (all first levels) plus one-at-a-time toggles
- `full_factorial` — Cartesian product (use safeguards)
- `explicit` — list cells manually in `cells:`

Plan only (dry-run; writes per-cell configs and cost estimate):

```bash
python -m causal_agent_bench ablation-matrix --config configs/ablation_matrix_local_stub.yaml
python scripts/run_ablation_matrix.py --config configs/ablation_matrix_local_stub.yaml
```

Execute all cells with `local_stub` (engineering-only, not scientific evidence):

```bash
python -m causal_agent_bench ablation-matrix --config configs/ablation_matrix_local_stub.yaml --execute
```

Re-aggregate after manual edits:

```bash
python -m causal_agent_bench ablation-matrix --config configs/ablation_matrix_local_stub.yaml --aggregate-only
```

Exports land under `<output_dir>/<run_name>/exports/`:

- `ablation_matrix_table.{csv,md,tex}`
- `ablation_matrix_acrs_heatmap.{png,pdf}` (when ACRS is available)
- `ablation_matrix_aggregate.{json,md}`

Safeguards in the matrix YAML:

- `max_cells` — abort if expansion exceeds this count
- `max_estimated_cost_usd` — abort when summed cell cost estimates exceed the cap
- `block_paid_providers_without_flag` — require `base_model.allow_paid_calls: true` for paid providers
- `require_dry_run_before_execute` — two-step workflow: plan first, then `--execute` without replanning

Aggregated columns include clean success, intervention success, ACRS, estimated cost, latency, and tool overuse (`unnecessary_tool_call_rate`), plus run directory and config hash when scoring completed.
