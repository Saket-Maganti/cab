# Cryptographic Approval Report

Status: `CAB_CRYPTOGRAPHIC_APPROVAL_GATE_READY`.

The committed fixture receipt verifies: `true`.
It uses Ed25519 and binds candidate, Stage-1, Stage-2, fixture C10, executable
reachability, gold, isolation, task-pack, and intervention-pack hashes, plus
scorer version/policy set, system identity, code revision, evidence time,
exclusions, nonce, expiry, issuer, and the hashed revocation registry.

The fixture issuer is trusted only for `fixture`; replay as `scientific` fails.
No production issuer or signing secret is committed, so live execution remains
blocked until genuine C10 and a separately trusted scientific receipt exist.
