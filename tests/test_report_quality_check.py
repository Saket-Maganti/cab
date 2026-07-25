from __future__ import annotations

import json
from pathlib import Path

from causal_agent_bench.safety.report_quality_check import build_report_quality_check


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_noisy_raw_report_without_clustering_flagged(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    _write_json(reports / "repair_plan.json", {"summary": {"raw_repair_item_count": 1201}, "raw_items": [{}] * 1201})
    (reports / "repair_plan.md").write_text("# Repair Plan\n", encoding="utf-8")
    report = build_report_quality_check(tmp_path, input_dir=reports, output_dir=tmp_path / "quality")
    assert any(check["id"] == "noisy_raw_report_without_clustering" for check in report["checks"])
    assert report["verdicts"]["blocked_by_noise"] is True


def test_clustered_report_passes_noise_check(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    _write_json(
        reports / "repair_plan.json",
        {
            "summary": {"raw_repair_item_count": 1201, "root_cause_count": 12},
            "raw_items": [{}] * 1201,
            "root_causes": [{"root_cause_id": "root_1"}] * 12,
        },
    )
    (reports / "repair_plan.md").write_text("# Repair Plan\n", encoding="utf-8")
    report = build_report_quality_check(tmp_path, input_dir=reports, output_dir=tmp_path / "quality")
    assert not any(check["id"] == "noisy_raw_report_without_clustering" for check in report["checks"])


def test_unsupported_claim_language_flagged(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    _write_json(reports / "claim_evidence_matrix.json", {"summary": {"blockers": 0}})
    (reports / "claim_evidence_matrix.md").write_text("This proves the benchmark result.", encoding="utf-8")
    report = build_report_quality_check(tmp_path, input_dir=reports, output_dir=tmp_path / "quality")
    assert any(check["id"] == "unsupported_claim_language" for check in report["checks"])


def test_valid_json_array_not_flagged_unparseable(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    # A valid top-level JSON array (e.g. a list of scenario rows) is a legitimate
    # report shape and must not be a blocker.
    (reports / "what_if_plan.json").parent.mkdir(parents=True, exist_ok=True)
    (reports / "what_if_plan.json").write_text(
        json.dumps([{"scenario_id": "s1", "claim_boundary": "static only"}]), encoding="utf-8"
    )
    (reports / "what_if_plan.md").write_text("# What If\n", encoding="utf-8")
    report = build_report_quality_check(tmp_path, input_dir=reports, output_dir=tmp_path / "quality")
    assert not any(check["id"] == "json_not_parseable" for check in report["checks"])


def test_truly_malformed_json_still_flagged(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "broken.json").write_text("{not valid json", encoding="utf-8")
    report = build_report_quality_check(tmp_path, input_dir=reports, output_dir=tmp_path / "quality")
    assert any(
        check["id"] == "json_not_parseable" and check["severity"] == "blocker"
        for check in report["checks"]
    )


def test_forbidden_wording_examples_not_flagged(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    _write_json(reports / "claim_safe_wording_bank.json", {"summary": {"blockers": 0}})
    # A wording bank lists forbidden phrases verbatim as examples to avoid.
    (reports / "claim_safe_wording_bank.md").write_text(
        "## Forbidden\n- The benchmark demonstrates robustness.\n- Human validation confirms the benchmark.\n",
        encoding="utf-8",
    )
    report = build_report_quality_check(tmp_path, input_dir=reports, output_dir=tmp_path / "quality")
    assert not any(check["id"] == "unsupported_claim_language" for check in report["checks"])


def test_missing_json_flagged(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "custom_report.md").write_text("# Custom Report\n", encoding="utf-8")
    report = build_report_quality_check(tmp_path, input_dir=reports, output_dir=tmp_path / "quality")
    assert any(check["id"] == "json_missing" for check in report["checks"])
    assert Path(report["report_paths"]["json"]).exists()


def test_noisy_raw_leakage_report_without_clusters_warned(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    _write_json(reports / "static_leakage_report.json", {"summary": {"raw_finding_count": 1500}})
    (reports / "static_leakage_report.md").write_text("# Static Leakage\n", encoding="utf-8")
    report = build_report_quality_check(tmp_path, input_dir=reports, output_dir=tmp_path / "quality")
    assert any(
        check["id"] == "noisy_raw_report_without_clustering"
        and check["severity"] == "warning"
        for check in report["checks"]
    )


def test_clustered_leakage_report_passes_noise_check(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    _write_json(
        reports / "static_leakage_report.json",
        {
            "summary": {
                "raw_finding_count": 2500,
                "cluster_count": 5,
                "suppressed_symptom_count": 2495,
                "classification_counts": {"shared_tool_description": 4, "answer_leakage": 1},
                "false_positive_candidate_count": 4,
            },
            "top_clusters": [{"root_cause_id": "leak_root_1"}],
            "top_true_leakage_clusters": [{"root_cause_id": "leak_root_2"}],
            "manual_review_queue": [],
            "false_positive_candidates": [{"root_cause_id": "leak_root_1"}],
        },
    )
    (reports / "static_leakage_report.md").write_text("# Static Leakage\n## Root-Cause Summary\n", encoding="utf-8")
    report = build_report_quality_check(tmp_path, input_dir=reports, output_dir=tmp_path / "quality")
    assert not any(check["id"] == "noisy_raw_report_without_clustering" for check in report["checks"])
    assert not any(check["id"] == "top_clusters_missing" for check in report["checks"])


def test_markdown_raw_flood_flagged(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    _write_json(
        reports / "static_leakage_report.json",
        {
            "summary": {
                "raw_finding_count": 2500,
                "cluster_count": 3,
                "suppressed_symptom_count": 2497,
                "classification_counts": {"shared_tool_description": 3},
                "false_positive_candidate_count": 3,
            },
            "top_clusters": [{"root_cause_id": "leak_root_1"}],
            "top_true_leakage_clusters": [],
            "manual_review_queue": [],
            "false_positive_candidates": [{"root_cause_id": "leak_root_1"}],
        },
    )
    raw_lines = "\n".join("- `warning` `data` `x` `near_duplicate_prompt`: raw" for _ in range(151))
    (reports / "static_leakage_report.md").write_text(raw_lines, encoding="utf-8")
    report = build_report_quality_check(tmp_path, input_dir=reports, output_dir=tmp_path / "quality")
    assert any(check["id"] == "markdown_raw_flood" for check in report["checks"])


def test_top_clusters_required_for_high_volume_leakage(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    _write_json(
        reports / "static_leakage_report.json",
        {"summary": {"raw_finding_count": 2500, "cluster_count": 3, "suppressed_symptom_count": 2497}},
    )
    (reports / "static_leakage_report.md").write_text("# Static Leakage\n", encoding="utf-8")
    report = build_report_quality_check(tmp_path, input_dir=reports, output_dir=tmp_path / "quality")
    assert any(check["id"] == "top_clusters_missing" for check in report["checks"])


def test_high_raw_leakage_without_classification_flagged(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    _write_json(
        reports / "static_leakage_report.json",
        {
            "summary": {"raw_finding_count": 2500, "cluster_count": 3, "suppressed_symptom_count": 2497},
            "top_clusters": [{"root_cause_id": "leak_root_1"}],
        },
    )
    (reports / "static_leakage_report.md").write_text("# Static Leakage\n", encoding="utf-8")
    report = build_report_quality_check(tmp_path, input_dir=reports, output_dir=tmp_path / "quality")
    assert any(check["id"] == "classification_counts_missing" for check in report["checks"])
    assert any(check["id"] == "false_positive_section_missing" for check in report["checks"])


def test_classified_leakage_report_has_required_false_positive_section(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    _write_json(
        reports / "static_leakage_report.json",
        {
            "summary": {
                "raw_finding_count": 2500,
                "cluster_count": 3,
                "suppressed_symptom_count": 2497,
                "classification_counts": {"shared_tool_description": 2, "answer_leakage": 1},
                "false_positive_candidate_count": 2,
            },
            "top_clusters": [{"root_cause_id": "leak_root_1"}],
            "top_true_leakage_clusters": [{"root_cause_id": "leak_root_2"}],
            "manual_review_queue": [],
            "top_false_positive_candidates": [{"root_cause_id": "leak_root_1"}],
        },
    )
    (reports / "static_leakage_report.md").write_text("# Static Leakage\n## Top Likely False Positives / Boilerplate Clusters\n", encoding="utf-8")
    report = build_report_quality_check(tmp_path, input_dir=reports, output_dir=tmp_path / "quality")
    assert not any(check["id"] == "classification_counts_missing" for check in report["checks"])
    assert not any(check["id"] == "false_positive_section_missing" for check in report["checks"])


def test_large_payload_claim_scan_is_bounded(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    large_rows = [
        {"finding": "shared tool boilerplate", "detail": "x" * 1000}
        for _ in range(5000)
    ]
    _write_json(
        reports / "static_leakage_report.json",
        {
            "summary": {
                "raw_finding_count": 5000,
                "cluster_count": 2,
                "suppressed_symptom_count": 4998,
                "classification_counts": {"shared_tool_description": 2},
                "false_positive_candidate_count": 2,
            },
            "top_clusters": [{"root_cause_id": "leak_root_1"}],
            "top_true_leakage_clusters": [],
            "manual_review_queue": [],
            "false_positive_candidates": [{"root_cause_id": "leak_root_1"}],
            "raw_findings": large_rows,
        },
    )
    (reports / "static_leakage_report.md").write_text(
        "# Static Leakage\n## Top Likely False Positives / Boilerplate Clusters\n",
        encoding="utf-8",
    )
    report = build_report_quality_check(tmp_path, input_dir=reports, output_dir=tmp_path / "quality")
    assert not any(check["id"] == "paper_ready_with_zero_eligible_runs" for check in report["checks"])
