#!/usr/bin/env python3
"""Build the protected-heldout Git exposure inventory without payload copies."""

from __future__ import annotations

import argparse
from pathlib import Path

from causal_agent_bench.safety.exposure_inventory import (
    write_protected_exposure_inventory,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = Path("reports/PROTECTED_HELDOUT_EXPOSURE_INVENTORY.json")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args(argv)
    output, payload = write_protected_exposure_inventory(
        ROOT,
        args.output,
    )
    print(f"wrote {output.relative_to(ROOT)} (artifacts={payload['summary']['artifact_count']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
