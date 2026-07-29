# Public API policy

Supported Python imports live in `causal_agent_bench.sdk`. The `cab` executable
is the stable CLI name; `causal-agent-bench` remains compatible. Public schemas
carry explicit versions and reject unknown fields at trust boundaries.

CAB follows semantic versioning. Removing or changing a supported interface
requires a documented deprecation period and migration note. Internal modules
outside the SDK may change in a minor release.

Stable CLI behavior includes deterministic JSON where applicable, non-zero
exit status on failed gates, no secrets/protected payloads, dry-run support
before execution and actionable errors. Fixture commands label their evidence
class.
