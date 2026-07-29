"""Backend-agnostic run planning, fixture scheduling, and immutable artifact storage."""

from __future__ import annotations

import json
import os
import tempfile
import zlib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field

from causal_agent_bench.level5.core import canonical_json, content_hash, sha256_bytes, utc_now
from causal_agent_bench.level5.registry import Registry


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

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.objects = self.root / "objects"
        self.staging = self.root / "staging"
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
                handle.write(stored)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(staging_name, object_path)
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
        if checkpoint["manifest_hash"] != manifest.manifest_hash:
            raise ValueError("checkpoint manifest hash mismatch")

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
    "ContentAddressedStore",
    "FixtureBackend",
    "LocalScheduler",
    "RunManifest",
    "RunPlanSpec",
    "RunUnit",
    "compile_run_plan",
    "fixture_20_spec",
]
