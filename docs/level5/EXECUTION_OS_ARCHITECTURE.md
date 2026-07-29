# Execution OS architecture

`RunPlanSpec` compiles a frozen task/split, models, policies, repeats, seeds,
scorer, code revision and backend into an immutable matrix. Units receive
deterministic IDs and disjoint shard numbers. Provider backends introduce
explicit approval requirements.

The local scheduler writes the manifest before work, links attempts, retries
within a bound, checkpoints after every completed unit and skips completed
units on resume. A different manifest cannot reuse a checkpoint. Collection
stores each output in the CAS and merges in manifest order.

The initial supported backend executes provider-free fixtures. Local model,
Kaggle, provider and cloud backends must implement the same discovery, prepare,
execute/checkpoint, cancel, collect and cleanup invariants before activation.

## Queue and workers

The SQLite queue orders eligible work by priority, study fairness and unit ID.
Dependencies must succeed before a child can lease. Global, backend and model
limits are checked inside the lease transaction. Quota exhaustion produces
`QUOTA_DEFERRED`; it is never disguised as success.

Workers receive a random lease token whose hash alone is persisted. Heartbeats
extend expiry. A generation and token check fences stale workers. Resource
reservations, attempts, heartbeats and state events remain inspectable.

## Retries, pause and cancellation

Only backend-classified transient failures retry. Backoff is exponential,
bounded and has deterministic per-unit jitter. Pausing changes queued units to
`PAUSED`; resuming returns them to eligibility. Cancellation removes the lease
and releases reservations.

## Atomic success

The backend result must name the leased unit. The coordinator writes and
verifies the content-addressed object, stages the digest on the attempt,
registers the artifact and provenance, then performs a conditional
exactly-once commit. Recovery commits a staged result only when the digest is
still valid in the CAS.

## Operational backends

`LocalSubprocessBackend` uses argument arrays with `shell=False`, a small
environment allowlist, process groups, bounded output, wall timeouts and strict
UTF-8 JSON validation. `KaggleBundleBackend` only exports and imports offline
bundles; it never calls Kaggle. Bundles pin manifest, task, model and policy
commitments and support T4x2 or single-T4 layouts. The provider backend remains
disabled unless approval, credentials and budget flags are all present.

For diagnosis, inspect `cab registry events`, queue state counts, stale-lease
events and CAS verification. Never edit queue rows manually.
