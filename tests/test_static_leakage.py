from __future__ import annotations

import json
from pathlib import Path

from causal_agent_bench.safety.static_leakage import (
    build_static_leakage_report,
    check_static_leakage_for_dataset,
)


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def _task(task_id: str, prompt: str, answer: object = "ok", domain: str = "policy") -> dict:
    return {
        "task_id": task_id,
        "domain": domain,
        "goal": {"user_instruction": prompt, "expected_final_answer": answer},
    }


def _dataset(tmp_path: Path, tasks: list[dict], splits: dict | None = None) -> Path:
    dataset = tmp_path / "data/processed/tiny"
    _write_jsonl(dataset / "base_tasks.jsonl", tasks)
    _write_jsonl(dataset / "instances.jsonl", [{"instance_id": f"{task['task_id']}.clean", "condition": "clean", "base_task": task} for task in tasks])
    if splits is not None:
        (dataset / "splits.json").write_text(json.dumps({"splits": splits}), encoding="utf-8")
    return dataset


def test_duplicate_across_splits_flagged(tmp_path: Path) -> None:
    dataset = _dataset(
        tmp_path,
        [_task("task_1", "Find the policy threshold.")],
        {"dev": {"base_task_ids": ["task_1"], "instance_ids": ["task_1.clean"]}, "heldout": {"base_task_ids": ["task_1"], "instance_ids": ["task_1.clean"]}},
    )
    report = check_static_leakage_for_dataset(dataset, repo_root=tmp_path)
    assert any(issue["issue_type"] == "duplicate_task_id" for issue in report["issues"])
    assert report["root_causes"]


def test_near_duplicate_high_overlap_flagged(tmp_path: Path) -> None:
    dataset = _dataset(
        tmp_path,
        [
            _task("task_1", "Find the policy threshold using the database and report a concise answer."),
            _task("task_2", "Find the policy threshold using the database and report a concise final answer."),
        ],
    )
    report = check_static_leakage_for_dataset(dataset, repo_root=tmp_path, near_duplicate_threshold=0.75)
    assert any(issue["issue_type"] == "near_duplicate_prompt" for issue in report["issues"])


def test_label_leakage_flagged(tmp_path: Path) -> None:
    task = _task("task_1", "This memory_corruption intervention asks for the threshold.")
    dataset = tmp_path / "data/processed/tiny"
    _write_jsonl(
        dataset / "instances.jsonl",
        [{"instance_id": "task_1.memory_corruption", "condition": "intervention", "base_task": task, "intervention": {"base_task_id": "task_1", "family": "memory_corruption"}}],
    )
    report = check_static_leakage_for_dataset(dataset, repo_root=tmp_path)
    assert any(issue["issue_type"] == "intervention_label_leakage" and issue["severity"] == "blocker" for issue in report["issues"])


def test_label_leakage_in_hidden_metadata_is_warning(tmp_path: Path) -> None:
    task = _task("task_1", "Find the threshold.")
    dataset = tmp_path / "data/processed/tiny"
    _write_jsonl(
        dataset / "instances.jsonl",
        [
            {
                "instance_id": "task_1.memory_corruption",
                "condition": "intervention",
                "base_task": task,
                "intervention": {"base_task_id": "task_1", "family": "memory_corruption"},
                "metadata": {"review_note": "memory_corruption"},
            }
        ],
    )
    report = check_static_leakage_for_dataset(dataset, repo_root=tmp_path)
    assert any(issue["issue_type"] == "intervention_label_leakage" and issue["severity"] == "warning" for issue in report["issues"])


def test_answer_leakage_flagged(tmp_path: Path) -> None:
    dataset = _dataset(tmp_path, [_task("task_1", "The answer is secret42; report it.", "secret42")])
    report = check_static_leakage_for_dataset(dataset, repo_root=tmp_path)
    assert any(issue["issue_type"] == "answer_text_leakage" and issue["severity"] == "blocker" for issue in report["issues"])


