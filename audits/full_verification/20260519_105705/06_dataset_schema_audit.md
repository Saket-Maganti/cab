# 06 Dataset Schema Audit

## Files checked

Validated JSONL datasets under `data/sample/`, `data/processed/`, and `data/frozen/` using the available schema commands and one-off schema loops.

| Dataset | Base tasks | Interventions | Instances | Validation status |
|---|---:|---:|---:|---|
| `data/sample` | 3 | 6 | 9 | pass |
| `data/processed/dev_20` | 20 | 60 | 80 | pass |
| `data/processed/main_200` | 200 | 1000 | 1200 | pass |
| `data/processed/main_v0_1_500` | 500 | 2500 | 3000 | pass |
| `data/processed/pilot_v0_1` | 250 | 1250 | 1500 | pass |
| `data/processed/web_shadow_25` | 50 | 250 | 300 | pass |
| `data/frozen/pilot_v0.1` | 250 | 1250 | 1500 | pass |

## Intervention and contamination audits

- `python3 -m causal_agent_bench audit-interventions --benchmark-dir data/processed/pilot_v0_1 --output-dir audits/full_verification/20260519_105705/pilot_intervention_audit`: passed, 0 structural issues, 1000 pass and 500 warning-level validity ratings.
- `python3 -m causal_agent_bench audit-contamination --benchmark-dir data/frozen/pilot_v0.1 --output-dir audits/full_verification/20260519_105705/frozen_contamination_audit`: passed, 0 critical errors, 0 errors, 102 warnings.

## Risks

- Warning-level intervention validity should be reviewed before submission-scale use.
- `human_audit_sample.jsonl` files were not schema-validated by a dedicated schema.
- No private credentials, real emails, or real bookings were observed in validated benchmark data.

