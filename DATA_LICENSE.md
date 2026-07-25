# Data License

## Synthetic benchmark data (default)

All JSONL tasks, interventions, and instances under `data/sample/`, `data/processed/`, and `data/frozen/` are **synthetic** unless explicitly marked otherwise.

- **No real personal data** — email addresses use `@example.com`; names and organizations are fictional.
- **No proprietary corpora** — mock artifacts are generated in-repo.
- **License:** MIT, same as the code (`LICENSE`), unless a future release states otherwise in `release/release_manifest.json`.

## Human-validation exports (optional)

If you run human-validation workflows, exported annotation packets may contain task text. Annotators must follow `docs/HUMAN_VALIDATION_PROTOCOL.md`. Do not commit completed annotation files with real annotator identifiers or private notes without review.

## Web shadow study (optional)

`data/web_shadow/` contains a **frozen static HTML snapshot** for offline navigation tests. It does not crawl the live web during benchmark execution.

## Redistribution

When redistributing a frozen dataset bundle, include:

- `freeze_manifest.json` with `dataset_hash`
- `dataset_card.md` / `docs/DATASET_CARD.md`
- This file

## Citation

See `CITATION.cff`.
