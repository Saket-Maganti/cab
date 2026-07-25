# Final Audit Summary

## Executive verdict

Classification: **deterministic prototype working**.

The repository installs with `python3`, passes the full test suite, validates/generates datasets, and runs the local-stub pipeline end to end. It is **not** provider-pilot ready in this environment, **not** main-experiment ready, and **not** submission ready. No current artifact supports scientific claims about real LLM agent robustness.

## Current scientific status

Supported:

- Engineering-only reproducibility of the local deterministic pipeline.
- Pilot dataset generation reproducibility for `configs/generate_pilot_v0_1.yaml`.
- Schema validation for sample/processed/frozen benchmark data.
- Security and claim-ledger checks.

Not supported:

- Real LLM robustness claims.
- Model ranking claims.
- ACRS findings for provider-backed agents.
- Human validation claims.
- NeurIPS-scale experiment claims.

Engineering-only:

- Smoke runs, local-stub runs, deterministic analysis outputs, and oracle sanity checks.

Placeholder:

- Paper generated placeholders `[N]`, `[M]`, `[K]`, `[X]`, `[rho]`, `[domains]`, and `[main finding placeholder]`.

Must not be claimed:

- That clean success overstates real-agent skill.
- That particular provider models are more robust.
- That self-checking/planner agents improve ACRS.
- That results are submission-ready.

## Verification checklist

| Area | Status | Evidence | Blocking issues |
|---|---|---|---|
| install | pass with `python3` | `02_environment_check.md` | bare `python` pyenv failure |
| tests | pass | `244 passed, 1 skipped` | clean-checkout CI not proven |
| CLI | pass | `04_cli_verification.md` | provider commands setup-dependent |
| configs | mixed | `05_config_audit.md` | provider model IDs/API keys/pricing missing |
| data validation | pass | `06_dataset_schema_audit.md` | human audit sample schema missing |
| generation reproducibility | pass | `07_generation_reproducibility.md` | versioning discipline required for future mutations |
| tools | pass | `08_tool_environment_audit.md` | keep live APIs out of simulated tools |
| agents | mixed | `09_agent_audit.md` | oracle must stay excluded |
| provider readiness | fail for real providers | `10_provider_readiness.md` | no external provider setup |
| run pipeline | pass engineering-only | `11_run_pipeline_audit.md` | local-stub only |
| results directories | not scientific | `12_results_directory_audit.md` | no provider-backed run |
| scoring | pass | `13_metrics_and_scoring_audit.md` | scientific validity needs real data |
| statistics | pass engineering-only | `14_statistical_analysis_audit.md` | small n/local stub only |
| paper placeholders | fail for submission | `15_paper_claims_audit.md` | unresolved placeholders |
| claim ledger | pass structurally | `15_paper_claims_audit.md` | scientific claims remain planned |
| bibliography | pass draft checks | `17_bibliography_audit.md` | final citation relevance pass needed |
| README | mostly pass | `18_readme_audit.md` | prefer/document `python3` |
| security/privacy | pass | `19_security_privacy_audit.md` | recheck after real provider runs |
| reproducibility | pass engineering-only | `20_reproducibility_audit.md` | lock/clean checkout/provider runs missing |

## Critical blockers

P0 before any real run:

- Configure provider model IDs, API keys, pricing, budget caps, and explicit paid-call approval.
- Keep oracle agents out of realistic comparison configs.
- Resolve missing mini-study datasets if those configs are used.

P1 before paper claims:

- Run non-oracle provider pilot and main experiments.
- Link every empirical claim to run artifacts in `docs/claim_ledger.json`.
- Fill paper values only from verified run-local assets.
- Add or complete human validation before claiming diagnostic reliability.

P2 before submission:

- Fix or document the pyenv/bare-`python` issue.
- Prove clean-checkout reproduction.
- Complete sentence-level citation relevance review.
- Add schema coverage for human audit samples.

P3:

- Reduce generated artifact churn.
- Add stronger README distinctions between scaffold, engineering, pilot, and main results.

## Exact next commands

```bash
python3 -m pytest -q
python3 -m causal_agent_bench list-providers
python3 -m causal_agent_bench validate-config --config configs/pilot_multi_provider_20.yaml
python3 -m causal_agent_bench dry-run --config configs/pilot_multi_provider_20.yaml --output-dir results/dry_runs
python3 -m causal_agent_bench estimate-cost --config configs/pilot_multi_provider_20.yaml
```

Only after provider setup, pricing, and explicit paid-call approval:

```bash
python3 -m causal_agent_bench run --config configs/pilot_multi_provider_20.yaml
python3 -m causal_agent_bench score --run-dir results/<run_dir>
python3 -m causal_agent_bench analyze --run-dir results/<run_dir>
python3 -m causal_agent_bench export-paper-assets --run-dir results/<run_dir>
python3 scripts/check_claim_ledger.py
python3 scripts/check_paper_placeholders.py --mode submission
```

## Exact next Codex tasks

- Configure and validate a tiny non-oracle provider pilot without running paid calls until cost is known.
- Add schema validation for `human_audit_sample.jsonl`.
- Update claim ledger only after real provider artifacts exist.
- Perform a clean-checkout reproduction dry run.
- Complete citation sentence relevance review.

## Files changed during this audit

- `src/causal_agent_bench/phase2.py`: deterministic hash exclusion for contamination reports; provider-readiness cost fix; ablation-matrix validation support.
- `configs/web_shadow_api_stub.yaml`: corrected benchmark directory field.
- `configs/web_shadow_web_stub.yaml`: corrected benchmark directory field.
- `release/release_manifest.json`: refreshed bundle hash after asset check.
- `figures/`, `tables/`, and `results/20260511T162146Z_pilot_20_multi_agent_stub/paper_assets/`: regenerated engineering-only assets required by existing checks.
- `results/20260519T053609Z_pilot_20_multi_agent_stub/`: fresh local-stub verification run.
- `audits/full_verification/20260519_105705/`: audit evidence and reports.

## Final recommendation

- Safe to continue: yes.
- Ready for real LLM pilot: not yet in this environment.
- Ready for human validation: only after a real pilot or clearly scoped engineering sample is chosen.
- Ready for NeurIPS-scale experiments: no.
- Paper allowed to claim scientific results yet: no.

Suggested commit message if these changes are committed later:

`audit: verify CausalAgentBench pipeline and claims integrity`

