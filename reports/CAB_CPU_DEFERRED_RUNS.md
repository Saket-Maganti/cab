# CAB CPU Deferred Runs

All currently legal CPU runs were completed. Evidence-dependent CPU runs
remain blocked because genuine human or GPU outputs do not yet exist.

Commands containing angle-bracket parameters are exact command templates; the
parameters must come from a genuine frozen manifest or audited run and must
not be guessed.

## After genuine human review and C10

Prerequisite: two independent qualified reviewers complete every locked
Compact-20 review group, disagreements are adjudicated, and the validator
returns C10 `PASS`.

```bash
python3 scripts/validate_cab_human_reviews.py \
  --review-dir data/human_validation/compact20_real_review
python3 scripts/check_iclr_preexecution_readiness.py \
  --write-json reports/iclr_preexecution_readiness_post_c10.json
PYTHONPATH=src python3 scripts/cab_resource_preflight.py \
  --worker-mode low_memory --bootstrap-mode pilot \
  --output reports/cab_resource_preflight_post_c10.json
```

Only after those commands pass may the passing slice be frozen with the
review-derived input and version:

```bash
python3 -m causal_agent_bench freeze-dataset \
  --source-dir <REVIEW_DERIVED_PASSING_SLICE_DIR> \
  --version <PREREGISTERED_COMPACT20_VERSION>
```

Deferred outputs: slice lock, frozen-run manifest, post-C10 preflight, and
exact Compact-20 trajectory plan.

## After Compact-20 GPU execution

Prerequisite: complete, disjoint, hash-matching real shards from the frozen
Compact-20 manifest.

```bash
python3 -m causal_agent_bench batch-merge \
  --batch-dir <COMPACT20_BATCH_DIR> --output-dir <COMPACT20_MERGED_RUN_DIR>
python3 -m causal_agent_bench score --run-dir <COMPACT20_MERGED_RUN_DIR>
python3 -m causal_agent_bench failure-report \
  --run-dir <COMPACT20_MERGED_RUN_DIR>
python3 -m causal_agent_bench analyze \
  --run-dir <COMPACT20_MERGED_RUN_DIR>
python3 -m causal_agent_bench export-human-validation \
  --run-dir <COMPACT20_MERGED_RUN_DIR> --output-dir <BLINDED_SCORER_AUDIT_DIR>
```

Deferred outputs: merge, rescoring, blinded scorer-sanity packet, paired
preliminary analysis, 1,000-replicate clustered bootstrap, and audit
promotion. Raw trajectories must remain immutable.

## After Scale-100 and naturalistic GPU execution

Prerequisite: both real studies have passed completeness, scorer, provenance,
privacy, missingness, and postrun audit gates.

```bash
python3 -m causal_agent_bench batch-merge \
  --batch-dir <SCALE100_BATCH_DIR> --output-dir <SCALE100_MERGED_RUN_DIR>
python3 -m causal_agent_bench batch-merge \
  --batch-dir <NATURALISTIC_BATCH_DIR> --output-dir <NATURALISTIC_MERGED_RUN_DIR>
python3 -m causal_agent_bench score --run-dir <SCALE100_MERGED_RUN_DIR>
python3 -m causal_agent_bench score --run-dir <NATURALISTIC_MERGED_RUN_DIR>
python3 -m causal_agent_bench analyze --run-dir <SCALE100_MERGED_RUN_DIR>
python3 -m causal_agent_bench analyze --run-dir <NATURALISTIC_MERGED_RUN_DIR>
PYTHONPATH=src python3 scripts/cab_resource_preflight.py \
  --bootstrap-mode final --output reports/cab_resource_preflight_final.json
```

Deferred analyses: 10,000-replicate resumable bootstrap, rank uncertainty,
mixed effects, RAAC effect/overhead, naturalistic predictive validity,
scorer-error sensitivity, and claim promotion. RAAC ablations and Main
expansion remain model-execution stages and were not run.

## Final empirical release

Prerequisite: audited real evidence and individually eligible paper assets.

```bash
PYTHONPATH=src python3 scripts/export_phase15_paper_assets.py \
  --source main=<AUDITED_MAIN_ASSET_DIR> \
  --source naturalistic=<AUDITED_NATURALISTIC_ASSET_DIR> \
  --source ablation=<AUDITED_ABLATION_ASSET_DIR> \
  --source scorer_validation=<AUDITED_SCORER_VALIDATION_ASSET_DIR> \
  --source intervention_validity=<AUDITED_INTERVENTION_VALIDITY_ASSET_DIR> \
  --output-dir <NEW_PHASE15_OUTPUT_DIR>
python3 scripts/validate_paper_assets.py --mode submission
python3 scripts/check_claim_ledger.py --mode submission
make release-check
make artifact-check
```

The final submission bundle must still exclude private payloads and must refuse
unsupported claims or fixture-derived results.
