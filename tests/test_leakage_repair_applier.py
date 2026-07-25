from __future__ import annotations

import json
from pathlib import Path

import pytest

from causal_agent_bench.safety.leakage_repair_applier import (
    apply_leakage_patch,
    build_leakage_patch_preview,
    build_reviewed_ops_template,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _rename_manifest(tmp_path: Path, *, old_id: str, new_id: str, affected_files: list[str], safe: bool = True) -> Path:
    manifest = tmp_path / "manifest.json"
    payload = {
        "manifest_version": 1,
        "operations": [
            {
                "operation_id": "leak_patch_rename_1",
                "type": "rename_instance_id",
                "reason": "duplicate ID rename",
                "classification": "duplicate_id_leakage",
                "affected_files": affected_files,
                "details": {"old_id": old_id, "new_id": new_id},
                "candidate_auto_patch": safe,
                "requires_manual_review": not safe,
                "safe_to_auto_patch": safe,
                "unsafe": False,
            }
        ],
    }
    _write_json(manifest, payload)
    return manifest


def _make_dataset(tmp_path: Path, file_path: str, content_lines: list[dict]) -> Path:
    path = tmp_path / file_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row) for row in content_lines) + "\n", encoding="utf-8")
    return path


def test_preview_does_not_modify_files(tmp_path: Path) -> None:
    data_file = _make_dataset(tmp_path, "data/processed/tiny/instances.jsonl", [{"instance_id": "task_1.dup", "condition": "clean"}])
    manifest = _rename_manifest(
        tmp_path,
        old_id="task_1.dup",
        new_id="task_1.dup__dedupe_candidate",
        affected_files=[str(data_file.relative_to(tmp_path))],
    )
    report = build_leakage_patch_preview(
        tmp_path,
        manifest_path=manifest,
        selected_ops=["leak_patch_rename_1"],
        output_dir=tmp_path / "out",
    )
    assert report["mode"] == "preview"
    assert report["verdicts"]["patches_applied"] is False
    assert data_file.read_text(encoding="utf-8") == '{"instance_id": "task_1.dup", "condition": "clean"}\n'


def test_preview_requires_selected_ops(tmp_path: Path) -> None:
    manifest = _rename_manifest(tmp_path, old_id="x", new_id="y", affected_files=[])
    report = build_leakage_patch_preview(tmp_path, manifest_path=manifest, selected_ops=[], output_dir=tmp_path / "out")
    refusal_ids = {r["id"] for r in report["refusals"]}
    assert "no_selected_operations" in refusal_ids


def test_apply_requires_reviewed_ops_argument(tmp_path: Path) -> None:
    manifest = _rename_manifest(tmp_path, old_id="x", new_id="y", affected_files=[])
    with pytest.raises(ValueError):
        apply_leakage_patch(
            tmp_path,
            manifest_path=manifest,
            selected_ops=["leak_patch_rename_1"],
            reviewed_ops_path=None,
            reviewed_by="reviewer",
            approval_note="ok",
            output_dir=tmp_path / "out",
        )


def test_apply_requires_reviewed_by_and_approval_note(tmp_path: Path) -> None:
    manifest = _rename_manifest(tmp_path, old_id="x", new_id="y", affected_files=[])
    reviewed = tmp_path / "reviewed.json"
    reviewed.write_text(json.dumps(["leak_patch_rename_1"]), encoding="utf-8")
    with pytest.raises(ValueError):
        apply_leakage_patch(
            tmp_path,
            manifest_path=manifest,
            selected_ops=["leak_patch_rename_1"],
            reviewed_ops_path=reviewed,
            reviewed_by="",
            approval_note="ok",
            output_dir=tmp_path / "out",
        )
    with pytest.raises(ValueError):
        apply_leakage_patch(
            tmp_path,
            manifest_path=manifest,
            selected_ops=["leak_patch_rename_1"],
            reviewed_ops_path=reviewed,
            reviewed_by="reviewer",
            approval_note="",
            output_dir=tmp_path / "out",
        )


