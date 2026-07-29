# Phase 03 end-to-end fixture

The immutable fixture manifest contains 20 unique units and two disjoint
shards. The first scheduling call completes seven and records `INTERRUPTED`; the
second uses the identical manifest/checkpoint and reaches 20 `COMPLETE`.

Observed internal reproduction verified 22 CAS objects (20 unit results and two
merge objects), 22 registry entities, zero duplicate units and a deterministic
merge. One deterministic fail-once unit is retried with linked attempt count
two in tests.

Evidence class: `FIXTURE_ONLY`.

Acceptance: `CAB_EXECUTION_OS_FOUNDATION_READY`.
