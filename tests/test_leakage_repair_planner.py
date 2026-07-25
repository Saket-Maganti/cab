from __future__ import annotations

import json
from pathlib import Path

from causal_agent_bench.safety.evidence_dashboard import build_evidence_dashboard
from causal_agent_bench.safety.leakage_repair_planner import (
    build_leakage_repair_plan,
    validate_leakage_patch_manifest,
)
from causal_agent_bench.safety.report_quality_check import build_report_quality_check


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _static_report(*clusters: dict) -> dict:
    counts: dict[str, int] = {}
    for cluster in clusters:
        name = cluster.get("cluster_classification", "needs_manual_review")
        counts[name] = counts.get(name, 0) + 1
    return {
        "summary": {
            "raw_finding_count": 2000,
            "cluster_count": len(clusters),
            "suppressed_symptom_count": 1990,
            "classification_counts": counts,
            "false_positive_candidate_count": counts.get("shared_tool_description", 0),
        },
        "root_causes": list(clusters),
        "top_clusters": list(clusters),
        "top_true_leakage_clusters": [
            row for row in clusters if row.get("leakage_risk") == "blocker"
        ],
        "manual_review_queue": [],
        "false_positive_candidates": [
            row for row in clusters if row.get("leakage_risk") == "false_positive_candidate"
        ],
    }


def _cluster(classification: str, **overrides: object) -> dict:
    base = {
        "root_cause_id": f"leak_root_{classification}",
        "root_cause_title": classification.replace("_", " "),
        "cluster_classification": classification,
        "leakage_risk": "blocker",
        "severity": "blocker",
        "symptom_count": 3,
        "affected_task_ids": ["task_1"],
        "affected_instance_ids": ["task_1.clean"],
        "affected_splits": ["pilot", "heldout"],
        "confidence": "high",
        "representative_examples": [
            {
                "finding_id": "leak_1",
                "entity_id": "task_1.clean::task_2.clean",
                "representative_snippet": "secret answer text",
            }
        ],
        "raw_finding_ids": ["leak_1", "leak_2"],
        "readiness_gate": "must_fix_before_provider_pilot",
    }
    base.update(overrides)
    return base


