"""Backend-agnostic run planning, fixture scheduling, and immutable artifact storage."""

from __future__ import annotations

import json
import os
import resource
import secrets
import signal
import subprocess
import tempfile
import threading
import time
import zlib
from collections.abc import Callable, Mapping
from concurrent.futures import ThreadPoolExecutor
from contextlib import suppress
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field

from causal_agent_bench.level5.core import (
    ActorClass,
    EvidenceClass,
    canonical_json,
    content_hash,
    sha256_bytes,
    utc_now,
)
from causal_agent_bench.level5.registry import Registry, SQLiteRegistry


class RunPlanSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    study_id: str
    task_version: str
    split_version: str
    model_versions: list[str] = Field(min_length=1)
    policies: list[str] = Field(min_length=1)
    repeats: int = Field(default=1, ge=1)
    seeds: list[int] = Field(min_length=1)
    task_ids: list[str] = Field(min_length=1)
    scorer_version: str
    code_revision: str
    backend: str = "fixture"
    max_concurrency: int = Field(default=2, ge=1)
    max_attempts: int = Field(default=2, ge=1)
    timeout_seconds: float = Field(default=30.0, gt=0)


class RunUnit(BaseModel):
    unit_id: str
    task_id: str
    model_version: str
    policy: str
    repeat: int
    seed: int
    shard: int


class RunManifest(BaseModel):
    schema_version: str = "1.0"
    manifest_id: str
    manifest_hash: str
    spec: RunPlanSpec
    units: list[RunUnit]
    shard_count: int
    resource_projection: dict[str, Any]
    approval_requirements: list[str]


def compile_run_plan(spec: RunPlanSpec, *, shard_count: int = 2) -> RunManifest:
    if shard_count < 1:
        raise ValueError("shard_count must be positive")
    raw_units: list[dict[str, Any]] = []
    index = 0
    for task_id in sorted(spec.task_ids):
        for model in sorted(spec.model_versions):
            for policy in sorted(spec.policies):
                for repeat in range(spec.repeats):
                    seed = spec.seeds[repeat % len(spec.seeds)]
                    identity = {
                        "task_id": task_id,
                        "model_version": model,
                        "policy": policy,
                        "repeat": repeat,
                        "seed": seed,
                    }
                    raw_units.append(
                        {
                            **identity,
                            "unit_id": f"unit.{content_hash(identity)[:24]}",
                            "shard": index % shard_count,
                        }
                    )
                    index += 1
    units = [RunUnit.model_validate(unit) for unit in raw_units]
    payload = {
        "spec": spec.model_dump(mode="json"),
        "units": [unit.model_dump(mode="json") for unit in units],
        "shard_count": shard_count,
    }
    digest = content_hash(payload)
    provider_backends = {"openai", "anthropic", "gemini", "provider"}
    approvals = (
        ["explicit_live_execution_approval", "provider_budget_approval"]
        if spec.backend in provider_backends
        else []
    )
    return RunManifest(
        manifest_id=f"manifest.{digest[:24]}",
        manifest_hash=digest,
        spec=spec,
        units=units,
        shard_count=shard_count,
        resource_projection={
            "unit_count": len(units),
            "max_concurrency": spec.max_concurrency,
            "projected_only": True,
            "estimated_worker_seconds": len(units),
        },
        approval_requirements=approvals,
    )


@dataclass(frozen=True)
class ArtifactMetadata:
    digest: str
    size_bytes: int
    stored_size_bytes: int
    media_type: str
    artifact_class: str
    compressed: bool
    created_at: str


