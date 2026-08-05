#!/usr/bin/env python3
"""Record the repository baseline the post-human-review chain starts from.

The point of this script is that every later claim in the post-review chain can
be checked against a value that was written down *before* anything changed.  It
records the preserved scientific kernel — the freeze, the packet commitment, the
issued package hashes, the reviewer mappings — so a reader can prove the kernel
survived the import untouched rather than take it on trust.

Key *paths* are recorded as booleans only.  No key value is ever read here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = REPO_ROOT / "reports" / "post_human_review"
REVIEWER_REPORTS = REPO_ROOT / "reports" / "reviewer_ready_v2"

SCHEMA_VERSION = "cab_post_human_review_baseline_v1"

#: External key environment variables.  Recorded as configured/not configured.
KEY_ENV_VARS = (
    "CAB_COORDINATOR_KEY_PATH",
    "CAB_QUALIFICATION_KEY_PATH",
    "CAB_STAGE2_KEY_PATH",
)


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=False
    )
    return result.stdout.strip()


def sha256_file(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def _repository() -> dict[str, Any]:
    head = git("rev-parse", "HEAD")
    origin = git("rev-parse", "origin/main")
    porcelain = git("status", "--porcelain")
    return {
        "toplevel": git("rev-parse", "--show-toplevel"),
        "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
        "head": head,
        "origin_main": origin,
        "head_equals_origin_main": head == origin and bool(head),
        "remote": git("remote", "get-url", "origin"),
        "tracked_worktree_clean": git("status", "--porcelain", "--untracked-files=no") == "",
        "untracked_top_level_paths": sorted(
            {line[3:].split("/")[0] for line in porcelain.splitlines() if line.startswith("??")}
        ),
        "recent_commits": git("log", "-10", "--oneline").splitlines(),
        "worktrees": git("worktree", "list").splitlines(),
    }


def _environment() -> dict[str, Any]:
    usage = shutil.disk_usage(REPO_ROOT)
    return {
        "python_version": platform.python_version(),
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor_count": os.cpu_count(),
        "disk_free_gib": round(usage.free / 2**30, 2),
        "disk_total_gib": round(usage.total / 2**30, 2),
        "repository_size_mib": round(
            sum(p.stat().st_size for p in REPO_ROOT.rglob("*") if p.is_file() and ".git" not in p.parts)
            / 2**20,
            1,
        ),
    }


def _external_keys() -> dict[str, bool]:
    """Whether each key path resolves to a readable file.  Never its content."""

    configured: dict[str, bool] = {}
    for env_var in KEY_ENV_VARS:
        raw = os.environ.get(env_var, "").strip()
        configured[env_var] = bool(raw) and Path(raw).expanduser().is_file()
    return configured


def _preserved_kernel() -> dict[str, Any]:
    """The scientific values that must be identical before and after the import."""

    freeze = json.loads((REVIEWER_REPORTS / "SCIENTIFIC_FREEZE_V2.json").read_text())
    registry = json.loads((REVIEWER_REPORTS / "ACTIVE_PATH_REGISTRY.json").read_text())
    private_root = REPO_ROOT / registry["active_private_root"]
    mappings = private_root / "mappings"
    return {
        "scientific_freeze_sha256": freeze["freeze_sha256"],
        "packet_commitment_sha256": freeze["packet_commitment_sha256"],
        "qualification_commitment_sha256": freeze["qualification_commitment_sha256"],
        "stage1_package_hashes": freeze["stage1_package_hashes"],
        "qualification_package_hashes": freeze["qualification_package_hashes"],
        "stage2_encrypted_vault_sha256": freeze["stage2_encrypted_vault_sha256"],
        "review_schema_version": freeze["review_input_graph_schema_version"],
        "two_stage_workflow_version": freeze["two_stage_workflow_version"],
        "stage1_commitment_schema_version": freeze["stage1_commitment_schema_version"],
        "active_packet_version": registry["active_private_packet_version"],
        "report_file_hashes": {
            name: sha256_file(REVIEWER_REPORTS / name)
            for name in (
                "SCIENTIFIC_FREEZE_V2.json",
                "PUBLIC_PACKET_COMMITMENT.json",
                "ACTIVE_PATH_REGISTRY.json",
                "STAGE2_ACCEPTANCE_POLICY.json",
                "RETIRED_PACKET_REGISTRY.json",
            )
        },
        "reviewer_mapping_hashes": {
            path.name: sha256_file(path) for path in sorted(mappings.glob("*.json"))
        },
        "issued_package_file_hashes": {
            path.name: sha256_file(path)
            for path in sorted((private_root / "stage1").glob("*.zip"))
        },
    }


def build_baseline() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "recorded_at_utc": datetime.now(UTC).isoformat(),
        "repository": _repository(),
        "environment": _environment(),
        "external_keys_configured": _external_keys(),
        "preserved_scientific_kernel": _preserved_kernel(),
        "preservation_rule": (
            "Every value under preserved_scientific_kernel must be byte-identical after the "
            "post-human-review chain completes. A change is a hard blocker, not a migration."
        ),
    }


def _markdown(baseline: dict[str, Any]) -> str:
    repo = baseline["repository"]
    env = baseline["environment"]
    kernel = baseline["preserved_scientific_kernel"]
    lines = [
        "# Post-human-review baseline",
        "",
        f"Recorded at `{baseline['recorded_at_utc']}`.",
        "",
        "## Repository",
        "",
        f"- branch: `{repo['branch']}`",
        f"- HEAD: `{repo['head']}`",
        f"- origin/main: `{repo['origin_main']}`",
        f"- HEAD == origin/main: `{repo['head_equals_origin_main']}`",
        f"- tracked worktree clean: `{repo['tracked_worktree_clean']}`",
        f"- untracked top-level paths: {', '.join(f'`{p}`' for p in repo['untracked_top_level_paths']) or '_none_'}",
        "",
        "## Environment",
        "",
        f"- Python `{env['python_version']}`",
        f"- platform `{env['platform']}` (`{env['machine']}`, {env['processor_count']} cores)",
        f"- disk free {env['disk_free_gib']} GiB of {env['disk_total_gib']} GiB",
        "",
        "## External keys",
        "",
        "Recorded as configured/not configured only. No key value is read.",
        "",
    ]
    lines += [
        f"- `{name}`: `{value}`" for name, value in sorted(baseline["external_keys_configured"].items())
    ]
    lines += [
        "",
        "## Preserved scientific kernel",
        "",
        "These values must be identical after the chain completes.",
        "",
        f"- scientific freeze: `{kernel['scientific_freeze_sha256']}`",
        f"- packet commitment: `{kernel['packet_commitment_sha256']}`",
        f"- qualification commitment: `{kernel['qualification_commitment_sha256']}`",
        f"- Stage-2 encrypted vault: `{kernel['stage2_encrypted_vault_sha256']}`",
        f"- active packet version: `{kernel['active_packet_version']}`",
        "",
        "### Stage-1 package hashes",
        "",
    ]
    lines += [f"- `{role}`: `{value}`" for role, value in sorted(kernel["stage1_package_hashes"].items())]
    lines += ["", "### Reviewer mappings", ""]
    lines += [
        f"- `{name}`: `{value}`" for name, value in sorted(kernel["reviewer_mapping_hashes"].items())
    ]
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        default=str(REPORT_DIR),
        help="where BASELINE.json and BASELINE.md are written",
    )
    args = parser.parse_args()

    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    baseline = build_baseline()
    (output / "BASELINE.json").write_text(json.dumps(baseline, indent=2, sort_keys=True) + "\n")
    (output / "BASELINE.md").write_text(_markdown(baseline))
    print(json.dumps(baseline["repository"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
