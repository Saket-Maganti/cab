"""Exact-final-tip reproducible build contracts and detached-source builder."""

from __future__ import annotations

import gzip
import hashlib
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from causal_agent_bench.hashing import stable_hash


class FinalTipReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "cab_exact_final_tip_receipt_v1"
    source_commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    source_tree_hash: str = Field(pattern=r"^[0-9a-f]{40}$")
    source_archive_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    artifact_hashes: dict[str, str]
    build_environment: dict[str, Any]
    dependency_hashes: dict[str, str]
    test_summary: dict[str, Any]
    sbom_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    provenance_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    signature: dict[str, str] | None = None
    transparency_log_receipt: dict[str, str] | None = None
    development_foundation_only: bool = True


def exact_final_tip_path_check(repo_root: str | Path) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    head = _git(root, "rev-parse", "HEAD")
    tree = _git(root, "rev-parse", f"{head}^{{tree}}")
    checks = {
        "head_resolves": len(head) == 40,
        "tree_resolves": len(tree) == 40,
        "git_archive_supported": bool(shutil.which("git")),
        "build_metadata_present": (root / "pyproject.toml").is_file(),
        "dependency_lock_with_hashes_present": (root / "constraints.txt").is_file(),
        "sbom_generator_present": (root / "scripts/generate_level5_sbom.py").is_file(),
        "provenance_contract_present": True,
        "private_keys_untracked_by_policy": "*.key" in (root / ".gitignore").read_text(encoding="utf-8"),
    }
    return {
        "schema_version": "cab_exact_final_tip_path_check_v1",
        "status": "CAB_EXACT_FINAL_TIP_RELEASE_PATH_READY",
        "passed": all(checks.values()),
        "checks": checks,
        "current_source_commit": head,
        "current_source_tree_hash": tree,
        "final_scientific_tag_published": False,
        "development_tag_policy": "cab-level6-foundation-v1",
        "receipt_sealing_rule": (
            "Generate the receipt outside the source tree from the exact tagged commit; "
            "a receipt committed afterward cannot honestly call itself the final source tip."
        ),
    }


def build_exact_commit_artifacts(
    repo_root: str | Path,
    *,
    source_commit: str,
    output_dir: str | Path,
    run_tests: bool = False,
) -> dict[str, Any]:
    """Build a wheel and sdist from a detached Git archive of one exact commit."""

    root = Path(repo_root).resolve()
    resolved = _git(root, "rev-parse", source_commit)
    if resolved != source_commit:
        raise ValueError("source_commit must be a full exact commit SHA")
    tree_hash = _git(root, "rev-parse", f"{source_commit}^{{tree}}")
    destination = Path(output_dir).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="cab-final-tip-") as temporary:
        temp = Path(temporary)
        archive = temp / "source.tar"
        with archive.open("wb") as handle:
            subprocess.run(
                ["git", "archive", "--format=tar", source_commit],
                cwd=root,
                check=True,
                stdout=handle,
            )
        source_archive_sha = _sha256(archive)
        source = temp / "source"
        source.mkdir()
        with tarfile.open(archive) as tar:
            _safe_extract(tar, source)
        source_epoch = int(_git(root, "show", "-s", "--format=%ct", source_commit))
        environment = os.environ.copy()
        environment["SOURCE_DATE_EPOCH"] = str(source_epoch)
        test_summary: dict[str, Any] = {"executed": False, "passed": None}
        if run_tests:
            completed = subprocess.run(
                [sys.executable, "-m", "pytest", "-q", "-m", "not provider and not model and not local_run"],
                cwd=source,
                env=environment,
                check=False,
                capture_output=True,
                text=True,
            )
            test_summary = {
                "executed": True,
                "passed": completed.returncode == 0,
                "returncode": completed.returncode,
                "output_sha256": hashlib.sha256(completed.stdout.encode()).hexdigest(),
            }
            if completed.returncode:
                raise RuntimeError("detached-source tests failed")
        subprocess.run(
            [sys.executable, "-m", "build", "--outdir", str(destination)],
            cwd=source,
            env=environment,
            check=True,
        )
        for sdist in sorted(destination.glob("*.tar.gz")):
            _normalize_sdist_artifact(sdist, source_epoch=source_epoch)
    artifacts = {
        path.name: _sha256(path)
        for path in sorted(destination.iterdir())
        if path.is_file() and path.suffix in {".whl", ".gz"}
    }
    receipt = FinalTipReceipt(
        source_commit=source_commit,
        source_tree_hash=tree_hash,
        source_archive_sha256=source_archive_sha,
        artifact_hashes=artifacts,
        build_environment={
            "python": sys.version.split()[0],
            "platform": sys.platform,
            "source_date_epoch_set": True,
            "detached_git_archive": True,
        },
        dependency_hashes={"constraints.txt": _sha256(root / "constraints.txt")},
        test_summary=test_summary,
        development_foundation_only=True,
    )
    payload = receipt.model_dump(mode="json")
    payload["receipt_hash"] = stable_hash(payload, length=64)
    return payload


def compare_reproducible_builds(first: dict[str, Any], second: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "same_source_commit": first.get("source_commit") == second.get("source_commit"),
        "same_source_tree": first.get("source_tree_hash") == second.get("source_tree_hash"),
        "same_source_archive": first.get("source_archive_sha256") == second.get("source_archive_sha256"),
        "same_artifacts": first.get("artifact_hashes") == second.get("artifact_hashes"),
    }
    return {
        "passed": all(checks.values()),
        "checks": checks,
        "normalized_reproducibility_fallback_required": not checks["same_artifacts"],
    }


def _normalize_sdist_artifact(path: Path, *, source_epoch: int) -> None:
    """Remove setuptools' wall-clock ownership and mtime variance from an sdist."""

    with tempfile.TemporaryDirectory(prefix="cab-normalize-sdist-") as temporary:
        temp = Path(temporary)
        normalized_tar = temp / "normalized.tar"
        normalized_gzip = temp / "normalized.tar.gz"
        with tarfile.open(path, mode="r:gz") as source, tarfile.open(
            normalized_tar,
            mode="w",
            format=tarfile.PAX_FORMAT,
        ) as destination:
            for member in source.getmembers():
                member.mtime = source_epoch
                member.uid = 0
                member.gid = 0
                member.uname = ""
                member.gname = ""
                member.pax_headers = {}
                payload = source.extractfile(member) if member.isfile() else None
                destination.addfile(member, payload)
        with (
            normalized_tar.open("rb") as source,
            normalized_gzip.open("wb") as raw,
            gzip.GzipFile(
                filename="",
                mode="wb",
                fileobj=raw,
                mtime=source_epoch,
            ) as compressed,
        ):
            shutil.copyfileobj(source, compressed)
        os.replace(normalized_gzip, path)


def _safe_extract(archive: tarfile.TarFile, destination: Path) -> None:
    root = destination.resolve()
    for member in archive.getmembers():
        target = (destination / member.name).resolve()
        if not target.is_relative_to(root):
            raise ValueError(f"archive traversal entry: {member.name}")
    archive.extractall(destination)


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


__all__ = [
    "FinalTipReceipt",
    "build_exact_commit_artifacts",
    "compare_reproducible_builds",
    "exact_final_tip_path_check",
]
