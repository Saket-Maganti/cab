from __future__ import annotations

import csv
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]


def _read(relative: str) -> str:
    return (REPO / relative).read_text(encoding="utf-8")


def test_self_authorized_approved_config_is_dry_run_only() -> None:
    approval = _read("docs/approvals/SELF_AUTHORIZATION_TINY_PROVIDER_PILOT.md")
    approved = yaml.safe_load(_read("configs/provider_pilot_tiny_APPROVED.yaml"))
    assert "Dry-run approval: Yes" in approval
    assert "Live-run approval: No" in approval
    assert approved["allow_paid_calls"] is False
    assert approved["approval"]["approved_for_dry_run"] is True
    assert approved["approval"]["approved_for_live_run"] is False
    assert approved["limits"]["max_trajectories"] <= 5
    assert approved["budget"]["max_calls"] <= 30


def test_tiny_pilot_cannot_support_final_claims() -> None:
    approved = yaml.safe_load(_read("configs/provider_pilot_tiny_APPROVED.yaml"))
    strategy = _read("docs/COMPACT_PAPER_STRATEGY.md")
    assert approved["scientific_evidence"] is False
    assert approved["scientific_evidence_level"] == "preliminary_or_engineering"
    assert "They do not support C1-C8, C10" in strategy
    assert "pipeline sanity" in strategy


def test_scorer_sanity_required_before_compact_benchmark() -> None:
    scorer = _read("reports/SCORER_SANITY_BLOCKED_NO_PROVIDER_OUTPUTS.md")
    plan = _read("experiments/COMPACT_EMPIRICAL_BENCHMARK_PLAN.md")
    assert "blocked" in scorer.lower()
    assert "SCORER_SANITY_TINY_PROVIDER_PILOT.md" in plan
    assert "Before Compact-20" in plan


def test_gold_policy_forbids_ambiguous_autofix() -> None:
    policy = _read("docs/GOLD_OUTPUT_POLICY.md")
    triage = _read("reports/GOLD_OUTPUT_TRIAGE_COMPACT_PLAN.md")
    assert "Do not auto-fix frozen data" in policy
    assert "Forbidden" in policy
    assert "Ambiguous cases: exclude" in triage


def test_compact_plan_uses_20_50_not_main_benchmark() -> None:
    plan = _read("experiments/COMPACT_EMPIRICAL_BENCHMARK_PLAN.md")
    config_readme = _read("configs/README_COMPACT_EMPIRICAL.md")
    assert "Compact-20" in plan
    assert "Compact-50" in plan
    assert "Do not run `main_200`" in plan
    assert "Do not run `main_500`" in plan
    assert "20 paired intervention items" in config_readme
    assert "50 paired intervention items" in config_readme


def test_compact_paper_forbids_neurips_ready_claims() -> None:
    paper = _read("paper/COMPACT_EMPIRICAL_PAPER_BLUEPRINT.md")
    strategy = _read("docs/COMPACT_PAPER_STRATEGY.md")
    assert "Forbidden Phrases Until Supported" in paper
    assert "NeurIPS ready" in paper
    assert "Future NeurIPS E&D path requires" in paper
    assert "not ready" in strategy.lower()


def test_human_validation_not_complete_without_annotations() -> None:
    status = _read("reports/HUMAN_VALIDATION_COMPACT_STATUS.md")
    protocol = _read("docs/HUMAN_VALIDATION_COMPACT_PROTOCOL.md")
    assert "Completed annotations | 0" in status
    assert "Agreement metrics | not computed" in status
    assert "No annotations are completed" in protocol


def test_no_paper_asset_eligibility_without_provider_evidence() -> None:
    diagnosis = _read("reports/COMPACT_EMPIRICAL_INTERNAL_DIAGNOSIS.md")
    strategy = _read("docs/COMPACT_PAPER_STRATEGY.md")
    assert "No paper-eligible runs" in diagnosis
    assert "No eligible empirical paper assets" in diagnosis
    assert "paper asset eligibility" in strategy


def test_human_validation_templates_have_only_headers() -> None:
    for relative in [
        "data/human_validation/compact_pilot/annotation_template.csv",
        "data/human_validation/compact_pilot/adjudication_template.csv",
    ]:
        path = REPO / relative
        rows = list(csv.reader(path.open(newline="", encoding="utf-8")))
        assert len(rows) == 1
        assert "sample_id" in rows[0]
