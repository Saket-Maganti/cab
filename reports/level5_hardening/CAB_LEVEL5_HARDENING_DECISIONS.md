# CAB Level-5 hardening decisions

## D001 — Extend canonical storage

All durable hardening tables and repositories use the canonical
`SQLiteRegistry` database and migration framework. Private human identity
details and encrypted task bodies use separate adapter boundaries and remain
outside public exports.

## D002 — Preserve the fixture scheduler

`LocalScheduler` remains as the compatible deterministic vertical-slice API.
Operational concurrent scheduling is added to the same execution module and
uses the same manifests, CAS and registry.

## D003 — SQLite coordinator

The hardened scheduler uses a primary-process coordinator, SQLite-backed queue
and thread workers. Leases and heartbeats are durable and future-compatible
with remote workers.

## D004 — No provider execution

Provider backends remain disabled unless a future caller supplies explicit
approval, credentials and budget. This pass executes no model or paid-provider
call.

## D005 — Honest unavailable controls

Container attacks and optional external tools are reported `NOT_EXECUTED` when
their runtime is unavailable. Manual-policy controls do not count as automatic
mitigation.

## D006 — Development cryptography is visibly scoped

Fixture HMAC remains available only through an explicit development signer.
Protected mode requires a non-development signer and never generates or stores
a production private key.

## D007 — Lease duration and heartbeat policy

The mandatory stress campaign exposed false stale reclamation when an
aggressive 250 ms lease met eight-worker SQLite contention. Operational stress
uses a 10-second lease, while stale recovery remains a separately forced and
verified case. Workers start heartbeat threads only when their resource
estimate can cross a heartbeat interval. Lease fencing is monotonic across
restarts because its generation is the durable attempt number.

## D008 — Unavailable containers are not evidence

The evaluator campaign enumerates all twelve container attacks but records them
`NOT_EXECUTED` when the local image/daemon is unavailable. Deterministic mocked
subprocess tests validate the classifier and cleanup orchestration, but they are
not reported as a real container pilot. Clean-room container reproduction uses
the same honest classification.
