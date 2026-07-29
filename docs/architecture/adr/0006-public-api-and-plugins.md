# ADR 0006: Stable SDK and constrained plugins

Status: accepted

Supported imports live in `causal_agent_bench.sdk`. Plugins declare a type,
semantic version, API version and capabilities. Loading failures are isolated,
duplicates are rejected, and no plugin can replace canonical safety gates by
name collision.