def test_valid_fixture_passes(tmp_path: Path) -> None:
    dataset = _dataset(
        tmp_path,
        [_task("task_1", "Find the policy threshold using the lookup table.", "500")],
        {"dev": {"base_task_ids": ["task_1"], "instance_ids": ["task_1.clean"]}},
    )
    report = check_static_leakage_for_dataset(dataset, repo_root=tmp_path)
    assert report["passed"] is True
    assert report["issues"] == []


def test_subset_family_overlap_is_informational(tmp_path: Path) -> None:
    """pilot_20 ⊂ pilot_100 ⊂ pilot is expected; duplicates inside the family
    must not appear as blockers."""

    dataset = _dataset(
        tmp_path,
        [_task("task_1", "Find the policy threshold.")],
        {
            "pilot": {"base_task_ids": ["task_1"], "instance_ids": ["task_1.clean"]},
            "pilot_100": {"base_task_ids": ["task_1"], "instance_ids": ["task_1.clean"]},
            "pilot_20": {"base_task_ids": ["task_1"], "instance_ids": ["task_1.clean"]},
            "dev": {"base_task_ids": ["task_1"], "instance_ids": ["task_1.clean"]},
        },
    )
    report = check_static_leakage_for_dataset(dataset, repo_root=tmp_path)
    duplicate_issues = [issue for issue in report["issues"] if issue["finding_type"] in {"duplicate_task_id", "duplicate_instance_id"}]
    assert duplicate_issues, "Subset overlaps should still be reported, but as informational"
    assert all(issue["severity"] == "informational" for issue in duplicate_issues)
    assert all(issue["cluster_classification"] == "expected_subset_overlap" for issue in duplicate_issues)
    assert report["passed"] is True


def test_same_family_protected_overlap_is_needs_review_not_blocker(tmp_path: Path) -> None:
    """Different tasks in the same task family across heldout/pilot should be needs_review,
    not blockers — they're typically scaffolding, not real leakage."""

    dataset_dir = tmp_path / "data/processed/family_overlap"
    dataset_dir.mkdir(parents=True, exist_ok=True)
    # Two different research_assistant tasks with similar scaffolding.
    tasks = [
        {
            "task_id": "research_assistant_hard_003",
            "domain": "research",
            "task_family": "research_assistant_hard",
            "goal": {
                "user_instruction": "Use the research database tool to find relevant papers on memory consolidation and report a concise summary.",
                "expected_final_answer": "summary_for_003",
            },
        },
        {
            "task_id": "research_assistant_hard_025",
            "domain": "research",
            "task_family": "research_assistant_hard",
            "goal": {
                "user_instruction": "Use the research database tool to find relevant papers on attention mechanisms and report a concise summary.",
                "expected_final_answer": "summary_for_025",
            },
        },
    ]
    (dataset_dir / "base_tasks.jsonl").write_text(
        "\n".join(json.dumps(t) for t in tasks) + "\n", encoding="utf-8"
    )
    (dataset_dir / "instances.jsonl").write_text(
        "\n".join(
            json.dumps({"instance_id": f"{t['task_id']}.clean", "condition": "clean", "base_task": t}) for t in tasks
        )
        + "\n",
        encoding="utf-8",
    )
    (dataset_dir / "splits.json").write_text(
        json.dumps(
            {
                "splits": {
                    "heldout": {"base_task_ids": ["research_assistant_hard_003"], "instance_ids": ["research_assistant_hard_003.clean"]},
                    "pilot": {"base_task_ids": ["research_assistant_hard_025"], "instance_ids": ["research_assistant_hard_025.clean"]},
                }
            }
        ),
        encoding="utf-8",
    )
    report = check_static_leakage_for_dataset(dataset_dir, repo_root=tmp_path, near_duplicate_threshold=0.4)
    nd = [i for i in report["issues"] if i["finding_type"] == "near_duplicate_prompt"]
    assert nd, "Expected near-duplicate finding across heldout/pilot"
    family_class = [i for i in nd if i.get("cluster_classification") == "same_family_protected_split_overlap"]
    assert family_class, "Same-family protected-split overlap should be classified specifically"
    assert all(i["severity"] in {"warning", "needs_review", "informational"} for i in family_class)
    # No blocker should be raised for this same-family overlap.
    assert not any(i["severity"] == "blocker" for i in family_class)