class ContentAddressedStore:
    """Filesystem SHA-256 CAS with atomic writes, verification, and bundles."""

    def __init__(
        self,
        root: str | Path,
        *,
        fault_injector: Callable[[str, Path], None] | None = None,
    ) -> None:
        self.root = Path(root)
        self.objects = self.root / "objects"
        self.staging = self.root / "staging"
        self.fault_injector = fault_injector
        self.objects.mkdir(parents=True, exist_ok=True)
        self.staging.mkdir(parents=True, exist_ok=True)

    def _object_path(self, digest: str) -> Path:
        return self.objects / digest[:2] / digest[2:]

    def _metadata_path(self, digest: str) -> Path:
        return self._object_path(digest).with_suffix(".metadata.json")

    def put_bytes(
        self,
        data: bytes,
        *,
        media_type: str = "application/octet-stream",
        artifact_class: str = "derived",
        compress: bool = False,
    ) -> ArtifactMetadata:
        if artifact_class not in {"raw", "derived", "fixture"}:
            raise ValueError("artifact_class must be raw, derived, or fixture")
        digest = sha256_bytes(data)
        object_path = self._object_path(digest)
        metadata_path = self._metadata_path(digest)
        object_path.parent.mkdir(parents=True, exist_ok=True)
        stored = zlib.compress(data, level=9) if compress else data
        metadata = ArtifactMetadata(
            digest=digest,
            size_bytes=len(data),
            stored_size_bytes=len(stored),
            media_type=media_type,
            artifact_class=artifact_class,
            compressed=compress,
            created_at=utc_now(),
        )
        if object_path.exists():
            existing = self.get_bytes(digest)
            if existing != data:
                raise ValueError(f"CAS collision or corruption at {digest}")
            return self.metadata(digest)

        descriptor, staging_name = tempfile.mkstemp(prefix="cas.", dir=self.staging)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                if self.fault_injector:
                    self.fault_injector("before_write", Path(staging_name))
                handle.write(stored)
                handle.flush()
                os.fsync(handle.fileno())
            if self.fault_injector:
                self.fault_injector("before_replace", Path(staging_name))
            os.replace(staging_name, object_path)
            if self.fault_injector:
                self.fault_injector("before_metadata", metadata_path)
            metadata_path.write_text(
                json.dumps(metadata.__dict__, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        finally:
            staging_path = Path(staging_name)
            if staging_path.exists():
                staging_path.unlink()
        return metadata

    def put_json(
        self,
        value: Any,
        *,
        artifact_class: str = "derived",
        compress: bool = False,
    ) -> ArtifactMetadata:
        return self.put_bytes(
            canonical_json(value).encode("utf-8"),
            media_type="application/json",
            artifact_class=artifact_class,
            compress=compress,
        )

    def get_bytes(self, digest: str) -> bytes:
        metadata = self.metadata(digest)
        stored = self._object_path(digest).read_bytes()
        data = zlib.decompress(stored) if metadata.compressed else stored
        if sha256_bytes(data) != digest:
            raise ValueError(f"artifact integrity failure: {digest}")
        return data

    def metadata(self, digest: str) -> ArtifactMetadata:
        path = self._metadata_path(digest)
        if not path.is_file():
            raise KeyError(f"artifact metadata not found: {digest}")
        return ArtifactMetadata(**json.loads(path.read_text(encoding="utf-8")))

    def verify(self, digest: str | None = None) -> dict[str, Any]:
        if digest is not None:
            digests = [digest]
        else:
            digests = sorted(
                path.parent.name + path.name.removesuffix(".metadata.json")
                for path in self.objects.glob("*/*.metadata.json")
            )
        errors: list[str] = []
        verified = 0
        for value in digests:
            try:
                self.get_bytes(value)
            except (KeyError, OSError, ValueError, zlib.error) as exc:
                errors.append(f"{value}: {exc}")
            else:
                verified += 1
        return {"passed": not errors, "verified": verified, "errors": errors}

    def export_bundle(self, digests: list[str], destination: str | Path) -> Path:
        destination = Path(destination)
        destination.mkdir(parents=True, exist_ok=True)
        manifest: list[dict[str, Any]] = []
        for digest in sorted(set(digests)):
            data = self.get_bytes(digest)
            metadata = self.metadata(digest)
            (destination / f"{digest}.blob").write_bytes(data)
            manifest.append(metadata.__dict__)
        (destination / "bundle_manifest.json").write_text(
            json.dumps({"artifacts": manifest}, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return destination

    def import_bundle(self, source: str | Path) -> list[str]:
        source = Path(source)
        payload = json.loads((source / "bundle_manifest.json").read_text(encoding="utf-8"))
        imported: list[str] = []
        for row in payload["artifacts"]:
            digest = str(row["digest"])
            data = (source / f"{digest}.blob").read_bytes()
            metadata = self.put_bytes(
                data,
                media_type=str(row["media_type"]),
                artifact_class=str(row["artifact_class"]),
                compress=bool(row["compressed"]),
            )
            if metadata.digest != digest:
                raise ValueError(f"bundle hash mismatch: {digest}")
            imported.append(digest)
        return imported

    def gc_dry_run(self, referenced: set[str]) -> dict[str, Any]:
        observed = {
            path.parent.name + path.name.removesuffix(".metadata.json")
            for path in self.objects.glob("*/*.metadata.json")
        }
        candidates = sorted(observed - referenced)
        return {
            "dry_run": True,
            "candidate_count": len(candidates),
            "candidate_digests": candidates,
            "deleted": 0,
        }


class Backend(Protocol):
    name: str

    def capabilities(self) -> Mapping[str, Any]: ...

    def prepare(self, manifest: RunManifest) -> None: ...

    def execute(self, unit: RunUnit, *, attempt: int) -> dict[str, Any]: ...

    def cancel(self, unit_id: str) -> None: ...

    def cleanup(self) -> None: ...


class FixtureBackend:
    name = "fixture"

    def __init__(self, fail_once: set[str] | None = None) -> None:
        self.fail_once = set(fail_once or set())
        self._cancelled: set[str] = set()

    def capabilities(self) -> Mapping[str, Any]:
        return {
            "fixture_only": True,
            "checkpoint": True,
            "resume": True,
            "network": False,
        }

    def prepare(self, manifest: RunManifest) -> None:
        if manifest.spec.backend != self.name:
            raise ValueError(
                f"backend mismatch: manifest={manifest.spec.backend} backend={self.name}"
            )

    def execute(self, unit: RunUnit, *, attempt: int) -> dict[str, Any]:
        if unit.unit_id in self._cancelled:
            raise RuntimeError("unit cancelled")
        if unit.unit_id in self.fail_once and attempt == 1:
            raise RuntimeError("deterministic fixture failure")
        return {
            "unit_id": unit.unit_id,
            "task_id": unit.task_id,
            "model_version": unit.model_version,
            "policy": unit.policy,
            "repeat": unit.repeat,
            "seed": unit.seed,
            "fixture_output": content_hash(unit.model_dump(mode="json")),
            "evidence_class": "FIXTURE_ONLY",
        }

    def cancel(self, unit_id: str) -> None:
        self._cancelled.add(unit_id)

    def cleanup(self) -> None:
        return


class LocalScheduler:
    """Deterministic local scheduler with retries and checkpoint-based resume."""

    def __init__(
        self,
        backend: Backend,
        store: ContentAddressedStore,
        *,
        registry: Registry | None = None,
    ) -> None:
        self.backend = backend
        self.store = store
        self.registry = registry

    def run(
        self,
        manifest: RunManifest,
        run_dir: str | Path,
        *,
        interrupt_after: int | None = None,
    ) -> dict[str, Any]:
        run_dir = Path(run_dir)
        run_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = run_dir / "run_manifest.json"
        checkpoint_path = run_dir / "checkpoint.json"
        if manifest_path.exists():
            previous = json.loads(manifest_path.read_text(encoding="utf-8"))
            if previous.get("manifest_hash") != manifest.manifest_hash:
                raise ValueError("resume requires an identical immutable manifest")
        else:
            manifest_path.write_text(
                manifest.model_dump_json(indent=2) + "\n", encoding="utf-8"
            )
        checkpoint: dict[str, Any] = (
            json.loads(checkpoint_path.read_text(encoding="utf-8"))
            if checkpoint_path.exists()
            else {
                "manifest_hash": manifest.manifest_hash,
                "completed": {},
                "attempts": {},
                "failures": {},
            }
        )
        validate_checkpoint(checkpoint, manifest)

        if self.registry is not None:
            self.registry.register(
                "run_manifest",
                manifest.manifest_id,
                {
                    "manifest_hash": manifest.manifest_hash,
                    "unit_count": len(manifest.units),
                    "backend": manifest.spec.backend,
                },
                freeze=True,
            )
        self.backend.prepare(manifest)
        completed_this_call = 0
        try:
            for unit in manifest.units:
                if unit.unit_id in checkpoint["completed"]:
                    continue
                if interrupt_after is not None and completed_this_call >= interrupt_after:
                    break
                success = False
                while int(checkpoint["attempts"].get(unit.unit_id, 0)) < manifest.spec.max_attempts:
                    attempt = int(checkpoint["attempts"].get(unit.unit_id, 0)) + 1
                    checkpoint["attempts"][unit.unit_id] = attempt
                    try:
                        result = self.backend.execute(unit, attempt=attempt)
                    except Exception as exc:
                        checkpoint["failures"][unit.unit_id] = {
                            "attempt": attempt,
                            "error_type": type(exc).__name__,
                            "message": str(exc),
                        }
                        self._write_checkpoint(checkpoint_path, checkpoint)
                        continue
                    metadata = self.store.put_json(result, artifact_class="fixture", compress=True)
                    checkpoint["completed"][unit.unit_id] = metadata.digest
                    checkpoint["failures"].pop(unit.unit_id, None)
                    self._write_checkpoint(checkpoint_path, checkpoint)
                    completed_this_call += 1
                    success = True
                    if self.registry is not None:
                        artifact_id = f"artifact.{metadata.digest[:24]}"
                        self.registry.register(
                            "artifact",
                            artifact_id,
                            {
                                "digest": metadata.digest,
                                "artifact_class": metadata.artifact_class,
                                "unit_id": unit.unit_id,
                            },
                            freeze=True,
                        )
                    break
                if not success and checkpoint["attempts"][unit.unit_id] >= manifest.spec.max_attempts:
                    continue
        finally:
            self.backend.cleanup()
        status = (
            "COMPLETE"
            if len(checkpoint["completed"]) == len(manifest.units)
            else "INTERRUPTED"
        )
        merged = self.merge(manifest, checkpoint)
        merge_metadata = self.store.put_json(merged, artifact_class="fixture", compress=True)
        report = {
            "status": status,
            "manifest_hash": manifest.manifest_hash,
            "total_units": len(manifest.units),
            "completed_units": len(checkpoint["completed"]),
            "failed_units": len(checkpoint["failures"]),
            "merge_digest": merge_metadata.digest,
            "duplicate_units": 0,
            "missing_units": len(manifest.units) - len(checkpoint["completed"]),
            "evidence_class": "FIXTURE_ONLY",
        }
        (run_dir / "run_report.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        return report

    def merge(self, manifest: RunManifest, checkpoint: Mapping[str, Any]) -> dict[str, Any]:
        completed = checkpoint.get("completed", {})
        if len(completed) != len(set(completed)):
            raise ValueError("duplicate completed unit IDs")
        results = [
            json.loads(self.store.get_bytes(str(completed[unit.unit_id])))
            for unit in manifest.units
            if unit.unit_id in completed
        ]
        return {
            "manifest_hash": manifest.manifest_hash,
            "results": results,
            "result_count": len(results),
            "evidence_class": "FIXTURE_ONLY",
        }

    @staticmethod
    def _write_checkpoint(path: Path, checkpoint: Mapping[str, Any]) -> None:
        temporary = path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(dict(checkpoint), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, path)


def validate_checkpoint(checkpoint: Mapping[str, Any], manifest: RunManifest) -> None:
    """Fail closed on corrupt, foreign, or structurally invalid checkpoints."""

    required = {"manifest_hash", "completed", "attempts", "failures"}
    missing = required - set(checkpoint)
    if missing:
        raise ValueError(f"checkpoint missing required fields: {sorted(missing)}")
    if checkpoint["manifest_hash"] != manifest.manifest_hash:
        raise ValueError("checkpoint manifest hash mismatch")
    for field in ("completed", "attempts", "failures"):
        if not isinstance(checkpoint[field], dict):
            raise ValueError(f"checkpoint {field} must be an object")
    known_units = {unit.unit_id for unit in manifest.units}
    completed = checkpoint["completed"]
    unknown = set(completed) - known_units
    if unknown:
        raise ValueError(f"checkpoint contains unknown completed units: {sorted(unknown)}")
    for unit_id, digest in completed.items():
        if not isinstance(digest, str) or len(digest) != 64:
            raise ValueError(f"checkpoint has invalid artifact digest for {unit_id}")
    for unit_id, attempt in checkpoint["attempts"].items():
        if unit_id not in known_units or not isinstance(attempt, int) or attempt < 0:
            raise ValueError(f"checkpoint has invalid attempt record for {unit_id}")


class RunState(StrEnum):
    PLANNED = "PLANNED"
    QUEUED = "QUEUED"
    LEASED = "LEASED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    CHECKPOINTING = "CHECKPOINTING"
    PAUSED = "PAUSED"
    RETRY_WAIT = "RETRY_WAIT"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    TIMED_OUT = "TIMED_OUT"
    QUOTA_DEFERRED = "QUOTA_DEFERRED"
    STALE = "STALE"
    AUDIT_REQUIRED = "AUDIT_REQUIRED"


RUN_TRANSITIONS: dict[RunState, frozenset[RunState]] = {
    RunState.PLANNED: frozenset({RunState.QUEUED, RunState.CANCELLED}),
    RunState.QUEUED: frozenset(
        {RunState.LEASED, RunState.PAUSED, RunState.CANCELLED, RunState.QUOTA_DEFERRED}
    ),
    RunState.LEASED: frozenset(
        {RunState.STARTING, RunState.STALE, RunState.CANCELLED, RunState.RETRY_WAIT}
    ),
    RunState.STARTING: frozenset(
        {RunState.RUNNING, RunState.FAILED, RunState.TIMED_OUT, RunState.CANCELLED}
    ),
    RunState.RUNNING: frozenset(
        {
            RunState.CHECKPOINTING,
            RunState.SUCCEEDED,
            RunState.RETRY_WAIT,
            RunState.FAILED,
            RunState.TIMED_OUT,
            RunState.CANCELLED,
            RunState.STALE,
        }
    ),
    RunState.CHECKPOINTING: frozenset(
        {RunState.RUNNING, RunState.PAUSED, RunState.FAILED}
    ),
    RunState.PAUSED: frozenset({RunState.QUEUED, RunState.CANCELLED}),
    RunState.RETRY_WAIT: frozenset(
        {RunState.LEASED, RunState.FAILED, RunState.CANCELLED}
    ),
    RunState.STALE: frozenset(
        {RunState.LEASED, RunState.RETRY_WAIT, RunState.FAILED, RunState.CANCELLED}
    ),
    RunState.QUOTA_DEFERRED: frozenset({RunState.QUEUED, RunState.CANCELLED}),
    RunState.SUCCEEDED: frozenset(),
    RunState.FAILED: frozenset(),
    RunState.CANCELLED: frozenset(),
    RunState.TIMED_OUT: frozenset(),
    RunState.AUDIT_REQUIRED: frozenset(),
}

TERMINAL_RUN_STATES = frozenset(
    {
        RunState.SUCCEEDED,
        RunState.FAILED,
        RunState.CANCELLED,
        RunState.TIMED_OUT,
        RunState.QUOTA_DEFERRED,
        RunState.AUDIT_REQUIRED,
    }
)


class FailureClass(StrEnum):
    TRANSIENT = "TRANSIENT"
    WORKER_KILLED = "WORKER_KILLED"
    TIMEOUT = "TIMEOUT"
    CANCELLED = "CANCELLED"
    OOM = "OOM"
    INVALID_OUTPUT = "INVALID_OUTPUT"
    PERMANENT = "PERMANENT"


class ExecutionFailure(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        failure_class: FailureClass,
        retryable: bool,
    ) -> None:
        super().__init__(message)
        self.failure_class = failure_class
        self.retryable = retryable


class BackendCapabilities(BaseModel):
    execution: bool = True
    fixture_only: bool = False
    subprocess: bool = False
    checkpoint: bool = False
    resume: bool = False
    cancellation: bool = True
    heartbeat: bool = True
    network: bool = False
    accelerator: str | None = None


class ResourceEstimate(BaseModel):
    cpu_units: float = Field(default=1.0, gt=0)
    memory_mb: int = Field(default=128, ge=1)
    wall_seconds: float = Field(default=30.0, gt=0)


class BackendResult(BaseModel):
    unit_id: str
    output: dict[str, Any]
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    failure_class: FailureClass | None = None
    orphan_processes: int = 0
    resource_use: dict[str, float] = Field(default_factory=dict)


class OperationalBackend(Protocol):
    name: str
    version: str

    def capabilities(self) -> BackendCapabilities: ...

    def validate_compatibility(self, manifest: RunManifest) -> list[str]: ...

    def estimate_resources(self, unit: RunUnit) -> ResourceEstimate: ...

    def prepare(self, manifest: RunManifest) -> None: ...

    def launch(self, unit: RunUnit, *, attempt: int) -> str: ...

    def poll(self, handle: str) -> str: ...

    def heartbeat(self, handle: str) -> dict[str, Any]: ...

    def checkpoint(self, handle: str) -> dict[str, Any]: ...

    def resume(self, unit: RunUnit, checkpoint: Mapping[str, Any], *, attempt: int) -> str: ...

    def cancel(self, unit_id: str) -> None: ...

    def collect(self, handle: str, *, timeout_seconds: float) -> BackendResult: ...

    def cleanup(self, handle: str | None = None) -> None: ...

    def classify_failure(self, error: BaseException) -> tuple[FailureClass, bool]: ...

    def provenance_receipt(
        self, unit: RunUnit, result: BackendResult, *, attempt: int
    ) -> dict[str, Any]: ...


@dataclass(frozen=True)
class UnitLease:
    unit: RunUnit
    worker_id: str
    token: str
    attempt: int
    generation: int


class QueueRepository:
    """SQLite-backed priority queue, leases, heartbeats, retries, and quotas."""

    def __init__(self, registry: SQLiteRegistry) -> None:
        self.registry = registry
        self.registry.initialize()

    @staticmethod
    def _event(
        connection: Any,
        *,
        unit_id: str | None,
        event_type: str,
        previous: RunState | None,
        new: RunState | None,
        payload: Mapping[str, Any] | None = None,
    ) -> None:
        connection.execute(
            """
            INSERT INTO scheduler_events(
                event_id, unit_id, event_type, previous_state, new_state,
                payload_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"sched.{secrets.token_hex(16)}",
                unit_id,
                event_type,
                previous.value if previous else None,
                new.value if new else None,
                canonical_json(dict(payload or {})),
                utc_now(),
            ),
        )

    @staticmethod
    def _assert_transition(source: RunState, target: RunState) -> None:
        if target not in RUN_TRANSITIONS[source]:
            raise ValueError(f"invalid scheduler transition: {source.value} -> {target.value}")

    def enqueue(
        self,
        manifest: RunManifest,
        *,
        dependencies: Mapping[str, list[str]] | None = None,
        priorities: Mapping[str, int] | None = None,
        quota_keys: Mapping[str, str] | None = None,
    ) -> None:
        dependencies = dependencies or {}
        priorities = priorities or {}
        quota_keys = quota_keys or {}
        with self.registry.transaction() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO scheduler_controls(manifest_hash, state, updated_at)
                VALUES (?, 'RUNNING', ?)
                """,
                (manifest.manifest_hash, utc_now()),
            )
            for unit in manifest.units:
                payload = unit.model_dump(mode="json")
                payload_hash = content_hash(payload)
                row = connection.execute(
                    "SELECT payload_hash, manifest_hash FROM queue_entries WHERE unit_id=?",
                    (unit.unit_id,),
                ).fetchone()
                if row:
                    if (
                        str(row["payload_hash"]) != payload_hash
                        or str(row["manifest_hash"]) != manifest.manifest_hash
                    ):
                        raise ValueError(f"idempotency conflict for queued unit {unit.unit_id}")
                    continue
                connection.execute(
                    """
                    INSERT INTO queue_entries(
                        unit_id, manifest_hash, study_id, backend, model_version,
                        priority, state, dependencies_json, payload_json, payload_hash,
                        available_at, attempt_count, max_attempts, quota_key,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?)
                    """,
                    (
                        unit.unit_id,
                        manifest.manifest_hash,
                        manifest.spec.study_id,
                        manifest.spec.backend,
                        unit.model_version,
                        int(priorities.get(unit.unit_id, 0)),
                        RunState.QUEUED.value,
                        canonical_json(sorted(dependencies.get(unit.unit_id, []))),
                        canonical_json(payload),
                        payload_hash,
                        time.time(),
                        manifest.spec.max_attempts,
                        quota_keys.get(unit.unit_id, "default"),
                        utc_now(),
                        utc_now(),
                    ),
                )
                self._event(
                    connection,
                    unit_id=unit.unit_id,
                    event_type="ENQUEUED",
                    previous=RunState.PLANNED,
                    new=RunState.QUEUED,
                    payload={"manifest_hash": manifest.manifest_hash},
                )

    def set_quota(self, quota_key: str, allowance: int) -> None:
        if allowance < 0:
            raise ValueError("quota allowance must be non-negative")
        with self.registry.transaction() as connection:
            connection.execute(
                """
                INSERT INTO scheduler_quotas(quota_key, allowance, consumed, updated_at)
                VALUES (?, ?, 0, ?)
                ON CONFLICT(quota_key) DO UPDATE SET
                    allowance=excluded.allowance,
                    consumed=0,
                    updated_at=excluded.updated_at
                """,
                (quota_key, allowance, utc_now()),
            )

    def pause(self, manifest_hash: str) -> None:
        with self.registry.transaction() as connection:
            connection.execute(
                "UPDATE scheduler_controls SET state='PAUSED', updated_at=? "
                "WHERE manifest_hash=?",
                (utc_now(), manifest_hash),
            )
            rows = connection.execute(
                "SELECT unit_id, state FROM queue_entries "
                "WHERE manifest_hash=? AND state='QUEUED'",
                (manifest_hash,),
            ).fetchall()
            for row in rows:
                connection.execute(
                    "UPDATE queue_entries SET state=?, updated_at=? WHERE unit_id=?",
                    (RunState.PAUSED.value, utc_now(), row["unit_id"]),
                )
                self._event(
                    connection,
                    unit_id=str(row["unit_id"]),
                    event_type="PAUSED",
                    previous=RunState.QUEUED,
                    new=RunState.PAUSED,
                )

    def resume(self, manifest_hash: str) -> None:
        with self.registry.transaction() as connection:
            connection.execute(
                "UPDATE scheduler_controls SET state='RUNNING', updated_at=? "
                "WHERE manifest_hash=?",
                (utc_now(), manifest_hash),
            )
            rows = connection.execute(
                "SELECT unit_id FROM queue_entries "
                "WHERE manifest_hash=? AND state='PAUSED'",
                (manifest_hash,),
            ).fetchall()
            for row in rows:
                connection.execute(
                    "UPDATE queue_entries SET state=?, available_at=?, updated_at=? "
                    "WHERE unit_id=?",
                    (RunState.QUEUED.value, time.time(), utc_now(), row["unit_id"]),
                )
                self._event(
                    connection,
                    unit_id=str(row["unit_id"]),
                    event_type="RESUMED",
                    previous=RunState.PAUSED,
                    new=RunState.QUEUED,
                )

    def acquire(
        self,
        *,
        worker_id: str,
        manifest_hash: str,
        backend_limit: int,
        model_limit: int,
        global_limit: int,
        lease_seconds: float,
    ) -> UnitLease | None:
        now = time.time()
        with self.registry.transaction() as connection:
            control = connection.execute(
                "SELECT state FROM scheduler_controls WHERE manifest_hash=?",
                (manifest_hash,),
            ).fetchone()
            if not control or str(control["state"]) != "RUNNING":
                return None
            if int(
                connection.execute("SELECT COUNT(*) FROM worker_leases").fetchone()[0]
            ) >= global_limit:
                return None
            rows = connection.execute(
                """
                SELECT q.*,
                       (
                         SELECT COUNT(*)
                           FROM scheduler_attempts a
                           JOIN queue_entries q2 ON q2.unit_id=a.unit_id
                          WHERE q2.study_id=q.study_id
                       ) AS study_attempts
                  FROM queue_entries q
                 WHERE q.manifest_hash=?
                   AND q.state IN ('QUEUED', 'RETRY_WAIT', 'STALE')
                   AND q.available_at <= ?
                 ORDER BY q.priority DESC, study_attempts ASC, q.study_id, q.unit_id
                 LIMIT 256
                """,
                (manifest_hash, now),
            ).fetchall()
            for row in rows:
                dependencies = json.loads(str(row["dependencies_json"]))
                if dependencies:
                    placeholders = ",".join("?" for _ in dependencies)
                    dependency_rows = connection.execute(
                        f"SELECT unit_id, state FROM queue_entries "
                        f"WHERE unit_id IN ({placeholders})",
                        tuple(dependencies),
                    ).fetchall()
                    states = {str(value["unit_id"]): str(value["state"]) for value in dependency_rows}
                    if any(
                        states.get(dependency) in {
                            RunState.FAILED.value,
                            RunState.CANCELLED.value,
                            RunState.TIMED_OUT.value,
                            RunState.AUDIT_REQUIRED.value,
                        }
                        for dependency in dependencies
                    ):
                        source = RunState(str(row["state"]))
                        connection.execute(
                            "UPDATE queue_entries SET state=?, terminal_reason=?, updated_at=? "
                            "WHERE unit_id=?",
                            (
                                RunState.AUDIT_REQUIRED.value,
                                "dependency did not succeed",
                                utc_now(),
                                row["unit_id"],
                            ),
                        )
                        self._event(
                            connection,
                            unit_id=str(row["unit_id"]),
                            event_type="DEPENDENCY_FAILED",
                            previous=source,
                            new=RunState.AUDIT_REQUIRED,
                        )
                        continue
                    if any(
                        states.get(dependency) != RunState.SUCCEEDED.value
                        for dependency in dependencies
                    ):
                        continue
                backend = str(row["backend"])
                model_version = str(row["model_version"])
                backend_active = int(
                    connection.execute(
                        """
                        SELECT COUNT(*) FROM worker_leases l
                        JOIN queue_entries q ON q.unit_id=l.unit_id
                        WHERE q.backend=?
                        """,
                        (backend,),
                    ).fetchone()[0]
                )
                if backend_active >= backend_limit:
                    continue
                model_active = int(
                    connection.execute(
                        """
                        SELECT COUNT(*) FROM worker_leases l
                        JOIN queue_entries q ON q.unit_id=l.unit_id
                        WHERE q.model_version=?
                        """,
                        (model_version,),
                    ).fetchone()[0]
                )
                if model_active >= model_limit:
                    continue
                quota_key = str(row["quota_key"])
                quota = connection.execute(
                    "SELECT allowance, consumed FROM scheduler_quotas WHERE quota_key=?",
                    (quota_key,),
                ).fetchone()
                if quota and int(quota["consumed"]) >= int(quota["allowance"]):
                    source = RunState(str(row["state"]))
                    connection.execute(
                        "UPDATE queue_entries SET state=?, terminal_reason=?, updated_at=? "
                        "WHERE unit_id=?",
                        (
                            RunState.QUOTA_DEFERRED.value,
                            f"quota exhausted: {quota_key}",
                            utc_now(),
                            row["unit_id"],
                        ),
                    )
                    self._event(
                        connection,
                        unit_id=str(row["unit_id"]),
                        event_type="QUOTA_DEFERRED",
                        previous=source,
                        new=RunState.QUOTA_DEFERRED,
                        payload={"quota_key": quota_key},
                    )
                    continue
                if quota:
                    connection.execute(
                        "UPDATE scheduler_quotas SET consumed=consumed+1, updated_at=? "
                        "WHERE quota_key=?",
                        (utc_now(), quota_key),
                    )
                source = RunState(str(row["state"]))
                self._assert_transition(source, RunState.LEASED)
                attempt = int(row["attempt_count"]) + 1
                # Attempt numbers survive lease-row deletion, so they provide a
                # monotonic fencing generation across coordinator restarts.
                generation = attempt
                token = secrets.token_urlsafe(32)
                token_hash = sha256_bytes(token.encode("utf-8"))
                connection.execute(
                    "UPDATE queue_entries SET state=?, attempt_count=?, updated_at=? "
                    "WHERE unit_id=?",
                    (RunState.LEASED.value, attempt, utc_now(), row["unit_id"]),
                )
                connection.execute(
                    """
                    INSERT INTO worker_leases(
                        unit_id, worker_id, lease_token_hash, generation,
                        acquired_at, expires_at, heartbeat_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        row["unit_id"],
                        worker_id,
                        token_hash,
                        generation,
                        now,
                        now + lease_seconds,
                        now,
                    ),
                )
                attempt_id = f"attempt.{content_hash([row['unit_id'], attempt])[:24]}"
                connection.execute(
                    """
                    INSERT INTO scheduler_attempts(
                        attempt_id, unit_id, attempt_number, worker_id, state, started_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        attempt_id,
                        row["unit_id"],
                        attempt,
                        worker_id,
                        RunState.LEASED.value,
                        utc_now(),
                    ),
                )
                reservation_id = (
                    f"reservation.{content_hash([row['unit_id'], attempt, worker_id])[:24]}"
                )
                connection.execute(
                    """
                    INSERT INTO resource_reservations(
                        reservation_id, unit_id, backend, model_version, quota_key,
                        cpu_units, memory_mb, acquired_at
                    ) VALUES (?, ?, ?, ?, ?, 1.0, 128, ?)
                    """,
                    (
                        reservation_id,
                        row["unit_id"],
                        backend,
                        model_version,
                        quota_key,
                        now,
                    ),
                )
                connection.execute(
                    """
                    INSERT INTO worker_heartbeats(
                        worker_id, backend, last_seen, active_unit_id, generation, metadata_json
                    ) VALUES (?, ?, ?, ?, ?, '{}')
                    ON CONFLICT(worker_id) DO UPDATE SET
                        backend=excluded.backend,
                        last_seen=excluded.last_seen,
                        active_unit_id=excluded.active_unit_id,
                        generation=excluded.generation
                    """,
                    (worker_id, backend, now, row["unit_id"], generation),
                )
                self._event(
                    connection,
                    unit_id=str(row["unit_id"]),
                    event_type="LEASE_ACQUIRED",
                    previous=source,
                    new=RunState.LEASED,
                    payload={"worker_id": worker_id, "attempt": attempt},
                )
                return UnitLease(
                    unit=RunUnit.model_validate_json(str(row["payload_json"])),
                    worker_id=worker_id,
                    token=token,
                    attempt=attempt,
                    generation=generation,
                )
        return None

    def _lease_row(self, connection: Any, lease: UnitLease) -> Any:
        row = connection.execute(
            "SELECT * FROM worker_leases WHERE unit_id=?",
            (lease.unit.unit_id,),
        ).fetchone()
        if (
            row is None
            or str(row["worker_id"]) != lease.worker_id
            or str(row["lease_token_hash"]) != sha256_bytes(lease.token.encode("utf-8"))
            or int(row["generation"]) != lease.generation
        ):
            raise PermissionError("invalid or stale unit lease")
        return row

    def heartbeat(self, lease: UnitLease, *, lease_seconds: float) -> None:
        now = time.time()
        with self.registry.transaction() as connection:
            self._lease_row(connection, lease)
            connection.execute(
                "UPDATE worker_leases SET heartbeat_at=?, expires_at=? WHERE unit_id=?",
                (now, now + lease_seconds, lease.unit.unit_id),
            )
            connection.execute(
                "UPDATE worker_heartbeats SET last_seen=?, active_unit_id=? WHERE worker_id=?",
                (now, lease.unit.unit_id, lease.worker_id),
            )

    def mark_running(self, lease: UnitLease) -> None:
        with self.registry.transaction() as connection:
            self._lease_row(connection, lease)
            current = RunState(
                str(
                    connection.execute(
                        "SELECT state FROM queue_entries WHERE unit_id=?",
                        (lease.unit.unit_id,),
                    ).fetchone()["state"]
                )
            )
            for target in (RunState.STARTING, RunState.RUNNING):
                self._assert_transition(current, target)
                connection.execute(
                    "UPDATE queue_entries SET state=?, updated_at=? WHERE unit_id=?",
                    (target.value, utc_now(), lease.unit.unit_id),
                )
                connection.execute(
                    "UPDATE scheduler_attempts SET state=? "
                    "WHERE unit_id=? AND attempt_number=?",
                    (target.value, lease.unit.unit_id, lease.attempt),
                )
                self._event(
                    connection,
                    unit_id=lease.unit.unit_id,
                    event_type=target.value,
                    previous=current,
                    new=target,
                )
                current = target

    def stage_result(self, lease: UnitLease, digest: str) -> None:
        with self.registry.transaction() as connection:
            self._lease_row(connection, lease)
            connection.execute(
                """
                UPDATE scheduler_attempts
                   SET result_digest=?, receipt_json=?
                 WHERE unit_id=? AND attempt_number=?
                """,
                (
                    digest,
                    canonical_json({"stage": "CAS_VERIFIED", "digest": digest}),
                    lease.unit.unit_id,
                    lease.attempt,
                ),
            )

    def commit_success(self, lease: UnitLease, digest: str) -> bool:
        with self.registry.transaction() as connection:
            row = connection.execute(
                "SELECT state, result_digest FROM queue_entries WHERE unit_id=?",
                (lease.unit.unit_id,),
            ).fetchone()
            if row is None:
                raise KeyError(lease.unit.unit_id)
            if str(row["state"]) == RunState.SUCCEEDED.value:
                if str(row["result_digest"]) != digest:
                    raise ValueError("duplicate commit attempted with a different digest")
                return False
            self._lease_row(connection, lease)
            source = RunState(str(row["state"]))
            self._assert_transition(source, RunState.SUCCEEDED)
            connection.execute(
                """
                UPDATE queue_entries
                   SET state=?, result_digest=?, terminal_reason=NULL, updated_at=?
                 WHERE unit_id=? AND result_digest IS NULL
                """,
                (RunState.SUCCEEDED.value, digest, utc_now(), lease.unit.unit_id),
            )
            if connection.execute("SELECT changes()").fetchone()[0] != 1:
                return False
            connection.execute(
                """
                UPDATE scheduler_attempts
                   SET state=?, finished_at=?, result_digest=?
                 WHERE unit_id=? AND attempt_number=?
                """,
                (
                    RunState.SUCCEEDED.value,
                    utc_now(),
                    digest,
                    lease.unit.unit_id,
                    lease.attempt,
                ),
            )
            self._release(connection, lease)
            self._event(
                connection,
                unit_id=lease.unit.unit_id,
                event_type="RESULT_COMMITTED",
                previous=source,
                new=RunState.SUCCEEDED,
                payload={"digest": digest, "exactly_once": True},
            )
        return True

    def fail(
        self,
        lease: UnitLease,
        error: BaseException,
        *,
        failure_class: FailureClass,
        retryable: bool,
        retry_base_seconds: float,
    ) -> RunState:
        with self.registry.transaction() as connection:
            row = connection.execute(
                "SELECT state, attempt_count, max_attempts FROM queue_entries WHERE unit_id=?",
                (lease.unit.unit_id,),
            ).fetchone()
            if row is None:
                raise KeyError(lease.unit.unit_id)
            current = RunState(str(row["state"]))
            if current in TERMINAL_RUN_STATES:
                return current
            self._lease_row(connection, lease)
            attempts = int(row["attempt_count"])
            if failure_class is FailureClass.TIMEOUT:
                target = RunState.TIMED_OUT
            elif failure_class is FailureClass.CANCELLED:
                target = RunState.CANCELLED
            elif retryable and attempts < int(row["max_attempts"]):
                target = RunState.RETRY_WAIT
            else:
                target = RunState.FAILED
            self._assert_transition(current, target)
            deterministic_fraction = int(
                content_hash([lease.unit.unit_id, attempts])[:4], 16
            ) / 65535
            backoff = min(retry_base_seconds * (2 ** max(0, attempts - 1)), 30.0)
            available_at = time.time() + backoff + deterministic_fraction * retry_base_seconds
            connection.execute(
                """
                UPDATE queue_entries
                   SET state=?, available_at=?, terminal_reason=?, updated_at=?
                 WHERE unit_id=?
                """,
                (
                    target.value,
                    available_at,
                    f"{failure_class.value}: {error}",
                    utc_now(),
                    lease.unit.unit_id,
                ),
            )
            connection.execute(
                """
                UPDATE scheduler_attempts
                   SET state=?, finished_at=?, error_class=?, error_message=?
                 WHERE unit_id=? AND attempt_number=?
                """,
                (
                    target.value,
                    utc_now(),
                    failure_class.value,
                    str(error),
                    lease.unit.unit_id,
                    lease.attempt,
                ),
            )
            self._release(connection, lease)
            self._event(
                connection,
                unit_id=lease.unit.unit_id,
                event_type="ATTEMPT_FAILED",
                previous=current,
                new=target,
                payload={
                    "attempt": attempts,
                    "failure_class": failure_class.value,
                    "retryable": retryable,
                    "backoff_seconds": backoff if target is RunState.RETRY_WAIT else 0.0,
                },
            )
        return target

    @staticmethod
    def _release(connection: Any, lease: UnitLease) -> None:
        connection.execute(
            "DELETE FROM worker_leases WHERE unit_id=?",
            (lease.unit.unit_id,),
        )
        connection.execute(
            "UPDATE resource_reservations SET released_at=? "
            "WHERE unit_id=? AND released_at IS NULL",
            (time.time(), lease.unit.unit_id),
        )
        connection.execute(
            "UPDATE worker_heartbeats SET active_unit_id=NULL, last_seen=? WHERE worker_id=?",
            (time.time(), lease.worker_id),
        )

    def cancel(self, unit_id: str) -> bool:
        with self.registry.transaction() as connection:
            row = connection.execute(
                "SELECT state FROM queue_entries WHERE unit_id=?",
                (unit_id,),
            ).fetchone()
            if row is None:
                raise KeyError(unit_id)
            current = RunState(str(row["state"]))
            if current in TERMINAL_RUN_STATES:
                return False
            if RunState.CANCELLED not in RUN_TRANSITIONS[current]:
                raise ValueError(f"cannot cancel unit in {current.value}")
            connection.execute(
                "UPDATE queue_entries SET state=?, terminal_reason=?, updated_at=? "
                "WHERE unit_id=?",
                (RunState.CANCELLED.value, "cancelled by coordinator", utc_now(), unit_id),
            )
            connection.execute("DELETE FROM worker_leases WHERE unit_id=?", (unit_id,))
            connection.execute(
                "UPDATE resource_reservations SET released_at=? "
                "WHERE unit_id=? AND released_at IS NULL",
                (time.time(), unit_id),
            )
            self._event(
                connection,
                unit_id=unit_id,
                event_type="CANCELLED",
                previous=current,
                new=RunState.CANCELLED,
            )
        return True

    def reclaim_stale(self, *, now: float | None = None) -> int:
        now = time.time() if now is None else now
        reclaimed = 0
        with self.registry.transaction() as connection:
            rows = connection.execute(
                """
                SELECT l.*, q.state, q.attempt_count, q.max_attempts
                  FROM worker_leases l
                  JOIN queue_entries q ON q.unit_id=l.unit_id
                 WHERE l.expires_at < ?
                """,
                (now,),
            ).fetchall()
            for row in rows:
                current = RunState(str(row["state"]))
                target = (
                    RunState.RETRY_WAIT
                    if int(row["attempt_count"]) < int(row["max_attempts"])
                    else RunState.FAILED
                )
                if target not in RUN_TRANSITIONS[current]:
                    target = RunState.STALE
                connection.execute(
                    "UPDATE queue_entries SET state=?, available_at=?, terminal_reason=?, "
                    "updated_at=? WHERE unit_id=?",
                    (
                        target.value,
                        now,
                        "stale heartbeat lease reclaimed",
                        utc_now(),
                        row["unit_id"],
                    ),
                )
                connection.execute(
                    "UPDATE scheduler_attempts SET state=?, finished_at=?, "
                    "error_class=?, error_message=? WHERE unit_id=? AND attempt_number=?",
                    (
                        target.value,
                        utc_now(),
                        FailureClass.WORKER_KILLED.value,
                        "lease expired without heartbeat",
                        row["unit_id"],
                        row["attempt_count"],
                    ),
                )
                connection.execute(
                    "DELETE FROM worker_leases WHERE unit_id=?",
                    (row["unit_id"],),
                )
                connection.execute(
                    "UPDATE resource_reservations SET released_at=? "
                    "WHERE unit_id=? AND released_at IS NULL",
                    (now, row["unit_id"]),
                )
                self._event(
                    connection,
                    unit_id=str(row["unit_id"]),
                    event_type="STALE_LEASE_RECLAIMED",
                    previous=current,
                    new=target,
                )
                reclaimed += 1
        return reclaimed

    def recover_staged_results(self, store: ContentAddressedStore) -> int:
        recovered = 0
        with self.registry._connect() as connection:
            rows = connection.execute(
                """
                SELECT q.unit_id, a.attempt_number, a.worker_id, a.result_digest
                  FROM queue_entries q
                  JOIN scheduler_attempts a ON a.unit_id=q.unit_id
                 WHERE q.state NOT IN ('SUCCEEDED','FAILED','CANCELLED','TIMED_OUT')
                   AND a.result_digest IS NOT NULL
                   AND a.attempt_number=(
                       SELECT MAX(a2.attempt_number)
                         FROM scheduler_attempts a2
                        WHERE a2.unit_id=q.unit_id
                          AND a2.result_digest IS NOT NULL
                   )
                 ORDER BY a.attempt_number DESC
                """
            ).fetchall()
        for row in rows:
            digest = str(row["result_digest"])
            if store.verify(digest)["passed"]:
                with self.registry.transaction() as connection:
                    current = connection.execute(
                        "SELECT state FROM queue_entries WHERE unit_id=?",
                        (row["unit_id"],),
                    ).fetchone()
                    if current is None or RunState(str(current["state"])) in TERMINAL_RUN_STATES:
                        continue
                    connection.execute(
                        "UPDATE queue_entries SET state=?, result_digest=?, "
                        "terminal_reason=NULL, updated_at=? WHERE unit_id=?",
                        (RunState.SUCCEEDED.value, digest, utc_now(), row["unit_id"]),
                    )
                    connection.execute(
                        """
                        UPDATE scheduler_attempts
                           SET state=?, finished_at=?, result_digest=?
                         WHERE unit_id=? AND attempt_number=?
                        """,
                        (
                            RunState.SUCCEEDED.value,
                            utc_now(),
                            digest,
                            row["unit_id"],
                            row["attempt_number"],
                        ),
                    )
                    connection.execute(
                        "DELETE FROM worker_leases WHERE unit_id=?",
                        (row["unit_id"],),
                    )
                    connection.execute(
                        "UPDATE resource_reservations SET released_at=? "
                        "WHERE unit_id=? AND released_at IS NULL",
                        (time.time(), row["unit_id"]),
                    )
                    connection.execute(
                        "UPDATE worker_heartbeats SET active_unit_id=NULL, last_seen=? "
                        "WHERE worker_id=?",
                        (time.time(), row["worker_id"]),
                    )
                    self._event(
                        connection,
                        unit_id=str(row["unit_id"]),
                        event_type="STAGED_RESULT_RECOVERED",
                        previous=None,
                        new=RunState.SUCCEEDED,
                        payload={"digest": digest},
                    )
                recovered += 1
        return recovered

    def is_complete(self, manifest_hash: str) -> bool:
        with self.registry._connect() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS pending
                  FROM queue_entries
                 WHERE manifest_hash=?
                   AND state NOT IN (
                     'SUCCEEDED','FAILED','CANCELLED','TIMED_OUT',
                     'QUOTA_DEFERRED','AUDIT_REQUIRED'
                   )
                """,
                (manifest_hash,),
            ).fetchone()
        return int(row["pending"]) == 0

    def summary(self, manifest_hash: str) -> dict[str, Any]:
        with self.registry._connect() as connection:
            state_rows = connection.execute(
                "SELECT state, COUNT(*) AS count FROM queue_entries "
                "WHERE manifest_hash=? GROUP BY state",
                (manifest_hash,),
            ).fetchall()
            duplicates = int(
                connection.execute(
                    """
                    SELECT COUNT(*) FROM (
                        SELECT unit_id FROM scheduler_attempts
                        WHERE result_digest IS NOT NULL
                        GROUP BY unit_id HAVING COUNT(*) > 1
                    )
                    """
                ).fetchone()[0]
            )
            attempts = int(
                connection.execute(
                    """
                    SELECT COUNT(*) FROM scheduler_attempts a
                    JOIN queue_entries q ON q.unit_id=a.unit_id
                    WHERE q.manifest_hash=?
                    """,
                    (manifest_hash,),
                ).fetchone()[0]
            )
            results = connection.execute(
                "SELECT unit_id, result_digest, state FROM queue_entries "
                "WHERE manifest_hash=? ORDER BY unit_id",
                (manifest_hash,),
            ).fetchall()
        counts = {str(row["state"]): int(row["count"]) for row in state_rows}
        deterministic_rows = [
            {
                "unit_id": str(row["unit_id"]),
                "state": str(row["state"]),
                "result_digest": row["result_digest"],
            }
            for row in results
        ]
        return {
            "manifest_hash": manifest_hash,
            "state_counts": counts,
            "unit_count": len(results),
            "attempt_count": attempts,
            "duplicate_committed_results": duplicates,
            "missing_terminal_states": sum(
                count
                for state, count in counts.items()
                if RunState(state) not in TERMINAL_RUN_STATES
            ),
            "deterministic_merged_hash": content_hash(deterministic_rows),
        }

    def events(self) -> list[dict[str, Any]]:
        with self.registry._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM scheduler_events ORDER BY seq"
            ).fetchall()
        return [dict(row) for row in rows]


class ConcurrentFixtureBackend:
    name = "fixture"
    version = "2.0"

    def __init__(
        self,
        *,
        fail_once: set[str] | None = None,
        durations: Mapping[str, float] | None = None,
    ) -> None:
        self.fail_once = set(fail_once or set())
        self.durations = dict(durations or {})
        self._handles: dict[str, tuple[RunUnit, int]] = {}
        self._cancelled: set[str] = set()
        self._lock = threading.Lock()

    def capabilities(self) -> BackendCapabilities:
        return BackendCapabilities(
            fixture_only=True,
            checkpoint=True,
            resume=True,
            cancellation=True,
            heartbeat=True,
        )

    def validate_compatibility(self, manifest: RunManifest) -> list[str]:
        return [] if manifest.spec.backend == self.name else ["backend name mismatch"]

    def estimate_resources(self, unit: RunUnit) -> ResourceEstimate:
        return ResourceEstimate(wall_seconds=max(0.1, self.durations.get(unit.unit_id, 0.0) + 1))

    def prepare(self, manifest: RunManifest) -> None:
        errors = self.validate_compatibility(manifest)
        if errors:
            raise ValueError("; ".join(errors))

    def launch(self, unit: RunUnit, *, attempt: int) -> str:
        handle = f"fixture.{content_hash([unit.unit_id, attempt, time.monotonic_ns()])[:24]}"
        with self._lock:
            self._handles[handle] = (unit, attempt)
        return handle

    def poll(self, handle: str) -> str:
        return "CANCELLED" if self._handles[handle][0].unit_id in self._cancelled else "RUNNING"

    def heartbeat(self, handle: str) -> dict[str, Any]:
        return {"handle": handle, "state": self.poll(handle), "monotonic": time.monotonic()}

    def checkpoint(self, handle: str) -> dict[str, Any]:
        unit, attempt = self._handles[handle]
        return {
            "unit_id": unit.unit_id,
            "attempt": attempt,
            "checkpoint_hash": content_hash([unit.unit_id, attempt]),
        }

    def resume(self, unit: RunUnit, checkpoint: Mapping[str, Any], *, attempt: int) -> str:
        if checkpoint.get("unit_id") != unit.unit_id:
            raise ValueError("checkpoint unit mismatch")
        return self.launch(unit, attempt=attempt)

    def cancel(self, unit_id: str) -> None:
        self._cancelled.add(unit_id)

    def collect(self, handle: str, *, timeout_seconds: float) -> BackendResult:
        unit, attempt = self._handles[handle]
        duration = self.durations.get(unit.unit_id, 0.0)
        if duration > timeout_seconds:
            raise ExecutionFailure(
                "fixture deadline exceeded",
                failure_class=FailureClass.TIMEOUT,
                retryable=False,
            )
        if duration:
            time.sleep(duration)
        if unit.unit_id in self._cancelled:
            raise ExecutionFailure(
                "fixture unit cancelled",
                failure_class=FailureClass.CANCELLED,
                retryable=False,
            )
        if unit.unit_id in self.fail_once and attempt == 1:
            raise ExecutionFailure(
                "deterministic injected transient failure",
                failure_class=FailureClass.TRANSIENT,
                retryable=True,
            )
        output = {
            "unit_id": unit.unit_id,
            "task_id": unit.task_id,
            "model_version": unit.model_version,
            "policy": unit.policy,
            "repeat": unit.repeat,
            "seed": unit.seed,
            "fixture_output": content_hash(unit.model_dump(mode="json")),
            "evidence_class": EvidenceClass.FIXTURE_ONLY.value,
        }
        return BackendResult(
            unit_id=unit.unit_id,
            output=output,
            resource_use={"wall_seconds": duration},
        )

    def cleanup(self, handle: str | None = None) -> None:
        with self._lock:
            if handle is None:
                self._handles.clear()
            else:
                self._handles.pop(handle, None)

    def classify_failure(self, error: BaseException) -> tuple[FailureClass, bool]:
        if isinstance(error, ExecutionFailure):
            return error.failure_class, error.retryable
        return FailureClass.PERMANENT, False

    def provenance_receipt(
        self, unit: RunUnit, result: BackendResult, *, attempt: int
    ) -> dict[str, Any]:
        return {
            "backend": self.name,
            "backend_version": self.version,
            "unit_id": unit.unit_id,
            "attempt": attempt,
            "result_hash": content_hash(result.output),
            "fixture_only": True,
        }


class LocalSubprocessBackend:
    """Shell-free subprocess backend with timeout, cancellation, and child cleanup."""

    name = "local_subprocess"
    version = "1.0"

    def __init__(
        self,
        commands: Mapping[str, list[str]] | None = None,
        *,
        output_limit: int = 1_000_000,
        environment_allowlist: tuple[str, ...] = ("PATH", "LANG", "LC_ALL"),
    ) -> None:
        self.commands = {key: list(value) for key, value in (commands or {}).items()}
        self.output_limit = output_limit
        self.environment_allowlist = environment_allowlist
        self._processes: dict[str, tuple[str, subprocess.Popen[bytes]]] = {}
        self._lock = threading.Lock()

    def capabilities(self) -> BackendCapabilities:
        return BackendCapabilities(subprocess=True, cancellation=True, heartbeat=True)

    def validate_compatibility(self, manifest: RunManifest) -> list[str]:
        return [] if manifest.spec.backend == self.name else ["backend name mismatch"]

    def estimate_resources(self, unit: RunUnit) -> ResourceEstimate:
        del unit
        return ResourceEstimate()

    def prepare(self, manifest: RunManifest) -> None:
        errors = self.validate_compatibility(manifest)
        if errors:
            raise ValueError("; ".join(errors))

    def _command(self, unit: RunUnit) -> list[str]:
        command = self.commands.get(
            unit.unit_id,
            [
                os.environ.get("PYTHON", "python3"),
                "-c",
                (
                    "import json;"
                    f"print(json.dumps({{'unit_id': {unit.unit_id!r}, "
                    "'evidence_class': 'FIXTURE_ONLY'}))"
                ),
            ],
        )
        if not command or any(not isinstance(value, str) or "\x00" in value for value in command):
            raise ValueError("subprocess command must be a non-empty null-free argument list")
        return command

    def launch(self, unit: RunUnit, *, attempt: int) -> str:
        command = self._command(unit)
        environment = {
            key: value
            for key, value in os.environ.items()
            if key in self.environment_allowlist
        }
        handle = f"process.{content_hash([unit.unit_id, attempt, time.monotonic_ns()])[:24]}"
        process = subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            env=environment,
            start_new_session=True,
        )
        with self._lock:
            self._processes[handle] = (unit.unit_id, process)
        return handle

    def poll(self, handle: str) -> str:
        process = self._processes[handle][1]
        return "RUNNING" if process.poll() is None else "EXITED"

    def heartbeat(self, handle: str) -> dict[str, Any]:
        process = self._processes[handle][1]
        return {"pid": process.pid, "state": self.poll(handle), "monotonic": time.monotonic()}

    def checkpoint(self, handle: str) -> dict[str, Any]:
        return {"handle": handle, "state": self.poll(handle), "resumable": False}

    def resume(self, unit: RunUnit, checkpoint: Mapping[str, Any], *, attempt: int) -> str:
        del checkpoint
        return self.launch(unit, attempt=attempt)

    @staticmethod
    def _terminate_process(process: subprocess.Popen[bytes]) -> None:
        if process.poll() is not None:
            return
        try:
            os.killpg(process.pid, signal.SIGTERM)
            process.wait(timeout=1)
        except (ProcessLookupError, subprocess.TimeoutExpired):
            with suppress(ProcessLookupError):
                os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=2)

    def cancel(self, unit_id: str) -> None:
        with self._lock:
            processes = [
                process
                for observed_unit, process in self._processes.values()
                if observed_unit == unit_id
            ]
        for process in processes:
            self._terminate_process(process)

    def collect(self, handle: str, *, timeout_seconds: float) -> BackendResult:
        unit_id, process = self._processes[handle]
        started = time.monotonic()
        try:
            stdout, stderr = process.communicate(timeout=timeout_seconds)
        except subprocess.TimeoutExpired as exc:
            self._terminate_process(process)
            process.communicate()
            raise ExecutionFailure(
                "local subprocess wall-clock timeout",
                failure_class=FailureClass.TIMEOUT,
                retryable=False,
            ) from exc
        wall = time.monotonic() - started
        stdout = stdout[: self.output_limit]
        stderr = stderr[: self.output_limit]
        if process.returncode is None:
            raise ExecutionFailure(
                "subprocess did not reach a terminal exit",
                failure_class=FailureClass.PERMANENT,
                retryable=False,
            )
        if process.returncode < 0:
            raise ExecutionFailure(
                f"subprocess terminated by signal {-process.returncode}",
                failure_class=FailureClass.WORKER_KILLED,
                retryable=True,
            )
        if process.returncode != 0:
            raise ExecutionFailure(
                f"subprocess exited {process.returncode}: "
                f"{stderr.decode('utf-8', errors='replace')[:256]}",
                failure_class=FailureClass.PERMANENT,
                retryable=False,
            )
        try:
            output = json.loads(stdout.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ExecutionFailure(
                "subprocess output is not valid UTF-8 JSON",
                failure_class=FailureClass.INVALID_OUTPUT,
                retryable=False,
            ) from exc
        if not isinstance(output, dict) or output.get("unit_id") != unit_id:
            raise ExecutionFailure(
                "subprocess output violates the unit schema",
                failure_class=FailureClass.INVALID_OUTPUT,
                retryable=False,
            )
        return BackendResult(
            unit_id=unit_id,
            output=output,
            stdout=stdout.decode("utf-8", errors="replace"),
            stderr=stderr.decode("utf-8", errors="replace"),
            exit_code=process.returncode,
            orphan_processes=0,
            resource_use={"wall_seconds": wall},
        )

    def cleanup(self, handle: str | None = None) -> None:
        with self._lock:
            handles = list(self._processes) if handle is None else [handle]
        for value in handles:
            with self._lock:
                row = self._processes.pop(value, None)
            if row:
                self._terminate_process(row[1])

    def classify_failure(self, error: BaseException) -> tuple[FailureClass, bool]:
        if isinstance(error, ExecutionFailure):
            return error.failure_class, error.retryable
        if isinstance(error, OSError):
            return FailureClass.TRANSIENT, True
        return FailureClass.PERMANENT, False

    def provenance_receipt(
        self, unit: RunUnit, result: BackendResult, *, attempt: int
    ) -> dict[str, Any]:
        return {
            "backend": self.name,
            "backend_version": self.version,
            "unit_id": unit.unit_id,
            "attempt": attempt,
            "exit_code": result.exit_code,
            "orphan_processes": result.orphan_processes,
            "output_hash": content_hash(result.output),
        }


class KaggleBundleBackend:
    """Offline-only deterministic Kaggle export/import contract."""

    name = "kaggle"
    version = "1.0"

    def capabilities(self) -> BackendCapabilities:
        return BackendCapabilities(
            execution=False,
            checkpoint=True,
            resume=True,
            cancellation=False,
            heartbeat=False,
            network=False,
            accelerator="T4x2_or_single_T4",
        )

    def validate_compatibility(self, manifest: RunManifest) -> list[str]:
        return [] if manifest.spec.backend == self.name else ["backend name mismatch"]

    def estimate_resources(self, unit: RunUnit) -> ResourceEstimate:
        del unit
        return ResourceEstimate(cpu_units=1, memory_mb=4096, wall_seconds=3600)

    def prepare(self, manifest: RunManifest) -> None:
        errors = self.validate_compatibility(manifest)
        if errors:
            raise ValueError("; ".join(errors))

    def export_bundle(
        self,
        manifest: RunManifest,
        destination: str | Path,
        *,
        accelerator_mode: str = "T4x2",
    ) -> dict[str, Any]:
        if accelerator_mode not in {"T4x2", "single-T4"}:
            raise ValueError("accelerator mode must be T4x2 or single-T4")
        destination = Path(destination)
        destination.mkdir(parents=True, exist_ok=True)
        units = [unit.model_dump(mode="json") for unit in manifest.units]
        commitments = {
            "manifest_hash": manifest.manifest_hash,
            "task_hash": content_hash(sorted(unit.task_id for unit in manifest.units)),
            "model_hash": content_hash(sorted(set(manifest.spec.model_versions))),
            "policy_hash": content_hash(sorted(set(manifest.spec.policies))),
        }
        shard_count = 2 if accelerator_mode == "T4x2" else 1
        shards = {
            str(index): [
                unit["unit_id"]
                for position, unit in enumerate(units)
                if position % shard_count == index
            ]
            for index in range(shard_count)
        }
        payload = {
            "schema_version": "1.0",
            "backend": self.name,
            "backend_version": self.version,
            "accelerator_mode": accelerator_mode,
            "fallback_mode": "single-T4",
            "commitments": commitments,
            "units": units,
            "shards": shards,
            "provider_execution": False,
        }
        payload["bundle_hash"] = content_hash(payload)
        (destination / "kaggle_run_bundle.json").write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (destination / "kernel-metadata.json").write_text(
            json.dumps(
                {
                    "id": "cab/level5-offline-export",
                    "title": "CAB Level-5 offline export",
                    "code_file": "runner.ipynb",
                    "is_private": True,
                    "enable_gpu": True,
                    "enable_internet": False,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        return payload

    def import_receipts(
        self,
        manifest: RunManifest,
        receipt_path: str | Path,
        store: ContentAddressedStore,
        registry: SQLiteRegistry,
    ) -> dict[str, Any]:
        registry.initialize()
        payload = json.loads(Path(receipt_path).read_text(encoding="utf-8"))
        expected = {
            "manifest_hash": manifest.manifest_hash,
            "task_hash": content_hash(sorted(unit.task_id for unit in manifest.units)),
            "model_hash": content_hash(sorted(set(manifest.spec.model_versions))),
            "policy_hash": content_hash(sorted(set(manifest.spec.policies))),
        }
        if payload.get("commitments") != expected:
            raise ValueError("Kaggle receipt commitment mismatch")
        known = {unit.unit_id for unit in manifest.units}
        imported: list[str] = []
        for result in payload.get("results", []):
            if result.get("unit_id") not in known:
                raise ValueError("Kaggle receipt contains an unknown unit")
            metadata = store.put_json(result, artifact_class="fixture", compress=True)
            registry.register(
                "artifact",
                f"artifact.{metadata.digest[:24]}",
                {
                    "digest": metadata.digest,
                    "artifact_class": "fixture",
                    "unit_id": result["unit_id"],
                    "source": "kaggle_offline_import",
                },
                freeze=True,
            )
            imported.append(str(result["unit_id"]))
        return {
            "imported_units": sorted(imported),
            "partial_session": len(imported) < len(manifest.units),
            "remaining_units": sorted(known - set(imported)),
            "commitments_verified": True,
        }

    def launch(self, unit: RunUnit, *, attempt: int) -> str:
        del unit, attempt
        raise RuntimeError("Kaggle backend exports bundles; it never calls Kaggle automatically")

    def poll(self, handle: str) -> str:
        del handle
        return "NOT_EXECUTED"

    def heartbeat(self, handle: str) -> dict[str, Any]:
        del handle
        return {"state": "NOT_EXECUTED"}

    def checkpoint(self, handle: str) -> dict[str, Any]:
        del handle
        return {"state": "OFFLINE_EXPORT"}

    def resume(self, unit: RunUnit, checkpoint: Mapping[str, Any], *, attempt: int) -> str:
        del unit, checkpoint, attempt
        raise RuntimeError("resume occurs by partial receipt import and re-export")

    def cancel(self, unit_id: str) -> None:
        del unit_id

    def collect(self, handle: str, *, timeout_seconds: float) -> BackendResult:
        del handle, timeout_seconds
        raise RuntimeError("Kaggle execution is disabled in the local coordinator")

    def cleanup(self, handle: str | None = None) -> None:
        del handle

    def classify_failure(self, error: BaseException) -> tuple[FailureClass, bool]:
        del error
        return FailureClass.PERMANENT, False

    def provenance_receipt(
        self, unit: RunUnit, result: BackendResult, *, attempt: int
    ) -> dict[str, Any]:
        del unit, result, attempt
        return {"backend": self.name, "backend_version": self.version, "offline_only": True}


class DisabledProviderBackend:
    name = "provider"
    version = "disabled"

    def __init__(
        self,
        *,
        approved: bool = False,
        credentials_present: bool = False,
        budget_approved: bool = False,
    ) -> None:
        self.approved = approved
        self.credentials_present = credentials_present
        self.budget_approved = budget_approved

    def capabilities(self) -> BackendCapabilities:
        return BackendCapabilities(execution=False, network=True)

    def validate_compatibility(self, manifest: RunManifest) -> list[str]:
        errors = []
        if manifest.spec.backend not in {"provider", "openai", "anthropic", "gemini"}:
            errors.append("backend name mismatch")
        if not self.approved:
            errors.append("explicit live execution approval missing")
        if not self.credentials_present:
            errors.append("provider credentials missing")
        if not self.budget_approved:
            errors.append("provider budget approval missing")
        return errors

    def prepare(self, manifest: RunManifest) -> None:
        errors = self.validate_compatibility(manifest)
        if errors:
            raise PermissionError("; ".join(errors))


class ConcurrentScheduler:
    """Operational coordinator using durable leases and a real worker pool."""

    def __init__(
        self,
        backend: OperationalBackend,
        store: ContentAddressedStore,
        registry: SQLiteRegistry,
        *,
        max_concurrency: int,
        per_backend_limit: int | None = None,
        per_model_limit: int | None = None,
        lease_seconds: float = 5.0,
        retry_base_seconds: float = 0.001,
    ) -> None:
        if max_concurrency < 1:
            raise ValueError("max_concurrency must be positive")
        self.backend = backend
        self.store = store
        self.registry = registry
        self.queue = QueueRepository(registry)
        self.max_concurrency = max_concurrency
        self.per_backend_limit = per_backend_limit or max_concurrency
        self.per_model_limit = per_model_limit or max_concurrency
        self.lease_seconds = lease_seconds
        self.retry_base_seconds = retry_base_seconds

    def run(
        self,
        manifest: RunManifest,
        *,
        dependencies: Mapping[str, list[str]] | None = None,
        priorities: Mapping[str, int] | None = None,
        quota_keys: Mapping[str, str] | None = None,
        cancel_units: set[str] | None = None,
    ) -> dict[str, Any]:
        self.backend.prepare(manifest)
        self.queue.enqueue(
            manifest,
            dependencies=dependencies,
            priorities=priorities,
            quota_keys=quota_keys,
        )
        for unit_id in sorted(cancel_units or set()):
            self.queue.cancel(unit_id)
            self.backend.cancel(unit_id)
        self.queue.recover_staged_results(self.store)
        started = time.monotonic()
        contention_errors = 0

        def worker(index: int) -> None:
            nonlocal contention_errors
            worker_id = f"worker.{index:02d}"
            idle_rounds = 0
            while not self.queue.is_complete(manifest.manifest_hash):
                self.queue.reclaim_stale()
                try:
                    lease = self.queue.acquire(
                        worker_id=worker_id,
                        manifest_hash=manifest.manifest_hash,
                        backend_limit=self.per_backend_limit,
                        model_limit=self.per_model_limit,
                        global_limit=self.max_concurrency,
                        lease_seconds=self.lease_seconds,
                    )
                except Exception as exc:
                    if "locked" in str(exc).lower():
                        contention_errors += 1
                        time.sleep(0.002)
                        continue
                    raise
                if lease is None:
                    idle_rounds += 1
                    if idle_rounds > 10_000:
                        raise RuntimeError("scheduler made no progress")
                    time.sleep(0.001)
                    continue
                idle_rounds = 0
                handle: str | None = None
                heartbeat_stop = threading.Event()
                heartbeat_thread: threading.Thread | None = None
                try:
                    self.queue.mark_running(lease)
                    handle = self.backend.launch(lease.unit, attempt=lease.attempt)

                    def heartbeat_loop(
                        stop: threading.Event = heartbeat_stop,
                        backend_handle: str = handle,
                        active_lease: UnitLease = lease,
                    ) -> None:
                        while not stop.wait(max(0.01, self.lease_seconds / 3)):
                            try:
                                self.backend.heartbeat(backend_handle)
                                self.queue.heartbeat(
                                    active_lease,
                                    lease_seconds=self.lease_seconds,
                                )
                            except (KeyError, PermissionError):
                                # A terminal commit can release the lease between
                                # the stop check and heartbeat transaction, and
                                # cleanup can remove its backend handle. Both are
                                # correctly fenced terminal races.
                                return

                    estimate = self.backend.estimate_resources(lease.unit)
                    if estimate.wall_seconds >= self.lease_seconds / 3:
                        heartbeat_thread = threading.Thread(
                            target=heartbeat_loop,
                            name=f"cab-heartbeat-{worker_id}",
                            daemon=True,
                        )
                        heartbeat_thread.start()
                    result = self.backend.collect(
                        handle,
                        timeout_seconds=manifest.spec.timeout_seconds,
                    )
                    if result.unit_id != lease.unit.unit_id:
                        raise ExecutionFailure(
                            "backend returned a different unit ID",
                            failure_class=FailureClass.INVALID_OUTPUT,
                            retryable=False,
                        )
                    metadata = self.store.put_json(
                        result.output,
                        artifact_class="fixture",
                        compress=True,
                    )
                    if not self.store.verify(metadata.digest)["passed"]:
                        raise ExecutionFailure(
                            "CAS verification failed before commit",
                            failure_class=FailureClass.PERMANENT,
                            retryable=False,
                        )
                    self.queue.stage_result(lease, metadata.digest)
                    artifact_id = f"artifact.{metadata.digest[:24]}"
                    self.registry.register(
                        "artifact",
                        artifact_id,
                        {
                            "digest": metadata.digest,
                            "artifact_class": metadata.artifact_class,
                            "unit_id": lease.unit.unit_id,
                            "backend": self.backend.name,
                        },
                        freeze=True,
                    )
                    provenance = self.backend.provenance_receipt(
                        lease.unit,
                        result,
                        attempt=lease.attempt,
                    )
                    self.registry.add_provenance(
                        output_hash=metadata.digest,
                        parent_hashes=[manifest.manifest_hash],
                        transformation_command=canonical_json(provenance),
                        code_revision=manifest.spec.code_revision,
                        environment_id=f"backend.{self.backend.name}.{self.backend.version}",
                        actor_class=ActorClass.FIXTURE,
                        evidence_class=EvidenceClass.FIXTURE_ONLY,
                    )
                    self.queue.commit_success(lease, metadata.digest)
                except BaseException as exc:
                    failure_class, retryable = self.backend.classify_failure(exc)
                    with suppress(PermissionError):
                        self.queue.fail(
                            lease,
                            exc,
                            failure_class=failure_class,
                            retryable=retryable,
                            retry_base_seconds=self.retry_base_seconds,
                        )
                finally:
                    heartbeat_stop.set()
                    if heartbeat_thread:
                        heartbeat_thread.join(timeout=1)
                    self.backend.cleanup(handle)

        with ThreadPoolExecutor(
            max_workers=self.max_concurrency,
            thread_name_prefix="cab-worker",
        ) as pool:
            futures = [pool.submit(worker, index) for index in range(self.max_concurrency)]
            for future in futures:
                future.result()
        wall = time.monotonic() - started
        summary = self.queue.summary(manifest.manifest_hash)
        summary.update(
            {
                "wall_seconds": wall,
                "throughput_units_per_second": (
                    summary["unit_count"] / wall if wall else float("inf")
                ),
                "max_concurrency": self.max_concurrency,
                "per_backend_limit": self.per_backend_limit,
                "per_model_limit": self.per_model_limit,
                "registry_contention_errors": contention_errors,
                "evidence_class": EvidenceClass.FIXTURE_ONLY.value,
            }
        )
        return summary


def run_scheduler_stress(
    root: str | Path,
    *,
    unit_count: int = 1_000,
    concurrencies: tuple[int, ...] = (1, 2, 4, 8),
) -> dict[str, Any]:
    """Run deterministic 1,000-unit scheduling at four concurrency levels."""

    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    spec = RunPlanSpec(
        study_id="study.level5_scheduler_stress",
        task_version="tasks.scheduler_stress.v1",
        split_version="split.scheduler_stress.v1",
        model_versions=["model.fixture.v1"],
        policies=["policy.standard.v1"],
        repeats=1,
        seeds=[2026],
        task_ids=[f"stress_task_{index:04d}" for index in range(unit_count)],
        scorer_version="scorer.fixture.v1",
        code_revision="hardening-fixture",
        backend="fixture",
        max_concurrency=max(concurrencies),
        max_attempts=3,
        timeout_seconds=10,
    )
    manifest = compile_run_plan(spec, shard_count=max(concurrencies))
    unit_ids = [unit.unit_id for unit in manifest.units]
    dependencies = {
        unit_ids[index]: [unit_ids[index - 1]]
        for index in range(1, len(unit_ids))
        if index % 25 == 0
    }
    fail_once = {unit_id for index, unit_id in enumerate(unit_ids) if index % 53 == 0}
    cancel_units = {unit_id for index, unit_id in enumerate(unit_ids) if index % 211 == 7}
    deferred = {unit_id for index, unit_id in enumerate(unit_ids) if index % 223 == 11}
    quota_keys = dict.fromkeys(deferred, "deferred")
    priorities = {unit_id: 10 if index % 97 == 0 else 0 for index, unit_id in enumerate(unit_ids)}
    reports: list[dict[str, Any]] = []
    merged_hashes: set[str] = set()
    for concurrency in concurrencies:
        run_root = root / f"concurrency-{concurrency}"
        registry = SQLiteRegistry(run_root / "registry.sqlite3")
        registry.initialize()
        queue = QueueRepository(registry)
        queue.set_quota("deferred", 0)
        store = ContentAddressedStore(run_root / "cas")
        durations = {
            unit_id: (index % 4) * 0.0002
            for index, unit_id in enumerate(unit_ids)
        }
        scheduler = ConcurrentScheduler(
            ConcurrentFixtureBackend(fail_once=fail_once, durations=durations),
            store,
            registry,
            max_concurrency=concurrency,
            lease_seconds=10.0,
        )
        queue.enqueue(
            manifest,
            dependencies=dependencies,
            priorities=priorities,
            quota_keys=quota_keys,
        )
        queue.pause(manifest.manifest_hash)
        paused_count = queue.summary(manifest.manifest_hash)["state_counts"].get("PAUSED", 0)
        queue.resume(manifest.manifest_hash)
        # Create and immediately reclaim one real stale lease.
        stale = queue.acquire(
            worker_id="worker.stale",
            manifest_hash=manifest.manifest_hash,
            backend_limit=concurrency,
            model_limit=concurrency,
            global_limit=concurrency,
            lease_seconds=0.01,
        )
        stale_recovered = 0
        if stale is not None:
            stale_recovered = queue.reclaim_stale(now=time.time() + 1)
        result = scheduler.run(
            manifest,
            dependencies=dependencies,
            priorities=priorities,
            quota_keys=quota_keys,
            cancel_units=cancel_units,
        )
        peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        peak = int(peak_rss if os.uname().sysname == "Darwin" else peak_rss * 1024)
        result.update(
            {
                "paused_units_observed": paused_count,
                "stale_leases_recovered": stale_recovered,
                "peak_memory_bytes": peak,
                "memory_measurement": "process_peak_rss",
                "cas_verification": store.verify(),
            }
        )
        reports.append(result)
        merged_hashes.add(str(result["deterministic_merged_hash"]))
    passed = all(
        report["duplicate_committed_results"] == 0
        and report["missing_terminal_states"] == 0
        and report["cas_verification"]["passed"]
        and report["stale_leases_recovered"] == 1
        for report in reports
    ) and len(merged_hashes) == 1
    return {
        "passed": passed,
        "unit_count": unit_count,
        "concurrencies": list(concurrencies),
        "reports": reports,
        "deterministic_hash_agreement": len(merged_hashes) == 1,
        "deterministic_merged_hash": next(iter(merged_hashes)) if len(merged_hashes) == 1 else None,
        "duplicate_committed_results": sum(
            int(report["duplicate_committed_results"]) for report in reports
        ),
        "missing_terminal_states": sum(
            int(report["missing_terminal_states"]) for report in reports
        ),
        "evidence_class": EvidenceClass.FIXTURE_ONLY.value,
    }


def run_crash_consistency_demo(root: str | Path) -> dict[str, Any]:
    """Exercise durable recovery at five coordinator crash boundaries."""

    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    crash_points = (
        "after_lease",
        "after_artifact_write",
        "before_registry_commit",
        "after_artifact_registration",
        "before_terminal_scheduler_state",
    )
    reports: list[dict[str, Any]] = []
    for index, crash_point in enumerate(crash_points):
        run_root = root / f"{index + 1:02d}-{crash_point}"
        registry_path = run_root / "registry.sqlite3"
        cas_path = run_root / "cas"
        spec = RunPlanSpec(
            study_id=f"study.crash_consistency.{index}",
            task_version="tasks.crash_consistency.v1",
            split_version="split.crash_consistency.v1",
            model_versions=["model.fixture.v1"],
            policies=["policy.standard.v1"],
            repeats=1,
            seeds=[2026],
            task_ids=[f"crash_task_{index}"],
            scorer_version="scorer.fixture.v1",
            code_revision="hardening-fixture",
            backend="fixture",
            max_concurrency=1,
            max_attempts=3,
            timeout_seconds=5,
        )
        manifest = compile_run_plan(spec, shard_count=1)
        unit = manifest.units[0]
        registry = SQLiteRegistry(registry_path)
        queue = QueueRepository(registry)
        store = ContentAddressedStore(cas_path)
        queue.enqueue(manifest)
        lease = queue.acquire(
            worker_id=f"worker.crash.{index}",
            manifest_hash=manifest.manifest_hash,
            backend_limit=1,
            model_limit=1,
            global_limit=1,
            lease_seconds=0.01,
        )
        if lease is None:  # pragma: no cover - defensive invariant
            raise RuntimeError("crash demo failed to acquire its fixture lease")
        if crash_point != "after_lease":
            queue.mark_running(lease)

        output = {
            "unit_id": unit.unit_id,
            "task_id": unit.task_id,
            "model_version": unit.model_version,
            "policy": unit.policy,
            "repeat": unit.repeat,
            "seed": unit.seed,
            "fixture_output": content_hash(unit.model_dump(mode="json")),
            "evidence_class": EvidenceClass.FIXTURE_ONLY.value,
        }
        digest: str | None = None
        if crash_point != "after_lease":
            digest = store.put_json(
                output,
                artifact_class="fixture",
                compress=True,
            ).digest
        if crash_point in {"before_registry_commit", "before_terminal_scheduler_state"}:
            if digest is None:  # pragma: no cover - construction invariant
                raise RuntimeError("missing staged crash-demo artifact")
            queue.stage_result(lease, digest)
        if crash_point in {
            "after_artifact_registration",
            "before_terminal_scheduler_state",
        }:
            if digest is None:  # pragma: no cover - construction invariant
                raise RuntimeError("missing registered crash-demo artifact")
            registry.register(
                "artifact",
                f"artifact.{digest[:24]}",
                {
                    "digest": digest,
                    "artifact_class": "fixture",
                    "unit_id": unit.unit_id,
                    "backend": "fixture",
                },
                freeze=True,
            )

        # Coordinator crash: discard every process-local object. The reopened
        # coordinator receives only the durable SQLite registry and CAS.
        del queue, store, registry, lease
        restarted_registry = SQLiteRegistry(registry_path)
        restarted_queue = QueueRepository(restarted_registry)
        restarted_store = ContentAddressedStore(cas_path)
        journal_recovered = restarted_queue.recover_staged_results(restarted_store)
        stale_recovered = restarted_queue.reclaim_stale(now=time.time() + 1)
        summary = ConcurrentScheduler(
            ConcurrentFixtureBackend(),
            restarted_store,
            restarted_registry,
            max_concurrency=1,
            lease_seconds=0.1,
        ).run(manifest)
        with restarted_registry._connect() as connection:
            row = connection.execute(
                "SELECT result_digest FROM queue_entries WHERE unit_id=?",
                (unit.unit_id,),
            ).fetchone()
        committed_digest = str(row["result_digest"]) if row and row["result_digest"] else None
        expected_digest = restarted_store.put_json(
            output,
            artifact_class="fixture",
            compress=True,
        ).digest
        point_passed = (
            summary["state_counts"] == {"SUCCEEDED": 1}
            and summary["duplicate_committed_results"] == 0
            and summary["missing_terminal_states"] == 0
            and committed_digest == expected_digest
            and restarted_store.verify(expected_digest)["passed"]
        )
        reports.append(
            {
                "crash_point": crash_point,
                "passed": point_passed,
                "journaled_results_recovered": journal_recovered,
                "stale_leases_recovered": stale_recovered,
                "committed_digest": committed_digest,
                "expected_digest": expected_digest,
                "duplicate_committed_results": summary[
                    "duplicate_committed_results"
                ],
                "terminal_state": next(iter(summary["state_counts"])),
                "restart_model": "coordinator_state_discard_and_durable_reopen",
            }
        )
    return {
        "passed": all(report["passed"] for report in reports),
        "crash_points": reports,
        "duplicate_committed_results": sum(
            int(report["duplicate_committed_results"]) for report in reports
        ),
        "evidence_class": EvidenceClass.FIXTURE_ONLY.value,
    }


def fixture_20_spec() -> RunPlanSpec:
    return RunPlanSpec(
        study_id="study.level5_fixture",
        task_version="tasks.public_fixture.v1",
        split_version="split.public_fixture.v1",
        model_versions=["model.fixture.v1"],
        policies=["policy.standard.v1"],
        repeats=1,
        seeds=[2026],
        task_ids=[f"fixture_task_{index:02d}" for index in range(20)],
        scorer_version="scorer.fixture.v1",
        code_revision="fixture",
        backend="fixture",
        max_concurrency=2,
        max_attempts=2,
    )


__all__ = [
    "ArtifactMetadata",
    "Backend",
    "BackendCapabilities",
    "BackendResult",
    "ConcurrentFixtureBackend",
    "ConcurrentScheduler",
    "ContentAddressedStore",
    "DisabledProviderBackend",
    "ExecutionFailure",
    "FailureClass",
    "FixtureBackend",
    "KaggleBundleBackend",
    "LocalScheduler",
    "LocalSubprocessBackend",
    "OperationalBackend",
    "QueueRepository",
    "ResourceEstimate",
    "RunManifest",
    "RunPlanSpec",
    "RunState",
    "RunUnit",
    "UnitLease",
    "compile_run_plan",
    "fixture_20_spec",
    "run_crash_consistency_demo",
    "run_scheduler_stress",
    "validate_checkpoint",
]
