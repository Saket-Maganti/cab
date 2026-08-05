#!/usr/bin/env python3
"""Prove the real Kaggle input bundle is found by content, whatever it is called.

The unit tests already cover this against synthetic archives.  This probe runs
the *actual* freshly built bundle through the same discovery module under every
name and layout Kaggle is known to produce, plus the malicious shapes discovery
must refuse, and writes the outcomes down.

Kaggle renames things routinely — the dataset slug is the uploader's choice, a
browser appends " (1)", and a re-upload can uppercase the extension.  Every one
of those must be a non-event.  Each hostile case is expected to be *refused*, so
a probe that quietly succeeded everywhere would be reporting a broken gate, not
a healthy one.

Read-only with respect to the repository: everything is staged in a temporary
directory that is removed afterwards.
"""

from __future__ import annotations

import argparse
import json
import shutil
import struct
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from causal_agent_bench.kaggle_input_discovery import (
    REPOSITORY_BUNDLE,
    KaggleInputError,
    discover_kaggle_input,
    file_sha256,
    verify_bundle_manifest,
)

DEFAULT_BUNDLE_DIR = REPO_ROOT / "dist" / "kaggle_inputs"

#: Names a real Kaggle round-trip can produce.  Every one must be a non-event.
BENIGN_NAMES: tuple[str, ...] = (
    "archive.zip",
    "my bundle with spaces.zip",
    "ünïcødé-архив-束.zip",
    "UPPERCASE.ZIP",
    "MiXeD.Zip",
    "final_FINAL_v3 (2).zip",
    "cab-input.zip",
)


def _stage(root: Path, name: str, source: Path, *, subdir: str = "dataset") -> Path:
    destination = root / subdir
    destination.mkdir(parents=True, exist_ok=True)
    target = destination / name
    shutil.copy2(source, target)
    return target


def _probe(search_root: Path, working: Path) -> dict[str, Any]:
    """Run discovery once, reporting either the selection or the refusal."""

    try:
        result = discover_kaggle_input(search_root=search_root, working_root=working)
    except KaggleInputError as error:
        return {"outcome": "REFUSED", "reason": str(error)[:300]}
    manifest = verify_bundle_manifest(Path(result["bundle_root"]))
    return {
        "outcome": "SELECTED",
        "bundle_type": result["bundle_type"],
        "selected_filename": Path(result["selected"]["path"]).name,
        "bundle_content_sha256": manifest["bundle_content_sha256"],
        "created_from_commit": manifest["created_from_commit"],
        "manifest_reverified": manifest["passed"],
        "manifest_checks": manifest["checks"],
    }


def _case(name: str, expected: str, run) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="cab-name-probe-") as raw:
        root = Path(raw)
        inputs = root / "input"
        working = root / "working"
        inputs.mkdir()
        working.mkdir()
        run(inputs)
        observed = _probe(inputs, working)
    return {
        "case": name,
        "expected": expected,
        "observed_outcome": observed["outcome"],
        "passed": observed["outcome"] == expected,
        **{key: value for key, value in observed.items() if key != "outcome"},
    }


