"""Static quality checks for no-run report bundles."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from causal_agent_bench.safety.common import section_markdown, write_dual_report

UNSUPPORTED_CLAIM_WORDS = ("proves", "demonstrates", "outperforms", "confirms")
CLAIM_CAVEATS = (
    "no empirical",
    "not empirical",
    "unsupported",
    "not supported",
    "does not",
    "do not",
    "cannot",
    "static",
    "no-run",
    "no run",
    "planned",
    "blocked",
    "not claim",
    # Forbidden-example context: the word is being shown as language to avoid.
    "forbidden",
    "never",
    "avoid",
    "not allowed",
    "do not say",
    "example of overclaim",
)
SKIP_MARKDOWN_STEMS = {
    "benchmark_card",
    "dataset_card",
    "intervention_card",
    "limitations_card",
    "advisor_review_packet",
    "advisor_review_checklist",
    # Reference doc that intentionally lists forbidden phrases verbatim.
    "claim_safe_wording_bank",
}


def build_report_quality_check(
    repo_root: str | Path,
    *,
    input_dir: str | Path,
    output_dir: str | Path = "reports/report_quality",
) -> dict[str, Any]:
    """Check that no-run reports are parseable, clustered, and claim-safe."""

    root = Path(repo_root).resolve()
    reports_dir = Path(input_dir)
    if not reports_dir.is_absolute():
        reports_dir = root / reports_dir
    out = Path(output_dir)
    if not out.is_absolute():
        out = root / out

    checks: list[dict[str, Any]] = []
    report_summaries: list[dict[str, Any]] = []
    json_paths = [
        path
        for path in sorted(reports_dir.glob("**/*.json")) if "report_quality" not in path.parts
    ] if reports_dir.exists() else []
    markdown_paths = [
        path
        for path in sorted(reports_dir.glob("**/*.md")) if "report_quality" not in path.parts
    ] if reports_dir.exists() else []

    if not reports_dir.exists():
        _add(checks, "blocker", "input_dir_missing", "bundle", f"Input report directory is missing: {reports_dir}")

    if not json_paths:
        _add(checks, "blocker", "no_json_reports", "bundle", "No JSON reports were found.")

    evidence_state = _evidence_state(json_paths)
    total_raw = 0
    total_clustered = 0
    for path in json_paths:
        relpath = _rel(path, reports_dir)
        try:
            raw_payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            _add(checks, "blocker", "json_not_parseable", relpath, "JSON report is not parseable.")
            continue
        if not isinstance(raw_payload, dict):
            # A valid top-level JSON array/scalar (e.g. a list of scenario rows) is
            # a legitimate report shape, not a malformed file; dict-shaped quality
            # checks simply do not apply to it.
            continue
        payload = raw_payload
        md_path = _matching_markdown(path)
        if not _manifest_like(path) and not md_path.exists():
            _add(checks, "warning", "markdown_missing", relpath, "JSON report has no matching Markdown companion.")
        summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
        raw_count, clustered_count = _raw_and_clustered_counts(payload)
        total_raw += raw_count
        total_clustered += clustered_count
        if raw_count > 1000 and clustered_count == 0:
            _add(
                checks,
                "warning" if path.name == "static_leakage_report.json" else "blocker",
                "noisy_raw_report_without_clustering",
                relpath,
                f"Report has {raw_count} raw issues and no root-cause clustering.",
            )
        if path.name == "static_leakage_report.json":
            if raw_count > 1000 and not _has_suppressed_count(payload):
                _add(
                    checks,
                    "warning",
                    "suppressed_symptom_count_missing",
                    relpath,
                    "High-volume static leakage report should include suppressed_symptom_count.",
                )
            if raw_count > 1000 and not payload.get("top_clusters"):
                _add(
                    checks,
                    "warning",
                    "top_clusters_missing",
                    relpath,
                    "High-volume static leakage report should include top_clusters.",
                )
            if raw_count > 1000 and not _has_classification_counts(payload):
                _add(
                    checks,
                    "warning",
                    "classification_counts_missing",
                    relpath,
                    "High-volume static leakage report should separate true leakage, manual-review, and false-positive candidates.",
                )
            if raw_count > 1000 and "false_positive_candidate_count" not in payload and "false_positive_candidate_count" not in summary:
                _add(
                    checks,
                    "warning",
                    "false_positive_candidate_count_missing",
                    relpath,
                    "High-volume static leakage report should count false-positive candidate clusters.",
                )
            if raw_count > 1000 and "top_true_leakage_clusters" not in payload:
                _add(
                    checks,
                    "warning",
                    "top_true_leakage_clusters_missing",
                    relpath,
                    "High-volume static leakage report should include a top_true_leakage_clusters field, even if empty.",
                )
            if raw_count > 1000 and "manual_review_queue" not in payload and "top_needs_manual_review" not in payload:
                _add(
                    checks,
                    "warning",
                    "manual_review_queue_missing",
                    relpath,
                    "High-volume static leakage report should include a manual-review queue.",
                )
            if raw_count > 1000 and "false_positive_candidates" not in payload and "top_false_positive_candidates" not in payload:
                _add(
                    checks,
                    "warning",
                    "false_positive_section_missing",
                    relpath,
                    "High-volume static leakage report should include likely false-positive/boilerplate clusters.",
                )
            if _static_leakage_requires_repair_plan(payload):
                leakage_plan_path = _find_report(reports_dir, "leakage_repair_plan.json")
                patch_manifest_path = _find_report(reports_dir, "proposed_patch_manifest.json")
                if leakage_plan_path is None:
                    _add(
                        checks,
                        "blocker",
                        "leakage_repair_plan_missing",
                        relpath,
                        "Static leakage has true/duplicate/answer leakage blockers, but leakage_repair_plan.json is missing.",
                    )
                else:
                    leakage_plan = _read_json(leakage_plan_path) or {}
                    if "manual_review_queue" not in leakage_plan:
                        _add(
                            checks,
                            "warning",
                            "leakage_manual_review_queue_missing",
                            _rel(leakage_plan_path, reports_dir),
                            "Leakage repair plan should include manual_review_queue.",
                        )
                if patch_manifest_path is None:
                    _add(
                        checks,
                        "blocker",
                        "proposed_patch_manifest_missing",
                        relpath,
                        "Leakage repair plan should produce proposed_patch_manifest.json.",
                    )
        if path.name == "proposed_patch_manifest.json":
            _patch_manifest_quality_checks(payload, checks, relpath)
        if path.name == "leakage_patch_apply_report.json":
            _patch_apply_quality_checks(payload, checks, relpath)
        if path.name == "leakage_suppression_registry.json":
            _suppression_registry_quality_checks(payload, checks, relpath)
        if path.name == "run_health_report.json":
            _run_health_quality_checks(payload, checks, relpath)
        if raw_count > 1000 and clustered_count and raw_count / max(clustered_count, 1) < 2:
            _add(
                checks,
                "warning",
                "weak_deduplication_ratio",
                relpath,
                f"Report has {raw_count} raw issues but {clustered_count} clusters; check whether grouping is too fine.",
            )
        if not _has_verdict_surface(payload):
            _add(checks, "warning", "top_level_verdict_missing", relpath, "Report has no clear verdict/summary surface.")
        if not _has_severity_separation(payload) and raw_count:
            _add(checks, "warning", "severity_separation_missing", relpath, "Issues are not clearly separated by severity.")
        if evidence_state["paper_eligible_runs"] == 0 and _paper_ready_claim(payload):
            _add(
                checks,
                "blocker",
                "paper_ready_with_zero_eligible_runs",
                relpath,
                "Report appears to mark empirical paper readiness despite zero paper-eligible runs.",
            )
        report_summaries.append(
            {
                "path": relpath,
                "raw_issue_count": raw_count,
                "clustered_issue_count": clustered_count,
                "has_verdict_surface": _has_verdict_surface(payload),
            }
        )

    json_stems = {path.with_suffix("").resolve() for path in json_paths}
    for path in markdown_paths:
        if path.stem in SKIP_MARKDOWN_STEMS:
            continue
        if path.with_suffix("").resolve() not in json_stems and _looks_like_report_markdown(path):
            _add(checks, "warning", "json_missing", _rel(path, reports_dir), "Markdown report has no matching JSON file.")
        if _markdown_raw_flood(path):
            _add(checks, "warning", "markdown_raw_flood", _rel(path, reports_dir), "Markdown appears to list too many raw findings.")
        for word, context in _unsupported_claim_language(path):
            _add(
                checks,
                "warning",
                "unsupported_claim_language",
                _rel(path, reports_dir),
                f"Uncaveated result-like word `{word}` found near: {context}",
            )

    if evidence_state["paper_eligible_runs"] == 0 and not evidence_state["included"]:
        _add(checks, "warning", "evidence_state_missing", "bundle", "Evidence state was not discoverable from reports.")

    blockers = [check for check in checks if check["severity"] == "blocker"]
    warnings = [check for check in checks if check["severity"] == "warning"]
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": "Static report-quality check only; no benchmark, provider, model, or claim-promotion commands are invoked.",
        "input_dir": str(reports_dir),
        "summary": {
            "json_report_count": len(json_paths),
            "markdown_report_count": len(markdown_paths),
            "raw_issue_count": total_raw,
            "clustered_issue_count": total_clustered,
            "blockers": len(blockers),
            "warnings": len(warnings),
            "informational": sum(1 for check in checks if check["severity"] == "informational"),
            "noisy_raw_reports": sum(
                1 for row in report_summaries if row["raw_issue_count"] > 1000 and row["clustered_issue_count"] == 0
            ),
        },
        "evidence_state": evidence_state,
        "verdicts": {
            "report_quality_passed": not blockers,
            "needs_review": bool(blockers or warnings),
            "blocked_by_noise": any(check["id"] == "noisy_raw_report_without_clustering" for check in blockers),
        },
        "checks": checks,
        "report_summaries": report_summaries,
    }
    md = report_quality_markdown(payload)
    md_path, json_path = write_dual_report(
        stem="report_quality_check",
        payload=payload,
        markdown=md,
        output_dir=out,
    )
    payload["report_paths"] = {"markdown": str(md_path), "json": str(json_path)}
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def report_quality_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# Report Quality Check",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        payload["scope"],
        "",
        section_markdown(
            "Summary",
            [
                f"- JSON reports: {summary['json_report_count']}",
                f"- Markdown reports: {summary['markdown_report_count']}",
                f"- Raw issues: {summary['raw_issue_count']}",
                f"- Clustered issues/root causes: {summary['clustered_issue_count']}",
                f"- Blockers: {summary['blockers']}",
                f"- Warnings: {summary['warnings']}",
                f"- Noisy raw reports without clustering: {summary['noisy_raw_reports']}",
            ],
        ),
        section_markdown(
            "Evidence State",
            [
                f"- Paper-eligible runs: {payload['evidence_state']['paper_eligible_runs']}",
                f"- Eligible paper assets: {payload['evidence_state']['eligible_paper_assets']}",
                f"- Evidence state discovered: `{payload['evidence_state']['included']}`",
            ],
        ),
        "## Checks",
        "",
    ]
    if not payload["checks"]:
        lines.append("- (none)")
    for check in payload["checks"]:
        lines.append(f"- `{check['severity']}` `{check['id']}` `{check['report']}`: {check['message']}")
    lines.append("")
    return "\n".join(lines)


def _add(checks: list[dict[str, Any]], severity: str, check_id: str, report: str, message: str) -> None:
    checks.append({"severity": severity, "id": check_id, "report": report, "message": message})


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    return payload if isinstance(payload, dict) else None


def _matching_markdown(path: Path) -> Path:
    if path.name == "index.json":
        return path.with_name("index.md")
    return path.with_suffix(".md")


def _manifest_like(path: Path) -> bool:
    return path.name.endswith("_manifest.json") or path.name == "benchmark_cards_manifest.json"


def _looks_like_report_markdown(path: Path) -> bool:
    stem = path.stem.lower()
    return any(token in stem for token in ("report", "validation", "plan", "readiness", "dashboard", "triage", "quality", "preflight", "index"))


def _raw_and_clustered_counts(payload: dict[str, Any]) -> tuple[int, int]:
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    raw = _int_or_none(summary.get("raw_repair_item_count"))
    if raw is None:
        raw = _int_or_none(summary.get("raw_finding_count"))
    if raw is None:
        raw = _int_or_none(payload.get("raw_finding_count"))
    if raw is None:
        raw = _int_or_none(summary.get("raw_issue_count"))
    if raw is None:
        raw = len(payload.get("raw_items") or payload.get("symptom_items") or [])
    if raw == 0:
        raw = max(
            len(payload.get("issues") or []),
            len(payload.get("checks") or []),
            len(payload.get("pairs") or []),
            len(payload.get("items") or []),
        )
    clustered = _int_or_none(summary.get("root_cause_count"))
    if clustered is None:
        clustered = _int_or_none(summary.get("cluster_count"))
    if clustered is None:
        clustered = _int_or_none(payload.get("cluster_count"))
    if clustered is None:
        clustered = _int_or_none(summary.get("clustered_issue_count"))
    if clustered is None:
        clustered = max(len(payload.get("root_causes") or []), len(payload.get("root_cause_summary") or []), len(payload.get("root_cause_groups") or []))
    return raw, clustered


def _int_or_none(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _has_suppressed_count(payload: dict[str, Any]) -> bool:
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    return "suppressed_symptom_count" in payload or "suppressed_symptom_count" in summary


def _has_classification_counts(payload: dict[str, Any]) -> bool:
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    return isinstance(payload.get("classification_counts"), dict) or isinstance(summary.get("classification_counts"), dict)


def _static_leakage_requires_repair_plan(payload: dict[str, Any]) -> bool:
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    counts = payload.get("classification_counts") or summary.get("classification_counts") or {}
    if not isinstance(counts, dict):
        return False
    return any(int(counts.get(name) or 0) > 0 for name in ("true_split_leakage", "duplicate_id_leakage", "answer_leakage"))


def _find_report(reports_dir: Path, filename: str) -> Path | None:
    direct = reports_dir / filename
    if direct.exists():
        return direct
    matches = sorted(reports_dir.glob(f"**/{filename}")) if reports_dir.exists() else []
    return matches[0] if matches else None


def _patch_manifest_quality_checks(payload: dict[str, Any], checks: list[dict[str, Any]], relpath: str) -> None:
    operations = payload.get("operations") if isinstance(payload.get("operations"), list) else []
    for op in operations:
        if not isinstance(op, dict):
            continue
        target = str(op.get("operation_id") or relpath)
        for affected in op.get("affected_files") or []:
            path = str(affected).replace("\\", "/").strip("/")
            if path == "results" or path.startswith("results/") or "/results/" in path:
                _add(checks, "blocker", "patch_manifest_touches_results", target, f"Patch manifest operation touches results path: {affected}")
            if "claim_ledger" in path or "claim_evidence" in path:
                _add(checks, "blocker", "patch_manifest_touches_claims", target, f"Patch manifest operation touches claim/evidence path: {affected}")
        if _contains_true_marker(op, "scientific_evidence"):
            _add(checks, "blocker", "patch_manifest_promotes_evidence", target, "Patch manifest operation sets scientific_evidence=true.")
        if _contains_true_marker(op, "allow_paid_calls"):
            _add(checks, "blocker", "patch_manifest_enables_paid_calls", target, "Patch manifest operation sets allow_paid_calls=true.")


def _patch_apply_quality_checks(payload: dict[str, Any], checks: list[dict[str, Any]], relpath: str) -> None:
    """Flag obvious risks in a leakage_patch_apply_report.json file."""

    verdicts = payload.get("verdicts") if isinstance(payload.get("verdicts"), dict) else {}
    if verdicts.get("manifest_blocked"):
        _add(checks, "blocker", "patch_apply_manifest_blocked", relpath, "Patch-apply report indicates the manifest was blocked by safety checks.")
    if payload.get("apply_requested") and not verdicts.get("patches_applied"):
        _add(checks, "warning", "patch_apply_requested_but_no_patches_applied", relpath, "Apply was requested but no patches were applied; review refusals.")
    refusals = payload.get("refusals") if isinstance(payload.get("refusals"), list) else []
    for refusal in refusals:
        if not isinstance(refusal, dict):
            continue
        if refusal.get("id") in {"manifest_touches_forbidden_path", "manifest_promotes_evidence"}:
            _add(
                checks,
                "blocker",
                f"patch_apply_{refusal['id']}",
                relpath,
                f"Patch-apply refusal `{refusal['id']}`: {refusal.get('message', '')}",
            )
    actions = payload.get("actions") if isinstance(payload.get("actions"), list) else []
    for action in actions:
        if not isinstance(action, dict):
            continue
        category = str(action.get("category") or "")
        if category == "applied":
            if str(action.get("type") or "") != "rename_instance_id":
                _add(
                    checks,
                    "blocker",
                    "patch_apply_unexpected_type_applied",
                    relpath,
                    f"Only rename_instance_id may be applied; got `{action.get('type')}` for `{action.get('operation_id')}`.",
                )


def _suppression_registry_quality_checks(payload: dict[str, Any], checks: list[dict[str, Any]], relpath: str) -> None:
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    verdicts = payload.get("verdicts") if isinstance(payload.get("verdicts"), dict) else {}
    if summary.get("malformed_count", 0) > 0 or verdicts.get("registry_valid") is False:
        _add(checks, "warning", "suppression_registry_invalid", relpath, "Suppression registry contains malformed entries.")
    for entry in payload.get("entries") or []:
        if not isinstance(entry, dict):
            continue
        forbidden = {key for key in ("scientific_evidence", "allow_paid_calls", "paper_eligible") if key in entry}
        if forbidden:
            _add(
                checks,
                "blocker",
                "suppression_entry_promotes_evidence",
                relpath,
                f"Suppression entry `{entry.get('id')}` uses forbidden keys: {sorted(forbidden)}.",
            )
        if "answer_leakage" in (entry.get("classifications") or []) or "duplicate_id_leakage" in (entry.get("classifications") or []):
            _add(
                checks,
                "blocker",
                "suppression_blocks_evidence_class",
                relpath,
                f"Suppression entry `{entry.get('id')}` targets an always-blocking class.",
            )


def _run_health_quality_checks(payload: dict[str, Any], checks: list[dict[str, Any]], relpath: str) -> None:
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    if summary.get("index_stale"):
        indexed = summary.get("indexed_run_count")
        live = summary.get("live_run_count")
        _add(
            checks,
            "warning",
            "stale_run_index",
            relpath,
            f"Run index is stale ({indexed} indexed vs {live} on disk); reports undercount runs "
            "until `index-runs` is re-run (inventory-only, safe).",
        )
    if summary.get("unindexed_paper_eligible_count"):
        _add(
            checks,
            "blocker",
            "unindexed_paper_eligible_run",
            relpath,
            f"{summary['unindexed_paper_eligible_count']} run(s) on disk but not in the index would "
            "classify as paper-eligible — verify provenance before indexing; do not promote.",
        )


def _contains_true_marker(value: Any, key: str) -> bool:
    if isinstance(value, dict):
        for current_key, current_value in value.items():
            if str(current_key) == key and current_value is True:
                return True
            if _contains_true_marker(current_value, key):
                return True
    if isinstance(value, list):
        return any(_contains_true_marker(item, key) for item in value)
    return False


def _has_verdict_surface(payload: dict[str, Any]) -> bool:
    return any(
        key in payload
        for key in (
            "summary",
            "verdict",
            "verdicts",
            "passed",
            "readiness",
            "gate_summary",
            "gate_status",
            "current_evidence_state",
        )
    )


def _has_severity_separation(payload: dict[str, Any]) -> bool:
    if isinstance(payload.get("summary"), dict):
        summary = payload["summary"]
        if any(key in summary for key in ("blockers", "warnings", "informational")):
            return True
    if any(key in payload for key in ("blockers", "warnings", "groups", "issue_families")):
        return True
    rows: list[dict[str, Any]] = []
    for key in ("issues", "checks", "pairs", "items", "raw_items"):
        value = payload.get(key)
        if isinstance(value, list):
            rows.extend(row for row in value if isinstance(row, dict))
    severities = {str(row.get("severity") or row.get("badge") or "") for row in rows}
    return bool(severities & {"blocker", "warning", "informational", "needs_review"})


def _evidence_state(json_paths: list[Path]) -> dict[str, Any]:
    state = {"included": False, "paper_eligible_runs": 0, "eligible_paper_assets": 0}
    for path in json_paths:
        payload = _read_json(path)
        if not payload:
            continue
        current = payload.get("current_evidence_state")
        if isinstance(current, dict):
            state["included"] = True
            state["paper_eligible_runs"] = int(current.get("paper_eligible_runs") or 0)
            state["eligible_paper_assets"] = int(current.get("eligible_paper_assets") or 0)
        if path.name == "run_health_report.json":
            summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
            state["included"] = True
            state["paper_eligible_runs"] = int(summary.get("paper_eligible_count") or state["paper_eligible_runs"])
        if path.name == "paper_asset_eligibility.json":
            state["included"] = True
            state["eligible_paper_assets"] = int(payload.get("eligible_count") or state["eligible_paper_assets"])
    return state


def _paper_ready_claim(payload: dict[str, Any]) -> bool:
    verdicts = payload.get("verdicts") if isinstance(payload.get("verdicts"), dict) else {}
    if verdicts.get("ready_for_empirical_paper_submission") is True:
        return True
    readiness = payload.get("readiness") if isinstance(payload.get("readiness"), dict) else {}
    if readiness.get("empirical_paper_ready") is True:
        return True
    text = _bounded_payload_text(payload).lower()
    return "paper-ready" in text and "empirical" in text and "false" not in text[: text.find("paper-ready") + 120]


def _bounded_payload_text(value: Any, *, max_chars: int = 200_000, max_list_items: int = 25) -> str:
    """Return enough text for claim checks without serializing huge reports."""
    parts: list[str] = []

    def add(text: str) -> bool:
        if sum(len(part) for part in parts) >= max_chars:
            return False
        remaining = max_chars - sum(len(part) for part in parts)
        parts.append(text[:remaining])
        return remaining > len(text)

    def walk(item: Any) -> None:
        if sum(len(part) for part in parts) >= max_chars:
            return
        if isinstance(item, dict):
            for key, child in item.items():
                if not add(str(key)):
                    return
                walk(child)
        elif isinstance(item, list):
            for child in item[:max_list_items]:
                walk(child)
                if sum(len(part) for part in parts) >= max_chars:
                    return
            if len(item) > max_list_items:
                add(f"list_truncated_{len(item) - max_list_items}")
        elif isinstance(item, (str, int, float, bool)) or item is None:
            add(str(item))

    walk(value)
    return " ".join(parts)


def _unsupported_claim_language(path: Path) -> list[tuple[str, str]]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []
    lowered = text.lower()
    findings: list[tuple[str, str]] = []
    for word in UNSUPPORTED_CLAIM_WORDS:
        for match in re.finditer(rf"\b{re.escape(word)}\b", lowered):
            start = max(0, match.start() - 80)
            end = min(len(lowered), match.end() + 80)
            window = lowered[start:end]
            if any(caveat in window for caveat in CLAIM_CAVEATS):
                continue
            context = " ".join(text[start:end].split())
            findings.append((word, context[:180]))
            break
    return findings


def _markdown_raw_flood(path: Path) -> bool:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return False
    raw_like = [
        line
        for line in lines
        if line.startswith("- `")
        and any(token in line for token in ("`near_duplicate_prompt`", "`answer_text_leakage`", "`duplicate_task_id`", "`intervention_label_leakage`", "`hidden_metadata_visible`"))
    ]
    return len(raw_like) > 150


def _rel(path: Path, base: Path) -> str:
    try:
        return str(path.relative_to(base))
    except ValueError:
        return str(path)
