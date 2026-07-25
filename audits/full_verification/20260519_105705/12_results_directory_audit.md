# 12 Results Directory Audit

## Classification table

| Run dir | Type | Config/dataset | Agents/providers | Oracle? | Complete? | Scientific evidence? |
|---|---|---|---|---:|---:|---:|
| `results/20260510T110807Z_dev_20` | `oracle_sanity_check` | dev | local baselines | yes | yes | no |
| `results/20260510T165955Z_dev_20` | `oracle_sanity_check` | dev | local baselines | yes | yes | no |
| `results/20260510T110830Z_smoke` and other timestamped smoke dirs | `smoke_only` | sample/smoke | local baselines | usually yes | yes | no |
| `results/20260511T162146Z_pilot_20_multi_agent_stub` | `stub_only` | pilot v0.1 | local stub | no | yes | no |
| `results/20260519T053609Z_pilot_20_multi_agent_stub` | `stub_only` | pilot v0.1 | local stub | no | yes | no |
| `results/smoke` | `invalid_or_incomplete` | unclear | local | unclear | no | no |
| `results/smoke_run` | `invalid_or_incomplete` | unclear | local | unclear | no | no |

## Main finding

No result directory under `results/` qualifies as a real provider-backed pilot or main scientific run candidate. Existing complete runs are engineering-only, smoke-only, stub-only, or oracle sanity checks.

## Submission rule

Do not cite any existing result directory as scientific evidence for real LLM agent robustness or ranking.

