"""Static clean/intervention pair isolation audit."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from causal_agent_bench.safety.benchmark_quality import (
    _condition,
    _instance_id,
    _instance_task_id,
    _read_jsonl,
)
from causal_agent_bench.safety.common import section_markdown, write_dual_report

TOOL_INTERVENTIONS = frozenset(
    {
        "tool_removal",
        "tool_failure",
        "tool_corruption",
        "irrelevant_tools",
        "web_broken_link",
        "web_stale_page",
        "web_irrelevant_search_result",
    }
)
MEMORY_INTERVENTIONS = frozenset({"memory_corruption"})
OBSERVATION_INTERVENTIONS = frozenset(
    {
        "observation_conflict",
        "distractor_evidence",
        "premature_success_signal",
        "web_conflicting_page",
        "web_hidden_evidence",
    }
)
# long_horizon_dependency is delivered via tool_output_patch (a dependency marker
# on an earlier observation), NOT by editing the user instruction — see the
# generator's INTERVENTION_FAMILY_AUDIT_GUIDE (patch_group=tool_output_patch).
INSTRUCTION_INTERVENTIONS = frozenset({"ambiguous_instruction"})
FIELD_WHITELIST_BY_INTERVENTION = {
    "tool_removal": {"available_tools", "tool_availability_patch", "patch_details"},
    "irrelevant_tools": {"available_tools", "tool_availability_patch", "patch_details"},
    "tool_failure": {"tool_output_patch", "observations", "patch_details"},
    "tool_corruption": {"tool_output_patch", "observations", "patch_details"},
    "web_broken_link": {"tool_output_patch", "observations", "patch_details"},
    "web_stale_page": {"tool_output_patch", "observations", "patch_details"},
    "web_irrelevant_search_result": {"tool_output_patch", "observations", "patch_details"},
    "memory_corruption": {"initial_memory", "memory_patch", "patch_details"},
    "observation_conflict": {"tool_output_patch", "observations", "patch_details"},
    "distractor_evidence": {"tool_output_patch", "observations", "patch_details"},
    "premature_success_signal": {"tool_output_patch", "observations", "patch_details", "metadata"},
    "web_conflicting_page": {"tool_output_patch", "observations", "patch_details"},
    "web_hidden_evidence": {"tool_output_patch", "observations", "patch_details"},
    "ambiguous_instruction": {"instruction_patch", "user_instruction", "patch_details"},
    "long_horizon_dependency": {"tool_output_patch", "observations", "patch_details"},
    "argument_perturbation": {"tool_arguments", "argument_schema", "patch_details"},
    "stopping_recovery": {"tool_output_patch", "observations", "patch_details", "metadata"},
}
DEFAULT_EXPECTED_UNCHANGED_FIELDS = {
    "base_task_id",
    "domain",
    "difficulty",
    "hidden_ground_truth",
    "success_criteria",
}


def built_in_intervention_taxonomy() -> dict[str, dict[str, Any]]:
    taxonomy: dict[str, dict[str, Any]] = {}
    for intervention_type, allowed in FIELD_WHITELIST_BY_INTERVENTION.items():
        expected_unchanged = set(DEFAULT_EXPECTED_UNCHANGED_FIELDS)
        if intervention_type not in TOOL_INTERVENTIONS:
            expected_unchanged.add("available_tools")
        if intervention_type not in MEMORY_INTERVENTIONS:
            expected_unchanged.add("initial_memory")
        if intervention_type not in INSTRUCTION_INTERVENTIONS:
            expected_unchanged.add("user_instruction")
        answer_preservation = "answer_preserving"
        if intervention_type in {"tool_removal", "tool_failure", "ambiguous_instruction"}:
            answer_preservation = "depends"
        return_row = {
            "intervention_type": intervention_type,
            "description": "Built-in conservative isolation policy.",
            "intended_causal_factor": _default_factor(intervention_type),
            "allowed_changed_fields": sorted(allowed),
            "allowed_change_categories": sorted(_categories_for_fields(allowed, intervention_type)),
            "expected_unchanged_fields": sorted(expected_unchanged - set(allowed)),
            "answer_preservation": answer_preservation,
            "requires_human_review": intervention_type in OBSERVATION_INTERVENTIONS
            or intervention_type in {"ambiguous_instruction", "long_horizon_dependency"},
            "severity_if_violated": "blocker",
        }
        taxonomy[intervention_type] = return_row
    return taxonomy


def load_intervention_taxonomy(
    taxonomy_path: str | Path | None = None,
    *,
    repo_root: str | Path | None = None,
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """Load machine-readable intervention taxonomy with conservative fallback."""

    root = Path(repo_root).resolve() if repo_root else Path.cwd().resolve()
    if taxonomy_path is None:
        candidate = root / "configs/intervention_taxonomy.yaml"
    else:
        candidate = Path(taxonomy_path)
        if not candidate.is_absolute():
            candidate = root / candidate
    if not candidate.exists():
        return built_in_intervention_taxonomy(), {
            "source": "built_in_defaults",
            "path": str(candidate),
            "loaded": False,
            "warning": "taxonomy file missing; using built-in conservative defaults",
        }
    try:
        raw = yaml.safe_load(candidate.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        return built_in_intervention_taxonomy(), {
            "source": "built_in_defaults",
            "path": str(candidate),
            "loaded": False,
            "warning": f"taxonomy file could not be parsed: {exc}",
        }
    rows = raw.get("interventions") if isinstance(raw, dict) else []
    if not isinstance(rows, list):
        rows = []
    taxonomy: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        intervention_type = str(row.get("intervention_type") or row.get("family") or "").strip()
        if not intervention_type:
            continue
        taxonomy[intervention_type] = {
            "intervention_type": intervention_type,
            "description": str(row.get("description") or ""),
            "intended_causal_factor": str(row.get("intended_causal_factor") or row.get("target_factor") or ""),
            "allowed_changed_fields": sorted(_as_string_set(row.get("allowed_changed_fields"))),
            "allowed_change_categories": sorted(_as_string_set(row.get("allowed_change_categories"))),
            "expected_unchanged_fields": sorted(_as_string_set(row.get("expected_unchanged_fields"))),
            "answer_preservation": str(row.get("answer_preservation") or "depends"),
            "requires_human_review": bool(row.get("requires_human_review", True)),
            "examples": row.get("examples") or [],
            "risks": row.get("risks") or [],
            "severity_if_violated": str(row.get("severity_if_violated") or "warning"),
        }
    if not taxonomy:
        return built_in_intervention_taxonomy(), {
            "source": "built_in_defaults",
            "path": str(candidate),
            "loaded": False,
            "warning": "taxonomy file had no usable interventions; using built-in conservative defaults",
        }
    return taxonomy, {"source": "file", "path": str(candidate), "loaded": True, "version": raw.get("version")}


def build_intervention_isolation_report(
    repo_root: str | Path,
    *,
    benchmark_dir: str | Path | None = None,
    instances_path: str | Path | None = None,
    output_dir: str | Path = "reports/intervention_isolation",
    taxonomy_path: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    out = Path(output_dir)
    if not out.is_absolute():
        out = root / out
    if instances_path:
        path = Path(instances_path)
        if not path.is_absolute():
            path = root / path
    else:
        base = Path(benchmark_dir) if benchmark_dir else root / "data/processed/pilot_v0_1"
        if not base.is_absolute():
            base = root / base
        path = base / "instances.jsonl"

    report = audit_intervention_isolation_instances(path, repo_root=root, taxonomy_path=taxonomy_path)
    md = intervention_isolation_markdown(report)
    md_path, json_path = write_dual_report(
        stem="intervention_isolation_report",
        payload=report,
        markdown=md,
        output_dir=out,
    )
    report["report_paths"] = {"markdown": str(md_path), "json": str(json_path)}
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def audit_intervention_isolation_instances(
    instances_path: str | Path,
    *,
    repo_root: str | Path | None = None,
    taxonomy_path: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(repo_root).resolve() if repo_root else Path.cwd().resolve()
    path = Path(instances_path)
    if not path.is_absolute():
        path = root / path
    instances, errors = _read_jsonl(path)
    taxonomy, taxonomy_meta = load_intervention_taxonomy(taxonomy_path, repo_root=root)
    pairs = _pair_rows(instances)
    records: list[dict[str, Any]] = []

    for base_task_id in sorted(pairs):
        clean_items = pairs[base_task_id].get("clean", [])
        intervention_items = pairs[base_task_id].get("intervention", [])
        if not clean_items:
            for intervention in intervention_items:
                records.append(_missing_clean_record(base_task_id, intervention, taxonomy))
            continue
        clean = clean_items[0]
        if not intervention_items:
            records.append(_missing_intervention_record(base_task_id, clean))
            continue
        for intervention in intervention_items:
            records.append(_compare_pair(clean, intervention, taxonomy))

    for error in errors:
        records.append(
            {
                "pair_id": "invalid_jsonl",
                "clean_id": None,
                "intervention_id": None,
                "intervention_type": "unknown",
                "isolation_status": "needs_review",
                "changed_fields": [],
                "intended_changed_fields": [],
                "unexpected_changed_fields": [],
                "changed_field_diff": {},
                "isolation_score": 0,
                "risk_score": 100,
                "severity": "blocker",
                "explanation": f"Could not parse instances file: {error}",
            }
        )

    counts = Counter(record["isolation_status"] for record in records)
    severity_counts = Counter(record["severity"] for record in records)
    intervention_type_scores = _intervention_type_scores(records)
    isolation_score = _overall_isolation_score(records)
    risk_ranked = sorted(records, key=lambda item: (-item.get("risk_score", 0), item["pair_id"]))
    root_causes = _cluster_isolation_records(records)
    classification_counts: dict[str, int] = {}
    for row in root_causes:
        key = row["cluster_classification"]
        classification_counts[key] = classification_counts.get(key, 0) + 1
    summary = {
        "total_pairs": len(records),
        "isolated_count": counts.get("isolated", 0),
        "likely_isolated_count": counts.get("likely_isolated", 0),
        "multi_factor_count": counts.get("multi_factor_change", 0),
        "needs_review_count": counts.get("needs_review", 0),
        "missing_clean_pair_count": counts.get("missing_clean_pair", 0),
        "missing_intervention_pair_count": counts.get("missing_intervention_pair", 0),
        "blockers": severity_counts.get("blocker", 0),
        "warnings": severity_counts.get("warning", 0),
        "isolation_score": isolation_score,
        "per_intervention_type_score": intervention_type_scores,
        "raw_issue_count": len(records),
        "cluster_count": len(root_causes),
        "suppressed_symptom_count": max(0, len(records) - len(root_causes)),
        "classification_counts": classification_counts,
    }
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": (
            "Static heuristic validation of clean/intervention pairs only. "
            "This is not human expert validation and does not prove causal validity."
        ),
        "instances_path": str(path),
        "taxonomy": taxonomy_meta,
        "summary": summary,
        "isolation_score": isolation_score,
        "per_intervention_type_score": intervention_type_scores,
        "top_riskiest_pairs": risk_ranked[:20],
        "recommended_manual_review": [
            record
            for record in risk_ranked
            if record["isolation_status"] in {"multi_factor_change", "needs_review", "missing_clean_pair"}
        ][:20],
        "root_causes": root_causes,
        "root_cause_summary": root_causes,
        "top_clusters": root_causes[:20],
        "classification_counts": classification_counts,
        "raw_finding_count": len(records),
        "cluster_count": len(root_causes),
        "pairs": records,
    }


def _cluster_isolation_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Cluster pair-level isolation records by (status, intervention_type, severity)."""

    if not records:
        return []
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    severity_rank = {"blocker": 0, "warning": 1, "informational": 2, "needs_review": 3}
    for record in records:
        key = (
            str(record.get("isolation_status") or "unknown"),
            str(record.get("intervention_type") or "unknown"),
            str(record.get("severity") or "informational"),
        )
        groups.setdefault(key, []).append(record)
    rows: list[dict[str, Any]] = []
    for (status, itype, sev), members in groups.items():
        rows.append(
            {
                "root_cause_id": f"iso_root_{status}__{itype}__{sev}",
                "root_cause_title": f"{status} for intervention `{itype}`",
                "cluster_classification": status,
                "intervention_type": itype,
                "severity": sev,
                "symptom_count": len(members),
                "representative_pair_ids": [str(m.get("pair_id", "")) for m in members[:5]],
                "readiness_gate": (
                    "must_fix_before_provider_pilot" if sev == "blocker"
                    else "must_fix_before_main_benchmark" if sev == "warning"
                    else "nice_to_have"
                ),
            }
        )
    rows.sort(key=lambda r: (severity_rank.get(r["severity"], 99), -r["symptom_count"], r["root_cause_id"]))
    for rank, row in enumerate(rows, start=1):
        row["rank"] = rank
    return rows