def test_cross_family_protected_overlap_still_blocks(tmp_path: Path) -> None:
    """Different task families with high task-specific overlap across heldout/pilot must still block."""

    dataset_dir = tmp_path / "data/processed/cross_family"
    dataset_dir.mkdir(parents=True, exist_ok=True)
    tasks = [
        {
            "task_id": "task_a_family_a_000",
            "domain": "domainA",
            "task_family": "family_a",
            "goal": {
                "user_instruction": "Find policy threshold and verify lookup database identification process accurately.",
                "expected_final_answer": "100",
            },
        },
        {
            "task_id": "task_b_family_b_000",
            "domain": "domainB",
            "task_family": "family_b",
            "goal": {
                "user_instruction": "Find policy threshold and verify lookup database identification process accurately.",
                "expected_final_answer": "200",
            },
        },
    ]
    (dataset_dir / "base_tasks.jsonl").write_text("\n".join(json.dumps(t) for t in tasks) + "\n", encoding="utf-8")
    (dataset_dir / "instances.jsonl").write_text(
        "\n".join(
            json.dumps({"instance_id": f"{t['task_id']}.clean", "condition": "clean", "base_task": t}) for t in tasks
        )
        + "\n",
        encoding="utf-8",
    )
    (dataset_dir / "splits.json").write_text(
        json.dumps(
            {
                "splits": {
                    "heldout": {"base_task_ids": ["task_a_family_a_000"], "instance_ids": ["task_a_family_a_000.clean"]},
                    "pilot": {"base_task_ids": ["task_b_family_b_000"], "instance_ids": ["task_b_family_b_000.clean"]},
                }
            }
        ),
        encoding="utf-8",
    )
    report = check_static_leakage_for_dataset(dataset_dir, repo_root=tmp_path, near_duplicate_threshold=0.4)
    nd = [i for i in report["issues"] if i["finding_type"] == "near_duplicate_prompt"]
    assert nd
    cross = [i for i in nd if i.get("cluster_classification") == "true_split_leakage"]
    assert cross, "Cross-family protected-split overlap should still be true_split_leakage"
    assert any(i["severity"] == "blocker" for i in cross)


def test_pilot_into_heldout_still_blocks(tmp_path: Path) -> None:
    """A duplicate ID crossing pilot/heldout boundary must remain a blocker."""

    dataset = _dataset(
        tmp_path,
        [_task("task_1", "Find the policy threshold.")],
        {
            "pilot": {"base_task_ids": ["task_1"], "instance_ids": ["task_1.clean"]},
            "heldout": {"base_task_ids": ["task_1"], "instance_ids": ["task_1.clean"]},
        },
    )
    report = check_static_leakage_for_dataset(dataset, repo_root=tmp_path)
    duplicates = [issue for issue in report["issues"] if issue["finding_type"] in {"duplicate_task_id", "duplicate_instance_id"}]
    assert duplicates, "pilot↔heldout overlap must be flagged"
    assert any(issue["severity"] == "blocker" for issue in duplicates)