def test_apply_refuses_when_selected_ops_empty(tmp_path: Path) -> None:
    manifest = _rename_manifest(tmp_path, old_id="x", new_id="y", affected_files=[])
    reviewed = tmp_path / "reviewed.json"
    reviewed.write_text(json.dumps(["leak_patch_rename_1"]), encoding="utf-8")
    with pytest.raises(ValueError):
        apply_leakage_patch(
            tmp_path,
            manifest_path=manifest,
            selected_ops=[],
            reviewed_ops_path=reviewed,
            reviewed_by="reviewer",
            approval_note="approved by advisor",
            output_dir=tmp_path / "out",
        )


def test_apply_renames_within_data_dir(tmp_path: Path) -> None:
    data_file = _make_dataset(
        tmp_path,
        "data/processed/tiny/instances.jsonl",
        [{"instance_id": "task_1.dup", "condition": "clean"}, {"instance_id": "task_2.dup", "condition": "clean"}],
    )
    manifest = _rename_manifest(
        tmp_path,
        old_id="task_1.dup",
        new_id="task_1.dup__dedupe_candidate",
        affected_files=[str(data_file.relative_to(tmp_path))],
    )
    reviewed = tmp_path / "reviewed.txt"
    reviewed.write_text("leak_patch_rename_1\n", encoding="utf-8")
    report = apply_leakage_patch(
        tmp_path,
        manifest_path=manifest,
        selected_ops=["leak_patch_rename_1"],
        reviewed_ops_path=reviewed,
        reviewed_by="advisor",
        approval_note="approved deterministic ID rename",
        output_dir=tmp_path / "out",
    )
    assert report["mode"] == "apply"
    assert report["verdicts"]["patches_applied"] is True
    text = data_file.read_text(encoding="utf-8")
    assert "task_1.dup__dedupe_candidate" in text
    assert "\"task_2.dup\"" in text  # unrelated ID preserved


