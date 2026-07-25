"""Offline-only support for the Kaggle notebook fixture path.

This module deliberately does not import or call any agent, model, provider,
runner, scorer, or metric implementation.  It exists so the Kaggle notebooks
can prove deterministic sharding, checkpoint/resume, append-safe ledgers,
merge integrity, and export hashing without producing model-shaped outputs.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import tempfile
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

FIXTURE_EVIDENCE_CLASS = "FIXTURE_ONLY"
FIXTURE_RECEIPT_STATUS = "fixture_contract_validated"


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_write_text(path: str | Path, text: str) -> Path:
    """Replace ``path`` atomically with UTF-8 text."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temporary_name = tempfile.mkstemp(
        dir=target.parent,
        prefix=f".{target.name}.",
        suffix=".tmp",
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(file_descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, target)
    finally:
        temporary_path.unlink(missing_ok=True)
    return target


def write_json(path: str | Path, payload: object) -> Path:
    return atomic_write_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def read_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_jsonl(path: str | Path, rows: Iterable[Mapping[str, object]]) -> Path:
    rendered = "".join(_canonical_json(dict(row)) + "\n" for row in rows)
    return atomic_write_text(path, rendered)


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    source = Path(path)
    if not source.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        payload = json.loads(line)
        if not isinstance(payload, dict):
            raise ValueError(f"{source}:{line_number}: expected one JSON object per line")
        rows.append(payload)
    return rows


def append_jsonl(path: str | Path, payload: Mapping[str, object]) -> Path:
    """Append one compact JSON record using a single ``O_APPEND`` write.

    Each worker has its own ledger in the notebook design.  ``O_APPEND`` also
    prevents accidental overwrite if two processes append to the same file.
    """

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    line = (_canonical_json(dict(payload)) + "\n").encode("utf-8")
    descriptor = os.open(target, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o644)
    try:
        written = os.write(descriptor, line)
        if written != len(line):
            raise OSError(f"short append to {target}: wrote {written} of {len(line)} bytes")
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return target


def build_fixture_work_items(notebook_id: str, count: int = 8) -> list[dict[str, object]]:
    """Build non-model work items used only to test notebook mechanics."""

    if count < 1:
        raise ValueError("fixture count must be positive")
    return [
        {
            "item_id": f"{notebook_id}__fixture_{index:03d}",
            "ordinal": index,
            "evidence_class": FIXTURE_EVIDENCE_CLASS,
            "fixture_kind": "notebook_mechanics_only",
        }
        for index in range(count)
    ]


def deterministic_shards(
    rows: Sequence[Mapping[str, object]],
    *,
    worker_count: int,
    key: str = "item_id",
) -> list[list[dict[str, object]]]:
    """Round-robin a stable sort into deterministic non-overlapping shards."""

    if worker_count < 1:
        raise ValueError("worker_count must be at least one")
    normalized = [dict(row) for row in rows]
    identifiers = [str(row.get(key, "")) for row in normalized]
    if any(not identifier for identifier in identifiers):
        raise ValueError(f"every fixture row must have a non-empty {key!r}")
    if len(set(identifiers)) != len(identifiers):
        raise ValueError(f"duplicate fixture {key} values are forbidden")

    ordered = sorted(normalized, key=lambda row: str(row[key]))
    shards: list[list[dict[str, object]]] = [[] for _ in range(worker_count)]
    for position, row in enumerate(ordered):
        shards[position % worker_count].append(row)
    assert_shards_complete_and_disjoint(shards, expected_ids=set(identifiers), key=key)
    return shards


def assert_shards_complete_and_disjoint(
    shards: Sequence[Sequence[Mapping[str, object]]],
    *,
    expected_ids: set[str],
    key: str = "item_id",
) -> None:
    seen: set[str] = set()
    for worker_index, shard in enumerate(shards):
        shard_ids = {str(row.get(key, "")) for row in shard}
        if "" in shard_ids:
            raise ValueError(f"worker {worker_index} has a row without {key!r}")
        overlap = seen & shard_ids
        if overlap:
            raise ValueError(f"worker {worker_index} overlaps prior shards: {sorted(overlap)}")
        seen.update(shard_ids)
    missing = expected_ids - seen
    extra = seen - expected_ids
    if missing or extra:
        raise ValueError(f"shard coverage mismatch: missing={sorted(missing)} extra={sorted(extra)}")


