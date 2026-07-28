from __future__ import annotations

import json
import os
import shutil
from collections import Counter
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from causal_agent_bench import __version__
from causal_agent_bench.agents.llm_clients import list_provider_status

# Re-exported for backwards-compatible ``causal_agent_bench.phase2`` import paths
# used by the CLI; the implementations live in ``claim_ledger``.
from causal_agent_bench.claim_ledger import (
    update_claim_ledger as update_claim_ledger,
)
from causal_agent_bench.claim_ledger import (
    update_claim_ledger_from_run as update_claim_ledger_from_run,
)
from causal_agent_bench.contamination.audit import (
    apply_canary_metadata,
    contamination_report_markdown,
    run_contamination_audit,
)
from causal_agent_bench.generation.instances import BenchmarkGenerationConfig
from causal_agent_bench.generation.quality_checks import (
    quality_report_markdown,
    run_quality_checks,
)
from causal_agent_bench.hashing import stable_hash
from causal_agent_bench.runners.commercial import check_paid_run_gates, uses_paid_providers
from causal_agent_bench.runners.config import (
    ORACLE_AGENT_NAMES,
    PAID_PROVIDERS,
    PROVIDER_MODEL_ENV_VARS,
    AgentRunConfig,
    AnalysisConfig,
    CostEstimationConfig,
    DatasetValidationConfig,
    ExperimentConfig,
    LegacyTaskGenerationConfig,
    ScoringConfig,
    is_experiment_config,
    load_experiment_config,
)
from causal_agent_bench.runners.costing import estimate_config_cost, estimate_experiment_cost
from causal_agent_bench.runners.execution import execute_agent_on_instance
from causal_agent_bench.runners.redaction import redact_config_for_persistence, sanitize_metadata
from causal_agent_bench.schemas import BaseTask, BenchmarkInstance, InterventionSpec
from causal_agent_bench.tools.registry import ToolRegistry
from causal_agent_bench.utils.io import (
    git_commit,
    load_yaml,
    read_json,
    read_jsonl,
    write_json,
    write_jsonl,
)
from causal_agent_bench.validation import validate_jsonl_file


def validate_config_file(config_path: str | Path) -> dict[str, Any]:
    """Validate a YAML config and return a concise audit summary."""

    path = Path(config_path)
    raw = load_yaml(path)
    digest = stable_hash(raw)
    if "matrix_version" in raw and "base_model" in raw:
        from causal_agent_bench.ablation_matrix import (
            expand_matrix_cells,
            load_ablation_matrix_config,
        )

        config = load_ablation_matrix_config(path)
        benchmark_path = Path(config.benchmark_path)
        benchmark_path = benchmark_path if benchmark_path.is_absolute() else Path.cwd() / benchmark_path
        return {
            "valid": True,
            "config_type": "ablation_matrix",
            "path": str(path),
            "config_hash": digest,
            "run_name": config.run_name,
            "benchmark_path": str(benchmark_path),
            "benchmark_exists": benchmark_path.exists(),
            "cells": len(expand_matrix_cells(config)),
            "provider": config.base_model.provider,
            "model": config.base_model.model,
            "ready_to_run": benchmark_path.exists(),
        }
    if is_experiment_config(raw):
        config, expanded = load_experiment_config(path)
        benchmark_path = config.resolved_benchmark_path()
        instances_count = _count_jsonl_rows(benchmark_path) if benchmark_path.exists() else None
        readiness = _experiment_readiness(config, benchmark_path, raw)
        return {
            "valid": True,
            "config_type": "experiment",
            "path": str(path),
            "config_hash": stable_hash(expanded),
            "run_name": config.run_name,
            "benchmark_path": str(benchmark_path),
            "benchmark_exists": benchmark_path.exists(),
            "instances": instances_count,
            "agents": [agent_run.run_id() for agent_run in config.iter_agent_runs()],
            "provider_checks": readiness["provider_checks"],
            "issues": readiness["issues"],
            "ready_to_run": readiness["ready_to_run"],
            "auto_score": config.auto_score,
        }
    if "num_base_tasks" in raw:
        config = BenchmarkGenerationConfig.model_validate(raw)
        return {
            "valid": True,
            "config_type": "generation",
            "path": str(path),
            "config_hash": digest,
            "benchmark_version": config.benchmark_version,
            "num_base_tasks": config.num_base_tasks,
            "domains": config.domains,
            "interventions_per_task": config.interventions_per_task,
            "output_dir": config.output_dir,
        }
    if {"base_tasks_path", "interventions_path", "instances_path"}.issubset(raw):
        config = DatasetValidationConfig.model_validate(raw)
        file_checks = {
            "base_tasks_path": Path(config.base_tasks_path).exists(),
            "interventions_path": Path(config.interventions_path).exists(),
            "instances_path": Path(config.instances_path).exists(),
            "splits_path": Path(config.splits_path).exists() if config.splits_path else None,
        }
        return {
            "valid": True,
            "config_type": "dataset_validation",
            "path": str(path),
            "config_hash": digest,
            "benchmark_version": config.benchmark_version,
            "file_checks": file_checks,
            "ready_to_validate": all(value is not False for value in file_checks.values()),
            "expected": config.expected,
        }
    if {"run_dir"}.issubset(raw) and "export_paper_assets" in raw:
        config = AnalysisConfig.model_validate(raw)
        return {
            "valid": True,
            "config_type": "analysis",
            "path": str(path),
            "config_hash": digest,
            "run_dir": config.run_dir,
            "run_dir_exists": Path(config.run_dir).exists(),
            "export_paper_assets": config.export_paper_assets,
            "raac_treatment_analysis": config.raac_treatment_analysis,
            "raac_overhead_analysis": config.raac_overhead_analysis,
            "raac_clean_tradeoff_analysis": config.raac_clean_tradeoff_analysis,
        }
    if {"run_dir"}.issubset(raw):
        config = ScoringConfig.model_validate(raw)
        return {
            "valid": True,
            "config_type": "scoring",
            "path": str(path),
            "config_hash": digest,
            "run_dir": config.run_dir,
            "run_dir_exists": Path(config.run_dir).exists(),
        }
    if set(raw) == {"config"}:
        config = CostEstimationConfig.model_validate(raw)
        return {
            "valid": True,
            "config_type": "cost_estimation",
            "path": str(path),
            "config_hash": digest,
            "target_config": config.config,
            "target_exists": Path(config.config).exists(),
        }
    if {"output_path", "n_tasks", "domains"}.issubset(raw):
        config = LegacyTaskGenerationConfig.model_validate(raw)
        return {
            "valid": True,
            "config_type": "legacy_task_generation",
            "path": str(path),
            "config_hash": digest,
            "n_tasks": config.n_tasks,
            "domains": config.domains,
            "interventions": config.interventions,
            "output_path": config.output_path,
        }
    return {
        "valid": True,
        "config_type": "legacy_or_unknown",
        "path": str(path),
        "config_hash": digest,
        "keys": sorted(raw),
    }


