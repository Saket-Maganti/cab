"""Phase 2 build-mode tests — fast, no model calls."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from causal_agent_bench.runners.audit_dataset import audit_dataset
from causal_agent_bench.runners.compare_runs import compare_runs
from causal_agent_bench.runners.config import ExperimentConfig
from causal_agent_bench.runners.experiment import run_experiment
from causal_agent_bench.runners.failure_gallery_report import write_failure_gallery
from causal_agent_bench.runners.generate_report import build_run_report, write_run_report

REPO = Path(__file__).resolve().parents[1]


def test_compare_runs_missing_metrics(tmp_path):
    a = run_experiment(_micro_config(tmp_path))
    b = run_experiment(_micro_config(tmp_path))
    comparison = compare_runs(a["run_dir"], b["run_dir"])
    assert comparison["metrics_available"]["a"] is False


def test_issue_templates_exist():
    templates = REPO / ".github" / "ISSUE_TEMPLATE"
    for name in ("bug_report.md", "experiment_task.md", "paper_task.md", "reviewer_risk.md", "config.yml"):
        assert (templates / name).exists()


def test_experiment_registry_exists():
    assert (REPO / "experiments" / "EXPERIMENT_REGISTRY.md").exists()


def test_generate_report_incomplete_run(tmp_path):
    result = run_experiment(_micro_config(tmp_path, limits={"stop_after_trajectories": 1}))
    report = build_run_report(result["run_dir"])
    assert report["claim_usability"]["usable_for_final_claims"] is False


def _micro_config(tmp_path, limits=None):
    payload = {
        "seed": 1,
        "run_name": "phase2_micro",
        "benchmark_path": "data/processed/pilot_v0_1/pilot_20_instances.jsonl",
        "max_instances": 2,
        "budget": {"max_total_usd": 0, "max_calls": 10, "require_explicit_paid_approval": True, "strict_pricing": False},
        "agent_runs": [{"name": "mock", "agent": "mock_behavior_agent", "extra": {"mock_behavior": "helpful"}}],
        "max_steps": 2,
        "auto_score": False,
        "output_dir": str(tmp_path),
    }
    if limits:
        payload["limits"] = limits
    return ExperimentConfig.model_validate(payload)


def test_generate_report_on_mock_run(tmp_path):
    result = run_experiment(_micro_config(tmp_path))
    paths = write_run_report(result["run_dir"], include_html=True)
    assert paths["markdown"].exists()
    assert paths["json"].exists()
    assert paths["html"].exists()
    report = build_run_report(result["run_dir"])
    assert report["claim_usability"]["engineering_or_preliminary_only"] is True


def test_failure_gallery_on_mock_run(tmp_path):
    result = run_experiment(_micro_config(tmp_path))
    paths = write_failure_gallery(result["run_dir"])
    payload = json.loads(paths["json"].read_text(encoding="utf-8"))
    assert "engineering" in payload["evidence_label"] or payload["evidence_label"].startswith("preliminary")


def test_compare_runs(tmp_path):
    a = run_experiment(_micro_config(tmp_path))
    b = run_experiment(_micro_config(tmp_path))
    comparison = compare_runs(a["run_dir"], b["run_dir"])
    assert "metric_diffs" in comparison


def test_audit_dataset_sample():
    report = audit_dataset("data/processed/pilot_v0_1/pilot_20_instances.jsonl")
    assert report["n_instances"] > 0
    assert "domain_distribution" in report


def test_submission_readiness_script():
    proc = subprocess.run(
        [sys.executable, "scripts/check_submission_readiness.py"],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    assert "classification:" in proc.stdout
    assert proc.returncode == 1


def test_validate_paper_assets_draft():
    proc = subprocess.run(
        [sys.executable, "scripts/validate_paper_assets.py", "--mode", "draft"],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    assert proc.returncode in {0, 1}


def test_cli_generate_report_help():
    proc = subprocess.run(
        [sys.executable, "-m", "causal_agent_bench", "generate-report", "--help"],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