def choose_worker_count(gpu_count: int, requested_workers: int = 2) -> dict[str, object]:
    """Choose independent data-parallel workers with a one-worker fallback."""

    if gpu_count < 0:
        raise ValueError("gpu_count cannot be negative")
    if requested_workers < 1:
        raise ValueError("requested_workers must be at least one")
    active = min(requested_workers, gpu_count) if gpu_count else 1
    return {
        "requested_workers": requested_workers,
        "active_workers": max(1, active),
        "gpu_count": gpu_count,
        "parallel_mode": "data_parallel" if active >= 2 else "single_worker_fallback",
        "single_gpu_fallback": active < requested_workers,
        "worker_to_gpu": {
            str(worker): (worker if gpu_count else None) for worker in range(max(1, active))
        },
    }


def initialize_fixture_workspace(work_root: str | Path, notebook_id: str) -> Path:
    """Create the fixed fixture directory layout idempotently."""

    root = Path(work_root).expanduser().resolve() / notebook_id / "fixture"
    for relative in ("inputs", "shards", "merged", "exports"):
        (root / relative).mkdir(parents=True, exist_ok=True)
    return root


def load_checkpoint(path: str | Path) -> dict[str, object]:
    checkpoint = Path(path)
    if not checkpoint.exists():
        return {
            "schema_version": 1,
            "evidence_class": FIXTURE_EVIDENCE_CLASS,
            "completed_item_ids": [],
            "status": "not_started",
        }
    payload = read_json(checkpoint)
    if payload.get("evidence_class") != FIXTURE_EVIDENCE_CLASS:
        raise ValueError(f"{checkpoint} is not a FIXTURE_ONLY checkpoint")
    completed = payload.get("completed_item_ids")
    if not isinstance(completed, list) or len(completed) != len(set(completed)):
        raise ValueError(f"{checkpoint} has invalid completed_item_ids")
    return payload


def _fixture_receipt(row: Mapping[str, object], worker_id: int) -> dict[str, object]:
    """Return a mechanics receipt, never an answer, trajectory, score, or label."""

    item_id = str(row["item_id"])
    return {
        "item_id": item_id,
        "worker_id": worker_id,
        "status": FIXTURE_RECEIPT_STATUS,
        "evidence_class": FIXTURE_EVIDENCE_CLASS,
        "input_sha256": sha256_bytes(_canonical_json(dict(row)).encode("utf-8")),
    }


