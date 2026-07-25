# Milestones

## M0: Scaffold Health

- [x] Package imports and CLI help work locally.
- [x] Sample schema validation works.
- [x] Smoke run executes without paid services.
- [x] Tests, lint, doctor, paper draft check, and claim-ledger check run locally.
- [x] Paper placeholders are visible in draft mode and blocked in submission mode.

## M1: 20-Task Provider Pilot

- [x] Pilot configs exist for local stub and provider-backed runs.
- [x] `dry-run` shows planned trajectories without provider calls.
- [x] `estimate-cost` provides conservative cost bounds.
- [ ] API keys and model IDs configured through environment variables.
- [ ] 20-base-task provider-backed run completed with non-oracle agents.
- [ ] Run summarized, analyzed, and exported to paper assets.
- [ ] Claim ledger updated as pilot or engineering evidence only.

## M2: 100-Task Multi-Provider Pilot

- [x] Config placeholder exists for `pilot_100_multi_agent`.
- [ ] 100-base-task dataset split validated.
- [ ] Multi-provider budget approved before execution.
- [ ] Provider-backed run completed without oracle in main ranking table.
- [ ] Bootstrap intervals, paired comparisons, ranking instability, and error cases reviewed.
- [ ] Failure categories audited for metric false positives.

## M3: Human Validation

- [x] Human audit sample generation exists for `pilot_v0.1`.
- [ ] Annotation protocol finalized.
- [ ] Reviewers judge task clarity, label validity, goal preservation, factor isolation, and ambiguity.
- [ ] Agreement and adjudication procedure reported.
- [ ] Claim C10 remains planned until this milestone is complete.

## M4: Frozen Benchmark v1.0

- [x] `freeze-dataset` command creates a manifest for generated datasets.
- [ ] Dataset version and split policy finalized.
- [ ] Intervention audit warnings resolved or documented.
- [ ] Frozen files written under a versioned release directory.
- [ ] Dataset and benchmark cards updated for v1.0.

## M5: NeurIPS-Scale Run

- [ ] Main benchmark scale and agent/model list finalized.
- [ ] Cost, latency, and provider-version reporting locked.
- [ ] Non-oracle LLM-backed runs completed.
- [ ] Human validation complete.
- [ ] Claim ledger updated with artifact-backed evidence paths.
- [ ] Paper placeholders replaced only where evidence exists.
- [ ] `make paper-submission-check` passes.
