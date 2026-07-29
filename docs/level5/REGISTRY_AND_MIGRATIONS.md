# Registry and migrations

SQLite is the canonical Level-5 registry. Schema v1 stores typed entities,
dependencies, events and provenance. V2 adds the durable scheduler. V3 adds
review, evidence, certificates, evaluator, benchmark and plugin repositories.

## Upgrade

Inspect without mutation:

```bash
cab registry version --path .cab/registry.sqlite3
cab registry migrate --path .cab/registry.sqlite3 --dry-run
```

The plan shows ordered source/target versions, frozen checksums, preconditions,
postconditions, reversibility and backup requirements. Apply:

```bash
cab registry migrate --path .cab/registry.sqlite3 \
  --export-before-upgrade .cab/registry.pre-upgrade.json
```

Each non-reversible step performs an SQLite integrity check and consistent
backup, writes an in-progress marker, applies all statements in one immediate
transaction, records duration and checksum, verifies postconditions, then
clears the marker.

## Backup, restore and interruption

```bash
cab registry backup --path .cab/registry.sqlite3 \
  --output .cab/backups/registry.sqlite3
cab registry restore --backup .cab/backups/registry.sqlite3 \
  --path .cab/restored.sqlite3
cab registry doctor --path .cab/restored.sqlite3
```

An interrupted migration rolls back its SQL transaction and records `FAILED`
with the backup path and hash. `recover_migration()` verifies that the database
still matches the source version and that the backup is intact before retrying.
Never delete a failed marker or edit migration history by hand.

## Compatibility and corruption recovery

Downgrades and unknown future versions are rejected. Applied migration IDs and
checksums must match the source descriptors. On corruption, stop writers, copy
the database and WAL files, verify the latest backup, restore to a new path,
run `registry doctor`, then switch callers. Preserve the damaged copy.
