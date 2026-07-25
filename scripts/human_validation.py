from __future__ import annotations

import argparse
import json
from pathlib import Path

from causal_agent_bench.analysis.human_validation import (
    export_human_validation_sample,
    summarize_human_validation_annotations,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Human validation export and agreement utilities.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    export_parser = subparsers.add_parser("export", help="Export annotation CSV/JSONL from a run.")
    export_parser.add_argument("--run-dir", required=True)
    export_parser.add_argument("--output-dir", default=None)
    export_parser.add_argument("--sample-size", type=int, default=100)
    export_parser.add_argument("--seed", type=int, default=0)
    export_parser.add_argument("--annotators-per-item", type=int, default=2)
    export_parser.add_argument("--no-html", action="store_true")

    summarize_parser = subparsers.add_parser("summarize", help="Summarize completed annotations.")
    summarize_parser.add_argument("--annotations", required=True)
    summarize_parser.add_argument("--output-dir", default=None)

    args = parser.parse_args()
    if args.command == "export":
        payload = export_human_validation_sample(
            args.run_dir,
            output_dir=args.output_dir,
            sample_size=args.sample_size,
            seed=args.seed,
            annotators_per_item=args.annotators_per_item,
            include_html=not args.no_html,
        )
    else:
        payload = summarize_human_validation_annotations(
            Path(args.annotations),
            output_dir=args.output_dir,
        )
    print(json.dumps(payload, indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
