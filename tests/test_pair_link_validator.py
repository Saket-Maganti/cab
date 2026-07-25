from __future__ import annotations

import json
from pathlib import Path

from causal_agent_bench.safety.pair_link_validator import (
    build_pair_link_report,
    validate_dataset_pair_links,
)


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


def _task(tid: str, family: str = "test_family") -> dict:
    return {"task_id": tid, "domain": family, "task_family": family, "goal": {"user_instruction": "do x", "expected_final_answer": "ok"}}


def _instance(iid: str, base_id: str, condition: str = "clean", family: str = "test_family", **extra) -> dict:
    row = {
        "instance_id": iid,
        "condition": condition,
        "base_task": _task(base_id, family=family),
    }
    if condition != "clean":
        row["intervention"] = {"base_task_id": base_id, "family": condition}
    row.update(extra)
    return row


def _dataset(tmp_path: Path, tasks: list[dict], instances: list[dict], splits: dict | None = None) -> Path:
    dataset = tmp_path / "data/processed/tiny"
    _write_jsonl(dataset / "base_tasks.jsonl", tasks)
    _write_jsonl(dataset / "instances.jsonl", instances)
    if splits is not None:
        (dataset / "splits.json").write_text(json.dumps({"splits": splits}), encoding="utf-8")
    return dataset


def test_orphaned_intervention_is_blocker(tmp_path: Path) -> None:
    dataset = _dataset(
        tmp_path,
        [_task("task_1")],
        [_instance("task_1.tool_removal", "task_1", condition="tool_removal")],
    )
    report = validate_dataset_pair_links(dataset, repo_root=tmp_path)
    assert any(i["issue_type"] == "orphaned_intervention" and i["severity"] == "blocker" for i in report["issues"])


def test_orphaned_clean_is_warning(tmp_path: Path) -> None:
    dataset = _dataset(
        tmp_path,
        [_task("task_1")],
        [_instance("task_1.clean", "task_1", condition="clean")],
    )
    report = validate_dataset_pair_links(dataset, repo_root=tmp_path)
    assert any(i["issue_type"] == "orphaned_clean" and i["severity"] == "warning" for i in report["issues"])


def test_mismatched_base_task_id_is_blocker(tmp_path: Path) -> None:
    bad = {
        "instance_id": "task_99.clean",
        "condition": "clean",
        "base_task_id": "task_1",
        "base_task": _task("task_1"),
    }
    dataset = _dataset(tmp_path, [_task("task_1")], [bad])
    report = validate_dataset_pair_links(dataset, repo_root=tmp_path)
    assert any(i["issue_type"] == "mismatched_base_task_id" and i["severity"] == "blocker" for i in report["issues"])


def test_intervention_missing_base_task_is_blocker(tmp_path: Path) -> None:
    inter = {
        "instance_id": "missing_task.tool_removal",
        "condition": "tool_removal",
        "intervention": {"base_task_id": "missing_task", "family": "tool_removal"},
    }
    dataset = _dataset(tmp_path, [_task("task_1")], [_instance("task_1.clean", "task_1"), inter])
    report = validate_dataset_pair_links(dataset, repo_root=tmp_path)
    assert any(i["issue_type"] == "intervention_missing_clean_base_task" and i["severity"] == "blocker" for i in report["issues"])


def test_pair_crosses_task_family_is_blocker(tmp_path: Path) -> None:
    clean = _instance("task_1.clean", "task_1", condition="clean", family="family_a")
    inter = _instance("task_1.tool_removal", "task_1", condition="tool_removal", family="family_b")
    dataset = _dataset(tmp_path, [_task("task_1", family="family_a")], [clean, inter])
    report = validate_dataset_pair_links(dataset, repo_root=tmp_path)
    assert any(i["issue_type"] == "pair_crosses_task_family" and i["severity"] == "blocker" for i in report["issues"])


def test_pair_crosses_protected_split_is_blocker(tmp_path: Path) -> None:
    clean = _instance("task_1.clean", "task_1", condition="clean")
    inter = _instance("task_1.tool_removal", "task_1", condition="tool_removal")
    dataset = _dataset(
        tmp_path,
        [_task("task_1")],
        [clean, inter],
        {
            "pilot": {"base_task_ids": ["task_1"], "instance_ids": ["task_1.clean"]},
            "heldout": {"base_task_ids": ["task_1"], "instance_ids": ["task_1.tool_removal"]},
        },
    )
    report = validate_dataset_pair_links(dataset, repo_root=tmp_path)
    assert any(i["issue_type"] == "pair_crosses_protected_split" and i["severity"] == "blocker" for i in report["issues"])


def test_subset_family_overlap_pair_not_flagged(tmp_path: Path) -> None:
    """pilot and pilot_20 share the pair — that is allowed by the subset family."""

    clean = _instance("task_1.clean", "task_1", condition="clean")
    inter = _instance("task_1.tool_removal", "task_1", condition="tool_removal")
    dataset = _dataset(
        tmp_path,
        [_task("task_1")],
        [clean, inter],
        {
            "pilot": {"base_task_ids": ["task_1"], "instance_ids": ["task_1.clean", "task_1.tool_removal"]},
            "pilot_20": {"base_task_ids": ["task_1"], "instance_ids": ["task_1.clean", "task_1.tool_removal"]},
        },
    )
    report = validate_dataset_pair_links(dataset, repo_root=tmp_path)
    assert not any(i["issue_type"] == "pair_crosses_protected_split" for i in report["issues"])


def test_duplicate_intervention_variants_is_warning(tmp_path: Path) -> None:
    clean = _instance("task_1.clean", "task_1", condition="clean")
    a = {
        "instance_id": "task_1.tool_removal",
        "condition": "tool_removal",
        "intervention": {"base_task_id": "task_1", "family": "tool_removal"},
        "base_task": _task("task_1"),
    }
    b = {
        "instance_id": "task_1.tool_removal_v2",
        "condition": "tool_removal",
        "intervention": {"base_task_id": "task_1", "family": "tool_removal"},
        "base_task": _task("task_1"),
    }
    dataset = _dataset(tmp_path, [_task("task_1")], [clean, a, b])
    report = validate_dataset_pair_links(dataset, repo_root=tmp_path)
    assert any(i["issue_type"] == "duplicate_intervention_variants" and i["severity"] == "warning" for i in report["issues"])


def test_clean_pair_no_issues(tmp_path: Path) -> None:
    clean = _instance("task_1.clean", "task_1", condition="clean")
    inter = _instance("task_1.tool_removal", "task_1", condition="tool_removal")
    dataset = _dataset(tmp_path, [_task("task_1")], [clean, inter])
    report = validate_dataset_pair_links(dataset, repo_root=tmp_path)
    assert report["issue_count"] == 0


def test_build_pair_link_report_writes_artifacts(tmp_path: Path) -> None:
    clean = _instance("task_1.clean", "task_1", condition="clean")
    inter = _instance("task_1.tool_removal", "task_1", condition="tool_removal")
    _dataset(tmp_path, [_task("task_1")], [clean, inter])
    report = build_pair_link_report(tmp_path, benchmark_dir=tmp_path / "data/processed/tiny", output_dir=tmp_path / "out")
    assert Path(report["report_paths"]["json"]).exists()
    assert Path(report["report_paths"]["markdown"]).exists()
    assert report["verdicts"]["pair_link_consistent"] is True
