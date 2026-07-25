# Split Protocol

Causal Agent Bench uses **disjoint base-task splits** under policy `release_disjoint_v1`. Each split is defined in `splits.json` next to a frozen dataset bundle (for example `data/frozen/pilot_v0.1/splits.json`).

## Split names

| Split | Role | Public visibility | Leaderboard use |
| --- | --- | --- | --- |
| `dev` | Pipeline checks, unit-style debugging | Disclosed in repo | Engineering only |
| `pilot` | Early method development, failure analysis | Disclosed in repo | Engineering / pilot reports only |
| `public_dev` | Alias: union of `dev` + `pilot` | Disclosed | Engineering only |
| `validation` | Prompt/scaffold selection, ablations | Disclosed | Method selection, not headline ranking |
| `test` | Final held-back evaluation | **Hidden instance IDs until release** | Official headline split when all reporting rules are met |
| `heldout_templates` | Reserved template variants | Disclosed policy, reserved tasks | **Not** for public ranking |

## Public vs hidden

- **Public / disclosed splits:** `dev`, `pilot`, `validation`, and the combined alias `public_dev`. These support reproducible development but must not be treated as final scientific evidence on their own.
- **Hidden / held-out:** `test` is the primary held-back evaluation split. Do not train, tune prompts, or select hyperparameters using `test` labels or trajectories.
- **Reserved:** `heldout_templates` reduces template leakage across releases. Do not merge it into public leaderboard exports.

## Disjointness guarantees

Frozen bundles record:

- disjoint `base_task_ids` per split;
- leakage checks for repeated instructions, duplicate ground-truth objects, and held-out template keys (`freeze_manifest.json`, `docs/DATASET_FREEZE.md`).

## Exporting metrics on a split

```bash
python -m causal_agent_bench export-leaderboard \
  --run-dir results/<timestamp>_<run_name> \
  --eval-split pilot

python -m causal_agent_bench export-leaderboard \
  --run-dir results/<timestamp>_<run_name> \
  --eval-split test \
  --splits-path data/frozen/pilot_v0.1/splits.json
```

Use `--eval-split unfiltered` only when the run already targets a single split file (for example `pilot_20_instances.jsonl`) and you document that scope in the submission.

## Versioning

Every export must record:

- `dataset_version` (benchmark bundle id);
- `split_policy_name` from `splits.json`;
- `eval_split` used for filtering;
- run provenance (`run_dir`, `config_hash`, `git_commit`, `seed`).

When the benchmark version changes, prior leaderboard rows are **not** comparable without explicit recalibration.

## Related docs

- [PUBLIC_VS_HIDDEN_SPLITS.md](PUBLIC_VS_HIDDEN_SPLITS.md)
- [MODEL_CONTAMINATION.md](MODEL_CONTAMINATION.md)
- [DATASET_FREEZE.md](DATASET_FREEZE.md)
- [LEADERBOARD_PROTOCOL.md](LEADERBOARD_PROTOCOL.md)
