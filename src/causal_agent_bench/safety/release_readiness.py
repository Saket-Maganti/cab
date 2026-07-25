"""No-run release readiness report."""

from __future__ import annotations

import json
import subprocess
import tomllib
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from causal_agent_bench.safety.common import (
    classify_run_entry,
    load_run_index_entries,
    section_markdown,
    write_dual_report,
)


def build_release_readiness_report(
    repo_root: str | Path,
    *,
    output_dir: str | Path = "reports/release_readiness",
    results_root: str | Path = "results",
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    out = Path(output_dir)
    if not out.is_absolute():
        out = root / out
    checks: list[dict[str, Any]] = []
    pyproject = _load_pyproject(root / "pyproject.toml")
    _check_file(checks, root, "pyproject.toml", "blocker_before_public_release", "pyproject presence")
    _check_python_version(checks, pyproject)
    if not (root / ".python-version").exists():
        _add(checks, "warning", ".python-version missing", "Pinning a local Python version improves reproducibility.")
    if not _has_lockfile(root):
        _add(checks, "warning", "lockfile missing", "No uv/poetry/pip-tools lockfile detected.")
    _check_readme_setup(checks, root)
    _check_required_docs(checks, root)
    _check_release_files(checks, root)
    _check_provider_template(checks, root)
    _check_dataset_splits(checks, root)
    paper_assets = _read_json(out / "paper_asset_eligibility.json") or _read_json(root / "reports/paper_asset_eligibility.json") or {}
    eligible_assets = int(paper_assets.get("eligible_count") or 0)
    if not paper_assets:
        _add(checks, "warning", "paper asset eligibility report missing", "Run validate-paper-assets in a no-run lane.")
    runs = [classify_run_entry(entry, root) for entry in load_run_index_entries(root, results_root=results_root)]
    eligible_runs = [run for run in runs if run["paper_eligible"]]
    if not eligible_runs:
        _add(
            checks,
            "blocker_before_empirical_claims",
            "no eligible runs",
            "No paper-eligible provider/main runs are indexed.",
        )
    if eligible_assets == 0:
        _add(
            checks,
            "blocker_before_empirical_claims",
            "no eligible paper assets",
            "No eligible paper assets are currently available.",
        )
    claim_state = _claim_state(root)
    if not claim_state["empirical_claims_supported"]:
        _add(
            checks,
            "blocker_before_empirical_claims",
            "empirical claims unsupported",
            "C1-C8/C10 are not supported by strict claim-evidence gates.",
        )
    dirty = _git_dirty(root)
    if dirty:
        _add(checks, "warning", "dirty git tree", "Public release should be cut from an intentional clean state.")
    summary = {
        "check_count": len(checks),
        "by_severity": dict(Counter(item["severity"] for item in checks)),
        "indexed_runs": len(runs),
        "paper_eligible_run_count": len(eligible_runs),
        "eligible_asset_count": eligible_assets,
        "claim_state": claim_state,
        "git_dirty": dirty,
    }
    verdicts = {
        "ready_for_internal_advisor_review": _has_docs_for_advisor(root),
        "ready_for_provider_pilot": False,
        "ready_for_public_release": not any(
            item["severity"] == "blocker_before_public_release" for item in checks
        )
        and not dirty
        and _has_lockfile(root),
        "ready_for_empirical_paper_submission": bool(eligible_runs)
        and eligible_assets > 0
        and claim_state["empirical_claims_supported"]
        and not any(item["severity"].startswith("blocker") for item in checks),
    }
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": "Static release readiness inspection only; no paper build, benchmark run, provider call, or model call.",
        "summary": summary,
        "verdicts": verdicts,
        "checks": checks,
    }
    md = release_readiness_markdown(payload)
    md_path, json_path = write_dual_report(
        stem="release_readiness_report",
        payload=payload,
        markdown=md,
        output_dir=out,
    )
    payload["report_paths"] = {"markdown": str(md_path), "json": str(json_path)}
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def release_readiness_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    verdicts = payload["verdicts"]
    lines = [
        "# Release Readiness Report",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        payload["scope"],
        "",
        section_markdown(
            "Verdicts",
            [
                f"- Ready for internal advisor review: `{verdicts['ready_for_internal_advisor_review']}`",
                f"- Ready for provider pilot execution: `{verdicts['ready_for_provider_pilot']}`",
                f"- Ready for public release: `{verdicts['ready_for_public_release']}`",
                f"- Ready for empirical paper submission: `{verdicts['ready_for_empirical_paper_submission']}`",
            ],
        ),
        section_markdown(
            "Summary",
            [
                f"- Indexed runs: {summary['indexed_runs']}",
                f"- Paper-eligible runs: {summary['paper_eligible_run_count']}",
                f"- Eligible paper assets: {summary['eligible_asset_count']}",
                f"- Git dirty: `{summary['git_dirty']}`",
                f"- Check severities: {summary['by_severity']}",
            ],
        ),
        "## Checks",
        "",
    ]
    for check in payload["checks"]:
        lines.append(f"- `{check['severity']}` {check['name']}: {check['message']}")
    lines.extend(
        [
            "",
            "## Reproduction Paths",
            "",
            "### Static-only (no models, no spend)",
            "",
            "```bash",
            "make fast-check",
            "python3 scripts/check_evidence_safety.py",
            "python3 -m causal_agent_bench all-no-run-reports --output-dir /tmp/cab_release_check",
            "python3 scripts/reproduce_artifact.py --all-deterministic",
            "```",
            "",
            "### Provider-required (after advisor + APPROVED config)",
            "",
            "```bash",
            "python3 -m causal_agent_bench validate-config --config configs/provider_pilot_tiny_APPROVED.yaml",
            "python3 -m causal_agent_bench plan-run --config configs/provider_pilot_tiny_APPROVED.yaml",
            "python3 -m causal_agent_bench estimate-run-cost --config configs/provider_pilot_tiny_APPROVED.yaml",
            "# Live run only with explicit approval:",
            "# python3 -m causal_agent_bench run --config configs/provider_pilot_tiny_APPROVED.yaml",
            "```",
            "",
            "## Reviewer Artifact Instructions",
            "",
            "- Start with `artifact/README.md` and `docs/QUICKSTART.md`.",
            "- Use `handoff/ADVISOR_REVIEW_BUNDLE_INDEX.md` for advisor-facing navigation.",
            "- Treat `reports/` and `all-no-run-reports` output as governance aids, not empirical results.",
            "",
            "## Artifact Evaluation Checklist",
            "",
            "- [ ] Deterministic reproduction path runs without API keys",
            "- [ ] Claim ledger shows C1–C8/C10 not supported",
            "- [ ] No paper-eligible runs mislabeled in README",
            "- [ ] Provider template not runnable without APPROVED copy",
            "",
            "## Public Release Blockers",
            "",
            "- Empirical claims unsupported (by design at current stage)",
            "- Dirty git tree and/or missing lockfile",
            "- Leakage repair clusters may remain",
            "- No frozen public release tag with reviewed dataset",
            "",
        ]
    )
    return "\n".join(lines)