def dry_run_config(
    config_path: str | Path,
    *,
    output_dir: str | Path | None = "results/dry_runs",
) -> dict[str, Any]:
    """Validate and locally simulate one trajectory per agent without provider calls."""

    path = Path(config_path)
    summary = validate_config_file(path)
    if summary["config_type"] != "experiment":
        return {
            "dry_run": True,
            "would_execute": False,
            "reason": "dry-run currently supports experiment configs only",
            "config": summary,
            "paid_calls_made": False,
            "scientific_evidence": False,
        }
    config, raw_config = load_experiment_config(path)
    benchmark_path = config.resolved_benchmark_path()
    if not benchmark_path.exists():
        raise FileNotFoundError(
            f"benchmark_path does not exist: {benchmark_path}. Generate the dataset first or update the config."
        )
    loaded_instances = read_jsonl(benchmark_path, BenchmarkInstance)
    if not loaded_instances:
        raise ValueError(f"benchmark_path contains no instances: {benchmark_path}")
    if config.max_instances is not None:
        loaded_instances = loaded_instances[: config.max_instances]
    instances = len(loaded_instances)
    agent_runs = config.iter_agent_runs()
    provider_status = {row["provider"]: row for row in list_provider_status()}
    estimated = estimate_config_cost(path)
    tool_schema_report = _tool_schema_report(loaded_instances[0])
    simulations = []
    prompt_hashes: set[str] = set()
    for agent_run in agent_runs:
        simulation = _simulate_dry_run_agent(
            config=config,
            agent_run=agent_run,
            instance=loaded_instances[0],
        )
        simulations.append(simulation)
        if simulation.get("prompt_version_hash"):
            prompt_hashes.add(str(simulation["prompt_version_hash"]))
        for value in simulation.get("prompt_hashes") or []:
            prompt_hashes.add(str(value))

    provider_rows = []
    for agent_run in agent_runs:
        provider = agent_run.provider
        status = provider_status.get(provider or "", {})
        provider_rows.append(
            {
                "agent_run": agent_run.run_id(),
                "agent": agent_run.agent,
                "provider": provider,
                "model": agent_run.model,
                "model_configured": bool(agent_run.model),
                "provider_configured": bool(status.get("configured")) if provider else None,
                "requires_api_key_for_real_run": provider in PAID_PROVIDERS,
                "required_env_vars": list(status.get("env_vars") or []),
                "secret_values_logged": False,
            }
        )

    model_id_warnings = _model_id_warnings(agent_runs)
    gate_report = check_paid_run_gates(config, config_path=path)
    config_hash = summary.get("config_hash")

    report = {
        "dry_run": True,
        "would_execute": True,
        "config_path": str(path.resolve()),
        "config_hash": config_hash,
        "config": summary,
        "planned_trajectories": instances * len(agent_runs) * config.num_repeats,
        "num_instances": instances,
        "num_agent_runs": len(agent_runs),
        "num_repeats": config.num_repeats,
        "dataset_probe": {
            "benchmark_path": str(benchmark_path),
            "sample_instance_id": loaded_instances[0].instance_id,
            "sample_condition": loaded_instances[0].condition,
        },
        "tool_schema_report": tool_schema_report,
        "simulations": simulations,
        "providers": provider_rows,
        "provider_readiness": {
            "providers": provider_rows,
            "run_allowed": gate_report.get("run_allowed"),
            "run_blocked_reasons": gate_report.get("run_blocked_reasons"),
            "warnings": gate_report.get("warnings"),
            "uses_paid_providers": uses_paid_providers(config),
            "allow_paid_calls": config.allow_paid_calls,
        },
        "model_id_warnings": model_id_warnings,
        "prompt_hashes": sorted(prompt_hashes),
        "cost_estimate": estimated,
        "cost_summary": {
            "expected_max_calls": estimated.get("expected_max_calls"),
            "estimated_input_tokens": estimated.get("estimated_input_tokens"),
            "estimated_output_tokens": estimated.get("estimated_output_tokens"),
            "total_cost_estimate_usd": estimated.get("total_cost_estimate_usd"),
            "budget_status": estimated.get("budget_status"),
            "budget_cap_usd": estimated.get("run_budget_cap_usd"),
            "pricing_known": estimated.get("pricing_known"),
        },
        "paid_calls_made": False,
        "scientific_evidence": False,
        "safety": {
            "will_call_providers": False,
            "will_write_results": output_dir is not None,
            "api_keys_printed": False,
            "provider_calls_replaced_with_local_stub": True,
            "paid_calls_made": False,
            "scientific_evidence": False,
        },
    }
    if output_dir is not None:
        report_dir = _write_dry_run_report(
            report,
            output_dir,
            config.run_name,
            raw_config=raw_config,
        )
        report["report_dir"] = str(report_dir)
    return report


