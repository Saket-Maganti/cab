# Leaderboard Protocol

This document defines how to report Causal Agent Bench results without immediately destroying benchmark validity.

## Design principles

1. **Diagnostics over single scores.** Clean success, intervention success, and ACRS are reported together with per-family breakdowns.
2. **Oracle separation.** `scripted_oracle_agent` is a sanity-check upper bound, not a realistic agent. It is excluded from default leaderboard exports.
3. **Split discipline.** Headline claims require the held-out `test` split after disclosure rules are met. Development splits are labeled engineering-only.
4. **Provenance required.** Every row links to configs, run directories, seeds, model IDs, prompt hashes, scorer versions, and git commits when available.
5. **No fabricated evidence.** Local stub, smoke, and deterministic runs export for engineering checks only (`engineering_only: true`).

## Versioned schema

Leaderboard exports use schema id `causal_agent_bench.leaderboard.v1` (JSON Schema in `docs/leaderboard_schema_v1.json`).

### Entry fields

| Field | Description |
| --- | --- |
| `model` | Provider model id |
| `agent_scaffold` | Registered agent class / scaffold |
| `agent_run_name` | Config run name |
| `provider` | API or runtime provider |
| `submitted_at` | Run timestamp (UTC) |
| `dataset_version` | Frozen or processed bundle version |
| `eval_split` | Split filter used (`test`, `pilot`, `public_dev`, …) |
| `clean_success` | Mean success on clean instances |
| `intervention_success` | Mean success on intervention instances |
| `acrs` | Intervention success / clean success |
| `estimated_cost_usd` | Run cost aggregate when logged |
| `avg_latency_s` | Mean trajectory latency |
| `per_family_scores` | Per intervention family: success, ACRS, n |
| `retry_count` | Configured retries per agent run |
| `prompt_version_hash` / `prompt_template_hash` | Prompt disclosure |
| `evidence_scope` / `engineering_only` | Whether row may support scientific claims |

## Reporting rules

Submissions must:

1. **Exclude oracle agents** from model rankings (`scripted_oracle_agent`).
2. **Not train on held-out test** — no fine-tuning, prompt tuning, or hyperparameter search on `test`.
3. **Disclose prompts and scaffolds** — agent class, prompt files, and prompt hashes from run metadata.
4. **Disclose model version** — exact provider model string and temperature when applicable.
5. **Disclose cost and retries** — `estimated_cost_usd`, per-task cost, `retry_count`, and budget caps from config.
6. **Declare eval split** — never present `public_dev` or `pilot` numbers as final NeurIPS-scale test results.
7. **Link provenance** — include `run_dir`, `config_hash`, `git_commit`, and `scorer_versions`.

## Contamination and gaming warning

> Causal Agent Bench leaderboards are diagnostic instruments, not static product leaderboards. Training, prompt tuning, or hyperparameter search on the held-out test split, repeated test submissions, oracle-agent inclusion, undisclosed scaffold changes, or treating local stub/smoke runs as scientific evidence will invalidate comparability.

Additional risks:

- **Split leakage:** tuning on `validation` then reporting `test` without disclosure.
- **Template memorization:** training on disclosed `pilot` tasks that share templates with `heldout_templates`.
- **Judge hacking:** optimizing only for deterministic scorer proxies without human validation.
- **Cost hiding:** reporting success without latency, token, or retry budgets.

See also `docs/ETHICS_AND_LIMITATIONS.md` and `reviews/reviewer_attack_response_matrix.md` (attack 17).

## Export formats

```bash
python -m causal_agent_bench export-leaderboard --run-dir results/<run_dir>
python -m causal_agent_bench export-leaderboard --run-dir results/<run_dir> --eval-split test
```

Writes under `<run-dir>/leaderboard/` (or `--output-dir`):

- `leaderboard_v1_<eval_split>.json`
- `leaderboard_v1_<eval_split>.csv`
- `leaderboard_v1_<eval_split>.md`

## Official vs engineering exports

| `leaderboard_eligibility` | Meaning |
| --- | --- |
| `eligible_for_official_headline_if_all_reporting_rules_met` | `test` split, non-engineering evidence scope |
| `engineering_or_method_development_only` | `dev`, `pilot`, `public_dev`, `validation` |
| `engineering_export_only_not_official_submission` | stub/smoke/local unvalidated runs |
| `reserved_split_not_for_public_ranking` | `heldout_templates` |

## Related docs

- [SPLIT_PROTOCOL.md](SPLIT_PROTOCOL.md)
- [DATASET_FREEZE.md](DATASET_FREEZE.md)
- [BASELINE_AGENTS.md](BASELINE_AGENTS.md)
- [leaderboard_schema_v1.json](leaderboard_schema_v1.json)