def test_apply_refuses_unsafe_operation_type(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    _write_json(
        manifest,
        {
            "operations": [
                {
                    "operation_id": "op_unsafe",
                    "type": "remove_prompt_answer_leakage",
                    "affected_files": [],
                    "details": {"instance_id": "task_1"},
                    "requires_manual_review": True,
                    "safe_to_auto_patch": False,
                }
            ]
        },
    )
    reviewed = tmp_path / "reviewed.json"
    reviewed.write_text(json.dumps(["op_unsafe"]), encoding="utf-8")
    report = apply_leakage_patch(
        tmp_path,
        manifest_path=manifest,
        selected_ops=["op_unsafe"],
        reviewed_ops_path=reviewed,
        reviewed_by="advisor",
        approval_note="approved",
        output_dir=tmp_path / "out",
    )
    actions = {action["operation_id"]: action["category"] for action in report["actions"]}
    assert actions["op_unsafe"] == "preview_only"
    assert report["verdicts"]["patches_applied"] is False


def test_apply_refuses_path_outside_data(tmp_path: Path) -> None:
    outside = tmp_path / "results/some/file.json"
    outside.parent.mkdir(parents=True, exist_ok=True)
    outside.write_text(json.dumps([{"instance_id": "task_1.dup"}]), encoding="utf-8")
    manifest = _rename_manifest(
        tmp_path,
        old_id="task_1.dup",
        new_id="task_1.dup__dedupe_candidate",
        affected_files=["results/some/file.json"],
    )
    reviewed = tmp_path / "reviewed.json"
    reviewed.write_text(json.dumps(["leak_patch_rename_1"]), encoding="utf-8")
    report = apply_leakage_patch(
        tmp_path,
        manifest_path=manifest,
        selected_ops=["leak_patch_rename_1"],
        reviewed_ops_path=reviewed,
        reviewed_by="advisor",
        approval_note="approved",
        output_dir=tmp_path / "out",
    )
    # apply_refused mode should fire because manifest validation flagged a forbidden path
    assert report["mode"] == "apply_refused"
    assert any("forbidden" in refusal["id"] for refusal in report["refusals"])
    assert outside.read_text(encoding="utf-8") == '[{"instance_id": "task_1.dup"}]'


def test_apply_refuses_promotes_evidence_marker(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    _write_json(
        manifest,
        {
            "operations": [
                {
                    "operation_id": "op_promote",
                    "type": "rename_instance_id",
                    "affected_files": [],
                    "details": {"old_id": "a", "new_id": "b", "scientific_evidence": True},
                    "candidate_auto_patch": True,
                    "requires_manual_review": False,
                    "safe_to_auto_patch": True,
                }
            ]
        },
    )
    reviewed = tmp_path / "reviewed.json"
    reviewed.write_text(json.dumps(["op_promote"]), encoding="utf-8")
    report = apply_leakage_patch(
        tmp_path,
        manifest_path=manifest,
        selected_ops=["op_promote"],
        reviewed_ops_path=reviewed,
        reviewed_by="advisor",
        approval_note="approved",
        output_dir=tmp_path / "out",
    )
    assert report["mode"] == "apply_refused"
    assert report["verdicts"]["manifest_blocked"] is True


def test_apply_does_not_apply_when_operation_not_in_reviewed_set(tmp_path: Path) -> None:
    data_file = _make_dataset(tmp_path, "data/processed/tiny/instances.jsonl", [{"instance_id": "task_1.dup"}])
    manifest = _rename_manifest(
        tmp_path,
        old_id="task_1.dup",
        new_id="task_1.dup__dedupe_candidate",
        affected_files=[str(data_file.relative_to(tmp_path))],
    )
    reviewed = tmp_path / "reviewed.json"
    reviewed.write_text(json.dumps(["op_other"]), encoding="utf-8")
    report = apply_leakage_patch(
        tmp_path,
        manifest_path=manifest,
        selected_ops=["leak_patch_rename_1"],
        reviewed_ops_path=reviewed,
        reviewed_by="advisor",
        approval_note="approved",
        output_dir=tmp_path / "out",
    )
    assert report["verdicts"]["patches_applied"] is False
    assert any(r["id"] == "operation_not_reviewed" for r in report["refusals"])
    assert "task_1.dup__dedupe_candidate" not in data_file.read_text(encoding="utf-8")


def test_reviewed_ops_template_lists_safe_candidates_only(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    _write_json(
        manifest,
        {
            "operations": [
                {
                    "operation_id": "op_safe",
                    "type": "rename_instance_id",
                    "classification": "duplicate_id_leakage",
                    "reason": "deterministic rename",
                    "affected_files": ["data/processed/tiny/instances.jsonl"],
                    "details": {"old_id": "task_1.dup", "new_id": "task_1.dup__dedupe_candidate"},
                    "candidate_auto_patch": True,
                    "requires_manual_review": False,
                    "safe_to_auto_patch": True,
                },
                {
                    "operation_id": "op_content",
                    "type": "remove_prompt_answer_leakage",
                    "classification": "answer_leakage",
                    "reason": "manual rewrite required",
                    "affected_files": [],
                    "details": {},
                    "candidate_auto_patch": False,
                    "requires_manual_review": True,
                    "safe_to_auto_patch": False,
                },
            ]
        },
    )
    template = build_reviewed_ops_template(tmp_path, manifest_path=manifest, output_dir=tmp_path / "out")
    assert template["candidate_count"] == 1
    assert template["rows"][0]["operation_id"] == "op_safe"
    blank = Path(template["report_paths"]["blank"]).read_text(encoding="utf-8")
    # The blank file must NOT preselect any operation_ids.
    assert "op_safe" not in blank
    md = Path(template["report_paths"]["markdown"]).read_text(encoding="utf-8")
    assert "op_safe" in md
    assert "op_content" not in md


def test_reviewed_ops_template_include_all(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    _write_json(
        manifest,
        {
            "operations": [
                {
                    "operation_id": "op_safe",
                    "type": "rename_instance_id",
                    "affected_files": ["data/processed/tiny/instances.jsonl"],
                    "details": {"old_id": "a", "new_id": "b"},
                    "safe_to_auto_patch": True,
                },
                {
                    "operation_id": "op_manual",
                    "type": "update_split_assignment",
                    "details": {"instance_id": "task_1"},
                    "affected_files": [],
                    "safe_to_auto_patch": False,
                    "requires_manual_review": True,
                },
            ]
        },
    )
    template = build_reviewed_ops_template(tmp_path, manifest_path=manifest, output_dir=tmp_path / "out", include_only="all")
    assert template["candidate_count"] == 2


def test_apply_refuses_when_new_id_appears_globally(tmp_path: Path) -> None:
    """new_id must not appear in any data file outside frozen/."""

    other_file = _make_dataset(
        tmp_path,
        "data/processed/other/instances.jsonl",
        [{"instance_id": "task_1.dup__dedupe_candidate"}],
    )
    data_file = _make_dataset(tmp_path, "data/processed/tiny/instances.jsonl", [{"instance_id": "task_1.dup"}])
    manifest = _rename_manifest(
        tmp_path,
        old_id="task_1.dup",
        new_id="task_1.dup__dedupe_candidate",
        affected_files=[str(data_file.relative_to(tmp_path))],
    )
    reviewed = tmp_path / "reviewed.json"
    reviewed.write_text(json.dumps(["leak_patch_rename_1"]), encoding="utf-8")
    report = apply_leakage_patch(
        tmp_path,
        manifest_path=manifest,
        selected_ops=["leak_patch_rename_1"],
        reviewed_ops_path=reviewed,
        reviewed_by="advisor",
        approval_note="approved",
        output_dir=tmp_path / "out",
    )
    refusal_ids = {r["id"] for r in report["refusals"]}
    assert "id_rename_new_id_collision_global" in refusal_ids
    assert "task_1.dup__dedupe_candidate" not in data_file.read_text(encoding="utf-8")
    # Other file untouched too.
    assert "task_1.dup__dedupe_candidate" in other_file.read_text(encoding="utf-8")


def test_apply_refuses_frozen_dataset_edits(tmp_path: Path) -> None:
    frozen_file = _make_dataset(
        tmp_path,
        "data/frozen/pilot_v0.1/instances.jsonl",
        [{"instance_id": "task_1.dup"}],
    )
    manifest = _rename_manifest(
        tmp_path,
        old_id="task_1.dup",
        new_id="task_1.dup__dedupe_candidate",
        affected_files=[str(frozen_file.relative_to(tmp_path))],
    )
    reviewed = tmp_path / "reviewed.json"
    reviewed.write_text(json.dumps(["leak_patch_rename_1"]), encoding="utf-8")
    report = apply_leakage_patch(
        tmp_path,
        manifest_path=manifest,
        selected_ops=["leak_patch_rename_1"],
        reviewed_ops_path=reviewed,
        reviewed_by="advisor",
        approval_note="approved",
        output_dir=tmp_path / "out",
    )
    refusal_ids = {r["id"] for r in report["refusals"]}
    assert "id_rename_path_in_frozen" in refusal_ids
    assert frozen_file.read_text(encoding="utf-8") == '{"instance_id": "task_1.dup"}\n'


def test_apply_refuses_when_new_id_collides(tmp_path: Path) -> None:
    data_file = _make_dataset(
        tmp_path,
        "data/processed/tiny/instances.jsonl",
        [{"instance_id": "task_1.dup"}, {"instance_id": "task_1.dup__dedupe_candidate"}],
    )
    manifest = _rename_manifest(
        tmp_path,
        old_id="task_1.dup",
        new_id="task_1.dup__dedupe_candidate",
        affected_files=[str(data_file.relative_to(tmp_path))],
    )
    reviewed = tmp_path / "reviewed.json"
    reviewed.write_text(json.dumps(["leak_patch_rename_1"]), encoding="utf-8")
    report = apply_leakage_patch(
        tmp_path,
        manifest_path=manifest,
        selected_ops=["leak_patch_rename_1"],
        reviewed_ops_path=reviewed,
        reviewed_by="advisor",
        approval_note="approved",
        output_dir=tmp_path / "out",
    )
    # The global pre-flight check fires before per-file collision.
    refusal_ids = {r["id"] for r in report["refusals"]}
    assert refusal_ids & {"id_rename_new_id_collision_global", "id_rename_new_id_collision"}
    assert report["verdicts"]["patches_applied"] is False
