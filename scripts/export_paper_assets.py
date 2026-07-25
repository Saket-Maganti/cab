#!/usr/bin/env python3
"""Export canonical paper tables and figures with metadata sidecars."""

from __future__ import annotations

import argparse

from causal_agent_bench.analysis.paper_assets import export_paper_assets


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument(
        "--allow-engineering-only",
        action="store_true",
        help="Allow stub/smoke/local-stub runs (assets marked engineering-only).",
    )
    parser.add_argument(
        "--no-write-global",
        action="store_true",
        help="Skip copying to repo-level figures/ and tables/.",
    )
    args = parser.parse_args()
    paths = export_paper_assets(
        args.run_dir,
        write_global=not args.no_write_global,
        allow_engineering_only=args.allow_engineering_only,
    )
    for path in paths:
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
