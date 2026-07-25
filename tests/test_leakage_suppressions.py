from __future__ import annotations

import json
from pathlib import Path

import yaml

from causal_agent_bench.safety.leakage_suppressions import (
    apply_suppressions,
    build_suppression_registry_report,
    load_suppression_registry,
)


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload), encoding="utf-8")


def test_missing_registry_is_empty(tmp_path: Path) -> None:
    registry = load_suppression_registry(tmp_path, path=tmp_path / "configs/missing.yaml")
    assert registry["entries"] == []
    assert registry["exists"] is False
    assert registry["active_count"] == 0
    assert registry["malformed_count"] == 0


def test_valid_entry_is_loaded(tmp_path: Path) -> None:
    cfg = tmp_path / "configs/suppressions.yaml"
    _write_yaml(
        cfg,
        {
            "suppressions": [
                {
                    "id": "supp_example",
                    "reviewer": "advisor",
                    "reason": "reviewed shared tool templates",
                    "scope": "static_leakage_tool_description",
                    "date": "2026-05-01",
                    "classifications": ["shared_tool_description"],
                }
            ]
        },
    )
    registry = load_suppression_registry(tmp_path, path=cfg)
    assert registry["active_count"] == 1
    assert registry["entries"][0]["scope"] == "static_leakage_tool_description"


def test_entry_with_forbidden_keys_rejected(tmp_path: Path) -> None:
    cfg = tmp_path / "configs/suppressions.yaml"
    _write_yaml(
        cfg,
        {
            "suppressions": [
                {
                    "reviewer": "advisor",
                    "reason": "x",
                    "scope": "static_leakage_template_reuse",
                    "date": "2026-05-01",
                    "classifications": ["likely_template_reuse"],
                    "scientific_evidence": True,
                }
            ]
        },
    )
    registry = load_suppression_registry(tmp_path, path=cfg)
    assert registry["entries"] == []
    assert any(issue["id"] == "entry_uses_forbidden_keys" for issue in registry["issues"])


def test_entry_with_always_blocking_class_rejected(tmp_path: Path) -> None:
    cfg = tmp_path / "configs/suppressions.yaml"
    _write_yaml(
        cfg,
        {
            "suppressions": [
                {
                    "reviewer": "advisor",
                    "reason": "should not be allowed",
                    "scope": "static_leakage_false_positive",
                    "date": "2026-05-01",
                    "classifications": ["answer_leakage"],
                }
            ]
        },
    )
    registry = load_suppression_registry(tmp_path, path=cfg)
    assert registry["entries"] == []
    assert any(issue["id"] == "entry_classifications_blocked" for issue in registry["issues"])


def test_review_after_in_past_marks_entry_expired(tmp_path: Path) -> None:
    cfg = tmp_path / "configs/suppressions.yaml"
    _write_yaml(
        cfg,
        {
            "suppressions": [
                {
                    "reviewer": "advisor",
                    "reason": "review",
                    "scope": "static_leakage_template_reuse",
                    "date": "2024-01-01",
                    "review_after": "2024-02-01",
                    "classifications": ["likely_template_reuse"],
                }
            ]
        },
    )
    registry = load_suppression_registry(tmp_path, path=cfg)
    assert registry["expired_count"] == 1
    assert registry["active_count"] == 0


def test_apply_suppressions_annotates_matching_clusters(tmp_path: Path) -> None:
    cfg = tmp_path / "configs/suppressions.yaml"
    _write_yaml(
        cfg,
        {
            "suppressions": [
                {
                    "reviewer": "advisor",
                    "reason": "shared tool descriptions",
                    "scope": "static_leakage_tool_description",
                    "date": "2026-05-01",
                    "classifications": ["shared_tool_description"],
                }
            ]
        },
    )
    registry = load_suppression_registry(tmp_path, path=cfg)
    rows = [
        {"cluster_id": "leak_a", "cluster_classification": "shared_tool_description", "leakage_risk": "false_positive_candidate"},
        {"cluster_id": "leak_b", "cluster_classification": "likely_template_reuse", "leakage_risk": "informational"},
    ]
    annotated = apply_suppressions(rows, registry=registry)
    assert annotated["annotated_root_causes"][0]["suppressed"] is True
    assert annotated["annotated_root_causes"][0]["suppression_reviewer"] == "advisor"
    assert annotated["annotated_root_causes"][1]["suppressed"] is False
    assert sum(annotated["usage_counts"].values()) == 1


