"""Pre-provider-pilot benchmark and dataset card generator."""

from __future__ import annotations

import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from causal_agent_bench.safety.benchmark_quality import discover_benchmark_dirs
from causal_agent_bench.safety.common import classify_run_entry, load_run_index_entries

CARD_FILENAMES = {
    "benchmark_card": "benchmark_card.md",
    "dataset_card": "dataset_card.md",
    "intervention_card": "intervention_card.md",
    "limitations_card": "limitations_card.md",
}


def build_benchmark_cards(
    repo_root: str | Path,
    *,
    output_dir: str | Path = "reports/benchmark_cards",
    benchmark_dir: str | Path | None = None,
    reports_dir: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    out = Path(output_dir)
    if not out.is_absolute():
        out = root / out
    out.mkdir(parents=True, exist_ok=True)
    reports = Path(reports_dir) if reports_dir else root / "reports"
    if not reports.is_absolute():
        reports = root / reports

    dataset_dirs = [Path(benchmark_dir)] if benchmark_dir else discover_benchmark_dirs(root)
    datasets = [_summarize_dataset(path if path.is_absolute() else root / path, root) for path in dataset_dirs]
    evidence = _evidence_state(root)
    leakage = _leakage_summary(reports)
    taxonomy = _taxonomy_summary(root)
    generated_at = datetime.now(UTC).isoformat()
    context = {
        "generated_at": generated_at,
        "datasets": datasets,
        "evidence": evidence,
        "leakage": leakage,
        "taxonomy": taxonomy,
        "stage": "pre-provider-pilot",
    }
    contents = {
        "benchmark_card": _benchmark_card(context),
        "dataset_card": _dataset_card(context),
        "intervention_card": _intervention_card(context),
        "limitations_card": _limitations_card(context),
    }
    files: dict[str, str] = {}
    for key, filename in CARD_FILENAMES.items():
        path = out / filename
        path.write_text(contents[key], encoding="utf-8")
        files[key] = str(path)
    manifest = {
        "generated_at": generated_at,
        "scope": "Pre-provider-pilot descriptive cards only; no empirical results are claimed.",
        "stage": "pre-provider-pilot",
        "files": files,
        "dataset_count": len(datasets),
        "current_evidence_state": evidence,
        "hard_rules": {
            "no_empirical_results_claimed": True,
            "C1_C8_supported": False,
            "C9_status": "engineering_only",
            "C10_supported": False,
            "claims_promoted": False,
        },
    }
    manifest_path = out / "benchmark_cards_manifest.json"
    manifest["report_paths"] = {**files, "manifest": str(manifest_path)}
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest["manifest_path"] = str(manifest_path)
    return manifest


def _benchmark_card(context: dict[str, Any]) -> str:
    evidence = context["evidence"]
    taxonomy = context["taxonomy"]
    task_families = _join_counter(_counter_union(context["datasets"], "task_family_counts"))
    intervention_families = _join_counter(taxonomy["intervention_type_counts"])
    return "\n".join(
        [
            "# Benchmark Card",
            "",
            f"Generated: {context['generated_at']}",
            "",
            "Status: pre-provider-pilot. No empirical results are claimed in this card.",
            "",
            "## Benchmark Purpose",
            "",
            "Causal Agent Bench is a static benchmark scaffold for evaluating tool-using LLM agents under paired clean and causal-intervention variants.",
            "",
            "## Intended Use",
            "",
            "- Method development for paired clean/intervention evaluation.",
            "- No-run review of dataset, intervention, and configuration readiness.",
            "- Planning a small future provider pilot after advisor approval.",
            "",
            "## Out-of-Scope Use",
            "",
            "- Claiming model performance, robustness, rankings, or human-validation outcomes from the current no-run assets.",
            "- Treating mock, oracle, local stub, or static reports as paper-eligible empirical evidence.",
            "",
            "## Task Families",
            "",
            task_families or "- Needs review; no task families were detected.",
            "",
            "## Intervention Families",
            "",
            intervention_families or "- Needs review; no intervention families were detected.",
            "",
            "## Tool-Use Environment",
            "",
            "Tasks reference simulated tools and deterministic task metadata. Tool schemas should be validated statically before any provider spend.",
            "",
            "## Scoring Metrics",
            "",
            "The repository includes final-answer, tool-use, recovery, and causal robustness metric scaffolds. Current cards do not report metric values.",
            "",
            "## Evidence Levels",
            "",
            "- Static/no-run reports: method and readiness evidence only.",
            "- Mock/oracle/local outputs: engineering-only unless later reviewed under strict policy.",
            "- Provider-backed runs: not yet available as paper-eligible evidence.",
            "",
            "## Current Evidence State",
            "",
            f"- Paper-eligible runs: {evidence['paper_eligible_runs']}",
            f"- Eligible paper assets: {evidence['eligible_paper_assets']}",
            "- C1-C8: planned / unsupported",
            "- C9: engineering_only",
            "- C10: planned / unsupported",
            "",
            "## Leakage Status",
            "",
            f"- Provider-pilot leakage blocker clusters: {context['leakage']['blocker_clusters']}",
            f"- Must-fix before provider pilot: {context['leakage']['must_fix_before_pilot']}",
            "- Instruction-parameter overlap (task dates in prompts) is calibrated as non-blocking.",
            "",
            "## Human Validation Status",
            "",
            "- Protocol/templates may exist; **no completed annotations**.",
            "- C3 and C10 remain blocked; Table 5 cannot support claims.",
            "",
            "## Release Status",
            "",
            "- Pre-provider-pilot advisory cards only; not a public benchmark v1.0 release claim.",
            "",
            "## Known Limitations",
            "",
            "- No provider-backed empirical evidence is available.",
            "- Human validation is not complete.",
            "- Static audits can find structural issues but cannot prove task validity.",
            "",
            "## No Empirical Results Disclaimer",
            "",
            "This card reports **zero** paper-eligible runs and **zero** eligible empirical assets. Do not cite metric values from mock/stub runs.",
            "",
            "## Ethical and Reproducibility Notes",
            "",
            "Use these cards to document scope and blockers. They must not be used to promote claims or fill empirical paper results.",
            "",
        ]
    )


def _dataset_card(context: dict[str, Any]) -> str:
    datasets = context["datasets"]
    lines = [
        "# Dataset Card",
        "",
        f"Generated: {context['generated_at']}",
        "",
        "Status: pre-provider-pilot. No provider evidence or empirical benchmark results are claimed.",
        "",
        "## Sources and Generation Method",
        "",
        "Datasets are synthetic/generated benchmark assets discovered under repository data directories. Generation reports are referenced when present.",
        "",
        "## Splits and Counts",
        "",
    ]
    if not datasets:
        lines.append("- No dataset directories with instances.jsonl were detected.")
    for dataset in datasets:
        lines.extend(
            [
                f"- `{dataset['path']}`: tasks={dataset['task_count']}, instances={dataset['instance_count']}, heldout={dataset['heldout_status']}",
                f"  quality warnings={dataset['quality_warning_count']}, invalid/high-risk hints={dataset['high_risk_count']}",
            ]
        )
    lines.extend(
        [
            "",
            "## Intervention Distributions",
            "",
            _join_counter(_counter_union(datasets, "intervention_counts")) or "- Needs review.",
            "",
            "## Leakage Status",
            "",
            f"- Blocker clusters (true leakage): {context['leakage']['blocker_clusters']}",
            f"- Must-fix before provider pilot: {context['leakage']['must_fix_before_pilot']}",
            "",
            "## Human Validation Status",
            "",
            "Templates exist; **no scientific annotations**. C3/C10 blocked.",
            "",
            "## Release Status",
            "",
            "Advisory pre-provider-pilot card; not a public v1.0 dataset release.",
            "",
        ]
    )
    return "\n".join(lines)


def _intervention_card(context: dict[str, Any]) -> str:
    taxonomy = context["taxonomy"]
    lines = [
        "# Intervention Card",
        "",
        f"Generated: {context['generated_at']}",
        "",
        "Status: pre-provider-pilot. Intervention definitions support no-run review only.",
        "",
        "## Intervention Taxonomy",
        "",
    ]
    if taxonomy["interventions"]:
        for row in taxonomy["interventions"]:
            lines.extend(
                [
                    f"### {row['intervention_type']}",
                    "",
                    f"- Intended causal factor: {row.get('intended_causal_factor', 'needs_review')}",
                    f"- Allowed changed fields: {', '.join(row.get('allowed_changed_fields', [])) or 'needs_review'}",
                    f"- Expected invariants: {', '.join(row.get('expected_unchanged_fields', [])) or 'needs_review'}",
                    f"- Answer preservation: {row.get('answer_preservation', 'depends')}",
                    f"- Requires human review: {row.get('requires_human_review', True)}",
                    "",
                ]
            )
    else:
        lines.append("- Taxonomy file not detected; built-in conservative defaults should be reviewed.")
    lines.extend(
        [
            "## Validation Methods",
            "",
            "- Static field-change isolation audit.",
            "- Gold-output consistency validator.",
            "- Human review for high-risk or answer-changing interventions.",
            "",
            "## Isolation Risk Notes",
            "",
            "Unknown intervention types, unexpected field changes, and answer-preserving gold-answer changes require review before provider spend.",
            "",
        ]
    )
    return "\n".join(lines)


def _limitations_card(context: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Limitations Card",
            "",
            f"Generated: {context['generated_at']}",
            "",
            "Status: pre-provider-pilot. This card makes no empirical result claims.",
            "",
            "## Synthetic Benchmark Limitations",
            "",
            "- Synthetic tasks may miss real-world ambiguity, distribution shift, and tool-interface complexity.",
            "- Static task metadata can encode assumptions that require human review.",
            "",
            "## Static Validation Limitations",
            "",
            "- Static validators can flag missing, inconsistent, duplicate, or leaky metadata.",
            "- Static validators cannot prove causal validity or model behavior.",
            "",
            "## Evidence Limitations",
            "",
            "- No current provider-backed evidence.",
            "- No empirical paper results yet.",
            "- C1-C8 and C10 remain planned / unsupported.",
            "- C9 is engineering-only if claims are mentioned.",
            "- Human validation is not complete.",
            "",
            "## Use Restriction",
            "",
            "These cards may support method transparency and release review. They cannot support empirical performance, robustness, ranking, ablation, or human-validation claims.",
            "",
        ]
    )


