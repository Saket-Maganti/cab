from __future__ import annotations

import json
from pathlib import Path

from causal_agent_bench.safety.gold_output_validation import validate_gold_outputs_for_dataset


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def _task(answer: object = "500") -> dict:
    task = {
        "task_id": "task_1",
        "domain": "policy",
        "goal": {"user_instruction": "Check policy.", "success_criteria": ["Answer threshold."]},
    }
    if answer != "__missing__":
        task["goal"]["expected_final_answer"] = answer
    return task


def _dataset(tmp_path: Path, rows: list[dict]) -> Path:
    dataset = tmp_path / "data/processed/tiny"
    _write_jsonl(dataset / "instances.jsonl", rows)
    return dataset


def _clean(answer: object = "500") -> dict:
    return {"instance_id": "task_1.clean", "condition": "clean", "base_task": _task(answer)}


def _intervention(answer: object = "500", *, family: str = "memory_corruption", expected_change: str = "no", rationale: bool = True) -> dict:
    intervention = {
        "intervention_id": f"task_1.{family}",
        "base_task_id": "task_1",
        "family": family,
        "expected_final_answer_change": expected_change,
    }
    if rationale:
        intervention["scoring_notes"] = "Rationale documented."
    return {
        "instance_id": f"task_1.{family}",
        "condition": "intervention",
        "base_task": _task(answer),
        "intervention": intervention,
    }


def test_missing_gold_output_flagged(tmp_path: Path) -> None:
    report = validate_gold_outputs_for_dataset(_dataset(tmp_path, [_clean("__missing__")]), repo_root=tmp_path)
    assert any(issue["issue_type"] == "missing_gold_output" for issue in report["issues"])


def test_placeholder_gold_output_flagged(tmp_path: Path) -> None:
    report = validate_gold_outputs_for_dataset(_dataset(tmp_path, [_clean("TODO")]), repo_root=tmp_path)
    assert any(issue["issue_type"] == "placeholder_gold_output" for issue in report["issues"])


def test_answer_preserving_pair_answer_change_flagged(tmp_path: Path) -> None:
    report = validate_gold_outputs_for_dataset(
        _dataset(tmp_path, [_clean("500"), _intervention("600", expected_change="no")]),
        repo_root=tmp_path,
    )
    assert any(issue["issue_type"] == "answer_preserving_expected_answer_changed" for issue in report["issues"])


def test_answer_changing_without_rationale_flagged(tmp_path: Path) -> None:
    report = validate_gold_outputs_for_dataset(
        _dataset(tmp_path, [_clean("500"), _intervention("600", family="ambiguous_instruction", expected_change="yes", rationale=False)]),
        repo_root=tmp_path,
    )
    assert any(issue["issue_type"] == "answer_changing_without_rationale" for issue in report["issues"])


def test_manual_review_queue_and_auto_fix_forbidden(tmp_path: Path) -> None:
    from causal_agent_bench.safety.gold_output_validation import build_gold_output_validation

    dataset = tmp_path / "data/processed/tiny"
    _write_jsonl(dataset / "instances.jsonl", [_clean("500"), _intervention("600", expected_change="no")])
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\nversion='0.1.0'\n", encoding="utf-8")
    report = build_gold_output_validation(tmp_path, benchmark_dir=dataset, output_dir=tmp_path / "gold")
    assert report["verdicts"]["auto_fix_forbidden"] is True
    assert "manual_review_queue" in report


def test_valid_tiny_fixture_passes(tmp_path: Path) -> None:
    report = validate_gold_outputs_for_dataset(
        _dataset(tmp_path, [_clean("500"), _intervention("500", expected_change="no")]),
        repo_root=tmp_path,
    )
    assert report["passed"] is True
    assert report["issues"] == []
