# CAB Level-5 capability matrix

Status values are `READY`, `FIXTURE_READY`, `BLOCKED_GENUINE_INPUT` and `FUTURE`.

| Capability | Status | Validation |
|---|---|---|
| Scientific kernel | READY | Existing provider-free suite |
| Transactional registry | READY | Rollback, concurrency, backup/restore, tamper tests |
| Benchmark factory/compiler | FIXTURE_READY | Public authoring vertical slice and rejection tests |
| Execution OS | FIXTURE_READY | 20 units, interrupt at 7, resume to 20 |
| Artifact store | READY | Atomic SHA-256 CAS, compression, corruption and bundle tests |
| Observability/reliability | FIXTURE_READY | 18 deterministic fault classes |
| Human review OS | READY | Local app, immutable ledger, assignments and agreement |
| Genuine C10 | BLOCKED_GENUINE_INPUT | Zero genuine human rows |
| Protected evaluator | FIXTURE_READY | Mock sandbox contract and malicious fixtures |
| Public SDK/CLI/plugins | FIXTURE_READY | Import, discovery and CLI tests |
| Evidence graph/certification | FIXTURE_READY | Cycle, transition, redaction and tamper tests |
| Internal reproduction | FIXTURE_READY | Provider-free vertical-slice receipt |
| Independent reproduction | BLOCKED_GENUINE_INPUT | Zero external attestations |
| Protected evaluator pilot | BLOCKED_GENUINE_INPUT | Zero external pilot receipts |
| Community pilot | BLOCKED_GENUINE_INPUT | Zero external pilot receipts |
| Live model evidence | BLOCKED_GENUINE_INPUT | C10 and live approval absent |
| PostgreSQL/cloud adapters | FUTURE | SQLite/filesystem are the supported local defaults |

The highest truthful build-now state is
`CAB_LEVEL5_PLATFORM_FOUNDATION_COMPLETE`, accompanied by all unresolved
genuine-evidence blocker states. `CAB_LEVEL5_COMPLETE` is forbidden at this
stage.
