from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]


def _read(relative: str) -> str:
    return (REPO / relative).read_text(encoding="utf-8")


def _yaml(relative: str) -> dict:
    return yaml.safe_load(_read(relative))


def test_3model_config_template_is_non_runnable() -> None:
    template = _yaml("configs/compact20_3model_TEMPLATE_NOT_APPROVED.yaml")
    assert template["template_only"] is True
    assert template["not_runnable_without_approval"] is True
    assert template["allow_paid_calls"] is False
    assert template["approved_for_live_run"] is False
    assert template["approved_for_dry_run"] is False
    assert template["evidence_scope"] == "planned_paper_eligible_pilot"
    assert template["scientific_claims_allowed"] is False
    assert template["paper_asset_eligibility"] is False
    assert template["planned_design"]["exact_planned_trajectories"] == 120
    assert "agent_runs" not in template
    assert "benchmark_instances_path" not in template


def test_local_template_is_non_runnable_and_not_paper_eligible() -> None:
    template = _yaml("configs/compact20_3model_LOCAL_TEMPLATE_NOT_APPROVED.yaml")
    assert template["template_only"] is True
    assert template["not_runnable_without_approval"] is True
    assert template["allow_paid_calls"] is False
    assert template["approved_for_live_run"] is False
    assert template["evidence_scope"] == "planned_local_sanity_only_not_paper_eligible"
    assert template["local_model_policy"]["cannot_substitute_for_provider_backed_pilot"] is True
    assert template["paper_asset_eligibility"] is False


def test_no_secret_fields_or_key_shaped_values_in_templates() -> None:
    forbidden_field = re.compile(r"(?im)^\s*(api_key|apikey|token|secret|bearer)\s*:")
    key_shaped_value = re.compile(r"(?i)(sk-[A-Za-z0-9]{16,}|AIza[0-9A-Za-z_-]{16,})")
    for relative in [
        "configs/compact20_3model_TEMPLATE_NOT_APPROVED.yaml",
        "configs/compact20_3model_LOCAL_TEMPLATE_NOT_APPROVED.yaml",
    ]:
        text = _read(relative)
        assert not forbidden_field.search(text), relative
        assert not key_shaped_value.search(text), relative


def test_first_pilot_plan_does_not_claim_results() -> None:
    plan = _read("experiments/FIRST_PAPER_ELIGIBLE_3MODEL_COMPACT20_PLAN.md")
    lowered = plan.lower()
    assert "provider-backed evidence: `0`" in lowered
    assert "human annotations: `0`" in lowered
    assert "eligible paper assets: `0`" in lowered
    assert "this plan promotes no claims" in lowered
    for forbidden in ["we demonstrate", "we find", "c1 is supported", "c10 is supported"]:
        assert forbidden not in lowered


def test_local_preliminary_traces_cannot_support_paper_claims() -> None:
    memo = _read("docs/LOCAL_MODEL_EVIDENCE_BOUNDARY.md")
    lowered = memo.lower()
    assert "qwen2.5:7b" in memo
    assert "zero_cost_local_preliminary" in memo
    assert "not paper-eligible evidence" in lowered
    assert "c1-c8 and c10 remain planned/unsupported" in lowered


def test_paper_result_schemas_are_placeholders_not_fake_numbers() -> None:
    schema = _read("paper/FIRST_3MODEL_PILOT_RESULT_TABLE_SCHEMAS.md")
    assert "SCHEMA_ONLY_NO_RESULTS" in schema
    assert "TODO_REAL_RESULT" in schema
    assert "Do not enter illustrative numeric values" in schema
    for fake_value in ["0.75", "75%", "0.50", "1.00"]:
        assert fake_value not in schema


def test_first_money_plot_requires_real_results_before_plotting() -> None:
    spec = _read("paper/FIRST_MONEY_PLOT_SPEC.md")
    lowered = spec.lower()
    assert "requires real audited 3-model compact-20 results" in lowered
    assert "do not create this plot for the paper until real results" in lowered
    assert "if rankings do not change" in lowered


def test_c1_c8_c10_remain_unsupported_before_execution() -> None:
    triage = _read("docs/CLAIM_TRIAGE_NO_RUN.md")
    plan = _read("experiments/FIRST_PAPER_ELIGIBLE_3MODEL_COMPACT20_PLAN.md")
    assert "C1-C8 and C10 must remain planned/unsupported" in triage
    assert "C1-C8/C10: planned/unsupported" in plan
    assert "No-Execution Boundary" in plan
