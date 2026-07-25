# 08 Tool Environment Audit

## Findings

Simulated tool implementations under `src/causal_agent_bench/tools/` are local and deterministic by design. The email and booking tools are explicitly draft/stub tools and do not send real emails or create real bookings. The web-shadow tool uses static local snapshots.

No benchmark tool implementation was found that performs real shell execution, real email sending, real booking, credential reads, or live web calls as part of agent task execution.

## Schema and failure behavior

Tool observations are emitted through the benchmark environment and are recorded in trajectories. Failure/corruption interventions are auditable through the generated intervention metadata and the intervention audit report.

## Risks

- Provider adapters do make network API calls when explicitly configured; these are not simulated benchmark tools and must stay behind dry-run/cost/provider readiness checks.
- Tool-failure semantics should continue to be covered by tests as intervention families evolve.

