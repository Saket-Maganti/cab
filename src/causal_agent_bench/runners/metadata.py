from __future__ import annotations

import platform
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from causal_agent_bench import __version__
from causal_agent_bench.hashing import stable_hash
from causal_agent_bench.runners.commercial import build_commercial_run_metadata
from causal_agent_bench.runners.config import ExperimentConfig, is_zero_cost_config
from causal_agent_bench.runners.evidence_scope import (
    classify_evidence_scope,
    classify_scientific_scope,
)
from causal_agent_bench.runners.redaction import redact_config_for_persistence, sanitize_metadata
from causal_agent_bench.runners.zero_cost import zero_cost_metadata_fields
from causal_agent_bench.utils.io import git_commit, read_json, write_json


def utc_timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def safe_run_name(run_name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", run_name).strip("_")
    return cleaned or "run"


def prepare_run_directory(config: ExperimentConfig, resume_dir: str | Path | None = None) -> Path:
    if resume_dir is not None:
        run_dir = Path(resume_dir)
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir
    base = config.resolved_output_dir()
    stem = f"{utc_timestamp()}_{safe_run_name(config.run_name)}"
    run_dir = base / stem
    counter = 1
    while run_dir.exists():
        counter += 1
        run_dir = base / f"{stem}_{counter}"
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir


def persist_run_setup(
    run_dir: Path,
    config: ExperimentConfig,
    raw_config: dict[str, Any],
    instances_count: int,
    config_hash: str | None = None,
    *,
    cost_estimate: dict[str, Any] | None = None,
) -> dict[str, Any]:
    digest = config_hash or stable_hash(raw_config)
    safe_config = redact_config_for_persistence(raw_config)
    (run_dir / "config.yaml").write_text(
        yaml.safe_dump(safe_config, sort_keys=False),
        encoding="utf-8",
    )
    (run_dir / "config_hash.txt").write_text(f"{digest}\n", encoding="utf-8")
    metadata = sanitize_metadata(
        build_run_metadata(config, digest, instances_count, cost_estimate=cost_estimate)
    )
    write_json(run_dir / "run_metadata.json", metadata)
    write_json(run_dir / "metadata.json", metadata)
    _write_run_audit_files(run_dir, metadata, config)
    return metadata


def build_run_metadata(
    config: ExperimentConfig,
    config_hash: str,
    instances_count: int,
    *,
    cost_estimate: dict[str, Any] | None = None,
) -> dict[str, Any]:
    dataset = _dataset_metadata(config)
    agent_runs = config.iter_agent_runs()
    providers = sorted(
        {agent_run.provider for agent_run in agent_runs if agent_run.provider}
    )
    agent_names = {agent_run.agent for agent_run in agent_runs}
    evidence_scope = classify_evidence_scope(
        set(providers),
        run_name=config.run_name,
        agent_names=agent_names,
    )
    if is_zero_cost_config(config) and evidence_scope != "mock_diagnostic_only":
        evidence_scope = zero_cost_metadata_fields(config)["evidence_scope"]
    scientific_scope = classify_scientific_scope(set(providers), run_name=config.run_name)
    if is_zero_cost_config(config):
        scientific_scope = "preliminary_or_engineering_only"
    commercial = build_commercial_run_metadata(config, cost_estimate=cost_estimate)
    metadata = {
        "timestamp": datetime.now(UTC).isoformat(),
        "git_commit": git_commit(Path.cwd()),
        "python_version": sys.version.split()[0],
        "package_version": __version__,
        "seed": config.seed,
        "config_hash": config_hash,
        "number_of_instances": instances_count,
        "agents": [agent_run.run_id() for agent_run in agent_runs],
        "agent_runs": [agent_run.model_dump(mode="json") for agent_run in agent_runs],
        "providers": providers,
        "evidence_scope": evidence_scope,
        "scientific_scope": scientific_scope,
        "deployment_class": evidence_scope,
        "model_ids": sorted(
            {agent_run.model for agent_run in agent_runs if agent_run.model}
        ),
        "benchmark_location": config.benchmark_path or config.benchmark_dir,
        "benchmark_instances_path": str(config.resolved_benchmark_path()),
        "dataset_version": dataset.get("dataset_version"),
        "dataset_generation_config_hash": dataset.get("generation_config_hash"),
        "run_name": config.run_name,
        "max_steps": config.max_steps,
        "num_repeats": config.num_repeats,
        "max_instances": config.max_instances,
        "max_api_calls": config.max_api_calls,
        "raac": (
            config.raac.model_dump(mode="json")
            if config.raac is not None
            else None
        ),
        "raac_agent_policies": {
            agent_run.run_id(): resolved.model_dump(mode="json")
            for agent_run in agent_runs
            if (resolved := config.resolved_raac(agent_run)) is not None
        },
        "budget_cap_usd": config.budget_cap_usd,
        "task_budget_cap_usd": config.task_budget_cap_usd,
        "cost_models_configured": bool(config.cost_models),
        "machine": {
            "platform": platform.platform(),
            "processor": platform.processor(),
            "python_implementation": platform.python_implementation(),
        },
        **commercial,
    }
    if is_zero_cost_config(config):
        metadata.update(zero_cost_metadata_fields(config))
    metadata.setdefault("scientific_evidence", False)
    if evidence_scope == "mock_diagnostic_only":
        metadata["not_real_llm_behavior"] = True
        metadata["scientific_evidence"] = False
        metadata["provider_type"] = "mock"
    elif evidence_scope == "pilot_stub_engineering_only":
        metadata["not_real_llm_behavior"] = True
        metadata["scientific_evidence"] = False
        metadata["provider_type"] = "stub"
    elif is_zero_cost_config(config):
        metadata["scientific_evidence"] = False
    return metadata


def _write_run_audit_files(
    run_dir: Path,
    metadata: dict[str, Any],
    config: ExperimentConfig,
) -> None:
    git = metadata.get("git_commit")
    if git:
        (run_dir / "git_commit.txt").write_text(f"{git}\n", encoding="utf-8")
    (run_dir / "python_version.txt").write_text(
        f"{metadata.get('python_version', 'unknown')}\n",
        encoding="utf-8",
    )
    (run_dir / "package_version.txt").write_text(
        f"{metadata.get('package_version', 'unknown')}\n",
        encoding="utf-8",
    )
    benchmark_location = config.benchmark_path or config.benchmark_dir or "unknown"
    lines = [
        f"# Run {run_dir.name}",
        "",
        "This directory was produced by the CausalAgentBench experiment runner.",
        "",
        "## Contents",
        "",
        "- `config.yaml`: exact run configuration.",
        "- `config_hash.txt`: stable hash of the configuration.",
        "- `metadata.json` / `run_metadata.json`: runtime metadata for reproducibility.",
        "- `trajectories.jsonl`: recorded agent trajectories.",
        "- `errors.jsonl`: per-instance execution errors; empty means no runner errors were logged.",
        "- `scores.jsonl`, `aggregate_scores.json`, `aggregate_summary.json`: deterministic heuristic scores when scoring is enabled.",
        "",
        "## Scope",
        "",
        f"- Run name: `{config.run_name}`",
        f"- Benchmark input: `{benchmark_location}`",
        f"- Seed: `{config.seed}`",
        f"- Agents: `{', '.join(agent_run.run_id() for agent_run in config.iter_agent_runs())}`",
        f"- Evidence scope: `{classify_evidence_scope({run.provider for run in config.iter_agent_runs() if run.provider}, run_name=config.run_name)}`",
        "",
        "This run is an engineering or experimental artifact. It is not a scientific result unless the paper and claim ledger explicitly cite it as evidence.",
    ]
    (run_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _dataset_metadata(config: ExperimentConfig) -> dict[str, Any]:
    benchmark_path = config.resolved_benchmark_path()
    candidates = [
        benchmark_path.parent / "generation_report.json",
    ]
    if config.benchmark_dir:
        candidates.append(config.resolved_benchmark_path().parent / "generation_report.json")
    for path in candidates:
        if not path.exists():
            continue
        try:
            report = read_json(path)
        except Exception:
            continue
        return {
            "dataset_version": report.get("benchmark_version"),
            "generation_config_hash": report.get("config_hash"),
        }
    return {"dataset_version": None, "generation_config_hash": None}
