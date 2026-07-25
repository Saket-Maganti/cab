# Next Steps

## Immediate engineering fixes

- [ ] Add CI that runs `python3 -m pytest -q`, `python3 -m causal_agent_bench doctor`, and draft paper placeholder checks.
- [ ] Add a small fixture for each intervention family to guard against generator regressions.
- [ ] Add stronger trajectory schema checks for observation redaction and saved agent thoughts.
- [ ] Add a clean-clone reproducibility log from a second machine or CI runner.

## Pilot experiment milestone

- [ ] Select 3-5 non-oracle agents or LLM adapters for a small paid/free pilot.
- [ ] Freeze `data/processed/dev_20` or regenerate with a documented seed and config hash.
- [ ] Run the pilot with `configs/dev_20_run.yaml` and archive the run directory.
- [ ] Audit 25-50 trajectories for scoring errors and intervention realism.
- [ ] Update `docs/claim_ledger.json` only with evidence paths that exist.

## NeurIPS-scale milestone

- [ ] Finalize task/intervention generation rules and lock benchmark version `v0.1`.
- [ ] Run the main 200-task experiment with model/version metadata and cost logs.
- [ ] Run human validation for intervention validity and trajectory diagnostic agreement.
- [ ] Add statistical uncertainty to all main tables and figures.
- [ ] Replace paper placeholders only after evidence exists and the claim ledger passes in submission mode.
