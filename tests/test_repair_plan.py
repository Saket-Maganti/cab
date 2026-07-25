from __future__ import annotations

import json
from pathlib import Path

from causal_agent_bench.safety.repair_plan import build_repair_plan


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _minimal_reports(reports: Path) -> None:
    _write(reports / "benchmark_quality_report.json", {"issues": []})
    _write(reports / "intervention_isolation_report.json", {"pairs": []})
    _write(reports / "dataset_issue_triage.json", {"issues": []})
    _write(reports / "provider_pilot_preflight.json", {"checks": []})
    _write(reports / "release_readiness_report.json", {"checks": []})
    _write(reports / "config_metadata_lint.json", {"issues": [], "issue_count": 0})
    _write(reports / "paper_todo_inventory.json", {"items": []})
    _write(
        reports / "claim_evidence_matrix.json",
        {"claims": [{"claim_id": f"C{i}", "status": "supported"} for i in range(1, 9)] + [{"claim_id": "C9", "status": "engineering_only"}, {"claim_id": "C10", "status": "supported"}]},
    )


def test_missing_input_reports_does_not_crash(tmp_path: Path) -> None:
    report = build_repair_plan(tmp_path, input_dir=tmp_path / "missing", output_dir=tmp_path / "out")
    assert report["summary"]["missing_report_count"] > 0
    assert report["items"]
    assert Path(report["output_paths"]["json"]).exists()
    assert "all-no-run-reports" in report["recommendation_if_missing"]


