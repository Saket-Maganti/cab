"""Static checks for provider pilot readiness artifacts (no runs, no APIs)."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from causal_agent_bench.runners.config import ExperimentConfig
from causal_agent_bench.safety.provider_pilot_config import (
    load_experiment_config,
    template_metadata_defaults,
    validate_oracle_sanity_config,
    validate_provider_pilot_evidence_config,
)

REPO = Path(__file__).resolve().parents[1]
TEMPLATE = REPO / "configs" / "provider_pilot_tiny_template.yaml"
ORACLE_TEMPLATE = REPO / "configs" / "provider_pilot_oracle_sanity_check_template.yaml"
PACKET = REPO / "docs" / "PROVIDER_PILOT_READINESS_PACKET.md"
METADATA_DOC = REPO / "docs" / "PROVIDER_PILOT_METADATA_REQUIREMENTS.md"
POST_CHECKLIST = REPO / "docs" / "POST_PROVIDER_PILOT_CHECKLIST.md"
NO_RUN_DOC = REPO / "docs" / "NO_RUN_VALIDATION.md"


def test_provider_pilot_docs_exist() -> None:
    for path in (PACKET, METADATA_DOC, POST_CHECKLIST):
        assert path.exists(), f"missing doc: {path}"
    text = PACKET.read_text(encoding="utf-8")
    assert "Advisor approval checklist" in text
    assert "DO NOT RUN" in text or "do not run" in text.lower()
    assert "Provider pilot vs oracle sanity check" in text


def test_no_run_validation_mentions_provider_pilot() -> None:
    text = NO_RUN_DOC.read_text(encoding="utf-8")
    assert "Before provider pilot" in text
    assert "PROVIDER_PILOT_READINESS_PACKET" in text


def test_no_run_validation_approves_only_explicit_strict_lane() -> None:
    text = NO_RUN_DOC.read_text(encoding="utf-8")
    safe_section = text.split("## Marker lane warning", 1)[0]
    explicit = (
        "python3 -m pytest tests/test_safety_reports.py tests/test_cli.py "
        "tests/test_claim_ledger.py tests/test_provider_pilot_readiness.py -q"
    )
    assert explicit in safe_section
    assert "python3 scripts/check_evidence_safety.py" in safe_section
    assert "not currently sufficient" in text
    assert "only the explicit named-file pytest command" in text
    assert 'python3 -m pytest tests/ -m "not integration and not local_run" -q' not in safe_section
    assert 'python3 -m pytest --collect-only -m "not integration and not local_run"' not in safe_section


def test_provider_pilot_tiny_template_has_no_oracle_mock_stub() -> None:
    assert TEMPLATE.exists()
    text = TEMPLATE.read_text(encoding="utf-8")
    assert "TEMPLATE ONLY" in text
    assert "DO NOT RUN WITHOUT APPROVAL" in text
    assert "not paper-eligible" in text.lower() or "NOT paper-eligible" in text
    assert "no claims may be promoted" in text.lower() or "No claims may be promoted" in text
    assert "scripted_oracle" not in text
    assert "mock_behavior" not in text

    config = load_experiment_config(TEMPLATE)
    issues = validate_provider_pilot_evidence_config(config)
    assert issues == [], issues
    assert all("oracle" not in run.agent.lower() for run in config.iter_agent_runs())
    assert config.allow_paid_calls is False


def test_provider_pilot_template_metadata_defaults_scientific_false() -> None:
    meta = template_metadata_defaults(TEMPLATE)
    assert meta["scientific_evidence"] is False
    assert meta["allow_paid_calls"] is False
    assert meta["evidence_scope"] == "provider_pilot_pending_verification"


def test_oracle_sanity_template_is_engineering_only() -> None:
    assert ORACLE_TEMPLATE.exists()
    text = ORACLE_TEMPLATE.read_text(encoding="utf-8")
    assert "ORACLE SANITY" in text
    assert "engineering_only" in text.lower() or "ENGINEERING ONLY" in text
    assert "oracle_sanity_only" in text
    assert "MUST NOT" in text and "promote-to-supported" in text

    config = load_experiment_config(ORACLE_TEMPLATE)
    issues = validate_oracle_sanity_config(config)
    assert issues == [], issues
    meta = template_metadata_defaults(ORACLE_TEMPLATE)
    assert meta["scientific_evidence"] is False
    assert meta["evidence_scope"] == "oracle_sanity_only"
    assert config.allow_paid_calls is False


def test_provider_pilot_with_oracle_agent_fails_static_validation() -> None:
    raw = yaml.safe_load(TEMPLATE.read_text(encoding="utf-8"))
    raw["agent_runs"] = [*list(raw["agent_runs"]), {"name": "bad_oracle", "agent": "scripted_oracle_agent"}]
    config = ExperimentConfig.model_validate(raw)
    issues = validate_provider_pilot_evidence_config(config)
    assert any("oracle" in issue.lower() for issue in issues)


def test_provider_pilot_with_stub_provider_fails_static_validation() -> None:
    raw = yaml.safe_load(TEMPLATE.read_text(encoding="utf-8"))
    raw["agent_runs"][0]["provider"] = "local_stub"
    config = ExperimentConfig.model_validate(raw)
    issues = validate_provider_pilot_evidence_config(config)
    assert any("stub" in issue or "local_stub" in issue for issue in issues)


def _provider_validation_issues(raw: dict) -> list[str]:
    try:
        config = ExperimentConfig.model_validate(raw)
    except Exception as exc:
        return [str(exc)]
    return validate_provider_pilot_evidence_config(config)


@pytest.mark.parametrize(
    "provider_value",
    [
        None,
        "",
        "local",
        "local_stub",
        "default",
        "placeholder",
        "provider",
        "mock",
        "stub",
        "oracle",
        "scripted_oracle",
        "synthetic",
        "deterministic",
        "fake",
        "test",
        "debug",
        "none",
        "offline",
    ],
)
def test_provider_pilot_rejects_non_provider_backed_provider_values(provider_value: str | None) -> None:
    raw = yaml.safe_load(TEMPLATE.read_text(encoding="utf-8"))
    raw["agent_runs"][0]["provider"] = provider_value
    issues = _provider_validation_issues(raw)
    assert issues


def test_provider_pilot_rejects_missing_provider() -> None:
    raw = yaml.safe_load(TEMPLATE.read_text(encoding="utf-8"))
    raw["agent_runs"][0].pop("provider")
    issues = _provider_validation_issues(raw)
    assert any("missing provider" in issue.lower() for issue in issues)


@pytest.mark.parametrize("provider", ["openai", "anthropic", "gemini", "openrouter"])
def test_provider_pilot_accepts_real_provider_families(provider: str) -> None:
    raw = yaml.safe_load(TEMPLATE.read_text(encoding="utf-8"))
    raw["agent_runs"][0]["provider"] = provider
    raw["agent_runs"][0]["model"] = f"${{{provider.upper()}_MODEL_ID}}"
    config = ExperimentConfig.model_validate(raw)
    assert validate_provider_pilot_evidence_config(config) == []


def test_provider_pilot_rejects_missing_or_generic_model() -> None:
    for model in (None, "", "default", "placeholder-model", "${MODEL_ID}"):
        raw = yaml.safe_load(TEMPLATE.read_text(encoding="utf-8"))
        raw["agent_runs"][0]["model"] = model
        config = ExperimentConfig.model_validate(raw)
        issues = validate_provider_pilot_evidence_config(config)
        assert any("model" in issue.lower() for issue in issues)


def test_oracle_sanity_template_fails_provider_pilot_validation() -> None:
    config = load_experiment_config(ORACLE_TEMPLATE)
    assert validate_oracle_sanity_config(config) == []
    issues = validate_provider_pilot_evidence_config(config)
    assert issues
    assert any("oracle" in issue.lower() or "missing provider" in issue.lower() for issue in issues)


def test_template_scientific_evidence_level_not_main_supported() -> None:
    config = load_experiment_config(TEMPLATE)
    assert config.scientific_evidence_level != "main_supported"


@pytest.mark.parametrize(
    "doc_path,phrase",
    [
        (POST_CHECKLIST, "run-health"),
        (POST_CHECKLIST, "claim-evidence"),
        (POST_CHECKLIST, "check_evidence_safety"),
        (POST_CHECKLIST, "Pre-promotion"),
        (POST_CHECKLIST, "provider_backed_pilot"),
        (METADATA_DOC, "scientific_evidence"),
        (METADATA_DOC, "provider_backed_pilot"),
        (METADATA_DOC, "oracle_sanity_only"),
    ],
)
def test_provider_pilot_docs_include_required_commands(doc_path: Path, phrase: str) -> None:
    assert phrase in doc_path.read_text(encoding="utf-8")
