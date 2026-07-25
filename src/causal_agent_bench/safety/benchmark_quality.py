"""Static benchmark quality audit for no-run validation lanes."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from causal_agent_bench.safety.common import section_markdown, write_dual_report

Issue = dict[str, Any]

HIGH_RISK_INTERVENTIONS = frozenset(
    {
        "ambiguous_instruction",
        "memory_corruption",
        "observation_conflict",
        "distractor_evidence",
        "long_horizon_dependency",
        "web_conflicting_page",
        "web_hidden_evidence",
        "premature_success_signal",
    }
)
MAIN_SPLIT_NAMES = frozenset({"main", "test", "heldout", "heldout_templates"})
ITERATION_SPLIT_NAMES = frozenset({"train", "dev", "pilot", "pilot_20", "pilot_100", "validation"})


def build_benchmark_quality_report(
    repo_root: str | Path,
    *,
    benchmark_dir: str | Path | None = None,
    output_dir: str | Path = "reports/benchmark_quality",
) -> dict[str, Any]:
    """Write a static benchmark quality report.

    The audit reads JSON/JSONL/config/report files only. It does not construct
    environments, instantiate agents, start runs, or call providers.
    """

    root = Path(repo_root).resolve()
    out = Path(output_dir)
    if not out.is_absolute():
        out = root / out

    dataset_dirs = [Path(benchmark_dir)] if benchmark_dir else discover_benchmark_dirs(root)
    datasets = [audit_benchmark_dataset(path, repo_root=root) for path in dataset_dirs]
    issues = [issue for dataset in datasets for issue in dataset["issues"]]
    summary = _summary(datasets, issues)
    summary["raw_issue_count"] = len(issues)
    root_causes = _cluster_quality_issues(issues)
    summary["cluster_count"] = len(root_causes)
    summary["suppressed_symptom_count"] = max(0, len(issues) - len(root_causes))
    summary["blockers"] = sum(1 for issue in issues if issue.get("severity") == "blocker")
    summary["warnings"] = sum(1 for issue in issues if issue.get("severity") == "warning")
    summary["informational"] = sum(1 for issue in issues if issue.get("severity") == "informational")
    classification_counts: dict[str, int] = {}
    for row in root_causes:
        classification_counts[row["cluster_classification"]] = classification_counts.get(row["cluster_classification"], 0) + 1
    summary["classification_counts"] = classification_counts
    verdicts = {
        "benchmark_quality_ready_for_provider_pilot": any(
            dataset["verdicts"]["ready_for_provider_pilot"] for dataset in datasets
        ),
        "benchmark_quality_ready_for_main_claims": any(
            dataset["verdicts"]["ready_for_main_claims"] for dataset in datasets
        ),
        "benchmark_quality_ready_for_release": bool(datasets)
        and any(dataset["verdicts"]["ready_for_release"] for dataset in datasets),
    }
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": (
            "Static benchmark/data/config inspection only; no agents, providers, "
            "local models, or benchmark runs are invoked."
        ),
        "dataset_count": len(datasets),
        "summary": summary,
        "verdicts": verdicts,
        "datasets": datasets,
        "root_causes": root_causes,
        "root_cause_summary": root_causes,
        "top_clusters": root_causes[:20],
        "classification_counts": classification_counts,
        "issues": issues,
        "raw_finding_count": len(issues),
        "cluster_count": len(root_causes),
    }
    md = benchmark_quality_markdown(payload)
    md_path, json_path = write_dual_report(
        stem="benchmark_quality_report",
        payload=payload,
        markdown=md,
        output_dir=out,
    )
    payload["report_paths"] = {"markdown": str(md_path), "json": str(json_path)}
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def discover_benchmark_dirs(repo_root: str | Path) -> list[Path]:
    root = Path(repo_root)
    candidates: list[Path] = []
    for base in (root / "data/frozen", root / "data/processed", root / "data/sample"):
        if not base.exists():
            continue
        if (base / "instances.jsonl").exists():
            candidates.append(base)
        for path in sorted(base.glob("*")):
            if path.is_dir() and (path / "instances.jsonl").exists():
                candidates.append(path)
    seen: set[Path] = set()
    out: list[Path] = []
    for path in candidates:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            out.append(path)
    return out


def audit_benchmark_dataset(dataset_dir: str | Path, *, repo_root: str | Path | None = None) -> dict[str, Any]:
    root = Path(repo_root).resolve() if repo_root else Path.cwd().resolve()
    dataset = Path(dataset_dir)
    if not dataset.is_absolute():
        dataset = root / dataset
    rel = _rel(dataset, root)
    issues: list[Issue] = []

    base_tasks, base_errors = _read_jsonl(dataset / "base_tasks.jsonl")
    interventions, intervention_errors = _read_jsonl(dataset / "interventions.jsonl")
    instances, instance_errors = _read_jsonl(dataset / "instances.jsonl")
    for source, errors in (
        ("base_tasks.jsonl", base_errors),
        ("interventions.jsonl", intervention_errors),
        ("instances.jsonl", instance_errors),
    ):
        for error in errors:
            _issue(issues, "blocker", "invalid_jsonl", f"{source}: {error}", rel)

    if not (dataset / "instances.jsonl").exists():
        _issue(issues, "blocker", "missing_instances_file", "instances.jsonl is missing", rel)
    if not base_tasks:
        _issue(issues, "blocker", "missing_base_tasks", "No base tasks were found", rel)
    if not instances:
        _issue(issues, "blocker", "missing_instances", "No benchmark instances were found", rel)

    task_ids = [_task_id(task) for task in base_tasks]
    instance_ids = [_instance_id(instance) for instance in instances]
    duplicate_task_ids = _duplicates([value for value in task_ids if value])
    duplicate_instance_ids = _duplicates([value for value in instance_ids if value])
    near_duplicate_instance_ids = _near_duplicate_ids([value for value in instance_ids if value])

    for index, task_id in enumerate(task_ids):
        if not task_id:
            _issue(issues, "blocker", "missing_task_id", f"Base task row {index + 1} has no task_id", rel)
    for index, instance in enumerate(instances):
        if not _instance_id(instance):
            _issue(
                issues,
                "blocker",
                "missing_instance_id",
                f"Instance row {index + 1} has no instance_id",
                rel,
            )
        if not _instance_task_id(instance):
            _issue(
                issues,
                "blocker",
                "missing_instance_task_id",
                f"Instance {_instance_id(instance) or index + 1} has no linked task id",
                rel,
            )
    for task_id in duplicate_task_ids:
        _issue(issues, "blocker", "duplicate_task_id", f"Duplicate task_id: {task_id}", rel)
    for instance_id in duplicate_instance_ids:
        _issue(issues, "blocker", "duplicate_instance_id", f"Duplicate instance_id: {instance_id}", rel)
    for group in near_duplicate_instance_ids:
        _issue(
            issues,
            "warning",
            "near_duplicate_instance_ids",
            f"Near-duplicate instance ids: {', '.join(group)}",
            rel,
        )

    task_id_set = {value for value in task_ids if value}
    clean_by_task: dict[str, list[dict[str, Any]]] = defaultdict(list)
    intervention_by_task: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for instance in instances:
        base_id = _instance_task_id(instance)
        if base_id and base_id not in task_id_set and base_tasks:
            _issue(
                issues,
                "blocker",
                "invalid_pair_reference",
                f"Instance {_instance_id(instance)} references missing base task {base_id}",
                rel,
            )
        if _condition(instance) == "clean":
            clean_by_task[base_id].append(instance)
        elif _condition(instance) == "intervention":
            intervention_by_task[base_id].append(instance)

    clean_intervention_pair_count = 0
    for base_id, intervention_instances in intervention_by_task.items():
        if not clean_by_task.get(base_id):
            _issue(
                issues,
                "blocker",
                "missing_clean_pair",
                f"Intervention task {base_id} has no clean pair",
                rel,
            )
        else:
            clean_intervention_pair_count += len(intervention_instances)
    for base_id, clean_instances in clean_by_task.items():
        if not intervention_by_task.get(base_id):
            _issue(
                issues,
                "warning",
                "missing_intervention_pair",
                f"Clean task {base_id} has no intervention pair",
                rel,
            )
        if len(clean_instances) > 1:
            _issue(
                issues,
                "warning",
                "multiple_clean_instances",
                f"Task {base_id} has {len(clean_instances)} clean instances",
                rel,
            )

    _check_expected_outputs(base_tasks, instances, issues, rel)
    _check_tool_specs(base_tasks, instances, issues, rel)
    _check_gold_labels(base_tasks, issues, rel)
    _check_metadata(base_tasks, instances, interventions, issues, rel)
    _check_high_risk_interventions(interventions, instances, issues, rel)
    split_summary = _check_splits(dataset, instances, base_tasks, issues, rel)
    generation_quality = _check_generation_quality(dataset, issues, rel)

    distributions = {
        "task_category_distribution": dict(sorted(Counter(_category(task) for task in base_tasks).items())),
        "intervention_type_distribution": dict(
            sorted(Counter(_intervention_type(item) for item in interventions or _intervention_instances(instances)).items())
        ),
        "difficulty_distribution": dict(sorted(Counter(_difficulty(task) for task in base_tasks).items())),
        "tool_coverage_distribution": dict(
            sorted(Counter(",".join(sorted(_available_tools(item))) for item in base_tasks).items())
        ),
    }
    blockers = [issue for issue in issues if issue["severity"] == "blocker"]
    has_heldout = bool(split_summary.get("heldout_present") and split_summary.get("heldout_size", 0) > 0)
    has_main_candidate = _is_main_candidate(dataset)
    sufficient_main_metadata = (
        has_heldout
        and split_summary.get("split_metadata_present", False)
        and not split_summary.get("leakage_risks")
        and clean_intervention_pair_count > 0
    )
    ready_for_provider_pilot = not blockers and len(instances) > 0 and clean_intervention_pair_count > 0
    ready_for_main_claims = ready_for_provider_pilot and sufficient_main_metadata
    ready_for_release = ready_for_main_claims and not any(
        issue["severity"] == "warning"
        and issue["id"]
        in {
            "missing_tool_specs",
            "missing_expected_output",
            "quality_report_warning",
            "high_risk_intervention",
        }
        for issue in issues
    )
    if has_main_candidate and not sufficient_main_metadata:
        _issue(
            issues,
            "blocker",
            "main_candidate_not_ready",
            "Dataset name/config suggests a main candidate but heldout/split/pairing metadata is insufficient",
            rel,
        )
        ready_for_main_claims = False
        ready_for_release = False
    scores = _score_dataset(
        task_count=len(base_tasks),
        instance_count=len(instances),
        intervention_count=len(interventions),
        clean_intervention_pair_count=clean_intervention_pair_count,
        intervention_instance_count=sum(1 for item in instances if _condition(item) == "intervention"),
        distributions=distributions,
        split_summary=split_summary,
        generation_quality=generation_quality,
        issues=issues,
    )
    return {
        "dataset_dir": str(dataset),
        "dataset_relpath": rel,
        "task_count": len(base_tasks),
        "instance_count": len(instances),
        "clean_instance_count": sum(1 for item in instances if _condition(item) == "clean"),
        "intervention_instance_count": sum(1 for item in instances if _condition(item) == "intervention"),
        "clean_intervention_pair_count": clean_intervention_pair_count,
        "intervention_count": len(interventions),
        "distributions": distributions,
        "duplicate_task_ids": duplicate_task_ids,
        "duplicate_instance_ids": duplicate_instance_ids,
        "near_duplicate_instance_id_groups": near_duplicate_instance_ids,
        "split_summary": split_summary,
        "generation_quality": generation_quality,
        "issues": issues,
        "issue_counts": dict(Counter(issue["severity"] for issue in issues)),
        "scores": scores,
        "top_blockers": _top_issues(issues, "blocker"),
        "top_warnings": _top_issues(issues, "warning"),
        "recommended_fixes": _recommended_fixes(issues),
        "verdicts": {
            "ready_for_provider_pilot": ready_for_provider_pilot,
            "ready_for_main_claims": ready_for_main_claims,
            "ready_for_release": ready_for_release,
            "blocked_from_main_benchmark_ready_label": not ready_for_main_claims,
        },
    }


def _main_benchmark_gate_lines(payload: dict[str, Any]) -> list[str]:
    """Separate tiny-provider-pilot gates from main-benchmark (main_200 / main_v0_1_500) blockers."""
    lines = [
        "",
        "## Main benchmark vs provider pilot",
        "",
        "Provider-pilot blockers (leakage, tiny caps) are independent of main-benchmark readiness labels below.",
        "",
    ]
    main_rows: list[str] = []
    pilot_ok: list[str] = []
    for dataset in payload.get("datasets") or []:
        rel = str(dataset.get("dataset_relpath") or "")
        issues = dataset.get("issues") or []
        main_blockers = [i for i in issues if i.get("id") == "main_candidate_not_ready"]
        split = dataset.get("split_summary") or {}
        if main_blockers:
            risks = split.get("leakage_risks") or []
            main_rows.append(
                f"- `{rel}`: **main_candidate_not_ready** — heldout={split.get('has_heldout')}, "
                f"split_metadata={split.get('split_metadata_present')}, "
                f"protected_split_risks={len(risks)}"
            )
        elif dataset.get("verdicts", {}).get("ready_for_provider_pilot"):
            pilot_ok.append(rel)
    if main_rows:
        lines.extend(["### Main benchmark blockers", "", *main_rows])
    else:
        lines.extend(["### Main benchmark blockers", "", "- (none flagged as main_candidate_not_ready)"])
    lines.extend(
        [
            "",
            "### Provider-pilot static quality (no leakage substitute)",
            "",
            f"- Datasets with static `ready_for_provider_pilot` quality verdict: {len(pilot_ok)}",
            "- Binding provider gate still requires leakage repair + advisor approval (see provider_pilot_preflight).",
            "",
        ]
    )
    return lines


def benchmark_quality_markdown(payload: dict[str, Any]) -> str:
    verdicts = payload["verdicts"]
    summary = payload["summary"]
    lines = [
        "# Benchmark Quality Report",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        payload["scope"],
        "",
        section_markdown(
            "Verdicts",
            [
                f"- Ready for provider pilot quality gate: `{verdicts['benchmark_quality_ready_for_provider_pilot']}`",
                f"- Ready for main empirical claims: `{verdicts['benchmark_quality_ready_for_main_claims']}`",
                f"- Ready for release quality label: `{verdicts['benchmark_quality_ready_for_release']}`",
                "",
                "These verdicts are conservative static checks. They are not evidence of LLM behavior.",
            ],
        ),
        section_markdown(
            "Summary",
            [
                f"- Datasets inspected: {payload['dataset_count']}",
                f"- Tasks: {summary['total_tasks']}",
                f"- Instances: {summary['total_instances']}",
                f"- Clean/intervention pairs: {summary['total_clean_intervention_pairs']}",
                f"- Overall quality score: {summary['scores']['overall_quality_score']}",
                f"- Provider-pilot readiness score: {summary['scores']['provider_pilot_readiness_score']}",
                f"- Main benchmark readiness score: {summary['scores']['main_benchmark_readiness_score']}",
                f"- Release readiness score: {summary['scores']['release_readiness_score']}",
                f"- Blockers: {summary['issue_counts'].get('blocker', 0)}",
                f"- Warnings: {summary['issue_counts'].get('warning', 0)}",
                f"- Informational: {summary['issue_counts'].get('informational', 0)}",
                f"- Raw issues: {summary.get('raw_issue_count', 0)}",
                f"- Root-cause clusters: {summary.get('cluster_count', 0)}",
                f"- Suppressed/deduplicated symptoms: {summary.get('suppressed_symptom_count', 0)}",
            ],
        ),
        *_main_benchmark_gate_lines(payload),
        "## Top Root Causes",
        "",
    ]
    top_clusters = payload.get("top_clusters") or []
    if not top_clusters:
        lines.append("- (none)")
    for row in top_clusters[:15]:
        lines.append(
            f"- rank {row['rank']} `{row['root_cause_id']}` [{row['severity']}] "
            f"{row['root_cause_title']} ({row['symptom_count']} symptoms; "
            f"gate=`{row['readiness_gate']}`)"
        )
    lines.extend(["", "## Datasets", ""])
    for dataset in payload["datasets"]:
        lines.extend(
            [
                f"### `{dataset['dataset_relpath']}`",
                "",
                f"- Tasks: {dataset['task_count']}",
                f"- Instances: {dataset['instance_count']}",
                f"- Pairs: {dataset['clean_intervention_pair_count']}",
                f"- Provider-pilot quality ready: `{dataset['verdicts']['ready_for_provider_pilot']}`",
                f"- Main-claims ready: `{dataset['verdicts']['ready_for_main_claims']}`",
                f"- Release quality ready: `{dataset['verdicts']['ready_for_release']}`",
                f"- Heldout present: `{dataset['split_summary'].get('heldout_present', False)}`",
                f"- Scores: overall `{dataset['scores']['overall_quality_score']}`, provider `{dataset['scores']['provider_pilot_readiness_score']}`, main `{dataset['scores']['main_benchmark_readiness_score']}`, release `{dataset['scores']['release_readiness_score']}`",
                "",
                "| Category | Score | Weight | Notes |",
                "|---|---:|---:|---|",
                *[
                    f"| {row['category']} | {row['score']} | {row['weight']} | {row['notes']} |"
                    for row in dataset["scores"]["breakdown"]
                ],
                "",
            ]
        )
        if dataset["top_blockers"]:
            lines.append("**Top blockers:**")
            lines.extend(f"- `{issue['id']}`: {issue['message']}" for issue in dataset["top_blockers"])
            lines.append("")
        if dataset["recommended_fixes"]:
            lines.append("**Recommended fixes:**")
            lines.extend(f"- {fix}" for fix in dataset["recommended_fixes"][:8])
            lines.append("")
        for severity in ("blocker", "warning", "informational"):
            filtered = [issue for issue in dataset["issues"] if issue["severity"] == severity]
            if not filtered:
                continue
            lines.append(f"**{severity.title()}s:**")
            for issue in filtered[:20]:
                lines.append(f"- `{issue['id']}`: {issue['message']}")
            if len(filtered) > 20:
                lines.append(f"- ... {len(filtered) - 20} more")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _cluster_quality_issues(issues: list[Issue]) -> list[dict[str, Any]]:
    """Group raw quality issues by (id, dataset, severity) so root causes are visible.

    Returns a deterministic, ranked list of root-cause clusters that the
    report-quality checker can use to mark this report as clustered rather
    than a raw flood.
    """

    if not issues:
        return []
    groups: dict[tuple[str, str, str], list[Issue]] = defaultdict(list)
    severity_rank = {"blocker": 0, "warning": 1, "informational": 2, "needs_review": 3}
    for issue in issues:
        key = (
            str(issue.get("id") or "unknown"),
            str(issue.get("dataset") or ""),
            str(issue.get("severity") or "informational"),
        )
        groups[key].append(issue)
    rows: list[dict[str, Any]] = []
    for (issue_id, dataset, severity), members in groups.items():
        sample_messages = [str(m.get("message")) for m in members[:3] if m.get("message")]
        rows.append(
            {
                "root_cause_id": f"bq_root_{issue_id}__{re.sub(r'[^a-zA-Z0-9]+', '_', dataset)}__{severity}"[:120],
                "root_cause_title": f"{issue_id} in {dataset or '(root)'}",
                "cluster_classification": issue_id,
                "severity": severity,
                "leakage_risk": severity if severity in {"blocker", "warning"} else "informational",
                "dataset": dataset,
                "symptom_count": len(members),
                "representative_messages": sample_messages,
                "readiness_gate": (
                    "must_fix_before_provider_pilot" if severity == "blocker"
                    else "must_fix_before_main_benchmark" if severity == "warning"
                    else "nice_to_have"
                ),
            }
        )
    rows.sort(key=lambda row: (severity_rank.get(row["severity"], 99), -row["symptom_count"], row["root_cause_id"]))
    for rank, row in enumerate(rows, start=1):
        row["rank"] = rank
    return rows


def _summary(datasets: list[dict[str, Any]], issues: list[Issue]) -> dict[str, Any]:
    score_keys = (
        "overall_quality_score",
        "provider_pilot_readiness_score",
        "main_benchmark_readiness_score",
        "release_readiness_score",
    )
    scores = {
        key: max((dataset.get("scores", {}).get(key, 0) for dataset in datasets), default=0)
        for key in score_keys
    }
    return {
        "total_tasks": sum(dataset["task_count"] for dataset in datasets),
        "total_instances": sum(dataset["instance_count"] for dataset in datasets),
        "total_clean_intervention_pairs": sum(
            dataset["clean_intervention_pair_count"] for dataset in datasets
        ),
        "issue_counts": dict(Counter(issue["severity"] for issue in issues)),
        "scores": scores,
        "dataset_issue_counts": {
            dataset["dataset_relpath"]: dataset["issue_counts"] for dataset in datasets
        },
    }


def _score_dataset(
    *,
    task_count: int,
    instance_count: int,
    intervention_count: int,
    clean_intervention_pair_count: int,
    intervention_instance_count: int,
    distributions: dict[str, dict[str, int]],
    split_summary: dict[str, Any],
    generation_quality: dict[str, Any],
    issues: list[Issue],
) -> dict[str, Any]:
    issue_counts = Counter(issue["id"] for issue in issues)
    blockers = [issue for issue in issues if issue["severity"] == "blocker"]
    warnings = [issue for issue in issues if issue["severity"] == "warning"]
    pair_score = 100 if intervention_instance_count == 0 else round(100 * clean_intervention_pair_count / max(intervention_instance_count, 1))
    if task_count and intervention_instance_count == 0:
        pair_score = 30
    coverage_score = _coverage_score(distributions.get("intervention_type_distribution", {}), expected_min=3)
    category_score = _balance_score(distributions.get("task_category_distribution", {}))
    difficulty_score = _balance_score(distributions.get("difficulty_distribution", {}))
    tool_score = _coverage_score(distributions.get("tool_coverage_distribution", {}), expected_min=2)
    expected_output_score = max(0, 100 - issue_counts.get("missing_expected_output", 0) * 35)
    duplicate_score = 0 if (issue_counts.get("duplicate_task_id") or issue_counts.get("duplicate_instance_id")) else 100
    heldout_score = 100 if split_summary.get("heldout_present") and split_summary.get("heldout_size", 0) > 0 else 0
    generation_score = max(0, 100 - len(generation_quality.get("quality_warnings") or []) * 8 - issue_counts.get("quality_report_warning", 0) * 6)
    high_risk_score = max(0, 100 - issue_counts.get("high_risk_intervention", 0) * 8)
    metadata_score = max(
        0,
        100
        - issue_counts.get("missing_scenario_metadata", 0) * 12
        - issue_counts.get("missing_intervention_type", 0) * 12
        - issue_counts.get("missing_changed_factor", 0) * 10
        - issue_counts.get("missing_condition_metadata", 0) * 10,
    )
    leakage_score = 0 if split_summary.get("leakage_risks") else 100
    breakdown = [
        _score_row("pair_completeness", pair_score, 16, f"{clean_intervention_pair_count}/{intervention_instance_count} intervention instances paired"),
        _score_row("intervention_coverage", coverage_score, 8, f"{len(distributions.get('intervention_type_distribution', {}))} intervention types"),
        _score_row("task_category_balance", category_score, 6, f"{len(distributions.get('task_category_distribution', {}))} categories"),
        _score_row("difficulty_balance", difficulty_score, 6, f"{len(distributions.get('difficulty_distribution', {}))} difficulty levels"),
        _score_row("tool_coverage", tool_score, 6, f"{len(distributions.get('tool_coverage_distribution', {}))} tool patterns"),
        _score_row("expected_outputs", expected_output_score, 14, f"{issue_counts.get('missing_expected_output', 0)} missing expected outputs"),
        _score_row("duplicate_ids", duplicate_score, 14, f"{issue_counts.get('duplicate_task_id', 0) + issue_counts.get('duplicate_instance_id', 0)} duplicate-id issues"),
        _score_row("heldout_split_status", heldout_score, 12, f"heldout_present={bool(split_summary.get('heldout_present'))}"),
        _score_row("generation_warnings", generation_score, 5, f"{len(generation_quality.get('quality_warnings') or [])} generation warnings"),
        _score_row("high_risk_interventions", high_risk_score, 4, f"{issue_counts.get('high_risk_intervention', 0)} high-risk interventions"),
        _score_row("metadata_completeness", metadata_score, 5, f"{issue_counts.get('missing_scenario_metadata', 0)} missing scenario metadata"),
        _score_row("dataset_leakage_risk", leakage_score, 4, f"{len(split_summary.get('leakage_risks') or [])} leakage risks"),
    ]
    overall = _weighted_score(breakdown)
    provider = overall
    if blockers:
        provider = min(provider, 49)
    if issue_counts.get("missing_expected_output"):
        provider = min(provider, 45)
    if issue_counts.get("missing_tool_specs"):
        provider = min(provider, 60)
    if instance_count == 0 or clean_intervention_pair_count == 0:
        provider = min(provider, 30)
    main = min(overall, provider)
    if heldout_score == 0 or split_summary.get("leakage_risks"):
        main = min(main, 49)
    release = min(overall, main)
    if warnings:
        release = min(release, max(55, overall - min(25, len(warnings) * 2)))
    return {
        "overall_quality_score": overall,
        "provider_pilot_readiness_score": int(provider),
        "main_benchmark_readiness_score": int(main),
        "release_readiness_score": int(release),
        "breakdown": breakdown,
        "scoring_note": "Static readiness score only; not empirical evidence and not claim support.",
    }


def _score_row(category: str, score: int | float, weight: int, notes: str) -> dict[str, Any]:
    return {"category": category, "score": int(max(0, min(100, round(score)))), "weight": weight, "notes": notes}


def _weighted_score(rows: list[dict[str, Any]]) -> int:
    total_weight = sum(int(row["weight"]) for row in rows)
    if total_weight <= 0:
        return 0
    return round(sum(row["score"] * row["weight"] for row in rows) / total_weight)


def _coverage_score(distribution: dict[str, int], *, expected_min: int) -> int:
    count = len([key for key, value in distribution.items() if key != "unknown" and value > 0])
    total = sum(distribution.values())
    if total == 0:
        return 0
    if total < expected_min:
        return 100
    return int(min(100, round(100 * count / expected_min)))


def _balance_score(distribution: dict[str, int]) -> int:
    values = [value for key, value in distribution.items() if key != "unknown" and value > 0]
    total = sum(values)
    if total == 0:
        return 0
    if total < 4 or len(values) <= 1:
        return 100
    ratio = min(values) / max(values)
    return round(60 + 40 * ratio)


def _top_issues(issues: list[Issue], severity: str) -> list[Issue]:
    return [issue for issue in issues if issue["severity"] == severity][:10]


def _recommended_fixes(issues: list[Issue]) -> list[str]:
    fixes_by_id = {
        "duplicate_task_id": "Rename or remove duplicate task IDs before any pilot.",
        "duplicate_instance_id": "Rename or remove duplicate instance IDs before any pilot.",
        "missing_expected_output": "Add expected_final_answer, expected output, or gold label metadata.",
        "missing_tool_specs": "Add explicit tool schemas or at least validated tool specs.",
        "missing_clean_pair": "Add a linked clean instance for every intervention instance.",
        "missing_intervention_pair": "Add at least one intervention variant for clean-only tasks.",
        "missing_split_metadata": "Add splits.json with train/dev/pilot/main or heldout metadata.",
        "missing_heldout_split": "Add a non-empty heldout/test split before main benchmark claims.",
        "split_leakage_risk": "Remove overlapping IDs between development and heldout/test splits.",
        "high_risk_intervention": "Queue high-risk interventions for manual/human isolation review.",
        "quality_report_warning": "Resolve generation quality warnings or document why they are acceptable.",
        "main_candidate_not_ready": "Do not call this dataset main-ready until split and pairing metadata are sufficient.",
    }
    seen: set[str] = set()
    out: list[str] = []
    for issue in issues:
        fix = fixes_by_id.get(issue["id"])
        if fix and fix not in seen:
            seen.add(fix)
            out.append(fix)
    return out


def _read_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    if not path.exists():
        return [], []
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"line {line_no}: {exc}")
            continue
        if isinstance(value, dict):
            rows.append(value)
        else:
            errors.append(f"line {line_no}: expected object, got {type(value).__name__}")
    return rows, errors


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def _issue(issues: list[Issue], severity: str, issue_id: str, message: str, dataset: str) -> None:
    issues.append({"severity": severity, "id": issue_id, "message": message, "dataset": dataset})


def _duplicates(values: list[str]) -> list[str]:
    counts = Counter(values)
    return sorted(value for value, count in counts.items() if count > 1)


def _near_duplicate_ids(values: list[str]) -> list[list[str]]:
    buckets: dict[str, set[str]] = defaultdict(set)
    for value in values:
        normalized = re.sub(r"[^a-z0-9]+", "", value.lower())
        buckets[normalized].add(value)
    return [sorted(group) for group in buckets.values() if len(group) > 1]


def _task_id(task: dict[str, Any]) -> str | None:
    value = task.get("task_id") or task.get("id")
    return str(value) if value else None


def _instance_id(instance: dict[str, Any]) -> str | None:
    value = instance.get("instance_id") or instance.get("id")
    return str(value) if value else None


def _instance_task_id(instance: dict[str, Any]) -> str | None:
    base_task = instance.get("base_task")
    if isinstance(base_task, dict) and base_task.get("task_id"):
        return str(base_task["task_id"])
    value = instance.get("base_task_id") or instance.get("task_id")
    return str(value) if value else None


def _condition(instance: dict[str, Any]) -> str:
    value = str(instance.get("condition") or "").lower()
    if value in {"clean", "intervention"}:
        return value
    instance_id = str(instance.get("instance_id") or "").lower()
    if instance_id.endswith(".clean") or ".clean." in instance_id:
        return "clean"
    if instance.get("intervention") or instance.get("intervention_id"):
        return "intervention"
    return "unknown"


def _category(task: dict[str, Any]) -> str:
    return str(task.get("domain") or task.get("category") or task.get("metadata", {}).get("category") or "unknown")


def _difficulty(task: dict[str, Any]) -> str:
    return str(task.get("difficulty") or task.get("metadata", {}).get("difficulty") or "unknown")


def _available_tools(item: dict[str, Any]) -> list[str]:
    value = item.get("available_tools") or item.get("tools") or []
    if isinstance(value, list):
        tools: list[str] = []
        for tool in value:
            if isinstance(tool, dict):
                tools.append(str(tool.get("name") or "unknown"))
            else:
                tools.append(str(tool))
        return tools
    return []


def _intervention_instances(instances: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [item.get("intervention") or item for item in instances if _condition(item) == "intervention"]


def _intervention_type(intervention: dict[str, Any]) -> str:
    value = (
        intervention.get("family")
        or intervention.get("type")
        or intervention.get("intervention_type")
        or intervention.get("metadata", {}).get("intervention_type")
    )
    return str(value or "unknown")


def _expected_output(task_or_instance: dict[str, Any]) -> Any:
    task = task_or_instance.get("base_task") if "base_task" in task_or_instance else task_or_instance
    if not isinstance(task, dict):
        task = task_or_instance
    goal = task.get("goal") if isinstance(task.get("goal"), dict) else {}
    return (
        goal.get("expected_final_answer")
        or task.get("expected_output")
        or task.get("expected_answer")
        or task.get("gold_label")
        or task.get("hidden_ground_truth")
    )


def _check_expected_outputs(
    base_tasks: list[dict[str, Any]],
    instances: list[dict[str, Any]],
    issues: list[Issue],
    rel: str,
) -> None:
    source = base_tasks if base_tasks else instances
    for item in source:
        if not _expected_output(item):
            label = _task_id(item) or _instance_id(item) or "unknown"
            _issue(issues, "blocker", "missing_expected_output", f"{label} has no expected output/gold label", rel)


def _check_tool_specs(
    base_tasks: list[dict[str, Any]],
    instances: list[dict[str, Any]],
    issues: list[Issue],
    rel: str,
) -> None:
    # The benchmark ships its tool schemas as the code-level simulated registry
    # (the repo-default tool environment), so a task that names registry tools
    # already has a resolvable schema even without an inline spec block. Lazy
    # import avoids a circular dependency with tool_schema_validation.
    from causal_agent_bench.safety.tool_schema_validation import load_code_registry_tool_specs

    registry_names = {str(spec.get("name")) for spec in load_code_registry_tool_specs()}
    source = base_tasks if base_tasks else instances
    for item in source:
        tools = _available_tools(item)
        label = _task_id(item) or _instance_id(item) or "unknown"
        if not tools:
            _issue(issues, "blocker", "missing_tool_specs", f"{label} has no available tool list", rel)
            continue
        explicit_specs = item.get("tool_specs") or item.get("tools")
        has_inline_specs = bool(explicit_specs) and (
            not isinstance(explicit_specs, list)
            or all(isinstance(tool, dict) and tool.get("name") for tool in explicit_specs)
        )
        covered_by_registry = bool(registry_names) and all(tool in registry_names for tool in tools)
        if not has_inline_specs and not covered_by_registry:
            unresolved = sorted(tool for tool in tools if tool not in registry_names)
            detail = f" ({', '.join(unresolved)} not in code registry)" if unresolved else ""
            _issue(
                issues,
                "warning",
                "missing_tool_specs",
                f"{label} has tool names but no explicit tool spec schema{detail}",
                rel,
            )


def _check_gold_labels(base_tasks: list[dict[str, Any]], issues: list[Issue], rel: str) -> None:
    for task in base_tasks:
        if task.get("metadata", {}).get("requires_gold_label") and not _expected_output(task):
            _issue(
                issues,
                "blocker",
                "missing_gold_label",
                f"{_task_id(task) or 'unknown'} requires a gold label but none is present",
                rel,
            )


def _check_metadata(
    base_tasks: list[dict[str, Any]],
    instances: list[dict[str, Any]],
    interventions: list[dict[str, Any]],
    issues: list[Issue],
    rel: str,
) -> None:
    for task in base_tasks:
        label = _task_id(task) or "unknown"
        missing: list[str] = []
        if not _category(task) or _category(task) == "unknown":
            missing.append("domain/category")
        if not _difficulty(task) or _difficulty(task) == "unknown":
            missing.append("difficulty")
        goal = task.get("goal") if isinstance(task.get("goal"), dict) else {}
        if not (goal.get("user_instruction") or task.get("user_instruction")):
            missing.append("scenario/user_instruction")
        if missing:
            _issue(
                issues,
                "warning",
                "missing_scenario_metadata",
                f"{label} missing metadata fields: {', '.join(missing)}",
                rel,
            )
    for intervention in interventions:
        label = str(intervention.get("intervention_id") or "unknown")
        if not _intervention_type(intervention) or _intervention_type(intervention) == "unknown":
            _issue(issues, "warning", "missing_intervention_type", f"{label} has no intervention type", rel)
        if not intervention.get("changed_factor"):
            _issue(issues, "warning", "missing_changed_factor", f"{label} has no changed_factor", rel)
    for instance in instances:
        if _condition(instance) == "unknown":
            _issue(
                issues,
                "warning",
                "missing_condition_metadata",
                f"{_instance_id(instance) or 'unknown'} has no clean/intervention condition",
                rel,
            )


def _check_high_risk_interventions(
    interventions: list[dict[str, Any]],
    instances: list[dict[str, Any]],
    issues: list[Issue],
    rel: str,
) -> None:
    source = interventions or _intervention_instances(instances)
    for intervention in source:
        family = _intervention_type(intervention)
        risk = str(intervention.get("intervention_validity_risk") or intervention.get("severity") or "").lower()
        if family in HIGH_RISK_INTERVENTIONS or risk == "high":
            _issue(
                issues,
                "warning",
                "high_risk_intervention",
                f"{intervention.get('intervention_id') or family} needs human review before causal-validity claims",
                rel,
            )


def _check_generation_quality(dataset: Path, issues: list[Issue], rel: str) -> dict[str, Any]:
    generation_report = _read_json(dataset / "generation_report.json") or {}
    warnings = generation_report.get("quality_warnings") or []
    if warnings:
        for warning in warnings[:20]:
            _issue(issues, "warning", "quality_report_warning", str(warning), rel)
    quality_report = dataset / "quality_report.md"
    quality_report_present = quality_report.exists()
    if quality_report_present:
        text = quality_report.read_text(encoding="utf-8", errors="replace").lower()
        if "warning" in text or "failed" in text:
            _issue(
                issues,
                "informational",
                "quality_report_mentions_warnings",
                "quality_report.md contains warning/failed language; review details",
                rel,
            )
    return {
        "generation_report_present": bool(generation_report),
        "quality_report_present": quality_report_present,
        "quality_warnings": warnings,
        "quality_passed": generation_report.get("quality_passed"),
    }


def _check_splits(
    dataset: Path,
    instances: list[dict[str, Any]],
    base_tasks: list[dict[str, Any]],
    issues: list[Issue],
    rel: str,
) -> dict[str, Any]:
    split_path = dataset / "splits.json"
    splits_payload = _read_json(split_path)
    split_sizes: dict[str, dict[str, int]] = {}
    leakage_risks: list[str] = []
    if not splits_payload:
        _issue(
            issues,
            "warning",
            "missing_split_metadata",
            "splits.json is missing; dataset cannot support main-claims readiness",
            rel,
        )
        return {
            "splits_present": False,
            "heldout_present": False,
            "heldout_size": 0,
            "split_sizes": split_sizes,
            "split_metadata_present": False,
            "leakage_risks": leakage_risks,
        }
    splits = splits_payload.get("splits") if isinstance(splits_payload.get("splits"), dict) else splits_payload
    if not isinstance(splits, dict):
        _issue(issues, "blocker", "invalid_split_metadata", "splits.json is not a split mapping", rel)
        splits = {}
    ids_by_split: dict[str, set[str]] = {}
    for name, value in splits.items():
        if isinstance(value, dict):
            instance_ids = set(map(str, value.get("instance_ids") or []))
            task_ids = set(map(str, value.get("base_task_ids") or value.get("task_ids") or []))
        elif isinstance(value, list):
            instance_ids = set(map(str, value))
            task_ids = set()
        else:
            instance_ids = set()
            task_ids = set()
        split_sizes[str(name)] = {"instances": len(instance_ids), "tasks": len(task_ids)}
        ids_by_split[str(name)] = instance_ids or task_ids
    heldout_names = [name for name in split_sizes if "heldout" in name or name == "test"]
    heldout_size = sum(split_sizes[name]["instances"] or split_sizes[name]["tasks"] for name in heldout_names)
    if heldout_size == 0:
        _issue(
            issues,
            "warning",
            "missing_heldout_split",
            "No non-empty heldout/test split detected; main claims remain blocked",
            rel,
        )
    main_sets = [
        (name, values)
        for name, values in ids_by_split.items()
        if name in MAIN_SPLIT_NAMES or "heldout" in name or name == "test"
    ]
    iter_sets = [
        (name, values)
        for name, values in ids_by_split.items()
        if name in ITERATION_SPLIT_NAMES or name.startswith("pilot")
    ]
    for main_name, main_ids in main_sets:
        for iter_name, iter_ids in iter_sets:
            overlap = main_ids & iter_ids
            if overlap:
                risk = f"{main_name} overlaps {iter_name} on {len(overlap)} ids"
                leakage_risks.append(risk)
                _issue(issues, "warning", "split_leakage_risk", risk, rel)
    if not any(name in splits for name in ("dev", "pilot", "pilot_20", "validation", "train")):
        _issue(
            issues,
            "warning",
            "missing_iteration_split",
            "No train/dev/pilot/validation split metadata detected",
            rel,
        )
    return {
        "splits_present": True,
        "heldout_present": heldout_size > 0,
        "heldout_size": heldout_size,
        "split_sizes": split_sizes,
        "split_metadata_present": True,
        "leakage_risks": leakage_risks,
        "declared_policy": splits_payload.get("split_policy"),
        "benchmark_version": splits_payload.get("benchmark_version"),
        "base_task_total": len(base_tasks),
        "instance_total": len(instances),
    }


def _is_main_candidate(dataset: Path) -> bool:
    name = dataset.name.lower()
    return "main" in name or "500" in name or "candidate" in name


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)
