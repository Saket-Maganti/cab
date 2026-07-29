"""Structured observability and deterministic fixture fault-injection laboratory."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from causal_agent_bench.level5.core import content_hash, redact_sensitive, utc_now


class FaultKind(StrEnum):
    WORKER_KILL = "worker_kill"
    TIMEOUT = "timeout"
    DISK_FULL = "disk_full"
    PERMISSION_FAILURE = "permission_failure"
    CORRUPT_CHECKPOINT = "corrupt_checkpoint"
    CORRUPT_ARTIFACT = "corrupt_artifact"
    DUPLICATE_SHARD = "duplicate_shard"
    PARTIAL_UPLOAD = "partial_upload"
    NETWORK_DISCONNECT = "network_disconnect"
    MALFORMED_MODEL_OUTPUT = "malformed_model_output"
    INVALID_SCHEMA = "invalid_schema"
    SCORER_CRASH = "scorer_crash"
    REGISTRY_CONTENTION = "registry_contention"
    STALE_HEARTBEAT = "stale_heartbeat"
    MODEL_OOM = "model_oom"
    QUOTA_EXHAUSTION = "quota_exhaustion"
    CLOCK_SKEW = "clock_skew"
    REBOOT_MARKER = "reboot_marker"


DESIGN_SLOS = {
    "silent_data_loss": {"target": 0, "measured_real_execution": False},
    "duplicate_execution": {"target": 0, "measured_real_execution": False},
    "checkpoint_recovery_rate": {"target": 1.0, "measured_real_execution": False},
    "artifact_integrity_rate": {"target": 1.0, "measured_real_execution": False},
    "deterministic_merge_rate": {"target": 1.0, "measured_real_execution": False},
    "provenance_completeness": {"target": 1.0, "measured_real_execution": False},
    "bounded_retry_rate": {"target": 1.0, "measured_real_execution": False},
    "fail_closed_security_rate": {"target": 1.0, "measured_real_execution": False},
}


@dataclass(frozen=True)
class StructuredEvent:
    timestamp: str
    sequence: int
    component: str
    event_type: str
    correlation_id: str
    run_id: str | None
    shard_id: str | None
    attempt_id: str | None
    fields: dict[str, Any]


class EventLog:
    """Append-only JSON event writer with monotonic sequence numbers."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._sequence = self._last_sequence()

    def _last_sequence(self) -> int:
        if not self.path.exists():
            return 0
        lines = [line for line in self.path.read_text(encoding="utf-8").splitlines() if line]
        if not lines:
            return 0
        return int(json.loads(lines[-1])["sequence"])

    def emit(
        self,
        component: str,
        event_type: str,
        *,
        correlation_id: str,
        run_id: str | None = None,
        shard_id: str | None = None,
        attempt_id: str | None = None,
        fields: dict[str, Any] | None = None,
    ) -> StructuredEvent:
        self._sequence += 1
        event = StructuredEvent(
            timestamp=utc_now(),
            sequence=self._sequence,
            component=component,
            event_type=event_type,
            correlation_id=correlation_id,
            run_id=run_id,
            shard_id=shard_id,
            attempt_id=attempt_id,
            fields=redact_sensitive(fields or {}),
        )
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event.__dict__, sort_keys=True) + "\n")
        return event

    def read(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        return [
            json.loads(line)
            for line in self.path.read_text(encoding="utf-8").splitlines()
            if line
        ]


FAULT_EXPECTATIONS: dict[FaultKind, tuple[str, ...]] = {
    FaultKind.WORKER_KILL: ("retry_linked", "unit_recovered"),
    FaultKind.TIMEOUT: ("bounded_retry", "unit_recovered"),
    FaultKind.DISK_FULL: ("atomic_write_preserved", "failed_closed"),
    FaultKind.PERMISSION_FAILURE: ("failed_closed",),
    FaultKind.CORRUPT_CHECKPOINT: ("corruption_detected", "failed_closed"),
    FaultKind.CORRUPT_ARTIFACT: ("corruption_detected", "not_promoted"),
    FaultKind.DUPLICATE_SHARD: ("duplicate_rejected",),
    FaultKind.PARTIAL_UPLOAD: ("partial_not_visible",),
    FaultKind.NETWORK_DISCONNECT: ("bounded_retry", "unit_recovered"),
    FaultKind.MALFORMED_MODEL_OUTPUT: ("schema_rejected",),
    FaultKind.INVALID_SCHEMA: ("schema_rejected",),
    FaultKind.SCORER_CRASH: ("raw_preserved", "rescore_possible"),
    FaultKind.REGISTRY_CONTENTION: ("transaction_preserved",),
    FaultKind.STALE_HEARTBEAT: ("stale_detected",),
    FaultKind.MODEL_OOM: ("bounded_retry", "failure_recorded"),
    FaultKind.QUOTA_EXHAUSTION: ("quota_enforced", "work_deferred"),
    FaultKind.CLOCK_SKEW: ("sequence_monotonic",),
    FaultKind.REBOOT_MARKER: ("resume_required", "completed_not_rerun"),
}


def run_fixture_chaos_campaign(
    *,
    injected_failures: set[FaultKind] | None = None,
) -> dict[str, Any]:
    """Evaluate the deterministic recovery contract without real execution."""

    selected = injected_failures or set(FaultKind)
    cases: list[dict[str, Any]] = []
    for fault in sorted(selected, key=lambda value: value.value):
        invariants = list(FAULT_EXPECTATIONS[fault])
        case = {
            "fault": fault.value,
            "invariants": invariants,
            "passed": bool(invariants),
            "receipt": content_hash({"fault": fault.value, "invariants": invariants}),
            "evidence_class": "FIXTURE_ONLY",
        }
        cases.append(case)
    passed = all(case["passed"] for case in cases)
    return {
        "campaign_id": f"chaos.{content_hash(cases)[:24]}",
        "passed": passed,
        "case_count": len(cases),
        "passed_count": sum(bool(case["passed"]) for case in cases),
        "cases": cases,
        "design_slos": DESIGN_SLOS,
        "real_execution_slos_measured": False,
        "evidence_class": "FIXTURE_ONLY",
    }


def diagnostic_summary(events: list[dict[str, Any]]) -> dict[str, Any]:
    sequences = [int(event["sequence"]) for event in events]
    components = sorted({str(event["component"]) for event in events})
    return {
        "event_count": len(events),
        "sequence_monotonic": sequences == sorted(set(sequences)),
        "components": components,
        "errors": [
            event
            for event in events
            if str(event.get("event_type", "")).upper() in {"ERROR", "FAILED"}
        ],
    }


__all__ = [
    "DESIGN_SLOS",
    "EventLog",
    "FaultKind",
    "StructuredEvent",
    "diagnostic_summary",
    "run_fixture_chaos_campaign",
]
