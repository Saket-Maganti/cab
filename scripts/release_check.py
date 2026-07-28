#!/usr/bin/env python3
"""Validate release cards, manifest inventory, and reproducibility metadata."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPO_ROOT / "release" / "release_manifest.json"
PYPROJECT = REPO_ROOT / "pyproject.toml"
PACKAGE_INIT = REPO_ROOT / "src" / "causal_agent_bench" / "__init__.py"


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _release_bundle_hash(paths: list[Path], repo_root: Path = REPO_ROOT) -> str:
    lines = []
    for path in sorted(paths, key=lambda item: str(item)):
        rel = path.relative_to(repo_root).as_posix()
        lines.append(f"{rel}\t{_file_sha256(path)}")
    payload = "\n".join(lines).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _package_version() -> str:
    text = PACKAGE_INIT.read_text(encoding="utf-8")
    match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', text)
    if not match:
        raise ValueError("could not read package version from src/causal_agent_bench/__init__.py")
    return match.group(1)


def _load_manifest(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _collect_manifest_paths(manifest: dict) -> list[str]:
    keys = (
        "cards",
        "docs",
        "configs",
        "scripts",
        "source_packages",
        "benchmark_specs",
        "dataset_versions",
        "paper_files",
        "notebooks",
        "data_manifests",
        "root_documents",
        "license_files",
    )
    paths: list[str] = []
    for key in keys:
        values = manifest.get(key, [])
        if not isinstance(values, list):
            raise ValueError(f"manifest field {key!r} must be a list")
        paths.extend(str(value) for value in values)
    license_file = manifest.get("license_file")
    if license_file:
        paths.append(str(license_file))
    frozen_manifest = manifest.get("default_frozen_manifest")
    if frozen_manifest:
        paths.append(str(frozen_manifest))
    return sorted(set(paths))


def _check_complete_inventory(manifest: dict, repo_root: Path) -> list[str]:
    """Refuse a canonical release manifest that silently omits live files."""

    policy = manifest.get("inventory_policy", {})
    if not isinstance(policy, dict) or not policy.get("completeness_enforced"):
        return []
    categories = policy.get("categories", {})
    if not isinstance(categories, dict):
        return ["inventory_policy.categories must be an object"]

    errors: list[str] = []
    for category, patterns in sorted(categories.items()):
        if not isinstance(patterns, list) or not all(
            isinstance(pattern, str) for pattern in patterns
        ):
            errors.append(f"inventory_policy category {category!r} must contain glob strings")
            continue
        listed = manifest.get(category, [])
        if not isinstance(listed, list):
            errors.append(f"manifest field {category!r} must be a list")
            continue
        observed = {
            path.relative_to(repo_root).as_posix()
            for pattern in patterns
            for path in repo_root.glob(pattern)
            if path.is_file()
        }
        recorded = {str(path) for path in listed}
        omitted = sorted(observed - recorded)
        stale = sorted(recorded - observed)
        if omitted:
            errors.append(
                f"incomplete {category} inventory; omitted {len(omitted)} file(s): "
                + ", ".join(omitted[:10])
            )
        if stale:
            errors.append(
                f"stale {category} inventory; absent {len(stale)} file(s): "
                + ", ".join(stale[:10])
            )
    return errors


def _check_paths_exist(paths: list[str], repo_root: Path) -> list[str]:
    errors: list[str] = []
    for rel_path in paths:
        path = repo_root / rel_path
        if not path.exists():
            errors.append(f"missing release file: {rel_path}")
    return errors


def _check_forbidden_release_payloads(
    paths: list[str],
    repo_root: Path,
) -> list[str]:
    """Reject private/protected payload paths from every release category."""

    policy_path = repo_root / "configs/cab_heldout_release_policy.json"
    policy: dict = {}
    if policy_path.is_file():
        try:
            value = json.loads(policy_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            value = {}
        if isinstance(value, dict):
            policy = value
    private_root = str(
        policy.get(
            "private_payload_root",
            "private_data/heldout_challenge_v2/",
        )
    ).rstrip("/")
    patterns = [
        str(value)
        for value in policy.get(
            "protected_payload_globs",
            [
                "private_data/heldout_challenge_v2/**",
                "data/**/heldout_challenge_v2*.jsonl",
                "data/**/*protected*heldout*.jsonl",
            ],
        )
        if isinstance(value, str)
    ]
    allowed = {
        str(value)
        for value in policy.get("allowed_public_metadata", [])
        if isinstance(value, str)
    }
    errors: list[str] = []
    for value in paths:
        if value in allowed:
            continue
        candidate = Path(value)
        private = value == private_root or value.startswith(f"{private_root}/")
        protected = any(candidate.match(pattern) for pattern in patterns)
        if private or protected:
            errors.append(
                f"forbidden private/protected release payload: {value}"
            )
    return errors


def _check_card_sections(cards: list[str], required_sections: list[str], repo_root: Path) -> list[str]:
    errors: list[str] = []
    for rel_path in cards:
        text = (repo_root / rel_path).read_text(encoding="utf-8")
        for section in required_sections:
            pattern = rf"^##\s+{re.escape(section)}\s*$"
            if not re.search(pattern, text, flags=re.MULTILINE):
                errors.append(f"{rel_path}: missing section '{section}'")
    return errors


def _check_package_version(manifest: dict) -> list[str]:
    errors: list[str] = []
    expected = str(manifest.get("package_version", ""))
    actual = _package_version()
    if expected and expected != actual:
        errors.append(f"package_version mismatch: manifest={expected!r} package={actual!r}")
    return errors


def _check_frozen_manifest(manifest: dict, repo_root: Path) -> list[str]:
    errors: list[str] = []
    rel_path = manifest.get("default_frozen_manifest")
    if not rel_path:
        return errors
    path = repo_root / rel_path
    if not path.exists():
        return [f"default frozen manifest missing: {rel_path}"]
    payload = json.loads(path.read_text(encoding="utf-8"))
    for field in ("dataset_version", "dataset_hash", "files", "quality_passed"):
        if field not in payload:
            errors.append(f"{rel_path}: missing field {field!r}")
    return errors


def run_release_check(
    manifest_path: str | Path = DEFAULT_MANIFEST,
    *,
    repo_root: str | Path | None = None,
    write_bundle_hash: bool = False,
) -> dict:
    root = Path(repo_root) if repo_root is not None else REPO_ROOT
    manifest_path = Path(manifest_path)
    if not manifest_path.is_absolute():
        manifest_path = root / manifest_path
    manifest = _load_manifest(manifest_path)
    errors: list[str] = []
    errors.extend(_check_package_version(manifest))
    errors.extend(_check_complete_inventory(manifest, root))
    inventory = _collect_manifest_paths(manifest)
    errors.extend(_check_paths_exist(inventory, root))
    errors.extend(_check_forbidden_release_payloads(inventory, root))
    errors.extend(
        _check_card_sections(
            manifest.get("section_validated_cards") or manifest.get("cards", []),
            manifest.get("required_card_sections", []),
            root,
        )
    )
    errors.extend(_check_frozen_manifest(manifest, root))

    resolved_paths = [root / rel for rel in inventory if (root / rel).exists()]
    bundle_hash = _release_bundle_hash(resolved_paths, root)
    file_hashes = {
        path.relative_to(root).as_posix(): _file_sha256(path) for path in resolved_paths
    }
    expected_bundle_hash = manifest.get("release_bundle_hash")
    if expected_bundle_hash and expected_bundle_hash != bundle_hash and not write_bundle_hash:
        errors.append(
            "release_bundle_hash mismatch: "
            f"manifest={expected_bundle_hash} computed={bundle_hash}"
        )

    report = {
        "passed": not errors,
        "errors": errors,
        "release_id": manifest.get("release_id"),
        "release_version": manifest.get("release_version"),
        "package_version": _package_version(),
        "release_bundle_hash": bundle_hash,
        "inventory_file_count": len(resolved_paths),
        "file_hashes": file_hashes,
        "validation_status": manifest.get("validation_status", {}),
    }

    if write_bundle_hash:
        manifest["release_bundle_hash"] = bundle_hash
        manifest["inventory_file_count"] = len(resolved_paths)
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument(
        "--write-bundle-hash",
        action="store_true",
        help="Write computed release_bundle_hash back into the manifest.",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON report to stdout.")
    args = parser.parse_args(argv)

    try:
        report = run_release_check(args.manifest, write_bundle_hash=args.write_bundle_hash)
    except Exception as exc:
        print(json.dumps({"passed": False, "error": str(exc)}), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        status = "PASS" if report["passed"] else "FAIL"
        print(f"release-check: {status}")
        print(f"release_id: {report.get('release_id')}")
        print(f"release_version: {report.get('release_version')}")
        print(f"package_version: {report.get('package_version')}")
        print(f"release_bundle_hash: {report.get('release_bundle_hash')}")
        print(f"inventory_file_count: {report.get('inventory_file_count')}")
        for error in report.get("errors", []):
            print(f"ERROR: {error}")

    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
