from __future__ import annotations

import json
from pathlib import Path

import yaml

from causal_agent_bench.phase2 import validate_config_file
from causal_agent_bench.runners.plan_run import plan_run
from causal_agent_bench.safety.provider_pilot_preflight import validate_provider_pilot_preflight
from causal_agent_bench.safety.run_cost_estimator import estimate_run_cost


def _repo(tmp_path: Path) -> Path:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/POST_PROVIDER_PILOT_CHECKLIST.md").write_text("checklist", encoding="utf-8")
    (tmp_path / "data").mkdir()
    (tmp_path / "data/instances.jsonl").write_text(json.dumps({"instance_id": "i1"}) + "\n", encoding="utf-8")
    return tmp_path


def _config(tmp_path: Path, name: str, updates: dict | None = None) -> Path:
    is_template = "template" in name.lower()
    raw = {
        "run_name": name.replace(".yaml", ""),
        "benchmark_path": "data/instances.jsonl",
        "allow_paid_calls": False,
        "budget_cap_usd": 5.0,
        "evidence_scope": "provider_pilot_pending_verification",
        "scientific_evidence": False,
        "require_dry_run_before_live": True,
        "max_instances": 2,
        "limits": {
            "max_trajectories": 2,
            "stop_after_trajectories": 2,
            "max_runtime_minutes": 10,
            "max_steps_per_instance": 4,
        },
        "agent_runs": [{"agent": "direct_tool_agent", "provider": "openai", "model": "${OPENAI_MODEL_ID}"}],
        "approval": (
            {
                "advisor_approved": False,
                "budget_approved": False,
                "approved_for_dry_run": False,
                "approved_for_live_run": False,
                "approved_by": None,
                "approval_date": None,
                "advisor_approval_id": None,
                "max_budget_usd": 5,
                "notes": "TEMPLATE ONLY",
            }
            if is_template
            else {
                "advisor_approved": True,
                "budget_approved": True,
                "approved_for_dry_run": True,
                "approved_for_live_run": False,
                "approved_by": "advisor",
                "approval_date": "2026-06-04",
                "advisor_approval_id": "ADV-TEST-001",
                "max_budget_usd": 5,
            }
        ),
    }
    if updates:
        raw.update(updates)
    path = tmp_path / name
    path.write_text(yaml.safe_dump(raw), encoding="utf-8")
    return path


def _ids(report: dict) -> set[str]:
    return {check["id"] for check in report["checks"] if check["severity"] == "blocker"}


