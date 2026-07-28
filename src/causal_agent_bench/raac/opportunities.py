"""Evaluator-side RAAC opportunity flags derived from public traces."""

from __future__ import annotations

from typing import Any

from causal_agent_bench.raac.types import AnomalySignal

_RECOVERY_SIGNALS = {
    AnomalySignal.TOOL_ERROR.value,
    AnomalySignal.TIMEOUT.value,
    AnomalySignal.MALFORMED_OUTPUT.value,
    AnomalySignal.MISSING_REQUIRED_FIELD.value,
    AnomalySignal.SCHEMA_MISMATCH.value,
    AnomalySignal.PARTIAL_OUTPUT.value,
    AnomalySignal.IMPOSSIBLE_VALUE.value,
}
_VERIFICATION_SIGNALS = {
    AnomalySignal.CONTRADICTORY_OBSERVATION.value,
    AnomalySignal.STALE_TIMESTAMP.value,
    AnomalySignal.INCONSISTENT_REPEATED_RESULT.value,
    AnomalySignal.INSUFFICIENT_EVIDENCE.value,
    AnomalySignal.UNVERIFIABLE_SUCCESS_SIGNAL.value,
}


def raac_opportunity_flags(trajectory: Any) -> dict[str, bool | int | None]:
    metadata = getattr(trajectory, "raac_metadata", None)
    if not isinstance(metadata, dict) or not metadata:
        root_metadata = getattr(trajectory, "metadata", {})
        metadata = root_metadata.get("raac", {}) if isinstance(root_metadata, dict) else {}
    if not isinstance(metadata, dict) or not metadata.get("enabled"):
        return {
            "raac_enabled_binary": False,
            "raac_recovery_opportunity_binary": None,
            "raac_verification_opportunity_binary": None,
            "raac_clarification_opportunity_binary": None,
            "raac_abstention_opportunity_binary": None,
            "raac_anomaly_signal_count": 0,
            "raac_budget_exhaustion_binary": None,
            "raac_infrastructure_failure_binary": None,
            "raac_abstained_binary": None,
            "raac_unverified_success_failure_binary": None,
        }
    trace = metadata.get("trace", [])
    rows = [row for row in trace if isinstance(row, dict)] if isinstance(trace, list) else []
    signals = [
        str(row["trigger_signal"])
        for row in rows
        if row.get("trigger_signal") is not None
    ]
    decisions = [str(row.get("decision")) for row in rows]
    reasons = [str(row.get("reason_code")) for row in rows]
    unverified_failure = any(
        str(row.get("trigger_signal")) == AnomalySignal.UNVERIFIABLE_SUCCESS_SIGNAL.value
        and str(row.get("decision")) not in {"final_verification", "verify_current_evidence"}
        for row in rows
    )
    return {
        "raac_enabled_binary": True,
        "raac_recovery_opportunity_binary": any(signal in _RECOVERY_SIGNALS for signal in signals),
        "raac_verification_opportunity_binary": any(
            signal in _VERIFICATION_SIGNALS for signal in signals
        ),
        "raac_clarification_opportunity_binary": (
            AnomalySignal.INSUFFICIENT_EVIDENCE.value in signals
        ),
        "raac_abstention_opportunity_binary": bool(signals),
        "raac_anomaly_signal_count": len(signals),
        "raac_budget_exhaustion_binary": "budget_exhausted" in reasons,
        "raac_infrastructure_failure_binary": (
            "terminate_infrastructure_failure" in decisions
        ),
        "raac_abstained_binary": "abstain" in decisions,
        "raac_unverified_success_failure_binary": unverified_failure,
    }
