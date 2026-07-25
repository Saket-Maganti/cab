from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]


def _read(relative: str) -> str:
    return (REPO / relative).read_text(encoding="utf-8")


def test_no_run_build_expected_artifacts_exist() -> None:
    expected = [
        "docs/FOCUSED_PROJECT_THESIS.md",
        "docs/CLAIM_TRIAGE_NO_RUN.md",
        "docs/TITLE_AND_FRAMING_OPTIONS.md",
        "reports/GOLD_WARNING_INVENTORY_NO_RUN.md",
        "docs/GOLD_POLICY_DECISION_MATRIX.md",
        "docs/COMPACT20_SELECTION_CRITERIA.md",
        "data/human_validation/no_api_task_review/compact20_candidate_manifest.json",
        "data/human_validation/no_api_task_review/compact20_task_review.csv",
        "docs/C10_INTERVENTION_ISOLATION_VALIDATION_PROTOCOL.md",
        "data/human_validation/c10_isolation_review/c10_isolation_annotation_template.csv",
        "paper/NO_RUN_PAPER_SKELETON.md",
        "paper/FIGURE_TABLE_SPEC_NO_RUN.md",
        "paper/PAPER_WORDING_GUARDRAILS.md",
        "docs/RELATED_WORK_GAP_MAP.md",
        "docs/NOVELTY_BOUNDARY_MEMO.md",
        "docs/DOCUMENTATION_FREEZE_POLICY.md",
        "experiments/FUTURE_3MODEL_COMPACT20_PILOT_RUNBOOK_NO_EXECUTION.md",
        "configs/compact20_3model_TEMPLATE_NOT_APPROVED.yaml",
        "docs/REVIEWER_SIMULATION_NO_RUN.md",
        "docs/SUBMISSION_LADDER.md",
        "reports/FINAL_NO_RUN_BUILD_GATE.md",
    ]
    missing = [relative for relative in expected if not (REPO / relative).exists()]
    assert missing == []


def test_claim_triage_keeps_claims_unsupported() -> None:
    triage = _read("docs/CLAIM_TRIAGE_NO_RUN.md")
    thesis = _read("docs/FOCUSED_PROJECT_THESIS.md")
    assert "C1-C8 and C10 must remain planned/unsupported" in triage
    assert "C9 may be described only as engineering reproducibility" in triage
    assert "Outcome-success leaderboards" in thesis
    assert "It cannot yet say the interventions empirically isolate" in thesis


def test_compact20_manifest_is_manual_review_only() -> None:
    manifest = json.loads(_read("data/human_validation/no_api_task_review/compact20_candidate_manifest.json"))
    assert manifest["status"] == "no_run_manual_review_pending"
    assert "no_provider_evidence" in manifest["labels"]
    assert manifest["candidate_count"] == 20
    assert {candidate["family"] for candidate in manifest["candidates"]} == {
        "tool_failure",
        "tool_removal",
        "memory_corruption",
        "observation_conflict",
    }
    assert all(candidate["status"] == "no_run_manual_review_pending" for candidate in manifest["candidates"])

    rows = list(
        csv.DictReader(
            (REPO / "data/human_validation/no_api_task_review/compact20_task_review.csv").open(
                newline="", encoding="utf-8"
            )
        )
    )
    assert len(rows) == 20
    reviewer_fields = ["task_clear", "intervention_isolated", "gold_policy_clear", "include_in_compact20"]
    assert all(row[field] == "" for row in rows for field in reviewer_fields)


def test_c10_packet_cannot_support_validation_yet() -> None:
    status = _read("reports/C10_VALIDATION_STATUS_NO_RUN.md")
    assert "C10_UNSUPPORTED_MANUAL_PACKET_READY" in status
    assert "Completed annotations: `0`" in status
    assert "Agreement metrics: not computed" in status

    rows = list(
        csv.reader(
            (REPO / "data/human_validation/c10_isolation_review/c10_isolation_annotation_template.csv").open(
                newline="", encoding="utf-8"
            )
        )
    )
    assert len(rows) == 1


def test_future_compact20_template_is_not_runnable_and_has_no_secrets() -> None:
    template_path = REPO / "configs/compact20_3model_TEMPLATE_NOT_APPROVED.yaml"
    template = yaml.safe_load(template_path.read_text(encoding="utf-8"))
    assert template["template_only"] is True
    assert template["not_runnable_without_approval"] is True
    assert template["allow_paid_calls"] is False
    assert template["approved_for_live_run"] is False
    assert template["scientific_claims"] is False
    assert template["claim_policy"]["promote_claims"] is False
    assert template["claim_policy"]["mark_paper_assets_eligible"] is False

    scanned = [
        template_path,
        REPO / "experiments/FUTURE_3MODEL_COMPACT20_PILOT_RUNBOOK_NO_EXECUTION.md",
        REPO / "configs/COMPACT20_CONFIG_PLAN_NO_RUN.md",
    ]
    secret_value_pattern = re.compile("".join(["s", "k", "-", r"[A-Za-z0-9]{20,}"]))
    forbidden_secret_fields = re.compile(
        r"(?im)^\s*(api_key|apikey|openai_api_key|anthropic_api_key|gemini_api_key)\s*:"
    )
    for path in scanned:
        text = path.read_text(encoding="utf-8")
        assert not secret_value_pattern.search(text), path
        assert not forbidden_secret_fields.search(text), path


def test_paper_skeleton_has_no_empirical_result_claims() -> None:
    skeleton = _read("paper/NO_RUN_PAPER_SKELETON.md").lower()
    for forbidden in ["we demonstrate", "we find", "validated benchmark", "model rankings"]:
        assert forbidden not in skeleton
    assert "empirical results, human-validation claims, and leaderboard claims are not yet reported" in skeleton
    assert "provider outputs" in skeleton

    figure_spec = _read("paper/FIGURE_TABLE_SPEC_NO_RUN.md")
    assert "future required result assets" in figure_spec
    assert "None is currently paper-eligible" in figure_spec


def test_final_gate_recommends_manual_review_not_claim_promotion() -> None:
    gate = _read("reports/FINAL_NO_RUN_BUILD_GATE.md")
    remaining = _read("reports/NO_RUN_BUILD_REMAINING_TASKS.md")
    stop = _read("reports/STOP_BUILDING_START_REVIEWING.md")
    assert "STOP_BUILDING_MANUAL_REVIEW_NEXT" in gate
    assert "Provider-backed evidence: `0`" in gate
    assert "Human annotations: `0`" in gate
    assert "Eligible paper assets: `0`" in gate
    assert "Do not call providers" in remaining
    assert "The next useful work is not more scaffolding" in stop

