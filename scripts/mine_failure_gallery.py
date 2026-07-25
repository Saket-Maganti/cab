from __future__ import annotations

import argparse
from pathlib import Path

from causal_agent_bench.analysis.error_analysis import generate_failure_gallery
from causal_agent_bench.analysis.load_results import load_run_results


def main() -> None:
    parser = argparse.ArgumentParser(description="Mine trajectory failures into a review gallery.")
    parser.add_argument("--run-dir", required=True, help="Run directory with trajectories and scores.")
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Gallery directory. Defaults to <run-dir>/error_cases.",
    )
    parser.add_argument("--max-cases", type=int, default=5)
    parser.add_argument(
        "--no-filters",
        action="store_true",
        help="Skip cross-case filters such as model contrast and high-cost low-quality cases.",
    )
    args = parser.parse_args()

    data = load_run_results(Path(args.run_dir))
    output_dir = Path(args.output_dir) if args.output_dir else Path(args.run_dir) / "error_cases"
    paths = generate_failure_gallery(
        data,
        output_dir,
        max_cases=args.max_cases,
        include_filters=not args.no_filters,
        include_legacy_aliases=True,
    )
    for path in paths:
        print(path)


if __name__ == "__main__":
    main()
