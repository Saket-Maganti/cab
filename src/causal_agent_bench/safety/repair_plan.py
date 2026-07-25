"""Report-driven no-run repair plan generator."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from causal_agent_bench.safety.common import section_markdown, write_dual_report

REPAIR_GROUPS = (
    "must_fix_before_provider_pilot",
    "must_fix_before_main_benchmark",
    "must_fix_before_public_release",
    "must_fix_before_empirical_paper",
    "should_fix_for_paper_clarity",
    "nice_to_have",
)

EXPECTED_REPORTS = {
    "benchmark_quality": "benchmark_quality_report.json",
    "intervention_isolation": "intervention_isolation_report.json",
    "dataset_issue_triage": "dataset_issue_triage.json",
    "provider_pilot_preflight": "provider_pilot_preflight.json",
    "release_readiness": "release_readiness_report.json",
    "config_metadata_lint": "config_metadata_lint.json",
    "paper_todo_inventory": "paper_todo_inventory.json",
    "claim_evidence_matrix": "claim_evidence_matrix.json",
}

SEVERITY_RANK = {"blocker": 4, "blocker_before_public_release": 4, "blocker_before_empirical_claims": 4, "warning": 3, "needs_review": 2, "informational": 1}
GROUP_RANK = {group: index for index, group in enumerate(REPAIR_GROUPS)}


def build_repair_plan(
    repo_root: str | Path,
    *,
    input_dir: str | Path = "reports",
    output_dir: str | Path = "reports/repair_plan",
) -> dict[str, Any]:
    """Build a ranked repair plan from previously generated no-run reports."""

    root = Path(repo_root).resolve()
    reports_dir = Path(input_dir)
    if not reports_dir.is_absolute():
        reports_dir = root / reports_dir
    out = Path(output_dir)
    if not out.is_absolute():
        out = root / out

    report_payloads: dict[str, dict[str, Any] | None] = {}
    report_paths: dict[str, str | None] = {}
    items: list[dict[str, Any]] = []

    for name, filename in EXPECTED_REPORTS.items():
        path = _find_report(reports_dir, filename)
        report_paths[name] = str(path) if path else None
        payload = _read_json(path) if path else None
        report_payloads[name] = payload
        if payload is None:
            items.append(_missing_report_item(name, filename))

    for name, payload in report_payloads.items():
        if payload is None:
            continue
        if name == "benchmark_quality":
            items.extend(_benchmark_quality_items(payload))
        elif name == "intervention_isolation":
            items.extend(_intervention_isolation_items(payload))
        elif name == "dataset_issue_triage":
            items.extend(_dataset_triage_items(payload))
        elif name == "provider_pilot_preflight":
            items.extend(_provider_preflight_items(payload))
        elif name == "release_readiness":
            items.extend(_release_readiness_items(payload))
        elif name == "config_metadata_lint":
            items.extend(_config_lint_items(payload))
        elif name == "paper_todo_inventory":
            items.extend(_paper_todo_items(payload))
        elif name == "claim_evidence_matrix":
            items.extend(_claim_evidence_items(payload))

    leakage_repair_payload = _read_json(_find_report(reports_dir, "leakage_repair_plan.json"))
    if leakage_repair_payload is not None:
        items.extend(_leakage_repair_plan_items(leakage_repair_payload))

    items = [_score_and_finalize(item) for item in items]
    items = sorted(
        items,
        key=lambda row: (
            GROUP_RANK.get(row["readiness_gate"], 99),
            -row["urgency_score"],
            -row["impact_score"],
            row["repair_id"],
        ),
    )
    for rank, item in enumerate(items, start=1):
        item["rank"] = rank

    root_causes = _cluster_root_causes(items)
    top_50 = root_causes[:50]
    top_provider_blockers = [
        row
        for row in root_causes
        if "must_fix_before_provider_pilot" in row["affected_readiness_gates"]
        and not _is_false_positive_root(row)
    ][:10]
    grouped = {group: [item for item in items if item["readiness_gate"] == group] for group in REPAIR_GROUPS}
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": "Static repair planning only; no benchmark run, provider call, model call, or claim promotion.",
        "input_dir": str(reports_dir),
        "report_paths": report_paths,
        "missing_reports": [name for name, report in report_payloads.items() if report is None],
        "recommendation_if_missing": "Run `python3 -m causal_agent_bench all-no-run-reports --output-dir <reports_dir>` before relying on this plan.",
        "summary": {
            "repair_item_count": len(items),
            "raw_repair_item_count": len(items),
            "root_cause_count": len(root_causes),
            "top_50_count": len(top_50),
            "suppressed_symptom_count": max(0, len(items) - len(root_causes)),
            "missing_report_count": sum(1 for report in report_payloads.values() if report is None),
            "top_gate": root_causes[0]["readiness_gate"] if root_causes else (items[0]["readiness_gate"] if items else "none"),
        },
        "groups": grouped,
        "root_causes": root_causes,
        "root_cause_summary": root_causes,
        "top_10_provider_pilot_blockers": top_provider_blockers,
        "false_positive_candidate_repairs": [
            row for row in root_causes if _is_false_positive_root(row)
        ][:50],
        "top_50_actionable_repairs": top_50,
        "suppressed_deduplicated_symptoms": [
            {
                "root_cause_id": row["root_cause_id"],
                "suppressed_count": max(0, row["symptom_count"] - len(row["representative_examples"])),
            }
            for row in root_causes
            if row["symptom_count"] > len(row["representative_examples"])
        ],
        "raw_items": items,
        "symptom_items": items,
        "items": top_50,
    }
    md = repair_plan_markdown(payload)
    md_path, json_path = write_dual_report(
        stem="repair_plan",
        payload=payload,
        markdown=md,
        output_dir=out,
    )
    payload["output_paths"] = {"markdown": str(md_path), "json": str(json_path)}
    payload["report_paths"] = {**payload["report_paths"], "markdown": str(md_path), "json": str(json_path)}
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def repair_plan_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Repair Plan",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        payload["scope"],
        "",
        section_markdown(
            "Summary",
            [
                f"- Raw repair items: {payload['summary']['raw_repair_item_count']}",
                f"- Root causes: {payload['summary']['root_cause_count']}",
                f"- Suppressed/deduplicated symptoms: {payload['summary']['suppressed_symptom_count']}",
                f"- Missing reports: {payload['summary']['missing_report_count']}",
                f"- Top readiness gate: `{payload['summary']['top_gate']}`",
                f"- Missing-report recommendation: {payload['recommendation_if_missing']}",
            ],
        ),
    ]
    lines.extend(["## Root Cause Summary", ""])
    if not payload.get("root_causes"):
        lines.append("- (none)")
    for item in payload.get("root_causes", [])[:20]:
        lines.append(
            f"{item['rank']}. `{item['root_cause_id']}` [{item['severity']}] "
            f"{item['root_cause_title']} ({item['symptom_count']} symptoms) -> {item['recommended_root_fix']}"
        )
    lines.extend(["", "## Top 10 Provider-Pilot Blockers", ""])
    if not payload.get("top_10_provider_pilot_blockers"):
        lines.append("- (none)")
    for item in payload.get("top_10_provider_pilot_blockers", []):
        lines.append(
            f"- rank {item['rank']} `{item['root_cause_id']}` [{item['severity']}] "
            f"{item['recommended_root_fix']} Examples: {', '.join(item['representative_examples']) or '(none)'}"
        )
    lines.extend(["", "## Top 50 Actionable Repairs", ""])
    if not payload.get("top_50_actionable_repairs"):
        lines.append("- (none)")
    for item in payload.get("top_50_actionable_repairs", []):
        lines.append(
            f"- rank {item['rank']} `{item['root_cause_id']}` [{item['severity']}] "
            f"{item['root_cause_title']} ({item['symptom_count']} symptoms, gates={', '.join(item['affected_readiness_gates'])})"
        )
    lines.extend(["", "## Suppressed / Deduplicated Symptoms", ""])
    suppressed = payload.get("suppressed_deduplicated_symptoms", [])
    if not suppressed:
        lines.append("- (none)")
    for row in suppressed[:50]:
        lines.append(f"- `{row['root_cause_id']}` suppressed {row['suppressed_count']} repeated symptoms")
    lines.extend(
        [
            "",
            "## Raw Symptom Policy",
            "",
            "Raw repair items are preserved in JSON under `raw_items` and `symptom_items`. Markdown intentionally emphasizes root causes so reviewers do not triage thousands of repeated symptoms manually.",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _find_report(reports_dir: Path, filename: str) -> Path | None:
    direct = reports_dir / filename
    if direct.exists():
        return direct
    matches = sorted(reports_dir.glob(f"**/{filename}")) if reports_dir.exists() else []
    return matches[0] if matches else None


def _read_json(path: Path | None) -> dict[str, Any] | None:
    if not path or not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _missing_report_item(name: str, filename: str) -> dict[str, Any]:
    return _item(
        source_report=name,
        source_issue_id="missing_report",
        severity="needs_review",
        affected_path=filename,
        affected_entity=name,
        recommended_fix=f"Generate {filename} with the no-run report lane.",
        rationale="The repair plan cannot evaluate this safety surface without the source report.",
        estimated_effort="tiny",
        compute_requirement="no-run only",
        risk_if_ignored="A missing static report can hide release or provider-pilot blockers.",
        dependencies=["all-no-run-reports"],
        suggested_owner="validation",
        readiness_gate="must_fix_before_provider_pilot",
    )


def _benchmark_quality_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for issue in payload.get("issues", []):
        severity = _severity(issue)
        out.append(
            _item(
                source_report="benchmark_quality_report.json",
                source_issue_id=str(issue.get("id") or "quality_issue"),
                severity=severity,
                affected_path=issue.get("dataset"),
                affected_entity=_entity(issue),
                recommended_fix=_quality_fix(str(issue.get("id") or "")),
                rationale=str(issue.get("message") or "Benchmark quality issue."),
                estimated_effort=_effort_for_issue(str(issue.get("id") or ""), severity),
                compute_requirement="no-run only",
                risk_if_ignored="Dataset quality defects can invalidate pilot diagnostics or later causal comparisons.",
                dependencies=[],
                suggested_owner="dataset",
                readiness_gate=_gate_for_quality(str(issue.get("id") or ""), severity),
            )
        )
    return out


def _intervention_isolation_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for pair in payload.get("pairs", []):
        severity = _severity(pair)
        if severity == "informational" and pair.get("isolation_status") in {"isolated", "likely_isolated"}:
            continue
        status = str(pair.get("isolation_status") or "needs_review")
        out.append(
            _item(
                source_report="intervention_isolation_report.json",
                source_issue_id=status,
                severity=severity,
                affected_path=payload.get("instances_path"),
                affected_entity=pair.get("pair_id") or pair.get("intervention_id"),
                recommended_fix=_isolation_fix(status),
                rationale=str(pair.get("explanation") or "Intervention pair needs review."),
                estimated_effort="small" if severity != "blocker" else "medium",
                compute_requirement="no-run only",
                risk_if_ignored="Multi-factor or unknown interventions weaken causal attribution.",
                dependencies=["intervention_taxonomy"],
                suggested_owner="dataset",
                readiness_gate="must_fix_before_provider_pilot" if severity == "blocker" else "must_fix_before_main_benchmark",
            )
        )
    return out


def _dataset_triage_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for issue in payload.get("issues", []):
        group = str(issue.get("group") or "nice_to_have")
        gate = group if group in REPAIR_GROUPS else "must_fix_before_main_benchmark"
        out.append(
            _item(
                source_report="dataset_issue_triage.json",
                source_issue_id=str(issue.get("issue_id") or issue.get("raw_issue_id") or "triage_issue"),
                severity=_severity(issue),
                affected_path=issue.get("dataset_or_file"),
                affected_entity=issue.get("task_instance_or_pair_id"),
                recommended_fix=str(issue.get("suggested_fix") or "Repair the dataset issue."),
                rationale=str(issue.get("reason") or "Dataset triage item."),
                estimated_effort="small",
                compute_requirement="no-run only",
                risk_if_ignored="Known dataset issues will carry forward into provider spending.",
                dependencies=[],
                suggested_owner="dataset",
                readiness_gate=gate,
            )
        )
    for row in payload.get("leakage_root_causes", []):
        if not isinstance(row, dict):
            continue
        risk = str(row.get("leakage_risk") or "")
        classification = str(row.get("cluster_classification") or "")
        if risk == "informational":
            severity = "informational"
        elif risk == "false_positive_candidate":
            severity = "warning"
        elif risk == "blocker":
            severity = "blocker"
        else:
            severity = _severity(row)
        gate = str(row.get("readiness_gate") or "must_fix_before_main_benchmark")
        if risk == "false_positive_candidate":
            gate = "nice_to_have"
        item = _item(
            source_report="dataset_issue_triage.json",
            source_issue_id=str(row.get("root_cause_id") or row.get("finding_type") or "static_leakage_cluster"),
            severity=severity,
            affected_path="static_leakage_report.json",
            affected_entity=row.get("root_cause_title") or row.get("finding_type"),
            recommended_fix=str(row.get("recommended_root_fix") or row.get("recommended_action") or row.get("suggested_fix") or "Review leakage root cause."),
            rationale=str(row.get("reason") or row.get("root_cause_title") or "Static leakage root cause."),
            estimated_effort="small" if risk != "blocker" else "medium",
            compute_requirement="no-run only",
            risk_if_ignored="Leakage-like dataset structure can invalidate provider-pilot split interpretation if it is true leakage.",
            dependencies=[],
            suggested_owner="dataset",
            readiness_gate=gate,
        )
        item.update(
            {
                "leakage_risk": risk,
                "cluster_classification": classification,
                "symptom_count": row.get("symptom_count", 1),
            }
        )
        out.append(item)
    return out


def _leakage_repair_plan_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for item in payload.get("repair_items", []):
        if not isinstance(item, dict):
            continue
        classification = str(item.get("classification") or "needs_manual_review")
        leakage_risk = str(item.get("leakage_risk") or "needs_review")
        if leakage_risk == "false_positive_candidate":
            gate = "nice_to_have"
            severity = "warning"
        else:
            gate = str(item.get("readiness_gate") or "manual_review_needed")
            severity = "blocker" if leakage_risk == "blocker" else "warning"
        repair = _item(
            source_report="leakage_repair_plan.json",
            source_issue_id=str(item.get("cluster_id") or classification),
            severity=severity,
            affected_path="proposed_patch_manifest.json",
            affected_entity=item.get("cluster_id"),
            recommended_fix=str(item.get("suggested_safe_repair") or item.get("repair_strategy") or "Review leakage repair plan."),
            rationale=str(item.get("likely_root_cause") or "Leakage repair plan item."),
            estimated_effort="small" if severity != "blocker" else "medium",
            compute_requirement="no-run only",
            risk_if_ignored="Unrepaired leakage blockers can invalidate provider-pilot or main benchmark split readiness.",
            dependencies=["leakage_repair_plan_review"],
            suggested_owner="dataset",
            readiness_gate=gate,
        )
        repair.update(
            {
                "leakage_risk": leakage_risk,
                "cluster_classification": classification,
                "symptom_count": item.get("symptom_count", 1),
            }
        )
        out.append(repair)
    return out


def _provider_preflight_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    gate_status = str(payload.get("gate_status") or payload.get("gate_summary", {}).get("gate_status") or "")
    for check in payload.get("checks", []):
        severity = _severity(check)
        if severity == "informational":
            continue
        check_id = str(check.get("id") or "provider_preflight_check")
        if gate_status == "template_safe_but_not_runnable" and check_id in {
            "template_not_runnable",
            "approved_copy_required",
            "approved_copy_name",
            "model_placeholder_unresolved",
        }:
            source_issue_id = "provider_pilot_config_not_approved_yet"
            recommended_fix = "Provider pilot config not approved yet: complete advisor approval, copy the template, and resolve placeholders in the approved copy."
            rationale = "Provider pilot template is safe for static review but intentionally not runnable."
        else:
            source_issue_id = check_id
            recommended_fix = _provider_fix(check_id)
            rationale = str(check.get("message") or "Provider preflight issue.")
        out.append(
            _item(
                source_report="provider_pilot_preflight.json",
                source_issue_id=source_issue_id,
                severity=severity,
                affected_path=payload.get("config_path"),
                affected_entity=source_issue_id,
                recommended_fix=recommended_fix,
                rationale=rationale,
                estimated_effort="tiny" if severity == "warning" else "small",
                compute_requirement="none",
                risk_if_ignored="Provider pilot could be unsafe, unauditable, or spend without explicit approval.",
                dependencies=["advisor_approval"] if "approval" in source_issue_id else [],
                suggested_owner="config",
                readiness_gate="must_fix_before_provider_pilot",
            )
        )
    return out


def _release_readiness_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for check in payload.get("checks", []):
        severity = str(check.get("severity") or "warning")
        if severity == "informational":
            continue
        gate = "must_fix_before_empirical_paper" if "empirical" in severity or "claim" in severity else "must_fix_before_public_release"
        out.append(
            _item(
                source_report="release_readiness_report.json",
                source_issue_id=str(check.get("name") or "release_check"),
                severity="blocker" if severity.startswith("blocker") else severity,
                affected_path=None,
                affected_entity=check.get("name"),
                recommended_fix=str(check.get("message") or "Resolve release readiness check."),
                rationale=str(check.get("message") or "Release readiness issue."),
                estimated_effort="small",
                compute_requirement="none",
                risk_if_ignored="Release or empirical-paper readiness may be overstated.",
                dependencies=[],
                suggested_owner="release" if gate == "must_fix_before_public_release" else "paper",
                readiness_gate=gate,
            )
        )
    return out


def _config_lint_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for issue in payload.get("issues", []):
        severity = _severity(issue)
        out.append(
            _item(
                source_report="config_metadata_lint.json",
                source_issue_id=str(issue.get("id") or "config_lint"),
                severity=severity,
                affected_path=issue.get("path"),
                affected_entity=issue.get("id"),
                recommended_fix=_config_fix(str(issue.get("id") or "")),
                rationale=str(issue.get("message") or "Config metadata lint issue."),
                estimated_effort="tiny" if severity == "warning" else "small",
                compute_requirement="none",
                risk_if_ignored="Config provenance or paid-call safety may be ambiguous.",
                dependencies=[],
                suggested_owner="config",
                readiness_gate="must_fix_before_provider_pilot" if severity == "blocker" else "must_fix_before_public_release",
            )
        )
    return out


def _paper_todo_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = payload.get("items") or payload.get("todos") or []
    out = []
    for todo in rows:
        out.append(
            _item(
                source_report="paper_todo_inventory.json",
                source_issue_id=str(todo.get("id") or todo.get("kind") or "paper_todo"),
                severity=_severity(todo) if todo.get("severity") else "warning",
                affected_path=todo.get("path") or todo.get("file"),
                affected_entity=todo.get("line") or todo.get("claim_id"),
                recommended_fix="Resolve, rewrite, or explicitly mark the paper TODO as blocked.",
                rationale=str(todo.get("text") or todo.get("message") or "Paper TODO/placeholder."),
                estimated_effort="tiny",
                compute_requirement="none",
                risk_if_ignored="Paper draft may contain placeholders or unsupported wording.",
                dependencies=[],
                suggested_owner="paper",
                readiness_gate="should_fix_for_paper_clarity",
            )
        )
    return out


def _claim_evidence_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for claim in payload.get("claims", []):
        claim_id = str(claim.get("claim_id") or "")
        status = str(claim.get("status") or "planned")
        if claim_id == "C9" and status == "engineering_only":
            continue
        if status == "supported":
            continue
        gate = "must_fix_before_empirical_paper" if claim_id.startswith("C") else "should_fix_for_paper_clarity"
        out.append(
            _item(
                source_report="claim_evidence_matrix.json",
                source_issue_id=claim_id or "claim",
                severity="blocker" if claim_id in {f"C{i}" for i in range(1, 9)} | {"C10"} else "warning",
                affected_path="docs/claim_ledger.json",
                affected_entity=claim_id,
                recommended_fix="Keep claim blocked until eligible evidence exists; use method-only wording in drafts.",
                rationale=f"Claim {claim_id or '(unknown)'} is `{status}`, not supported by eligible evidence.",
                estimated_effort="large" if claim_id in {f"C{i}" for i in range(1, 9)} | {"C10"} else "small",
                compute_requirement="requires future provider run" if claim_id != "C10" else "no-run only",
                risk_if_ignored="Unsupported claims could be promoted into paper or release material.",
                dependencies=["eligible_provider_evidence"] if claim_id != "C10" else ["human_validation_artifacts"],
                suggested_owner="paper",
                readiness_gate=gate,
            )
        )
    return out


def _item(
    *,
    source_report: str,
    source_issue_id: str | None,
    severity: str,
    affected_path: Any,
    affected_entity: Any,
    recommended_fix: str,
    rationale: str,
    estimated_effort: str,
    compute_requirement: str,
    risk_if_ignored: str,
    dependencies: list[str],
    suggested_owner: str,
    readiness_gate: str,
) -> dict[str, Any]:
    source_issue_id = str(source_issue_id or "issue")
    affected = str(affected_path or "") + "|" + str(affected_entity or "") + "|" + rationale
    stable = hashlib.sha1(f"{source_report}|{source_issue_id}|{affected}".encode()).hexdigest()[:12]
    affected_entity_text = str(affected_entity) if affected_entity is not None else ""
    return {
        "repair_id": f"repair_{stable}",
        "source_report": source_report,
        "source_issue_id": source_issue_id,
        "severity": severity,
        "affected_path": str(affected_path) if affected_path else None,
        "affected_entity": affected_entity_text or None,
        "affected_task_id": _task_id_from_entity(affected_entity_text),
        "affected_intervention_type": _intervention_type_from_entity(affected_entity_text) or _intervention_type_from_text(rationale),
        "affected_field": _affected_field_from_text(source_issue_id, rationale, recommended_fix),
        "issue_family": _issue_family(source_report, source_issue_id, rationale, recommended_fix),
        "path_pattern": _path_pattern(str(affected_path or "")),
        "recommended_fix": recommended_fix,
        "rationale": rationale,
        "estimated_effort": estimated_effort,
        "compute_requirement": compute_requirement,
        "risk_if_ignored": risk_if_ignored,
        "dependencies": dependencies,
        "suggested_owner": suggested_owner,
        "readiness_gate": readiness_gate if readiness_gate in REPAIR_GROUPS else "nice_to_have",
    }


def _score_and_finalize(item: dict[str, Any]) -> dict[str, Any]:
    severity_score = SEVERITY_RANK.get(item["severity"], 2)
    gate_score = len(REPAIR_GROUPS) - GROUP_RANK.get(item["readiness_gate"], len(REPAIR_GROUPS) - 1)
    owner_bonus = 1 if item["suggested_owner"] in {"dataset", "config", "validation"} else 0
    compute_bonus = -1 if item["compute_requirement"] == "requires future provider run" else 0
    if item.get("leakage_risk") == "blocker":
        severity_score = max(severity_score, SEVERITY_RANK["blocker"])
    if item.get("cluster_classification") in {"answer_leakage", "duplicate_id_leakage", "true_split_leakage"}:
        owner_bonus += 1
    if _is_false_positive_root(item):
        severity_score = min(severity_score, SEVERITY_RANK["warning"])
        compute_bonus -= 2
    item["impact_score"] = max(1, min(10, severity_score * 2 + owner_bonus))
    item["urgency_score"] = max(1, min(10, gate_score + severity_score + compute_bonus))
    return item


def _cluster_root_causes(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        key = "|".join(
            [
                _cluster_source(item),
                item.get("issue_family") or item.get("source_issue_id") or "issue",
                item.get("affected_field") or "field_any",
                item.get("affected_intervention_type") or "intervention_any",
                item.get("path_pattern") or "path_any",
                item.get("readiness_gate") or "gate_any",
                item.get("cluster_classification") or "classification_any",
                item.get("leakage_risk") or "risk_any",
                _normalize_fix(item.get("recommended_fix")),
            ]
        )
        grouped.setdefault(key, []).append(item)

    root_causes = [_root_cause(key, rows) for key, rows in grouped.items()]
    root_causes = sorted(
        root_causes,
        key=lambda row: (
            GROUP_RANK.get(row["readiness_gate"], 99),
            _leakage_priority(row),
            -row["urgency_score"],
            -row["impact_score"],
            -row["symptom_count"],
            row["root_cause_id"],
        ),
    )
    for rank, row in enumerate(root_causes, start=1):
        row["rank"] = rank
    return root_causes


def _root_cause(key: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    severity = _max_severity(rows)
    gates = sorted({row["readiness_gate"] for row in rows})
    files = sorted({row["affected_path"] for row in rows if row.get("affected_path")})
    task_ids = sorted({row["affected_task_id"] for row in rows if row.get("affected_task_id")})
    intervention_types = sorted(
        {row["affected_intervention_type"] for row in rows if row.get("affected_intervention_type")}
    )
    issue_family = rows[0].get("issue_family") or rows[0].get("source_issue_id") or "issue"
    source_reports = sorted({row["source_report"] for row in rows})
    stable = hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]
    recommended = _root_fix(rows)
    representative = [
        row.get("affected_entity") or row.get("affected_path") or row.get("source_issue_id") or row["repair_id"]
        for row in rows[:5]
    ]
    impact = max(row.get("impact_score", 1) for row in rows)
    urgency = max(row.get("urgency_score", 1) for row in rows)
    leakage_risk = _mode([row.get("leakage_risk") for row in rows])
    cluster_classification = _mode([row.get("cluster_classification") for row in rows])
    return {
        "root_cause_id": f"root_{stable}",
        "repair_id": f"root_{stable}",
        "root_cause_title": _root_title(issue_family, intervention_types, files, source_reports),
        "symptom_count": len(rows),
        "representative_examples": representative,
        "affected_files": files[:20],
        "affected_task_ids": task_ids[:50],
        "affected_intervention_types": intervention_types,
        "affected_readiness_gates": gates,
        "recommended_root_fix": recommended,
        "severity": severity,
        "rank": None,
        "source_reports": source_reports,
        "source_report": ",".join(source_reports),
        "source_issue_id": issue_family,
        "readiness_gate": gates[0] if gates else "nice_to_have",
        "suggested_owner": _mode([row.get("suggested_owner") for row in rows]) or "validation",
        "impact_score": impact,
        "urgency_score": urgency,
        "leakage_risk": leakage_risk,
        "cluster_classification": cluster_classification,
        "raw_repair_ids": [row["repair_id"] for row in rows],
    }


def _cluster_source(item: dict[str, Any]) -> str:
    source = str(item.get("source_report") or "")
    if source == "dataset_issue_triage.json" and item.get("issue_family") == "intervention_isolation":
        return "intervention_isolation"
    return source


def _is_false_positive_root(row: dict[str, Any]) -> bool:
    return row.get("leakage_risk") == "false_positive_candidate" or row.get("cluster_classification") in {
        "likely_template_reuse",
        "clean_intervention_pair_similarity",
        "task_family_boilerplate",
        "shared_tool_description",
        "shared_system_instruction",
    }


def _leakage_priority(row: dict[str, Any]) -> int:
    if row.get("cluster_classification") in {"answer_leakage", "duplicate_id_leakage", "true_split_leakage"}:
        return 0
    if row.get("leakage_risk") == "blocker":
        return 1
    if row.get("leakage_risk") == "needs_review":
        return 2
    if _is_false_positive_root(row):
        return 9
    return 4


def _max_severity(rows: list[dict[str, Any]]) -> str:
    return max((row.get("severity", "warning") for row in rows), key=lambda value: SEVERITY_RANK.get(value, 0))


def _root_fix(rows: list[dict[str, Any]]) -> str:
    fixes = [str(row.get("recommended_fix") or "") for row in rows if row.get("recommended_fix")]
    if not fixes:
        return "Review this root cause before advancing readiness gates."
    return _mode(fixes) or fixes[0]


def _root_title(issue_family: str, intervention_types: list[str], files: list[str], sources: list[str]) -> str:
    parts = [issue_family.replace("_", " ")]
    if intervention_types:
        parts.append("for " + ", ".join(intervention_types[:3]))
    if files:
        parts.append("in " + _path_pattern(files[0]))
    elif sources:
        parts.append("from " + ", ".join(sources[:2]))
    return " ".join(parts)


def _mode(values: list[Any]) -> Any:
    counts: dict[Any, int] = {}
    for value in values:
        if value is None:
            continue
        counts[value] = counts.get(value, 0) + 1
    if not counts:
        return None
    return sorted(counts.items(), key=lambda row: (-row[1], str(row[0])))[0][0]


def _normalize_fix(value: Any) -> str:
    text = str(value or "").lower()
    for token in ("the affected ", "this ", "specific "):
        text = text.replace(token, "")
    return " ".join(text.split())[:80]


def _task_id_from_entity(entity: str) -> str | None:
    if not entity:
        return None
    token = entity.split("::", 1)[0]
    if "." in token:
        return token.split(".", 1)[0]
    return token if "_" in token else None


def _intervention_type_from_entity(entity: str) -> str | None:
    if not entity:
        return None
    token = entity.split("::")[-1]
    if "." not in token:
        return None
    return token.rsplit(".", 1)[-1]


def _intervention_type_from_text(text: str) -> str | None:
    known = (
        "long_horizon_dependency",
        "memory_corruption",
        "tool_failure",
        "tool_corruption",
        "tool_removal",
        "irrelevant_tools",
        "observation_conflict",
        "distractor_evidence",
        "ambiguous_instruction",
        "premature_success_signal",
    )
    lowered = text.lower()
    for value in known:
        if value in lowered:
            return value
    return None


def _affected_field_from_text(issue_id: str, rationale: str, fix: str) -> str:
    lowered = " ".join([issue_id, rationale, fix]).lower()
    fields = {
        "expected_final_answer": ("expected answer", "gold", "expected output", "final answer"),
        "available_tools": ("available_tools", "tool availability", "tool references", "tool schema"),
        "initial_memory": ("initial_memory", "memory"),
        "user_instruction": ("user_instruction", "instruction", "prompt"),
        "split_metadata": ("split", "heldout"),
        "approval": ("approval", "advisor"),
        "budget": ("budget",),
        "claim": ("claim", "c1", "c10"),
    }
    for field, markers in fields.items():
        if any(marker in lowered for marker in markers):
            return field
    return "metadata"


def _issue_family(source_report: str, issue_id: str, rationale: str, fix: str) -> str:
    lowered = " ".join([source_report, issue_id, rationale, fix]).lower()
    if "intervention" in lowered or "multi_factor" in lowered:
        return "intervention_isolation"
    if "gold" in lowered or "expected" in lowered or "answer" in lowered:
        return "gold_output"
    if "tool" in lowered:
        return "tool_schema"
    if "leak" in lowered or "duplicate" in lowered or "split" in lowered:
        return "leakage"
    if "config" in lowered or "approval" in lowered or "budget" in lowered:
        return "config"
    if "release" in lowered:
        return "release"
    if "paper" in lowered or "claim" in lowered:
        return "paper"
    if "pair" in lowered:
        return "pairing"
    return "validation"


def _path_pattern(path: str) -> str:
    if not path:
        return "repo"
    p = Path(path)
    parts = p.parts
    if "data" in parts:
        idx = parts.index("data")
        return "/".join(parts[idx : min(len(parts), idx + 3)])
    if "configs" in parts:
        return "configs/*.yaml"
    if "paper" in parts:
        return "paper/*"
    if "docs" in parts:
        return "docs/*"
    return str(p.parent) if p.suffix else str(p)


def _severity(row: dict[str, Any]) -> str:
    value = str(row.get("severity") or row.get("badge") or "warning")
    if value.startswith("blocker"):
        return "blocker"
    if value in {"safe", "ok"}:
        return "informational"
    return value


def _entity(row: dict[str, Any]) -> str | None:
    message = str(row.get("message") or "")
    for token in message.split():
        cleaned = token.strip("`:,.;")
        if "." in cleaned or "_" in cleaned:
            return cleaned
    return None


def _gate_for_quality(issue_id: str, severity: str) -> str:
    if severity == "blocker" and issue_id in {"missing_clean_pair", "missing_expected_output", "missing_tool_specs", "duplicate_task_id", "duplicate_instance_id"}:
        return "must_fix_before_provider_pilot"
    if issue_id in {"missing_heldout_split", "missing_split_metadata", "split_leakage_risk"}:
        return "must_fix_before_main_benchmark"
    if severity == "warning":
        return "must_fix_before_public_release"
    return "nice_to_have"


def _quality_fix(issue_id: str) -> str:
    fixes = {
        "missing_expected_output": "Add explicit expected output/gold-answer metadata.",
        "missing_tool_specs": "Add machine-readable tool specs or schemas.",
        "duplicate_task_id": "Rename duplicate task IDs and regenerate dependent instances.",
        "duplicate_instance_id": "Rename duplicate instance IDs before any run planning.",
        "missing_clean_pair": "Add the linked clean instance or remove the unpaired intervention.",
        "missing_heldout_split": "Create a frozen heldout/test split before main benchmark claims.",
    }
    return fixes.get(issue_id, "Review the benchmark quality finding and repair the affected metadata.")


def _effort_for_issue(issue_id: str, severity: str) -> str:
    if issue_id in {"duplicate_task_id", "duplicate_instance_id", "missing_clean_pair"}:
        return "medium"
    if severity == "blocker":
        return "small"
    return "tiny"


def _isolation_fix(status: str) -> str:
    if status == "multi_factor_change":
        return "Reduce the variant to one intended causal factor or exclude it from causal claims."
    if status == "missing_clean_pair":
        return "Add the matching clean instance for this intervention."
    if status == "missing_intervention_pair":
        return "Add an intervention variant or document paired-analysis exclusion."
    return "Review the intervention taxonomy and pair metadata."


def _provider_fix(check_id: str) -> str:
    if "approval" in check_id:
        return "Add explicit advisor approval markers only after human approval."
    if "paid" in check_id:
        return "Keep paid calls disabled in templates; enable only in approved copies."
    if "budget" in check_id:
        return "Add a tiny budget cap before provider approval."
    if "trajectory" in check_id or "stop" in check_id:
        return "Add tiny trajectory and runtime stop caps."
    return "Resolve the provider preflight blocker before any live provider run."


def _config_fix(issue_id: str) -> str:
    if "allow_paid_calls" in issue_id:
        return "Set allow_paid_calls explicitly and keep templates false."
    if "budget" in issue_id:
        return "Add a budget cap."
    if "trajectory" in issue_id:
        return "Add a tiny trajectory cap."
    if "evidence_scope" in issue_id:
        return "Declare a conservative evidence_scope."
    return "Repair config metadata according to the lint finding."