def test_subset_families_declared_in_splits_json_take_precedence(tmp_path: Path) -> None:
    """Explicit subset_families declared in splits.json should be honored."""

    dataset_dir = tmp_path / "data/processed/custom"
    dataset_dir.mkdir(parents=True, exist_ok=True)
    (dataset_dir / "base_tasks.jsonl").write_text(
        json.dumps({"task_id": "task_1", "domain": "policy", "goal": {"user_instruction": "Find x.", "expected_final_answer": "ok"}}) + "\n",
        encoding="utf-8",
    )
    (dataset_dir / "instances.jsonl").write_text(
        json.dumps({"instance_id": "task_1.clean", "condition": "clean", "base_task": {"task_id": "task_1", "domain": "policy", "goal": {"user_instruction": "Find x.", "expected_final_answer": "ok"}}}) + "\n",
        encoding="utf-8",
    )
    (dataset_dir / "splits.json").write_text(
        json.dumps(
            {
                "subset_families": [["family_a", "family_b"]],
                "splits": {
                    "family_a": {"base_task_ids": ["task_1"], "instance_ids": ["task_1.clean"]},
                    "family_b": {"base_task_ids": ["task_1"], "instance_ids": ["task_1.clean"]},
                },
            }
        ),
        encoding="utf-8",
    )
    report = check_static_leakage_for_dataset(dataset_dir, repo_root=tmp_path)
    duplicates = [issue for issue in report["issues"] if issue["finding_type"] in {"duplicate_task_id", "duplicate_instance_id"}]
    assert duplicates
    assert all(issue["severity"] == "informational" for issue in duplicates)


def test_repeated_duplicate_findings_cluster_into_one_root_cause(tmp_path: Path) -> None:
    splits = {
        "dev": {"base_task_ids": [f"task_{idx}" for idx in range(20)], "instance_ids": [f"task_{idx}.clean" for idx in range(20)]},
        "heldout": {"base_task_ids": [f"task_{idx}" for idx in range(20)], "instance_ids": [f"task_{idx}.clean" for idx in range(20)]},
    }
    dataset = _dataset(tmp_path, [_task(f"task_{idx}", f"Find threshold {idx}.") for idx in range(20)], splits)
    report = check_static_leakage_for_dataset(dataset, repo_root=tmp_path)
    duplicate_roots = [row for row in report["root_causes"] if row["finding_type"] == "duplicate_task_id"]
    assert duplicate_roots
    assert sum(row["symptom_count"] for row in duplicate_roots) >= 20
    assert report["raw_findings"]


def test_markdown_does_not_list_thousands_of_raw_findings(tmp_path: Path) -> None:
    tasks = [
        _task(f"task_{idx}", "Find the policy threshold using the database and report a concise answer.", str(idx))
        for idx in range(65)
    ]
    dataset = _dataset(tmp_path, tasks)
    report = build_static_leakage_report(
        tmp_path,
        benchmark_dir=dataset,
        output_dir=tmp_path / "reports",
        near_duplicate_threshold=0.70,
        max_raw_findings_in_markdown=10,
    )
    md = Path(report["report_paths"]["markdown"]).read_text(encoding="utf-8")
    assert report["raw_finding_count"] > 1000
    assert report["cluster_count"] < report["raw_finding_count"]
    assert "Raw finding examples capped at 10" in md
    assert md.count("`near_duplicate_prompt`") <= 10


def test_protected_split_leakage_ranks_above_generic_near_duplicate(tmp_path: Path) -> None:
    dataset = _dataset(
        tmp_path,
        [
            _task("task_1", "Find the policy threshold using the database and report a concise answer."),
            _task("task_2", "Find the policy threshold using the database and report a concise final answer."),
        ],
        {
            "pilot": {"base_task_ids": ["task_1"], "instance_ids": ["task_1.clean"]},
            "heldout": {"base_task_ids": ["task_1"], "instance_ids": ["task_1.clean"]},
        },
    )
    report = check_static_leakage_for_dataset(dataset, repo_root=tmp_path, near_duplicate_threshold=0.75)
    assert report["root_causes"][0]["readiness_gate"] == "must_fix_before_provider_pilot"
    assert report["root_causes"][0]["severity"] == "blocker"