def intervention_isolation_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Intervention Isolation Audit",
        "",
        f"Generated: {report['generated_at']}",
        "",
        report["scope"],
        "",
        section_markdown(
            "Summary",
            [
                f"- Total pair records: {summary['total_pairs']}",
                f"- Isolated: {summary['isolated_count']}",
                f"- Likely isolated: {summary['likely_isolated_count']}",
                f"- Multi-factor changes: {summary['multi_factor_count']}",
                f"- Needs review: {summary['needs_review_count']}",
                f"- Missing clean pairs: {summary['missing_clean_pair_count']}",
                f"- Missing intervention pairs: {summary['missing_intervention_pair_count']}",
                f"- Blockers: {summary['blockers']}",
                f"- Warnings: {summary['warnings']}",
                f"- Isolation score: {summary['isolation_score']}",
            ],
        ),
        "## Per-Type Scores",
        "",
        "| Intervention type | Score | Pairs |",
        "|---|---:|---:|",
        *[
            f"| `{kind}` | {row['score']} | {row['pairs']} |"
            for kind, row in sorted(summary["per_intervention_type_score"].items())
        ],
        "",
        "## Top Risky Pairs",
        "",
    ]
    for record in report.get("top_riskiest_pairs", [])[:20]:
        lines.append(
            f"- `{record['pair_id']}` risk={record.get('risk_score')}, status=`{record['isolation_status']}`, unexpected={', '.join(record['unexpected_changed_fields']) or '(none)'}"
        )
    lines.extend(
        [
            "",
        "## Pair Findings",
        "",
        ]
    )
    for record in report["pairs"]:
        lines.extend(
            [
                f"### `{record['pair_id']}`",
                "",
                f"- Status: `{record['isolation_status']}`",
                f"- Severity: `{record['severity']}`",
                f"- Clean / intervention: `{record['clean_id']}` / `{record['intervention_id']}`",
                f"- Type: `{record['intervention_type']}`",
                f"- Isolation score / risk: `{record.get('isolation_score')}` / `{record.get('risk_score')}`",
                f"- Changed fields: {', '.join(record['changed_fields']) or '(none)'}",
                f"- Unexpected fields: {', '.join(record['unexpected_changed_fields']) or '(none)'}",
                f"- Explanation: {record['explanation']}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def _pair_rows(instances: list[dict[str, Any]]) -> dict[str, dict[str, list[dict[str, Any]]]]:
    pairs: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for instance in instances:
        base_id = _instance_task_id(instance) or _base_from_instance_id(_instance_id(instance))
        if not base_id:
            base_id = "unknown"
        pairs[base_id][_condition(instance)].append(instance)
    return pairs


def _base_from_instance_id(instance_id: str | None) -> str | None:
    if not instance_id or "." not in instance_id:
        return None
    return instance_id.split(".", 1)[0]


def _missing_clean_record(
    base_task_id: str,
    intervention: dict[str, Any],
    taxonomy: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    intervention_obj = intervention.get("intervention") or {}
    intervention_type = _intervention_type(intervention_obj)
    return {
        "pair_id": f"{base_task_id}.missing_clean",
        "clean_id": None,
        "intervention_id": _instance_id(intervention),
        "intervention_type": intervention_type,
        "isolation_status": "missing_clean_pair",
        "changed_fields": [],
        "intended_changed_fields": sorted(_intended_fields(intervention_type, taxonomy)),
        "unexpected_changed_fields": [],
        "changed_field_diff": {},
        "isolation_score": 0,
        "risk_score": 100,
        "severity": "blocker",
        "explanation": "Intervention instance has no statically linked clean pair.",
    }


def _missing_intervention_record(base_task_id: str, clean: dict[str, Any]) -> dict[str, Any]:
    return {
        "pair_id": f"{base_task_id}.missing_intervention",
        "clean_id": _instance_id(clean),
        "intervention_id": None,
        "intervention_type": "unknown",
        "isolation_status": "missing_intervention_pair",
        "changed_fields": [],
        "intended_changed_fields": [],
        "unexpected_changed_fields": [],
        "changed_field_diff": {},
        "isolation_score": 55,
        "risk_score": 45,
        "severity": "warning",
        "explanation": "Clean instance has no intervention variant; pair coverage is incomplete.",
    }


def _compare_pair(
    clean: dict[str, Any],
    intervention: dict[str, Any],
    taxonomy: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    intervention_obj = intervention.get("intervention") or {}
    intervention_type = _intervention_type(intervention_obj)
    changed = _changed_fields(clean, intervention, intervention_obj)
    policy = taxonomy.get(intervention_type)
    intended = _intended_fields(intervention_type, taxonomy)
    allowed_categories = set(policy.get("allowed_change_categories") or []) if policy else set()
    expected_unchanged = set(policy.get("expected_unchanged_fields", [])) if policy else set()
    change_categories = _semantic_change_categories(changed, intervention_type)
    benign_categories = sorted(category for category in change_categories if category in {"metadata_only", "provenance_only", "formatting_only"})
    semantic_categories = sorted(category for category in change_categories if category not in {"metadata_only", "provenance_only", "formatting_only"})
    unchanged_violations = sorted(
        field
        for field in changed
        if field in expected_unchanged and _field_category(field, intervention_type) not in allowed_categories
    )
    unexpected = sorted(
        field
        for field in changed
        if field not in intended
        and _field_category(field, intervention_type) not in allowed_categories
        and _field_category(field, intervention_type) not in {"metadata_only", "provenance_only", "formatting_only"}
    )
    missing_intended = not bool(set(changed) & intended)
    mapping_known = policy is not None
    expected_change = str(
        intervention_obj.get("expected_final_answer_change")
        or intervention.get("metadata", {}).get("expected_final_answer_change")
        or "no"
    ).lower()
    answer_preservation = str(policy.get("answer_preservation", "depends") if policy else "depends").lower()

    explanation_parts: list[str] = []
    severity = "informational"
    status = "isolated"
    severity_reason = "Only expected or benign static differences were detected."
    manual_review_reason = None

    if not mapping_known:
        status = "needs_review"
        severity = "warning"
        severity_reason = "Unknown intervention type requires manual review."
        manual_review_reason = "No taxonomy entry exists for this intervention type."
        explanation_parts.append(f"No field-change whitelist is registered for intervention type {intervention_type!r}.")
        unexpected = []
    if _instance_task_id(clean) != _instance_task_id(intervention):
        unexpected.append("base_task_id")
        explanation_parts.append("Clean and intervention task ids do not match.")
    if unchanged_violations:
        unexpected.extend(unchanged_violations)
        explanation_parts.append(
            "Changed fields violate the taxonomy expected-unchanged policy: "
            + ", ".join(unchanged_violations)
            + "."
        )
    if "expected_final_answer" in changed and (expected_change == "no" or answer_preservation == "answer_preserving"):
        unexpected.append("expected_final_answer")
        severity_reason = "Answer-preserving intervention changed the expected output."
        manual_review_reason = "Expected-output changes require taxonomy permission and rationale."
        explanation_parts.append("Expected answer changed despite an answer-preserving policy.")
    if "expected_final_answer" not in changed and (expected_change == "yes" or answer_preservation == "answer_changing"):
        status = "needs_review"
        severity = "warning"
        explanation_parts.append("Intervention is marked answer-changing but no answer/gold field change was detectable.")
    if "available_tools" in changed and intervention_type not in TOOL_INTERVENTIONS:
        unexpected.append("available_tools")
        explanation_parts.append("Tool availability changed for a non-tool intervention.")
    if "initial_memory" in changed and intervention_type not in MEMORY_INTERVENTIONS:
        unexpected.append("initial_memory")
        explanation_parts.append("Memory/context changed for a non-memory intervention.")
    if _observation_field_changed(changed) and intervention_type not in OBSERVATION_INTERVENTIONS:
        explanation_parts.append("Observation/conflict fields changed for a non-observation intervention.")
    if missing_intended:
        explanation_parts.append("The intended causal factor was not detectable in static fields.")
    if unexpected:
        status = "multi_factor_change"
        policy_severity = str(policy.get("severity_if_violated") or "") if policy else ""
        severe_semantic = _severe_semantic_violation(unexpected, semantic_categories, intervention_type)
        severity = "blocker" if (policy_severity == "blocker" and severe_semantic) or any(
            field
            in {
                "base_task_id",
                "expected_final_answer",
                "available_tools",
                "initial_memory",
                "user_instruction",
                "success_criteria",
            }
            for field in unexpected
        ) else "warning"
        if severity == "blocker":
            severity_reason = "Unexpected changes cross severe semantic categories."
        else:
            severity_reason = "Unexpected changes are review-worthy but not automatic provider-pilot blockers."
            manual_review_reason = "Review taxonomy or generator mapping before causal claims."
        if _long_horizon_expected_dependency(changed, unexpected, semantic_categories, intervention_type):
            severity = "warning"
            status = "needs_review"
            severity_reason = "Long-horizon dependency additions are expected but should be manually reviewed."
            manual_review_reason = "Confirm the dependency-chain edit did not alter the answer or tool schema."
    elif missing_intended:
        status = "needs_review"
        severity = "warning"
        severity_reason = "No intended causal-factor field was detectable."
        manual_review_reason = "Static mapping could be incomplete or the intervention may be ineffective."
    elif changed:
        if any(field.endswith("_patch") for field in changed):
            status = "likely_isolated"
        else:
            status = "isolated"
        severity = "informational"
        severity_reason = "Only intended static fields changed under the taxonomy policy."
        explanation_parts.append("Only intended static fields changed under the heuristic mapping.")
    else:
        status = "needs_review"
        severity = "warning"
        severity_reason = "No static field change was detected."
        manual_review_reason = "The intervention may be metadata-only or not applied."
        explanation_parts.append("No static field change was detected.")

    if changed and not semantic_categories and benign_categories and severity != "blocker":
        status = "likely_isolated"
        severity = "informational"
        severity_reason = "Only metadata/provenance/formatting differences were detected."
        manual_review_reason = None

    if len(changed) > 1 and unexpected:
        status = "multi_factor_change"
    unexpected = sorted(set(unexpected))
    isolation_score = _pair_isolation_score(status, severity, unexpected, changed, mapping_known)
    return {
        "pair_id": f"{_instance_id(clean)}::{_instance_id(intervention)}",
        "clean_id": _instance_id(clean),
        "intervention_id": _instance_id(intervention),
        "intervention_type": intervention_type,
        "isolation_status": status,
        "changed_fields": sorted(changed),
        "semantic_change_categories": semantic_categories,
        "benign_change_categories": benign_categories,
        "intended_changed_fields": sorted(intended),
        "unexpected_changed_fields": unexpected,
        "changed_field_diff": _changed_field_diff(clean, intervention, intervention_obj, changed),
        "isolation_score": isolation_score,
        "risk_score": 100 - isolation_score,
        "severity": severity,
        "severity_reason": severity_reason,
        "manual_review_reason": manual_review_reason,
        "explanation": " ".join(explanation_parts) or "Static heuristic found no isolation issues.",
    }


def _changed_fields(
    clean: dict[str, Any],
    intervention: dict[str, Any],
    intervention_obj: dict[str, Any],
) -> set[str]:
    changed: set[str] = set()
    comparisons = {
        "base_task_id": (_instance_task_id(clean), _instance_task_id(intervention)),
        "available_tools": (clean.get("available_tools"), intervention.get("available_tools")),
        "initial_memory": (clean.get("initial_memory"), intervention.get("initial_memory")),
        "observations": (clean.get("observations") or clean.get("initial_observations"), intervention.get("observations") or intervention.get("initial_observations")),
        "metadata": (_stable_subset(clean.get("metadata")), _stable_subset(intervention.get("metadata"))),
    }
    clean_task = clean.get("base_task") if isinstance(clean.get("base_task"), dict) else {}
    int_task = intervention.get("base_task") if isinstance(intervention.get("base_task"), dict) else {}
    comparisons.update(
        {
            "domain": (clean_task.get("domain"), int_task.get("domain")),
            "difficulty": (clean_task.get("difficulty"), int_task.get("difficulty")),
            "user_instruction": (_goal_field(clean_task, "user_instruction"), _goal_field(int_task, "user_instruction")),
            "success_criteria": (_goal_field(clean_task, "success_criteria"), _goal_field(int_task, "success_criteria")),
            "expected_final_answer": (_goal_field(clean_task, "expected_final_answer"), _goal_field(int_task, "expected_final_answer")),
            "hidden_ground_truth": (clean_task.get("hidden_ground_truth"), int_task.get("hidden_ground_truth")),
            "max_steps": (clean_task.get("max_steps"), int_task.get("max_steps")),
        }
    )
    for field, (left, right) in comparisons.items():
        if left != right and _formatting_equivalent(field, left, right):
            changed.add("formatting_only")
        elif left != right:
            changed.add(field)
    if intervention_obj.get("tool_availability_patch"):
        changed.add("tool_availability_patch")
    if intervention_obj.get("tool_output_patch"):
        changed.add("tool_output_patch")
    if intervention_obj.get("memory_patch"):
        changed.add("memory_patch")
    if intervention_obj.get("instruction_patch"):
        changed.add("instruction_patch")
    patch_details = intervention_obj.get("patch_details")
    if patch_details and patch_details not in ({}, None):
        changed.add("patch_details")
    return changed


def _stable_subset(metadata: Any) -> dict[str, Any]:
    if not isinstance(metadata, dict):
        return {}
    return {
        key: value
        for key, value in metadata.items()
        if key
        not in {
            "synthetic",
            "expected_final_answer_change",
            "final_answer_should_change",
            "designed_failure_mode",
            "timestamp",
            "created_at",
            "updated_at",
            "generated_at",
            "generator_seed",
            "provenance",
            "notes",
            "comments",
            "comment",
        }
    }


def _goal_field(task: dict[str, Any], field: str) -> Any:
    goal = task.get("goal") if isinstance(task.get("goal"), dict) else {}
    return goal.get(field, task.get(field))


def _intervention_type(intervention: dict[str, Any]) -> str:
    return str(
        intervention.get("family")
        or intervention.get("type")
        or intervention.get("intervention_type")
        or "unknown"
    )


def _intended_fields(intervention_type: str, taxonomy: dict[str, dict[str, Any]]) -> set[str]:
    policy = taxonomy.get(intervention_type)
    if policy is None:
        return set()
    return set(policy.get("allowed_changed_fields") or [])


def _observation_field_changed(changed: set[str]) -> bool:
    return bool({"observations", "tool_output_patch", "patch_details"} & changed)


def _semantic_change_categories(changed: set[str], intervention_type: str) -> set[str]:
    return {_field_category(field, intervention_type) for field in changed}


def _field_category(field: str, intervention_type: str) -> str:
    if field == "formatting_only":
        return "formatting_only"
    if field in {"metadata"}:
        return "metadata_only"
    if field in {"base_task_id", "domain", "difficulty"}:
        return "provenance_only"
    if field in {"user_instruction", "instruction_patch", "max_steps"}:
        return "prompt_surface"
    if field in {"available_tools", "tool_availability_patch", "tool_arguments", "argument_schema"}:
        return "tool_schema"
    if field in {"initial_memory", "memory_patch"}:
        return "memory_context"
    if field in {"observations", "tool_output_patch", "patch_details"}:
        return "observation_conflict"
    if field in {"expected_final_answer", "success_criteria", "hidden_ground_truth"}:
        return "expected_output"
    return "metadata_only" if field.endswith("_id") else "prompt_surface"


def _categories_for_fields(fields: set[str], intervention_type: str) -> set[str]:
    return {_field_category(field, intervention_type) for field in fields}


def _severe_semantic_violation(
    unexpected: list[str],
    semantic_categories: list[str],
    intervention_type: str,
) -> bool:
    if "expected_final_answer" in unexpected:
        return True
    if "tool_schema" in semantic_categories and intervention_type not in TOOL_INTERVENTIONS:
        return True
    if "memory_context" in semantic_categories and intervention_type not in MEMORY_INTERVENTIONS:
        return True
    categories = set(semantic_categories) - {"metadata_only", "provenance_only", "formatting_only"}
    return len(categories) >= 2


def _long_horizon_expected_dependency(
    changed: set[str],
    unexpected: list[str],
    semantic_categories: list[str],
    intervention_type: str,
) -> bool:
    if intervention_type != "long_horizon_dependency":
        return False
    if "expected_final_answer" in unexpected or "available_tools" in unexpected:
        return False
    allowed = {"prompt_surface", "metadata_only", "provenance_only", "formatting_only"}
    return set(semantic_categories).issubset(allowed) and bool(changed)


def _formatting_equivalent(field: str, left: Any, right: Any) -> bool:
    if field == "user_instruction":
        return _normalize_text(left) == _normalize_text(right)
    if field == "success_criteria":
        return sorted(_normalize_text(item) for item in _as_list(left)) == sorted(
            _normalize_text(item) for item in _as_list(right)
        )
    if field == "available_tools":
        return sorted(map(str, _as_list(left))) == sorted(map(str, _as_list(right)))
    return False


def _normalize_text(value: Any) -> str:
    return " ".join(str(value or "").split()).strip().lower()


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _pair_isolation_score(
    status: str,
    severity: str,
    unexpected: list[str],
    changed: set[str],
    mapping_known: bool,
) -> int:
    base = {
        "isolated": 100,
        "likely_isolated": 90,
        "needs_review": 62,
        "multi_factor_change": 35,
        "missing_clean_pair": 0,
        "missing_intervention_pair": 55,
    }.get(status, 50)
    if severity == "blocker":
        base -= 25
    elif severity == "warning":
        base -= 10
    base -= min(30, len(unexpected) * 10)
    if not mapping_known:
        base -= 10
    if len(changed) >= 4:
        base -= 10
    return int(max(0, min(100, base)))


def _overall_isolation_score(records: list[dict[str, Any]]) -> int:
    if not records:
        return 0
    return round(sum(record.get("isolation_score", 0) for record in records) / len(records))


def _intervention_type_scores(records: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    grouped: dict[str, list[int]] = defaultdict(list)
    for record in records:
        grouped[str(record.get("intervention_type") or "unknown")].append(int(record.get("isolation_score", 0)))
    return {
        kind: {"score": round(sum(scores) / len(scores)), "pairs": len(scores)}
        for kind, scores in grouped.items()
    }


def _changed_field_diff(
    clean: dict[str, Any],
    intervention: dict[str, Any],
    intervention_obj: dict[str, Any],
    changed: set[str],
) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for field in sorted(changed):
        out[field] = {
            "clean": _field_value(clean, {}, field),
            "intervention": _field_value(intervention, intervention_obj, field),
        }
    return out


def _field_value(instance: dict[str, Any], intervention_obj: dict[str, Any], field: str) -> Any:
    task = instance.get("base_task") if isinstance(instance.get("base_task"), dict) else {}
    if field == "base_task_id":
        return _instance_task_id(instance)
    if field in {"available_tools", "initial_memory", "observations", "metadata"}:
        return _short_value(instance.get(field))
    if field in {"domain", "difficulty", "hidden_ground_truth", "max_steps"}:
        return _short_value(task.get(field))
    if field in {"user_instruction", "success_criteria", "expected_final_answer"}:
        return _short_value(_goal_field(task, field))
    if field in {"tool_availability_patch", "tool_output_patch", "memory_patch", "instruction_patch", "patch_details"}:
        return _short_value(intervention_obj.get(field))
    return None


def _short_value(value: Any) -> Any:
    text = json.dumps(value, sort_keys=True, default=str)
    if len(text) > 240:
        return text[:237] + "..."
    return value


def _default_factor(intervention_type: str) -> str:
    if intervention_type in TOOL_INTERVENTIONS:
        return "tool behavior or availability"
    if intervention_type in MEMORY_INTERVENTIONS:
        return "initial memory"
    if intervention_type in OBSERVATION_INTERVENTIONS:
        return "observation evidence"
    if intervention_type in INSTRUCTION_INTERVENTIONS:
        return "user instruction"
    return "task behavior"


def _as_string_set(value: Any) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, str):
        return {value}
    if isinstance(value, list | tuple | set):
        return {str(item) for item in value if str(item)}
    return set()
