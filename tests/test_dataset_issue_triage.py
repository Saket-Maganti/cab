from __future__ import annotations

import json
from pathlib import Path

from causal_agent_bench.safety.dataset_issue_triage import build_dataset_issue_triage


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def _task(expected: bool = False) -> dict:
    goal = {"user_instruction": "Check policy.", "success_criteria": ["Answer."]}
    if expected:
        goal["expected_final_answer"] = "answer"
    return {
        "task_id": "task_1",
        "domain": "policy",
        "difficulty": "easy",
        "goal": goal,
        "available_tools": ["lookup"],
        "tool_specs": [{"name": "lookup"}],
    }


def _dataset(tmp_path: Path) -> Path:
    dataset = tmp_path / "data"
    task = _task(expected=False)
    clean = {"instance_id": "task_1.clean", "base_task": task, "condition": "clean", "available_tools": ["lookup"], "initial_memory": {}}
    intervention = {
        "instance_id": "task_1.memory_corruption",
        "base_task": task,
        "condition": "intervention",
        "available_tools": ["lookup", "extra"],
        "initial_memory": {"stale": True},
        "intervention": {
            "intervention_id": "task_1.memory_corruption",
            "base_task_id": "task_1",
            "family": "memory_corruption",
            "changed_factor": "memory",
            "memory_patch": {"stale": True},
            "expected_final_answer_change": "no",
        },
    }
    _write_jsonl(dataset / "base_tasks.jsonl", [task])
    _write_jsonl(dataset / "interventions.jsonl", [intervention["intervention"]])
    _write_jsonl(dataset / "instances.jsonl", [clean, intervention])
    return dataset


def test_triage_combines_quality_and_isolation_issues(tmp_path: Path) -> None:
    report = build_dataset_issue_triage(tmp_path, benchmark_dir=_dataset(tmp_path), output_dir=tmp_path / "reports")
    sources = {item["source"] for item in report["issues"]}
    assert {"benchmark_quality", "intervention_isolation"}.issubset(sources)
    assert report["groups"]["must_fix_before_provider_pilot"]


def test_triage_sorts_blockers_first_and_ids_are_stable(tmp_path: Path) -> None:
    dataset = _dataset(tmp_path)
    first = build_dataset_issue_triage(tmp_path, benchmark_dir=dataset, output_dir=tmp_path / "reports1")
    second = build_dataset_issue_triage(tmp_path, benchmark_dir=dataset, output_dir=tmp_path / "reports2")
    assert first["issues"][0]["group"] == "must_fix_before_provider_pilot"
    assert [item["issue_id"] for item in first["issues"]] == [item["issue_id"] for item in second["issues"]]
    assert Path(first["report_paths"]["json"]).exists()
    assert Path(first["report_paths"]["markdown"]).exists()


def test_duplicated_issue_family_grouped(tmp_path: Path) -> None:
    report = build_dataset_issue_triage(tmp_path, benchmark_dir=_dataset(tmp_path), output_dir=tmp_path / "reports")
    assert "gold_output" in report["issue_families"]
    assert report["blocker_counts_by_family"]["gold_output"] >= 1


