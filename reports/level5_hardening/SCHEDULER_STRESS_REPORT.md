# Scheduler stress and crash-consistency report

Status: passed. Evidence class: `FIXTURE_ONLY`.

The mandatory matrix compiled 1,000 deterministic units and ran the same
manifest with 1, 2, 4 and 8 worker threads. Each run paused and resumed all
1,000 units, used dependencies and priorities, injected 19 deterministic
first-attempt failures, cancelled 5 units, quota-deferred 5 units, and forcibly
recovered 1 stale lease.

Every worker count ended with 990 `SUCCEEDED`, 5 `CANCELLED` and 5
`QUOTA_DEFERRED` units in 1,010 attempts. All four runs produced merged hash
`aa6b63acbef06efb6f68fb100ae808dfd2d7ca83c602ab568ea022bdf7d41e9e`.
There were zero missing terminal states and zero duplicate committed results.
Measured wall times were 58.77, 58.69, 58.25 and 58.33 seconds. Peak process RSS
was at most 147,783,680 bytes.

The same campaign reopened durable state at five coordinator crash boundaries:
after lease, after artifact write, before registry commit, after artifact
registration, and before terminal scheduler state. All five converged to
`SUCCEEDED`, the expected CAS digest, and zero duplicate commits. Unjournaled
artifacts were deterministically re-executed; journaled CAS-verified results
were completed during restart recovery.

Machine-readable receipt: `SCHEDULER_STRESS_REPORT.json`.