def audit_interventions(
    *,
    benchmark_dir: str | Path | None = None,
    base_tasks_path: str | Path | None = None,
    interventions_path: str | Path | None = None,
    instances_path: str | Path | None = None,
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Run automated intervention-quality checks over an existing benchmark."""

    if benchmark_dir is not None:
        root = Path(benchmark_dir)
        base_tasks_path = root / "base_tasks.jsonl"
        interventions_path = root / "interventions.jsonl"
        instances_path = root / "instances.jsonl"
        output_dir = output_dir or root
    if base_tasks_path is None or interventions_path is None or instances_path is None:
        raise ValueError("provide --benchmark-dir or all of --base-tasks/--interventions/--instances")

    base_tasks = read_jsonl(base_tasks_path, BaseTask)
    interventions = read_jsonl(interventions_path, InterventionSpec)
    instances = read_jsonl(instances_path, BenchmarkInstance)
    report = run_quality_checks(base_tasks, interventions, instances)
    report["provenance"] = _intervention_audit_provenance(
        base_tasks_path=base_tasks_path,
        interventions_path=interventions_path,
        instances_path=instances_path,
        output_dir=output_dir,
        benchmark_dir=benchmark_dir,
    )
    if output_dir is not None:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        write_json(out / "intervention_audit_report.json", report)
        (out / "intervention_audit_report.md").write_text(
            quality_report_markdown(report),
            encoding="utf-8",
        )
    return report


def _intervention_audit_provenance(
    *,
    base_tasks_path: str | Path,
    interventions_path: str | Path,
    instances_path: str | Path,
    output_dir: str | Path | None,
    benchmark_dir: str | Path | None,
) -> dict[str, Any]:
    benchmark_root = Path(benchmark_dir) if benchmark_dir is not None else Path(instances_path).parent
    generation_report = _read_optional_json(benchmark_root / "generation_report.json") or {}
    return {
        "audit_generated_at": datetime.now(UTC).isoformat(),
        "base_tasks_path": str(base_tasks_path),
        "interventions_path": str(interventions_path),
        "instances_path": str(instances_path),
        "benchmark_dir": str(benchmark_root),
        "output_dir": str(output_dir) if output_dir is not None else None,
        "git_commit": git_commit(Path.cwd()),
        "benchmark_version": generation_report.get("benchmark_version"),
        "generation_config_hash": generation_report.get("config_hash"),
        "generation_seed": generation_report.get("config", {}).get("seed")
        if isinstance(generation_report.get("config"), dict)
        else None,
        "scope": "Intervention validity audit only; not scientific performance evidence.",
    }


def freeze_dataset(
    source_dir: str | Path,
    *,
    version: str,
    output_dir: str | Path = "data/frozen",
    force: bool = False,
) -> dict[str, Any]:
    """Copy a generated benchmark directory into an immutable release-like folder."""

    source = Path(source_dir)
    if not source.exists():
        raise FileNotFoundError(f"source dataset does not exist: {source}")
    target = Path(output_dir) / _safe_slug(version)
    if target.exists() and not force:
        raise FileExistsError(f"frozen dataset already exists: {target}; pass --force to replace")
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)

    schema_validation = _validate_dataset_schemas(source)
    invalid_schemas = {
        name: summary
        for name, summary in schema_validation.items()
        if int(summary.get("invalid", 0)) > 0
    }
    if invalid_schemas:
        raise ValueError(f"dataset schema validation failed for {sorted(invalid_schemas)}")

    required = ["base_tasks.jsonl", "interventions.jsonl", "instances.jsonl"]
    optional = [
        "generation_report.json",
        "quality_report.md",
        "dataset_card.md",
        "splits.json",
        "human_audit_sample.jsonl",
    ]
    copied: list[str] = []
    for name in required + optional:
        src = source / name
        if src.exists():
            shutil.copy2(src, target / name)
            copied.append(name)
        elif name in required:
            raise FileNotFoundError(f"required dataset file missing: {src}")

    base_tasks = read_jsonl(target / "base_tasks.jsonl", BaseTask)
    interventions = read_jsonl(target / "interventions.jsonl", InterventionSpec)
    instances = read_jsonl(target / "instances.jsonl", BenchmarkInstance)
    generation = _read_optional_json(target / "generation_report.json")
    split_policy = _write_release_splits(target, base_tasks, instances, generation)
    base_tasks = apply_canary_metadata(base_tasks, split_policy, dataset_version=version)
    write_jsonl(target / "base_tasks.jsonl", base_tasks)
    tasks_by_id = {task.task_id: task for task in base_tasks}
    for split_name in ("test", "heldout_templates"):
        split_ids = split_policy.get("splits", {}).get(split_name, {}).get("base_task_ids", [])
        if split_ids:
            write_jsonl(
                target / f"{split_name}_base_tasks.jsonl",
                [tasks_by_id[task_id] for task_id in split_ids if task_id in tasks_by_id],
            )
    for split_file in sorted(target.glob("*_base_tasks.jsonl")) + sorted(
        target.glob("*_instances.jsonl")
    ):
        if split_file.name not in copied:
            copied.append(split_file.name)
    audit = audit_interventions(benchmark_dir=target, output_dir=target)
    if not audit.get("passed"):
        raise ValueError(
            "quality audit failed; inspect intervention_audit_report.json before freezing"
        )
    copied.extend(["intervention_audit_report.json", "intervention_audit_report.md"])
    leakage_report = _split_leakage_report(split_policy, base_tasks)
    if not leakage_report["passed"]:
        raise ValueError(f"split leakage checks failed: {leakage_report['issues'][:3]}")
    contamination_report = run_contamination_audit(target, splits_path=target / "splits.json")
    write_json(target / "contamination_audit_report.json", contamination_report)
    (target / "contamination_audit_report.md").write_text(
        contamination_report_markdown(contamination_report),
        encoding="utf-8",
    )
    copied.extend(["contamination_audit_report.json", "contamination_audit_report.md"])
    card_path = _write_benchmark_card_snapshot(target, version, generation, audit, split_policy)
    copied.append(card_path.name)
    file_hashes = {name: _file_sha256(target / name) for name in sorted(set(copied))}
    dataset_hash = _dataset_hash(_stable_dataset_hash_inputs(file_hashes))
    manifest = {
        "dataset_version": version,
        "frozen_at": datetime.now(UTC).isoformat(),
        "source_dir": str(source),
        "target_dir": str(target),
        "package_version": __version__,
        "git_commit": git_commit(Path.cwd()),
        "files": file_hashes,
        "dataset_hash": dataset_hash,
        "schema_validation": schema_validation,
        "task_counts": _task_counts(base_tasks, instances),
        "intervention_counts": _intervention_counts(interventions, instances),
        "split_policy": split_policy,
        "leakage_report": leakage_report,
        "contamination_audit_summary": contamination_report.get("summary"),
        "contamination_audit_passed": contamination_report.get("passed"),
        "quality_audit_summary": _quality_audit_summary(audit),
        "known_limitations": _freeze_known_limitations(),
        "quality_passed": audit.get("passed"),
        "scope": "Dataset freeze artifact only; not scientific evidence by itself.",
    }
    if generation:
        manifest["source_generation_config_hash"] = generation.get("config_hash")
        manifest["source_benchmark_version"] = generation.get("benchmark_version")
    write_json(target / "freeze_manifest.json", manifest)
    return manifest


def _validate_dataset_schemas(source: Path) -> dict[str, dict[str, Any]]:
    checks = {
        "base_tasks": ("base_tasks.jsonl", "base_tasks"),
        "interventions": ("interventions.jsonl", "interventions"),
        "instances": ("instances.jsonl", "instances"),
    }
    return {
        label: validate_jsonl_file(source / filename, schema)
        for label, (filename, schema) in checks.items()
    }


def _write_release_splits(
    target: Path,
    base_tasks: list[BaseTask],
    instances: list[BenchmarkInstance],
    generation: dict[str, Any],
) -> dict[str, Any]:
    config = generation.get("config", {}) if isinstance(generation.get("config"), dict) else {}
    ordered_tasks = list(base_tasks)
    heldout_size = _heldout_split_size(len(ordered_tasks), config)
    heldout_tasks = _select_heldout_tasks(ordered_tasks, heldout_size)
    heldout_ids = {task.task_id for task in heldout_tasks}
    remaining_tasks = [task for task in ordered_tasks if task.task_id not in heldout_ids]

    dev_size = min(_configured_int(config, "dev_split_size", 20), len(remaining_tasks))
    dev_tasks = remaining_tasks[:dev_size]
    remaining_tasks = remaining_tasks[dev_size:]

    validation_size = min(_proportional_split_size(len(ordered_tasks), 0.1), len(remaining_tasks))
    validation_tasks = remaining_tasks[:validation_size]
    remaining_tasks = remaining_tasks[validation_size:]

    test_size = min(_proportional_split_size(len(ordered_tasks), 0.1), len(remaining_tasks))
    test_tasks = remaining_tasks[:test_size]
    pilot_tasks = remaining_tasks[test_size:]

    splits = {
        "dev": _freeze_split_payload(dev_tasks, instances),
        "pilot": _freeze_split_payload(pilot_tasks, instances),
        "validation": _freeze_split_payload(validation_tasks, instances),
        "test": _freeze_split_payload(test_tasks, instances),
        "heldout_templates": _freeze_split_payload(heldout_tasks, instances),
    }
    policy = {
        "policy_name": "release_disjoint_v1",
        "description": (
            "Frozen release splits are disjoint by base task. Dev is for pipeline checks, "
            "pilot is for early non-final experiments, validation is for method selection, "
            "test is for final held-back evaluation, and heldout_templates reserves later "
            "template variants where possible."
        ),
        "seed": config.get("seed"),
        "benchmark_version": generation.get("benchmark_version"),
        "split_names": list(splits),
        "splits": splits,
    }
    write_json(target / "splits.json", policy)
    tasks_by_id = {task.task_id: task for task in base_tasks}
    instances_by_id = {instance.instance_id: instance for instance in instances}
    for split_name, split in splits.items():
        split_tasks = [tasks_by_id[task_id] for task_id in split["base_task_ids"]]
        split_instances = [
            instances_by_id[instance_id]
            for instance_id in split["instance_ids"]
            if instance_id in instances_by_id
        ]
        write_jsonl(target / f"{split_name}_base_tasks.jsonl", split_tasks)
        write_jsonl(target / f"{split_name}_instances.jsonl", split_instances)
    return policy


def _heldout_split_size(total_tasks: int, config: dict[str, Any]) -> int:
    configured = _configured_int(config, "heldout_split_size", 0)
    if configured > 0:
        return min(configured, max(0, total_tasks - 1))
    if total_tasks < 5:
        return 0
    return min(max(1, total_tasks // 5), max(0, total_tasks - 1))


def _configured_int(config: dict[str, Any], key: str, default: int) -> int:
    value = config.get(key, default)
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return default


def _proportional_split_size(total_tasks: int, fraction: float) -> int:
    if total_tasks < 5:
        return 0
    return max(1, int(total_tasks * fraction))


def _select_heldout_tasks(base_tasks: list[BaseTask], heldout_size: int) -> list[BaseTask]:
    if heldout_size <= 0:
        return []
    selected: list[BaseTask] = []
    selected_templates: set[str] = set()
    for task in reversed(base_tasks):
        template = _template_key(task)
        if template in selected_templates:
            continue
        selected.append(task)
        selected_templates.add(template)
        if len(selected) >= heldout_size:
            return list(reversed(selected))
    selected_ids = {task.task_id for task in selected}
    for task in reversed(base_tasks):
        if task.task_id in selected_ids:
            continue
        selected.append(task)
        if len(selected) >= heldout_size:
            break
    return list(reversed(selected))


def _freeze_split_payload(
    tasks: list[BaseTask],
    instances: list[BenchmarkInstance],
) -> dict[str, Any]:
    task_ids = [task.task_id for task in tasks]
    task_id_set = set(task_ids)
    instance_ids = [
        instance.instance_id
        for instance in instances
        if instance.base_task.task_id in task_id_set
    ]
    return {
        "base_task_ids": task_ids,
        "instance_ids": instance_ids,
        "base_task_count": len(task_ids),
        "instance_count": len(instance_ids),
    }


def _split_leakage_report(
    split_policy: dict[str, Any],
    base_tasks: list[BaseTask],
) -> dict[str, Any]:
    tasks_by_id = {task.task_id: task for task in base_tasks}
    split_task_ids = {
        split_name: list(split.get("base_task_ids", []))
        for split_name, split in split_policy.get("splits", {}).items()
    }
    issues: list[str] = []
    warnings: list[str] = []
    seen_task_splits: dict[str, str] = {}
    for split_name, task_ids in split_task_ids.items():
        for task_id in task_ids:
            previous = seen_task_splits.get(task_id)
            if previous is not None:
                issues.append(f"base task {task_id} appears in both {previous} and {split_name}")
            seen_task_splits[task_id] = split_name

    for label, signature_fn in [
        ("instruction", lambda task: task.goal.user_instruction.strip()),
        ("ground_truth", _ground_truth_signature),
    ]:
        locations: dict[str, set[str]] = {}
        for split_name, task_ids in split_task_ids.items():
            for task_id in task_ids:
                task = tasks_by_id.get(task_id)
                if task is None:
                    issues.append(f"split {split_name} references missing base task {task_id}")
                    continue
                signature = signature_fn(task)
                locations.setdefault(signature, set()).add(split_name)
        leaked = {
            signature: sorted(split_names)
            for signature, split_names in locations.items()
            if len(split_names) > 1
        }
        if leaked:
            issues.append(f"duplicate {label} objects appear across splits: {list(leaked)[:3]}")

    heldout_ids = split_task_ids.get("heldout_templates", [])
    heldout_templates = [_template_key(tasks_by_id[task_id]) for task_id in heldout_ids if task_id in tasks_by_id]
    duplicate_heldout_templates = [
        template for template, count in Counter(heldout_templates).items() if count > 1
    ]
    all_unique_templates = len({_template_key(task) for task in base_tasks})
    if duplicate_heldout_templates and all_unique_templates >= len(heldout_ids):
        issues.append(
            "heldout_templates repeats template keys even though enough unique templates exist"
        )
    elif duplicate_heldout_templates:
        warnings.append("heldout_templates repeats template keys because unique templates are limited")

    return {
        "passed": not issues,
        "issues": issues,
        "warnings": warnings,
        "checks": [
            "base_task_ids_disjoint",
            "no_identical_instructions_across_splits",
            "no_duplicate_ground_truth_objects_across_splits",
            "heldout_templates_unique_when_possible",
        ],
    }


def _ground_truth_signature(task: BaseTask) -> str:
    return stable_hash(
        {
            "expected_final_answer": task.goal.expected_final_answer,
            "hidden_ground_truth": task.hidden_ground_truth,
        }
    )


def _template_key(task: BaseTask) -> str:
    template_domain = task.hidden_ground_truth.get("template_domain") or task.domain
    template_variant = task.metadata.get("template_variant", task.hidden_ground_truth.get("variant"))
    return stable_hash(
        {
            "domain": task.domain,
            "template_domain": template_domain,
            "template_variant": template_variant,
            "tags": task.tags,
        }
    )


def _write_benchmark_card_snapshot(
    target: Path,
    version: str,
    generation: dict[str, Any],
    audit: dict[str, Any],
    split_policy: dict[str, Any],
) -> Path:
    source_card = Path("docs/BENCHMARK_CARD.md")
    body = source_card.read_text(encoding="utf-8") if source_card.exists() else "# Benchmark Card\n"
    snapshot = [
        f"# Benchmark Card Snapshot: {version}",
        "",
        "This snapshot is bundled with a frozen dataset artifact. It documents dataset construction and limitations; it is not scientific performance evidence.",
        "",
        "## Freeze Metadata",
        "",
        f"- Dataset version: `{version}`",
        f"- Source benchmark version: `{generation.get('benchmark_version')}`",
        f"- Generation config hash: `{generation.get('config_hash')}`",
        f"- Quality audit passed: `{audit.get('passed')}`",
        f"- Split policy: `{split_policy.get('policy_name')}`",
        "",
        "## Source Benchmark Card",
        "",
        body.rstrip(),
        "",
    ]
    path = target / "benchmark_card_snapshot.md"
    path.write_text("\n".join(snapshot), encoding="utf-8")
    return path


def _dataset_hash(file_hashes: dict[str, str]) -> str:
    digest = sha256()
    for name, file_hash in sorted(file_hashes.items()):
        digest.update(name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_hash.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def _stable_dataset_hash_inputs(file_hashes: dict[str, str]) -> dict[str, str]:
    mutable_reports = {
        "intervention_audit_report.json",
        "intervention_audit_report.md",
        "contamination_audit_report.json",
        "contamination_audit_report.md",
    }
    return {name: digest for name, digest in file_hashes.items() if name not in mutable_reports}


def _task_counts(
    base_tasks: list[BaseTask],
    instances: list[BenchmarkInstance],
) -> dict[str, Any]:
    return {
        "base_tasks": len(base_tasks),
        "instances": len(instances),
        "clean_instances": sum(1 for instance in instances if instance.condition == "clean"),
        "intervention_instances": sum(
            1 for instance in instances if instance.condition == "intervention"
        ),
        "domains": dict(sorted(Counter(task.domain for task in base_tasks).items())),
        "difficulties": dict(sorted(Counter(task.difficulty for task in base_tasks).items())),
    }


def _intervention_counts(
    interventions: list[InterventionSpec],
    instances: list[BenchmarkInstance],
) -> dict[str, Any]:
    return {
        "interventions": len(interventions),
        "families": dict(sorted(Counter(intervention.family for intervention in interventions).items())),
        "instances_by_family": dict(
            sorted(
                Counter(
                    instance.intervention.family
                    for instance in instances
                    if instance.intervention is not None
                ).items()
            )
        ),
    }


def _quality_audit_summary(audit: dict[str, Any]) -> dict[str, Any]:
    return {
        "passed": audit.get("passed"),
        "counts": audit.get("counts", {}),
        "validity_score_counts": audit.get("validity_score_counts", {}),
        "warnings_count": len(audit.get("warnings", [])),
        "base_task_issues": len(audit.get("base_task_issues", {})),
        "intervention_issues": len(audit.get("intervention_issues", {})),
        "instance_issues": len(audit.get("instance_issues", {})),
    }


def _freeze_known_limitations() -> list[str]:
    return [
        "Frozen datasets are deterministic synthetic artifacts, not final scientific evidence.",
        "Human validation is still required before strong claims about label or intervention validity.",
        "Oracle agents must be reported only as sanity-check upper bounds.",
        "Provider-backed results must cite configs, run directories, model IDs, prompt hashes, scorer versions, seeds, and git commits when available.",
    ]


def summarize_run(run_dir: str | Path, *, output_path: str | Path | None = None) -> dict[str, Any]:
    """Create a concise run summary from run metadata and aggregate scores."""

    root = Path(run_dir)
    metadata = _read_optional_json(root / "metadata.json") or _read_optional_json(
        root / "run_metadata.json"
    )
    aggregate = _read_optional_json(root / "aggregate_scores.json") or {}
    errors = _count_jsonl_rows(root / "errors.jsonl") if (root / "errors.jsonl").exists() else 0
    trajectories = (
        _count_jsonl_rows(root / "trajectories.jsonl")
        if (root / "trajectories.jsonl").exists()
        else 0
    )
    summary = {
        "run_dir": str(root),
        "run_name": metadata.get("run_name"),
        "timestamp": metadata.get("timestamp"),
        "config_hash": metadata.get("config_hash"),
        "dataset_version": metadata.get("dataset_version"),
        "agents": metadata.get("agents", []),
        "model_ids": metadata.get("model_ids", []),
        "number_of_instances": metadata.get("number_of_instances"),
        "trajectories": trajectories,
        "errors": errors,
        "score_records": aggregate.get("n_score_records"),
        "scientific_scope": _scientific_scope(metadata),
        "evidence_scope": metadata.get("evidence_scope"),
        "providers": metadata.get("providers", []),
        "claim_status": "not submission evidence unless cited in docs/claim_ledger.json",
    }
    out = Path(output_path) if output_path else root / "run_summary.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(_run_summary_markdown(summary), encoding="utf-8")
    return summary


def _experiment_readiness(
    config: ExperimentConfig,
    benchmark_path: Path,
    raw_config: dict[str, Any],
) -> dict[str, Any]:
    provider_status = {row["provider"]: row for row in list_provider_status()}
    provider_checks: list[dict[str, Any]] = []
    issues: list[dict[str, str]] = []
    if not benchmark_path.exists():
        issues.append(
            {
                "severity": "error",
                "field": "benchmark_path",
                "message": f"Benchmark file is missing: {benchmark_path}",
                "fix": "Generate the dataset or update benchmark_path/benchmark_dir.",
            }
        )
    secret_paths = _secret_key_paths(raw_config)
    if secret_paths:
        issues.append(
            {
                "severity": "error",
                "field": "secrets",
                "message": f"Secret-like config keys detected at {secret_paths}; values were not displayed.",
                "fix": "Move API keys and secrets to environment variables instead of YAML configs.",
            }
        )
    for agent_run in config.iter_agent_runs():
        provider = agent_run.provider
        if provider in PAID_PROVIDERS and agent_run.agent in ORACLE_AGENT_NAMES:
            issues.append(
                {
                    "severity": "error",
                    "field": f"agent_runs.{agent_run.run_id()}.agent",
                    "message": (
                        f"Oracle agent {agent_run.agent!r} cannot be used in provider pilot configs."
                    ),
                    "fix": "Remove scripted_oracle_agent from realistic provider configs.",
                }
            )
        status = provider_status.get(provider or "", {})
        env_vars = [agent_run.api_key_env] if agent_run.api_key_env else status.get("env_vars", [])
        api_key_configured = any(os.getenv(name) for name in env_vars)
        check = {
            "agent_run": agent_run.run_id(),
            "agent": agent_run.agent,
            "provider": provider,
            "model_configured": bool(agent_run.model),
            "base_url_configured": bool(agent_run.base_url or status.get("base_url_configured")),
            "api_key_configured": api_key_configured if provider in PAID_PROVIDERS else None,
            "required_env_vars": env_vars if provider else [],
        }
        provider_checks.append(check)
        if provider == "openai_compatible" and not check["base_url_configured"]:
            issues.append(
                {
                    "severity": "error",
                    "field": f"agent_runs.{agent_run.run_id()}.base_url",
                    "message": "Generic OpenAI-compatible provider requires a base URL.",
                    "fix": "Set base_url in the agent run or OPENAI_COMPATIBLE_BASE_URL in the environment.",
                }
            )
        if provider in PAID_PROVIDERS and not agent_run.model:
            issues.append(
                {
                    "severity": "error",
                    "field": f"agent_runs.{agent_run.run_id()}.model",
                    "message": f"Model is empty for paid provider {provider!r}.",
                    "fix": "Set the model field or the corresponding *_MODEL_ID environment variable.",
                }
            )
        if provider in PAID_PROVIDERS and not api_key_configured:
            issues.append(
                {
                    "severity": "warning",
                    "field": f"agent_runs.{agent_run.run_id()}.provider",
                    "message": f"API key is not configured for provider {provider!r}.",
                    "fix": f"Set one of {env_vars} before running paid provider experiments.",
                }
            )
        if provider in PAID_PROVIDERS and not config.resolved_pricing(agent_run):
            issues.append(
                {
                    "severity": "warning",
                    "field": f"agent_runs.{agent_run.run_id()}.pricing",
                    "message": "Pricing is not configured; cost estimates will be unknown.",
                    "fix": "Add input_per_1m_tokens/output_per_1m_tokens if you want numeric cost bounds.",
                }
            )
        if provider == "local_openai" and not agent_run.model:
            issues.append(
                {
                    "severity": "error",
                    "field": f"agent_runs.{agent_run.run_id()}.model",
                    "message": "Local open-weight provider requires a model ID.",
                    "fix": "Set model in the agent run or LOCAL_OPENAI_MODEL_ID in the environment.",
                }
            )
        if provider == "local_openai" and not check["base_url_configured"]:
            issues.append(
                {
                    "severity": "warning",
                    "field": f"agent_runs.{agent_run.run_id()}.base_url",
                    "message": "LOCAL_OPENAI_BASE_URL is unset; defaulting to http://localhost:8000/v1.",
                    "fix": "Set base_url or LOCAL_OPENAI_BASE_URL to match your local server.",
                }
            )
    if uses_paid_providers(config) and not config.allow_paid_calls:
        issues.append(
            {
                "severity": "error",
                "field": "allow_paid_calls",
                "message": "Commercial API providers are configured but allow_paid_calls is false.",
                "fix": "Set allow_paid_calls: true explicitly before running paid provider experiments.",
            }
        )
    if config.budget_cap_usd is not None:
        estimate = estimate_experiment_cost(config)
        upper = estimate.get("known_cost_upper_bound_usd")
        if upper is not None and upper > config.budget_cap_usd:
            issues.append(
                {
                    "severity": "error",
                    "field": "budget_cap_usd",
                    "message": (
                        "Estimated run cost exceeds budget_cap_usd: "
                        f"estimate=${upper:.8f}, cap=${config.budget_cap_usd:.8f}"
                    ),
                    "fix": "Raise budget_cap_usd, reduce instances/agents/steps, or update pricing assumptions.",
                }
            )
    ready_to_run = not any(
        issue["severity"] == "error" or "API key is not configured" in issue["message"]
        for issue in issues
    )
    return {"provider_checks": provider_checks, "issues": issues, "ready_to_run": ready_to_run}


def _secret_key_paths(value: Any, prefix: str = "") -> list[str]:
    matches: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key)
            path = f"{prefix}.{key_text}" if prefix else key_text
            lowered = key_text.lower()
            if any(marker in lowered for marker in ("api_key", "secret", "password")):
                matches.append(path)
            matches.extend(_secret_key_paths(item, path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            matches.extend(_secret_key_paths(item, f"{prefix}[{index}]"))
    return matches


def _tool_schema_report(instance: BenchmarkInstance) -> dict[str, Any]:
    registry = ToolRegistry()
    specs = registry.specs(instance.available_tools)
    issues: list[dict[str, str]] = []
    for spec in specs:
        if not isinstance(spec.input_schema, dict):
            issues.append({"tool": spec.name, "message": "input_schema is not a mapping"})
        if not isinstance(spec.output_schema, dict):
            issues.append({"tool": spec.name, "message": "output_schema is not a mapping"})
        if "properties" not in spec.input_schema:
            issues.append({"tool": spec.name, "message": "input_schema lacks properties"})
    return {
        "checked_tools": len(specs),
        "available_tools": list(instance.available_tools),
        "issues": issues,
        "valid": not issues,
    }


def _simulate_dry_run_agent(
    *,
    config: ExperimentConfig,
    agent_run: AgentRunConfig,
    instance: BenchmarkInstance,
) -> dict[str, Any]:
    try:
        trajectory = execute_agent_on_instance(
            agent_name=agent_run.agent,
            instance=instance,
            run_id=f"dry_run_{_safe_slug(config.run_name)}",
            seed=config.seed,
            repeat=0,
            max_steps=min(config.max_steps, 3),
            save_observations=True,
            save_agent_thoughts=True,
            agent_run_id=f"{agent_run.run_id()}__dry_run",
            agent_kwargs=_dry_agent_kwargs(agent_run, config),
        )
    except Exception as exc:
        return {
            "agent_run": agent_run.run_id(),
            "agent": agent_run.agent,
            "ok": False,
            "error_type": type(exc).__name__,
            "message": str(exc),
            "provider_calls_made": False,
            "planned_provider": agent_run.provider,
            "planned_model": agent_run.model,
        }
    meta = trajectory.metadata
    prompt_hash = meta.get("prompt_version_hash") or meta.get("prompt_hash")
    prompt_files = meta.get("prompt_files")
    return {
        "agent_run": agent_run.run_id(),
        "agent": agent_run.agent,
        "ok": True,
        "planned_provider": agent_run.provider,
        "planned_model": agent_run.model,
        "dry_provider": "local_stub",
        "dry_model": meta.get("model_id") or "local-stub",
        "instance_id": instance.instance_id,
        "steps": len(trajectory.steps),
        "terminated_reason": trajectory.terminated_reason,
        "final_answer_present": trajectory.final_answer is not None,
        "estimated_cost_usd": meta.get("estimated_cost_usd", 0.0),
        "prompt_version_hash": prompt_hash,
        "prompt_hashes": meta.get("prompt_hashes") or ([prompt_hash] if prompt_hash else []),
        "prompt_files": prompt_files,
        "provider_calls_made": False,
        "trajectory_log": sanitize_metadata(
            {
                "agent_run": agent_run.run_id(),
                "instance_id": instance.instance_id,
                "steps": len(trajectory.steps),
                "terminated_reason": trajectory.terminated_reason,
                "final_answer_present": trajectory.final_answer is not None,
                "prompt_version_hash": prompt_hash,
                "prompt_files": prompt_files,
                "llm_call_count": meta.get("llm_call_count", 0),
                "tool_call_count": meta.get("tool_call_count", 0),
                "dry_run": True,
                "provider_calls_made": False,
            }
        ),
    }


def _dry_agent_kwargs(agent_run: AgentRunConfig, config: ExperimentConfig) -> dict[str, Any]:
    if agent_run.provider is None:
        return {}
    pricing_registry = None
    pricing_path = config.resolved_pricing_registry_path()
    if pricing_path is not None and pricing_path.exists():
        from causal_agent_bench.runners.registries import load_model_pricing_registry

        pricing_registry = load_model_pricing_registry(pricing_path)
    return {
        "provider": "local_stub",
        "model": agent_run.model or "local-stub-dry-run",
        "temperature": agent_run.temperature,
        "max_tokens": min(agent_run.max_tokens, 256),
        "retry_count": 0,
        "timeout": min(agent_run.timeout, 10.0),
        "pricing": config.resolved_pricing(agent_run, pricing_registry=pricing_registry),
        **agent_run.extra,
    }


def _model_id_warnings(agent_runs: list[AgentRunConfig]) -> list[dict[str, str]]:
    warnings: list[dict[str, str]] = []
    for agent_run in agent_runs:
        if agent_run.provider not in PAID_PROVIDERS:
            continue
        if agent_run.model:
            continue
        env_vars = PROVIDER_MODEL_ENV_VARS.get(agent_run.provider or "", ())
        warnings.append(
            {
                "agent_run": agent_run.run_id(),
                "provider": agent_run.provider or "",
                "message": (
                    f"Model ID is empty for {agent_run.run_id()}; "
                    f"set model in config or export {' or '.join(env_vars)} before paid runs."
                ),
            }
        )
    return warnings


def _write_dry_run_report(
    report: dict[str, Any],
    output_dir: str | Path,
    run_name: str,
    *,
    raw_config: dict[str, Any] | None = None,
) -> Path:
    import yaml

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    report_dir = Path(output_dir) / f"{timestamp}_{_safe_slug(run_name)}"
    report_dir.mkdir(parents=True, exist_ok=True)
    write_json(report_dir / "dry_run_report.json", sanitize_metadata(report))
    (report_dir / "dry_run_report.md").write_text(
        _dry_run_report_markdown(report),
        encoding="utf-8",
    )
    if raw_config is not None:
        safe_config = redact_config_for_persistence(raw_config)
        (report_dir / "config.yaml").write_text(
            yaml.safe_dump(safe_config, sort_keys=False),
            encoding="utf-8",
        )
    if report.get("config_hash"):
        (report_dir / "config_hash.txt").write_text(f"{report['config_hash']}\n", encoding="utf-8")
    metadata = sanitize_metadata(
        {
            "dry_run": True,
            "timestamp": datetime.now(UTC).isoformat(),
            "config_path": report.get("config_path"),
            "config_hash": report.get("config_hash"),
            "run_name": report["config"].get("run_name"),
            "paid_calls_made": False,
            "scientific_evidence": False,
            "provider_readiness": report.get("provider_readiness"),
            "model_id_warnings": report.get("model_id_warnings"),
            "prompt_hashes": report.get("prompt_hashes"),
            "cost_summary": report.get("cost_summary"),
            "git_commit": git_commit(Path.cwd()),
            "package_version": __version__,
        }
    )
    write_json(report_dir / "dry_run_metadata.json", metadata)
    write_jsonl(report_dir / "simulations.jsonl", report.get("simulations") or [])
    for simulation in report.get("simulations") or []:
        trajectory_log = simulation.get("trajectory_log")
        if not trajectory_log:
            continue
        slug = _safe_slug(str(simulation.get("agent_run", "agent")))
        write_json(report_dir / f"trajectory_{slug}.json", trajectory_log)
    return report_dir


def _dry_run_report_markdown(report: dict[str, Any]) -> str:
    cost = report.get("cost_summary") or {}
    lines = [
        "# Dry Run Report",
        "",
        "This report validates plumbing only. It does not call paid providers and is not scientific evidence.",
        "",
        f"- Config: `{report.get('config_path') or report['config']['path']}`",
        f"- Config hash: `{report.get('config_hash')}`",
        f"- Run name: `{report['config'].get('run_name')}`",
        f"- Benchmark: `{report['dataset_probe']['benchmark_path']}`",
        f"- Planned trajectories: `{report['planned_trajectories']}`",
        f"- Simulated trajectories: `{len(report['simulations'])}`",
        f"- Tool schemas valid: `{report['tool_schema_report']['valid']}`",
        f"- Paid calls made: `{report.get('paid_calls_made', False)}`",
        f"- Scientific evidence: `{report.get('scientific_evidence', False)}`",
        f"- Expected max calls: `{cost.get('expected_max_calls')}`",
        f"- Estimated cost upper bound (USD): `{cost.get('total_cost_estimate_usd')}`",
        f"- Budget status: `{cost.get('budget_status')}`",
        "",
        "## Provider readiness",
        "",
    ]
    readiness = report.get("provider_readiness") or {}
    lines.append(f"- Run allowed for paid execution: `{readiness.get('run_allowed')}`")
    lines.append(f"- Allow paid calls in config: `{readiness.get('allow_paid_calls')}`")
    for row in report.get("providers") or []:
        lines.append(
            f"- `{row.get('agent_run')}` provider=`{row.get('provider')}` "
            f"model=`{row.get('model') or '<missing>'}` configured=`{row.get('provider_configured')}`"
        )
    if report.get("model_id_warnings"):
        lines.extend(["", "## Model ID warnings", ""])
        for warning in report["model_id_warnings"]:
            lines.append(f"- `{warning['agent_run']}`: {warning['message']}")
    if report.get("prompt_hashes"):
        lines.extend(["", "## Prompt hashes", ""])
        for prompt_hash in report["prompt_hashes"]:
            lines.append(f"- `{prompt_hash}`")
    lines.extend(["", "## Simulations", ""])
    for simulation in report["simulations"]:
        status = "ok" if simulation.get("ok") else "failed"
        lines.append(
            f"- `{simulation.get('agent_run')}`: {status}, "
            f"steps={simulation.get('steps')}, stop={simulation.get('terminated_reason')}, "
            f"dry_provider={simulation.get('dry_provider')}"
        )
    if report["config"].get("issues"):
        lines.extend(["", "## Config Issues", ""])
        for issue in report["config"]["issues"]:
            lines.append(
                f"- {issue['severity']}: {issue['message']} Fix: {issue['fix']}"
            )
    if readiness.get("run_blocked_reasons"):
        lines.extend(["", "## Paid-run blockers (expected during dry-run)", ""])
        for reason in readiness["run_blocked_reasons"]:
            lines.append(f"- {reason}")
    return "\n".join(lines) + "\n"


def _count_jsonl_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def _safe_slug(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "_" for ch in value).strip("_")


def _file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_optional_json(path: Path) -> dict[str, Any]:
    return read_json(path) if path.exists() else {}


def _scientific_scope(metadata: dict[str, Any]) -> str:
    cached = metadata.get("scientific_scope")
    if cached:
        return str(cached)
    from causal_agent_bench.runners.evidence_scope import (
        classify_scientific_scope,
        providers_from_agent_runs,
    )

    agent_runs = metadata.get("agent_runs", [])
    if isinstance(agent_runs, list):
        providers = providers_from_agent_runs(agent_runs)
    else:
        providers = set(metadata.get("providers") or [])
    return classify_scientific_scope(providers, run_name=metadata.get("run_name"))


def _run_summary_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Run Summary",
        "",
        f"- Run directory: `{summary['run_dir']}`",
        f"- Run name: `{summary.get('run_name')}`",
        f"- Timestamp: `{summary.get('timestamp')}`",
        f"- Config hash: `{summary.get('config_hash')}`",
        f"- Dataset version: `{summary.get('dataset_version')}`",
        f"- Agents: `{', '.join(summary.get('agents') or [])}`",
        f"- Model IDs: `{', '.join(summary.get('model_ids') or [])}`",
        f"- Instances: `{summary.get('number_of_instances')}`",
        f"- Trajectories: `{summary.get('trajectories')}`",
        f"- Errors: `{summary.get('errors')}`",
        f"- Score records: `{summary.get('score_records')}`",
        f"- Scientific scope: `{summary.get('scientific_scope')}`",
        f"- Evidence scope: `{summary.get('evidence_scope')}`",
        f"- Providers: `{', '.join(summary.get('providers') or [])}`",
        "",
        "This file is a run audit summary. It is not a scientific claim unless the claim ledger cites this run as evidence.",
    ]
    return "\n".join(lines) + "\n"


def cli_json(payload: dict[str, Any]) -> str:
    """Stable JSON formatting for CLI output."""

    return json.dumps(payload, indent=2, sort_keys=True, default=str)


def config_error_payload(path: str | Path, exc: Exception) -> dict[str, Any]:
    error_type = type(exc).__name__
    if isinstance(exc, ValidationError):
        details = [
            {
                "field": ".".join(str(part) for part in error.get("loc", ())) or "<root>",
                "message": error["msg"],
                "fix": _validation_fix_hint(error),
            }
            for error in exc.errors()
        ]
        message = "; ".join(f"{item['field']}: {item['message']}" for item in details)
    else:
        details = []
        message = str(exc)
    return {
        "valid": False,
        "path": str(path),
        "error_type": error_type,
        "message": message,
        "details": details,
        "secret_values_logged": False,
    }


def _validation_fix_hint(error: dict[str, Any]) -> str:
    location = ".".join(str(part) for part in error.get("loc", ()))
    message = str(error.get("msg", ""))
    if "benchmark_path" in message or "benchmark_dir" in message or "benchmark_path" in location:
        return "Provide exactly one existing benchmark_path or benchmark_dir."
    if "agents" in message or "agent_runs" in message:
        return "Add agents or agent_runs to the config."
    if "Extra inputs" in message:
        return "Remove the unknown key or add it to the appropriate config schema."
    if "provider" in location or "provider" in message:
        return (
            "Use one of: local_stub, openai, anthropic, gemini, openrouter, "
            "openai_compatible, local_openai."
        )
    if "pricing" in location or "pricing" in message:
        return "Use non-negative input_per_1m_tokens/output_per_1m_tokens pricing fields."
    return "Edit the YAML field named above and rerun validate-config."