def test_duplicate_id_cluster_creates_rename_candidate(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    _write(reports / "static_leakage/static_leakage_report.json", _static_report(_cluster("duplicate_id_leakage")))
    report = build_leakage_repair_plan(tmp_path, input_dir=reports, output_dir=tmp_path / "plan")
    item = report["top_duplicate_id_repairs"][0]
    assert item["proposed_patch_type"] == "rename_duplicate_ids"
    assert item["safe_to_auto_patch"] is True
    manifest = json.loads(Path(report["patch_manifest_paths"]["json"]).read_text(encoding="utf-8"))
    assert manifest["operations"][0]["type"] == "rename_instance_id"
    assert manifest["operations"][0]["candidate_auto_patch"] is True


def test_answer_leakage_cluster_creates_manual_content_repair(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    _write(reports / "static_leakage/static_leakage_report.json", _static_report(_cluster("answer_leakage")))
    report = build_leakage_repair_plan(tmp_path, input_dir=reports, output_dir=tmp_path / "plan")
    item = report["top_answer_leakage_repairs"][0]
    assert item["proposed_patch_type"] == "remove_answer_from_prompt"
    manifest = json.loads(Path(report["patch_manifest_paths"]["json"]).read_text(encoding="utf-8"))
    op = manifest["operations"][0]
    assert op["type"] == "remove_prompt_answer_leakage"
    assert op["requires_manual_review"] is True
    assert op["safe_to_auto_patch"] is False


def test_true_split_leakage_creates_manual_split_repair(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    _write(reports / "static_leakage/static_leakage_report.json", _static_report(_cluster("true_split_leakage")))
    report = build_leakage_repair_plan(tmp_path, input_dir=reports, output_dir=tmp_path / "plan")
    manifest = json.loads(Path(report["patch_manifest_paths"]["json"]).read_text(encoding="utf-8"))
    op = manifest["operations"][0]
    assert report["top_10_must_fix_before_provider_pilot"][0]["classification"] == "true_split_leakage"
    assert op["type"] == "update_split_assignment"
    assert op["requires_manual_review"] is True


def test_split_metadata_issue_creates_metadata_repair(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    _write(reports / "static_leakage/static_leakage_report.json", _static_report(_cluster("split_metadata_issue")))
    report = build_leakage_repair_plan(tmp_path, input_dir=reports, output_dir=tmp_path / "plan")
    manifest = json.loads(Path(report["patch_manifest_paths"]["json"]).read_text(encoding="utf-8"))
    assert report["top_split_metadata_repairs"][0]["proposed_patch_type"] == "correct_split_metadata"
    assert manifest["operations"][0]["type"] == "correct_split_metadata"


def test_false_positive_creates_suppression_candidate(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    cluster = _cluster(
        "shared_tool_description",
        leakage_risk="false_positive_candidate",
        severity="informational",
        readiness_gate="nice_to_have",
    )
    _write(reports / "static_leakage/static_leakage_report.json", _static_report(cluster))
    report = build_leakage_repair_plan(tmp_path, input_dir=reports, output_dir=tmp_path / "plan")
    assert report["false_positive_suppression_candidates"][0]["proposed_patch_type"] == "suppress_false_positive"
    manifest = json.loads(Path(report["patch_manifest_paths"]["json"]).read_text(encoding="utf-8"))
    assert manifest["operations"][0]["type"] == "mark_false_positive"


def test_raw_findings_preserved_by_reference_not_repeated(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    _write(reports / "static_leakage/static_leakage_report.json", _static_report(_cluster("answer_leakage")))
    report = build_leakage_repair_plan(tmp_path, input_dir=reports, output_dir=tmp_path / "plan")
    assert report["repair_items"][0]["raw_finding_ids"] == ["leak_1", "leak_2"]
    assert "raw_findings" not in report


def test_patch_manifest_generated_and_validates(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    _write(reports / "static_leakage/static_leakage_report.json", _static_report(_cluster("duplicate_id_leakage")))
    report = build_leakage_repair_plan(tmp_path, input_dir=reports, output_dir=tmp_path / "plan")
    validation = validate_leakage_patch_manifest(tmp_path, manifest_path=report["patch_manifest_paths"]["json"])
    assert validation["verdicts"]["manifest_valid"] is True
    assert Path(validation["report_paths"]["json"]).exists()


def test_patch_manifest_validator_rejects_results_mutation(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    _write(
        manifest,
        {"operations": [{"operation_id": "op_1", "type": "rename_instance_id", "affected_files": ["results/run/a.json"], "details": {}}]},
    )
    validation = validate_leakage_patch_manifest(tmp_path, manifest_path=manifest)
    assert any(check["id"] == "touches_results" for check in validation["checks"])
    assert validation["verdicts"]["manifest_valid"] is False


def test_patch_manifest_validator_rejects_scientific_evidence_true(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    _write(
        manifest,
        {
            "operations": [
                {
                    "operation_id": "op_1",
                    "type": "manual_review_required",
                    "affected_files": [],
                    "details": {"scientific_evidence": True},
                }
            ]
        },
    )
    validation = validate_leakage_patch_manifest(tmp_path, manifest_path=manifest)
    assert any(check["id"] == "promotes_scientific_evidence" for check in validation["checks"])


def test_patch_manifest_validator_requires_manual_review_for_content_and_split(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    _write(
        manifest,
        {
            "operations": [
                {
                    "operation_id": "op_1",
                    "type": "remove_prompt_answer_leakage",
                    "affected_files": [],
                    "details": {},
                    "requires_manual_review": False,
                },
                {
                    "operation_id": "op_2",
                    "type": "update_split_assignment",
                    "affected_files": [],
                    "details": {},
                    "requires_manual_review": False,
                },
            ]
        },
    )
    validation = validate_leakage_patch_manifest(tmp_path, manifest_path=manifest)
    assert sum(1 for check in validation["checks"] if check["id"] == "manual_review_required") == 2


def test_dashboard_consumes_leakage_repair_plan(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    _write(reports / "run_health_report.json", {"summary": {"paper_eligible_count": 0}})
    _write(reports / "paper_asset_eligibility.json", {"eligible_count": 0})
    _write(
        reports / "claim_evidence_matrix.json",
        {"claims": [{"claim_id": f"C{i}", "status": "planned"} for i in range(1, 9)] + [{"claim_id": "C9", "status": "engineering_only"}, {"claim_id": "C10", "status": "planned"}]},
    )
    _write(
        reports / "leakage_repair_plan/leakage_repair_plan.json",
        {
            "summary": {"cluster_count": 1, "must_fix_before_provider_pilot_count": 1, "candidate_auto_patch_count": 0, "manual_review_count": 1},
            "top_10_must_fix_before_provider_pilot": [{"cluster_id": "leak_root_1"}],
            "manual_review_queue": [{"cluster_id": "leak_root_1"}],
            "patch_manifest_paths": {},
        },
    )
    _write(
        reports / "leakage_repair_plan/leakage_patch_validation.json",
        {"summary": {"blockers": 0}, "verdicts": {"manifest_valid": True}, "checks": []},
    )
    dashboard = build_evidence_dashboard(tmp_path, reports_dir=reports, output_dir=tmp_path / "dash")
    assert dashboard["leakage_repair_plan_summary"]["must_fix_before_provider_pilot_count"] == 1
    assert "Review leakage_repair_plan.md" in dashboard["provider_pilot_gate"]["exact_next_action"]


def test_report_quality_requires_repair_plan_when_blockers_exist(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    _write(reports / "static_leakage/static_leakage_report.json", _static_report(_cluster("true_split_leakage")))
    (reports / "static_leakage/static_leakage_report.md").write_text("# Static Leakage\n", encoding="utf-8")
    quality = build_report_quality_check(tmp_path, input_dir=reports, output_dir=tmp_path / "quality")
    assert any(check["id"] == "leakage_repair_plan_missing" for check in quality["checks"])


def test_report_quality_safe_repair_plan_manifest_passes_leakage_requirement(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    _write(reports / "static_leakage/static_leakage_report.json", _static_report(_cluster("true_split_leakage")))
    (reports / "static_leakage/static_leakage_report.md").write_text("# Static Leakage\n", encoding="utf-8")
    _write(
        reports / "leakage_repair_plan/leakage_repair_plan.json",
        {"summary": {"cluster_count": 1}, "manual_review_queue": [], "repair_items": []},
    )
    _write(
        reports / "leakage_repair_plan/proposed_patch_manifest.json",
        {"operations": [{"operation_id": "op_1", "type": "manual_review_required", "affected_files": [], "details": {}}]},
    )
    quality = build_report_quality_check(tmp_path, input_dir=reports, output_dir=tmp_path / "quality")
    assert not any(check["id"] == "leakage_repair_plan_missing" for check in quality["checks"])
    assert not any(check["id"] == "proposed_patch_manifest_missing" for check in quality["checks"])


def test_report_quality_flags_unsafe_manifest_touching_results(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    _write(
        reports / "leakage_repair_plan/proposed_patch_manifest.json",
        {"operations": [{"operation_id": "op_1", "type": "manual_review_required", "affected_files": ["results/x.json"], "details": {}}]},
    )
    quality = build_report_quality_check(tmp_path, input_dir=reports, output_dir=tmp_path / "quality")
    assert any(check["id"] == "patch_manifest_touches_results" for check in quality["checks"])
