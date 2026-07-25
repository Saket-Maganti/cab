from __future__ import annotations

from pathlib import Path

from causal_agent_bench.safety.synthetic_fixtures import (
    analyze_trajectory_signals,
    load_synthetic_fixtures,
    validate_synthetic_fixture,
)

FIXTURES = Path(__file__).parent / "fixtures" / "synthetic_trajectories"


def test_synthetic_fixtures_are_non_evidence_and_schema_compatible() -> None:
    fixtures = load_synthetic_fixtures(FIXTURES)
    assert set(fixtures) == {
        "tool_overuse",
        "premature_stopper",
        "contradiction_blind",
        "memory_blind",
        "argument_sloppy",
        "recovery_weak",
        "final_answer_hallucinator",
        "retry_loop_agent",
    }
    for name, fixture in fixtures.items():
        metadata = fixture["metadata"]
        assert metadata["synthetic_fixture"] is True
        assert metadata["not_real_llm_behavior"] is True
        assert metadata["scientific_evidence"] is False
        assert metadata["paper_eligible"] is False
        assert metadata["expected_failure_category"]
        result = validate_synthetic_fixture(name, fixture)
        assert result["passed"], result


def test_expected_metric_signals_are_detected() -> None:
    fixtures = load_synthetic_fixtures(FIXTURES)
    expected_flags = {
        "tool_overuse": "excessive_tool_calls",
        "premature_stopper": "too_few_steps",
        "retry_loop_agent": "repeated_calls",
        "final_answer_hallucinator": "unsupported_final_answer",
        "contradiction_blind": "ignored_contradiction",
        "memory_blind": "ignored_memory_verification",
        "recovery_weak": "failed_recovery_after_tool_error",
        "argument_sloppy": "malformed_tool_args",
    }
    for name, flag in expected_flags.items():
        signals = analyze_trajectory_signals(fixtures[name])
        assert signals["flags"][flag] is True
