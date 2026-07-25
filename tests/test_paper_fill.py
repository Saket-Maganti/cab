"""Integration tests that start local benchmark runs via run_experiment.

Excluded from strict no-run validation — see docs/NO_RUN_VALIDATION.md.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from causal_agent_bench.analysis.paper_fill import (
    fill_paper_from_run,
    verify_run_for_paper_fill,
)
from causal_agent_bench.runners.config import ExperimentConfig
from causal_agent_bench.runners.experiment import run_experiment

pytestmark = [pytest.mark.integration, pytest.mark.local_run]


def _sample_run(tmp_path: Path, repo: Path) -> Path:
    config = ExperimentConfig.model_validate(
        {
            "seed": 99,
            "run_name": "paper_fill_smoke",
            "benchmark_path": str(repo / "data/sample/instances.jsonl"),
            "agents": ["random_tool_agent", "scripted_oracle_agent"],
            "max_steps": 6,
            "num_repeats": 1,
            "output_dir": str(tmp_path),
            "auto_score": True,
        }
    )
    return run_experiment(config)["run_dir"]


def test_verify_run_rejects_stub_without_flag(tmp_path):
    from causal_agent_bench.analysis.load_results import load_run_results

    repo = Path(__file__).resolve().parents[1]
    run_dir = _sample_run(tmp_path, repo)
    data = load_run_results(run_dir)
    report = verify_run_for_paper_fill(data, allow_engineering_only=False)
    assert report.passed is False
    assert any("engineering-only" in error for error in report.errors)


def test_fill_paper_engineering_preview(tmp_path):
    repo = Path(__file__).resolve().parents[1]
    test_repo = tmp_path / "repo"
    (test_repo / "docs").mkdir(parents=True)
    (test_repo / "paper" / "latexpaper" / "generated").mkdir(parents=True)
    (test_repo / "docs" / "claim_ledger.json").write_text(
        (repo / "docs" / "claim_ledger.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    run_dir = _sample_run(tmp_path / "runs", repo)
    report = fill_paper_from_run(
        run_dir,
        repo_root=test_repo,
        allow_engineering_only=True,
        allow_mock_stub=True,
        export_assets=False,
        write_global_tables=False,
        update_ledger=True,
    )
    assert report["filled"] is True
    abstract = (test_repo / "paper" / "latexpaper" / "generated" / "00_abstract.tex").read_text(
        encoding="utf-8"
    )
    assert "[N]" not in abstract
    assert "engineering-only pilot" in abstract or "pilot" in abstract

    mapping = json.loads((test_repo / "docs" / "PAPER_EVIDENCE_MAPPING.json").read_text(encoding="utf-8"))
    assert mapping["run_dir"]
    assert mapping["config_hash"]


def test_fill_paper_requires_existing_run(tmp_path):
    with pytest.raises(ValueError, match=r"does not exist|verification failed"):
        fill_paper_from_run(
            tmp_path / "missing_run",
            repo_root=tmp_path,
            allow_engineering_only=True,
            export_assets=False,
            update_ledger=False,
        )
