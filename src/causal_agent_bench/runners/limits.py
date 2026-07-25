from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from causal_agent_bench.runners.config import ExperimentConfig
from causal_agent_bench.runners.resume import write_checkpoint


@dataclass
class RunLimiter:
    max_instances: int | None = None
    max_agents: int | None = None
    max_trajectories: int | None = None
    max_runtime_minutes: float | None = None
    stop_after_trajectories: int | None = None
    max_steps_per_instance: int | None = None
    max_output_tokens: int | None = None
    started_at: float = field(default_factory=time.monotonic)
    trajectories_this_run: int = 0

    @classmethod
    def from_config(
        cls,
        config: ExperimentConfig,
        *,
        cli_overrides: dict[str, Any] | None = None,
    ) -> RunLimiter:
        limits = config.limits
        overrides = cli_overrides or {}
        return cls(
            max_instances=_pick(overrides.get("max_instances"), limits.max_instances if limits else None, config.max_instances),
            max_agents=_pick(overrides.get("max_agents"), limits.max_agents if limits else None),
            max_trajectories=_pick(overrides.get("max_trajectories"), limits.max_trajectories if limits else None),
            max_runtime_minutes=_pick(
                overrides.get("max_runtime_minutes"),
                limits.max_runtime_minutes if limits else None,
            ),
            stop_after_trajectories=_pick(
                overrides.get("stop_after_trajectories"),
                limits.stop_after_trajectories if limits else None,
            ),
            max_steps_per_instance=_pick(
                overrides.get("max_steps_per_instance"),
                limits.max_steps_per_instance if limits else None,
            ),
            max_output_tokens=_pick(
                overrides.get("max_output_tokens"),
                limits.max_output_tokens if limits else None,
            ),
        )

    def effective_max_steps(self, config_max_steps: int) -> int:
        if self.max_steps_per_instance is None:
            return config_max_steps
        return min(config_max_steps, self.max_steps_per_instance)

    def effective_max_tokens(self, agent_max_tokens: int) -> int:
        if self.max_output_tokens is None:
            return agent_max_tokens
        return min(agent_max_tokens, self.max_output_tokens)

    def should_stop_before_trajectory(self, completed_count: int) -> str | None:
        if self.max_trajectories is not None and completed_count >= self.max_trajectories:
            return f"max_trajectories={self.max_trajectories}"
        if self.stop_after_trajectories is not None and self.trajectories_this_run >= self.stop_after_trajectories:
            return f"stop_after_trajectories={self.stop_after_trajectories}"
        if self.max_runtime_minutes is not None:
            elapsed_min = (time.monotonic() - self.started_at) / 60.0
            if elapsed_min >= self.max_runtime_minutes:
                return f"max_runtime_minutes={self.max_runtime_minutes}"
        return None

    def note_trajectory_completed(self) -> None:
        self.trajectories_this_run += 1

    def write_stop_checkpoint(
        self,
        run_dir: Path,
        *,
        completed: int,
        total: int,
        errors: int,
        reason: str,
    ) -> None:
        write_checkpoint(
            run_dir,
            completed=completed,
            total=total,
            errors=errors,
            extra={
                "status": "incomplete",
                "interruption_reason": "limiter_stop",
                "limiter_stop_reason": reason,
                "limiter_stopped_at": datetime.now(UTC).isoformat(),
                "scientific_evidence": False,
            },
        )


def _pick(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def estimate_runtime_category(
    *,
    expected_trajectories: int,
    max_steps: int,
    provider_types: set[str],
    seconds_per_trajectory: float | None = None,
) -> tuple[str, float]:
    if "local_openai" in provider_types or "openai_compatible" in provider_types:
        per_traj = seconds_per_trajectory or 120.0
    elif provider_types <= {"local_stub"}:
        per_traj = seconds_per_trajectory or 2.0
    else:
        per_traj = seconds_per_trajectory or 30.0
    total_seconds = expected_trajectories * per_traj * max(1, max_steps // 4)
    if total_seconds < 120:
        category = "micro_debug"
    elif total_seconds < 900:
        category = "fast_local"
    elif total_seconds < 3600:
        category = "medium"
    else:
        category = "long_hours"
    return category, total_seconds


def warn_if_huge_local_run(config: ExperimentConfig, expected_trajectories: int) -> list[str]:
    warnings: list[str] = []
    providers = {run.provider or "local_stub" for run in config.iter_agent_runs()}
    category, seconds = estimate_runtime_category(
        expected_trajectories=expected_trajectories,
        max_steps=config.max_steps,
        provider_types=providers,
    )
    if category == "long_hours":
        warnings.append(
            f"Estimated runtime category={category} (~{seconds / 3600:.1f}h). "
            "Use a micro config or limits block before running locally."
        )
    if "local_openai" in providers and expected_trajectories > 30:
        warnings.append(
            f"Local/Ollama run with {expected_trajectories} trajectories may take hours."
        )
    if config.allow_paid_calls:
        warnings.append("Config allows paid calls.")
    for run in config.iter_agent_runs():
        if run.agent in {"scripted_oracle_agent"}:
            warnings.append(f"Oracle agent present: {run.run_id()}")
    return warnings