def _summarize_dataset(path: Path, root: Path) -> dict[str, Any]:
    base_tasks = _read_jsonl(path / "base_tasks.jsonl")
    instances = _read_jsonl(path / "instances.jsonl")
    interventions = _read_jsonl(path / "interventions.jsonl")
    split_payload = _read_json(path / "splits.json") or {}
    quality_text = _read_text(path / "quality_report.md").lower()
    rel = _rel(path, root)
    return {
        "path": rel,
        "task_count": len(base_tasks),
        "instance_count": len(instances),
        "intervention_count": len(interventions),
        "heldout_status": "present" if _has_heldout(split_payload, path) else "needs_review",
        "task_family_counts": dict(Counter(str(row.get("domain") or row.get("category") or "unknown") for row in base_tasks)),
        "intervention_counts": dict(Counter(str(_intervention_type(row) or "unknown") for row in interventions or _intervention_instances(instances))),
        "quality_warning_count": quality_text.count("warning") + quality_text.count("needs review"),
        "high_risk_count": sum(1 for row in interventions if "high" in str(row.get("severity") or row.get("intervention_validity_risk") or "").lower()),
    }


def _evidence_state(root: Path) -> dict[str, Any]:
    runs = [classify_run_entry(entry, root) for entry in load_run_index_entries(root)]
    paper_eligible_runs = sum(1 for run in runs if run.get("paper_eligible"))
    assets = _read_json(root / "reports/paper_asset_eligibility.json") or {}
    return {
        "paper_eligible_runs": paper_eligible_runs,
        "eligible_paper_assets": int(assets.get("eligible_count") or 0),
        "C1_C8_status": "planned / unsupported",
        "C9_status": "engineering_only",
        "C10_status": "planned / unsupported",
        "claims_promoted_by_cards": False,
    }


