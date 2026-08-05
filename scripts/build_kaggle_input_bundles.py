#!/usr/bin/env python3
"""Build deterministic, content-addressed Kaggle input bundles.

The output filename carries the bundle's content hash, but nothing depends on
that: the notebooks find the bundle by inspecting what is inside it, so the user
is free to rename the ZIP or the Kaggle dataset afterwards.  The name is a
convenience for humans, not an interface.

Determinism is the point of the rest.  Members are sorted, timestamps are fixed,
permissions are normalized and compression is fixed, so the same repository state
produces the same bytes.  Every bundle carries a manifest listing each member and
its SHA-256, and a scan refuses to build if anything private would be included.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

BUNDLE_SCHEMA_VERSION = "cab_kaggle_input_bundle_manifest_v1"
MANIFEST_NAME = "CAB_KAGGLE_INPUT_MANIFEST.json"

#: Fixed archive timestamp.  ZIP stores local time with no zone, so any real
#: clock value would make the bytes depend on when the build ran.
FIXED_TIMESTAMP = (1980, 1, 1, 0, 0, 0)

PREEXECUTION = "cpu-preexecution"
COMPACT20_T4X2 = "compact20-t4x2"
POSTRUN_TYPES = (
    "compact20-postrun",
    "scale100-postrun",
    "raac-postrun",
    "naturalistic-postrun",
    "final-analysis",
)

#: Paths that must never enter a bundle, checked by prefix and by name.  This is
#: belt-and-braces: the include lists below already exclude them.
FORBIDDEN_PREFIXES: tuple[str, ...] = (
    ".cab/",
    ".env",
    ".git/",
    "human_review_files/",
    "private_data/",
)

FORBIDDEN_NAME_FRAGMENTS: tuple[str, ...] = (
    "qualification_key",
    "qualification_source",
    "stage2_vault",
    "private_pairs",
    "reviewer_assignments",
    "_mapping.json",
    ".key",
    ".enc",
    "credentials",
    "kaggle.json",
)

#: What the CPU pre-execution bundle carries.  Public commitments and the code
#: needed to re-verify them; no private review material of any kind.
PREEXECUTION_INCLUDES: tuple[str, ...] = (
    "pyproject.toml",
    "constraints.txt",
    "Makefile",
    "src/causal_agent_bench/**/*.py",
    "scripts/**/*.py",
    "configs/**/*.json",
    "configs/**/*.yaml",
    "tests/**/*.py",
    "reports/reviewer_ready_v2/*.json",
    "reports/post_human_review/*.json",
    "environment/*.json",
    "data/manifests/**/*.json",
    "data/compact20_reviewed/**/*.json",
    "notebooks/kaggle_cpu/*.ipynb",
    "notebooks/kaggle/*.ipynb",
    "docs/KAGGLE_*.md",
)

COMPACT20_T4X2_INCLUDES: tuple[str, ...] = (
    "pyproject.toml",
    "constraints.txt",
    "src/causal_agent_bench/**/*.py",
    "scripts/**/*.py",
    "configs/**/*.json",
    "configs/**/*.yaml",
    "reports/reviewer_ready_v2/*.json",
    "reports/post_human_review/EXECUTION_AUTHORIZATION_FINAL.json",
    "reports/post_human_review/REVIEWED_SLICE_LOCK_FINAL.json",
    "reports/post_human_review/C10_FINAL.json",
    "environment/*.json",
    "data/manifests/**/*.json",
    "data/compact20_reviewed/**/*.json",
    "notebooks/kaggle/*.ipynb",
)


class BundleError(RuntimeError):
    """A bundle refused to build."""


@dataclass(frozen=True)
class Member:
    arcname: str
    source: Path
    sha256: str


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=False
    ).stdout.strip()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _tracked_paths() -> set[str]:
    """Every path Git tracks.  A tracked file is public by construction.

    It has already passed the repository's own tracked-private-data and security
    scans, so the name-fragment screen below would only produce false positives
    on it — ``STAGE2_VAULT_STATUS.json`` records checks and a ciphertext hash, and
    is exactly the kind of public commitment a reviewer needs.
    """

    listing = _git("ls-files", "-z")
    return {name for name in listing.split("\0") if name}


def _forbidden(arcname: str, *, tracked: set[str]) -> str | None:
    """Why ``arcname`` must not be bundled, or ``None`` when it may be.

    Git's own view decides what is private: anything the repository ignores is
    private by the repository's declaration, which keeps this screen correct
    without a second list to maintain.
    """

    if arcname.startswith(FORBIDDEN_PREFIXES):
        return "path is on the never-bundle list"
    if arcname in tracked:
        return None
    lowered = arcname.casefold()
    for fragment in FORBIDDEN_NAME_FRAGMENTS:
        if fragment in lowered:
            return f"untracked file whose name contains {fragment!r}"
    return None


def collect(patterns: tuple[str, ...], *, root: Path = REPO_ROOT) -> list[Member]:
    """Resolve include patterns to a sorted, de-duplicated, screened member list."""

    tracked = _tracked_paths() if root == REPO_ROOT else set()
    ignored = _ignored(root)
    seen: dict[str, Path] = {}
    for pattern in patterns:
        for path in sorted(root.glob(pattern)):
            if not path.is_file() or path.is_symlink():
                continue
            arcname = str(path.relative_to(root))
            if "__pycache__" in arcname or arcname.endswith(".pyc"):
                continue
            if arcname in ignored:
                raise BundleError(
                    f"refusing to bundle {arcname}: the repository ignores it, which marks it "
                    "private"
                )
            reason = _forbidden(arcname, tracked=tracked)
            if reason:
                raise BundleError(f"refusing to bundle {arcname}: {reason}")
            seen[arcname] = path
    return [
        Member(arcname=arcname, source=seen[arcname], sha256=sha256_file(seen[arcname]))
        for arcname in sorted(seen)
    ]


def _ignored(root: Path) -> set[str]:
    """Paths under ``root`` that Git ignores, and which are therefore private."""

    if root != REPO_ROOT:
        return set()
    result = subprocess.run(
        ["git", "ls-files", "--others", "--ignored", "--exclude-standard", "-z"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return {name for name in result.stdout.split("\0") if name}


def build_manifest(members: list[Member], *, bundle_type: str) -> dict[str, Any]:
    """The manifest, with a content hash that excludes the manifest itself.

    Self-hash recursion is avoided by defining ``bundle_content_sha256`` over the
    sorted ``(path, sha256)`` pairs of the *other* members only.  That value is
    therefore stable and checkable without a fixed point.
    """

    payload = json.dumps(
        [[member.arcname, member.sha256] for member in members],
        separators=(",", ":"),
        sort_keys=False,
    ).encode()
    reports = REPO_ROOT / "reports"

    def report_hash(relative: str) -> str | None:
        path = reports / relative
        return sha256_file(path) if path.is_file() else None

    def report_field(relative: str, field: str) -> str | None:
        path = reports / relative
        if not path.is_file():
            return None
        return json.loads(path.read_text()).get(field)

    return {
        "schema_version": BUNDLE_SCHEMA_VERSION,
        "bundle_type": bundle_type,
        "created_from_commit": _git("rev-parse", "HEAD"),
        "scientific_freeze_sha256": report_field(
            "reviewer_ready_v2/SCIENTIFIC_FREEZE_V2.json", "freeze_sha256"
        ),
        "reviewed_slice_lock_sha256": report_field(
            "post_human_review/REVIEWED_SLICE_LOCK_FINAL.json", "receipt_sha256"
        ),
        "execution_authorization_sha256": report_field(
            "post_human_review/EXECUTION_AUTHORIZATION_FINAL.json", "receipt_sha256"
        ),
        "c10_report_sha256": report_hash("post_human_review/C10_FINAL.json"),
        "member_count": len(members),
        "members": [
            {"path": member.arcname, "sha256": member.sha256} for member in members
        ],
        "bundle_content_sha256": hashlib.sha256(payload).hexdigest(),
        "content_hash_procedure": (
            "sha256 of the compact JSON array of [path, sha256] pairs for every member "
            "except this manifest, in the member order recorded above"
        ),
        "private_material_included": False,
        "filename_is_not_an_interface": (
            "Notebooks locate this bundle by its contents. Renaming the ZIP or the Kaggle "
            "dataset does not affect discovery."
        ),
    }


def write_bundle(
    members: list[Member], manifest: dict[str, Any], output_dir: Path, *, bundle_type: str
) -> Path:
    """Write the ZIP deterministically and name it by content hash."""

    output_dir.mkdir(parents=True, exist_ok=True)
    slug = bundle_type.replace("-", "_").upper()
    short = manifest["bundle_content_sha256"][:16]
    target = output_dir / f"CAB_KAGGLE_{slug}_INPUT_{short}.zip"
    manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()

    if target.exists():
        target.unlink()
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        entries: list[tuple[str, bytes]] = [(MANIFEST_NAME, manifest_bytes)]
        entries += [(member.arcname, member.source.read_bytes()) for member in members]
        for arcname, data in sorted(entries):
            info = zipfile.ZipInfo(arcname, date_time=FIXED_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            # Regular file (0o100000) with normalized 0o644 permissions, so the
            # mode does not depend on whatever the build machine had on disk.
            info.external_attr = (0o100644) << 16
            info.create_system = 3
            archive.writestr(info, data)
    return target


def build(bundle_type: str, output_dir: Path, *, run_dir: Path | None = None) -> dict[str, Any]:
    if bundle_type == PREEXECUTION:
        members = collect(PREEXECUTION_INCLUDES)
    elif bundle_type == COMPACT20_T4X2:
        authorization = REPO_ROOT / "reports/post_human_review/EXECUTION_AUTHORIZATION_FINAL.json"
        if not authorization.is_file():
            raise BundleError(
                "the Compact-20 execution bundle requires a sealed execution authorization; "
                "run the manual-import gates first"
            )
        members = collect(COMPACT20_T4X2_INCLUDES)
    elif bundle_type in POSTRUN_TYPES:
        if run_dir is None:
            raise BundleError(f"--run-dir is required for {bundle_type}")
        if not run_dir.is_dir():
            raise BundleError(
                f"no run directory at {run_dir}. Post-run bundles are built from genuine "
                "returned results; there is nothing to bundle before a run exists."
            )
        members = collect(("**/*",), root=run_dir)
    else:
        raise BundleError(f"unknown bundle type {bundle_type!r}")

    if not members:
        raise BundleError(f"the {bundle_type} bundle would be empty")
    manifest = build_manifest(members, bundle_type=bundle_type)
    target = write_bundle(members, manifest, output_dir, bundle_type=bundle_type)
    return {
        "bundle_type": bundle_type,
        "path": str(target),
        "sha256": sha256_file(target),
        "size_bytes": target.stat().st_size,
        "member_count": manifest["member_count"],
        "bundle_content_sha256": manifest["bundle_content_sha256"],
        "created_from_commit": manifest["created_from_commit"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--bundle-type",
        default=PREEXECUTION,
        choices=[PREEXECUTION, COMPACT20_T4X2, *POSTRUN_TYPES],
    )
    parser.add_argument("--run-dir", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=REPO_ROOT / "dist" / "kaggle_inputs")
    parser.add_argument(
        "--manifest-out",
        type=Path,
        default=REPO_ROOT / "reports" / "post_human_review" / "KAGGLE_INPUT_BUNDLE_MANIFESTS.json",
    )
    args = parser.parse_args(argv)

    try:
        result = build(args.bundle_type, args.output_dir, run_dir=args.run_dir)
    except BundleError as error:
        print(json.dumps({"status": "BLOCKED", "blocker": str(error)}, indent=2))
        return 1

    existing: dict[str, Any] = {}
    if args.manifest_out.is_file():
        existing = json.loads(args.manifest_out.read_text())
    existing.setdefault("schema_version", "cab_kaggle_input_bundle_index_v1")
    existing.setdefault("bundles", {})
    # Only the hashes and counts are recorded in Git; the ZIP itself is a build
    # artifact and stays out of the repository.
    existing["bundles"][args.bundle_type] = {
        key: value for key, value in result.items() if key != "path"
    } | {"filename": Path(result["path"]).name}
    args.manifest_out.parent.mkdir(parents=True, exist_ok=True)
    args.manifest_out.write_text(json.dumps(existing, indent=2, sort_keys=True) + "\n")

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
