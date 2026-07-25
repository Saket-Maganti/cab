from __future__ import annotations

import argparse
from pathlib import Path

from causal_agent_bench.analysis.load_results import load_run_results
from causal_agent_bench.analysis.tables import (
    ablation_results_table,
    with_asset_metadata,
    write_table_bundle,
)
from causal_agent_bench.safety.export_guards import apply_export_watermark, validate_export_source


def _watermark_table_bundle(paths: list[Path], watermark: str | None) -> None:
    if not watermark:
        return
    for path in paths:
        if path.suffix in {".md", ".tex"}:
            path.write_text(
                apply_export_watermark(path.read_text(encoding="utf-8"), watermark),
                encoding="utf-8",
            )
        elif path.suffix == ".csv":
            text = path.read_text(encoding="utf-8")
            if watermark not in text:
                path.write_text(f"# {watermark}\n{text}", encoding="utf-8")


def export_ablation_table(
    run_dir: str | Path,
    *,
    output_dir: str | Path | None = None,
    allow_engineering_only: bool = False,
    allow_incomplete: bool = False,
    allow_placeholder: bool = False,
    allow_mock_stub: bool = False,
) -> list[Path]:
    guard = validate_export_source(
        run_dir,
        allow_engineering_only=allow_engineering_only,
        allow_incomplete=allow_incomplete,
        allow_placeholder=allow_placeholder,
        allow_mock_stub=allow_mock_stub,
        operation="export-ablation-table",
    )
    data = load_run_results(Path(run_dir))
    out = Path(output_dir) if output_dir else data.run_dir / "paper_assets" / "tables"
    out.mkdir(parents=True, exist_ok=True)
    frame = with_asset_metadata(ablation_results_table(data), data)
    paths = write_table_bundle(frame, out / "table4_ablation_results")
    _watermark_table_bundle(paths, guard.get("watermark"))
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Export CausalAgentBench ablation table bundles.")
    parser.add_argument("--run-dir", required=True, help="Run directory with ablation trajectories.")
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory. Defaults to <run-dir>/paper_assets/tables.",
    )
    parser.add_argument("--allow-engineering-only", action="store_true")
    parser.add_argument("--allow-incomplete", action="store_true")
    parser.add_argument("--allow-placeholder", action="store_true")
    parser.add_argument("--allow-mock-stub", action="store_true")
    args = parser.parse_args()

    paths = export_ablation_table(
        args.run_dir,
        output_dir=args.output_dir,
        allow_engineering_only=args.allow_engineering_only,
        allow_incomplete=args.allow_incomplete,
        allow_placeholder=args.allow_placeholder,
        allow_mock_stub=args.allow_mock_stub,
    )
    for path in paths:
        print(path)


if __name__ == "__main__":
    main()