def run_fixture_worker(
    fixture_root: str | Path,
    *,
    worker_id: int,
    rows: Sequence[Mapping[str, object]],
    max_new_items: int | None = None,
) -> dict[str, object]:
    """Exercise checkpoint/resume mechanics for one deterministic shard."""

    if worker_id < 0:
        raise ValueError("worker_id cannot be negative")
    if max_new_items is not None and max_new_items < 0:
        raise ValueError("max_new_items cannot be negative")
    worker_dir = Path(fixture_root) / "shards" / f"worker_{worker_id:02d}"
    worker_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = worker_dir / "checkpoint.json"
    receipts_path = worker_dir / "fixture_receipts.jsonl"
    ledger_path = worker_dir / "ledger.jsonl"

    checkpoint = load_checkpoint(checkpoint_path)
    completed_values = checkpoint["completed_item_ids"]
    if not isinstance(completed_values, list):
        raise ValueError(f"{checkpoint_path} has invalid completed_item_ids")
    completed = {str(item) for item in completed_values}
    existing_receipts = read_jsonl(receipts_path)
    receipt_by_id = {str(row["item_id"]): row for row in existing_receipts}
    if len(receipt_by_id) != len(existing_receipts):
        raise ValueError(f"duplicate receipt IDs in {receipts_path}")
    if completed != set(receipt_by_id):
        raise ValueError(f"checkpoint/receipt mismatch for worker {worker_id}")

    ordered = sorted((dict(row) for row in rows), key=lambda row: str(row["item_id"]))
    pending = [row for row in ordered if str(row["item_id"]) not in completed]
    selected = pending if max_new_items is None else pending[:max_new_items]

    for row in selected:
        receipt = _fixture_receipt(row, worker_id)
        item_id = str(receipt["item_id"])
        receipt_by_id[item_id] = receipt
        completed.add(item_id)
        write_jsonl(
            receipts_path,
            (receipt_by_id[key] for key in sorted(receipt_by_id)),
        )
        append_jsonl(
            ledger_path,
            {
                "event": "fixture_item_receipted",
                "item_id": item_id,
                "worker_id": worker_id,
                "evidence_class": FIXTURE_EVIDENCE_CLASS,
            },
        )
        write_json(
            checkpoint_path,
            {
                "schema_version": 1,
                "evidence_class": FIXTURE_EVIDENCE_CLASS,
                "worker_id": worker_id,
                "completed_item_ids": sorted(completed),
                "completed": len(completed),
                "total": len(ordered),
                "status": "complete" if len(completed) == len(ordered) else "interrupted_fixture",
            },
        )

    if not selected:
        write_json(
            checkpoint_path,
            {
                "schema_version": 1,
                "evidence_class": FIXTURE_EVIDENCE_CLASS,
                "worker_id": worker_id,
                "completed_item_ids": sorted(completed),
                "completed": len(completed),
                "total": len(ordered),
                "status": "complete" if len(completed) == len(ordered) else "interrupted_fixture",
            },
        )

    return {
        "worker_id": worker_id,
        "processed_this_call": len(selected),
        "completed": len(completed),
        "total": len(ordered),
        "pending": len(ordered) - len(completed),
        "checkpoint_path": checkpoint_path.relative_to(Path(fixture_root)).as_posix(),
        "receipts_path": receipts_path.relative_to(Path(fixture_root)).as_posix(),
        "evidence_class": FIXTURE_EVIDENCE_CLASS,
    }


def merge_fixture_shards(
    fixture_root: str | Path,
    *,
    expected_item_ids: set[str],
    worker_count: int,
) -> dict[str, object]:
    """Merge mechanics receipts and fail on missing, extra, or duplicate IDs."""

    root = Path(fixture_root)
    receipt_by_id: dict[str, dict[str, object]] = {}
    duplicates: list[str] = []
    workers: list[dict[str, object]] = []
    for worker_id in range(worker_count):
        worker_dir = root / "shards" / f"worker_{worker_id:02d}"
        receipts = read_jsonl(worker_dir / "fixture_receipts.jsonl")
        checkpoint = load_checkpoint(worker_dir / "checkpoint.json")
        workers.append(
            {
                "worker_id": worker_id,
                "receipt_count": len(receipts),
                "checkpoint_status": checkpoint.get("status"),
            }
        )
        for receipt in receipts:
            if receipt.get("evidence_class") != FIXTURE_EVIDENCE_CLASS:
                raise ValueError("non-fixture receipt encountered during fixture merge")
            item_id = str(receipt.get("item_id", ""))
            if item_id in receipt_by_id:
                duplicates.append(item_id)
            receipt_by_id[item_id] = receipt

    observed = set(receipt_by_id)
    missing = sorted(expected_item_ids - observed)
    extra = sorted(observed - expected_item_ids)
    if duplicates or missing or extra:
        raise ValueError(
            "fixture merge integrity failure: "
            f"duplicates={sorted(set(duplicates))} missing={missing} extra={extra}"
        )

    merged_dir = root / "merged"
    merged_dir.mkdir(parents=True, exist_ok=True)
    merged_path = write_jsonl(
        merged_dir / "fixture_receipts.jsonl",
        (receipt_by_id[key] for key in sorted(receipt_by_id)),
    )
    report = {
        "schema_version": 1,
        "evidence_class": FIXTURE_EVIDENCE_CLASS,
        "status": "FIXTURE_MERGE_COMPLETE",
        "expected": len(expected_item_ids),
        "merged": len(receipt_by_id),
        "duplicates": 0,
        "missing": 0,
        "extra": 0,
        "workers": workers,
        "merged_receipts_path": merged_path.relative_to(root).as_posix(),
    }
    write_json(merged_dir / "merge_report.json", report)
    return report


