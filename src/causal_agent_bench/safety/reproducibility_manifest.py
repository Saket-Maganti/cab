"""Static reproducibility manifest.

Tracks what artifacts in the repo are reproducible without provider/paid calls,
which datasets are frozen vs unfrozen, and which dependencies are pinned. No
provider, network, or shell-process is invoked.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from causal_agent_bench.safety.common import section_markdown, write_dual_report

DEPENDENCY_FILES = (
    "pyproject.toml",
    "requirements.txt",
    "requirements-lock.txt",
    "uv.lock",
    "poetry.lock",
    ".python-version",
)
DATA_LICENSE_FILES = ("DATA_LICENSE.md", "LICENSE", "CITATION.cff")
RUN_FORBIDDEN_TEST_PREFIXES = (
    "test_paper_assets",
    "test_paper_fill",
    "test_experiment_runner",
    "test_batch_runner",
    "test_run_management",
)


def build_reproducibility_manifest(
    repo_root: str | Path,
    *,
    output_dir: str | Path = "reports/reproducibility_manifest",
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    out = Path(output_dir)
    if not out.is_absolute():
        out = root / out

    frozen_datasets = _frozen_datasets(root)
    unfrozen_datasets = _unfrozen_datasets(root)
    dependency_state = _dependency_state(root)
    license_state = _license_state(root)
    no_run_safety = _no_run_safety_state(root)

    blockers: list[str] = []
    warnings: list[str] = []
    if not frozen_datasets:
        warnings.append("No frozen dataset directory found (data/frozen/*).")
    if not dependency_state.get("pyproject_present") and not dependency_state.get("requirements_present"):
        warnings.append("No pyproject.toml or requirements.txt found.")
    if not dependency_state.get("lockfile_present"):
        warnings.append("No lockfile found (uv.lock / poetry.lock / requirements-lock.txt).")
    if license_state.get("license_present") is False:
        blockers.append("LICENSE file missing.")
    if license_state.get("data_license_present") is False:
        warnings.append("DATA_LICENSE.md missing.")

    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": (
            "Static reproducibility manifest. Lists frozen vs unfrozen datasets, "
            "dependency lockfile state, license files, and forbidden tests. "
            "No provider/network/shell calls."
        ),
        "summary": {
            "frozen_dataset_count": len(frozen_datasets),
            "unfrozen_dataset_count": len(unfrozen_datasets),
            "dependency_files_present": dependency_state["files_present"],
            "lockfile_present": dependency_state["lockfile_present"],
            "license_present": license_state["license_present"],
            "data_license_present": license_state["data_license_present"],
            "citation_present": license_state["citation_present"],
            "no_run_safety_check_present": no_run_safety["check_script_present"],
            "blocker_count": len(blockers),
            "warning_count": len(warnings),
        },
        "verdicts": {
            "ready_for_public_reproducibility_packet": not blockers,
            "all_datasets_frozen": len(unfrozen_datasets) == 0,
            "dependency_locked": dependency_state["lockfile_present"],
            "license_complete": license_state["license_present"] and license_state["data_license_present"],
        },
        "frozen_datasets": frozen_datasets,
        "unfrozen_datasets": unfrozen_datasets,
        "dependency_state": dependency_state,
        "license_state": license_state,
        "no_run_safety": no_run_safety,
        "blockers": blockers,
        "warnings": warnings,
        "forbidden_run_tests": _forbidden_run_tests(root),
    }
    md = reproducibility_manifest_markdown(payload)
    md_path, json_path = write_dual_report(
        stem="reproducibility_manifest",
        payload=payload,
        markdown=md,
        output_dir=out,
    )
    payload["report_paths"] = {"markdown": str(md_path), "json": str(json_path)}
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def reproducibility_manifest_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# Reproducibility Manifest",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        payload["scope"],
        "",
        section_markdown(
            "Summary",
            [
                f"- Frozen datasets: {summary['frozen_dataset_count']}",
                f"- Unfrozen datasets: {summary['unfrozen_dataset_count']}",
                f"- Dependency files present: {summary['dependency_files_present']}",
                f"- Lockfile present: `{summary['lockfile_present']}`",
                f"- LICENSE present: `{summary['license_present']}`",
                f"- DATA_LICENSE present: `{summary['data_license_present']}`",
                f"- CITATION.cff present: `{summary['citation_present']}`",
                f"- No-run safety check script present: `{summary['no_run_safety_check_present']}`",
                f"- Blockers: {summary['blocker_count']}",
                f"- Warnings: {summary['warning_count']}",
            ],
        ),
        section_markdown(
            "Verdicts",
            [
                f"- Ready for public reproducibility packet: `{payload['verdicts']['ready_for_public_reproducibility_packet']}`",
                f"- All datasets frozen: `{payload['verdicts']['all_datasets_frozen']}`",
                f"- Dependencies locked: `{payload['verdicts']['dependency_locked']}`",
                f"- License complete: `{payload['verdicts']['license_complete']}`",
            ],
        ),
        "## Frozen Datasets",
        "",
    ]
    if not payload["frozen_datasets"]:
        lines.append("- (none)")
    for d in payload["frozen_datasets"]:
        lines.append(f"- `{d['path']}` files={d['file_count']} hash_prefix={d['content_hash_prefix']}")
    lines.extend(["", "## Unfrozen Datasets", ""])
    if not payload["unfrozen_datasets"]:
        lines.append("- (none)")
    for d in payload["unfrozen_datasets"]:
        lines.append(f"- `{d['path']}` files={d['file_count']}")
    lines.extend(["", "## Forbidden Run Tests", "", "These tests are excluded from the no-run lane; the harness must not invoke them."])
    for prefix in payload["forbidden_run_tests"]:
        lines.append(f"- `tests/{prefix}*.py`")
    lines.extend(["", "## Blockers", ""])
    if not payload["blockers"]:
        lines.append("- (none)")
    for b in payload["blockers"]:
        lines.append(f"- {b}")
    lines.extend(["", "## Warnings", ""])
    if not payload["warnings"]:
        lines.append("- (none)")
    for w in payload["warnings"]:
        lines.append(f"- {w}")
    lines.append("")
    return "\n".join(lines)


def _frozen_datasets(root: Path) -> list[dict[str, Any]]:
    base = root / "data/frozen"
    if not base.exists():
        return []
    out: list[dict[str, Any]] = []
    for path in sorted(base.iterdir()):
        if not path.is_dir():
            continue
        files = list(path.glob("**/*"))
        files = [p for p in files if p.is_file()]
        digest = hashlib.sha1()
        for file_path in sorted(files):
            digest.update(file_path.name.encode("utf-8"))
            with contextlib.suppress(OSError):
                digest.update(str(file_path.stat().st_size).encode("utf-8"))
        out.append(
            {
                "path": str(path.relative_to(root)),
                "file_count": len(files),
                "content_hash_prefix": digest.hexdigest()[:16],
            }
        )
    return out


def _unfrozen_datasets(root: Path) -> list[dict[str, Any]]:
    base = root / "data/processed"
    if not base.exists():
        return []
    out: list[dict[str, Any]] = []
    for path in sorted(base.iterdir()):
        if not path.is_dir():
            continue
        files = [p for p in path.glob("**/*") if p.is_file()]
        out.append({"path": str(path.relative_to(root)), "file_count": len(files)})
    return out


def _dependency_state(root: Path) -> dict[str, Any]:
    present: list[str] = []
    lockfile_present = False
    for name in DEPENDENCY_FILES:
        if (root / name).exists():
            present.append(name)
            if "lock" in name:
                lockfile_present = True
    return {
        "files_present": present,
        "pyproject_present": "pyproject.toml" in present,
        "requirements_present": "requirements.txt" in present,
        "lockfile_present": lockfile_present,
        "python_version_pinned": ".python-version" in present,
    }


def _license_state(root: Path) -> dict[str, Any]:
    return {
        "license_present": (root / "LICENSE").exists(),
        "data_license_present": (root / "DATA_LICENSE.md").exists(),
        "citation_present": (root / "CITATION.cff").exists(),
    }


def _no_run_safety_state(root: Path) -> dict[str, Any]:
    script = root / "scripts/check_evidence_safety.py"
    return {
        "check_script_present": script.exists(),
        "command": "python3 scripts/check_evidence_safety.py",
    }


def _forbidden_run_tests(root: Path) -> list[str]:
    tests_dir = root / "tests"
    if not tests_dir.exists():
        return list(RUN_FORBIDDEN_TEST_PREFIXES)
    present: list[str] = []
    for prefix in RUN_FORBIDDEN_TEST_PREFIXES:
        if any(tests_dir.glob(f"{prefix}*.py")):
            present.append(prefix)
    return present
