# Reliability operations

The provider-free reliability laboratory physically injects safe faults and
accepts only observed outcomes: prevented, detected and contained, recovered,
failed closed, or not mitigated.

| Fault | Injection | Required invariant | Recovery | Residual risk |
|---|---|---|---|---|
| Worker kill | SIGTERM subprocess | lease is reclaimed | retry durable state | host-wide kill untested |
| Timeout | sleeping subprocess | process group ends | terminal timeout | kernel hangs |
| Disk full | CAS raises `ENOSPC` | prior object intact | retry after capacity | real quotas vary |
| Permission | CAS raises `EACCES` | no visible partial | correct permissions | external ACL drift |
| Checkpoint corruption | alter fields or digest | validator rejects | known-good checkpoint | lost work |
| Artifact corruption | mutate stored bytes | digest mismatch | quarantine/recompute | hardware faults |
| Duplicate race | concurrent commit | one result commits | stale worker fenced | distributed DB semantics |
| Partial upload | fail before replace | object invisible | retry upload | remote stores differ |
| Disconnect | close socket | retry is bounded | reconnect once | long partitions |
| Malformed output | invalid UTF-8/JSON/schema | no commit | invalid-output state | novel encodings |
| Scorer crash | raise after raw write | raw stays intact | deterministic rescore | scorer logic |
| Registry contention | hold write lock | no data loss | busy timeout/retry | extreme volume |
| Stale heartbeat | expire a lease | old token invalid | re-lease | severe clock failure |
| OOM | classified fixture | host not exhausted | terminal OOM | cgroup differences |
| Quota exhaustion | allowance zero | work deferred | administrator decision | billing lag |
| Clock skew | reverse timestamps | sequence canonical | sequence ordering | cross-host chronology |
| Reboot marker | new coordinator | no rerun of commit | reconcile stage | power-loss hardware |

Run:

```bash
cab reliability campaign \
  --output reports/level5_hardening/REAL_FAULT_INJECTION_REPORT.json
```

Treat `NOT_MITIGATED` as a defect. Fixture recovery proves the local invariant,
not a production SLO.
