"""Fail-closed held-out/public-release policy validation."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from causal_agent_bench.safety.split_registry import (
    CANONICAL_SPLIT_REGISTRY_PATH,
)

DEFAULT_POLICY_PATH = Path("configs/cab_heldout_release_policy.json")
REQUIRED_RELEASE_TIERS = frozenset(
    {
        "development_release",
        "harness_only_release",
        "hidden_or_delayed_test_pack",
        "post_study_full_release",
    }
)


def validate_heldout_release_policy(
    repo_root: str | Path,
    *,
    policy_path: str | Path = DEFAULT_POLICY_PATH,
    registry_path: str | Path = CANONICAL_SPLIT_REGISTRY_PATH,
    release_manifest_path: str | Path = "release/release_manifest.json",
) -> dict[str, Any]:
    """Validate that protected task payloads remain outside public inventory."""

    root = Path(repo_root).resolve()
    policy_file = _resolve(root, policy_path)
    registry_file = _resolve(root, registry_path)
    manifest_file = _resolve(root, release_manifest_path)
    issues: list[dict[str, Any]] = []
    policy = _read_json(policy_file, issues, "release_policy_invalid")
    registry = _read_json(registry_file, issues, "split_registry_invalid")
    manifest = _read_json(
        manifest_file,
        issues,
        "release_manifest_invalid",
        required=False,
    )

    tiers = policy.get("release_tiers")
    tier_names = set(tiers) if isinstance(tiers, dict) else set()
    missing_tiers = sorted(REQUIRED_RELEASE_TIERS - tier_names)
    if missing_tiers:
        issues.append(
            _issue(
                policy_file,
                root,
                "release_tiers",
                "blocker",
                "release_tiers_missing",
                f"missing={missing_tiers}",
                "Define all four required public-release tiers.",
            )
        )
    if policy.get("current_state") != "PRE_EXECUTION_HIDDEN":
        issues.append(
            _issue(
                policy_file,
                root,
                "current_state",
                "blocker",
                "heldout_state_not_fail_closed",
                f"actual={policy.get('current_state')!r}",
                "Keep the state PRE_EXECUTION_HIDDEN until post-study approval.",
            )
        )
    if policy.get("full_release_unlocked") is not False:
        issues.append(
            _issue(
                policy_file,
                root,
                "full_release_unlocked",
                "blocker",
                "premature_full_release_unlock",
                f"actual={policy.get('full_release_unlocked')!r}",
                "Set full_release_unlocked=false before confirmatory execution.",
            )
        )
    approvals = policy.get("approval_records")
    if approvals not in ([], None):
        issues.append(
            _issue(
                policy_file,
                root,
                "approval_records",
                "blocker",
                "pre_execution_release_approval_present",
                "approval records must remain empty before execution",
                "Remove placeholder or premature approval records.",
            )
        )
    prerequisites = policy.get("unlock_prerequisites")
    if not isinstance(prerequisites, list) or len(prerequisites) < 5:
        issues.append(
            _issue(
                policy_file,
                root,
                "unlock_prerequisites",
                "blocker",
                "release_unlock_prerequisites_incomplete",
                "at least five independent prerequisites are required",
                "Define execution, integrity, human review, evidence, and release approvals.",
            )
        )

    protected_roles = policy.get("protected_roles")
    protected_roles = (
        protected_roles if isinstance(protected_roles, dict) else {}
    )
    registry_roles = {
        str(row.get("role")): row
        for row in registry.get("roles", [])
        if isinstance(row, dict) and row.get("role")
    }
    for role, expected_tier in protected_roles.items():
        row = registry_roles.get(str(role))
        if row is None:
            issues.append(
                _issue(
                    registry_file,
                    root,
                    "roles",
                    "blocker",
                    "protected_role_missing",
                    str(role),
                    "Add every protected role to the canonical split registry.",
                )
            )
            continue
        if row.get("release_tier") != expected_tier:
            issues.append(
                _issue(
                    registry_file,
                    root,
                    f"roles.{role}.release_tier",
                    "blocker",
                    "protected_role_release_tier_mismatch",
                    (
                        f"expected={expected_tier!r} "
                        f"actual={row.get('release_tier')!r}"
                    ),
                    "Keep the live role in the hidden/delayed tier.",
                )
            )

    allowed_public = {
        str(value)
        for value in policy.get("allowed_public_metadata", [])
        if isinstance(value, str)
    }
    protected_patterns = [
        str(value)
        for value in policy.get("protected_payload_globs", [])
        if isinstance(value, str)
    ]
    tracked_protected = sorted(
        path
        for path in _tracked_files(root, protected_patterns)
        if path not in allowed_public
    )
    for path in tracked_protected:
        issues.append(
            _issue(
                root / path,
                root,
                "git_index",
                "blocker",
                "protected_payload_git_tracked",
                path,
                "Remove protected prompt/answer payloads from public version control.",
            )
        )

    inventory = _release_inventory(manifest)
    protected_inventory = sorted(
        path
        for path in inventory
        if _matches_any(root, path, protected_patterns)
        and path not in allowed_public
    )
    for path in protected_inventory:
        issues.append(
            _issue(
                manifest_file,
                root,
                "release_inventory",
                "blocker",
                "protected_payload_in_release_manifest",
                path,
                "Remove protected task payloads from the pre-execution release bundle.",
            )
        )

    blockers = [
        issue for issue in issues if issue["severity"] in {"blocker", "error"}
    ]
    return {
        "scope": (
            "Static public-release inventory and policy validation only. "
            "No release is created and no protected data is moved."
        ),
        "evidence_class": "ENGINEERING_ONLY",
        "policy_path": _relative(policy_file, root),
        "registry_path": _relative(registry_file, root),
        "current_state": policy.get("current_state"),
        "full_release_unlocked": policy.get("full_release_unlocked"),
        "required_release_tiers_present": not missing_tiers,
        "protected_role_count": len(protected_roles),
        "tracked_protected_payload_count": len(tracked_protected),
        "release_manifest_protected_payload_count": len(protected_inventory),
        "post_study_full_release_allowed": False,
        "passed": not blockers,
        "issues": issues,
    }


def _tracked_files(root: Path, patterns: list[str]) -> set[str]:
    if not patterns:
        return set()
    result = subprocess.run(
        ["git", "ls-files", "--", *patterns],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return set()
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def _release_inventory(manifest: dict[str, Any]) -> set[str]:
    output: set[str] = set()
    for field in (
        "cards",
        "docs",
        "configs",
        "scripts",
        "source_packages",
    ):
        values = manifest.get(field, [])
        if isinstance(values, list):
            output.update(str(value) for value in values)
    for field in ("license_file", "default_frozen_manifest"):
        value = manifest.get(field)
        if value:
            output.add(str(value))
    return output


def _matches_any(root: Path, path: str, patterns: list[str]) -> bool:
    candidate = Path(path)
    for pattern in patterns:
        if candidate.match(pattern):
            return True
        if (root / candidate).match(str(root / pattern)):
            return True
    return False


def _read_json(
    path: Path,
    issues: list[dict[str, Any]],
    code: str,
    *,
    required: bool = True,
) -> dict[str, Any]:
    if not path.exists():
        if required:
            issues.append(
                {
                    "file": str(path),
                    "field": "file",
                    "severity": "blocker",
                    "code": code,
                    "detail": "file missing",
                    "suggested_repair": "Create the required machine-readable policy file.",
                    "automatic_repair_status": "not_attempted",
                    "unresolved_human_review_state": False,
                }
            )
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        issues.append(
            {
                "file": str(path),
                "field": "json",
                "severity": "blocker",
                "code": code,
                "detail": str(exc),
                "suggested_repair": "Repair the invalid JSON.",
                "automatic_repair_status": "not_attempted",
                "unresolved_human_review_state": False,
            }
        )
        return {}
    return value if isinstance(value, dict) else {}


def _issue(
    path: Path,
    root: Path,
    field: str,
    severity: str,
    code: str,
    detail: str,
    suggested_repair: str,
) -> dict[str, Any]:
    return {
        "file": _relative(path, root),
        "field": field,
        "severity": severity,
        "code": code,
        "detail": detail,
        "suggested_repair": suggested_repair,
        "automatic_repair_status": "not_attempted",
        "unresolved_human_review_state": False,
    }


def _resolve(root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def _relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return str(path)


__all__ = [
    "DEFAULT_POLICY_PATH",
    "REQUIRED_RELEASE_TIERS",
    "validate_heldout_release_policy",
]
