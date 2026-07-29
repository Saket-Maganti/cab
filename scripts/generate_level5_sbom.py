#!/usr/bin/env python3
"""Generate a deterministic CycloneDX-compatible dependency SBOM."""

from __future__ import annotations

import argparse
import json
from importlib.metadata import PackageNotFoundError, metadata, version
from pathlib import Path

from causal_agent_bench.level5.core import content_hash, utc_now

RUNTIME_PACKAGES = ("jinja2", "numpy", "pandas", "pydantic", "PyYAML", "rich", "scipy", "typer")


def build_sbom() -> dict:
    components = []
    for package in sorted(RUNTIME_PACKAGES, key=str.lower):
        try:
            observed_version = version(package)
            package_metadata = metadata(package)
        except PackageNotFoundError:
            observed_version = "NOT_INSTALLED"
            package_metadata = {}
        components.append(
            {
                "type": "library",
                "name": package,
                "version": observed_version,
                "purl": (
                    f"pkg:pypi/{package.lower()}@{observed_version}"
                    if observed_version != "NOT_INSTALLED"
                    else None
                ),
                "licenses": [{"license": {"name": package_metadata.get("License", "UNKNOWN")}}],
            }
        )
    serial = f"urn:uuid:{content_hash(components)[:32]}"
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": serial,
        "version": 1,
        "metadata": {
            "timestamp": utc_now(),
            "component": {"type": "application", "name": "causal-agent-bench"},
        },
        "components": components,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="release/level5_sbom.json")
    args = parser.parse_args()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(build_sbom(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
