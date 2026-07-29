# Observability and redaction

Local structured events carry UTC time, component, event type, correlation ID,
optional run/shard/attempt IDs and a monotonic sequence. The format supports
planner, scheduler, backend, model adapter, RAAC, checkpoint, artifact, scorer,
audit, analysis and evaluator events.

Fields matching private, protected, secret, answer, gold, reviewer-identity or
task-payload names are redacted before serialization. Logs are local JSONL by
default and require no external telemetry. Static dashboards and diagnostics
derive from this event stream without reading protected payloads.
