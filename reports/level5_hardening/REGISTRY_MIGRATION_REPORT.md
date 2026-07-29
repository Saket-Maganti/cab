# Registry migration report

Status: passed.

The canonical SQLite registry now has three ordered schemas:

| Migration | Edge | Statements | SHA-256 commitment | Backup |
|---|---:|---:|---|---|
| `registry-v1-fixture-foundation` | 0→1 | 9 | `69b08a2a5e9f4632c7b1fbb2dbe30a0bc9840fdbbf6420a69351b44ae2a0b5de` | bootstrap |
| `registry-v2-operational-scheduler` | 1→2 | 16 | `d16d7a464aeed7c185612c4e3771e107666c3c38ac425ddb5e1a9e4c5c09ac26` | required |
| `registry-v3-review-evidence-evaluator` | 2→3 | 40 | `816d9aee3e18cdac061c125df1db0bca5f1269e6a39683cc065434d4354b1690` | required |

Tests created a v1 database, planned v2/v3, exported its pre-upgrade state,
interrupted v2 after one statement, verified rollback and the durable failure
marker, recovered, applied v3, checked postconditions, and rejected a tampered
checksum. Queue, review, evidence, evaluator, benchmark and plugin records
persist in the same registry. Append-only and immutable tables have database
triggers, not application-only assertions.

The migration CLI supports version, dry-run plan, migrate, backup, restore and
doctor operations. Downgrades and unknown targets fail closed.
