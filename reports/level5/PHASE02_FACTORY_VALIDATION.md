# Phase 02 factory validation

The CC0 public fixture validates at `STATIC_VALIDATED` and compiles to
`inst.9a064c038e5d6634ddde42cc`. Tests cover determinism, target change,
multiple mechanisms, tool-role collision, confirmatory/public collision,
public/private split, duplicate detection, review-packet blinding and illegal
lifecycle jumps.

Human review and C10 remain absent. Freeze correctly exits blocked.

Acceptance: `CAB_BENCHMARK_FACTORY_READY`.
