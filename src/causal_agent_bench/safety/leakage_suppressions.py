"""Reviewed leakage suppression registry.

This module loads ``configs/static_leakage_suppressions.yaml`` (or a path provided
by the caller) and uses it to mark already-reviewed static-leakage clusters as
suppressed. Suppressions never silently delete findings: the raw findings remain
in JSON for traceability, the suppression is logged on the cluster row, and a
suppression report is generated for advisor review.

Hard rules:

* Suppressions can never hide ``answer_leakage`` or ``duplicate_id_leakage``
  clusters. Those classes are always considered hard blockers regardless of
  registry entries.
* Suppressions can never set ``scientific_evidence=true``, ``allow_paid_calls=true``,
  or otherwise promote evidence — those keys are simply not supported and any
  such entries are reported as malformed.
* Each entry must include ``reviewer``, ``reason``, ``scope``, and ``date``.
* ``review_after`` (a future date) flips the suppression to ``expired`` once the
  date has passed; the cluster reappears in active blocker lists with an
  ``expired_suppression`` warning.

The registry is purely advisory metadata. It does not modify the dataset or any
run output, and it never edits ``results/`` or claim-ledger files.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import yaml

from causal_agent_bench.safety.common import section_markdown, write_dual_report

DEFAULT_REGISTRY_PATH = Path("configs/static_leakage_suppressions.yaml")

REQUIRED_FIELDS = frozenset({"reviewer", "reason", "scope", "date"})
ALLOWED_SCOPES = frozenset(
    {
        "static_leakage_false_positive",
        "static_leakage_template_reuse",
        "static_leakage_pair_similarity",
        "static_leakage_tool_description",
        "static_leakage_system_instruction",
        "static_leakage_needs_review_documented",
    }
)
NEVER_SUPPRESSIBLE_CLASSIFICATIONS = frozenset(
    {"answer_leakage", "duplicate_id_leakage", "hidden_metadata_visible", "intervention_label_leakage"}
)
NEVER_SUPPRESSIBLE_RISKS = frozenset({"blocker"})
FORBIDDEN_KEYS = frozenset({"scientific_evidence", "allow_paid_calls", "paper_eligible", "promote_to_supported"})


def load_suppression_registry(
    repo_root: str | Path,
    *,
    path: str | Path | None = None,
) -> dict[str, Any]:
    """Load and validate the static leakage suppression registry."""

    root = Path(repo_root).resolve()
    registry_path = Path(path) if path else DEFAULT_REGISTRY_PATH
    if not registry_path.is_absolute():
        registry_path = root / registry_path

    issues: list[dict[str, Any]] = []
    entries: list[dict[str, Any]] = []
    raw_yaml: dict[str, Any] = {}

    if registry_path.exists():
        try:
            raw_yaml = yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            issues.append(
                {
                    "severity": "blocker",
                    "id": "registry_not_parseable",
                    "target": str(registry_path),
                    "message": f"Suppression registry is not parseable YAML: {exc}",
                }
            )
            raw_yaml = {}
        if not isinstance(raw_yaml, dict):
            issues.append(
                {
                    "severity": "blocker",
                    "id": "registry_not_mapping",
                    "target": str(registry_path),
                    "message": "Suppression registry root must be a mapping with a 'suppressions' list.",
                }
            )
            raw_yaml = {}

    raw_entries = raw_yaml.get("suppressions") if isinstance(raw_yaml, dict) else None
    if raw_entries is None and registry_path.exists() and isinstance(raw_yaml, dict):
        # Allow either {"suppressions": [...]} or a bare list-shaped value.
        if isinstance(raw_yaml.get("entries"), list):
            raw_entries = raw_yaml["entries"]
    if raw_entries is None:
        raw_entries = []
    if not isinstance(raw_entries, list):
        issues.append(
            {
                "severity": "blocker",
                "id": "suppressions_not_list",
                "target": str(registry_path),
                "message": "Suppression registry 'suppressions' must be a list.",
            }
        )
        raw_entries = []

    today = datetime.now(UTC).date()
    for index, entry in enumerate(raw_entries):
        normalized = _validate_entry(entry, index, today, issues, registry_path)
        if normalized is not None:
            entries.append(normalized)

    return {
        "registry_path": str(registry_path),
        "exists": registry_path.exists(),
        "entries": entries,
        "issues": issues,
        "active_count": sum(1 for entry in entries if entry["status"] == "active"),
        "expired_count": sum(1 for entry in entries if entry["status"] == "expired"),
        "malformed_count": sum(1 for issue in issues if issue["severity"] == "blocker"),
    }


def apply_suppressions(
    root_causes: list[dict[str, Any]],
    *,
    registry: dict[str, Any],
) -> dict[str, Any]:
    """Apply suppressions to a list of static-leakage root-cause rows.

    Returns a payload with annotated rows and a per-entry usage log. The
    original ``root_causes`` list is *not* mutated; a deep-ish copy is returned.
    """

    entries = [entry for entry in registry.get("entries", []) if entry["status"] == "active"]
    usage: dict[str, int] = {entry["id"]: 0 for entry in entries}
    refused: list[dict[str, Any]] = []
    annotated: list[dict[str, Any]] = []

    for row in root_causes:
        if not isinstance(row, dict):
            annotated.append(row)
            continue
        entry, refusal = _match_entry(row, entries)
        if refusal is not None:
            refused.append(refusal)
        clone = dict(row)
        if entry is not None:
            clone["suppressed"] = True
            clone["suppression_id"] = entry["id"]
            clone["suppression_reviewer"] = entry["reviewer"]
            clone["suppression_reason"] = entry["reason"]
            clone["suppression_date"] = entry["date"]
            clone["suppression_scope"] = entry["scope"]
            if entry.get("review_after"):
                clone["suppression_review_after"] = entry["review_after"]
            usage[entry["id"]] = usage.get(entry["id"], 0) + 1
        else:
            clone.setdefault("suppressed", False)
        annotated.append(clone)

    expired_entries = [entry for entry in registry.get("entries", []) if entry["status"] == "expired"]

    return {
        "annotated_root_causes": annotated,
        "active_entries": entries,
        "expired_entries": expired_entries,
        "refused_attempts": refused,
        "usage_counts": usage,
    }


def build_suppression_registry_report(
    repo_root: str | Path,
    *,
    path: str | Path | None = None,
    output_dir: str | Path = "reports/leakage_suppressions",
) -> dict[str, Any]:
    """Generate a no-run report describing the loaded suppression registry."""

    root = Path(repo_root).resolve()
    registry = load_suppression_registry(root, path=path)
    out = Path(output_dir)
    if not out.is_absolute():
        out = root / out

    summary = {
        "registry_path": registry["registry_path"],
        "exists": registry["exists"],
        "active_count": registry["active_count"],
        "expired_count": registry["expired_count"],
        "malformed_count": registry["malformed_count"],
        "entry_count": len(registry["entries"]),
    }
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": (
            "Static suppression-registry validation only. Suppressions document reviewed false-positive "
            "clusters; they cannot promote claims, suppress answer/duplicate-ID leakage, or modify "
            "results/, claim ledger, or run metadata."
        ),
        "summary": summary,
        "entries": registry["entries"],
        "issues": registry["issues"],
        "rules": _registry_rules(),
        "verdicts": {
            "registry_valid": registry["malformed_count"] == 0,
            "active_suppressions_present": registry["active_count"] > 0,
            "expired_entries_present": registry["expired_count"] > 0,
        },
    }
    md = suppression_registry_markdown(payload)
    md_path, json_path = write_dual_report(
        stem="leakage_suppression_registry",
        payload=payload,
        markdown=md,
        output_dir=out,
    )
    payload["report_paths"] = {"markdown": str(md_path), "json": str(json_path)}
    out_json_text = _json_dumps(payload)
    json_path.write_text(out_json_text, encoding="utf-8")
    return payload


def suppression_registry_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# Leakage Suppression Registry",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        payload["scope"],
        "",
        section_markdown(
            "Summary",
            [
                f"- Registry path: `{summary['registry_path']}`",
                f"- Registry exists: `{summary['exists']}`",
                f"- Active suppressions: {summary['active_count']}",
                f"- Expired suppressions: {summary['expired_count']}",
                f"- Malformed entries: {summary['malformed_count']}",
            ],
        ),
        "## Entries",
        "",
    ]
    if not payload["entries"]:
        lines.append("- (none)")
    for entry in payload["entries"]:
        lines.append(
            f"- `{entry['id']}` `{entry['status']}` reviewer={entry['reviewer']} "
            f"scope={entry['scope']} date={entry['date']}"
        )
        lines.append(f"  - Reason: {entry['reason']}")
        if entry.get("review_after"):
            lines.append(f"  - Review after: {entry['review_after']}")
        for matcher_kind in ("classifications", "root_cause_ids", "cluster_ids"):
            values = entry.get(matcher_kind)
            if values:
                lines.append(f"  - Match `{matcher_kind}`: {', '.join(map(str, values))}")
    lines.extend(["", "## Issues", ""])
    if not payload["issues"]:
        lines.append("- (none)")
    for issue in payload["issues"]:
        lines.append(f"- `{issue['severity']}` `{issue['id']}` `{issue.get('target', '')}`: {issue['message']}")
    lines.extend(["", "## Rules", ""])
    for rule in payload["rules"]:
        lines.append(f"- {rule}")
    lines.append("")
    return "\n".join(lines)


def _registry_rules() -> list[str]:
    return [
        "Suppressions never hide answer_leakage or duplicate_id_leakage clusters.",
        "Suppressions never hide blocker-risk clusters; only false-positive or needs-review entries can be suppressed.",
        "Each entry requires reviewer, reason, scope, and date.",
        "Forbidden keys (scientific_evidence, allow_paid_calls, paper_eligible, promote_to_supported) are rejected.",
        "Expired suppressions reappear with an `expired_suppression` warning until extended.",
        "Suppressions do not modify dataset files, results/, claim ledger, or run metadata.",
    ]


def _validate_entry(
    entry: Any,
    index: int,
    today: date,
    issues: list[dict[str, Any]],
    registry_path: Path,
) -> dict[str, Any] | None:
    target = f"suppressions[{index}]"
    if not isinstance(entry, dict):
        issues.append({"severity": "blocker", "id": "entry_not_mapping", "target": target, "message": "Entry is not a mapping."})
        return None
    forbidden = FORBIDDEN_KEYS & set(entry)
    if forbidden:
        issues.append(
            {
                "severity": "blocker",
                "id": "entry_uses_forbidden_keys",
                "target": target,
                "message": f"Forbidden keys in suppression entry: {sorted(forbidden)}",
            }
        )
        return None
    missing = sorted(REQUIRED_FIELDS - set(entry))
    if missing:
        issues.append(
            {
                "severity": "blocker",
                "id": "entry_missing_required_fields",
                "target": target,
                "message": f"Suppression entry missing required fields: {missing}",
            }
        )
        return None
    scope = str(entry.get("scope") or "")
    if scope not in ALLOWED_SCOPES:
        issues.append(
            {
                "severity": "blocker",
                "id": "entry_scope_not_allowed",
                "target": target,
                "message": f"Scope `{scope}` is not in the allowed list: {sorted(ALLOWED_SCOPES)}",
            }
        )
        return None
    classifications = entry.get("classifications") or []
    if isinstance(classifications, str):
        classifications = [classifications]
    classifications = [str(value) for value in classifications]
    forbidden_classes = NEVER_SUPPRESSIBLE_CLASSIFICATIONS & set(classifications)
    if forbidden_classes:
        issues.append(
            {
                "severity": "blocker",
                "id": "entry_classifications_blocked",
                "target": target,
                "message": (
                    f"Suppression cannot match always-blocking classes: {sorted(forbidden_classes)}. "
                    "Answer/duplicate-ID/hidden-metadata/intervention-label leakage is never suppressible."
                ),
            }
        )
        return None
    cluster_ids = _coerce_list(entry.get("cluster_ids"))
    root_cause_ids = _coerce_list(entry.get("root_cause_ids"))
    if not (classifications or cluster_ids or root_cause_ids):
        issues.append(
            {
                "severity": "blocker",
                "id": "entry_missing_matcher",
                "target": target,
                "message": "Suppression entry must list classifications, cluster_ids, or root_cause_ids.",
            }
        )
        return None
    date_str = str(entry.get("date"))
    try:
        date.fromisoformat(date_str)
    except ValueError:
        issues.append(
            {
                "severity": "blocker",
                "id": "entry_date_invalid",
                "target": target,
                "message": f"date must be ISO-format YYYY-MM-DD (got {date_str!r}).",
            }
        )
        return None
    review_after_value = entry.get("review_after")
    review_after_str: str | None = None
    review_after_date: date | None = None
    if review_after_value is not None:
        review_after_str = str(review_after_value)
        try:
            review_after_date = date.fromisoformat(review_after_str)
        except ValueError:
            issues.append(
                {
                    "severity": "blocker",
                    "id": "entry_review_after_invalid",
                    "target": target,
                    "message": f"review_after must be ISO-format YYYY-MM-DD (got {review_after_str!r}).",
                }
            )
            return None
    status = "expired" if review_after_date is not None and review_after_date < today else "active"
    entry_id = str(entry.get("id") or "")
    if not entry_id:
        entry_id = "supp_" + hashlib.sha1(
            "|".join([str(entry.get("reviewer", "")), date_str, scope, ",".join(sorted(classifications))]).encode("utf-8")
        ).hexdigest()[:12]
    if status == "expired":
        issues.append(
            {
                "severity": "warning",
                "id": "entry_expired",
                "target": target,
                "message": (
                    f"Suppression `{entry_id}` expired on {review_after_str}; the cluster will reappear "
                    "in active blocker lists until reviewed again."
                ),
            }
        )
    return {
        "id": entry_id,
        "status": status,
        "reviewer": str(entry["reviewer"]),
        "reason": str(entry["reason"]),
        "scope": scope,
        "date": date_str,
        "review_after": review_after_str,
        "classifications": classifications,
        "cluster_ids": cluster_ids,
        "root_cause_ids": root_cause_ids,
    }


def _match_entry(
    row: dict[str, Any],
    entries: list[dict[str, Any]],
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    classification = str(row.get("cluster_classification") or "")
    leakage_risk = str(row.get("leakage_risk") or "")
    cluster_id = str(row.get("cluster_id") or row.get("root_cause_id") or "")
    root_cause_id = str(row.get("root_cause_id") or "")
    for entry in entries:
        if (cluster_id and cluster_id in entry["cluster_ids"]) or (root_cause_id and root_cause_id in entry["root_cause_ids"]) or (classification and classification in entry["classifications"]):
            matched = True
        else:
            matched = False
        if not matched:
            continue
        if classification in NEVER_SUPPRESSIBLE_CLASSIFICATIONS:
            return None, {
                "suppression_id": entry["id"],
                "cluster_id": cluster_id or root_cause_id,
                "classification": classification,
                "leakage_risk": leakage_risk,
                "reason": (
                    f"Suppression `{entry['id']}` cannot apply to always-blocking classification "
                    f"`{classification}`."
                ),
            }
        if leakage_risk in NEVER_SUPPRESSIBLE_RISKS:
            return None, {
                "suppression_id": entry["id"],
                "cluster_id": cluster_id or root_cause_id,
                "classification": classification,
                "leakage_risk": leakage_risk,
                "reason": (
                    f"Suppression `{entry['id']}` cannot apply to blocker-risk cluster "
                    f"`{cluster_id or root_cause_id}`."
                ),
            }
        return entry, None
    return None, None


def _coerce_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def _json_dumps(payload: dict[str, Any]) -> str:
    import json

    return json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n"
