# CAB CPU Notebook Fixture Validation

Status: **PASS** (`FIXTURE_ONLY`)

| Item | Result |
|---|---:|
| Notebooks expected | 9 |
| Notebooks parsed and validated | 9 |
| Notebooks executed offline | 9 |
| Fixture receipts | 72 |
| Runtime | 0.452 s (`MEASURED_ON_LOCAL_M4`) |
| Scientific execution | false |

Each notebook demonstrated deterministic disjoint sharding, checkpoint/resume,
idempotent reruns, merge and integrity checks, and safe fixture archives. Live
execution was refused because live flags, approval, GPU, and approved offline
model snapshots were absent. No model was loaded, no provider was called, and
no real artifact was merged or scored.
