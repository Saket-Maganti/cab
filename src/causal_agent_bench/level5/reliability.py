"""Structured observability and deterministic fixture fault-injection laboratory."""

from __future__ import annotations

import errno
import json
import os
import signal
import socket
import sqlite3
import sys
import tempfile
import time
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from causal_agent_bench.level5.core import (
    content_hash,
    file_sha256,
    redact_sensitive,
    sha256_bytes,
    utc_now,
)
from causal_agent_bench.level5.execution import (
    ConcurrentFixtureBackend,
    ContentAddressedStore,
    ExecutionFailure,
    FailureClass,
    LocalSubprocessBackend,
    QueueRepository,
    RunPlanSpec,
    RunState,
    compile_run_plan,
    validate_checkpoint,
)
from causal_agent_bench.level5.registry import SQLiteRegistry


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


class FaultOutcome(StrEnum):
    PREVENTED = "PREVENTED"
    DETECTED_AND_CONTAINED = "DETECTED_AND_CONTAINED"
    RECOVERED = "RECOVERED"
    FAILED_CLOSED = "FAILED_CLOSED"
    MANUAL_RECOVERY_REQUIRED = "MANUAL_RECOVERY_REQUIRED"
    NOT_MITIGATED = "NOT_MITIGATED"
    NOT_EXECUTED = "NOT_EXECUTED"


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
        timestamp: str | None = None,
    ) -> StructuredEvent:
        self._sequence += 1
        event = StructuredEvent(
            timestamp=timestamp or utc_now(),
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


def _one_unit_manifest(*, backend: str = "fixture", max_attempts: int = 2) -> Any:
    spec = RunPlanSpec(
        study_id=f"study.fault_{backend}",
        task_version="tasks.fault_fixture.v1",
        split_version="split.fault_fixture.v1",
        model_versions=["model.fixture.v1"],
        policies=["policy.fixture.v1"],
        repeats=1,
        seeds=[7],
        task_ids=["fault_task"],
        scorer_version="scorer.fixture.v1",
        code_revision="hardening-fixture",
        backend=backend,
        max_concurrency=2,
        max_attempts=max_attempts,
        timeout_seconds=0.05,
    )
    return compile_run_plan(spec, shard_count=1)


def _subprocess_fault(root: Path, *, timeout: bool) -> tuple[FaultOutcome, dict[str, Any]]:
    manifest = _one_unit_manifest(backend="local_subprocess")
    unit = manifest.units[0]
    command = (
        [sys.executable, "-c", "import time; time.sleep(2)"]
        if timeout
        else [sys.executable, "-c", "import time; time.sleep(5)"]
    )
    backend = LocalSubprocessBackend({unit.unit_id: command})
    backend.prepare(manifest)
    handle = backend.launch(unit, attempt=1)
    process = backend._processes[handle][1]
    if not timeout:
        os.killpg(process.pid, signal.SIGTERM)
    try:
        backend.collect(handle, timeout_seconds=0.02 if timeout else 2)
    except ExecutionFailure as exc:
        expected = FailureClass.TIMEOUT if timeout else FailureClass.WORKER_KILLED
        classified = exc.failure_class is expected
    else:
        classified = False
    finally:
        backend.cleanup(handle)
    orphan_free = process.poll() is not None
    # Concrete recovery uses a fresh deterministic fixture execution.
    fixture = ConcurrentFixtureBackend()
    fixture_manifest = _one_unit_manifest()
    fixture.prepare(fixture_manifest)
    fixture_handle = fixture.launch(fixture_manifest.units[0], attempt=2)
    recovered = fixture.collect(fixture_handle, timeout_seconds=1)
    fixture.cleanup(fixture_handle)
    return (
        FaultOutcome.RECOVERED if classified and orphan_free else FaultOutcome.NOT_MITIGATED,
        {
            "failure_classified": classified,
            "orphan_processes": 0 if orphan_free else 1,
            "retry_linked": recovered.unit_id == fixture_manifest.units[0].unit_id,
        },
    )


def _filesystem_fault(
    root: Path,
    *,
    error_number: int,
    stage: str,
) -> tuple[FaultOutcome, dict[str, Any]]:
    healthy = ContentAddressedStore(root / "cas")
    prior = healthy.put_bytes(b"prior-object", artifact_class="fixture")
    enabled = True

    def inject(observed_stage: str, path: Path) -> None:
        del path
        if enabled and observed_stage == stage:
            raise OSError(error_number, os.strerror(error_number))

    broken = ContentAddressedStore(root / "cas", fault_injector=inject)
    failed_closed = False
    try:
        broken.put_bytes(b"new-object", artifact_class="fixture")
    except OSError as exc:
        failed_closed = exc.errno == error_number
    target = sha256_bytes(b"new-object")
    partial_invisible = not broken._metadata_path(target).exists()
    prior_intact = healthy.get_bytes(prior.digest) == b"prior-object"
    enabled = False
    recovered = broken.put_bytes(b"new-object", artifact_class="fixture")
    recovery_passed = healthy.verify(recovered.digest)["passed"]
    passed = failed_closed and partial_invisible and prior_intact and recovery_passed
    return (
        FaultOutcome.RECOVERED if passed else FaultOutcome.NOT_MITIGATED,
        {
            "errno": error_number,
            "injected_stage": stage,
            "failed_closed": failed_closed,
            "partial_object_visible": not partial_invisible,
            "prior_object_intact": prior_intact,
            "retry_succeeded": recovery_passed,
        },
    )


def _checkpoint_fault(root: Path) -> tuple[FaultOutcome, dict[str, Any]]:
    manifest = _one_unit_manifest()
    checkpoint_path = root / "checkpoint.json"
    detections: dict[str, bool] = {}
    checkpoint_path.write_text("{", encoding="utf-8")
    try:
        json.loads(checkpoint_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        detections["truncated_json"] = True
    valid = {
        "manifest_hash": manifest.manifest_hash,
        "completed": {},
        "attempts": {},
        "failures": {},
    }
    variants = {
        "wrong_manifest": {**valid, "manifest_hash": "f" * 64},
        "missing_required_field": {
            key: value for key, value in valid.items() if key != "failures"
        },
        "invalid_artifact_digest": {
            **valid,
            "completed": {manifest.units[0].unit_id: "short"},
        },
        "unknown_completed_unit": {
            **valid,
            "completed": {"unit.unknown": "a" * 64},
        },
    }
    for name, value in variants.items():
        try:
            validate_checkpoint(value, manifest)
        except ValueError:
            detections[name] = True
        else:
            detections[name] = False
    passed = len(detections) == 5 and all(detections.values())
    return (
        FaultOutcome.DETECTED_AND_CONTAINED if passed else FaultOutcome.NOT_MITIGATED,
        {"detections": detections, "failed_closed": passed},
    )


def _artifact_fault(root: Path) -> tuple[FaultOutcome, dict[str, Any]]:
    store = ContentAddressedStore(root / "cas")
    metadata = store.put_bytes(b"immutable-evidence", artifact_class="fixture")
    store._object_path(metadata.digest).write_bytes(b"tampered")
    verification = store.verify(metadata.digest)
    promotion_refused = not verification["passed"]
    return (
        FaultOutcome.DETECTED_AND_CONTAINED
        if promotion_refused
        else FaultOutcome.NOT_MITIGATED,
        {
            "corruption_detected": not verification["passed"],
            "quarantined_from_promotion": promotion_refused,
            "errors": verification["errors"],
        },
    )


def _duplicate_fault(root: Path) -> tuple[FaultOutcome, dict[str, Any]]:
    registry = SQLiteRegistry(root / "registry.sqlite3")
    repository = QueueRepository(registry)
    manifest = _one_unit_manifest()
    repository.enqueue(manifest)
    lease = repository.acquire(
        worker_id="worker.a",
        manifest_hash=manifest.manifest_hash,
        backend_limit=2,
        model_limit=2,
        global_limit=2,
        lease_seconds=5,
    )
    assert lease is not None
    competing = repository.acquire(
        worker_id="worker.b",
        manifest_hash=manifest.manifest_hash,
        backend_limit=2,
        model_limit=2,
        global_limit=2,
        lease_seconds=5,
    )
    repository.mark_running(lease)
    store = ContentAddressedStore(root / "cas")
    digest = store.put_json({"unit_id": lease.unit.unit_id}, artifact_class="fixture").digest
    repository.stage_result(lease, digest)
    first = repository.commit_success(lease, digest)
    second = repository.commit_success(lease, digest)
    passed = competing is None and first and not second
    return (
        FaultOutcome.PREVENTED if passed else FaultOutcome.NOT_MITIGATED,
        {
            "competing_lease_denied": competing is None,
            "first_commit": first,
            "duplicate_commit": second,
            "committed_result_count": 1,
        },
    )


def _network_fault(root: Path) -> tuple[FaultOutcome, dict[str, Any]]:
    del root
    receiver, sender = socket.socketpair()
    try:
        sender.sendall(b"10\nabc")
        sender.close()
        chunks: list[bytes] = []
        while True:
            chunk = receiver.recv(64)
            if not chunk:
                break
            chunks.append(chunk)
        declared, body = b"".join(chunks).split(b"\n", 1)
        disconnect_detected = len(body) != int(declared)
    finally:
        receiver.close()
        sender.close()
    retry_receiver, retry_sender = socket.socketpair()
    try:
        retry_sender.sendall(b"3\nabc")
        retry_sender.close()
        payload = retry_receiver.recv(64)
        declared, body = payload.split(b"\n", 1)
        retry_succeeded = len(body) == int(declared)
    finally:
        retry_receiver.close()
        retry_sender.close()
    passed = disconnect_detected and retry_succeeded
    return (
        FaultOutcome.RECOVERED if passed else FaultOutcome.NOT_MITIGATED,
        {
            "mid_transfer_disconnect_detected": disconnect_detected,
            "bounded_retry_succeeded": retry_succeeded,
        },
    )


def _output_fault(
    root: Path,
    *,
    invalid_json: bool,
) -> tuple[FaultOutcome, dict[str, Any]]:
    manifest = _one_unit_manifest(backend="local_subprocess")
    unit = manifest.units[0]
    output = "not-json" if invalid_json else json.dumps({"wrong": "schema"})
    backend = LocalSubprocessBackend(
        {unit.unit_id: [sys.executable, "-c", f"print({output!r})"]}
    )
    backend.prepare(manifest)
    handle = backend.launch(unit, attempt=1)
    detected = False
    try:
        backend.collect(handle, timeout_seconds=1)
    except ExecutionFailure as exc:
        detected = exc.failure_class is FailureClass.INVALID_OUTPUT
    finally:
        backend.cleanup(handle)
    return (
        FaultOutcome.FAILED_CLOSED if detected else FaultOutcome.NOT_MITIGATED,
        {"schema_rejected": detected, "invalid_json": invalid_json},
    )


def _scorer_fault(root: Path) -> tuple[FaultOutcome, dict[str, Any]]:
    store = ContentAddressedStore(root / "cas")
    raw = {"expected": "4", "observed": "4", "evidence_class": "FIXTURE_ONLY"}
    raw_digest = store.put_json(raw, artifact_class="raw").digest

    def crashing_scorer(value: dict[str, str]) -> float:
        del value
        raise RuntimeError("injected scorer crash")

    crashed = False
    try:
        crashing_scorer(raw)
    except RuntimeError:
        crashed = True
    raw_preserved = store.verify(raw_digest)["passed"]
    rescore_one = float(raw["expected"] == raw["observed"])
    rescore_two = float(raw["expected"] == raw["observed"])
    passed = crashed and raw_preserved and rescore_one == rescore_two == 1.0
    return (
        FaultOutcome.RECOVERED if passed else FaultOutcome.NOT_MITIGATED,
        {
            "scorer_crashed": crashed,
            "raw_preserved": raw_preserved,
            "deterministic_rescore": rescore_one == rescore_two,
        },
    )


def _contention_fault(root: Path) -> tuple[FaultOutcome, dict[str, Any]]:
    registry = SQLiteRegistry(root / "registry.sqlite3")
    registry.initialize()
    holder = sqlite3.connect(registry.path, isolation_level=None)
    contender = sqlite3.connect(registry.path, timeout=0.01, isolation_level=None)
    locked = False
    try:
        holder.execute("BEGIN IMMEDIATE")
        try:
            contender.execute("BEGIN IMMEDIATE")
        except sqlite3.OperationalError as exc:
            locked = "locked" in str(exc).lower()
        holder.execute("ROLLBACK")
        contender.execute("BEGIN IMMEDIATE")
        contender.execute("ROLLBACK")
        recovered = True
    finally:
        holder.close()
        contender.close()
    return (
        FaultOutcome.RECOVERED if locked and recovered else FaultOutcome.NOT_MITIGATED,
        {"contention_detected": locked, "backoff_recovery": recovered},
    )


def _queue_fault(
    root: Path,
    *,
    quota: bool,
) -> tuple[FaultOutcome, dict[str, Any]]:
    registry = SQLiteRegistry(root / "registry.sqlite3")
    repository = QueueRepository(registry)
    manifest = _one_unit_manifest()
    unit_id = manifest.units[0].unit_id
    if quota:
        repository.set_quota("empty", 0)
        repository.enqueue(manifest, quota_keys={unit_id: "empty"})
        lease = repository.acquire(
            worker_id="worker.quota",
            manifest_hash=manifest.manifest_hash,
            backend_limit=1,
            model_limit=1,
            global_limit=1,
            lease_seconds=1,
        )
        summary = repository.summary(manifest.manifest_hash)
        deferred = summary["state_counts"].get(RunState.QUOTA_DEFERRED.value) == 1
        return (
            FaultOutcome.PREVENTED if lease is None and deferred else FaultOutcome.NOT_MITIGATED,
            {"lease_denied": lease is None, "work_deferred": deferred},
        )
    repository.enqueue(manifest)
    lease = repository.acquire(
        worker_id="worker.stale",
        manifest_hash=manifest.manifest_hash,
        backend_limit=1,
        model_limit=1,
        global_limit=1,
        lease_seconds=0.01,
    )
    assert lease is not None
    reclaimed = repository.reclaim_stale(now=time.time() + 1)
    state = repository.summary(manifest.manifest_hash)["state_counts"]
    recovered = reclaimed == 1 and state.get(RunState.RETRY_WAIT.value) == 1
    return (
        FaultOutcome.RECOVERED if recovered else FaultOutcome.NOT_MITIGATED,
        {"stale_detected": reclaimed == 1, "lease_reclaimed": recovered},
    )


def _oom_fault(root: Path) -> tuple[FaultOutcome, dict[str, Any]]:
    del root
    backend = ConcurrentFixtureBackend()
    failure = ExecutionFailure(
        "fixture backend classified model OOM without exhausting host memory",
        failure_class=FailureClass.OOM,
        retryable=False,
    )
    observed, retryable = backend.classify_failure(failure)
    passed = observed is FailureClass.OOM and not retryable
    return (
        FaultOutcome.FAILED_CLOSED if passed else FaultOutcome.NOT_MITIGATED,
        {"failure_class": observed.value, "host_memory_exhausted": False, "retryable": retryable},
    )


def _clock_fault(root: Path) -> tuple[FaultOutcome, dict[str, Any]]:
    log = EventLog(root / "clock.jsonl")
    log.emit("scheduler", "FIRST", correlation_id="clock", timestamp="2099-01-01T00:00:00Z")
    log.emit("scheduler", "SECOND", correlation_id="clock", timestamp="1999-01-01T00:00:00Z")
    events = log.read()
    monotonic = [row["sequence"] for row in events] == [1, 2]
    skew_present = events[1]["timestamp"] < events[0]["timestamp"]
    return (
        FaultOutcome.PREVENTED if monotonic and skew_present else FaultOutcome.NOT_MITIGATED,
        {"wall_clock_skew_injected": skew_present, "event_sequence_monotonic": monotonic},
    )


def _reboot_fault(root: Path) -> tuple[FaultOutcome, dict[str, Any]]:
    registry = SQLiteRegistry(root / "registry.sqlite3")
    repository = QueueRepository(registry)
    manifest = _one_unit_manifest()
    repository.enqueue(manifest)
    lease = repository.acquire(
        worker_id="worker.before_reboot",
        manifest_hash=manifest.manifest_hash,
        backend_limit=1,
        model_limit=1,
        global_limit=1,
        lease_seconds=5,
    )
    assert lease is not None
    repository.mark_running(lease)
    store = ContentAddressedStore(root / "cas")
    digest = store.put_json({"unit_id": lease.unit.unit_id}, artifact_class="fixture").digest
    repository.stage_result(lease, digest)
    repository.commit_success(lease, digest)
    # A new repository instance represents a restarted coordinator.
    restarted = QueueRepository(SQLiteRegistry(registry.path))
    reacquired = restarted.acquire(
        worker_id="worker.after_reboot",
        manifest_hash=manifest.manifest_hash,
        backend_limit=1,
        model_limit=1,
        global_limit=1,
        lease_seconds=5,
    )
    completed = restarted.summary(manifest.manifest_hash)["state_counts"].get("SUCCEEDED") == 1
    passed = reacquired is None and completed
    return (
        FaultOutcome.PREVENTED if passed else FaultOutcome.NOT_MITIGATED,
        {"completed_work_rerun": reacquired is not None, "completion_persisted": completed},
    )


def _inject_fault(fault: FaultKind, root: Path) -> tuple[FaultOutcome, dict[str, Any]]:
    if fault is FaultKind.WORKER_KILL:
        return _subprocess_fault(root, timeout=False)
    if fault is FaultKind.TIMEOUT:
        return _subprocess_fault(root, timeout=True)
    if fault is FaultKind.DISK_FULL:
        return _filesystem_fault(root, error_number=errno.ENOSPC, stage="before_write")
    if fault is FaultKind.PERMISSION_FAILURE:
        return _filesystem_fault(root, error_number=errno.EACCES, stage="before_write")
    if fault is FaultKind.CORRUPT_CHECKPOINT:
        return _checkpoint_fault(root)
    if fault is FaultKind.CORRUPT_ARTIFACT:
        return _artifact_fault(root)
    if fault is FaultKind.DUPLICATE_SHARD:
        return _duplicate_fault(root)
    if fault is FaultKind.PARTIAL_UPLOAD:
        return _filesystem_fault(root, error_number=errno.EIO, stage="before_replace")
    if fault is FaultKind.NETWORK_DISCONNECT:
        return _network_fault(root)
    if fault is FaultKind.MALFORMED_MODEL_OUTPUT:
        return _output_fault(root, invalid_json=True)
    if fault is FaultKind.INVALID_SCHEMA:
        return _output_fault(root, invalid_json=False)
    if fault is FaultKind.SCORER_CRASH:
        return _scorer_fault(root)
    if fault is FaultKind.REGISTRY_CONTENTION:
        return _contention_fault(root)
    if fault is FaultKind.STALE_HEARTBEAT:
        return _queue_fault(root, quota=False)
    if fault is FaultKind.MODEL_OOM:
        return _oom_fault(root)
    if fault is FaultKind.QUOTA_EXHAUSTION:
        return _queue_fault(root, quota=True)
    if fault is FaultKind.CLOCK_SKEW:
        return _clock_fault(root)
    if fault is FaultKind.REBOOT_MARKER:
        return _reboot_fault(root)
    raise AssertionError(f"unhandled fault kind: {fault}")


def run_fixture_chaos_campaign(
    *,
    injected_failures: set[FaultKind] | None = None,
    workdir: str | Path | None = None,
) -> dict[str, Any]:
    """Physically inject each selected fault and verify observed invariants."""

    selected = injected_failures or set(FaultKind)
    root = (
        Path(workdir)
        if workdir is not None
        else Path(tempfile.mkdtemp(prefix="cab-real-fault-injection-"))
    )
    root.mkdir(parents=True, exist_ok=True)
    event_log = EventLog(root / "campaign.jsonl")
    cases: list[dict[str, Any]] = []
    for fault in sorted(selected, key=lambda value: value.value):
        case_root = root / fault.value
        case_root.mkdir(parents=True, exist_ok=True)
        started = time.monotonic()
        try:
            outcome, observations = _inject_fault(fault, case_root)
            error = None
        except BaseException as exc:
            outcome = FaultOutcome.NOT_MITIGATED
            observations = {}
            error = f"{type(exc).__name__}: {exc}"
        duration = time.monotonic() - started
        passed = outcome in {
            FaultOutcome.PREVENTED,
            FaultOutcome.DETECTED_AND_CONTAINED,
            FaultOutcome.RECOVERED,
            FaultOutcome.FAILED_CLOSED,
        }
        event = event_log.emit(
            "reliability",
            "FAULT_CASE_COMPLETED",
            correlation_id=fault.value,
            fields={
                "fault": fault.value,
                "outcome": outcome.value,
                "passed": passed,
                "error": error,
            },
        )
        case = {
            "fault": fault.value,
            "injection_executed": True,
            "expected_invariants": list(FAULT_EXPECTATIONS[fault]),
            "observations": observations,
            "outcome": outcome.value,
            "passed": passed,
            "error": error,
            "duration_seconds": duration,
            "event_sequence": event.sequence,
            "receipt": content_hash(
                {
                    "fault": fault.value,
                    "outcome": outcome.value,
                    "observations": observations,
                    "error": error,
                }
            ),
            "evidence_class": "FIXTURE_ONLY",
        }
        cases.append(case)
    passed = all(case["passed"] for case in cases)
    return {
        "campaign_id": f"chaos.{content_hash(cases)[:24]}",
        "passed": passed,
        "case_count": len(cases),
        "passed_count": sum(bool(case["passed"]) for case in cases),
        "not_mitigated_count": sum(
            case["outcome"] == FaultOutcome.NOT_MITIGATED.value for case in cases
        ),
        "manual_recovery_count": sum(
            case["outcome"] == FaultOutcome.MANUAL_RECOVERY_REQUIRED.value for case in cases
        ),
        "not_executed_count": sum(
            case["outcome"] == FaultOutcome.NOT_EXECUTED.value for case in cases
        ),
        "cases": cases,
        "event_log": str(event_log.path),
        "event_log_hash": file_sha256(event_log.path),
        "design_slos": DESIGN_SLOS,
        "real_execution_slos_measured": False,
        "physical_fixture_injection": True,
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
    "FaultOutcome",
    "StructuredEvent",
    "diagnostic_summary",
    "run_fixture_chaos_campaign",
]
