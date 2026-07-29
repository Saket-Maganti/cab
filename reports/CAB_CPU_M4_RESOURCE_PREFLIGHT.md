# CAB CPU M4 Resource Preflight

The preflight itself completed in 0.323 seconds (`MEASURED_ON_LOCAL_M4`).
All projected execution figures below are `ESTIMATE_NOT_MEASURED`.

| Item | Value |
|---|---:|
| Apple M4 logical CPUs | 10 |
| Memory | 16 GiB |
| Recommended conservative workers | 2 (`low_memory`) |
| Repository footprint | 1.88 GiB |
| Files inventoried | 8,194 |
| Default projected trajectories | 960 |
| Projected intermediate disk | 36–108 MiB (base 60 MiB) |
| Projected runtime | 3.6–10.8 h (base 6.0 h) |
| Pilot bootstrap | 1,000 replicates |
| Bootstrap shards | 4 × 250, disjoint and resumable |

Use streaming JSONL plus deterministic gzip for intermediates and retain raw
evidence until its audited derivative and hashes have been verified. The
largest safe cleanup opportunities are ignored historical leakage reports,
fixture/stub results, and tool caches; this run deletes none of them. Keep at
least 20 GiB free before future execution and fall back to serial mode under
memory pressure.
