# Benchmark factory specification

The factory accepts YAML, JSON or Python-built `BenchmarkAuthoringSpec` objects.
Each spec binds a base task, tool environment, answer contract, gold source,
intervention, invariance and solvability contracts, manipulation check, expected
opportunity, scorer, provenance, licence, privacy class and split role.

Compilation is deterministic over canonical JSON. It rejects target-answer
changes, multiple mechanisms, invalid tool schemas, duplicate tool roles,
missing manipulation checks, confirmatory/public role collision and public
answer leakage. Output consists of a public instance, an optional private view
and a hash receipt.

The offline diversity engine checks exact, normalized and structural duplicates
and reports domain, family, split, scorer and privacy balance. Semantic checking
is an optional plugin and never a paid dependency.

The fixture in `examples/level5/public_fixture` demonstrates the full path but
is permanently `FIXTURE_ONLY`.
