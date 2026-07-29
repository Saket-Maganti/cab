# Reliability model

CAB's core invariants are: no silent missing unit, no unreasoned duplicate
execution, immutable raw output, identical-manifest resume, bounded linked
attempts, deterministic merge, corruption exclusion and complete provenance.

The reliability laboratory covers worker kill, timeout, simulated disk full,
permission failure, corrupt checkpoint/artifact, duplicate shard, partial
upload, network disconnect, malformed output, invalid schema, scorer crash,
registry contention, stale heartbeat, OOM signal, quota exhaustion, clock skew
and reboot markers.

The current campaign is fixture evidence. Design SLO targets are present but
remain explicitly unmeasured for real execution until a legal live run exists.