def _taxonomy_summary(root: Path) -> dict[str, Any]:
    path = root / "configs/intervention_taxonomy.yaml"
    payload = _read_yaml_like(path)
    rows = payload.get("interventions") or payload.get("taxonomy") or []
    rows = [row for row in rows if isinstance(row, dict)]
    return {
        "interventions": rows,
        "intervention_type_counts": dict(Counter(str(row.get("intervention_type") or "unknown") for row in rows)),
    }


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        row = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return row if isinstance(row, dict) else None


def _read_yaml_like(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        import yaml

        row = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    return row if isinstance(row, dict) else {}


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _has_heldout(split_payload: dict[str, Any], path: Path) -> bool:
    splits = split_payload.get("splits") if isinstance(split_payload.get("splits"), dict) else split_payload
    if isinstance(splits, dict):
        for name, value in splits.items():
            if str(name).lower() in {"heldout", "test", "heldout_templates"} and value:
                return True
    return any((path / name).exists() for name in ("heldout_instances.jsonl", "test_instances.jsonl"))


def _intervention_instances(instances: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in instances:
        intervention = row.get("intervention")
        if isinstance(intervention, dict):
            out.append(intervention)
    return out


def _intervention_type(row: dict[str, Any]) -> str:
    return str(row.get("family") or row.get("type") or row.get("intervention_type") or "")


def _counter_union(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.get(key) or {})
    return dict(counter)


def _join_counter(counter: dict[str, int]) -> str:
    if not counter:
        return ""
    return "\n".join(f"- `{key}`: {value}" for key, value in sorted(counter.items()))


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _leakage_summary(reports: Path) -> dict[str, Any]:
    payload = _read_json_from_reports(reports, "static_leakage_report.json") or {}
    plan = _read_json_from_reports(reports, "leakage_repair_plan.json") or _read_json_from_reports(
        reports, "leakage_repair_plan/leakage_repair_plan.json"
    ) or {}
    summary_raw = payload.get("summary")
    summary = summary_raw if isinstance(summary_raw, dict) else {}
    plan_summary_raw = plan.get("summary")
    plan_summary = plan_summary_raw if isinstance(plan_summary_raw, dict) else {}
    return {
        "blocker_clusters": int(summary.get("blocker_cluster_count") or 0),
        "must_fix_before_pilot": int(
            plan_summary.get("must_fix_before_provider_pilot_count") or summary.get("blocker_cluster_count") or 0
        ),
    }


def _read_json_from_reports(reports: Path, filename: str) -> dict[str, Any] | None:
    direct = reports / filename
    if direct.exists():
        return _read_json(direct)
    for path in sorted(reports.glob(f"**/{filename}")) if reports.exists() else []:
        return _read_json(path)
    return None
