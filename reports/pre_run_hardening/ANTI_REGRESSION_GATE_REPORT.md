# Anti-Regression Gate Report

Acceptance surface: `cab pre-run scientific-check` and
`make pre-run-scientific-check`.

The gate checks scorer-v3 field separation and adversarial behavior, endpoint
identity, Compact count/balance/hash/reachability, Scale and transfer assignment
thresholds, v2-only execution, manifest-derived planning, frozen prospective
power, strict system identity, transfer provenance/hashes, canonical guidance,
required reports, zero genuine counters, and the public/private split.

CI workflow `.github/workflows/pre-run-scientific-hardening.yml` runs the gate,
focused regression tests, public v2 commitment validation, notebook validation,
security scan, Ruff, mypy, and `git diff --check` without providers or models.
