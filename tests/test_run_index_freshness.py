"""Fixture-only tests for stale run-index detection (no runs, no providers).

These guard the Section A inventory-freshness contract: reports must notice when
the persisted ``RUN_INDEX.jsonl`` undercounts (or overcounts) the live results
tree, while never marking a run eligible or mutating ``results/``.
"""

from __future__ import annotations

import json
from pathlib import Path

from causal_agent_bench.safety.common import (
    compute_run_index_freshness,
    scan_live_run_dirs,
)
from causal_agent_bench.safety.evidence_dashboard import build_evidence_dashboard
from causal_agent_bench.safety.report_quality_check import build_report_quality_check
from causal_agent_bench.safety.run_health import build_run_health_report


def _make_run(results: Path, name: str, metadata: dict) -> Path:
    run_dir = results / name
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "run_metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
    (run_dir / "checkpoint.json").write_text(
        json.dumps({"completed": 1, "total": 1, "status": "complete"}), encoding="utf-8"
    )
    return run_dir


def _stub_meta(name: str) -> dict:
    return {
        "run_name": name,
        "config_hash": "h",
        "evidence_scope": "pilot_stub_engineering_only",
        "provider_type": "stub",
        "scientific_evidence": False,
        "agents": ["stub_agent"],
        "n_instances": 1,
    }


def _write_index(results: Path, run_ids: list[str]) -> None:
    lines = []
    for run_id in run_ids:
        lines.append(json.dumps({"run_id": run_id, "path": str(results / run_id)}, sort_keys=True))
    (results / "RUN_INDEX.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_freshness_detects_unindexed_live_runs(tmp_path: Path) -> None:
    results = tmp_path / "results"
    for name in ("run_a", "run_b", "run_c"):
        _make_run(results, name, _stub_meta(name))
    # Only two of the three live runs are indexed -> stale, one un-indexed.
    _write_index(results, ["run_a", "run_b"])

    fresh = compute_run_index_freshness(tmp_path)
    assert fresh["index_stale"] is True
    assert fresh["live_run_count"] == 3
    assert fresh["indexed_run_count"] == 2
    assert fresh["unindexed_run_count"] == 1
    assert fresh["unindexed_run_ids"] == ["run_c"]
    # Refreshing the index is inventory-only: no stub run can be paper-eligible.
    assert fresh["unindexed_paper_eligible_count"] == 0


def test_freshness_reports_fresh_when_index_matches(tmp_path: Path) -> None:
    results = tmp_path / "results"
    for name in ("run_a", "run_b"):
        _make_run(results, name, _stub_meta(name))
    _write_index(results, ["run_a", "run_b"])

    fresh = compute_run_index_freshness(tmp_path)
    assert fresh["index_stale"] is False
    assert fresh["unindexed_run_count"] == 0
    assert fresh["orphaned_index_run_count"] == 0


def test_freshness_detects_orphaned_index_entries(tmp_path: Path) -> None:
    results = tmp_path / "results"
    _make_run(results, "run_a", _stub_meta("run_a"))
    # Index references a run directory that no longer exists on disk.
    _write_index(results, ["run_a", "ghost_run"])

    fresh = compute_run_index_freshness(tmp_path)
    assert fresh["index_stale"] is True
    assert fresh["orphaned_index_run_count"] == 1
    assert fresh["orphaned_index_run_ids"] == ["ghost_run"]


def test_scan_live_run_dirs_ignores_cache_and_unmarked(tmp_path: Path) -> None:
    results = tmp_path / "results"
    _make_run(results, "real_run", _stub_meta("real_run"))
    (results / "cache").mkdir(parents=True, exist_ok=True)
    (results / "dry_runs").mkdir(parents=True, exist_ok=True)
    (results / "no_metadata_dir").mkdir(parents=True, exist_ok=True)

    live = scan_live_run_dirs(tmp_path)
    assert live == ["real_run"]


def test_run_health_surfaces_stale_index_warning(tmp_path: Path) -> None:
    results = tmp_path / "results"
    for name in ("run_a", "run_b", "run_c"):
        _make_run(results, name, _stub_meta(name))
    _write_index(results, ["run_a"])

    report = build_run_health_report(tmp_path, output_dir=tmp_path / "reports")
    summary = report["summary"]
    assert summary["index_stale"] is True
    assert summary["live_run_count"] == 3
    assert summary["indexed_run_count"] == 1
    assert summary["unindexed_paper_eligible_count"] == 0
    assert any("STALE RUN INDEX" in warning for warning in summary["warnings"])
    # Inventory freshness block is persisted for downstream consumers.
    assert report["run_index_freshness"]["unindexed_run_count"] == 2


def test_run_health_no_warning_when_fresh(tmp_path: Path) -> None:
    results = tmp_path / "results"
    _make_run(results, "run_a", _stub_meta("run_a"))
    _write_index(results, ["run_a"])

    report = build_run_health_report(tmp_path, output_dir=tmp_path / "reports")
    assert report["summary"]["index_stale"] is False
    assert not any("STALE RUN INDEX" in warning for warning in report["summary"]["warnings"])


def test_report_quality_flags_stale_index(tmp_path: Path) -> None:
    results = tmp_path / "results"
    for name in ("run_a", "run_b"):
        _make_run(results, name, _stub_meta(name))
    _write_index(results, ["run_a"])
    reports = tmp_path / "reports"
    build_run_health_report(tmp_path, output_dir=reports)

    quality = build_report_quality_check(tmp_path, input_dir=reports, output_dir=tmp_path / "rq")
    check_ids = {check["id"] for check in quality["checks"]}
    assert "stale_run_index" in check_ids


def test_dashboard_marks_stale_run_health_needs_review(tmp_path: Path) -> None:
    results = tmp_path / "results"
    for name in ("run_a", "run_b"):
        _make_run(results, name, _stub_meta(name))
    _write_index(results, ["run_a"])
    reports = tmp_path / "reports"
    build_run_health_report(tmp_path, output_dir=reports)

    dashboard = build_evidence_dashboard(tmp_path, reports_dir=reports, output_dir=tmp_path / "dash")
    run_health_entry = dashboard["reports"]["run_health"]
    assert run_health_entry["badge"] == "needs_review"
    assert "STALE INDEX" in run_health_entry["summary"]


def test_freshness_does_not_mutate_results(tmp_path: Path) -> None:
    results = tmp_path / "results"
    _make_run(results, "run_a", _stub_meta("run_a"))
    _make_run(results, "run_b", _stub_meta("run_b"))
    _write_index(results, ["run_a"])
    before = {p.name for p in results.iterdir()}

    compute_run_index_freshness(tmp_path)

    after = {p.name for p in results.iterdir()}
    # No index regeneration, no new files, nothing removed.
    assert before == after
    index_lines = (results / "RUN_INDEX.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(index_lines) == 1
