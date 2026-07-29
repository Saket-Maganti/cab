# Phase 07 public API audit

The `cab` and legacy `causal-agent-bench` entry points share one parser. The SDK
exports registry, authoring/compiler, planner/CAS, evaluator and plugin
contracts. Example plugin registration and capability discovery pass; duplicate
and incompatible plugins fail before use.

Documentation includes quickstart, architecture, authoring, execution, review,
evaluation, evidence, security, governance, plugin development, CLI,
tutorial and troubleshooting pages.

Acceptance: `CAB_PUBLIC_INTERFACE_BETA_READY`.
