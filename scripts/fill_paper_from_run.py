#!/usr/bin/env python3
"""Fill paper/latexpaper/generated fragments from a verified experiment run directory."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, help="Experiment run directory with scores and metadata.")
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    parser.add_argument(
        "--allow-engineering-only",
        action="store_true",
        help="Allow pilot_stub/local-stub runs for draft previews (not scientific evidence).",
    )
    parser.add_argument(
        "--promote-to-supported",
        action="store_true",
        help="Promote claims to supported only when human-validation table is ready.",
    )
    parser.add_argument("--no-export", action="store_true", help="Skip export-paper-assets step.")
    parser.add_argument("--no-ledger", action="store_true", help="Skip claim-ledger updates.")
    parser.add_argument("--json", action="store_true", help="Print JSON summary.")
    args = parser.parse_args(argv)

    sys.path.insert(0, str(REPO_ROOT / "src"))
    from causal_agent_bench.analysis.paper_fill import fill_paper_from_run

    try:
        report = fill_paper_from_run(
            args.run_dir,
            repo_root=args.repo_root,
            allow_engineering_only=args.allow_engineering_only,
            export_assets=not args.no_export,
            update_ledger=not args.no_ledger,
            promote_to_supported=args.promote_to_supported,
        )
    except Exception as exc:
        print(json.dumps({"filled": False, "error": str(exc)}), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("fill-paper-from-run: OK")
        print(f"run_dir: {report['summary']['run_dir']}")
        print(f"evidence_scope: {report['summary']['evidence_scope']}")
        print(f"mapping: {report['mapping_path']}")
        print(f"generated: {report['generated_dir']}")
        for warning in report.get("warnings", []):
            print(f"WARNING: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
