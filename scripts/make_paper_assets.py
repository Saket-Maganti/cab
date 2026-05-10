from __future__ import annotations

import argparse
from pathlib import Path

from causal_agent_bench.analysis.report import export_paper_assets


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate CausalAgentBench paper assets.")
    parser.add_argument("--run-dir", required=True, help="Run directory with trajectories and scores.")
    parser.add_argument(
        "--no-global",
        action="store_true",
        help="Only write assets under the run directory.",
    )
    args = parser.parse_args()
    paths = export_paper_assets(Path(args.run_dir), write_global=not args.no_global)
    for path in paths:
        print(path)


if __name__ == "__main__":
    main()
