# Private packet security policy

## Never committed

The tracked repository must never contain candidate bodies, private manifests,
Stage-2 gold, accepted variants, answer contracts, recovery authorizations,
abstention labels, private reviewer mappings, encryption keys, decrypted Stage-2
files, reviewer submissions, adjudication submissions, qualification items,
qualification answer material, reviewer identity records, signed reviewer
declarations, or the reviewer assignment registry.

`private_data/` is Git-ignored. Everything sensitive lives under it, with
`0700` directories and `0600` files.

## What the tracked repository may contain

Schemas, generators, validators, public commitments, hashes, path conventions,
empty templates, non-sensitive readiness reports and fixture-only tests.

## Key management

Four secrets live outside the repository and are named only by environment
variable. No key value is ever committed, printed, logged, or bound into the
freeze.

| Variable | Protects |
|---|---|
| `CAB_PACKET_SEED_PATH` | private packet and qualification generation |
| `CAB_STAGE2_KEY_PATH` | the Stage-2 vault |
| `CAB_QUALIFICATION_KEY_PATH` | the qualification answer key |
| `CAB_COORDINATOR_KEY_PATH` | the coordinator acceptance key that seals production receipts |

Each follows the same rules:

| Property | Rule |
|---|---|
| Location | outside the repository |
| Size | exactly 32 bytes |
| Permissions | `0600` in a `0700` directory |
| If unset | the operation fails closed with an instruction |
| Inside repo | refused |
| In the freeze | the key value is never bound or hashed |

Only the seed's SHA-256 commitment, and the *ciphertext* hash of the
qualification key vault, appear in any tracked artifact.

## What the coordinator acceptance key is, and is not

Every production receipt carries a message-authentication code computed under
`$CAB_COORDINATOR_KEY_PATH`, and every production gate verifies it. This makes
receipts tamper-evident and makes coordinator acceptance explicit: a synthetic
run cannot mint a production receipt, and no flag or edit converts a fixture
artifact into genuine evidence.

It is **not** cryptographic verification of a human reviewer's identity, and
this project does not claim that it is. Reviewer declarations are content-bound,
tamper-evident records of what a reviewer stated — not signatures that a third
party could verify against an external identity.

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
