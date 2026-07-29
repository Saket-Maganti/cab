# Phase 01 architecture audit

The live repository at the starting SHA already contained the scientific kernel,
RAAC, scoring, runner, C10/safety gates and release scaffolding. The Level-5
build extends those systems through a bounded control plane.

Added contexts: experiment registry, provenance, benchmark factory, scheduler,
CAS, reliability, review service, evaluator, evidence graph, certification,
public SDK/plugins and governance. Six ADRs define storage, boundaries, fixture
isolation, public/private separation and API policy.

Acceptance: `CAB_LEVEL5_CORE_REGISTRY_READY`.
