"""Capture environment metadata without secrets."""

from __future__ import annotations

import contextlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from causal_agent_bench.utils.io import git_commit, write_json

SECRET_ENV_SUFFIXES = ("_KEY", "_TOKEN", "_SECRET", "_PASSWORD")


def _git_dirty(repo_root: Path) -> bool | None:
    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        return bool(proc.stdout.strip()) if proc.returncode == 0 else None
    except OSError:
        return None


def _provider_status() -> dict[str, bool]:
    status: dict[str, bool] = {}
    for name in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "OPENROUTER_API_KEY", "GEMINI_API_KEY"):
        status[name] = bool(os.environ.get(name))
    return status


def _ollama_available() -> bool | None:
    if shutil.which("ollama") is None:
        return False
    try:
        proc = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
        return proc.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return None


def _disk_usage_results(repo_root: Path) -> dict[str, Any]:
    results = repo_root / "results"
    if not results.exists():
        return {"present": False, "total_bytes": 0, "run_dir_count": 0}
    total = 0
    count = 0
    for child in results.iterdir():
        if child.is_dir():
            count += 1
            for path in child.rglob("*"):
                if path.is_file():
                    with contextlib.suppress(OSError):
                        total += path.stat().st_size
    return {"present": True, "total_bytes": total, "run_dir_count": count}


def _pip_freeze() -> list[str] | str:
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pip", "freeze"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if proc.returncode != 0:
            return f"pip freeze failed: {proc.stderr.strip()[:200]}"
        return proc.stdout.strip().splitlines()
    except (OSError, subprocess.TimeoutExpired) as exc:
        return str(exc)


def _python_warnings() -> list[str]:
    warnings: list[str] = []
    if shutil.which("python") is None and shutil.which("python3"):
        warnings.append("python not on PATH but python3 works — prefer python3 in docs/CI")
    return warnings


def capture_environment(repo_root: str | Path | None = None) -> dict[str, Any]:
    root = Path(repo_root or Path.cwd()).resolve()
    report: dict[str, Any] = {
        "generated_at": datetime.now(UTC).isoformat(),
        "os": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python": {
            "executable": sys.executable,
            "version": sys.version,
            "implementation": platform.python_implementation(),
        },
        "git": {
            "commit": git_commit(root),
            "dirty": _git_dirty(root),
        },
        "providers_configured": _provider_status(),
        "ollama": {
            "cli_present": shutil.which("ollama") is not None,
            "list_available": _ollama_available(),
            "models_not_queried": True,
        },
        "disk_usage": {"results": _disk_usage_results(root)},
        "pip_freeze": _pip_freeze(),
        "warnings": _python_warnings(),
        "secrets_policy": "No secret values captured; only configured/not-configured flags.",
    }

    # Redaction pass — env var names like OPENAI_API_KEY are OK; reject value-like secrets only
    text = json.dumps(report)
    if re.search(r"sk-[a-zA-Z0-9]{20,}", text):
        raise ValueError("environment report contains secret-like content")

    env_dir = root / "environment"
    env_dir.mkdir(parents=True, exist_ok=True)
    write_json(env_dir / "env_report.json", report)
    (env_dir / "env_report.md").write_text(_env_markdown(report), encoding="utf-8")
    return report


def _env_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Environment Report",
        "",
        f"Generated: `{report['generated_at']}`",
        "",
        f"- OS: `{report['os']}`",
        f"- Machine: `{report['machine']}`",
        f"- Python: `{report['python']['version'].split()[0]}` ({report['python']['executable']})",
        f"- Git commit: `{report['git']['commit']}` (dirty={report['git']['dirty']})",
        "",
        "## Providers (configured flag only)",
        "",
    ]
    for name, configured in report["providers_configured"].items():
        lines.append(f"- `{name}`: {'yes' if configured else 'no'}")
    lines.extend(
        [
            "",
            "## Ollama",
            "",
            f"- CLI present: {report['ollama']['cli_present']}",
            f"- `ollama list` OK: {report['ollama']['list_available']}",
            "",
            "## Results disk usage",
            "",
            f"- Run dirs: {report['disk_usage']['results'].get('run_dir_count', 0)}",
            f"- Total bytes: {report['disk_usage']['results'].get('total_bytes', 0)}",
            "",
        ]
    )
    if report.get("warnings"):
        lines.extend(["## Warnings", ""])
        for w in report["warnings"]:
            lines.append(f"- {w}")
    lines.append("")
    return "\n".join(lines)
