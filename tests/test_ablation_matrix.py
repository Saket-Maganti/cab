from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from causal_agent_bench.ablation_matrix import (
    AblationMatrixConfig,
    aggregate_ablation_matrix,
    build_cell_experiment_config,
    expand_matrix_cells,
    export_ablation_matrix_artifacts,
    load_ablation_matrix_config,
    plan_ablation_matrix,
    run_ablation_matrix,
)


def _minimal_matrix(**overrides) -> AblationMatrixConfig:
    payload = {
        "run_name": "pytest_matrix",
        "benchmark_path": "data/sample/instances.jsonl",
        "output_dir": "results/pytest_ablation_matrix",
        "strategy": "explicit",
        "factors": {
            "prompt_style": ["direct"],
            "self_check": ["off", "on"],
            "memory_verification": ["off"],
            "recovery_instruction": ["off"],
            "contradiction_instruction": ["off"],
            "uncertainty_instruction": ["off"],
        },
        "cells": [
            {
                "prompt_style": "direct",
                "self_check": "off",
                "memory_verification": "off",
                "recovery_instruction": "off",
                "contradiction_instruction": "off",
                "uncertainty_instruction": "off",
            },
            {
                "prompt_style": "direct",
                "self_check": "on",
                "memory_verification": "off",
                "recovery_instruction": "off",
                "contradiction_instruction": "off",
                "uncertainty_instruction": "off",
            },
        ],
        "safeguards": {
            "max_cells": 4,
            "max_estimated_cost_usd": 0.0,
            "require_dry_run_before_execute": False,
        },
    }
    payload.update(overrides)
    return AblationMatrixConfig.model_validate(payload)


def test_expand_baseline_plus_one():
    matrix = _minimal_matrix(strategy="baseline_plus_one")
    cells = expand_matrix_cells(matrix)
    assert len(cells) == 2
    assert cells[0]["self_check"] == "off"
    assert cells[1]["self_check"] == "on"


def test_plan_respects_max_cells(tmp_path):
    matrix = AblationMatrixConfig.model_validate(
        {
            "run_name": "too_big",
            "benchmark_path": "data/sample/instances.jsonl",
            "output_dir": str(tmp_path / "results"),
            "strategy": "full_factorial",
            "factors": {
                "prompt_style": ["direct", "react"],
                "self_check": ["off", "on"],
                "memory_verification": ["off", "on"],
                "recovery_instruction": ["off", "on"],
                "contradiction_instruction": ["off", "on"],
                "uncertainty_instruction": ["off", "on"],
            },
            "safeguards": {"max_cells": 4, "max_estimated_cost_usd": None},
        }
    )
    config_path = tmp_path / "matrix.yaml"
    config_path.write_text(yaml.safe_dump(matrix.model_dump()), encoding="utf-8")
    with pytest.raises(ValueError, match="max_cells"):
        plan_ablation_matrix(config_path, matrix_output_dir=tmp_path / "out")


def test_build_cell_unknown_level_raises():
    matrix = _minimal_matrix()
    with pytest.raises(ValueError, match="unknown level"):
        build_cell_experiment_config(
            matrix,
            {
                "prompt_style": "direct",
                "self_check": "bogus",
                "memory_verification": "off",
                "recovery_instruction": "off",
                "contradiction_instruction": "off",
                "uncertainty_instruction": "off",
            },
        )


def test_plan_writes_manifest_and_cell_configs(tmp_path):
    matrix = _minimal_matrix()
    config_path = tmp_path / "matrix.yaml"
    config_path.write_text(yaml.safe_dump(matrix.model_dump()), encoding="utf-8")
    out = tmp_path / "matrix_out"
    manifest = plan_ablation_matrix(config_path, matrix_output_dir=out)
    assert manifest["n_cells"] == 2
    assert (out / "matrix_manifest.json").exists()
    assert (out / "matrix_plan.md").exists()
    for cell in manifest["cells"]:
        assert Path(cell["config_path"]).exists()


def test_run_matrix_execute_local_stub(tmp_path):
    matrix = _minimal_matrix(output_dir=str(tmp_path / "results"))
    config_path = tmp_path / "matrix.yaml"
    config_path.write_text(yaml.safe_dump(matrix.model_dump()), encoding="utf-8")
    out = tmp_path / "matrix_out"
    manifest = run_ablation_matrix(
        config_path,
        execute=True,
        matrix_output_dir=out,
        skip_existing=False,
    )
    for cell in manifest["cells"]:
        assert cell.get("actual_run_dir")
    assert manifest.get("run_results")
    frame = aggregate_ablation_matrix(out)
    assert len(frame) == 2
    for column in [
        "clean_success",
        "intervention_success",
        "acrs",
        "estimated_cost_usd",
        "avg_latency_s",
        "tool_overuse",
    ]:
        assert column in frame.columns
    paths = export_ablation_matrix_artifacts(out, frame)
    assert any(path.name.endswith(".csv") for path in paths)
    assert (out / "exports" / "ablation_matrix_aggregate.json").exists()


def test_load_repo_example_config():
    path = Path("configs/ablation_matrix_local_stub.yaml")
    matrix = load_ablation_matrix_config(path)
    assert matrix.run_name == "ablation_matrix_local_stub"
    assert expand_matrix_cells(matrix)
