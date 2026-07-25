from __future__ import annotations

from pathlib import Path

import yaml

from causal_agent_bench.safety.config_metadata_lint import lint_config_file


def _write(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    return path


def _ids(issues: list[dict]) -> set[str]:
    return {issue["id"] for issue in issues}


def test_unsafe_provider_config_flagged(tmp_path: Path) -> None:
    path = _write(tmp_path / "configs/provider.yaml", {"agent_runs": [{"agent": "direct_tool_agent", "provider": "openai", "model": "m"}]})
    issues = lint_config_file(path, repo_root=tmp_path)
    assert {"allow_paid_calls_missing", "budget_cap_missing", "trajectory_cap_missing"}.issubset(_ids(issues))


def test_mock_config_without_scientific_evidence_false_flagged(tmp_path: Path) -> None:
    path = _write(tmp_path / "configs/mock.yaml", {"agent_runs": [{"agent": "mock_behavior_agent", "provider": "local_stub"}]})
    issues = lint_config_file(path, repo_root=tmp_path)
    assert "mock_scientific_evidence_not_false" in _ids(issues)


def test_template_not_runnable_passes_template_gate(tmp_path: Path) -> None:
    path = _write(
        tmp_path / "configs/provider_pilot_template.yaml",
        {"allow_paid_calls": False, "budget_cap_usd": 1.0, "max_instances": 1, "agent_runs": [{"agent": "direct_tool_agent", "provider": "openai", "model": "m"}]},
    )
    issues = lint_config_file(path, repo_root=tmp_path)
    assert "template_runnable_by_default" not in _ids(issues)


def test_provider_looking_local_config_flagged(tmp_path: Path) -> None:
    path = _write(
        tmp_path / "configs/provider_openai_local.yaml",
        {"allow_paid_calls": False, "agent_runs": [{"agent": "direct_tool_agent", "provider": "local_stub", "model": "none"}]},
    )
    issues = lint_config_file(path, repo_root=tmp_path)
    assert "provider_name_local_provider" in _ids(issues)
