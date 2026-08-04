# Private packet security policy

## Never committed

The tracked repository must never contain candidate bodies, private manifests,
Stage-2 gold, accepted variants, answer contracts, recovery authorizations,
abstention labels, private reviewer mappings, encryption keys, decrypted Stage-2
files, or reviewer submissions.

`private_data/` is Git-ignored. Everything sensitive lives under it, with
`0700` directories and `0600` files.

## What the tracked repository may contain

Schemas, generators, validators, public commitments, hashes, path conventions,
empty templates, non-sensitive readiness reports and fixture-only tests.

## Key management

| Property | Rule |
|---|---|
| Location | outside the repository, at `$CAB_STAGE2_KEY_PATH` |
| Size | exactly 32 bytes |
| Permissions | `0600` in a `0700` directory |
| If unset | every vault operation fails closed with an instruction |
| Inside repo | refused |
| In the freeze | the key value is never bound or hashed |

The generation seed follows the same rules via `CAB_PACKET_SEED_PATH`. Only its
SHA-256 commitment appears in any tracked artifact.

## Output discipline

No command, log, report, commit message, test name or summary may print a
private prompt, a private artifact, an expected answer, a route label, an
accepted variant, a private identifier or Stage-2 content. Reports carry
aggregate counts, statuses, matrices and hashes.

The Stage-1 leakage scanner deliberately reports only counts. When it finds a
leak it says how many and in which package; it never echoes the leaked value,
because a leak report that quotes the secret is itself a leak.

## Retired material

Every previously exposed or scientifically invalid packet is registered in
`reports/reviewer_ready_v2/RETIRED_PACKET_REGISTRY.json` and rejected in code at
ingestion, C10, slice lock and execution authorization. Rejection is by identity
— public commitment and Stage-1 package hashes — so renaming a retired packet
does not get it past the gate.

## Backups

Private backups belong outside the repository, under a timestamped owner-only
directory such as `~/.cab/private_backups/<timestamp>/`, with a SHA-256
inventory. Never back private material up into the working tree, and never into
any cloud-synced folder that is not encrypted at rest.