def test_repair_plan_root_cause_many_symptoms_listed_once(tmp_path: Path) -> None:
    dataset = _dataset(tmp_path)
    repair_dir = tmp_path / "reports" / "repair_plan"
    repair_dir.mkdir(parents=True)
    (repair_dir / "repair_plan.json").write_text(
        json.dumps(
            {
                "root_causes": [
                    {
                        "root_cause_id": "root_many",
                        "root_cause_title": "missing expected outputs",
                        "severity": "blocker",
                        "symptom_count": 500,
                        "representative_examples": ["task_1"],
                        "affected_readiness_gates": ["must_fix_before_provider_pilot"],
                        "recommended_root_fix": "Add expected outputs.",
                        "suggested_owner": "dataset",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    report = build_dataset_issue_triage(tmp_path, benchmark_dir=dataset, output_dir=tmp_path / "reports")
    assert [row["root_cause_id"] for row in report["root_cause_groups"]] == ["root_many"]
    assert report["top_provider_pilot_blockers"][0]["symptom_count"] == 500


def test_provider_pilot_blockers_separate_from_public_release_blockers(tmp_path: Path) -> None:
    report = build_dataset_issue_triage(tmp_path, benchmark_dir=_dataset(tmp_path), output_dir=tmp_path / "reports")
    assert report["top_provider_pilot_blockers"]
    assert all("must_fix_before_provider_pilot" in row["affected_readiness_gates"] for row in report["top_provider_pilot_blockers"])


def test_manual_review_queue_deterministic(tmp_path: Path) -> None:
    dataset = _dataset(tmp_path)
    first = build_dataset_issue_triage(tmp_path, benchmark_dir=dataset, output_dir=tmp_path / "reports1")
    second = build_dataset_issue_triage(tmp_path, benchmark_dir=dataset, output_dir=tmp_path / "reports2")
    assert [item["issue_id"] for item in first["manual_review_queue"]] == [
        item["issue_id"] for item in second["manual_review_queue"]
    ]


def test_static_leakage_clusters_appear_in_triage(tmp_path: Path) -> None:
    dataset = _dataset(tmp_path)
    leakage_dir = tmp_path / "reports" / "static_leakage"
    leakage_dir.mkdir(parents=True)
    (leakage_dir / "static_leakage_report.json").write_text(
        json.dumps(
            {
                "raw_finding_count": 5000,
                "cluster_count": 1,
                "top_clusters": [
                    {
                        "root_cause_id": "leak_root_1",
                        "root_cause_title": "answer text leakage in prompt",
                        "finding_type": "answer_text_leakage",
                        "severity": "blocker",
                        "cluster_classification": "answer_leakage",
                        "leakage_risk": "blocker",
                        "symptom_count": 5000,
                        "readiness_gate": "must_fix_before_provider_pilot",
                        "recommended_action": "Remove direct answer leakage.",
                    }
                ],
                "false_positive_candidates": [],
            }
        ),
        encoding="utf-8",
    )
    report = build_dataset_issue_triage(tmp_path, benchmark_dir=dataset, output_dir=tmp_path / "reports")
    assert report["top_leakage_root_causes"][0]["root_cause_id"] == "leak_root_1"
    assert report["provider_pilot_leakage_blockers"][0]["root_cause_id"] == "leak_root_1"
    assert report["blocker_counts_by_leakage_family"]["answer_leakage"] == 1
    assert report["top_true_leakage_blockers"][0]["cluster_classification"] == "answer_leakage"


def test_static_leakage_false_positive_candidate_not_blocker_in_triage(tmp_path: Path) -> None:
    dataset = _dataset(tmp_path)
    leakage_dir = tmp_path / "reports" / "static_leakage"
    leakage_dir.mkdir(parents=True)
    (leakage_dir / "static_leakage_report.json").write_text(
        json.dumps(
            {
                "top_clusters": [
                    {
                        "root_cause_id": "leak_root_near",
                        "root_cause_title": "near duplicate prompt",
                        "finding_type": "near_duplicate_prompt",
                        "severity": "informational",
                        "cluster_classification": "shared_tool_description",
                        "leakage_risk": "false_positive_candidate",
                        "symptom_count": 100,
                        "readiness_gate": "nice_to_have",
                        "recommended_action": "Review representative boilerplate cluster only.",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    report = build_dataset_issue_triage(tmp_path, benchmark_dir=dataset, output_dir=tmp_path / "reports")
    assert report["blocker_counts_by_leakage_family"]["near_duplicates"] == 0
    assert not report["provider_pilot_leakage_blockers"]
    assert report["false_positive_leakage_candidates"][0]["root_cause_id"] == "leak_root_near"
