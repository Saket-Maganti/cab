# Evidence level policy

Causal Agent Bench separates **engineering artifacts** from **scientific evidence** for paper claims.

## Canonical vocabulary

These are the only terms that may be used in run metadata, configs, and the
claim ledger. Free-text synonyms (e.g. "final", "validated", "publication
quality") are not permitted and are rejected by `scripts/audit_repo_consistency.py`.

**`scientific_evidence_level`** (config field, validated against
`SCIENTIFIC_EVIDENCE_LEVELS` in `runners/config.py`):

| Value | Meaning | Paper-eligible? |
|---|---|---|
| `default` | Unset / engineering scaffold | No |
| `preliminary_or_engineering` | Smoke, dev, stub, mock, local, zero-cost runs | No |
| `pilot_supported` | Reviewed provider-backed pilot | Pilot claims only |
| `main_supported` | Reviewed NeurIPS-scale main run | Yes (C1–C8, C10) |

**Experiment state** (see `docs/EXPERIMENT_STATE_MACHINE.md` and
`release/experiment_state.py`): `scaffold → pilot_ready → main_experiment_ready
→ submission_ready`. A run is only `submission_ready` once all readiness checks,
the release manifest, and ledger-approved claims pass; placeholder numbers are
forbidden at that state.

The mapping is one-directional: a `preliminary_or_engineering` artifact can never
promote a claim to `supported`, and reaching `submission_ready` requires at least
one `main_supported` run.

## Scientific evidence (paper-eligible)

A run may support empirical claims (C1–C8, C10) only when **all** hold:

- `completion_state=complete` and no `INCOMPLETE_RUN.json`
- `scientific_evidence=true` in run metadata
- `evidence_scope` is not mock/stub/dry-run/engineering-only
- Non-oracle agents with provider/model metadata on trajectories
- Not `not_real_llm_behavior` / not `deployment_class=mock_diagnostic_only`

Provider-backed pilots and main experiments still require human review before marking claims `supported` in `docs/claim_ledger.json`.

## Engineering-only

Includes: smoke, dev, stub agents, local preliminary, zero-cost matrix, mock diagnostic runs.

- Safe for CI, scoring tests, export **with** `--allow-engineering-only` and visible watermarks
- Must not appear as final results in abstract/conclusion without override labels

## Mock diagnostic

`mock_behavior_agent` modes are deterministic and never call paid APIs. Metadata sets `scientific_evidence=false` and `not_real_llm_behavior=true`.

## Tools

```bash
python3 -m causal_agent_bench run-health
python3 -m causal_agent_bench validate-paper-assets
python3 -m causal_agent_bench claim-evidence
python3 -m causal_agent_bench all-safety-reports
```

Reports are written under `reports/`. See `reports/INDEX.md`.
