"""Conservative benchmark validity scorecard (static, no-run)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from causal_agent_bench.safety.common import write_dual_report
from causal_agent_bench.safety.gold_output_validation import build_gold_output_validation
from causal_agent_bench.safety.high_risk_intervention_queue import (
    build_high_risk_intervention_queue,
)
from causal_agent_bench.safety.intervention_isolation import build_intervention_isolation_report
from causal_agent_bench.safety.provider_pilot_preflight import build_provider_pilot_preflight
from causal_agent_bench.safety.static_leakage import build_static_leakage_report
from causal_agent_bench.safety.tool_schema_validation import build_tool_schema_validation


def build_validity_scorecard(
    repo_root: str | Path,
    *,
    benchmark_dir: str | Path | None = None,
    taxonomy_path: str | Path | None = None,
    config_path: str | Path = "configs/provider_pilot_tiny_template.yaml",
    output_dir: str | Path = "reports/validity_scorecard",
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    out = Path(output_dir)
    if not out.is_absolute():
        out = root / out
    leakage = build_static_leakage_report(root, benchmark_dir=benchmark_dir, output_dir=out / "_scratch_leakage")
    isolation = build_intervention_isolation_report(
        root,
        benchmark_dir=benchmark_dir,
        taxonomy_path=taxonomy_path,
        output_dir=out / "_scratch_isolation",
    )
    gold = build_gold_output_validation(
        root,
        benchmark_dir=benchmark_dir,
        taxonomy_path=taxonomy_path,
        output_dir=out / "_scratch_gold",
    )
    tools = build_tool_schema_validation(root, benchmark_dir=benchmark_dir, output_dir=out / "_scratch_tools")
    high_risk = build_high_risk_intervention_queue(
        root,
        benchmark_dir=benchmark_dir,
        taxonomy_path=taxonomy_path,
        output_dir=out / "_scratch_high_risk",
    )
    preflight = build_provider_pilot_preflight(
        root,
        config_path=config_path,
        output_dir=out / "_scratch_preflight",
        reports_dir=out / "_scratch_preflight",
    )
    dimensions = _score_dimensions(root, leakage, isolation, gold, tools, high_risk, preflight)
    overall = _overall_score(dimensions)
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": (
            "Conservative static validity scorecard only. "
            "Scores reflect infrastructure readiness, not empirical benchmark results. "
            "No claims are promoted."
        ),
        "overall_score": overall,
        "overall_band": _band(overall),
        "evidence_state": {
            "paper_eligible_runs": 0,
            "eligible_empirical_assets": 0,
            "human_annotations_exist": _human_annotations_exist(root),
            "claims_supported": False,
        },
        "dimensions": dimensions,
        "verdicts": {
            "valid_for_infrastructure_review": overall >= 55,
            "valid_for_provider_pilot": all(
                row["score"] >= 50
                for row in dimensions
                if row["id"] in {"leakage_cleanliness", "intervention_isolation", "provider_pilot_readiness"}
            )
            and leakage.get("summary", {}).get("blocker_cluster_count", 1) == 0,
            "valid_for_main_benchmark": False,
            "valid_for_public_release": False,
            "empirical_claims_allowed": False,
        },
        "blockers": [row for row in dimensions if row["score"] < 40],
    }
    md = validity_scorecard_markdown(payload)
    md_path, json_path = write_dual_report(
        stem="validity_scorecard",
        payload=payload,
        markdown=md,
        output_dir=out,
    )
    payload["report_paths"] = {"markdown": str(md_path), "json": str(json_path)}
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def _score_dimensions(
    root: Path,
    leakage: dict[str, Any],
    isolation: dict[str, Any],
    gold: dict[str, Any],
    tools: dict[str, Any],
    high_risk: dict[str, Any],
    preflight: dict[str, Any],
) -> list[dict[str, Any]]:
    leak_blockers = int(leakage.get("summary", {}).get("blocker_cluster_count", 0))
    iso_score = float(isolation.get("isolation_score") or isolation.get("summary", {}).get("isolation_score") or 0)
    gold_blockers = int(gold.get("summary", {}).get("blockers", 0))
    gold_warnings = int(gold.get("summary", {}).get("warnings", 0))
    tool_blockers = int(tools.get("summary", {}).get("blockers", 0))
    pilot_hr = int(high_risk.get("summary", {}).get("pilot_blocker_count", 0))
    gate = str(preflight.get("gate_status") or preflight.get("summary", {}).get("gate_status") or "unknown")
    hv_ready = _human_validation_protocol_ready(root)
    main_frozen = (root / "data/frozen/main_v0.1").exists() or (root / "data/frozen/main_200").exists()
    release_ready = False

    return [
        _dim(
            "leakage_cleanliness",
            "Leakage cleanliness",
            95 if leak_blockers == 0 else max(0, 40 - leak_blockers * 15),
            f"blocker_cluster_count={leak_blockers}",
            "Re-run static leakage after any dataset edit.",
            leak_blockers > 0,
        ),
        _dim(
            "split_integrity",
            "Split integrity",
            75 if (root / "data/frozen/pilot_v0.1/splits.json").exists() else 45,
            "pilot_v0.1 frozen splits present" if (root / "data/frozen/pilot_v0.1/splits.json").exists() else "main splits not release-frozen",
            "Freeze main benchmark with disjoint split audit.",
            not (root / "data/frozen/pilot_v0.1/splits.json").exists(),
        ),
        _dim(
            "intervention_isolation",
            "Intervention isolation",
            min(90, max(20, int(iso_score))),
            f"isolation_score={iso_score:.1f}",
            "Clear high-risk manual-review queue before main freeze.",
            iso_score < 60 or pilot_hr > 0,
        ),
        _dim(
            "gold_output_consistency",
            "Gold-output consistency",
            max(15, 85 - gold_blockers * 20 - min(30, gold_warnings * 2)),
            f"blockers={gold_blockers} warnings={gold_warnings}",
            "Manual-review gold queue; do not auto-fix ambiguous answers.",
            gold_blockers > 0,
        ),
        _dim(
            "tool_schema_consistency",
            "Tool-schema consistency",
            max(20, 90 - tool_blockers * 25),
            f"blockers={tool_blockers}",
            "Resolve tool schema mismatches in processed datasets.",
            tool_blockers > 0,
        ),
        _dim(
            "human_validation_readiness",
            "Human-validation readiness",
            55 if hv_ready and not _human_annotations_exist(root) else (70 if _human_annotations_exist(root) else 35),
            "protocol/templates ready; annotations missing" if not _human_annotations_exist(root) else "annotations present — needs audit",
            "Complete C3/C10 annotation packets after provider pilot.",
            not _human_annotations_exist(root),
        ),
        _dim(
            "provider_pilot_readiness",
            "Provider-pilot readiness",
            60 if gate == "template_safe_but_not_runnable" else 30,
            f"gate_status={gate}",
            "Signed approvals + APPROVED config before live pilot.",
            gate != "template_safe_but_not_runnable",
        ),
        _dim(
            "main_benchmark_readiness",
            "Main-benchmark readiness",
            25 if not main_frozen else 45,
            "main_200/main_v0_1_500 not frozen" if not main_frozen else "main frozen but HR queue may remain",
            "Freeze main_v0_1_500 after gold triage + human audit.",
            True,
        ),
        _dim(
            "release_readiness",
            "Release readiness",
            20 if not release_ready else 50,
            "public v1.0 blocked",
            "Ship release bundle only after main evidence policy met.",
            True,
        ),
    ]


def _dim(
    dim_id: str,
    label: str,
    score: int,
    why: str,
    upgrade: str,
    blocked: bool,
) -> dict[str, Any]:
    score = max(0, min(100, int(score)))
    return {
        "id": dim_id,
        "label": label,
        "score": score,
        "band": _band(score),
        "why": why,
        "blocker": blocked,
        "upgrade_needed": upgrade,
        "supports_empirical_claims": False,
    }


def _overall_score(dimensions: list[dict[str, Any]]) -> int:
    if not dimensions:
        return 0
    return int(sum(row["score"] for row in dimensions) / len(dimensions))


def _band(score: int) -> str:
    if score >= 80:
        return "strong_infrastructure"
    if score >= 60:
        return "adequate_scaffold"
    if score >= 40:
        return "needs_work"
    return "blocked"


def _human_validation_protocol_ready(root: Path) -> bool:
    return (root / "docs/HUMAN_VALIDATION_MASTER_PROTOCOL.md").exists() or (
        root / "docs/HUMAN_VALIDATION_PROTOCOL.md"
    ).exists()


def _human_annotations_exist(root: Path) -> bool:
    hv = root / "data/human_validation"
    if not hv.exists():
        return False
    return any(p.name.startswith("completed") for p in hv.rglob("*") if p.is_file())


def validity_scorecard_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Validity Scorecard",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        payload["scope"],
        "",
        f"**Overall score:** {payload['overall_score']}/100 ({payload['overall_band']})",
        "",
        "## Dimensions",
        "",
        "| Dimension | Score | Band | Blocker | Why | Upgrade needed |",
        "|---|---:|---|---|---|---|",
    ]
    for row in payload["dimensions"]:
        lines.append(
            f"| {row['label']} | {row['score']} | {row['band']} | {row['blocker']} | "
            f"{row['why']} | {row['upgrade_needed']} |"
        )
    lines.extend(
        [
            "",
            "## Evidence boundary",
            "",
            "- Empirical claims (C1–C8): **not supported** by this scorecard.",
            "- Human validation claims (C3, C10): **blocked** until real annotations exist.",
            "- This scorecard measures static validity infrastructure only.",
            "",
        ]
    )
    return "\n".join(lines)
