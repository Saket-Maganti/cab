# Protected evaluator architecture

The public foundation defines a submission manifest, resource request, sandbox
contract, trusted task broker, output audit and signed receipt. Docker is the
target fixture runtime; CI may use the mock runtime when Docker is unavailable.

The sandbox is ephemeral, non-root and network-denied. Evaluator code is
read-only, Linux capabilities are dropped, CPU/memory/process/wall/output limits
are explicit, the environment has no secrets and private tasks mount only
inside the trusted runtime. Cleanup is verified before a receipt can pass.

The task broker resolves opaque IDs only for trusted callers. Public receipts
contain evaluator/submission/task-set hashes, declarations, aggregate resource
use, audit status and disqualification reasons. Development signatures are
marked and cannot be mistaken for production keys.

## Threat model and inspection

Attackers may submit traversal paths, symlinks, secrets, protected-like text,
unpinned images, output floods, prompt echoes, score-oracle requests, process
forks or resource-exhaustion code. Inspection bounds archive bytes and file
count, rejects traversal and links, scans content samples, checks the entry
point and requires a `sha256:` image digest in protected mode.

Protected mode additionally requires a rootless runtime, private user/PID/IPC
namespaces, seccomp, a named LSM hook, read-only root, hardened tmpfs, equal
memory and swap limits, no Docker socket, isolated output and a pinned image.

The local encrypted task store demonstrates authenticated encryption and
one-time leases but is not a KMS. The durable evaluator queue enforces
submitter quota, approval, priority, claim ownership, receipt persistence and
append-only revocation.

The signer/verifier interfaces support an external Ed25519 key loaded only from
an explicit permission-restricted path. Development HMAC keys are rejected by
protected mode. Rotation, key revocation and receipt revocation are auditable.

On an incident, stop claims, revoke affected receipts and keys, preserve logs
by hash, correct public results, and rerun only after an independent security
decision. This system is `PROTECTED_EVALUATOR_HARDENED_PILOT_READY`, not a
production evaluator.