def test_apply_suppressions_refuses_blocker_match(tmp_path: Path) -> None:
    cfg = tmp_path / "configs/suppressions.yaml"
    _write_yaml(
        cfg,
        {
            "suppressions": [
                {
                    "reviewer": "advisor",
                    "reason": "review",
                    "scope": "static_leakage_needs_review_documented",
                    "date": "2026-05-01",
                    "classifications": ["needs_manual_review"],
                }
            ]
        },
    )
    registry = load_suppression_registry(tmp_path, path=cfg)
    rows = [
        {"cluster_id": "leak_blocker", "cluster_classification": "needs_manual_review", "leakage_risk": "blocker"},
    ]
    annotated = apply_suppressions(rows, registry=registry)
    assert annotated["annotated_root_causes"][0]["suppressed"] is False
    assert annotated["refused_attempts"]
    assert annotated["refused_attempts"][0]["cluster_id"] == "leak_blocker"


def test_build_suppression_registry_report_writes_artifacts(tmp_path: Path) -> None:
    cfg = tmp_path / "configs/suppressions.yaml"
    _write_yaml(cfg, {"suppressions": []})
    report = build_suppression_registry_report(tmp_path, path=cfg, output_dir=tmp_path / "out")
    assert Path(report["report_paths"]["json"]).exists()
    assert Path(report["report_paths"]["markdown"]).exists()
    assert report["verdicts"]["registry_valid"] is True


def test_static_leakage_report_uses_suppressions(tmp_path: Path) -> None:
    """When suppressions cover a false-positive class, the static_leakage report should mark it suppressed."""

    from causal_agent_bench.safety.static_leakage import build_static_leakage_report

    cfg = tmp_path / "configs/static_leakage_suppressions.yaml"
    _write_yaml(
        cfg,
        {
            "suppressions": [
                {
                    "reviewer": "advisor",
                    "reason": "reviewed",
                    "scope": "static_leakage_tool_description",
                    "date": "2026-05-01",
                    "classifications": ["shared_tool_description"],
                }
            ]
        },
    )
    dataset_dir = tmp_path / "data/processed/tiny"
    dataset_dir.mkdir(parents=True, exist_ok=True)
    tasks = [
        {"task_id": "task_1", "domain": "policy", "goal": {"user_instruction": "Use the lookup tool to find the threshold value 100.", "expected_final_answer": "100"}},
        {"task_id": "task_2", "domain": "policy", "goal": {"user_instruction": "Use the lookup tool to find the threshold value 200.", "expected_final_answer": "200"}},
    ]
    (dataset_dir / "base_tasks.jsonl").write_text("\n".join(json.dumps(row) for row in tasks) + "\n", encoding="utf-8")
    (dataset_dir / "instances.jsonl").write_text(
        "\n".join(
            json.dumps({"instance_id": f"{t['task_id']}.clean", "condition": "clean", "base_task": t}) for t in tasks
        )
        + "\n",
        encoding="utf-8",
    )

    report = build_static_leakage_report(
        tmp_path,
        benchmark_dir=dataset_dir,
        output_dir=tmp_path / "out",
        suppression_path=cfg,
        near_duplicate_threshold=0.5,
    )
    # The report should still validate; suppression entries get propagated.
    assert report["summary"]["registry_active_suppressions"] == 1