def test_combines_fixture_report_issues_into_ranked_plan(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    _minimal_reports(reports)
    _write(
        reports / "benchmark_quality_report.json",
        {"issues": [{"id": "missing_expected_output", "severity": "blocker", "dataset": "data/x", "message": "Task task_1 has no expected output"}]},
    )
    _write(
        reports / "provider_pilot_preflight.json",
        {"checks": [{"id": "approval_marker_present", "severity": "blocker", "message": "Approval marker missing."}]},
    )
    _write(reports / "paper_todo_inventory.json", {"items": [{"id": "todo_1", "path": "paper/x.tex", "text": "TODO"}]})
    report = build_repair_plan(tmp_path, input_dir=reports, output_dir=tmp_path / "plan")
    assert report["summary"]["repair_item_count"] >= 3
    assert report["items"][0]["readiness_gate"] == "must_fix_before_provider_pilot"
    assert report["groups"]["should_fix_for_paper_clarity"]


def test_provider_pilot_blockers_rank_above_nice_to_have(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    _minimal_reports(reports)
    _write(
        reports / "provider_pilot_preflight.json",
        {"checks": [{"id": "budget_cap_present", "severity": "blocker", "message": "Budget cap missing."}]},
    )
    _write(reports / "paper_todo_inventory.json", {"items": [{"id": "clarity", "path": "paper/a.tex", "text": "clarify"}]})
    report = build_repair_plan(tmp_path, input_dir=reports, output_dir=tmp_path / "plan")
    top = report["items"][0]
    assert top["source_report"] == "provider_pilot_preflight.json"
    assert top["readiness_gate"] == "must_fix_before_provider_pilot"


def test_stable_repair_ids(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    _minimal_reports(reports)
    _write(
        reports / "config_metadata_lint.json",
        {"issues": [{"id": "allow_paid_calls_missing", "severity": "blocker", "path": "configs/x.yaml", "message": "missing"}]},
    )
    first = build_repair_plan(tmp_path, input_dir=reports, output_dir=tmp_path / "one")
    second = build_repair_plan(tmp_path, input_dir=reports, output_dir=tmp_path / "two")
    assert [row["repair_id"] for row in first["items"]] == [row["repair_id"] for row in second["items"]]


def test_output_markdown_and_json_generated_without_provider_calls(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    _minimal_reports(reports)
    report = build_repair_plan(tmp_path, input_dir=reports, output_dir=tmp_path / "plan")
    assert Path(report["output_paths"]["markdown"]).exists()
    assert Path(report["output_paths"]["json"]).exists()
    assert "no benchmark run, provider call, model call" in report["scope"]


def test_repeated_fixture_issues_cluster_into_one_root_cause(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    _minimal_reports(reports)
    _write(
        reports / "benchmark_quality_report.json",
        {
            "issues": [
                {
                    "id": "missing_expected_output",
                    "severity": "blocker",
                    "dataset": "data/processed/tiny",
                    "message": f"Task task_{index} has no expected output",
                }
                for index in range(75)
            ]
        },
    )
    report = build_repair_plan(tmp_path, input_dir=reports, output_dir=tmp_path / "plan")
    matching = [row for row in report["root_causes"] if row["source_issue_id"] == "gold_output"]
    assert matching
    assert max(row["symptom_count"] for row in matching) > 1
    assert len(report["top_50_actionable_repairs"]) < report["summary"]["raw_repair_item_count"]
    assert report["raw_items"]


def test_root_cause_ids_are_stable(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    _minimal_reports(reports)
    issues = [
        {
            "id": "missing_expected_output",
            "severity": "blocker",
            "dataset": "data/processed/tiny",
            "message": f"Task task_{index} has no expected output",
        }
        for index in range(3)
    ]
    _write(reports / "benchmark_quality_report.json", {"issues": issues})
    first = build_repair_plan(tmp_path, input_dir=reports, output_dir=tmp_path / "one")
    second = build_repair_plan(tmp_path, input_dir=reports, output_dir=tmp_path / "two")
    assert [row["root_cause_id"] for row in first["root_causes"]] == [row["root_cause_id"] for row in second["root_causes"]]


def test_top_provider_pilot_blockers_are_separate_from_public_release(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    _minimal_reports(reports)
    _write(
        reports / "provider_pilot_preflight.json",
        {"checks": [{"id": "budget_cap_present", "severity": "blocker", "message": "Budget cap missing."}]},
    )
    _write(
        reports / "release_readiness_report.json",
        {"checks": [{"name": "license_docs", "severity": "warning", "message": "Document license before release."}]},
    )
    report = build_repair_plan(tmp_path, input_dir=reports, output_dir=tmp_path / "plan")
    assert report["top_10_provider_pilot_blockers"]
    assert report["top_10_provider_pilot_blockers"][0]["readiness_gate"] == "must_fix_before_provider_pilot"
    assert report["top_10_provider_pilot_blockers"][0]["rank"] < report["root_causes"][-1]["rank"]


def test_provider_template_approval_noise_groups_into_one_root_cause(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    _minimal_reports(reports)
    _write(
        reports / "provider_pilot_preflight.json",
        {
            "gate_status": "template_safe_but_not_runnable",
            "config_path": "configs/provider_pilot_tiny_template.yaml",
            "checks": [
                {"id": "template_not_runnable", "severity": "warning", "message": "Template config is safe for static review but must not be run."},
                {"id": "approved_copy_required", "severity": "warning", "message": "Create a separate APPROVED copy only after advisor approval."},
                {"id": "approved_copy_name", "severity": "warning", "message": "Config path or run_name should clearly be an APPROVED copy."},
                {"id": "model_placeholder_unresolved", "severity": "warning", "message": "Model placeholder unresolved in template."},
            ],
        },
    )
    report = build_repair_plan(tmp_path, input_dir=reports, output_dir=tmp_path / "plan")
    grouped = [
        row
        for row in report["root_causes"]
        if row["source_issue_id"] == "config" and "not approved yet" in row["recommended_root_fix"]
    ]
    assert grouped
    assert grouped[0]["symptom_count"] == 4


def test_leakage_false_positive_candidate_not_top_provider_blocker(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    _minimal_reports(reports)
    _write(
        reports / "dataset_issue_triage.json",
        {
            "issues": [],
            "leakage_root_causes": [
                {
                    "root_cause_id": "leak_false",
                    "root_cause_title": "shared tool description",
                    "finding_type": "near_duplicate_prompt",
                    "severity": "informational",
                    "cluster_classification": "shared_tool_description",
                    "leakage_risk": "false_positive_candidate",
                    "symptom_count": 1000,
                    "readiness_gate": "must_fix_before_provider_pilot",
                    "recommended_action": "Review representative boilerplate examples.",
                },
                {
                    "root_cause_id": "leak_answer",
                    "root_cause_title": "answer leakage",
                    "finding_type": "answer_text_leakage",
                    "severity": "blocker",
                    "cluster_classification": "answer_leakage",
                    "leakage_risk": "blocker",
                    "symptom_count": 2,
                    "readiness_gate": "must_fix_before_provider_pilot",
                    "recommended_action": "Remove answer leakage.",
                },
            ],
        },
    )
    report = build_repair_plan(tmp_path, input_dir=reports, output_dir=tmp_path / "plan")
    assert report["top_10_provider_pilot_blockers"]
    assert report["top_10_provider_pilot_blockers"][0]["cluster_classification"] == "answer_leakage"
    assert all(row.get("cluster_classification") != "shared_tool_description" for row in report["top_10_provider_pilot_blockers"])
    assert report["false_positive_candidate_repairs"]


def test_duplicate_id_and_answer_leakage_rank_high(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    _minimal_reports(reports)
    _write(
        reports / "dataset_issue_triage.json",
        {
            "issues": [],
            "leakage_root_causes": [
                {
                    "root_cause_id": "leak_near",
                    "root_cause_title": "boilerplate near duplicate",
                    "finding_type": "near_duplicate_prompt",
                    "severity": "warning",
                    "cluster_classification": "task_family_boilerplate",
                    "leakage_risk": "false_positive_candidate",
                    "symptom_count": 900,
                    "readiness_gate": "must_fix_before_provider_pilot",
                    "recommended_action": "Review boilerplate.",
                },
                {
                    "root_cause_id": "leak_dup",
                    "root_cause_title": "duplicate IDs",
                    "finding_type": "duplicate_instance_id",
                    "severity": "blocker",
                    "cluster_classification": "duplicate_id_leakage",
                    "leakage_risk": "blocker",
                    "symptom_count": 3,
                    "readiness_gate": "must_fix_before_provider_pilot",
                    "recommended_action": "Repair split IDs.",
                },
            ],
        },
    )
    report = build_repair_plan(tmp_path, input_dir=reports, output_dir=tmp_path / "plan")
    assert report["top_10_provider_pilot_blockers"][0]["cluster_classification"] == "duplicate_id_leakage"
