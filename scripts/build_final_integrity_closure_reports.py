#!/usr/bin/env python3
"""Reports for the final integrity-closure pass over the reviewer workflow.

Three modes, each idempotent and provider-free:

``baseline``
    The repository state and the scientific-kernel preservation baseline, taken
    *before* the repair so that every preserved surface can be compared after it.
``preservation``
    The same kernel surfaces, recomputed, plus a per-surface comparison against
    the baseline.  Any drift is reported as a failure, never absorbed.
``final``
    The closure report and the full-validation record, assembled from the
    artifacts the other phases produced.

Nothing here reads a private body: the kernel is compared by hash alone, and the
private packet contributes only file digests of already-sealed archives.
"""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/final_integrity_closure"
V2_REPORTS = ROOT / "reports/reviewer_ready_v2"
PRIVATE_ROOT = ROOT / "private_data/human_review/compact20-review-ready-v2"

#: The commit this repair started from, recorded so the baseline is anchored.
STARTING_COMMIT = "131cd10abe519a7174171bb47e90347326862ca4"


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, check=False, capture_output=True, text=True
    )
    return result.stdout.strip()


def _sha256_file(path: Path) -> str | None:
    import hashlib

    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha256_json(value: Any) -> str:
    import hashlib

    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode()).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


# --------------------------------------------------------------------------
# scientific kernel preservation
# --------------------------------------------------------------------------


def scientific_kernel_surfaces() -> dict[str, Any]:
    """Every scientific surface this repair is forbidden to change.

    Values are hashes of already-public commitments and of sealed private
    archives.  No private body, key or answer is read.
    """

    commitment = _read_json(V2_REPORTS / "PUBLIC_PACKET_COMMITMENT.json")
    freeze = _read_json(V2_REPORTS / "SCIENTIFIC_FREEZE_V2.json")
    vault = _read_json(V2_REPORTS / "STAGE2_VAULT_STATUS.json")
    pair_hashes = dict(commitment["pair_content_hashes"])
    return {
        "schema_version": "cab_scientific_kernel_preservation_v1",
        "packet_version": commitment["packet_version"],
        "pair_count": commitment["pair_count"],
        "active_pair_content_digest": _sha256_json(pair_hashes),
        "pair_content_hashes": pair_hashes,
        "stage1_package_hashes": dict(freeze["stage1_package_hashes"]),
        "stage1_reviewer_a_archive_sha256": _sha256_file(
            PRIVATE_ROOT / "stage1/stage1_reviewer_a.zip"
        ),
        "stage1_reviewer_b_archive_sha256": _sha256_file(
            PRIVATE_ROOT / "stage1/stage1_reviewer_b.zip"
        ),
        "qualification_version": commitment["qualification_version"],
        "qualification_package_hashes": dict(commitment["qualification_package_hashes"]),
        "qualification_commitment_sha256": freeze["qualification_commitment_sha256"],
        "qualification_commitment": commitment["qualification_commitment"],
        "encrypted_qualification_vault_sha256": _sha256_file(
            PRIVATE_ROOT / "qualification_v4/qualification_key.enc"
        ),
        "stage2_encrypted_vault_sha256": vault["vault_sha256"],
        "stage2_vault_file_sha256": _sha256_file(PRIVATE_ROOT / "stage2/stage2_vault.enc"),
        "public_packet_commitment_sha256": commitment["commitment_sha256"],
        "seed_commitment": commitment["seed_commitment"],
        "distinct_semantic_objectives": commitment["distinct_semantic_objectives"],
        "family_counts": dict(commitment["family_counts"]),
        "domain_counts": dict(commitment["domain_counts"]),
        "difficulty_counts": dict(commitment["difficulty_counts"]),
        "scientific_freeze_sha256": freeze["freeze_sha256"],
    }


#: Surfaces that must be byte-identical before and after the repair.  The freeze
#: hash is deliberately absent: refreshing it is the *point* of Phase 12, and it
#: is compared separately as an expected change.
_PRESERVED_KEYS = (
    "packet_version",
    "pair_count",
    "active_pair_content_digest",
    "pair_content_hashes",
    "stage1_package_hashes",
    "stage1_reviewer_a_archive_sha256",
    "stage1_reviewer_b_archive_sha256",
    "qualification_version",
    "qualification_package_hashes",
    "qualification_commitment_sha256",
    "qualification_commitment",
    "encrypted_qualification_vault_sha256",
    "stage2_encrypted_vault_sha256",
    "stage2_vault_file_sha256",
    "public_packet_commitment_sha256",
    "seed_commitment",
    "distinct_semantic_objectives",
    "family_counts",
    "domain_counts",
    "difficulty_counts",
)


