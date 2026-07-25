# ACRS Metric Suite V2

Status: design and fixture-only implementation. No real results computed.

## Metrics

- raw clean success
- raw intervention success
- ACRS ratio
- absolute degradation
- relative degradation
- per-family ACRS
- macro-family ACRS
- micro-family ACRS
- rank shift
- rank correlation
- worst-family robustness
- recovery score
- abstention correctness score
- scorer-adjusted success after manual review exists

## Edge Cases

- `clean_success = 0`: ACRS and relative degradation are undefined.
- missing trajectories: mark run incomplete; do not impute.
- incomplete runs: no scientific evidence.
- tied ranks: use documented average-rank or stable tie policy.
- small samples: report uncertainty and avoid headline claims.
- scorer disagreement: report deterministic and manual-adjusted success separately.

## Implementation

Fixture-only helpers live in `src/causal_agent_bench/metrics/acrs_v2.py`. They are safe for unit tests and future analysis plumbing, but they do not compute evidence until eligible run artifacts exist.