def test_template_blocked(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    report = validate_provider_pilot_preflight(_config(repo, "provider_pilot_tiny_template.yaml"), repo_root=repo)
    assert report["verdicts"]["ready_for_dry_run"] is False
    assert report["verdicts"]["ready_for_live_provider_run"] is False
    assert "config_is_not_template" not in _ids(report)
    assert report["gate_summary"]["gate_status"] == "template_safe_but_not_runnable"
    assert report["verdicts"]["template_safe_but_not_runnable"] is True
    assert report["verdicts"]["blocked"] is False
    assert "Create an approved provider-pilot config copy" in report["gate_summary"]["exact_next_action"]


def test_real_template_has_caps_budget_and_false_approval() -> None:
    path = Path("configs/provider_pilot_tiny_template.yaml")
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert raw["allow_paid_calls"] is False
    assert raw["budget_cap_usd"] <= 5
    assert raw["limits"]["max_trajectories"] <= 5
    assert raw["limits"]["stop_after_trajectories"] <= 5
    assert raw["limits"]["max_runtime_minutes"] <= 30
    assert raw["approval"]["advisor_approved"] is False
    assert raw["approval"]["budget_approved"] is False
    assert raw["scientific_evidence"] is False
    assert raw["template_only"] is True
    assert raw["evidence_scope"] == "provider_pilot_pending_verification"


def test_real_approved_config_ready_for_dry_run_not_live() -> None:
    path = Path("configs/provider_pilot_tiny_APPROVED.yaml")
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    report = validate_provider_pilot_preflight(path, repo_root=Path("."))
    assert raw["allow_paid_calls"] is False
    assert raw["approval"]["approved_for_dry_run"] is True
    assert raw["approval"]["approved_for_live_run"] is False
    assert raw["evidence_scope"] == "provider_pilot_debug_or_preliminary"
    assert raw["budget"]["max_calls"] <= 30
    assert raw["limits"]["max_trajectories"] <= 5
    assert report["gate_status"] == "ready_for_dry_run"
    assert report["verdicts"]["ready_for_dry_run"] is True
    assert report["verdicts"]["ready_for_live_provider_run"] is False


def test_missing_budget_blocked(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    report = validate_provider_pilot_preflight(_config(repo, "provider_pilot_APPROVED.yaml", {"budget_cap_usd": None}), repo_root=repo)
    assert "budget_cap_present" in _ids(report)
    assert report["gate_summary"]["gate_status"] == "blocked"
    assert "budget cap" in report["gate_summary"]["exact_next_action"]


def test_local_provider_blocked(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    report = validate_provider_pilot_preflight(
        _config(repo, "provider_pilot_APPROVED.yaml", {"agent_runs": [{"agent": "direct_tool_agent", "provider": "local_stub", "model": "none"}]}),
        repo_root=repo,
    )
    assert "provider_backed_family" in _ids(report)


def test_oracle_agent_blocked(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    report = validate_provider_pilot_preflight(
        _config(repo, "provider_pilot_APPROVED.yaml", {"agent_runs": [{"agent": "scripted_oracle_agent", "provider": "openai", "model": "${OPENAI_MODEL_ID}"}]}),
        repo_root=repo,
    )
    assert "non_evidence_agent" in _ids(report)


def test_valid_approved_fixture_ready_for_dry_run(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    report = validate_provider_pilot_preflight(
        _config(
            repo,
            "provider_pilot_APPROVED.yaml",
            {
                "approval": {
                    "advisor_approved": True,
                    "budget_approved": True,
                    "approved_for_dry_run": True,
                    "approved_by": "advisor",
                    "approval_date": "2026-05-26",
                    "max_budget_usd": 5,
                }
            },
        ),
        repo_root=repo,
    )
    assert report["verdicts"]["ready_for_dry_run"] is True
    assert report["verdicts"]["ready_for_live_provider_run"] is False
    assert report["verdicts"]["blocked"] is False
    assert report["gate_summary"]["gate_status"] == "ready_for_dry_run"


def test_approved_fixture_requires_approval_markers(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    report = validate_provider_pilot_preflight(
        _config(
            repo,
            "provider_pilot_APPROVED.yaml",
            {
                "approval": {
                    "advisor_approved": False,
                    "budget_approved": False,
                    "approved_for_dry_run": False,
                    "approved_for_live_run": False,
                    "approved_by": None,
                    "approval_date": None,
                    "advisor_approval_id": None,
                    "max_budget_usd": 5,
                }
            },
        ),
        repo_root=repo,
    )
    assert "approval_marker_present" in _ids(report)
    assert report["verdicts"]["ready_for_dry_run"] is False
    assert report["gate_summary"]["gate_status"] == "blocked"


def test_approved_fixture_keeps_paid_calls_disabled(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    path = _config(repo, "provider_pilot_APPROVED.yaml")
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    report = validate_provider_pilot_preflight(path, repo_root=repo)
    assert raw["allow_paid_calls"] is False
    assert report["verdicts"]["ready_for_dry_run"] is True
    assert report["verdicts"]["ready_for_live_provider_run"] is False


def test_approved_fixture_rejects_api_keys_in_yaml(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    report = validate_provider_pilot_preflight(
        _config(repo, "provider_pilot_APPROVED.yaml", {"api_key": "placeholder-secret-should-never-be-here"}),
        repo_root=repo,
    )
    assert "api_key_in_config" in _ids(report)
    assert report["gate_summary"]["gate_status"] == "blocked"


def test_approved_fixture_cannot_support_scientific_claims(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    report = validate_provider_pilot_preflight(
        _config(
            repo,
            "provider_pilot_APPROVED.yaml",
            {
                "scientific_evidence": True,
                "scientific_evidence_level": "paper_eligible",
            },
        ),
        repo_root=repo,
    )
    blockers = _ids(report)
    assert "scientific_evidence_false_before_run" in blockers
    assert "scientific_evidence_level_too_strong" in blockers


def test_approved_fixture_caps_tiny_trajectories(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    path = _config(repo, "provider_pilot_APPROVED.yaml")
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert raw["max_instances"] <= 5
    assert raw["limits"]["max_trajectories"] <= 5
    assert raw["limits"]["stop_after_trajectories"] <= 5


def test_approved_fixture_validate_plan_and_estimate_pass(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    path = _config(
        repo,
        "provider_pilot_APPROVED.yaml",
        {
            "benchmark_path": str(Path("data/sample/instances.jsonl").resolve()),
            "agent_runs": [
                {
                    "agent": "direct_tool_agent",
                    "name": "direct_tool_provider_pilot",
                    "provider": "openai",
                    "model": "gpt-4o-mini",
                    "max_tokens": 128,
                    "pricing": {
                        "input_per_1m_tokens": 0.15,
                        "output_per_1m_tokens": 0.6,
                    },
                    "extra": {"input_tokens_per_call_estimate": 100},
                }
            ],
        },
    )

    validation = validate_config_file(path)
    plan = plan_run(path)
    estimate = estimate_run_cost(path, repo_root=repo)

    assert validation["valid"] is True
    assert plan["allow_paid_calls"] is False
    assert plan["expected_trajectories"] <= 5
    assert estimate["allow_paid_calls"] is False
    assert estimate["number_of_trajectories"] <= 5
    assert estimate["budget_cap_usd"] <= 5
    assert estimate["pricing_known"] is True


def test_live_run_never_true_without_explicit_live_approval_marker(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    report = validate_provider_pilot_preflight(
        _config(repo, "provider_pilot_APPROVED.yaml", {"allow_paid_calls": True}),
        repo_root=repo,
    )
    assert report["verdicts"]["ready_for_dry_run"] is True
    assert report["verdicts"]["ready_for_live_provider_run"] is False
    assert report["gate_summary"]["gate_status"] == "ready_for_dry_run"


def test_leakage_blockers_keep_gate_blocked(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    reports = tmp_path / "reports"
    leakage_dir = reports / "static_leakage"
    leakage_dir.mkdir(parents=True)
    (leakage_dir / "static_leakage_report.json").write_text(
        '{"summary": {"blocker_cluster_count": 2}}',
        encoding="utf-8",
    )
    report = validate_provider_pilot_preflight(
        _config(repo, "provider_pilot_APPROVED.yaml"),
        repo_root=repo,
        reports_dir=reports,
    )
    assert report["gate_summary"]["gate_status"] == "blocked"
    assert report["verdicts"]["ready_for_dry_run"] is False
    assert "leakage_repair_must_fix" in _ids(report) or "answer_leakage_blockers" in _ids(report)


def test_template_cannot_be_live_run_ready(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    report = validate_provider_pilot_preflight(_config(repo, "provider_pilot_tiny_template.yaml"), repo_root=repo)
    assert report["verdicts"]["ready_for_live_provider_run"] is False
    assert report["gate_summary"]["gate_status"] != "ready_for_live_run"