def compare_preservation(baseline: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    comparisons = {
        key: {
            "unchanged": baseline.get(key) == current.get(key),
            "baseline_digest": _sha256_json(baseline.get(key)),
            "current_digest": _sha256_json(current.get(key)),
        }
        for key in _PRESERVED_KEYS
    }
    drifted = sorted(key for key, row in comparisons.items() if not row["unchanged"])
    return {
        "schema_version": "cab_scientific_kernel_preservation_comparison_v1",
        "compared_surfaces": list(_PRESERVED_KEYS),
        "comparisons": comparisons,
        "drifted_surfaces": drifted,
        "scientific_kernel_preserved": not drifted,
        "scientific_freeze_expected_to_change": True,
        "baseline_scientific_freeze_sha256": baseline.get("scientific_freeze_sha256"),
        "current_scientific_freeze_sha256": current.get("scientific_freeze_sha256"),
    }


# --------------------------------------------------------------------------
# baseline
# --------------------------------------------------------------------------


def repository_state() -> dict[str, Any]:
    from causal_agent_bench.review_ready_v2 import PACKET_VERSION

    head = _git("rev-parse", "HEAD")
    status = [line for line in _git("status", "--porcelain").splitlines() if line.strip()]
    active_paths = _read_json(V2_REPORTS / "ACTIVE_PATH_REGISTRY.json")
    freeze = _read_json(V2_REPORTS / "SCIENTIFIC_FREEZE_V2.json")
    return {
        "schema_version": "cab_final_integrity_closure_baseline_v1",
        "recorded_at": datetime.now(UTC).isoformat(),
        "repository_root": str(ROOT),
        "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "head_commit": head,
        "starting_commit": STARTING_COMMIT,
        "starting_commit_is_ancestor_or_head": subprocess.run(
            ["git", "merge-base", "--is-ancestor", STARTING_COMMIT, "HEAD"],
            cwd=ROOT,
            check=False,
            capture_output=True,
        ).returncode
        == 0,
        "origin_url": _git("remote", "get-url", "origin"),
        "origin_main": _git("rev-parse", "origin/main"),
        "ahead_behind": _git("rev-list", "--left-right", "--count", "HEAD...origin/main"),
        "dirty_files": [line[3:] for line in status if not line.startswith("??")],
        "untracked_files": [line[3:] for line in status if line.startswith("??")],
        "submodules": [line for line in _git("submodule", "status").splitlines() if line.strip()],
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "active_packet_version": PACKET_VERSION,
        "workflow_schema_version": _workflow_schema_version(),
        "qualification_schema_version": active_paths["active_qualification_version"],
        "review_form_schema_version": active_paths["active_review_form_schema"],
        "receipt_schema_versions": _receipt_schema_versions(),
        "scientific_freeze_sha256": freeze["freeze_sha256"],
        "public_packet_commitment_sha256": freeze["packet_commitment_sha256"],
        "active_path_registry": active_paths,
        "active_status_documents": sorted(
            path
            for path in ("CURRENT_PROJECT_STATE.md", "MASTER_STATUS.md", "PROJECT_STATUS.md")
            if (ROOT / path).is_file()
        ),
        "private_surfaces_present": sorted(
            str(path.relative_to(ROOT))
            for path in sorted(PRIVATE_ROOT.rglob("*"))
            if path.is_file()
        )
        if PRIVATE_ROOT.is_dir()
        else [],
        "private_surfaces_tracked_in_git": [
            line for line in _git("ls-files", "private_data").splitlines() if line.strip()
        ],
    }


def _workflow_schema_version() -> str:
    from causal_agent_bench.review_ready_v2.workflow import WORKFLOW_SCHEMA_VERSION

    return WORKFLOW_SCHEMA_VERSION


def _receipt_schema_versions() -> dict[str, str]:
    from causal_agent_bench.review_ready_v2.receipts import (
        FIXTURE_RECEIPT_SCHEMA,
        PRODUCTION_RECEIPT_SCHEMA,
    )

    return {"production": PRODUCTION_RECEIPT_SCHEMA, "fixture": FIXTURE_RECEIPT_SCHEMA}


def _baseline_markdown(state: dict[str, Any], kernel: dict[str, Any]) -> str:
    lines = [
        "# CAB final integrity closure — baseline repository state",
        "",
        f"Recorded at `{state['recorded_at']}`.",
        "",
        "This is the authoritative pre-repair snapshot.  Every scientific-kernel",
        "surface listed below is compared again after the repair; drift is a",
        "failure, not a result.",
        "",
        "## Repository",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| branch | `{state['branch']}` |",
        f"| HEAD | `{state['head_commit']}` |",
        f"| starting commit | `{state['starting_commit']}` |",
        f"| starting commit is ancestor or HEAD | {state['starting_commit_is_ancestor_or_head']} |",
        f"| origin | `{state['origin_url']}` |",
        f"| origin/main | `{state['origin_main']}` |",
        f"| ahead/behind (HEAD...origin/main) | `{state['ahead_behind']}` |",
        f"| dirty files | {len(state['dirty_files'])} |",
        f"| untracked files | {len(state['untracked_files'])} |",
        f"| Python | `{state['python_version']}` |",
        "",
        "## Active schema surface",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| packet version | `{state['active_packet_version']}` |",
        f"| workflow schema | `{state['workflow_schema_version']}` |",
        f"| qualification schema | `{state['qualification_schema_version']}` |",
        f"| review form schema | `{state['review_form_schema_version']}` |",
        f"| production receipt schema | `{state['receipt_schema_versions']['production']}` |",
        f"| fixture receipt schema | `{state['receipt_schema_versions']['fixture']}` |",
        f"| scientific freeze | `{state['scientific_freeze_sha256']}` |",
        f"| public packet commitment | `{state['public_packet_commitment_sha256']}` |",
        "",
        "## Scientific kernel preservation baseline",
        "",
        "| surface | digest |",
        "| --- | --- |",
    ]
    for key in _PRESERVED_KEYS:
        lines.append(f"| `{key}` | `{_sha256_json(kernel.get(key))}` |")
    lines += [
        "",
        "## Private material",
        "",
        f"- private packet files present on disk: {len(state['private_surfaces_present'])}",
        f"- private files tracked in Git: {len(state['private_surfaces_tracked_in_git'])} "
        "(expected: 0)",
        "",
        "No private body, key, answer or reviewer identity appears in this report.",
        "",
    ]
    return "\n".join(lines)


def cmd_baseline() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    state = repository_state()
    kernel = scientific_kernel_surfaces()
    _write_json(OUT / "BASELINE_REPOSITORY_STATE.json", state)
    _write_json(OUT / "SCIENTIFIC_KERNEL_PRESERVATION_BASELINE.json", kernel)
    (OUT / "BASELINE_REPOSITORY_STATE.md").write_text(_baseline_markdown(state, kernel))
    print(f"baseline written for {state['head_commit']}")
    if state["private_surfaces_tracked_in_git"]:
        print("REFUSING: private material is tracked in Git", file=sys.stderr)
        return 1
    return 0


def cmd_preservation() -> int:
    baseline = _read_json(OUT / "SCIENTIFIC_KERNEL_PRESERVATION_BASELINE.json")
    current = scientific_kernel_surfaces()
    comparison = compare_preservation(baseline, current)
    _write_json(
        OUT / "SCIENTIFIC_KERNEL_PRESERVATION_FINAL.json",
        {**current, "comparison_against_baseline": comparison},
    )
    for key in comparison["drifted_surfaces"]:
        print(f"DRIFT: {key}", file=sys.stderr)
    print(
        "scientific kernel preserved"
        if comparison["scientific_kernel_preserved"]
        else "SCIENTIFIC KERNEL DRIFTED"
    )
    return 0 if comparison["scientific_kernel_preserved"] else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("baseline", "preservation"))
    args = parser.parse_args(argv)
    if args.mode == "baseline":
        return cmd_baseline()
    return cmd_preservation()


if __name__ == "__main__":
    raise SystemExit(main())
