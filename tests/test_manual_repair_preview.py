from __future__ import annotations

import json
from pathlib import Path

from causal_agent_bench.safety.manual_repair_preview import build_manual_repair_preview


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_preview_groups_operations_by_type(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    _write_json(
        manifest,
        {
            "operations": [
                {
                    "operation_id": "op_answer",
                    "type": "remove_prompt_answer_leakage",
                    "details": {"instance_id": "task_1.clean", "field": "prompt", "leaked_text_hash": "abc"},
                    "reason": "answer in prompt",
                },
                {
                    "operation_id": "op_split",
                    "type": "update_split_assignment",
                    "details": {"instance_id": "task_2.clean", "from_split": "heldout", "to_split": "manual_review_target_split"},
                    "reason": "protected boundary crossed",
                },
                {
                    "operation_id": "op_rename",
                    "type": "rename_instance_id",
                    "details": {"old_id": "task_3.dup", "new_id": "task_3.dup__dedupe_candidate"},
                    "reason": "duplicate ID",
                },
                {
                    "operation_id": "op_supp",
                    "type": "mark_false_positive",
                    "details": {"cluster_id": "leak_root_x", "classification": "shared_tool_description"},
                    "reason": "shared tool descriptions",
                },
            ]
        },
    )
    report = build_manual_repair_preview(tmp_path, manifest_path=manifest, output_dir=tmp_path / "out")
    summary = report["summary"]
    assert summary["operation_count"] == 3  # rename_instance_id is excluded
    assert summary["by_type"]["remove_prompt_answer_leakage"] == 1
    assert summary["by_type"]["update_split_assignment"] == 1
    assert summary["by_type"]["mark_false_positive"] == 1
    assert report["verdicts"]["patches_applied"] is False
    assert report["verdicts"]["manual_review_required"] is True
    md = Path(report["report_paths"]["markdown"]).read_text(encoding="utf-8")
    assert "Answer Leakage" in md
    assert "True Split Leakage" in md
    assert "False-Positive Cluster" in md
    assert "op_rename" not in md


def test_preview_handles_missing_manifest(tmp_path: Path) -> None:
    report = build_manual_repair_preview(tmp_path, manifest_path=tmp_path / "missing.json", output_dir=tmp_path / "out")
    assert report["summary"]["operation_count"] == 0
    assert report["verdicts"]["patches_applied"] is False


def test_preview_includes_unclassified_types(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    _write_json(
        manifest,
        {
            "operations": [
                {
                    "operation_id": "op_unknown",
                    "type": "some_future_repair",
                    "details": {},
                    "reason": "novel category",
                }
            ]
        },
    )
    report = build_manual_repair_preview(tmp_path, manifest_path=manifest, output_dir=tmp_path / "out")
    assert report["summary"]["unclassified_count"] == 1
    assert report["unclassified_operations"][0]["operation_id"] == "op_unknown"
