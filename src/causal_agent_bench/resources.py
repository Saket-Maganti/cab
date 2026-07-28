"""Resource-bounded execution planning for M4 and Kaggle T4x2 hosts."""

from __future__ import annotations

import gzip
import hashlib
import json
import os
from collections import defaultdict
from collections.abc import Iterator, Sequence
from enum import StrEnum
from pathlib import Path
from typing import Any


class WorkerMode(StrEnum):
    SERIAL = "serial"
    LOW_MEMORY = "low_memory"
    FOUR_WORKER = "four_worker"
    ADAPTIVE = "adaptive"


def choose_worker_limit(
    mode: WorkerMode | str,
    *,
    cpu_count: int | None = None,
    memory_gib: float | None = None,
) -> dict[str, Any]:
    """Return a bounded CPU worker count; never emit unbounded ``auto``."""

    selected = WorkerMode(mode)
    available_cpu = max(1, int(cpu_count or os.cpu_count() or 1))
    if selected is WorkerMode.SERIAL:
        workers = 1
    elif selected is WorkerMode.LOW_MEMORY:
        workers = min(2, available_cpu)
    elif selected is WorkerMode.FOUR_WORKER:
        workers = min(4, available_cpu)
    else:
        memory_bound = (
            max(1, int(memory_gib // 3))
            if memory_gib is not None and memory_gib > 0
            else 2
        )
        workers = min(4, available_cpu, memory_bound)
    return {
        "mode": selected.value,
        "workers": workers,
        "cpu_count": available_cpu,
        "memory_gib": memory_gib,
        "bounded": True,
        "evidence_class": "ENGINEERING_ONLY",
    }


def stream_jsonl(
    path: str | Path,
    *,
    chunk_size: int = 500,
) -> Iterator[list[dict[str, Any]]]:
    """Yield bounded JSONL chunks and reject non-object records."""

    if chunk_size < 1:
        raise ValueError("chunk_size must be positive")
    chunk: list[dict[str, Any]] = []
    with Path(path).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number}: expected JSON object")
            chunk.append(value)
            if len(chunk) == chunk_size:
                yield chunk
                chunk = []
    if chunk:
        yield chunk


def compress_jsonl(
    source: str | Path,
    destination: str | Path,
    *,
    chunk_size: int = 500,
) -> dict[str, Any]:
    """Stream a JSONL file into a reproducible gzip artifact."""

    source_path = Path(source)
    destination_path = Path(destination)
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    record_count = 0
    with gzip.GzipFile(
        filename="",
        mode="wb",
        fileobj=destination_path.open("wb"),
        mtime=0,
    ) as compressed:
        for chunk in stream_jsonl(source_path, chunk_size=chunk_size):
            for row in chunk:
                payload = (
                    json.dumps(
                        row,
                        sort_keys=True,
                        separators=(",", ":"),
                        ensure_ascii=False,
                    )
                    + "\n"
                ).encode("utf-8")
                compressed.write(payload)
                record_count += 1
    return {
        "source": str(source_path),
        "destination": str(destination_path),
        "records": record_count,
        "source_bytes": source_path.stat().st_size,
        "compressed_bytes": destination_path.stat().st_size,
        "sha256": _sha256_file(destination_path),
        "evidence_class": "ENGINEERING_ONLY",
    }


def repository_disk_report(
    root: str | Path,
    *,
    include_git: bool = False,
) -> dict[str, Any]:
    """Measure local disk use without deleting or opening file contents."""

    base = Path(root).resolve()
    category_bytes: dict[str, int] = defaultdict(int)
    file_count = 0
    total_bytes = 0
    largest: list[tuple[int, str]] = []
    for path in base.rglob("*"):
        if not path.is_file() or (not include_git and ".git" in path.parts):
            continue
        try:
            size = path.stat().st_size
        except OSError:
            continue
        relative = path.relative_to(base)
        category = relative.parts[0] if relative.parts else "."
        category_bytes[category] += size
        total_bytes += size
        file_count += 1
        largest.append((size, str(relative)))
    largest.sort(reverse=True)
    return {
        "root": str(base),
        "file_count": file_count,
        "total_bytes": total_bytes,
        "category_bytes": dict(sorted(category_bytes.items())),
        "largest_files": [
            {"path": path, "bytes": size} for size, path in largest[:20]
        ],
        "read_only": True,
        "evidence_class": "ENGINEERING_ONLY",
    }


def duplicate_artifact_report(
    roots: Sequence[str | Path],
    *,
    minimum_bytes: int = 1024,
) -> dict[str, Any]:
    """Find exact duplicate files by size and SHA-256."""

    if minimum_bytes < 0:
        raise ValueError("minimum_bytes must be non-negative")
    size_groups: dict[int, list[Path]] = defaultdict(list)
    for root in roots:
        base = Path(root)
        if not base.exists():
            continue
        paths = [base] if base.is_file() else base.rglob("*")
        for path in paths:
            if not path.is_file() or ".git" in path.parts:
                continue
            try:
                size = path.stat().st_size
            except OSError:
                continue
            if size >= minimum_bytes:
                size_groups[size].append(path.resolve())
    hash_groups: dict[str, list[Path]] = defaultdict(list)
    for paths in size_groups.values():
        if len(paths) < 2:
            continue
        for path in paths:
            hash_groups[_sha256_file(path)].append(path)
    duplicates = [
        {
            "sha256": digest,
            "bytes_each": paths[0].stat().st_size,
            "paths": [str(path) for path in sorted(paths)],
            "recoverable_bytes_if_one_retained": paths[0].stat().st_size
            * (len(paths) - 1),
        }
        for digest, paths in sorted(hash_groups.items())
        if len(paths) > 1
    ]
    potential_recoverable_bytes = sum(
        paths[0].stat().st_size * (len(paths) - 1)
        for paths in hash_groups.values()
        if len(paths) > 1
    )
    return {
        "duplicate_groups": duplicates,
        "duplicate_group_count": len(duplicates),
        "potential_recoverable_bytes": potential_recoverable_bytes,
        "automatic_deletion_performed": False,
        "evidence_class": "ENGINEERING_ONLY",
    }


def model_cache_report(paths: Sequence[str | Path]) -> dict[str, Any]:
    """Report explicitly supplied cache roots; never infer secrets or delete."""

    rows: list[dict[str, Any]] = []
    for value in paths:
        path = Path(value).expanduser().resolve()
        if not path.exists():
            rows.append({"path": str(path), "exists": False, "bytes": 0})
            continue
        total = sum(
            candidate.stat().st_size
            for candidate in path.rglob("*")
            if candidate.is_file()
        )
        rows.append({"path": str(path), "exists": True, "bytes": total})
    return {
        "caches": rows,
        "total_bytes": sum(int(row["bytes"]) for row in rows),
        "automatic_cleanup_performed": False,
        "evidence_class": "ENGINEERING_ONLY",
    }


def cache_cleanup_plan(paths: Sequence[str | Path]) -> dict[str, Any]:
    """Build a review-only cleanup plan with broad-target rejection."""

    rejected: list[str] = []
    candidates: list[dict[str, Any]] = []
    home = Path.home().resolve()
    for value in paths:
        path = Path(value).expanduser().resolve()
        if path in {Path("/"), home} or len(path.parts) < 3:
            rejected.append(str(path))
            continue
        size = (
            sum(item.stat().st_size for item in path.rglob("*") if item.is_file())
            if path.exists()
            else 0
        )
        candidates.append(
            {
                "path": str(path),
                "exists": path.exists(),
                "bytes": size,
                "requires_human_confirmation": True,
            }
        )
    return {
        "state": "review_required" if candidates else "no_safe_candidates",
        "candidates": candidates,
        "rejected_broad_targets": rejected,
        "automatic_cleanup_performed": False,
        "raw_evidence_must_be_retained": True,
        "evidence_class": "ENGINEERING_ONLY",
    }


def estimate_trajectory_resources(
    *,
    tasks: int,
    conditions_per_task: int,
    models: int,
    policies: int,
    repeats: int,
    mean_seconds_per_trajectory: float,
    mean_kib_per_trajectory: float,
    workers: int,
) -> dict[str, Any]:
    """Return transparent low/base/high planning estimates."""

    positive_integers = {
        "tasks": tasks,
        "conditions_per_task": conditions_per_task,
        "models": models,
        "policies": policies,
        "repeats": repeats,
        "workers": workers,
    }
    if any(value < 1 for value in positive_integers.values()):
        raise ValueError("task, condition, model, policy, repeat, and worker counts must be positive")
    if mean_seconds_per_trajectory <= 0 or mean_kib_per_trajectory <= 0:
        raise ValueError("per-trajectory estimates must be positive")
    trajectories = tasks * conditions_per_task * models * policies * repeats
    base_seconds = trajectories * mean_seconds_per_trajectory / workers
    base_bytes = trajectories * mean_kib_per_trajectory * 1024
    return {
        "label": "ESTIMATE_NOT_MEASURED",
        "assumptions": {
            **positive_integers,
            "mean_seconds_per_trajectory": mean_seconds_per_trajectory,
            "mean_kib_per_trajectory": mean_kib_per_trajectory,
        },
        "trajectory_count": trajectories,
        "runtime_seconds": {
            "low": round(base_seconds * 0.6, 2),
            "base": round(base_seconds, 2),
            "high": round(base_seconds * 1.8, 2),
        },
        "disk_bytes": {
            "low": round(base_bytes * 0.6),
            "base": round(base_bytes),
            "high": round(base_bytes * 1.8),
        },
        "scientific_evidence": False,
        "evidence_class": "DESIGN_ONLY",
    }


def bootstrap_execution_plan(
    *,
    mode: str,
    shard_size: int = 250,
    seed: int = 20260728,
) -> dict[str, Any]:
    """Return deterministic pilot/final bootstrap shard ranges."""

    replicates = {"pilot": 1000, "final": 10000}.get(mode)
    if replicates is None:
        raise ValueError("mode must be 'pilot' or 'final'")
    if shard_size < 1:
        raise ValueError("shard_size must be positive")
    shards = [
        {"replicate_start": start, "replicate_stop": min(start + shard_size, replicates)}
        for start in range(0, replicates, shard_size)
    ]
    return {
        "mode": mode,
        "replicates": replicates,
        "seed": seed,
        "clustering_unit": "base_task_id",
        "family_stratification": True,
        "resumable": True,
        "merge_requires_disjoint_complete_ranges": True,
        "shards": shards,
        "evidence_class": "ENGINEERING_ONLY",
    }


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
