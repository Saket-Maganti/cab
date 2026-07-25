"""Fixture-only tests for god-tier blocker cleanup (no runs, no providers)."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from causal_agent_bench.safety.answer_leakage_repair import (
    build_answer_leakage_repair_packet,
    validate_answer_leakage_cleared,
)
from causal_agent_bench.safety.common import compute_run_index_freshness
from causal_agent_bench.safety.evidence_dashboard import build_evidence_dashboard
from causal_agent_bench.safety.provider_pilot_preflight import validate_provider_pilot_preflight
from causal_agent_bench.safety.static_leakage import check_static_leakage_for_dataset


def _dataset(tmp_path: Path, tasks: list[dict], splits: dict) -> Path:
    dataset = tmp_path / "data/processed/tiny"
    dataset.mkdir(parents=True, exist_ok=True)
    instances = []
    for task in tasks:
        instances.append({"instance_id": f"{task['task_id']}.clean", "condition": "clean", "base_task": task})
    (dataset / "base_tasks.jsonl").write_text("\n".join(json.dumps(t) for t in tasks) + "\n", encoding="utf-8")
    (dataset / "instances.jsonl").write_text("\n".join(json.dumps(i) for i in instances) + "\n", encoding="utf-8")
    (dataset / "splits.json").write_text(json.dumps({"splits": splits, "subset_families": [["dev", "pilot_20"]]}), encoding="utf-8")
    return dataset


def _task(task_id: str, instruction: str, answer: str) -> dict:
    return {
        "task_id": task_id,
        "goal": {
            "user_instruction": instruction,
            "expected_final_answer": answer,
        },
    }


def test_instruction_date_overlap_not_provider_blocker(tmp_path: Path) -> None:
    dataset = _dataset(
        tmp_path,
        [
            _task(
                "task_cal",
                "Check Mina's calendar on 2026-06-03 and draft an email.",
                {"date": "2026-06-03", "slot": "15:00"},
            )
        ],
        {"dev": {"base_task_ids": ["task_cal"], "instance_ids": ["task_cal.clean"]}},
    )
    report = check_static_leakage_for_dataset(dataset, repo_root=tmp_path)
    answer_roots = [
        r
        for r in report["root_causes"]
        if r.get("cluster_classification") == "answer_leakage" and r.get("leakage_risk") == "blocker"
    ]
    assert answer_roots == []
    overlap = [r for r in report["root_causes"] if r.get("cluster_classification") == "instruction_parameter_overlap"]
    assert overlap


def test_true_answer_spoiler_remains_blocker(tmp_path: Path) -> None:
    dataset = _dataset(
        tmp_path,
        [_task("task_1", "Use tools and write the final answer secret42.", "secret42")],
        {"dev": {"base_task_ids": ["task_1"], "instance_ids": ["task_1.clean"]}},
    )
    report = check_static_leakage_for_dataset(dataset, repo_root=tmp_path)
    roots = [r for r in report["root_causes"] if r.get("cluster_classification") == "answer_leakage"]
    assert roots and roots[0]["leakage_risk"] == "blocker"


def test_expected_subset_overlap_not_provider_blocker(tmp_path: Path) -> None:
    dataset = tmp_path / "data/processed/subset"
    dataset.mkdir(parents=True, exist_ok=True)
    task = _task("task_1", "Do something unique redwood orbit.", "alpha")
    (dataset / "base_tasks.jsonl").write_text(json.dumps(task) + "\n", encoding="utf-8")
    (dataset / "instances.jsonl").write_text(
        "\n".join(
            [
                json.dumps({"instance_id": "task_1.clean", "condition": "clean", "base_task": task}),
                json.dumps({"instance_id": "task_1.clean", "condition": "clean", "base_task": task}),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (dataset / "splits.json").write_text(
        json.dumps(
            {
                "splits": {
                    "pilot_20": {"instance_ids": ["task_1.clean"]},
                    "pilot": {"instance_ids": ["task_1.clean"]},
                },
                "subset_families": [["pilot_20", "pilot"]],
            }
        ),
        encoding="utf-8",
    )
    report = check_static_leakage_for_dataset(dataset, repo_root=tmp_path)
    blockers = [r for r in report["root_causes"] if r.get("leakage_risk") == "blocker"]
    assert not any(r.get("cluster_classification") == "expected_subset_overlap" for r in blockers)


def test_answer_leakage_repair_packet_and_validator(tmp_path: Path) -> None:
    dataset = _dataset(
        tmp_path,
        [_task("task_1", "The final answer is BOGUS99 in the prompt.", "BOGUS99")],
        {"dev": {"base_task_ids": ["task_1"], "instance_ids": ["task_1.clean"]}},
    )
    report = check_static_leakage_for_dataset(dataset, repo_root=tmp_path)
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / "static_leakage_report.json").write_text(json.dumps(report), encoding="utf-8")

    packet = build_answer_leakage_repair_packet(tmp_path, leakage_report_path=reports_dir / "static_leakage_report.json")
    assert packet["summary"]["blocker_cluster_count"] >= 1
    assert packet["worksheets"][0]["manual_review_required"] is True

    validation = validate_answer_leakage_cleared(
        tmp_path, dataset / "instances.jsonl", instance_ids=["task_1.clean"]
    )
    assert validation["remaining_blockers"] >= 1


def test_provider_gate_blocked_with_true_leakage_report(tmp_path: Path) -> None:
    config = tmp_path / "configs/provider_pilot_tiny_template.yaml"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        yaml.safe_dump(
            {
                "run_name": "provider_pilot_tiny_PENDING_APPROVAL",
                "allow_paid_calls": False,
                "scientific_evidence": False,
                "evidence_scope": "provider_pilot_pending_verification",
                "approval": {"approved_for_live_run": False, "advisor_approved": False},
                "limits": {"max_instances": 5, "stop_after_trajectories": 5},
                "budget": {"max_total_usd": 5.0},
                "agent_runs": [{"agent": "direct_tool_agent", "provider": "openai", "model": "gpt-test"}],
            }
        ),
        encoding="utf-8",
    )
    reports = tmp_path / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "static_leakage").mkdir(parents=True, exist_ok=True)
    (reports / "static_leakage" / "static_leakage_report.json").write_text(
        json.dumps(
            {
                "summary": {"blocker_cluster_count": 2},
                "top_provider_pilot_blockers": [
                    {"cluster_classification": "answer_leakage", "leakage_risk": "blocker"}
                ],
            }
        ),
        encoding="utf-8",
    )
    preflight = validate_provider_pilot_preflight(config, repo_root=tmp_path, reports_dir=reports)
    assert any(c["id"] == "leakage_repair_must_fix" for c in preflight["blockers"])
    assert "answer-leakage" in preflight["gate_summary"]["exact_next_action"].lower()


def test_dashboard_next_action_mentions_leakage_when_blocked(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    static_dir = reports / "static_leakage"
    static_dir.mkdir(parents=True, exist_ok=True)
    (static_dir / "static_leakage_report.json").write_text(
        json.dumps(
            {
                "summary": {"blocker_cluster_count": 1, "blockers": 1},
                "top_provider_pilot_blockers": [{"cluster_classification": "answer_leakage"}],
            }
        ),
        encoding="utf-8",
    )
    plan_dir = reports / "leakage_repair_plan"
    plan_dir.mkdir(parents=True, exist_ok=True)
    (plan_dir / "leakage_repair_plan.json").write_text(
        json.dumps({"summary": {"must_fix_before_provider_pilot_count": 1}}),
        encoding="utf-8",
    )
    (reports / "provider_pilot_preflight.json").write_text(
        json.dumps({"verdicts": {"blocked": True}, "gate_summary": {"exact_next_action": "blocked"}}),
        encoding="utf-8",
    )
    dash = build_evidence_dashboard(tmp_path, reports_dir=reports, output_dir=tmp_path / "dash")
    assert "leakage" in dash["next_required_action"].lower()
    assert dash["provider_pilot_gate"]["leakage_must_fix_count"] == 1


def test_stale_index_detection_unchanged(tmp_path: Path) -> None:
    results = tmp_path / "results"
    results.mkdir(parents=True, exist_ok=True)
    for name in ("run_a", "run_b"):
        run = results / name
        run.mkdir()
        (run / "run_metadata.json").write_text(
            json.dumps(
                {
                    "run_name": name,
                    "config_hash": "h",
                    "evidence_scope": "pilot_stub_engineering_only",
                    "provider_type": "stub",
                    "scientific_evidence": False,
                }
            ),
            encoding="utf-8",
        )
    (results / "RUN_INDEX.jsonl").write_text(
        json.dumps({"run_id": "run_a", "path": str(results / "run_a")}) + "\n",
        encoding="utf-8",
    )
    fresh = compute_run_index_freshness(tmp_path)
    assert fresh["index_stale"] is True
    assert fresh["live_run_count"] == 2
