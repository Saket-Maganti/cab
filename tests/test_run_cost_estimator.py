from __future__ import annotations

import json
from pathlib import Path

import yaml

from causal_agent_bench.safety.run_cost_estimator import estimate_run_cost


def _write_benchmark(path: Path, n: int = 3) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps({"instance_id": f"i{i}"}) for i in range(n)) + "\n", encoding="utf-8")


def _write_config(tmp_path: Path, extra: dict | None = None) -> Path:
    benchmark = tmp_path / "instances.jsonl"
    _write_benchmark(benchmark)
    config = {
        "run_name": "provider_pilot_tiny_PENDING_APPROVAL",
        "benchmark_path": str(benchmark),
        "allow_paid_calls": False,
        "budget_cap_usd": 5.0,
        "max_instances": 2,
        "limits": {
            "max_trajectories": 2,
            "stop_after_trajectories": 2,
            "max_steps_per_instance": 4,
            "max_output_tokens": 256,
        },
        "agent_runs": [
            {
                "name": "pilot",
                "agent": "direct_tool_agent",
                "provider": "openai",
                "model": "PLACEHOLDER_SET_BEFORE_RUN",
                "max_tokens": 256,
            }
        ],
    }
    if extra:
        config.update(extra)
    path = tmp_path / "provider_pilot_tiny_template.yaml"
    path.write_text(yaml.safe_dump(config), encoding="utf-8")
    return path


def test_template_config_is_not_runnable_and_paid_calls_false(tmp_path: Path) -> None:
    path = _write_config(tmp_path)
    report = estimate_run_cost(path, repo_root=tmp_path)
    assert report["allow_paid_calls"] is False
    assert report["runnable_without_approval"] is False
    assert report["template_or_pending_approval"] is True


def test_missing_pricing_gives_unknown_cost_warning(tmp_path: Path) -> None:
    path = _write_config(tmp_path)
    report = estimate_run_cost(path, repo_root=tmp_path)
    assert report["pricing_known"] is False
    assert report["estimated_high_cost_usd"] is None
    assert any("Pricing unknown" in warning for warning in report["warnings"])


def test_budget_cap_and_trajectory_cap_detected(tmp_path: Path) -> None:
    path = _write_config(tmp_path)
    report = estimate_run_cost(path, repo_root=tmp_path)
    assert report["budget_cap_exists"] is True
    assert report["budget_cap_usd"] == 5.0
    assert report["max_trajectories"] == 2
    assert report["number_of_trajectories"] == 2


def test_local_mock_or_oracle_provider_rejected_as_provider_evidence(tmp_path: Path) -> None:
    path = _write_config(
        tmp_path,
        {
            "run_name": "local_stub_plan",
            "agent_runs": [
                {
                    "name": "oracle",
                    "agent": "scripted_oracle_agent",
                    "provider": "local_stub",
                    "model": "none",
                }
            ],
        },
    )
    report = estimate_run_cost(path, repo_root=tmp_path)
    assert report["agent_runs"][0]["provider_evidence_candidate"] is False
    assert any("not provider evidence" in warning for warning in report["warnings"])
