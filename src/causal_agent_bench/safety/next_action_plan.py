"""Synthesize all blockers from the no-run reports into a single, ranked plan.

Reads the existing no-run report bundle (JSON files) and produces:

- ``next_action_plan.json`` — machine-readable ranked actions with explicit
  dependencies (e.g. answer-leakage repair must precede provider-pilot).
- ``next_action_plan.md`` — human-readable checklist.

This module is read-only. It does not run providers, modify datasets, or
promote any claim.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from causal_agent_bench.safety.common import section_markdown, write_dual_report

PHASE_ORDER = (
    "evidence_safety",
    "leakage_repair",
    "pair_link_repair",
    "dataset_quality",
    "config_hardening",
    "advisor_review",
    "provider_pilot",
    "human_validation",
    "release",
    "paper",
)


def build_next_action_plan(
    repo_root: str | Path,
    *,
    reports_dir: str | Path = "reports/no_run",
    output_dir: str | Path = "reports/next_action_plan",
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    reports = Path(reports_dir)
    if not reports.is_absolute():
        reports = root / reports
    out = Path(output_dir)
    if not out.is_absolute():
        out = root / out
    out.mkdir(parents=True, exist_ok=True)

    actions: list[dict[str, Any]] = []
    actions.extend(_evidence_safety_actions(reports))
    actions.extend(_leakage_actions(reports))
    actions.extend(_pair_link_actions(reports))
    actions.extend(_dataset_quality_actions(reports))
    actions.extend(_config_actions(reports))
    actions.extend(_advisor_actions(reports))
    actions.extend(_provider_pilot_actions(reports))
    actions.extend(_human_validation_actions(reports))
    actions.extend(_release_actions(reports))
    actions.extend(_paper_actions(reports))

    actions = _rank_actions(actions)
    phase_counts = {phase: sum(1 for a in actions if a["phase"] == phase) for phase in PHASE_ORDER}
    blockers = [a for a in actions if a["severity"] == "blocker"]
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": (
            "Static synthesis of no-run report blockers into a ranked action plan. "
            "Does not run benchmarks, providers, or promote any claim."
        ),
        "summary": {
            "action_count": len(actions),
            "blocker_count": len(blockers),
            "warning_count": sum(1 for a in actions if a["severity"] == "warning"),
            "informational_count": sum(1 for a in actions if a["severity"] == "informational"),
            "phase_counts": phase_counts,
            "reports_dir": str(reports),
        },
        "verdicts": {
            "any_provider_pilot_blockers": any(a["phase"] in {"leakage_repair", "pair_link_repair", "config_hardening"} and a["severity"] == "blocker" for a in actions),
            "next_phase": _next_phase(actions),
        },
        "phase_order": list(PHASE_ORDER),
        "actions": actions,
        "top_10": actions[:10],
        "top_25": actions[:25],
    }
    md = next_action_plan_markdown(payload)
    md_path, json_path = write_dual_report(
        stem="next_action_plan",
        payload=payload,
        markdown=md,
        output_dir=out,
    )
    payload["report_paths"] = {"markdown": str(md_path), "json": str(json_path)}
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def next_action_plan_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# Next Action Plan",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        payload["scope"],
        "",
        section_markdown(
            "Summary",
            [
                f"- Actions total: {summary['action_count']}",
                f"- Blockers: {summary['blocker_count']}",
                f"- Warnings: {summary['warning_count']}",
                f"- Informational: {summary['informational_count']}",
                f"- Reports source: `{summary['reports_dir']}`",
                f"- Next phase: `{payload['verdicts']['next_phase']}`",
            ],
        ),
        "## Top 10 Actions",
        "",
    ]
    if not payload["top_10"]:
        lines.append("- (none — re-run all-no-run-reports first)")
    for action in payload["top_10"]:
        lines.append(
            f"- [{action['rank']}] `{action['phase']}` [{action['severity']}] {action['title']}"
        )
        if action.get("why"):
            lines.append(f"  - why: {action['why']}")
        if action.get("how"):
            lines.append(f"  - how: {action['how']}")
        if action.get("depends_on"):
            lines.append(f"  - depends on: {', '.join(action['depends_on'])}")
    lines.extend(["", "## Actions By Phase", ""])
    for phase in payload["phase_order"]:
        rows = [a for a in payload["actions"] if a["phase"] == phase]
        if not rows:
            continue
        lines.append(f"### `{phase}` ({len(rows)} actions)")
        for action in rows[:25]:
            lines.append(
                f"- [{action['rank']}] [{action['severity']}] {action['title']}"
            )
        if len(rows) > 25:
            lines.append(f"- ... {len(rows) - 25} more (see JSON)")
        lines.append("")
    return "\n".join(lines)


def _rank_actions(actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    phase_rank = {phase: i for i, phase in enumerate(PHASE_ORDER)}
    severity_rank = {"blocker": 0, "warning": 1, "informational": 2, "needs_review": 1}

    def sort_key(a: dict[str, Any]) -> tuple[int, int, int, str]:
        return (
            phase_rank.get(a["phase"], 99),
            severity_rank.get(a["severity"], 99),
            -int(a.get("impact_count", 0)),
            a["id"],
        )

    actions.sort(key=sort_key)
    for rank, action in enumerate(actions, start=1):
        action["rank"] = rank
    return actions


def _next_phase(actions: list[dict[str, Any]]) -> str:
    for phase in PHASE_ORDER:
        if any(a["phase"] == phase and a["severity"] == "blocker" for a in actions):
            return phase
    return "none_blocking"


def _evidence_safety_actions(reports: Path) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    payload = _read(reports / "claim_evidence_matrix.json")
    if payload is None:
        actions.append(
            _action(
                "evidence_safety",
                "warning",
                "claim_evidence_matrix_missing",
                "Generate the claim-evidence matrix",
                "Re-run all-no-run-reports to produce claim_evidence_matrix.json.",
                why="Without the matrix, we cannot confirm claims remain unsupported.",
            )
        )
        return actions
    statuses = {row.get("claim_id"): row.get("status") for row in payload.get("claims", [])}
    supported = [cid for cid, status in statuses.items() if status == "supported"]
    if supported:
        actions.append(
            _action(
                "evidence_safety",
                "blocker",
                f"claims_marked_supported_{','.join(supported)}",
                f"Claims marked supported: {supported}",
                "Re-verify each supported claim against the no-run state; demote if not provider-backed.",
                why="Supported claims without provider-backed evidence violate evidence safety.",
                impact_count=len(supported),
            )
        )
    return actions


def _leakage_actions(reports: Path) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    plan = _read(reports / "leakage_repair_plan/leakage_repair_plan.json") or _read(reports / "leakage_repair_plan.json")
    if plan is None:
        return actions
    summary = plan.get("summary") if isinstance(plan.get("summary"), dict) else {}
    answer_repairs = plan.get("top_answer_leakage_repairs") or []
    duplicate_repairs = plan.get("top_duplicate_id_repairs") or []
    split_repairs = plan.get("top_split_metadata_repairs") or []
    manual_queue = plan.get("manual_review_queue") or []
    if answer_repairs:
        actions.append(
            _action(
                "leakage_repair",
                "blocker",
                "answer_leakage_manual_rewrite",
                f"Manually rewrite {len(answer_repairs)} answer-leakage clusters",
                "Open `manual_repair_preview.md`; rewrite the prompt/context for each cluster.",
                why="Answer text visible in prompt invalidates evaluation.",
                impact_count=len(answer_repairs),
                depends_on=[],
            )
        )
    if duplicate_repairs:
        actions.append(
            _action(
                "leakage_repair",
                "blocker",
                "duplicate_id_renames",
                f"Plan {len(duplicate_repairs)} duplicate-ID rename clusters",
                "Use `reviewed-ops-template` to list candidate renames, then `apply-leakage-patch --apply` after advisor approval.",
                why="Duplicate IDs make split attribution ambiguous.",
                impact_count=len(duplicate_repairs),
            )
        )
    if split_repairs:
        actions.append(
            _action(
                "leakage_repair",
                "warning",
                "split_metadata_repairs",
                f"Manually fix {len(split_repairs)} split metadata clusters",
                "Edit splits.json or pair linkage as described in `manual_repair_preview.md`.",
                impact_count=len(split_repairs),
            )
        )
    if summary.get("must_fix_before_provider_pilot_count", 0) and not answer_repairs and not duplicate_repairs:
        actions.append(
            _action(
                "leakage_repair",
                "blocker",
                "leakage_must_fix_other",
                f"Resolve {summary['must_fix_before_provider_pilot_count']} other leakage clusters before provider pilot",
                "Inspect leakage_repair_plan.md for the cluster details.",
                impact_count=int(summary["must_fix_before_provider_pilot_count"]),
            )
        )
    if manual_queue:
        actions.append(
            _action(
                "leakage_repair",
                "warning",
                "leakage_manual_review_queue",
                f"Review {len(manual_queue)} manual-review leakage clusters",
                "Inspect representative_examples per cluster; decide rewrite/suppress/leave.",
                impact_count=len(manual_queue),
            )
        )
    return actions


def _pair_link_actions(reports: Path) -> list[dict[str, Any]]:
    payload = _read(reports / "pair_link_validator/pair_link_validation.json") or _read(reports / "pair_link_validation.json")
    if payload is None:
        return []
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    blockers = int(summary.get("blockers") or 0)
    warnings = int(summary.get("warnings") or 0)
    actions: list[dict[str, Any]] = []
    if blockers:
        actions.append(
            _action(
                "pair_link_repair",
                "blocker",
                "pair_link_blockers",
                f"Fix {blockers} pair-link blockers",
                "See `pair_link_validation.md` for orphaned interventions, mismatched IDs, family/protected-split crossings.",
                impact_count=blockers,
            )
        )
    if warnings:
        actions.append(
            _action(
                "pair_link_repair",
                "warning",
                "pair_link_warnings",
                f"Review {warnings} pair-link warnings",
                "Mostly orphaned clean instances and duplicate intervention variants.",
                impact_count=warnings,
            )
        )
    return actions


def _dataset_quality_actions(reports: Path) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    payload = _read(reports / "benchmark_quality_report.json")
    if payload is None:
        return actions
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    blockers = int(summary.get("blockers") or 0)
    if blockers:
        actions.append(
            _action(
                "dataset_quality",
                "blocker",
                "benchmark_quality_blockers",
                f"Resolve {blockers} benchmark-quality blockers",
                "Inspect `benchmark_quality_report.md` Top Root Causes.",
                impact_count=blockers,
            )
        )
    triage = _read(reports / "dataset_issue_triage.json")
    if triage:
        total = int(triage.get("total_issues") or 0)
        if total > 0:
            actions.append(
                _action(
                    "dataset_quality",
                    "warning",
                    "dataset_issue_triage_review",
                    f"Triage {total} dataset issues",
                    "Open `dataset_issue_triage.md`; group by root cause and decide repair priority.",
                    impact_count=total,
                )
            )
    isolation = _read(reports / "intervention_isolation_report.json")
    if isolation:
        sum_i = isolation.get("summary") if isinstance(isolation.get("summary"), dict) else {}
        if int(sum_i.get("blockers") or 0):
            actions.append(
                _action(
                    "dataset_quality",
                    "blocker",
                    "intervention_isolation_blockers",
                    f"Fix {sum_i['blockers']} intervention isolation blockers",
                    "Inspect `intervention_isolation_report.md` Top Root Causes.",
                    impact_count=int(sum_i["blockers"]),
                )
            )
    return actions


def _config_actions(reports: Path) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    lint = _read(reports / "config_metadata_lint.json")
    if lint:
        count = int(lint.get("issue_count") or 0)
        if count:
            actions.append(
                _action(
                    "config_hardening",
                    "warning",
                    "config_lint_issues",
                    f"Resolve {count} config metadata lint issues",
                    "Inspect `config_metadata_lint.md`; tighten budget caps, evidence_scope, stop conditions.",
                    impact_count=count,
                )
            )
    return actions


def _advisor_actions(reports: Path) -> list[dict[str, Any]]:
    advisor = _read(reports / "advisor_review/advisor_review_manifest.json") or _read(reports / "advisor_review_manifest.json")
    if advisor is None:
        return []
    verdicts = advisor.get("verdicts") if isinstance(advisor.get("verdicts"), dict) else {}
    if not verdicts.get("advisor_review_ready", True):
        return [
            _action(
                "advisor_review",
                "warning",
                "advisor_review_not_ready",
                "Complete advisor review packet readiness gates",
                "Resolve leakage blockers first, then re-run all-no-run-reports.",
            )
        ]
    return [
        _action(
            "advisor_review",
            "informational",
            "advisor_review_ready_to_send",
            "Send advisor review packet for sign-off",
            "Share `advisor_review_packet.md` with advisor; capture decision in `advisor_review_checklist.md`.",
        )
    ]


def _provider_pilot_actions(reports: Path) -> list[dict[str, Any]]:
    preflight = _read(reports / "provider_pilot_preflight.json")
    if preflight is None:
        return []
    gate = preflight.get("gate_status") or "blocked"
    blockers = preflight.get("blockers") or []
    actions: list[dict[str, Any]] = []
    if gate == "blocked" and blockers:
        actions.append(
            _action(
                "provider_pilot",
                "blocker",
                "provider_preflight_blocked",
                f"Resolve {len(blockers)} provider preflight blockers",
                "See provider_pilot_preflight.md Verdicts and Checks.",
                impact_count=len(blockers),
            )
        )
    if gate == "template_safe_but_not_runnable":
        actions.append(
            _action(
                "provider_pilot",
                "warning",
                "provider_template_not_runnable",
                "Create approved provider-pilot config copy after advisor sign-off",
                "Copy the template, add budget cap, stop conditions, approval block; then run preflight on the copy.",
            )
        )
    if gate == "ready_for_dry_run":
        actions.append(
            _action(
                "provider_pilot",
                "informational",
                "provider_dry_run_ready",
                "Provider config approved for dry run",
                "Run dry-run preflight and review outputs before any live run.",
            )
        )
    if gate == "ready_for_live_run":
        actions.append(
            _action(
                "provider_pilot",
                "informational",
                "provider_live_run_ready",
                "Provider config approved for live run",
                "Re-confirm budget and approval just before execution.",
            )
        )
    return actions


def _human_validation_actions(reports: Path) -> list[dict[str, Any]]:
    packet = _read(reports / "human_validation_dry_run_packet.json")
    if packet is None:
        return []
    return [
        _action(
            "human_validation",
            "warning",
            "human_validation_pending",
            "Run real human validation pilot when a frozen provider run exists",
            "Use the dry-run packet to validate the annotation flow; recruit annotators after provider pilot.",
        )
    ]


def _release_actions(reports: Path) -> list[dict[str, Any]]:
    payload = _read(reports / "release_readiness_report.json")
    if payload is None:
        return []
    verdicts = payload.get("verdicts") if isinstance(payload.get("verdicts"), dict) else {}
    actions: list[dict[str, Any]] = []
    if not verdicts.get("ready_for_public_release", False) and not verdicts.get("ready_for_release", False):
        actions.append(
            _action(
                "release",
                "warning",
                "release_not_ready",
                "Public release still blocked",
                "Resolve leakage, dataset quality, paper assets, and license issues before any public release.",
            )
        )
    return actions


def _paper_actions(reports: Path) -> list[dict[str, Any]]:
    payload = _read(reports / "paper_readiness/paper_readiness_map.json") or _read(reports / "paper_readiness_map.json")
    if payload is None:
        return []
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    blocked = int(summary.get("blocked") or 0)
    if blocked:
        return [
            _action(
                "paper",
                "warning",
                "paper_readiness_blocked_sections",
                f"{blocked} paper sections blocked",
                "Method-only paper readiness is acceptable; empirical sections remain blocked until provider-backed runs exist.",
                impact_count=blocked,
            )
        ]
    return []


def _action(
    phase: str,
    severity: str,
    action_id: str,
    title: str,
    how: str,
    *,
    why: str | None = None,
    impact_count: int = 0,
    depends_on: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": f"act_{phase}_{action_id}",
        "phase": phase,
        "severity": severity,
        "title": title,
        "how": how,
        "why": why,
        "impact_count": impact_count,
        "depends_on": depends_on or [],
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