def write_integrity_manifest(
    root: str | Path,
    *,
    output_name: str = "integrity_manifest.json",
) -> dict[str, object]:
    """Hash every regular file below ``root`` except the manifest itself."""

    base = Path(root).resolve()
    output_path = base / output_name
    rows: list[dict[str, object]] = []
    for path in sorted(base.rglob("*")):
        if not path.is_file() or path.resolve() == output_path.resolve():
            continue
        rows.append(
            {
                "path": path.relative_to(base).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    manifest = {
        "schema_version": 1,
        "evidence_class": FIXTURE_EVIDENCE_CLASS,
        "root_name": base.name,
        "file_count": len(rows),
        "files": rows,
    }
    write_json(output_path, manifest)
    return manifest


def verify_integrity_manifest(
    root: str | Path,
    *,
    output_name: str = "integrity_manifest.json",
) -> dict[str, object]:
    base = Path(root).resolve()
    manifest_path = base / output_name
    manifest = read_json(manifest_path)
    problems: list[str] = []
    expected_paths: set[str] = set()
    for row in manifest.get("files", []):
        relative = str(row["path"])
        expected_paths.add(relative)
        path = base / relative
        if not path.is_file():
            problems.append(f"missing:{relative}")
            continue
        if path.stat().st_size != int(row["bytes"]):
            problems.append(f"size:{relative}")
        if sha256_file(path) != row["sha256"]:
            problems.append(f"sha256:{relative}")
    observed_paths = {
        path.relative_to(base).as_posix()
        for path in base.rglob("*")
        if path.is_file() and path.resolve() != manifest_path.resolve()
    }
    for relative in sorted(observed_paths - expected_paths):
        problems.append(f"untracked:{relative}")
    return {
        "ok": not problems,
        "problems": problems,
        "checked_files": len(expected_paths),
        "evidence_class": FIXTURE_EVIDENCE_CLASS,
    }


def _system_memory_gib() -> float | None:
    try:
        page_size = os.sysconf("SC_PAGE_SIZE")
        pages = os.sysconf("SC_PHYS_PAGES")
    except (AttributeError, OSError, ValueError):
        return None
    return round((page_size * pages) / (1024**3), 3)


def _gpu_inventory() -> dict[str, object]:
    executable = shutil.which("nvidia-smi")
    if executable is None:
        return {
            "gpu_count": 0,
            "cuda_status": "NVIDIA_SMI_NOT_AVAILABLE",
            "cuda_version": None,
            "cuda_version_source": None,
            "gpus": [],
        }
    command = [
        executable,
        "--query-gpu=index,name,memory.total,driver_version",
        "--format=csv,noheader,nounits",
    ]
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "gpu_count": 0,
            "cuda_status": f"NVIDIA_SMI_ERROR:{type(exc).__name__}",
            "cuda_version": None,
            "cuda_version_source": None,
            "gpus": [],
        }
    if result.returncode != 0:
        return {
            "gpu_count": 0,
            "cuda_status": f"NVIDIA_SMI_EXIT_{result.returncode}",
            "cuda_version": None,
            "cuda_version_source": None,
            "gpus": [],
        }
    gpus: list[dict[str, object]] = []
    for line in result.stdout.splitlines():
        fields = [field.strip() for field in line.split(",")]
        if len(fields) != 4:
            continue
        index, name, memory_mib, driver = fields
        try:
            memory_value: int | None = int(memory_mib)
        except ValueError:
            memory_value = None
        gpus.append(
            {
                "index": int(index) if index.isdigit() else index,
                "name": name,
                "memory_total_mib": memory_value,
                "driver_version": driver,
            }
        )
    cuda_version: str | None = None
    cuda_version_source: str | None = None
    try:
        summary = subprocess.run(
            [executable],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        summary = None
    if summary is not None:
        match = re.search(r"CUDA Version:\s*([0-9.]+)", summary.stdout)
        if match:
            cuda_version = match.group(1)
            cuda_version_source = "nvidia-smi"

    if cuda_version is None:
        nvcc = shutil.which("nvcc")
        if nvcc is not None:
            try:
                nvcc_result = subprocess.run(
                    [nvcc, "--version"],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
            except (OSError, subprocess.TimeoutExpired):
                nvcc_result = None
            if nvcc_result is not None:
                match = re.search(r"release\s+([0-9.]+)", nvcc_result.stdout)
                if match:
                    cuda_version = match.group(1)
                    cuda_version_source = "nvcc"

    return {
        "gpu_count": len(gpus),
        "cuda_status": "NVIDIA_SMI_OK" if gpus else "NVIDIA_SMI_NO_GPUS",
        "cuda_version": cuda_version,
        "cuda_version_source": cuda_version_source,
        "gpus": gpus,
    }


def _internet_status(probe: bool) -> str:
    if not probe:
        return "NOT_PROBED_OFFLINE_POLICY"
    try:
        with socket.create_connection(("1.1.1.1", 53), timeout=1.0):
            return "TCP_PROBE_REACHABLE"
    except OSError:
        return "TCP_PROBE_UNREACHABLE"


def runtime_preflight(
    repo_root: str | Path,
    *,
    package_names: Sequence[str] = ("torch", "transformers", "accelerate", "bitsandbytes"),
    probe_internet: bool = False,
) -> dict[str, object]:
    """Collect non-secret environment facts without importing ML packages."""

    root = Path(repo_root).resolve()
    disk = shutil.disk_usage(root)
    gpu = _gpu_inventory()
    return {
        "schema_version": 1,
        "evidence_class": FIXTURE_EVIDENCE_CLASS,
        "python": {
            "version": platform.python_version(),
            "executable_name": Path(sys.executable).name,
            "implementation": platform.python_implementation(),
        },
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "repository": {
            "root_name": root.name,
            "pyproject_present": (root / "pyproject.toml").is_file(),
            "package_source_present": (root / "src" / "causal_agent_bench").is_dir(),
        },
        "system_ram_gib": _system_memory_gib(),
        "disk": {
            "total_gib": round(disk.total / (1024**3), 3),
            "free_gib": round(disk.free / (1024**3), 3),
        },
        "packages": {
            name: importlib.util.find_spec(name) is not None for name in sorted(package_names)
        },
        "internet_status": _internet_status(probe_internet),
        **gpu,
    }


def model_snapshot_record(snapshot_path: str | None) -> dict[str, object]:
    """Record lightweight model metadata without hashing large weight files."""

    if not snapshot_path:
        return {
            "configured": False,
            "exists": False,
            "status": "MODEL_SNAPSHOT_PATH_NOT_CONFIGURED",
            "metadata_files": [],
        }
    root = Path(snapshot_path).expanduser()
    if not root.is_dir():
        return {
            "configured": True,
            "exists": False,
            "status": "MODEL_SNAPSHOT_DIRECTORY_MISSING",
            "root_name": root.name,
            "metadata_files": [],
        }
    metadata_names = {
        "config.json",
        "generation_config.json",
        "preprocessor_config.json",
        "special_tokens_map.json",
        "tokenizer.json",
        "tokenizer_config.json",
    }
    metadata_files: list[dict[str, object]] = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.name in metadata_names:
            metadata_files.append(
                {
                    "path": path.relative_to(root).as_posix(),
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
            )
    return {
        "configured": True,
        "exists": True,
        "status": "MODEL_SNAPSHOT_METADATA_RECORDED",
        "root_name": root.name,
        "metadata_files": metadata_files,
    }


def export_fixture_archive(fixture_root: str | Path, archive_stem: str | Path) -> Path:
    """Create a convenience ZIP export via ``shutil.make_archive``.

    ZIP ordering and timestamps are not treated as provenance.  File-level
    hashes inside ``integrity_manifest.json`` are the authoritative surface.
    """

    root = Path(fixture_root).resolve()
    stem = Path(archive_stem).resolve()
    stem.parent.mkdir(parents=True, exist_ok=True)
    archive = shutil.make_archive(str(stem), "zip", root_dir=root.parent, base_dir=root.name)
    return Path(archive)
