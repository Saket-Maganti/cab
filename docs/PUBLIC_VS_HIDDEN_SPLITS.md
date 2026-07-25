# Public vs Hidden Splits

This document summarizes which benchmark splits are **disclosed for development** versus **reserved for held-out evaluation**. Full split mechanics live in [SPLIT_PROTOCOL.md](SPLIT_PROTOCOL.md).

## Public (disclosed) splits

| Split | Intended use | Leaderboard / claims |
| --- | --- | --- |
| `dev` | CI, schema checks, debugging | Engineering only |
| `pilot` | Early experiments, failure analysis | Engineering / pilot reports only |
| `validation` | Prompt and scaffold selection | Method selection, not headline ranking |
| `public_dev` | Alias: `dev` ∪ `pilot` | Engineering only |

Content in these splits may appear in repository artifacts, papers, and ablation tables. It must **not** be presented as final held-out test performance.

## Hidden (held-out) splits

| Split | Intended use | Leaderboard / claims |
| --- | --- | --- |
| `test` | Final evaluation after methods are frozen | Eligible for headline results when reporting rules are met |
| `heldout_templates` | Reserved template variants | Not for public ranking; reduces template leakage |

Hidden splits receive **canary strings** (`metadata.contamination_canary`) during `freeze-dataset`. Audits scan public splits for canary leakage.

## Rules of thumb

1. Do not train, fine-tune, or tune prompts on `test`.
2. Limit repeated `test` submissions; treat the split as single-shot when possible.
3. Do not merge `heldout_templates` into public leaderboard exports.
4. Always disclose which `eval_split` a number comes from.
5. Run `audit-contamination` before freezing or publishing new dataset versions.

## Related documentation

- [MODEL_CONTAMINATION.md](MODEL_CONTAMINATION.md) — fingerprinting, canaries, leakage checks, audit reports
- [LEADERBOARD_PROTOCOL.md](LEADERBOARD_PROTOCOL.md) — reporting rules and gaming warnings
- [DATASET_FREEZE.md](DATASET_FREEZE.md) — freeze process and manifest fields
