# Plugin system

Plugin types are agent, tool, backend, scorer, intervention family, analysis,
exporter and evaluator runtime. Metadata declares a unique name, semantic
version, API version, description and capabilities.

Entry points use `causal_agent_bench.plugins`. Discovery catches and records
individual load failures. API mismatches, duplicate names and validation errors
are isolated before use. Plugins cannot silently shadow canonical safety gates,
evidence transitions or scientific metrics.

`ExampleScorerPlugin` demonstrates a provider-free scorer. Third-party plugins
should test minimal installation, compatibility, malformed input and failure
isolation.
