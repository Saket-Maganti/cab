#!/usr/bin/env python3
"""Audit YAML experiment configs for evidence, budget, and safety consistency."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "audits" / "config_consistency"

REGISTRY_CONFIGS = frozenset({"model_pricing.yaml", "providers.yaml"})

KNOWN_EVIDENCE_LEVELS = frozenset(
    {
        "dry_run",
        "stub_engineering",
        "mock_diagnostic",
        "local_model_preliminary",
        "free_tier_preliminary",
        "provider_pilot",
        "main_experiment",
        "human_validated",
        "preliminary_or_engineering",
        "engineering_only",
    }
)
KNOWN_PROVIDERS = frozenset(
    {
        "local_stub",
        "local",
        "openai",
        "anthropic",
        "openrouter",
        "gemini",
        "ollama",
        "fake",
        "mock",
    }
)
PAID_PROVIDERS = frozenset({"openai", "anthropic", "openrouter", "gemini"})
SECRET_KEYS = frozenset({"api_key", "secret", "token", "password"})


def _load_yaml(path: Path) -> tuple[dict | None, str | None]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return None, str(exc)
    if not isinstance(data, dict):
        return None, "root must be a mapping"
    return data, None


def _agent_providers(cfg: dict) -> list[str]:
    providers: list[str] = []
    for row in cfg.get("agent_runs", []) or []:
        if isinstance(row, dict) and row.get("provider"):
            providers.append(str(row["provider"]))
    matrix = cfg.get("matrix", {})
    if isinstance(matrix, dict):
        for cell in matrix.get("cells", []) or []:
            if isinstance(cell, dict):
                for row in cell.get("agent_runs", []) or []:
                    if isinstance(row, dict) and row.get("provider"):
                        providers.append(str(row["provider"]))
    return providers


def _max_total_usd(cfg: dict) -> float | None:
    budget = cfg.get("budget")
    if isinstance(budget, dict) and budget.get("max_total_usd") is not None:
        return float(budget["max_total_usd"])
    if cfg.get("budget_cap_usd") is not None:
        return float(cfg["budget_cap_usd"])
    return None


def _is_micro(cfg: dict, path: Path) -> bool:
    name = str(cfg.get("run_name") or path.stem).lower()
    if "micro" in name or "smoke" in name:
        return True
    limits = cfg.get("limits") or {}
    if isinstance(limits, dict):
        for key in ("max_trajectories", "max_instances", "max_agents"):
            val = limits.get(key)
            if val is not None and int(val) <= 10:
                return True
    for key in ("max_instances", "max_trajectories"):
        val = cfg.get(key)
        if val is not None and int(val) <= 10:
            return True
    return False


def _dataset_path(cfg: dict) -> Path | None:
    raw = cfg.get("benchmark_path") or cfg.get("instances_path")
    if not raw:
        return None
    return (ROOT / str(raw)).resolve()


def _paired_generate_config(benchmark_path: Path) -> Path | None:
    parts = benchmark_path.parts
    if "processed" not in parts and "frozen" not in parts:
        return None
    dataset_name = benchmark_path.parent.name
    candidate = ROOT / "configs" / f"generate_{dataset_name}.yaml"
    if candidate.exists():
        return candidate
    if dataset_name == "pilot_v0_1":
        alt = ROOT / "configs" / "generate_pilot_v0_1.yaml"
        if alt.exists():
            return alt
    return None


def _walk_keys(obj: object, prefix: str = "") -> list[str]:
    keys: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            keys.append(path)
            keys.extend(_walk_keys(value, path))
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            keys.extend(_walk_keys(item, f"{prefix}[{idx}]"))
    return keys


def audit_config(path: Path) -> dict:
    cfg, err = _load_yaml(path)
    rel = str(path.relative_to(ROOT))
    row: dict = {"path": rel, "issues": [], "warnings": [], "fixes_applied": []}
    if path.name in REGISTRY_CONFIGS:
        if err:
            row["issues"].append(f"invalid YAML: {err}")
        else:
            row["warnings"].append("registry config (skipped experiment-field checks)")
        return row
    if err:
        row["issues"].append(f"invalid YAML: {err}")
        return row

    if not cfg.get("description") and not cfg.get("purpose"):
        row["warnings"].append("missing description/purpose field")

    evidence = cfg.get("scientific_evidence_level") or cfg.get("evidence_level")
    if evidence and evidence not in KNOWN_EVIDENCE_LEVELS:
        row["issues"].append(f"unknown evidence level: {evidence}")

    providers = _agent_providers(cfg)
    for provider in providers:
        base = provider.split("_")[0]
        if provider not in KNOWN_PROVIDERS and base not in KNOWN_PROVIDERS:
            row["warnings"].append(f"unknown provider: {provider}")

    allow_paid = cfg.get("allow_paid_calls")
    uses_paid_provider = any(p.split("_")[0] in PAID_PROVIDERS for p in providers)
    if uses_paid_provider and allow_paid is None:
        row["issues"].append("paid-capable config missing allow_paid_calls")
    if allow_paid is True:
        budget = cfg.get("budget") or {}
        require = budget.get("require_explicit_paid_approval") if isinstance(budget, dict) else None
        if require is not True and cfg.get("require_explicit_paid_approval") is not True:
            row["issues"].append("allow_paid_calls=true but require_explicit_paid_approval not true")
        max_usd = _max_total_usd(cfg)
        if max_usd is None or max_usd <= 0:
            row["issues"].append("paid config missing positive budget cap")

    cost_mode = str(cfg.get("cost_mode", "")).lower()
    max_usd = _max_total_usd(cfg)
    if cost_mode == "zero_cost" or (allow_paid is False and uses_paid_provider is False):
        if max_usd not in (None, 0, 0.0):
            row["warnings"].append(f"zero-cost config has max_total_usd={max_usd}")
        elif max_usd is None and allow_paid is False:
            row["warnings"].append("zero-cost config should set budget.max_total_usd: 0")

    if _is_micro(cfg, path):
        limits = cfg.get("limits") or {}
        max_traj = cfg.get("max_trajectories") or (
            limits.get("max_trajectories") if isinstance(limits, dict) else None
        )
        if max_traj is not None and int(max_traj) > 20:
            row["warnings"].append(f"micro config max_trajectories={max_traj} > 20")

    for run in cfg.get("agent_runs", []) or []:
        if isinstance(run, dict) and "oracle" in str(run.get("agent", "")).lower():
            if allow_paid is not False and "stub" not in rel and "mock" not in rel:
                row["warnings"].append(f"oracle agent in non-stub config: {run.get('name')}")

    output_dir = cfg.get("output_dir")
    if output_dir and output_dir != "results":
        row["warnings"].append(f"nonstandard output_dir: {output_dir}")

    dataset = _dataset_path(cfg)
    if dataset and not dataset.exists():
        gen = _paired_generate_config(dataset)
        if gen:
            row["warnings"].append(f"dataset missing; generate via {gen.relative_to(ROOT)}")
        else:
            row["issues"].append(f"dataset path missing: {dataset.relative_to(ROOT)}")

    for key_path in _walk_keys(cfg):
        leaf = key_path.rsplit(".", 1)[-1].lower()
        if leaf in SECRET_KEYS:
            if path.name == "providers.yaml" and leaf == "api_key":
                row["warnings"].append("providers registry references api_key env var names")
            else:
                row["issues"].append(f"possible secret key name in config: {key_path}")

    return row


def apply_safe_fixes(path: Path, row: dict) -> None:
    if path.name in REGISTRY_CONFIGS:
        return
    cfg, err = _load_yaml(path)
    if err or cfg is None:
        return
    changed = False
    if cfg.get("allow_paid_calls") is None:
        cfg["allow_paid_calls"] = False
        changed = True
        row["fixes_applied"].append("set allow_paid_calls: false")
    if _is_micro(cfg, path) and not cfg.get("scientific_evidence_level"):
        cfg["scientific_evidence_level"] = "preliminary_or_engineering"
        changed = True
        row["fixes_applied"].append("set scientific_evidence_level: preliminary_or_engineering")
    if cfg.get("allow_paid_calls") is False and isinstance(cfg.get("budget"), dict):
        if cfg["budget"].get("max_total_usd") is None:
            cfg["budget"]["max_total_usd"] = 0
            changed = True
            row["fixes_applied"].append("set budget.max_total_usd: 0")
    if cfg.get("allow_paid_calls") is True:
        if not isinstance(cfg.get("budget"), dict):
            cfg["budget"] = {}
        budget = cfg["budget"]
        if budget.get("require_explicit_paid_approval") is not True:
            budget["require_explicit_paid_approval"] = True
            changed = True
            row["fixes_applied"].append("set budget.require_explicit_paid_approval: true")
    if changed:
        path.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")


def run_audit(*, apply_fixes: bool = False) -> dict:
    rows: list[dict] = []
    for path in sorted((ROOT / "configs").glob("*.yaml")):
        row = audit_config(path)
        if apply_fixes:
            apply_safe_fixes(path, row)
            if row["fixes_applied"]:
                row = audit_config(path)
                row["fixes_applied"] = row.get("fixes_applied", [])
        rows.append(row)

    issues = sum(len(r["issues"]) for r in rows)
    warnings = sum(len(r["warnings"]) for r in rows)
    fixes = sum(len(r.get("fixes_applied", [])) for r in rows)
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "passed": issues == 0,
        "configs_scanned": len(rows),
        "issue_count": issues,
        "warning_count": warnings,
        "fixes_applied": fixes,
        "configs": rows,
    }


def _markdown_report(report: dict) -> str:
    lines = [
        "# Config Consistency Audit",
        "",
        f"**Generated:** {report['generated_at']}",
        f"**Passed:** {report['passed']}",
        f"**Configs scanned:** {report['configs_scanned']}",
        f"**Issues:** {report['issue_count']} · **Warnings:** {report['warning_count']}",
        "",
    ]
    bad = [r for r in report["configs"] if r["issues"]]
    if bad:
        lines.extend(["## Issues by config", ""])
        for row in bad:
            lines.append(f"### `{row['path']}`")
            for issue in row["issues"]:
                lines.append(f"- {issue}")
            lines.append("")
    warn = [r for r in report["configs"] if r["warnings"] and not r["issues"]]
    if warn:
        lines.extend(["## Warnings (no blocking issues)", ""])
        for row in warn[:15]:
            lines.append(f"- `{row['path']}`: {'; '.join(row['warnings'][:3])}")
        lines.append("")
    fixed = [r for r in report["configs"] if r.get("fixes_applied")]
    if fixed:
        lines.extend(["## Safe fixes applied", ""])
        for row in fixed:
            lines.append(f"- `{row['path']}`: {', '.join(row['fixes_applied'])}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit YAML configs.")
    parser.add_argument("--output-dir", default=str(OUT_DIR))
    parser.add_argument(
        "--apply-safe-fixes",
        action="store_true",
        help="Apply conservative fixes (allow_paid_calls, evidence level, zero budget).",
    )
    args = parser.parse_args(argv)

    report = run_audit(apply_fixes=args.apply_safe_fixes)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "config_audit.json"
    md_path = out_dir / "CONFIG_AUDIT.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(_markdown_report(report), encoding="utf-8")
    print(f"wrote {md_path}")
    print(f"wrote {json_path}")
    print(
        f"audit: {'PASS' if report['passed'] else 'FAIL'} "
        f"({report['issue_count']} issues, {report['warning_count']} warnings)"
    )
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