def _truncate(source: Path, target: Path) -> None:
    payload = source.read_bytes()
    target.write_bytes(payload[: len(payload) // 2])


def _zip_bomb(target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("pyproject.toml", "[project]\nname='cab'\n")
        archive.writestr("src/causal_agent_bench/__init__.py", "")
        archive.writestr("reports/reviewer_ready_v2/SCIENTIFIC_FREEZE_V2.json", "{}")
        archive.writestr("bomb.bin", b"\0" * (64 * 1024 * 1024))


def _traversal(target: Path, *, member: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w") as archive:
        archive.writestr("pyproject.toml", "[project]\nname='cab'\n")
        archive.writestr("src/causal_agent_bench/__init__.py", "")
        archive.writestr("reports/reviewer_ready_v2/SCIENTIFIC_FREEZE_V2.json", "{}")
        archive.writestr("configs/reviewer_ready_v2/analysis_plan_v2.json", "{}")
        archive.writestr("scripts/cab_review_ready_v2.py", "")
        archive.writestr(member, "owned\n")


def run_probe(bundle: Path, other: Path | None) -> dict[str, Any]:
    cases: list[dict[str, Any]] = []

    for name in BENIGN_NAMES:
        cases.append(
            _case(
                f"benign_name::{name}",
                "SELECTED",
                lambda inputs, name=name: _stage(inputs, name, bundle),
            )
        )

    cases.append(
        _case(
            "nested_kaggle_dataset_directory",
            "SELECTED",
            lambda inputs: _stage(inputs, "archive.zip", bundle, subdir="ds-9f3a/inner-71c"),
        )
    )
    cases.append(
        _case(
            "byte_identical_duplicate_is_not_an_ambiguity",
            "SELECTED",
            lambda inputs: (
                _stage(inputs, "one.zip", bundle),
                _stage(inputs, "two.zip", bundle, subdir="second"),
            ),
        )
    )
    cases.append(
        _case(
            "unrelated_zip_beside_a_valid_bundle",
            "SELECTED",
            lambda inputs: (
                _stage(inputs, "bundle.zip", bundle),
                _write_unrelated(inputs / "noise" / "holiday_photos.zip"),
            ),
        )
    )
    if other is not None:
        cases.append(
            _case(
                "two_conflicting_valid_bundles_fail_closed",
                "REFUSED",
                lambda inputs: (
                    _stage(inputs, "first.zip", bundle),
                    _stage(inputs, "second.zip", other, subdir="other"),
                ),
            )
        )
    cases.append(
        _case(
            "path_traversal_member",
            "REFUSED",
            lambda inputs: _traversal(inputs / "d" / "evil.zip", member="../escaped.txt"),
        )
    )
    cases.append(
        _case(
            "absolute_path_member",
            "REFUSED",
            lambda inputs: _traversal(inputs / "d" / "evil.zip", member="/etc/owned.txt"),
        )
    )
    cases.append(
        _case(
            "truncated_archive",
            "REFUSED",
            lambda inputs: _truncate(bundle, _mkfile(inputs / "d" / "cut.zip")),
        )
    )
    cases.append(
        _case(
            "zip_bomb_expansion_ratio",
            "REFUSED",
            lambda inputs: _zip_bomb(inputs / "d" / "bomb.zip"),
        )
    )
    cases.append(_case("no_bundle_attached_at_all", "REFUSED", lambda inputs: None))

    # A selection that resolved to the right bundle but failed its own manifest
    # re-verification is not a pass, so fold that in rather than reporting only
    # the outcome.
    for case in cases:
        if case["observed_outcome"] == "SELECTED":
            case["passed"] = (
                case["passed"]
                and bool(case.get("manifest_reverified"))
                and case.get("bundle_type") == REPOSITORY_BUNDLE
            )
    failed = [case["case"] for case in cases if not case["passed"]]
    selected_hashes = {
        case.get("bundle_content_sha256")
        for case in cases
        if case["observed_outcome"] == "SELECTED"
    }
    return {
        "schema_version": "cab_kaggle_arbitrary_name_input_tests_v1",
        "probed_bundle": bundle.name,
        "probed_bundle_sha256": file_sha256(bundle),
        "expected_bundle_type": REPOSITORY_BUNDLE,
        "case_count": len(cases),
        "passed": not failed,
        "failed_cases": failed,
        "every_selection_resolved_to_one_bundle": len(selected_hashes) == 1,
        "selected_bundle_content_sha256": sorted(h for h in selected_hashes if h),
        "discovery_basis": (
            "archive contents scored against a weighted sentinel set; filenames, dataset slugs "
            "and archive root folder names are never consulted"
        ),
        "cases": cases,
    }


def _mkfile(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _write_unrelated(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("IMG_0001.jpg", struct.pack("<4s", b"\xff\xd8\xff\xe0"))
        archive.writestr("notes.txt", "nothing to do with this project\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--bundle",
        type=Path,
        help="the input bundle to probe (defaults to the newest CPU bundle built)",
    )
    parser.add_argument(
        "--other-bundle",
        type=Path,
        help="a second, different valid bundle, used for the ambiguity case",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "reports" / "post_human_review" / "KAGGLE_ARBITRARY_NAME_INPUT_TESTS.json",
    )
    args = parser.parse_args(argv)

    bundle = args.bundle
    if bundle is None:
        found = sorted(DEFAULT_BUNDLE_DIR.glob("CAB_KAGGLE_CPU_PREEXECUTION_INPUT_*.zip"))
        if not found:
            print(
                json.dumps(
                    {
                        "status": "BLOCKED",
                        "blocker": f"no CPU input bundle in {DEFAULT_BUNDLE_DIR}; build one first",
                    },
                    indent=2,
                )
            )
            return 1
        bundle = found[-1]

    other = args.other_bundle
    if other is None:
        candidates = sorted(DEFAULT_BUNDLE_DIR.glob("CAB_KAGGLE_COMPACT20_T4X2_INPUT_*.zip"))
        other = candidates[-1] if candidates else None

    report = run_probe(bundle, other)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: value for key, value in report.items() if key != "cases"}, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
