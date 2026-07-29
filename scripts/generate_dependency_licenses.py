#!/usr/bin/env python3
"""Generate a public dependency licence inventory from installed metadata."""

from __future__ import annotations

import argparse
import json
from importlib.metadata import PackageNotFoundError, metadata, version
from pathlib import Path

from generate_level5_sbom import RUNTIME_PACKAGES


def build_inventory() -> dict:
    packages = []
    for package in sorted(RUNTIME_PACKAGES, key=str.lower):
        try:
            package_metadata = metadata(package)
            observed_version = version(package)
        except PackageNotFoundError:
            package_metadata = {}
            observed_version = "NOT_INSTALLED"
        packages.append(
            {
                "name": package,
                "version": observed_version,
                "licence": package_metadata.get("License", "UNKNOWN"),
                "homepage": package_metadata.get("Home-page", ""),
            }
        )
    return {"schema_version": "1.0", "packages": packages}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="release/dependency_licenses.json")
    args = parser.parse_args()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(build_inventory(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