def _add(checks: list[dict[str, Any]], severity: str, name: str, message: str) -> None:
    checks.append({"severity": severity, "name": name, "message": message})


def _check_file(
    checks: list[dict[str, Any]],
    root: Path,
    rel: str,
    severity: str,
    label: str,
) -> None:
    if (root / rel).exists():
        _add(checks, "informational", label, f"{rel} present.")
    else:
        _add(checks, severity, label, f"{rel} missing.")


def _load_pyproject(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError:
        return {}


def _check_python_version(checks: list[dict[str, Any]], pyproject: dict[str, Any]) -> None:
    requires = (pyproject.get("project") or {}).get("requires-python")
    if requires:
        _add(checks, "informational", "Python requirement", f"requires-python is {requires}.")
    else:
        _add(checks, "blocker_before_public_release", "Python requirement missing", "pyproject lacks requires-python.")


def _has_lockfile(root: Path) -> bool:
    return any((root / name).exists() for name in ("uv.lock", "poetry.lock", "Pipfile.lock", "requirements.lock"))


def _check_readme_setup(checks: list[dict[str, Any]], root: Path) -> None:
    readme = root / "README.md"
    if not readme.exists():
        _add(checks, "blocker_before_public_release", "README missing", "README.md is missing.")
        return
    text = readme.read_text(encoding="utf-8", errors="replace").lower()
    if "pip install" in text or "python -m" in text:
        _add(checks, "informational", "README setup commands", "README includes setup/run commands.")
    else:
        _add(checks, "warning", "README setup commands missing", "README does not appear to include setup commands.")


def _check_required_docs(checks: list[dict[str, Any]], root: Path) -> None:
    required = {
        "docs/NO_RUN_VALIDATION.md": "no-run validation docs",
        "docs/PROVIDER_PILOT_READINESS_PACKET.md": "provider pilot docs",
        "docs/REPRODUCIBILITY.md": "reproducibility docs",
        "docs/SECURITY_AND_PRIVACY.md": "security/privacy docs",
        "docs/DO_NOT_OVERCLAIM.md": "overclaiming policy",
        "docs/claim_ledger.json": "claim ledger",
        "paper/EVIDENCE_GAP_MAP.md": "evidence gap map",
    }
    for rel, label in required.items():
        severity = "blocker_before_empirical_claims" if rel.startswith("paper/") or "claim" in rel else "warning"
        _check_file(checks, root, rel, severity, label)
    pyproject = _load_pyproject(root / "pyproject.toml")
    markers = set((pyproject.get("tool") or {}).get("pytest", {}).get("ini_options", {}).get("markers", []))
    marker_text = "\n".join(markers)
    if "integration" in marker_text and "local_run" in marker_text:
        _add(checks, "informational", "unsafe test markers", "integration/local_run markers are registered.")
    else:
        _add(checks, "warning", "unsafe test markers missing", "integration/local_run pytest markers were not found.")


def _check_release_files(checks: list[dict[str, Any]], root: Path) -> None:
    if not ((root / "LICENSE").exists() or (root / "LICENSE.md").exists()):
        _add(checks, "blocker_before_public_release", "license file missing", "No top-level LICENSE file detected.")
    else:
        _add(checks, "informational", "license file", "License file present.")
    if not (root / "DATA_LICENSE.md").exists():
        _add(checks, "warning", "data license missing", "DATA_LICENSE.md missing.")
    else:
        _add(checks, "informational", "data license", "DATA_LICENSE.md present.")
    _check_file(checks, root, "CITATION.cff", "warning", "citation metadata")


def _check_provider_template(checks: list[dict[str, Any]], root: Path) -> None:
    path = root / "configs/provider_pilot_tiny_template.yaml"
    if not path.exists():
        _add(checks, "blocker_before_public_release", "provider template missing", "Provider pilot template missing.")
        return
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if raw.get("allow_paid_calls") is False:
        _add(checks, "informational", "provider template safety", "allow_paid_calls=false in provider template.")
    else:
        _add(checks, "blocker_before_public_release", "provider template unsafe", "Provider template must keep allow_paid_calls=false.")
    if (root / "configs/provider_pilot_oracle_sanity_check_template.yaml").exists():
        _add(checks, "informational", "oracle/provider separation", "Oracle sanity template is separate from provider pilot template.")
    else:
        _add(checks, "warning", "oracle/provider separation", "Oracle sanity template not detected.")


def _check_dataset_splits(checks: list[dict[str, Any]], root: Path) -> None:
    frozen = root / "data/frozen"
    if not frozen.exists():
        _add(checks, "warning", "frozen dataset missing", "No data/frozen directory detected.")
        return
    split_files = list(frozen.glob("*/splits.json"))
    if split_files:
        _add(checks, "informational", "frozen split metadata", f"{len(split_files)} frozen split file(s) detected.")
    else:
        _add(checks, "warning", "frozen split metadata missing", "No frozen splits.json detected.")


def _claim_state(root: Path) -> dict[str, Any]:
    ledger = _read_json(root / "docs/claim_ledger.json") or {}
    claims_raw = ledger.get("claims")
    claims = claims_raw if isinstance(claims_raw, list) else []
    statuses = {str(claim.get("claim_id")): str(claim.get("status", "planned")) for claim in claims if isinstance(claim, dict)}
    empirical_ids = [f"C{i}" for i in range(1, 9)] + ["C10"]
    empirical_supported = all(statuses.get(claim_id) == "supported" for claim_id in empirical_ids)
    return {
        "statuses": statuses,
        "empirical_claims_supported": empirical_supported,
        "C1_C8": {claim_id: statuses.get(claim_id, "planned") for claim_id in empirical_ids[:-1]},
        "C9": statuses.get("C9", "unknown"),
        "C10": statuses.get("C10", "planned"),
    }


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def _git_dirty(root: Path) -> bool:
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return True
    return bool(result.stdout.strip())


def _has_docs_for_advisor(root: Path) -> bool:
    return all(
        (root / rel).exists()
        for rel in (
            "docs/NO_RUN_VALIDATION.md",
            "docs/PROVIDER_PILOT_READINESS_PACKET.md",
            "docs/DO_NOT_OVERCLAIM.md",
            "reports/run_health_report.json",
            "reports/claim_evidence_matrix.json",
        )
    )