def test_false_positive_candidates_section_exists(tmp_path: Path) -> None:
    dataset = _dataset(
        tmp_path,
        [
            _task("task_1", "Find the policy threshold using the database and report a concise answer."),
            _task("task_2", "Find the policy threshold using the database and report a concise final answer."),
        ],
    )
    report = build_static_leakage_report(tmp_path, benchmark_dir=dataset, output_dir=tmp_path / "reports", near_duplicate_threshold=0.75)
    assert "false_positive_candidates" in report
    assert Path(report["report_paths"]["json"]).exists()


def test_missing_split_metadata_does_not_crash(tmp_path: Path) -> None:
    dataset = _dataset(tmp_path, [_task("task_1", "Find the threshold.")], splits=None)
    report = check_static_leakage_for_dataset(dataset, repo_root=tmp_path)
    assert report["split_count"] == 0


def test_boilerplate_only_overlap_becomes_false_positive_candidate(tmp_path: Path) -> None:
    dataset = _dataset(
        tmp_path,
        [
            _task("task_1", "Use tool lookup database table report concise final answer.", "alpha"),
            _task("task_2", "Use tool lookup database table report concise final answer.", "beta"),
        ],
        {
            "dev": {"base_task_ids": ["task_1"], "instance_ids": ["task_1.clean"]},
            "heldout": {"base_task_ids": ["task_2"], "instance_ids": ["task_2.clean"]},
        },
    )
    report = check_static_leakage_for_dataset(dataset, repo_root=tmp_path, near_duplicate_threshold=0.75)
    near_roots = [row for row in report["root_causes"] if row["finding_type"] == "near_duplicate_prompt"]
    assert near_roots
    assert near_roots[0]["leakage_risk"] == "false_positive_candidate"
    assert near_roots[0]["severity"] == "informational"


def test_task_specific_overlap_across_protected_splits_is_blocker(tmp_path: Path) -> None:
    # Use different task families so this is a true cross-family blocker.
    task_a = _task("task_1", "Investigate account redwood orbit cobalt invoice anomaly and cite vendor zeta.", "alpha", domain="finance_audit")
    task_b = _task("task_2", "Investigate account redwood orbit cobalt invoice anomaly and cite vendor eta.", "beta", domain="research_writing")
    dataset = _dataset(
        tmp_path,
        [task_a, task_b],
        {
            "dev": {"base_task_ids": ["task_1"], "instance_ids": ["task_1.clean"]},
            "heldout": {"base_task_ids": ["task_2"], "instance_ids": ["task_2.clean"]},
        },
    )
    report = check_static_leakage_for_dataset(dataset, repo_root=tmp_path, near_duplicate_threshold=0.70)
    roots = [row for row in report["root_causes"] if row["finding_type"] == "near_duplicate_prompt"]
    assert roots[0]["cluster_classification"] == "true_split_leakage"
    assert roots[0]["leakage_risk"] == "blocker"


def test_answer_leakage_remains_blocker_despite_boilerplate(tmp_path: Path) -> None:
    dataset = _dataset(
        tmp_path,
        [_task("task_1", "Use tool lookup database table report concise final answer secret42.", "secret42")],
        {"dev": {"base_task_ids": ["task_1"], "instance_ids": ["task_1.clean"]}},
    )
    report = check_static_leakage_for_dataset(dataset, repo_root=tmp_path)
    roots = [row for row in report["root_causes"] if row["finding_type"] == "answer_text_leakage"]
    assert roots[0]["cluster_classification"] == "answer_leakage"
    assert roots[0]["leakage_risk"] == "blocker"


