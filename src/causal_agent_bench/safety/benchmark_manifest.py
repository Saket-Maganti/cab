"""Benchmark version and provenance manifest generator."""

from __future__ import annotations

import json
import subprocess
import sys
import tomllib
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from causal_agent_bench.safety.benchmark_quality import discover_benchmark_dirs
from causal_agent_bench.safety.common import (
    classify_run_entry,
    load_run_index_entries,
    section_markdown,
    write_dual_report,
)


def build_benchmark_manifest(
    repo_root: str | Path,
    *,
    output_dir: str | Path = "reports/benchmark_manifest",
    results_root: str | Path = "results",
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    out = Path(output_dir)
    if not out.is_absolute():
        out = root / out
    pyproject = _read_pyproject(root / "pyproject.toml")
    git = _git_status(root)
    data_dirs = [_rel(path.resolve(), root) for path in discover_benchmark_dirs(root)]
    config_files = sorted(_rel(path, root) for path in (root / "configs").rglob("*.yaml")) if (root / "configs").exists() else []
    run_entries = [classify_run_entry(entry, root) for entry in load_run_index_entries(root, results_root=results_root)]
    paper_eligible = [row for row in run_entries if row.get("paper_eligible")]
    claim_state = _claim_state(root)
    evidence_state = {
        "paper_eligible_runs": len(paper_eligible),
        "eligible_paper_assets": int((_read_json(root / "reports/paper_asset_eligibility.json") or {}).get("eligible_count") or 0),
        "provider_evidence_present": any(row.get("classification") in {"provider_backed_pilot", "main_benchmark"} for row in paper_eligible),
        "claims_promoted_by_manifest": False,
    }
    checks = _checks(root, git, evidence_state)
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": "Static benchmark provenance manifest only; no benchmark run, provider call, or model call.",
        "repository": git,
        "python": {"version": sys.version.split()[0], "executable": sys.executable},
        "package": {
            "pyproject_name": (pyproject.get("project") or {}).get("name"),
            "pyproject_version": (pyproject.get("project") or {}).get("version"),
            "requires_python": (pyproject.get("project") or {}).get("requires-python"),
        },
        "data_directories": data_dirs,
        "config_files": config_files,
        "dataset_versions": _dataset_versions(root),
        "generation_configs": [path for path in config_files if "generate" in Path(path).name],
        "frozen_split_manifests": sorted(_rel(path, root) for path in (root / "data/frozen").glob("*/freeze_manifest.json")) if (root / "data/frozen").exists() else [],
        "run_index_summary": {
            "run_count": len(run_entries),
            "classifications": dict(Counter(str(row.get("classification")) for row in run_entries)),
            "paper_eligible_run_count": len(paper_eligible),
        },
        "evidence_state": evidence_state,
        "claim_state": claim_state,
        "provider_pilot_readiness_status": _provider_status(root),
        "no_run_report_timestamps": _report_timestamps(root / "reports"),
        "lockfile_status": _lockfile_status(root),
        "licenses_docs_present": {
            "license": (root / "LICENSE").exists() or (root / "LICENSE.md").exists(),
            "data_license": (root / "DATA_LICENSE.md").exists(),
            "citation": (root / "CITATION.cff").exists(),
            "reproducibility_doc": (root / "docs/REPRODUCIBILITY.md").exists(),
        },
        "checks": checks,
        "readiness": {
            "release_dirty_tree_blocker": bool(git.get("dirty_tree_count")),
            "empirical_paper_blocked": not evidence_state["provider_evidence_present"] or len(paper_eligible) == 0,
            "claims_promoted": False,
        },
    }
    md = benchmark_manifest_markdown(payload)
    md_path, json_path = write_dual_report(
        stem="benchmark_manifest",
        payload=payload,
        markdown=md,
        output_dir=out,
    )
    payload["report_paths"] = {"markdown": str(md_path), "json": str(json_path)}
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def benchmark_manifest_markdown(payload: dict[str, Any]) -> str:
    repo = payload["repository"]
    evidence = payload["evidence_state"]
    lines = [
        "# Benchmark Manifest",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        payload["scope"],
        "",
        section_markdown(
            "Repository",
            [
                f"- Branch: `{repo.get('branch')}`",
                f"- Commit: `{repo.get('commit')}`",
                f"- Dirty tree count: `{repo.get('dirty_tree_count')}`",
            ],
        ),
        section_markdown(
            "Evidence State",
            [
                f"- Paper-eligible runs: {evidence['paper_eligible_runs']}",
                f"- Eligible paper assets: {evidence['eligible_paper_assets']}",
                f"- Provider evidence present: `{evidence['provider_evidence_present']}`",
                "- Claims promoted by manifest: `False`",
            ],
        ),
        "## Checks",
        "",
    ]
    for check in payload["checks"]:
        lines.append(f"- `{check['severity']}` `{check['id']}`: {check['message']}")
    lines.append("")
    return "\n".join(lines)


