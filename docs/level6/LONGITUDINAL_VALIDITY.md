# Longitudinal Benchmark Validity

CAB monitors model saturation, score compression, ceiling effects, family
saturation, contamination risk, rank stability, scorer and reviewer drift,
domain drift, capability-definition drift, retirement pressure, and new-task
calibration. Each cycle binds a benchmark version, frozen inputs, observation
window, estimands, thresholds, findings, decisions, and signatures.

Lifecycle states are `ACTIVE`, `SATURATING`, `CONTAMINATION_SUSPECTED`,
`DEPRECATED`, and `RETIRED`. Transitions fail closed against the machine-readable
transition table. Retirement is terminal; deprecation may only advance to
retirement. A contamination investigation may restore active state only with a
signed resolution and version impact assessment.

The repository includes fixture transition tests but claims zero completed
longitudinal monitoring cycles.
