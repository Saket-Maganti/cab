"""Fixture-only tests for god-tier status banner."""

from __future__ import annotations

from pathlib import Path

from causal_agent_bench.safety.god_tier_status import build_god_tier_status


def test_god_tier_status_honest_evidence(tmp_path: Path) -> None:
    (tmp_path / "configs").mkdir()
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/claim_ledger.json").write_text(
        '{"claims":[{"claim_id":"C9","status":"engineering_only"}]}',
        encoding="utf-8",
    )
    (tmp_path / "configs/provider_pilot_tiny_template.yaml").write_text(
        "\n".join(
            [
                "run_name: provider_pilot_tiny_PENDING_APPROVAL",
                "template_only: true",
                "benchmark_path: data/x.jsonl",
                "allow_paid_calls: false",
                "scientific_evidence: false",
                "evidence_scope: provider_pilot_pending_verification",
                "budget_cap_usd: 5",
                "max_instances: 5",
                "limits:",
                "  stop_after_trajectories: 5",
                "  max_runtime_minutes: 30",
                "require_dry_run_before_live: true",
                "agent_runs:",
                "  - agent: direct_tool_agent",
                "    provider: openai",
                "    model: ${OPENAI_MODEL_ID}",
                "approval:",
                "  advisor_approved: false",
                "  budget_approved: false",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "docs/POST_PROVIDER_PILOT_CHECKLIST.md").write_text("x", encoding="utf-8")
    report = build_god_tier_status(tmp_path, output_dir=tmp_path / "out")
    assert report["evidence"]["paper_eligible_runs"] == 0
    assert report["verdicts"]["god_tier_empirical_paper"] is False
    assert report["verdicts"]["evidence_honesty_preserved"] is True
    md = Path(report["report_paths"]["markdown"]).read_text(encoding="utf-8")
    assert "God-Tier Status" in md


def test_real_repo_god_tier_script_fields() -> None:
    report = build_god_tier_status(Path("."), output_dir="/tmp/cab_god_tier_test_out")
    assert "safe_next_commands" in report
    assert report["provider_gate"]["approved_config_present"] is True
    assert report["provider_gate"]["gate_status"] == "ready_for_dry_run"
    assert report["provider_gate"]["verdicts"]["ready_for_live_provider_run"] is False
