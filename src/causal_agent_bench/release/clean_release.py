"""Clean-worktree build and release-path verification."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from causal_agent_bench.hashing import stable_hash


def run_clean_release_check(
    repo_root: str | Path,
    *,
    commit: str = "HEAD",
    output_path: str | Path | None = None,
) -> dict[str, Any]:
    """Build wheel/sdist and exercise import/CLI from a detached clean worktree."""

    root = Path(repo_root).resolve()
    source_commit = _run(["git", "rev-parse", commit], cwd=root).strip()
    source_tree = _run(["git", "rev-parse", f"{source_commit}^{{tree}}"], cwd=root).strip()
    with tempfile.TemporaryDirectory(prefix="cab-clean-release-") as temp:
        temp_root = Path(temp)
        worktree = temp_root / "worktree"
        dist = temp_root / "dist"
        subprocess.run(
            ["git", "worktree", "add", "--detach", str(worktree), source_commit],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
        try:
            clean_status = _run(["git", "status", "--porcelain=v1"], cwd=worktree)
            build = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "build",
                    "--no-isolation",
                    "--outdir",
                    str(dist),
                ],
                cwd=worktree,
                capture_output=True,
                text=True,
            )
            artifacts = sorted(dist.glob("*")) if dist.is_dir() else []
            twine = (
                subprocess.run(
                    [sys.executable, "-m", "twine", "check", *map(str, artifacts)],
                    cwd=worktree,
                    capture_output=True,
                    text=True,
                )
                if artifacts
                else None
            )
            wheel = next((path for path in artifacts if path.suffix == ".whl"), None)
            environment = dict(os.environ)
            if wheel is not None:
                environment["PYTHONPATH"] = str(wheel)
            import_check = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    (
                        "import causal_agent_bench; "
                        "from causal_agent_bench.cli_parsers import build_parser; "
                        "assert build_parser().prog"
                    ),
                ],
                cwd=temp_root,
                env=environment,
                capture_output=True,
                text=True,
            )
            inventory = [
                {
                    "name": path.name,
                    "bytes": path.stat().st_size,
                    "sha256": _sha256_file(path),
                }
                for path in artifacts
            ]
            checks = {
                "detached_clean_worktree": clean_status == "",
                "source_commit_exact": len(source_commit) == 40,
                "source_tree_exact": len(source_tree) == 40,
                "wheel_built": any(path.suffix == ".whl" for path in artifacts),
                "sdist_built": any(path.name.endswith(".tar.gz") for path in artifacts),
                "build_passed": build.returncode == 0,
                "twine_check_passed": twine is not None and twine.returncode == 0,
                "clean_import_and_cli_parser_passed": import_check.returncode == 0,
            }
            payload: dict[str, Any] = {
                "schema_version": "cab_clean_release_receipt_v1",
                "status": "CAB_CLEAN_RELEASE_PATH_READY"
                if all(checks.values())
                else "CAB_CLEAN_RELEASE_PATH_FAILED",
                "source_commit": source_commit,
                "source_tree_hash": source_tree,
                "development_manifest_label": "DEVELOPMENT_SNAPSHOT_NOT_FINAL_RELEASE",
                "checks": checks,
                "artifact_inventory": inventory,
                "build_stdout_tail": build.stdout[-2000:],
                "build_stderr_tail": build.stderr[-2000:],
                "twine_output_tail": ((twine.stdout + twine.stderr)[-2000:] if twine else ""),
                "import_output_tail": (import_check.stdout + import_check.stderr)[-2000:],
                "passed": all(checks.values()),
            }
            payload["receipt_hash"] = stable_hash(payload, length=64)
        finally:
            subprocess.run(
                ["git", "worktree", "remove", "--force", str(worktree)],
                cwd=root,
                check=False,
                capture_output=True,
                text=True,
            )
    if output_path is not None:
        output = Path(output_path)
        if not output.is_absolute():
            output = root / output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return payload


def _run(command: list[str], *, cwd: Path) -> str:
    return subprocess.run(
        command,
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


__all__ = ["run_clean_release_check"]
