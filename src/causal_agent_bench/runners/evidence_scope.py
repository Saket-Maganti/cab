from __future__ import annotations

"""Classify runs by deployment/provider so tables and summaries do not mix evidence types."""

COMMERCIAL_API_PROVIDERS = frozenset({"openai", "anthropic", "gemini", "openrouter"})
LOCAL_OPEN_WEIGHT_PROVIDERS = frozenset({"local_openai"})
ENGINEERING_ONLY_PROVIDERS = frozenset({"local_stub"})
OPENAI_COMPATIBLE_PROVIDERS = frozenset({"openai_compatible"})


def providers_from_agent_runs(agent_runs: list[dict[str, object]]) -> set[str]:
    return {
        str(run["provider"])
        for run in agent_runs
        if isinstance(run, dict) and run.get("provider") is not None
    }


def classify_evidence_scope(
    providers: set[str],
    *,
    run_name: str | None = None,
    agent_names: set[str] | None = None,
) -> str:
    """Return a stable evidence-scope label for paper tables and run summaries."""

    agents = agent_names or set()
    if agents == {"mock_behavior_agent"} or (
        agents and agents <= {"mock_behavior_agent"} and run_name and "mock" in run_name.lower()
    ):
        return "mock_diagnostic_only"
    if not providers:
        if run_name and "mock_diagnostic" in run_name.lower():
            return "mock_diagnostic_only"
        return "deterministic_baseline_engineering"
    if providers <= ENGINEERING_ONLY_PROVIDERS:
        return "pilot_stub_engineering_only"
    if providers <= LOCAL_OPEN_WEIGHT_PROVIDERS:
        return "local_open_weight_unvalidated"
    localish = providers & (LOCAL_OPEN_WEIGHT_PROVIDERS | ENGINEERING_ONLY_PROVIDERS)
    commercial = providers & COMMERCIAL_API_PROVIDERS
    compatible = providers & OPENAI_COMPATIBLE_PROVIDERS
    if localish and (commercial or compatible):
        return "mixed_local_and_api_do_not_merge"
    if commercial:
        if run_name and "pilot" in run_name.lower():
            return "commercial_api_pilot_unvalidated"
        return "commercial_api_experiment_unvalidated"
    if compatible:
        return "openai_compatible_endpoint_unvalidated"
    return "development_or_smoke"


def classify_scientific_scope(
    providers: set[str],
    *,
    run_name: str | None = None,
) -> str:
    """Return a concise scientific-scope label for run summaries."""

    evidence = classify_evidence_scope(providers, run_name=run_name)
    if evidence == "pilot_stub_engineering_only":
        return "engineering_only_local_stub"
    if evidence == "local_open_weight_unvalidated":
        return "local_open_weight_pilot_or_experiment"
    if evidence.startswith("commercial_api"):
        return "commercial_api_pilot_or_experiment"
    if evidence == "mixed_local_and_api_do_not_merge":
        return "mixed_deployment_do_not_merge"
    if evidence == "openai_compatible_endpoint_unvalidated":
        return "openai_compatible_endpoint_experiment"
    if providers:
        return "provider_backed_pilot_or_experiment"
    return "deterministic_baseline_engineering"