def _git_status(root: Path) -> dict[str, Any]:
    branch = _git(root, "rev-parse", "--abbrev-ref", "HEAD")
    commit = _git(root, "rev-parse", "HEAD")
    status = _git(root, "status", "--porcelain")
    dirty_lines = [line for line in status.splitlines() if line.strip()] if status is not None else []
    return {
        "available": branch is not None or commit is not None,
        "branch": branch,
        "commit": commit,
        "dirty_tree_count": len(dirty_lines) if status is not None else None,
        "dirty_tree_sample": dirty_lines[:20],
    }


def _git(root: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def _checks(root: Path, git: dict[str, Any], evidence: dict[str, Any]) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []
    if not git.get("commit"):
        checks.append(_check("warning", "missing_commit_hash", "Current commit hash is unavailable."))
    if git.get("dirty_tree_count"):
        checks.append(_check("blocker", "dirty_tree_for_release", "Dirty tree should be resolved or intentionally documented before release."))
    if not _lockfile_status(root)["present"]:
        checks.append(_check("warning", "missing_lockfile", "No uv/poetry/pip-tools lockfile detected."))
    if evidence["paper_eligible_runs"] == 0:
        checks.append(_check("blocker", "no_eligible_runs", "No paper-eligible runs are available."))
    if not evidence["provider_evidence_present"]:
        checks.append(_check("blocker", "no_provider_evidence", "No provider-backed evidence is available for empirical paper readiness."))
    return checks


def _check(severity: str, check_id: str, message: str) -> dict[str, str]:
    return {"severity": severity, "id": check_id, "message": message}


def _read_pyproject(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError:
        return {}


def _dataset_versions(root: Path) -> list[dict[str, Any]]:
    rows = []
    for path in discover_benchmark_dirs(root):
        path = path.resolve()
        split = _read_json(path / "splits.json") or {}
        generation = _read_json(path / "generation_report.json") or {}
        freeze = _read_json(path / "freeze_manifest.json") or {}
        rows.append(
            {
                "path": _rel(path, root),
                "benchmark_version": split.get("benchmark_version") or generation.get("benchmark_version") or freeze.get("benchmark_version") or path.name,
                "generation_seed": split.get("seed") or generation.get("seed") or freeze.get("seed"),
                "has_splits": bool(split),
                "has_freeze_manifest": bool(freeze),
            }
        )
    return rows


def _provider_status(root: Path) -> dict[str, Any]:
    preflight = _read_json(root / "reports/provider_pilot_preflight.json") or {}
    verdicts_raw = preflight.get("verdicts")
    verdicts = verdicts_raw if isinstance(verdicts_raw, dict) else {}
    return {
        "preflight_report_present": bool(preflight),
        "ready_for_dry_run": bool(verdicts.get("ready_for_dry_run")),
        "ready_for_live_provider_run": bool(verdicts.get("ready_for_live_provider_run")),
    }


def _claim_state(root: Path) -> dict[str, Any]:
    payload = _read_json(root / "docs/claim_ledger.json") or _read_json(root / "reports/claim_evidence_matrix.json") or {}
    claims_raw = payload.get("claims")
    claims = claims_raw if isinstance(claims_raw, list) else []
    statuses = {str(row.get("claim_id")): str(row.get("status")) for row in claims if isinstance(row, dict)}
    return {
        "C1_C8": {f"C{i}": statuses.get(f"C{i}", "planned") for i in range(1, 9)},
        "C9": statuses.get("C9", "engineering_only"),
        "C10": statuses.get("C10", "planned"),
        "empirical_claims_supported": all(statuses.get(f"C{i}") == "supported" for i in range(1, 9)) and statuses.get("C10") == "supported",
    }


def _report_timestamps(reports: Path) -> list[dict[str, Any]]:
    if not reports.exists():
        return []
    rows = []
    for path in sorted(reports.glob("**/*.json")):
        payload = _read_json(path) or {}
        rows.append({"path": str(path), "generated_at": payload.get("generated_at")})
    return rows[:200]


def _lockfile_status(root: Path) -> dict[str, Any]:
    names = ("uv.lock", "poetry.lock", "Pipfile.lock", "requirements.lock")
    found = [name for name in names if (root / name).exists()]
    return {"present": bool(found), "files": found}


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)
