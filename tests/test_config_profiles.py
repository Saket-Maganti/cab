from __future__ import annotations

from pathlib import Path

from causal_agent_bench.safety.config_profiles import classify_config_profile


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_mock_config_classified_mock_diagnostic(tmp_path: Path) -> None:
    path = _write(
        tmp_path / "configs/pilot_mock_diagnostic.yaml",
        "run_name: pilot_mock_diagnostic\nprovider: mock\nscientific_evidence: false\n",
    )
    row = classify_config_profile(path, repo_root=tmp_path)
    assert row["profile"] == "mock_diagnostic"
    assert row["paper_eligible_by_default"] is False


def test_provider_template_classified_template(tmp_path: Path) -> None:
    path = _write(
        tmp_path / "configs/provider_pilot_tiny_template.yaml",
        "run_name: provider_pilot_tiny_template\nprovider: openai\nallow_paid_calls: false\n",
    )
    row = classify_config_profile(path, repo_root=tmp_path)
    assert row["profile"] == "provider_pilot_template"


def test_approved_provider_fixture_classified_approved_only_with_markers(tmp_path: Path) -> None:
    no_marker = _write(
        tmp_path / "configs/provider_pilot_approved.yaml",
        "run_name: provider_pilot_approved\nprovider: openai\nallow_paid_calls: false\n",
    )
    assert classify_config_profile(no_marker, repo_root=tmp_path)["profile"] != "provider_pilot_approved"
    marked = _write(
        tmp_path / "configs/provider_pilot_approved_marked.yaml",
        "\n".join(
            [
                "run_name: provider_pilot_approved",
                "provider: openai",
                "allow_paid_calls: false",
                "approval:",
                "  advisor_approval_id: test-approval",
                "  approved_for_dry_run: true",
            ]
        ),
    )
    assert classify_config_profile(marked, repo_root=tmp_path)["profile"] == "provider_pilot_approved"


def test_local_provider_not_provider_approved(tmp_path: Path) -> None:
    path = _write(
        tmp_path / "configs/provider_pilot_approved_local.yaml",
        "\n".join(
            [
                "run_name: provider_pilot_approved_local",
                "provider: local",
                "allow_paid_calls: false",
                "approval:",
                "  advisor_approval_id: test-approval",
                "  approved_for_dry_run: true",
            ]
        ),
    )
    row = classify_config_profile(path, repo_root=tmp_path)
    assert row["profile"] != "provider_pilot_approved"


def test_unknown_config_needs_review(tmp_path: Path) -> None:
    path = _write(tmp_path / "configs/mystery.yaml", "run_name: mystery\n")
    row = classify_config_profile(path, repo_root=tmp_path)
    assert row["profile"] == "unknown_needs_review"
    assert row["safety_issues"]
