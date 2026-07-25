# Filling paper results from real runs

Use this workflow **only after** a verified experiment run exists. Do not fabricate numbers or cite stub/smoke runs as scientific evidence.

## Prerequisites

The run directory must contain:

- `scores.jsonl` and `aggregate_scores.json`
- `run_metadata.json` with `config_hash`
- `instances.jsonl`
- at least one **non-oracle** agent (`scripted_oracle_agent` is excluded from main tables)
- provider/model metadata for non-oracle agents (unless `--allow-engineering-only`)
- `evidence_scope` that is not `pilot_stub_engineering_only` (unless engineering preview)

## Commands

```bash
python -m causal_agent_bench.cli run --config configs/pilot_openai_20.yaml
python -m causal_agent_bench.cli export-paper-assets --run-dir results/<timestamp>_pilot_openai_20
python3 scripts/fill_paper_from_run.py --run-dir results/<timestamp>_pilot_openai_20
make paper-check
```

Engineering preview only (not scientific):

```bash
python3 scripts/fill_paper_from_run.py \
  --run-dir results/<timestamp>_pilot_20_multi_agent_stub \
  --allow-engineering-only
```

## Outputs

| Artifact | Purpose |
|----------|---------|
| `paper/generated/*.tex` | LaTeX fragments included by `paper/sections/*.tex` |
| `docs/PAPER_EVIDENCE_MAPPING.json` | Run → claim → table/figure mapping |
| `tables/`, `figures/` | Updated when `export-paper-assets` runs with `write_global=True` |
| `docs/claim_ledger.json` | Claim statuses set to `weakened` (or `engineering_only` for stubs) |

## Claim statuses

- **`weakened`**: default for validated non-stub LLM pilots without completed human validation.
- **`engineering_only`**: stub/local engineering runs with `--allow-engineering-only`.
- **`supported`**: only with `--promote-to-supported` and a completed Table~5 human-validation export.

## Placeholder checks

```bash
make paper-check          # draft: lists placeholders, passes
make paper-submission-check  # fails until placeholders and TODO citations are resolved
```

## Language

Generated text uses cautious phrasing (“In our pilot…”, “These results suggest…”) and links `run_dir`, `config_hash`, and `evidence_scope`. Do not generalize beyond the frozen dataset version cited in the mapping file.
