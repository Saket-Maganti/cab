"""Single canonical source of truth for public-release blockers.

Reads the existing no-run reports and aggregates every public-release blocker
into one ranked list with explicit categories: license, paper assets, evidence,
leakage, dataset quality, dependency state, and dirty tree. No provider/network
calls; no claim promotion.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from causal_agent_bench.safety.common import section_markdown, write_dual_report

CATEGORY_ORDER = (
    "license",
    "evidence",
    "leakage",
    "pair_link",
    "dataset_quality",
    "config",
    "provider_pilot",
    "paper_assets",
    "reproducibility",
    "dirty_tree",
)


def build_release_blocker_report(
    repo_root: str | Path,
    *,
    reports_dir: str | Path = "reports/no_run",
    output_dir: str | Path = "reports/release_blockers",
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    reports = Path(reports_dir)
    if not reports.is_absolute():
        reports = root / reports
    out = Path(output_dir)
    if not out.is_absolute():
        out = root / out

    blockers: list[dict[str, Any]] = []

    blockers.extend(_license_blockers(root))
    blockers.extend(_evidence_blockers(reports))
    blockers.extend(_leakage_blockers(reports))
    blockers.extend(_pair_link_blockers(reports))
    blockers.extend(_dataset_quality_blockers(reports))
    blockers.extend(_config_blockers(reports))
    blockers.extend(_provider_pilot_blockers(reports))
    blockers.extend(_paper_asset_blockers(reports))
    blockers.extend(_reproducibility_blockers(reports))

    category_counts = {c: sum(1 for b in blockers if b["category"] == c) for c in CATEGORY_ORDER}
    rank_order = {c: i for i, c in enumerate(CATEGORY_ORDER)}
    severity_rank = {"blocker": 0, "warning": 1, "informational": 2}
    blockers.sort(key=lambda b: (rank_order.get(b["category"], 99), severity_rank.get(b["severity"], 99), -int(b.get("impact_count") or 0), b["id"]))
    for rank, blocker in enumerate(blockers, start=1):
        blocker["rank"] = rank
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": (
            "Static synthesis of public-release blockers from existing no-run reports. "
            "Does not run benchmarks, providers, or promote claims."
        ),
        "summary": {
            "blocker_count": sum(1 for b in blockers if b["severity"] == "blocker"),
            "warning_count": sum(1 for b in blockers if b["severity"] == "warning"),
            "informational_count": sum(1 for b in blockers if b["severity"] == "informational"),
            "category_counts": category_counts,
            "total": len(blockers),
            "reports_dir": str(reports),
        },
        "verdicts": {
            "ready_for_public_release": all(b["severity"] != "blocker" for b in blockers),
            "any_evidence_blockers": any(b["category"] == "evidence" and b["severity"] == "blocker" for b in blockers),
            "any_leakage_blockers": any(b["category"] == "leakage" and b["severity"] == "blocker" for b in blockers),
            "any_license_blockers": any(b["category"] == "license" and b["severity"] == "blocker" for b in blockers),
        },
        "category_order": list(CATEGORY_ORDER),
        "blockers": blockers,
        "top_10_blockers": [b for b in blockers if b["severity"] == "blocker"][:10],
    }
    md = release_blocker_markdown(payload)
    md_path, json_path = write_dual_report(
        stem="release_blocker_report",
        payload=payload,
        markdown=md,
        output_dir=out,
    )
    payload["report_paths"] = {"markdown": str(md_path), "json": str(json_path)}
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def release_blocker_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# Public Release Blocker Report",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        payload["scope"],
        "",
        section_markdown(
            "Summary",
            [
                f"- Blockers: {summary['blocker_count']}",
                f"- Warnings: {summary['warning_count']}",
                f"- Informational: {summary['informational_count']}",
                f"- Total: {summary['total']}",
                f"- Reports source: `{summary['reports_dir']}`",
            ],
        ),
        section_markdown(
            "Verdicts",
            [
                f"- Ready for public release: `{payload['verdicts']['ready_for_public_release']}`",
                f"- Any evidence blockers: `{payload['verdicts']['any_evidence_blockers']}`",
                f"- Any leakage blockers: `{payload['verdicts']['any_leakage_blockers']}`",
                f"- Any license blockers: `{payload['verdicts']['any_license_blockers']}`",
            ],
        ),
        "## Top 10 Blockers",
        "",
    ]
    if not payload["top_10_blockers"]:
        lines.append("- (none)")
    for b in payload["top_10_blockers"]:
        lines.append(f"- [{b['rank']}] `{b['category']}` [{b['severity']}] {b['title']}")
        if b.get("how"):
            lines.append(f"  - how: {b['how']}")
    lines.extend(["", "## Blockers By Category", ""])
    for category in payload["category_order"]:
        rows = [b for b in payload["blockers"] if b["category"] == category]
        if not rows:
            continue
        lines.append(f"### `{category}` ({len(rows)} items)")
        for b in rows[:25]:
            lines.append(f"- [{b['rank']}] [{b['severity']}] {b['title']}")
        if len(rows) > 25:
            lines.append(f"- ... {len(rows) - 25} more (see JSON)")
        lines.append("")
    return "\n".join(lines)


def _license_blockers(root: Path) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    if not (root / "LICENSE").exists():
        issues.append(_b("license", "blocker", "license_missing", "LICENSE missing", "Add a top-level LICENSE file."))
    if not (root / "DATA_LICENSE.md").exists():
        issues.append(_b("license", "warning", "data_license_missing", "DATA_LICENSE.md missing", "Document the dataset license."))
    if not (root / "CITATION.cff").exists():
        issues.append(_b("license", "warning", "citation_missing", "CITATION.cff missing", "Add a citation file for academic users."))
    return issues


def _evidence_blockers(reports: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    matrix = _read(reports / "claim_evidence_matrix.json")
    if matrix is None:
        return out
    statuses = {row.get("claim_id"): row.get("status") for row in matrix.get("claims", [])}
    promoted = [cid for cid, status in statuses.items() if status == "supported"]
    if promoted:
        out.append(
            _b("evidence", "blocker", f"claims_supported_{','.join(promoted)}",
               f"Claims marked supported: {promoted}", "Demote unsupported claims or back them with provider-backed runs.", impact_count=len(promoted))
        )
    # Even if not promoted, lack of any supported empirical claim is a release notice (informational, not blocker).
    if not any(statuses.get(f"C{i}") == "supported" for i in range(1, 9)):
        out.append(
            _b("evidence", "informational", "no_empirical_claims_supported",
               "No empirical claims supported (C1-C8 all planned)", "Acceptable for a method-only release; required for an empirical release.")
        )
    return out


def _leakage_blockers(reports: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    plan = _read(reports / "leakage_repair_plan/leakage_repair_plan.json") or _read(reports / "leakage_repair_plan.json")
    if plan is None:
        return out
    summary = plan.get("summary") if isinstance(plan.get("summary"), dict) else {}
    must_fix = int(summary.get("must_fix_before_provider_pilot_count") or 0)
    if must_fix:
        out.append(
            _b("leakage", "blocker", "leakage_must_fix_blockers",
               f"{must_fix} leakage clusters must be fixed before provider pilot",
               "See leakage_repair_plan.md.", impact_count=must_fix)
        )
    return out


def _pair_link_blockers(reports: Path) -> list[dict[str, Any]]:
    payload = _read(reports / "pair_link_validator/pair_link_validation.json") or _read(reports / "pair_link_validation.json")
    if payload is None:
        return []
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    blockers = int(summary.get("blockers") or 0)
    if blockers:
        return [
            _b("pair_link", "blocker", "pair_link_blockers",
               f"{blockers} pair-link consistency blockers", "See pair_link_validation.md.", impact_count=blockers)
        ]
    return []


def _dataset_quality_blockers(reports: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    payload = _read(reports / "benchmark_quality_report.json")
    if payload is not None:
        verdicts = payload.get("verdicts") if isinstance(payload.get("verdicts"), dict) else {}
        if not verdicts.get("benchmark_quality_ready_for_release", False):
            out.append(_b("dataset_quality", "blocker", "benchmark_quality_not_ready_for_release",
                          "Benchmark quality not ready for release", "See benchmark_quality_report.md."))
    triage = _read(reports / "dataset_issue_triage.json")
    if triage is not None:
        total = int(triage.get("total_issues") or 0)
        if total:
            out.append(_b("dataset_quality", "warning", "dataset_triage_issues",
                          f"{total} dataset triage issues", "See dataset_issue_triage.md.", impact_count=total))
    return out


def _config_blockers(reports: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    lint = _read(reports / "config_metadata_lint.json")
    if lint is not None:
        count = int(lint.get("issue_count") or 0)
        if count:
            out.append(_b("config", "warning", "config_lint_issues",
                          f"{count} config metadata lint issues", "See config_metadata_lint.md.", impact_count=count))
    return out


def _provider_pilot_blockers(reports: Path) -> list[dict[str, Any]]:
    preflight = _read(reports / "provider_pilot_preflight.json")
    if preflight is None:
        return []
    gate = preflight.get("gate_status") or "blocked"
    if gate == "blocked":
        return [
            _b("provider_pilot", "warning", "provider_preflight_blocked",
               "Provider preflight blocked", "Public release is acceptable as method-only; empirical release requires preflight=ready_for_live_run + approved config.")
        ]
    return []


def _paper_asset_blockers(reports: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    payload = _read(reports / "paper_asset_eligibility.json")
    if payload is None:
        return out
    eligible = int(payload.get("eligible_count") or 0)
    flagged = int(payload.get("flagged_count") or 0)
    if eligible == 0:
        out.append(_b("paper_assets", "warning", "no_eligible_paper_assets",
                      "No paper assets eligible for empirical release",
                      "Method-only release is OK; empirical release requires eligible assets backed by provider runs."))
    if flagged:
        out.append(_b("paper_assets", "warning", "flagged_paper_assets",
                      f"{flagged} paper assets flagged", "See paper_asset_eligibility.md.", impact_count=flagged))
    return out


def _reproducibility_blockers(reports: Path) -> list[dict[str, Any]]:
    payload = _read(reports / "reproducibility_manifest/reproducibility_manifest.json") or _read(reports / "reproducibility_manifest.json")
    if payload is None:
        return []
    out: list[dict[str, Any]] = []
    verdicts = payload.get("verdicts") if isinstance(payload.get("verdicts"), dict) else {}
    if not verdicts.get("dependency_locked", False):
        out.append(_b("reproducibility", "warning", "no_lockfile",
                      "No lockfile detected", "Add uv.lock / poetry.lock / requirements-lock.txt for reproducibility."))
    if not verdicts.get("all_datasets_frozen", False):
        out.append(_b("reproducibility", "warning", "unfrozen_datasets",
                      "Unfrozen datasets exist", "Public release should freeze data/processed datasets before publication."))
    if not verdicts.get("license_complete", False):
        out.append(_b("reproducibility", "blocker", "license_incomplete",
                      "License/data_license incomplete", "Add LICENSE and DATA_LICENSE.md before release."))
    return out


def _b(category: str, severity: str, blocker_id: str, title: str, how: str, *, impact_count: int = 0) -> dict[str, Any]:
    return {
        "id": f"rel_{category}_{blocker_id}",
        "category": category,
        "severity": severity,
        "title": title,
        "how": how,
        "impact_count": impact_count,
        "rank": 0,
    }


def _read(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None
