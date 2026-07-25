# NeurIPS-Style Artifact Checklist

Use before claiming artifact or benchmark badges. Aligns with common NeurIPS reproducibility expectations; adapt if venue requirements differ.

## Code availability

- [ ] Public repository URL (or anonymous submission link)
- [ ] `LICENSE` covers code
- [ ] `pip install -e ".[dev]"` documented in README
- [ ] `make fast-check` passes on clean clone (Python 3.11+)

## Dataset card

- [ ] [docs/DATASET_CARD.md](DATASET_CARD.md) current
- [ ] [DATA_LICENSE.md](../DATA_LICENSE.md) for synthetic data
- [ ] Generation config + seed documented
- [ ] Held-out / dev / test splits in `splits.json`

## Benchmark card

- [ ] [docs/BENCHMARK_CARD.md](BENCHMARK_CARD.md) describes tasks, metrics, limitations
- [ ] [docs/BENCHMARK_TAXONOMY.md](BENCHMARK_TAXONOMY.md) defines skills/domains/interventions

## License

- [ ] Code license (MIT or as stated)
- [ ] Data license separate and linked
- [ ] Third-party model/API terms acknowledged in ethics section

## Environment setup

- [ ] `.env.example` without secrets
- [ ] `artifact/scripts/reproduce_deterministic.sh` runs without paid keys
- [ ] Docker/conda optional path documented if provided

## Deterministic seeds

- [ ] Generation seed in config YAML
- [ ] Run seed in experiment config
- [ ] `config_hash.txt` in each run directory

## Run configs

- [ ] All paper experiments have committed YAML under `configs/`
- [ ] `plan-run` documents trajectory counts before launch
- [ ] Mock/stub configs labeled non-scientific

## Model / provider metadata

- [ ] Model IDs, temperatures, max tokens in run metadata
- [ ] Provider registry version pinned
- [ ] Local vs API runs separated in evidence scope

## Human validation protocol

- [ ] [docs/HUMAN_VALIDATION_GUIDELINES.md](HUMAN_VALIDATION_GUIDELINES.md)
- [ ] Annotation export format documented
- [ ] Agreement metrics script tested

## Ethics / limitations

- [ ] [docs/ETHICS_AND_LIMITATIONS.md](ETHICS_AND_LIMITATIONS.md)
- [ ] No live email/booking; synthetic PII only (`example.com`)
- [ ] [docs/SECURITY_AND_PRIVACY.md](SECURITY_AND_PRIVACY.md)

## Reproducibility commands

- [ ] README quickstart + [artifact/README.md](../artifact/README.md)
- [ ] One-shot: `python3 scripts/reproduce_artifact.py --all-deterministic`
- [ ] Table/figure regeneration from complete runs only

## Expected compute / cost

- [ ] `estimate-cost` / `plan-run` outputs archived for main config
- [ ] Budget caps in YAML (`allow_paid_calls: false` by default)

## Known failure modes

- [ ] [docs/FAILURE_TAXONOMY.md](FAILURE_TAXONOMY.md)
- [ ] Failure gallery CLI documented
- [ ] Mock diagnostic suite for detector validation

## Held-out split plan

- [ ] Frozen benchmark version for leaderboard
- [ ] `audit-contamination` on release candidate
- [ ] Template held-out set documented in dataset card

## Leaderboard / gaming risk

- [ ] Test split not exposed in generation prompts
- [ ] Oracle agents excluded from leaderboards
- [ ] Submission requires frozen config hash + dataset version

## Archival release plan

- [ ] `release/release_manifest.json` updated
- [ ] Zenodo/Hugging Face dataset stub (if applicable)
- [ ] [CITATION.cff](../CITATION.cff) version bumped on release

## Pre-submission verification

```bash
make fast-check
python3 scripts/check_submission_readiness.py
python3 scripts/validate_paper_assets.py --mode submission
python3 scripts/check_claim_ledger.py --mode submission
python3 scripts/check_evidence_safety.py
```

**Current classification:** `deterministic_prototype` — not submission-ready.
