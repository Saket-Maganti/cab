"""Clean-checkout, clean-venv, and optional container reproduction receipts."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from typing import Any

from causal_agent_bench.level5.core import content_hash, utc_now


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    timeout: int = 900,
) -> dict[str, Any]:
    if env is None:
        env = {
            key: value
            for key, value in os.environ.items()
            if key
            not in {
                "CONDA_PREFIX",
                "PYTHONHOME",
                "PYTHONPATH",
                "VIRTUAL_ENV",
                "__PYVENV_LAUNCHER__",
            }
        }
        env["PYTHONNOUSERSITE"] = "1"
    started = utc_now()
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        exit_code: int | None = completed.returncode
        stdout = completed.stdout
        stderr = completed.stderr
        state = "PASSED" if completed.returncode == 0 else "FAILED"
    except subprocess.TimeoutExpired as exc:
        exit_code = None
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        state = "TIMED_OUT"
    return {
        "command": command,
        "cwd_class": "CLEAN_SOURCE",
        "started_at": started,
        "finished_at": utc_now(),
        "exit_code": exit_code,
        "state": state,
        "stdout_hash": content_hash(stdout),
        "stderr_hash": content_hash(stderr),
        "stdout_tail": stdout[-2_000:],
        "stderr_tail": stderr[-2_000:],
    }


def _safe_extract(source: Path, destination: Path) -> None:
    destination_resolved = destination.resolve()
    with tarfile.open(source, "r") as archive:
        for member in archive.getmembers():
            target = (destination / member.name).resolve()
            if destination_resolved not in target.parents and target != destination_resolved:
                raise ValueError("source archive contains a traversal path")
            if member.issym() or member.islnk():
                raise ValueError("source archive contains a link")
        archive.extractall(destination, filter="data")


def _reproduction_observations(receipt_path: Path) -> dict[str, Any]:
    if not receipt_path.is_file():
        return {"present": False}
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    return {
        "present": True,
        "passed": bool(receipt.get("passed")),
        "manifest_hash": receipt.get("manifest_hash"),
        "merge_digest": receipt.get("merge_digest"),
        "graph_hash": receipt.get("graph_hash"),
        "receipt_hash": receipt.get("receipt_hash"),
    }


def run_cleanroom_reproduction(
    repo_root: str | Path,
    output_path: str | Path,
    *,
    source_commit: str = "HEAD",
    execute_container: bool = True,
) -> dict[str, Any]:
    """Reproduce from a committed source archive, never the developer worktree."""

    root = Path(repo_root).resolve()
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    commands: list[dict[str, Any]] = []
    discrepancies: list[str] = []
    observed_artifacts: dict[str, Any] = {}

    commit_result = subprocess.run(
        ["git", "rev-parse", "--verify", f"{source_commit}^{{commit}}"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    commit = commit_result.stdout.strip()
    with tempfile.TemporaryDirectory(prefix="cab-cleanroom-") as temp_name:
        temp = Path(temp_name)
        source_archive = temp / "source.tar"
        with source_archive.open("wb") as archive_stream:
            archive_result = subprocess.run(
                ["git", "archive", "--format=tar", commit],
                cwd=root,
                check=False,
                stdout=archive_stream,
                stderr=subprocess.PIPE,
            )
        if archive_result.returncode != 0:
            raise RuntimeError("git archive failed for clean-room source")
        source_archive_hash = _file_hash(source_archive)
        source = temp / "source"
        source.mkdir()
        _safe_extract(source_archive, source)

        dist = temp / "dist"
        build = _run(
            [
                sys.executable,
                "-m",
                "build",
                "--outdir",
                str(dist),
                str(source),
            ],
            cwd=temp,
        )
        commands.append(build)
        wheels = sorted(dist.glob("*.whl"))
        sdists = sorted(dist.glob("*.tar.gz"))
        wheel_hash = _file_hash(wheels[0]) if wheels else None
        sdist_hash = _file_hash(sdists[0]) if sdists else None
        if build["state"] != "PASSED" or not wheels or not sdists:
            discrepancies.append("PACKAGE_BUILD_FAILED")

        venv = temp / "venv"
        create_venv = _run([sys.executable, "-m", "venv", str(venv)], cwd=temp)
        commands.append(create_venv)
        venv_python = venv / "bin" / "python"
        clean_run = temp / "clean_run"
        if wheels and create_venv["state"] == "PASSED":
            install = _run(
                [
                    str(venv_python),
                    "-m",
                    "pip",
                    "install",
                    "--constraint",
                    str(source / "constraints.txt"),
                    str(wheels[0]),
                ],
                cwd=temp,
            )
            commands.append(install)
            reproduce = _run(
                [
                    str(venv_python),
                    "-m",
                    "causal_agent_bench",
                    "reproduce",
                    "--workdir",
                    str(clean_run),
                ],
                cwd=temp,
            )
            commands.append(reproduce)
        else:
            install = {"state": "NOT_EXECUTED", "reason": "wheel or venv unavailable"}
            reproduce = {"state": "NOT_EXECUTED", "reason": "installation unavailable"}
        clean_observations = _reproduction_observations(
            clean_run / "reproduction_receipt.json"
        )
        observed_artifacts["clean_environment"] = clean_observations
        if install["state"] != "PASSED":
            discrepancies.append("CLEAN_WHEEL_INSTALL_FAILED")
        if reproduce["state"] != "PASSED" or not clean_observations.get("passed"):
            discrepancies.append("CLEAN_VENV_REPRODUCTION_FAILED")

        checkout_run = temp / "checkout_run"
        source_env = {
            key: value
            for key, value in os.environ.items()
            if key
            not in {
                "CONDA_PREFIX",
                "PYTHONHOME",
                "PYTHONPATH",
                "VIRTUAL_ENV",
                "__PYVENV_LAUNCHER__",
            }
        }
        source_env.update(
            {
                "PYTHONPATH": str(source / "src"),
                "PYTHONNOUSERSITE": "1",
            }
        )
        checkout_reproduce = _run(
            [
                sys.executable,
                "-m",
                "causal_agent_bench",
                "reproduce",
                "--workdir",
                str(checkout_run),
            ],
            cwd=source,
            env=source_env,
        )
        commands.append(checkout_reproduce)
        checkout_observations = _reproduction_observations(
            checkout_run / "reproduction_receipt.json"
        )
        observed_artifacts["clean_checkout"] = checkout_observations
        if checkout_reproduce["state"] != "PASSED" or not checkout_observations.get(
            "passed"
        ):
            discrepancies.append("CLEAN_CHECKOUT_REPRODUCTION_FAILED")
        for field in ("manifest_hash", "merge_digest", "graph_hash"):
            if clean_observations.get(field) != checkout_observations.get(field):
                discrepancies.append(f"HASH_MISMATCH_{field.upper()}")

        docker_path = shutil.which("docker")
        container: dict[str, Any]
        if execute_container and docker_path:
            tag = f"cab-cleanroom:{commit[:12]}"
            build_container = _run(
                [docker_path, "build", "--tag", tag, "."],
                cwd=source,
                timeout=1_800,
            )
            commands.append(build_container)
            if build_container["state"] == "PASSED":
                container_command = [
                    docker_path,
                    "run",
                    "--rm",
                    "--network",
                    "none",
                    tag,
                    "sh",
                    "-lc",
                    (
                        "cab env doctor --repo-root /app"
                        " && cab registry init --path /tmp/registry.sqlite3"
                        " && cab reproduce --workdir /tmp/reproduction"
                        " && cab level5 hardening-check"
                        " && cab benchmark compile"
                        " --spec /app/examples/level5/public_fixture/authoring.yaml"
                        " --output-dir /tmp/benchmark"
                    ),
                ]
                container = _run(container_command, cwd=source, timeout=900)
                commands.append(container)
            else:
                container = {
                    "state": "NOT_EXECUTED",
                    "reason": "container image build failed",
                }
            if container["state"] not in {"PASSED", "NOT_EXECUTED"}:
                discrepancies.append("CONTAINER_REPRODUCTION_FAILED")
        else:
            container = {
                "state": "NOT_EXECUTED",
                "reason": (
                    "container execution disabled"
                    if not execute_container
                    else "Docker unavailable"
                ),
            }

        receipt = {
            "schema_version": "1.0",
            "source_commit": commit,
            "source_archive_hash": source_archive_hash,
            "wheel_hash": wheel_hash,
            "sdist_hash": sdist_hash,
            "lockfile_hash": _file_hash(source / "constraints.txt"),
            "python": platform.python_version(),
            "os": platform.platform(),
            "architecture": platform.machine(),
            "container_digest": (
                content_hash([commit, build_container.get("stdout_hash")])
                if execute_container and docker_path and "build_container" in locals()
                else None
            ),
            "commands": commands,
            "expected_artifacts": [
                "manifest_hash",
                "merge_digest",
                "graph_hash",
            ],
            "observed_artifacts": observed_artifacts,
            "discrepancies": sorted(set(discrepancies)),
            "modes": {
                "clean_environment": "INTERNAL_CLEAN_ENVIRONMENT",
                "clean_checkout": "INTERNAL_CLEAN_CHECKOUT",
                "container": {
                    "class": "INTERNAL_CONTAINER",
                    **container,
                },
            },
            "external_independent_reproduction": "NOT_EXECUTED",
            "passed": not discrepancies
            and container["state"] in {"PASSED", "NOT_EXECUTED"},
            "created_at": utc_now(),
        }
        receipt["receipt_hash"] = content_hash(receipt)
        output.write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return receipt


__all__ = ["run_cleanroom_reproduction"]