def test_linked_clean_intervention_pair_similarity_not_true_leakage(tmp_path: Path) -> None:
    task = _task("task_1", "Investigate account redwood orbit cobalt invoice anomaly.", "alpha")
    dataset = tmp_path / "data/processed/tiny"
    _write_jsonl(dataset / "base_tasks.jsonl", [task])
    _write_jsonl(
        dataset / "instances.jsonl",
        [
            {"instance_id": "task_1.clean", "condition": "clean", "base_task": task},
            {
                "instance_id": "task_1.memory_corruption",
                "condition": "intervention",
                "base_task": task,
                "intervention": {"base_task_id": "task_1", "family": "memory_corruption"},
            },
        ],
    )
    (dataset / "splits.json").write_text(
        json.dumps({"splits": {"dev": {"base_task_ids": ["task_1"], "instance_ids": ["task_1.clean", "task_1.memory_corruption"]}}}),
        encoding="utf-8",
    )
    report = check_static_leakage_for_dataset(dataset, repo_root=tmp_path, near_duplicate_threshold=0.70)
    near_roots = [row for row in report["root_causes"] if row["finding_type"] == "near_duplicate_prompt"]
    assert near_roots[0]["cluster_classification"] == "clean_intervention_pair_similarity"
    assert near_roots[0]["leakage_risk"] == "false_positive_candidate"


def test_clean_intervention_pair_across_protected_split_flagged(tmp_path: Path) -> None:
    task = _task("task_1", "Investigate account redwood orbit cobalt invoice anomaly.", "alpha")
    dataset = tmp_path / "data/processed/tiny"
    _write_jsonl(dataset / "base_tasks.jsonl", [task])
    _write_jsonl(
        dataset / "instances.jsonl",
        [
            {"instance_id": "task_1.clean", "condition": "clean", "base_task": task},
            {
                "instance_id": "task_1.memory_corruption",
                "condition": "intervention",
                "base_task": task,
                "intervention": {"base_task_id": "task_1", "family": "memory_corruption"},
            },
        ],
    )
    (dataset / "splits.json").write_text(
        json.dumps(
            {
                "splits": {
                    "dev": {"base_task_ids": ["task_1"], "instance_ids": ["task_1.clean"]},
                    "heldout": {"base_task_ids": [], "instance_ids": ["task_1.memory_corruption"]},
                }
            }
        ),
        encoding="utf-8",
    )
    report = check_static_leakage_for_dataset(dataset, repo_root=tmp_path, near_duplicate_threshold=0.70)
    assert any(row["cluster_classification"] == "split_metadata_issue" and row["leakage_risk"] == "blocker" for row in report["root_causes"])


def test_same_family_boilerplate_across_split_not_blocker(tmp_path: Path) -> None:
    dataset = _dataset(
        tmp_path,
        [
            _task("task_1", "Answer final concise report given task instruction policy.", "alpha"),
            _task("task_2", "Answer final concise report given task instruction policy.", "beta"),
        ],
        {
            "dev": {"base_task_ids": ["task_1"], "instance_ids": ["task_1.clean"]},
            "heldout": {"base_task_ids": ["task_2"], "instance_ids": ["task_2.clean"]},
        },
    )
    report = check_static_leakage_for_dataset(dataset, repo_root=tmp_path, near_duplicate_threshold=0.70)
    near_roots = [row for row in report["root_causes"] if row["finding_type"] == "near_duplicate_prompt"]
    assert near_roots
    assert near_roots[0]["leakage_risk"] == "false_positive_candidate"


def test_missing_split_metadata_near_duplicate_needs_review(tmp_path: Path) -> None:
    dataset = _dataset(
        tmp_path,
        [
            _task("task_1", "Investigate account redwood orbit cobalt invoice anomaly.", "alpha"),
            _task("task_2", "Investigate account redwood orbit cobalt invoice anomaly.", "beta"),
        ],
        splits=None,
    )
    report = check_static_leakage_for_dataset(dataset, repo_root=tmp_path, near_duplicate_threshold=0.70)
    near_roots = [row for row in report["root_causes"] if row["finding_type"] == "near_duplicate_prompt"]
    assert near_roots[0]["cluster_classification"] == "split_metadata_issue"
    assert near_roots[0]["leakage_risk"] == "needs_review"
