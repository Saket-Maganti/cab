from __future__ import annotations

import json
import subprocess
from pathlib import Path

from causal_agent_bench.safety.benchmark_manifest import build_benchmark_manifest


def _repo(tmp_path: Path) -> Path:
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname='cab-fixture'\nversion='0.2.0'\nrequires-python='>=3.11'\n",
        encoding="utf-8",
    )
    data = tmp_path / "data/processed/tiny"
    data.mkdir(parents=True)
    (data / "instances.jsonl").write_text('{"instance_id":"task_1.clean"}\n', encoding="utf-8")
    (tmp_path / "results").mkdir()
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/claim_ledger.json").write_text(
        json.dumps({"claims": [{"claim_id": "C1", "status": "planned"}, {"claim_id": "C9", "status": "engineering_only"}, {"claim_id": "C10", "status": "planned"}]}),
        encoding="utf-8",
    )
    return tmp_path


def test_fixture_repo_metadata_parsed(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    report = build_benchmark_manifest(repo, output_dir=repo / "manifest")
    assert report["package"]["pyproject_name"] == "cab-fixture"
    assert report["package"]["pyproject_version"] == "0.2.0"
    assert report["data_directories"]


def test_dirty_tree_warning(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    (repo / "dirty.txt").write_text("dirty", encoding="utf-8")
    report = build_benchmark_manifest(repo, output_dir=repo / "manifest")
    assert report["repository"]["dirty_tree_count"] >= 1
    assert any(check["id"] == "dirty_tree_for_release" for check in report["checks"])


def test_missing_lockfile_warning(tmp_path: Path) -> None:
    report = build_benchmark_manifest(_repo(tmp_path), output_dir=tmp_path / "manifest")
    assert report["lockfile_status"]["present"] is False
    assert any(check["id"] == "missing_lockfile" for check in report["checks"])


def test_no_eligible_runs_blocks_empirical_readiness(tmp_path: Path) -> None:
    report = build_benchmark_manifest(_repo(tmp_path), output_dir=tmp_path / "manifest")
    assert report["readiness"]["empirical_paper_blocked"] is True
    assert any(check["id"] == "no_eligible_runs" for check in report["checks"])


def test_output_generated(tmp_path: Path) -> None:
    report = build_benchmark_manifest(_repo(tmp_path), output_dir=tmp_path / "manifest")
    assert Path(report["report_paths"]["json"]).exists()
    assert Path(report["report_paths"]["markdown"]).exists()
