"""Integration tests that start local benchmark runs via run_experiment.

Excluded from strict no-run validation — see docs/NO_RUN_VALIDATION.md.
"""

import json
from pathlib import Path

import pytest

from causal_agent_bench.analysis.figures import build_all_figures
from causal_agent_bench.analysis.load_results import load_run_results
from causal_agent_bench.analysis.paper_assets import (
    assess_run_for_paper_assets,
    export_paper_assets,
    validate_paper_asset_run,
)
from causal_agent_bench.runners.config import ExperimentConfig
from causal_agent_bench.runners.experiment import run_experiment

pytestmark = [pytest.mark.integration, pytest.mark.local_run]


def _smoke_run(tmp_path: Path) -> Path:
    config = ExperimentConfig.model_validate(
        {
            "seed": 17,
            "run_name": "paper_assets_smoke",
            "benchmark_path": "data/sample/instances.jsonl",
            "agents": ["random_tool_agent", "scripted_oracle_agent"],
            "max_steps": 8,
            "num_repeats": 1,
            "output_dir": str(tmp_path),
            "auto_score": True,
        }
    )
    return run_experiment(config)["run_dir"]


def test_engineering_only_run_blocked_without_flag(tmp_path):
    run_dir = _smoke_run(tmp_path)
    data = load_run_results(run_dir)
    assessment = assess_run_for_paper_assets(data)
    assert assessment["engineering_only"] is True
    issues = validate_paper_asset_run(assessment, allow_engineering_only=False)
    assert issues
    with pytest.raises(ValueError, match=r"refusing|engineering-only"):
        export_paper_assets(run_dir, write_global=False, allow_engineering_only=False)


def test_export_writes_sidecars_and_manifest(tmp_path):
    run_dir = _smoke_run(tmp_path / "export")
    paths = export_paper_assets(
        run_dir,
        write_global=False,
        allow_engineering_only=True,
        allow_mock_stub=True,
    )
    names = {Path(path).name for path in paths}
    assert "paper_assets_manifest.json" in names
    assert "table2_main_agent_performance.meta.json" in names
    assert "figure5_cost_vs_robustness.meta.json" in names

    manifest = json.loads(
        (Path(run_dir) / "paper_assets" / "paper_assets_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["assessment"]["engineering_only"] is True
    assert manifest["scope"] == "engineering_only_scaffold"

    sidecar = json.loads(
        (Path(run_dir) / "paper_assets" / "tables" / "table1_benchmark_statistics.meta.json").read_text(
            encoding="utf-8"
        )
    )
    assert "caption" in sidecar
    assert "config=" in sidecar["caption"]


def test_canonical_figures_generated(tmp_path):
    data = load_run_results(_smoke_run(tmp_path))
    paths = build_all_figures(data, tmp_path / "figures")
    names = {path.name for path in paths}
    assert "figure3_intervention_family_degradation.png" in names
    assert "figure5_cost_vs_robustness.pdf" in names
    assert "figure6_trajectory_failure_taxonomy.png" in names


def test_oracle_only_run_rejected(tmp_path):
    config = ExperimentConfig.model_validate(
        {
            "seed": 3,
            "run_name": "oracle_only_smoke",
            "benchmark_path": "data/sample/instances.jsonl",
            "agents": ["scripted_oracle_agent"],
            "max_steps": 4,
            "num_repeats": 1,
            "output_dir": str(tmp_path),
            "auto_score": True,
        }
    )
    run_dir = run_experiment(config)["run_dir"]
    assessment = assess_run_for_paper_assets(load_run_results(run_dir))
    assert assessment["oracle_only"] is True
    with pytest.raises(ValueError, match="oracle"):
        export_paper_assets(run_dir, write_global=False, allow_engineering_only=True)
