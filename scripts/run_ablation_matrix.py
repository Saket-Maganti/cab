from __future__ import annotations

import argparse
from pathlib import Path

from causal_agent_bench.ablation_matrix import (
    aggregate_ablation_matrix,
    export_ablation_matrix_artifacts,
    load_ablation_matrix_config,
    run_ablation_matrix,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Plan or run a CausalAgentBench ablation matrix.")
    parser.add_argument(
        "--config",
        default="configs/ablation_matrix_local_stub.yaml",
        help="Matrix YAML config path.",
    )
    parser.add_argument("--output-dir", default=None, help="Override matrix output root.")
    parser.add_argument("--execute", action="store_true", help="Run each cell after planning.")
    parser.add_argument("--replan", action="store_true", help="Force replan before execute.")
    parser.add_argument(
        "--no-skip-existing",
        action="store_true",
        help="Re-run cells that already have aggregate_scores.json.",
    )
    parser.add_argument(
        "--aggregate-only",
        action="store_true",
        help="Aggregate/export from an existing matrix directory.",
    )
    args = parser.parse_args()

    matrix = load_ablation_matrix_config(args.config)
    matrix_root = (
        Path(args.output_dir) if args.output_dir else Path(matrix.output_dir) / matrix.run_name
    )
    if args.aggregate_only:
        frame = aggregate_ablation_matrix(matrix_root)
        paths = export_ablation_matrix_artifacts(matrix_root, frame)
    else:
        manifest = run_ablation_matrix(
            args.config,
            execute=args.execute,
            matrix_output_dir=args.output_dir,
            skip_existing=not args.no_skip_existing,
            replan=args.replan,
        )
        if args.execute:
            paths = [Path(path) for path in manifest.get("aggregate_paths", [])]
        else:
            paths = [matrix_root / "matrix_manifest.json", matrix_root / "matrix_plan.md"]
    for path in paths:
        print(path)


if __name__ == "__main__":
    main()
