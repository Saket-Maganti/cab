#!/usr/bin/env python3
"""List, preflight, or export the strict Phase 15 empirical asset bundle."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from causal_agent_bench.analysis.phase15_assets import (
    REQUIRED_SOURCE_ROLES,
    export_phase15_asset_bundle,
    phase15_asset_contract,
    validate_phase15_asset_bundle,
)


def _source_mapping(values: list[str]) -> dict[str, Path]:
    sources: dict[str, Path] = {}
    for value in values:
        role, separator, raw_path = value.partition("=")
        if not separator or not role or not raw_path:
            raise ValueError(f"invalid --source {value!r}; expected ROLE=PATH")
        if role in sources:
            raise ValueError(f"duplicate --source role: {role}")
        sources[role] = Path(raw_path)
    return sources


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--list-contract",
        action="store_true",
        help="Print the design-only asset registry; never inspect or write result assets.",
    )
    parser.add_argument(
        "--source",
        action="append",
        default=[],
        metavar="ROLE=PATH",
        help=(
            "Audited paper-eligible source. Required roles: "
            + ", ".join(REQUIRED_SOURCE_ROLES)
        ),
    )
    parser.add_argument(
        "--output-dir",
        default="paper/phase15_empirical_assets",
        help="New output directory; existing paths are never overwritten.",
    )
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help="Validate all sources and required inputs without writing assets.",
    )
    args = parser.parse_args(argv)

    if args.list_contract:
        print(json.dumps(phase15_asset_contract(), indent=2, sort_keys=True))
        return 0

    try:
        sources = _source_mapping(args.source)
    except ValueError as exc:
        parser.error(str(exc))

    validation = validate_phase15_asset_bundle(sources)
    if args.preflight_only:
        print(json.dumps(validation, indent=2, sort_keys=True))
        return 0 if validation["passed"] else 1
    if not validation["passed"]:
        print("Phase 15 paper asset export refused:")
        for issue in validation["issues"]:
            print(f"- {issue}")
        return 1

    paths = export_phase15_asset_bundle(sources, args.output_dir)
    print(f"Phase 15 paper asset bundle written ({len(paths)} files):")
    for path in paths:
        print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
