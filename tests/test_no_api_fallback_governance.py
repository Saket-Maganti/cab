from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]

NO_API_ARTIFACTS = [
    REPO / "reports" / "NO_API_KEY_PROVIDER_PILOT_BLOCKER.md",
    REPO / "docs" / "FUTURE_PROVIDER_API_KEY_CHECKLIST.md",
    REPO / "experiments" / "NO_API_COMPACT_VALIDATION_PLAN.md",
    REPO / "data" / "human_validation" / "no_api_task_review" / "README.md",
    REPO / "data" / "human_validation" / "no_api_task_review" / "task_review_template.csv",
    REPO / "data" / "human_validation" / "no_api_task_review" / "gold_policy_review_template.csv",
]


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_no_api_blocker_report_exists_when_provider_key_missing(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    report = REPO / "reports" / "NO_API_KEY_PROVIDER_PILOT_BLOCKER.md"
    text = _text(report)
    assert report.exists()
    assert "OPENAI_API_KEY" in text
    assert "blocked" in text.lower()
    assert "Provider-backed scientific runs | `0`" in text
    assert "no provider calls were made" in text.lower()


def test_no_api_artifacts_cannot_support_c1_c8() -> None:
    combined = "\n".join(_text(path) for path in NO_API_ARTIFACTS)
    assert "C1-C8" in combined
    assert "unsupported" in combined.lower()
    assert "no_provider_evidence" in combined
    assert "not_scientific_model_performance" in combined


def test_no_api_task_review_cannot_support_c3_trajectory_claims() -> None:
    readme = _text(REPO / "data" / "human_validation" / "no_api_task_review" / "README.md")
    plan = _text(REPO / "experiments" / "NO_API_COMPACT_VALIDATION_PLAN.md")
    combined = f"{readme}\n{plan}"
    assert "C3 trajectory claims" in combined
    assert "cannot support" in combined
    assert "C10 must remain pending" in readme


def test_no_api_validation_is_engineering_only() -> None:
    plan = _text(REPO / "experiments" / "NO_API_COMPACT_VALIDATION_PLAN.md")
    for label in (
        "engineering_only",
        "no_provider_evidence",
        "not_scientific_model_performance",
    ):
        assert label in plan
    assert "does not create provider-backed evidence" in plan


def test_approved_config_keeps_allow_paid_calls_false() -> None:
    config = yaml.safe_load((REPO / "configs" / "provider_pilot_tiny_APPROVED.yaml").read_text(encoding="utf-8"))
    assert config["allow_paid_calls"] is False
    assert config["approval"]["approved_for_live_run"] is False
    assert config["scientific_evidence"] is False
    assert config["evidence_scope"] == "provider_pilot_debug_or_preliminary"


def test_api_keys_are_not_written_to_no_api_repo_files() -> None:
    secret_value_pattern = re.compile("".join(["s", "k", "-", r"[A-Za-z0-9]{20,}"]))
    forbidden_secret_fields = re.compile(
        r"(?im)^\s*(api_key|apikey|openai_api_key|anthropic_api_key|gemini_api_key)\s*:"
    )
    scanned = [
        *NO_API_ARTIFACTS,
        REPO / "configs" / "provider_pilot_tiny_APPROVED.yaml",
        REPO / "docs" / "COMPACT_PAPER_STRATEGY.md",
        REPO / "paper" / "COMPACT_EMPIRICAL_PAPER_BLUEPRINT.md",
    ]
    for path in scanned:
        text = _text(path)
        assert not secret_value_pattern.search(text), path
        assert not forbidden_secret_fields.search(text), path
