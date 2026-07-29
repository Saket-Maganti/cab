# Real fault-injection report

Status: passed. Evidence class: `FIXTURE_ONLY`.

All 18 selected faults created a physical failure state and checked an observed
invariant. Outcomes were 9 `RECOVERED`, 4 `PREVENTED`, 3 `FAILED_CLOSED` and 2
`DETECTED_AND_CONTAINED`; none were declaratively auto-passed and none were
unmitigated.

Executed faults: worker termination, timeout, disk full, permission failure,
partial upload, checkpoint corruption, artifact corruption, duplicate shard,
network disconnect, malformed JSON, invalid schema, scorer crash with raw
preservation/rescore, SQLite contention, stale heartbeat, model OOM
classification, quota exhaustion, clock skew and reboot marker.

Campaign ID: `chaos.0abd81abaa3e4913152d9ad3`. Machine-readable receipt:
`REAL_FAULT_INJECTION_REPORT.json`.
