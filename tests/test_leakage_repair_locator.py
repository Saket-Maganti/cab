"""Fixture-only tests: answer-leakage repair worksheets carry a file locator.

Section B requires the manual repair packet to tell a reviewer which file to
open and what the leak looks like, while never auto-applying a content rewrite.
"""

from __future__ import annotations

import json
from pathlib import Path

from causal_agent_bench.safety.leakage_repair_planner import build_leakage_repair_plan


def _write_static_leakage_report(reports_dir: Path) -> None:
    reports_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "root_causes": [
            {
                "root_cause_id": "leak_answer_1",
                "cluster_classification": "answer_leakage",
                "leakage_risk": "blocker",
                "severity": "blocker",
                "symptom_count": 1,
                "affected_instance_ids": ["task_42.clean"],
                "affected_task_ids": ["task_42"],
                "affected_splits": ["dev"],
                "representative_examples": [
                    {
                        "entity_id": "task_42.clean",
                        "message": "Expected answer text `2026-06-03` appears in visible prompt/context.",
                        "cluster_classification": "answer_leakage",
                    }
                ],
                "recommended_action": "rewrite_prompt",
                "readiness_gate": "must_fix_before_provider_pilot",
            }
        ]
    }
    (reports_dir / "static_leakage_report.json").write_text(json.dumps(payload), encoding="utf-8")


def _write_dataset(repo_root: Path) -> None:
    dataset = repo_root / "data/processed/tiny"
    dataset.mkdir(parents=True, exist_ok=True)
    instance = {
        "instance_id": "task_42.clean",
        "condition": "clean",
        "prompt": "The answer is 2026-06-03. What date?",
    }
    (dataset / "instances.jsonl").write_text(json.dumps(instance) + "\n", encoding="utf-8")


def test_answer_leakage_worksheet_has_file_locator(tmp_path: Path) -> None:
    reports_dir = tmp_path / "reports"
    _write_static_leakage_report(reports_dir)
    _write_dataset(tmp_path)

    plan = build_leakage_repair_plan(
        tmp_path, input_dir=reports_dir, output_dir=tmp_path / "out"
    )

    repairs = plan["top_answer_leakage_repairs"]
    assert len(repairs) == 1
    item = repairs[0]
    assert item["dataset_files"] == ["data/processed/tiny/instances.jsonl"]
    assert "2026-06-03" in item["representative_leak_snippet"]

    manifest = json.loads((tmp_path / "out" / "proposed_patch_manifest.json").read_text())
    op = next(o for o in manifest["operations"] if o["type"] == "remove_prompt_answer_leakage")
    assert op["affected_files"] == ["data/processed/tiny/instances.jsonl"]
    assert op["details"]["rewrite_recommendation"]
    assert op["details"]["leak_description"]
    # Critically: still manual-only, never auto-applied.
    assert op["safe_to_auto_patch"] is False
    assert op["requires_manual_review"] is True


def test_locator_pass_does_not_modify_dataset(tmp_path: Path) -> None:
    reports_dir = tmp_path / "reports"
    _write_static_leakage_report(reports_dir)
    _write_dataset(tmp_path)
    dataset_file = tmp_path / "data/processed/tiny/instances.jsonl"
    before = dataset_file.read_text(encoding="utf-8")

    build_leakage_repair_plan(tmp_path, input_dir=reports_dir, output_dir=tmp_path / "out")

    assert dataset_file.read_text(encoding="utf-8") == before
