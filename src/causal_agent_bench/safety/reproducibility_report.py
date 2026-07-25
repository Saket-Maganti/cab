from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from causal_agent_bench.safety.common import section_markdown, write_dual_report


def build_reproducibility_report(
    repo_root: str | Path,
    *,
    output_dir: str | Path = "reports",
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    out = Path(output_dir)
    if not out.is_absolute():
        out = root / out

    python_cmd = shutil.which("python")
    python3_cmd = shutil.which("python3")
    py_version = _python_version(python3_cmd or python_cmd)

    imports = _check_imports()
    pyproject_req = _read_pyproject_python(root)
    python_version_file = _read_python_version(root)
    lockfiles = _find_lockfiles(root)
    readme_cmds = _readme_python_usage(root)

    recommendations = _recommendations(
        python_cmd=python_cmd,
        python3_cmd=python3_cmd,
        py_version=py_version,
        pyproject_req=pyproject_req,
        python_version_file=python_version_file,
        lockfiles=lockfiles,
        readme_cmds=readme_cmds,
        imports=imports,
    )

    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "python": {
            "python_on_path": python_cmd,
            "python3_on_path": python3_cmd,
            "active_version": py_version,
            "sys_executable": sys.executable,
            "sys_version": sys.version.split()[0],
        },
        "imports": imports,
        "pyproject_python_requirement": pyproject_req,
        "dot_python_version": python_version_file,
        "lockfiles": lockfiles,
        "readme_command_style": readme_cmds,
        "recommendations": recommendations,
    }
    md = _format_markdown(payload)
    md_path, json_path = write_dual_report(
        stem="reproducibility_environment_report",
        payload=payload,
        markdown=md,
        output_dir=out,
    )
    payload["report_paths"] = {"markdown": str(md_path), "json": str(json_path)}
    return payload


def _python_version(cmd: str | None) -> str | None:
    if not cmd:
        return None
    try:
        result = subprocess.run(
            [cmd, "--version"],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return (result.stdout or result.stderr).strip()
    except (OSError, subprocess.SubprocessError):
        return None


def _check_imports() -> dict[str, Any]:
    modules = ("causal_agent_bench", "pandas", "numpy", "yaml", "pydantic", "matplotlib")
    status: dict[str, Any] = {}
    for name in modules:
        spec = importlib.util.find_spec(name)
        if spec is None:
            status[name] = {"available": False}
            continue
        try:
            mod = importlib.import_module(name)
            status[name] = {"available": True, "version": getattr(mod, "__version__", None)}
        except ImportError as exc:
            status[name] = {"available": False, "error": str(exc)}
    return status


def _read_pyproject_python(root: Path) -> str | None:
    path = root / "pyproject.toml"
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    for line in text.splitlines():
        if "requires-python" in line:
            return line.strip()
    return None


def _read_python_version(root: Path) -> str | None:
    path = root / ".python-version"
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    return None


def _find_lockfiles(root: Path) -> list[str]:
    names = []
    for candidate in (
        "uv.lock",
        "poetry.lock",
        "Pipfile.lock",
        "requirements-lock.txt",
        "requirements.txt",
        "constraints.txt",
    ):
        if (root / candidate).exists():
            names.append(candidate)
    return names


def _readme_python_usage(root: Path) -> dict[str, int]:
    readme = root / "README.md"
    counts = {"python": 0, "python3": 0}
    if not readme.exists():
        return counts
    text = readme.read_text(encoding="utf-8")
    counts["python"] = len([m for m in text.split() if m.startswith("python ") and not m.startswith("python3")])
    counts["python3"] = text.count("python3")
    return counts


def _recommendations(**ctx: Any) -> list[str]:
    recs: list[str] = []
    if not ctx["python3_cmd"]:
        recs.append("Install or expose python3 on PATH; document all commands with python3.")
    if ctx["python_version_file"] and "3.11.9" in str(ctx["python_version_file"]):
        recs.append("Fix pyenv 3.11.9 mismatch or standardize docs on python3 from a working interpreter.")
    if not ctx["lockfiles"]:
        recs.append("Add a lockfile or pinned requirements strategy for reproducible installs.")
    if ctx["readme_cmds"].get("python", 0) > ctx["readme_cmds"].get("python3", 0):
        recs.append("Prefer python3 in README examples (local pyenv python may be broken).")
    missing = [k for k, v in ctx["imports"].items() if not v.get("available")]
    if missing:
        recs.append(f"Missing imports for: {', '.join(missing)} — run pip install -e '.[dev]' with python3.")
    recs.append("Safe validation: python3 -m pytest tests/test_safety_reports.py -q")
    recs.append("Before provider runs: python3 -m causal_agent_bench.cli all-safety-reports")
    return recs


def _format_markdown(payload: dict[str, Any]) -> str:
    py = payload["python"]
    lines = [
        "# Reproducibility / environment report",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "Read-only environment inspection. Does not install packages or call providers.",
        "",
        section_markdown(
            "Python",
            [
                f"- `python`: {py.get('python_on_path')}",
                f"- `python3`: {py.get('python3_on_path')}",
                f"- Active: {py.get('active_version')}",
                f"- sys.executable: {py.get('sys_executable')}",
            ],
        ),
        section_markdown(
            "Project pins",
            [
                f"- pyproject: `{payload.get('pyproject_python_requirement')}`",
                f"- .python-version: `{payload.get('dot_python_version')}`",
                f"- Lockfiles: {', '.join(payload.get('lockfiles') or []) or '(none)'}",
            ],
        ),
        section_markdown(
            "Recommendations",
            [f"- {r}" for r in payload.get("recommendations", [])],
        ),
    ]
    return "\n".join(lines)
