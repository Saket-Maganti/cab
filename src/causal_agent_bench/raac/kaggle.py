"""Fail-closed RAAC config materialization for the governed Kaggle notebook."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from causal_agent_bench.raac.contracts import EQUAL_BUDGET_CONTRACT, ComputeContract
from causal_agent_bench.raac.types import ComparisonMode, PolicyVariant

REQUIRED_KAGGLE_ARMS = frozenset(
    {
        PolicyVariant.STANDARD_TOOL_USE,
        PolicyVariant.RAAC_LIGHT,
        PolicyVariant.RAAC_FULL,
        PolicyVariant.VERIFY_ONLY,
        PolicyVariant.RETRY_ONLY,
        PolicyVariant.ABSTAIN_ONLY,
        PolicyVariant.NO_CROSS_CHECK,
        PolicyVariant.NO_ALTERNATE_ROUTE,
        PolicyVariant.NO_FINAL_VERIFY,
    }
)


def materialize_raac_kaggle_config(
    source: str | Path,
    destination: str | Path,
    *,
    comparison_mode: ComparisonMode | str,
) -> Path:
    """Validate and write one selected budget-mode config without executing it."""

    source_path = Path(source)
    output_path = Path(destination)
    raw = yaml.safe_load(source_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("RAAC Kaggle source config must be a mapping")
    agent_runs = raw.get("agent_runs")
    if not isinstance(agent_runs, list) or not agent_runs:
        raise ValueError("RAAC Kaggle source config must declare agent_runs")
    mode = ComparisonMode(comparison_mode)
    observed: set[PolicyVariant] = set()
    for row in agent_runs:
        if not isinstance(row, dict) or not isinstance(row.get("raac"), dict):
            raise ValueError("every RAAC Kaggle agent run must declare a raac block")
        raac = row["raac"]
        variant = PolicyVariant(raac.get("variant"))
        observed.add(variant)
        raac["comparison_mode"] = mode.value
        raac["equal_budget_contract"] = (
            EQUAL_BUDGET_CONTRACT.model_dump(mode="json")
            if mode == ComparisonMode.EQUAL_BUDGET
            else None
        )
    missing = sorted(variant.value for variant in REQUIRED_KAGGLE_ARMS - observed)
    extras = sorted(variant.value for variant in observed - REQUIRED_KAGGLE_ARMS)
    if missing or extras:
        raise ValueError(f"RAAC Kaggle arm mismatch; missing={missing}, extras={extras}")
    raw["run_name"] = f"{raw.get('run_name', 'raac_kaggle')}_{mode.value}"

    # Local import avoids coupling the core policy package to the runner at
    # import time while still validating the exact generated runner schema.
    from causal_agent_bench.runners.config import ExperimentConfig

    ExperimentConfig.model_validate(raw)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(yaml.safe_dump(raw, sort_keys=False), encoding="utf-8")
    return output_path


def load_raac_kaggle_matrix(path: str | Path) -> dict[str, Any]:
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("RAAC Kaggle matrix must be a mapping")
    primary = {PolicyVariant(value) for value in payload.get("primary_arms", [])}
    ablations = {PolicyVariant(value) for value in payload.get("ablation_arms", [])}
    if primary | ablations != REQUIRED_KAGGLE_ARMS:
        raise ValueError("RAAC Kaggle matrix does not match the required frozen arms")
    if set(payload.get("budget_modes", [])) != {mode.value for mode in ComparisonMode}:
        raise ValueError("RAAC Kaggle matrix must declare both budget modes")
    required_fields = set(payload.get("required_compute_fields", []))
    if required_fields != set(ComputeContract.model_fields):
        raise ValueError("RAAC Kaggle matrix compute fields do not match the canonical contract")
    return payload
