"""Build manual-review queue for high-risk intervention families."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from causal_agent_bench.safety.common import section_markdown, write_dual_report
from causal_agent_bench.safety.intervention_isolation import (
    audit_intervention_isolation_instances,
    load_intervention_taxonomy,
)

HIGH_RISK_FAMILIES: dict[str, dict[str, str]] = {
    "long_horizon_dependency": {
        "review_reason": "Step-dependency edits can broaden difficulty or alter success criteria.",
        "reviewer_question": "Does the intervention add only a dependency marker without changing the target answer or instruction?",
        "failure_mode": "Agent stops after early sufficient-looking evidence.",
        "claim_dependency": "C2, C8, C10",
    },
    "memory_corruption": {
        "review_reason": "Memory edits can leak labels or change visible task semantics.",
        "reviewer_question": "Is the corrupted memory plausible, visible to the agent, and answer-preserving per taxonomy?",
        "failure_mode": "Agent trusts stale memory over tool evidence.",
        "claim_dependency": "C2, C3, C10",
    },
    "observation_conflict": {
        "review_reason": "Conflicting observations may become the only usable evidence.",
        "reviewer_question": "Can a competent agent resolve the conflict using remaining clean evidence?",
        "failure_mode": "Agent picks wrong branch or ignores contradiction.",
        "claim_dependency": "C2, C3, C10",
    },
    "tool_failure": {
        "review_reason": "Deterministic tool failure may remove all evidence paths.",
        "reviewer_question": "Is recovery still possible with remaining tools and is the gold answer policy explicit?",
        "failure_mode": "Agent does not retry, switch tools, or report limitation.",
        "claim_dependency": "C2, C7, C10",
    },
    "tool_removal": {
        "review_reason": "Removing a tool can change answer policy from factual to limitation-aware.",
        "reviewer_question": "Is the expected answer change documented when removal blocks the original solution path?",
        "failure_mode": "Agent hallucinates missing-tool results.",
        "claim_dependency": "C2, C7, C10",
    },
    "premature_success_signal": {
        "review_reason": "Metadata-only success cues may be invisible or too strong.",
        "reviewer_question": "Is the misleading success signal visible in the agent observation stream?",
        "failure_mode": "Agent stops before required validation.",
        "claim_dependency": "C3, C8, C10",
    },
    "noisy_observation": {
        "review_reason": "Alias cluster for distractor/noisy evidence families.",
        "reviewer_question": "Is distractor evidence plausible but non-decisive, without answer leakage?",
        "failure_mode": "Agent overweights noisy snippet.",
        "claim_dependency": "C2, C3, C10",
    },
    "stale_memory": {
        "review_reason": "Alias cluster for stale memory / stale web content interventions.",
        "reviewer_question": "Is stale content distinguishable from answer-changing updates?",
        "failure_mode": "Agent treats stale value as current.",
        "claim_dependency": "C2, C10",
    },
    "stopping_recovery": {
        "review_reason": "Recovery target may be underspecified.",
        "reviewer_question": "Is there a clear recoverable path after the early-completion trap?",
        "failure_mode": "Agent fails to resume after false completion cue.",
        "claim_dependency": "C3, C5, C8, C10",
    },
    "web_conflicting_page": {
        "review_reason": "Web conflict can become answer-changing without explicit rationale.",
        "reviewer_question": "Does the conflict preserve the clean gold answer policy?",
        "failure_mode": "Agent trusts wrong page.",
        "claim_dependency": "C2, C10",
    },
}

FAMILY_ALIASES: dict[str, str] = {
    "distractor_evidence": "noisy_observation",
    "web_irrelevant_search_result": "noisy_observation",
    "web_stale_page": "stale_memory",
    "tool_corruption": "observation_conflict",
    "ambiguous_instruction": "observation_conflict",
}


def build_high_risk_intervention_queue(
    repo_root: str | Path,
    *,
    benchmark_dir: str | Path | None = None,
    taxonomy_path: str | Path | None = None,
    output_dir: str | Path = "reports/high_risk_interventions",
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    out = Path(output_dir)
    if not out.is_absolute():
        out = root / out
    base = Path(benchmark_dir) if benchmark_dir else root / "data/processed/pilot_v0_1"
    if not base.is_absolute():
        base = root / base
    instances_path = base / "instances.jsonl"
    taxonomy, taxonomy_meta = load_intervention_taxonomy(taxonomy_path, repo_root=root)
    isolation = audit_intervention_isolation_instances(instances_path, repo_root=root, taxonomy_path=taxonomy_path)
    queue = _build_queue(isolation, taxonomy, dataset=_rel(base, root))
    clusters = _cluster_queue(queue)
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": (
            "Static high-risk intervention manual-review queue only. "
            "No auto-approval, no claim promotion, no provider execution."
        ),
        "dataset": _rel(base, root),
        "instances_path": str(instances_path),
        "taxonomy": taxonomy_meta,
        "summary": {
            "queue_item_count": len(queue),
            "cluster_count": len(clusters),
            "pilot_blocker_count": sum(1 for row in queue if row["pilot_blocker"]),
            "main_benchmark_blocker_count": sum(1 for row in queue if row["main_benchmark_blocker"]),
            "requires_human_validation_count": sum(1 for row in queue if row["human_validation_required"]),
        },
        "verdicts": {
            "auto_approval_forbidden": True,
            "claims_supported": False,
            "C3_blocked": True,
            "C10_blocked": True,
        },
        "clusters": clusters,
        "manual_review_queue": queue,
    }
    md = high_risk_queue_markdown(payload)
    md_path, json_path = write_dual_report(
        stem="high_risk_intervention_queue",
        payload=payload,
        markdown=md,
        output_dir=out,
    )
    csv_path = out / "high_risk_intervention_queue.csv"
    _write_csv(csv_path, queue)
    payload["report_paths"] = {
        "markdown": str(md_path),
        "json": str(json_path),
        "csv": str(csv_path),
    }
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def _build_queue(
    isolation: dict[str, Any],
    taxonomy: dict[str, dict[str, Any]],
    *,
    dataset: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for record in isolation.get("pairs", []):
        itype = str(record.get("intervention_type") or "unknown")
        canonical = FAMILY_ALIASES.get(itype, itype)
        if canonical not in HIGH_RISK_FAMILIES and not taxonomy.get(itype, {}).get("requires_human_review"):
            continue
        meta = HIGH_RISK_FAMILIES.get(canonical) or HIGH_RISK_FAMILIES.get(itype) or {
            "review_reason": "Taxonomy marks intervention as requires_human_review.",
            "reviewer_question": "Does this pair isolate exactly one intended causal factor?",
            "failure_mode": "Underspecified isolation risk.",
            "claim_dependency": "C10",
        }
        pair_id = str(record.get("pair_id") or record.get("intervention_id") or "")
        if pair_id in seen:
            continue
        seen.add(pair_id)
        severity = str(record.get("severity") or "warning")
        status = str(record.get("isolation_status") or "needs_review")
        pilot_blocker = severity == "blocker" or status in {"multi_factor_change", "missing_clean_pair", "needs_review"}
        main_blocker = pilot_blocker or canonical in {
            "long_horizon_dependency",
            "memory_corruption",
            "observation_conflict",
            "tool_failure",
            "tool_removal",
        }
        tax_row = taxonomy.get(itype, {})
        rows.append(
            {
                "queue_id": f"hr_{pair_id or itype}",
                "pair_id": pair_id,
                "intervention_type": itype,
                "canonical_family": canonical,
                "dataset": dataset,
                "isolation_status": status,
                "severity": severity,
                "risk_score": record.get("risk_score", 0),
                "review_reason": meta["review_reason"],
                "reviewer_question": meta["reviewer_question"],
                "failure_mode_tested": meta["failure_mode"],
                "paper_claim_dependency": meta["claim_dependency"],
                "human_validation_required": bool(tax_row.get("requires_human_review", True)),
                "pilot_blocker": pilot_blocker,
                "main_benchmark_blocker": main_blocker,
                "required_action": _required_action(status, severity),
                "auto_approve_forbidden": True,
            }
        )
    rows.sort(key=lambda row: (-int(row.get("risk_score") or 0), row["intervention_type"], row["pair_id"]))
    if not rows:
        for family, meta in HIGH_RISK_FAMILIES.items():
            if family in FAMILY_ALIASES.values():
                continue
            rows.append(
                {
                    "queue_id": f"hr_family_{family}",
                    "pair_id": "",
                    "intervention_type": family,
                    "canonical_family": family,
                    "dataset": dataset,
                    "isolation_status": "taxonomy_review",
                    "severity": "warning",
                    "risk_score": 50,
                    "review_reason": meta["review_reason"],
                    "reviewer_question": meta["reviewer_question"],
                    "failure_mode_tested": meta["failure_mode"],
                    "paper_claim_dependency": meta["claim_dependency"],
                    "human_validation_required": True,
                    "pilot_blocker": False,
                    "main_benchmark_blocker": True,
                    "required_action": "Manual expert review before main-benchmark freeze.",
                    "auto_approve_forbidden": True,
                }
            )
    return rows


def _cluster_queue(queue: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = {}
    for row in queue:
        key = row["canonical_family"]
        buckets.setdefault(key, []).append(row)
    clusters = []
    for family, members in sorted(buckets.items()):
        clusters.append(
            {
                "cluster_id": f"cluster_{family}",
                "intervention_type": family,
                "item_count": len(members),
                "pilot_blocker_count": sum(1 for row in members if row["pilot_blocker"]),
                "main_benchmark_blocker_count": sum(1 for row in members if row["main_benchmark_blocker"]),
                "review_reason": members[0]["review_reason"],
                "reviewer_question": members[0]["reviewer_question"],
                "required_action": members[0]["required_action"],
                "sample_pair_ids": [row["pair_id"] for row in members[:5] if row["pair_id"]],
            }
        )
    return clusters


def high_risk_queue_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# High-Risk Intervention Review Queue",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        payload["scope"],
        "",
        section_markdown(
            "Summary",
            [
                f"- Dataset: `{payload['dataset']}`",
                f"- Queue items: {summary['queue_item_count']}",
                f"- Clusters: {summary['cluster_count']}",
                f"- Pilot blockers: {summary['pilot_blocker_count']}",
                f"- Main-benchmark blockers: {summary['main_benchmark_blocker_count']}",
                f"- Human validation required: {summary['requires_human_validation_count']}",
            ],
        ),
        "## Clusters",
        "",
    ]
    if not payload["clusters"]:
        lines.append("- (none)")
    for cluster in payload["clusters"]:
        lines.append(
            f"- `{cluster['intervention_type']}` items={cluster['item_count']} "
            f"pilot_blockers={cluster['pilot_blocker_count']} "
            f"main_blockers={cluster['main_benchmark_blocker_count']}: {cluster['review_reason']}"
        )
    lines.extend(["", "## Manual review queue (top 25)", ""])
    for row in payload["manual_review_queue"][:25]:
        lines.append(
            f"- `{row['intervention_type']}` `{row['pair_id'] or 'taxonomy'}` "
            f"pilot={row['pilot_blocker']} main={row['main_benchmark_blocker']}: {row['reviewer_question']}"
        )
    lines.append("")
    return "\n".join(lines)


def _required_action(status: str, severity: str) -> str:
    if severity == "blocker":
        return "Fix isolation violation or document rationale before pilot/provider use."
    if status == "multi_factor_change":
        return "Reduce to single-factor change or reclassify intervention family."
    if status == "needs_review":
        return "Expert manual review; do not auto-approve."
    return "Optional pre-main review."


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    import csv

    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)
