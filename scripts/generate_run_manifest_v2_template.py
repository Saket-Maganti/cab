#!/usr/bin/env python3
"""Write the non-runnable canonical CAB run-manifest template."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from causal_agent_bench.runners.run_manifest_v2 import write_manifest_template


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        default="configs/run_manifest_v2_TEMPLATE_NOT_RUNNABLE.json",
    )
    args = parser.parse_args(argv)
    output = Path(args.output)
    if not output.is_absolute():
        output = ROOT / output
    print(write_manifest_template(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

