# 07 Generation Reproducibility

## Config used

- Config: `configs/generate_pilot_v0_1.yaml`
- Seed: `20270511`
- Version: `pilot_v0.1`
- Output path: `data/processed/pilot_v0_1`

## Commands

- `python3 -m causal_agent_bench generate --config configs/generate_pilot_v0_1.yaml`
- `python3 -m causal_agent_bench validate data/processed/pilot_v0_1/instances.jsonl --schema instances`
- Reran generation with the same seed into `audits/full_verification/20260519_105705/generation_repro/pilot_v0_1_rerun`.

## Counts

- Base tasks: 250
- Interventions: 1250
- Instances: 1500
- Intervention families: 10, 125 interventions each
- Domains: 8, approximately balanced

## Reproducibility result

Byte-for-byte hashes matched for the canonical output and rerun files checked: `base_tasks.jsonl`, `interventions.jsonl`, `instances.jsonl`, `splits.json`, split JSONLs, `human_audit_sample.jsonl`, and `quality_report.md`.

## Warnings

The generation pipeline is reproducible for this seed/config. Scientific claims still require non-oracle model runs over the generated data.

