"""Honest publication-tier readiness (no-run, no empirical claims)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from causal_agent_bench.safety.common import section_markdown, write_dual_report

PUBLICATION_TIERS = (
    "arxiv_method_only",
    "workshop_short",
    "colm_acl_emnlp_main",
    "neurips_ed",
    "tmlr",
)


def build_publication_readiness_report(
    repo_root: str | Path,
    *,
    reports_dir: str | Path = "reports",
    output_dir: str | Path = "reports/publication_readiness",
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    reports = Path(reports_dir)
    if not reports.is_absolute():
        reports = root / reports
    state = _evidence_state(root, reports)
    tiers = [_tier_row(name, state) for name in PUBLICATION_TIERS]
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": (
            "Static publication-tier assessment only. Does not claim the paper is complete, "
            "submittable, or empirically validated."
        ),
        "current_evidence": state,
        "tiers": tiers,
        "summary": {
            "empirical_paper_ready": False,
            "method_only_preprint_ready": state["method_docs_complete"] and state["paper_eligible_runs"] == 0,
            "any_main_venue_ready": False,
            "claims_promoted": False,
        },
        "verdicts": {
            "arxiv_method_only": tiers[0]["ready"],
            "workshop": tiers[1]["ready"],
            "colm_acl_emnlp": tiers[2]["ready"],
            "neurips_ed": tiers[3]["ready"],
            "tmlr": tiers[4]["ready"],
        },
    }
    out = Path(output_dir)
    if not out.is_absolute():
        out = root / out
    md = publication_readiness_markdown(payload)
    md_path, json_path = write_dual_report(
        stem="publication_readiness",
        payload=payload,
        markdown=md,
        output_dir=out,
    )
    payload["report_paths"] = {"markdown": str(md_path), "json": str(json_path)}
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def publication_readiness_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Publication Readiness",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        payload["scope"],
        "",
        "**Disclaimer:** No empirical claims exist yet. C1–C8 and C10 are unsupported. C9 is engineering-only.",
        "",
        section_markdown(
            "Current Evidence",
            [
                f"- Paper-eligible runs: {payload['current_evidence']['paper_eligible_runs']}",
                f"- Eligible paper assets: {payload['current_evidence']['eligible_paper_assets']}",
                f"- Provider pilot completed: {payload['current_evidence']['provider_pilot_complete']}",
                f"- Human validation complete: {payload['current_evidence']['human_validation_complete']}",
            ],
        ),
        "## Tier Assessment",
        "",
        "| Tier | Ready? | Rationale | Missing for this tier |",
        "|---|:---:|---|---|",
    ]
    for tier in payload["tiers"]:
        missing = "; ".join(tier["missing"]) if tier["missing"] else "(none for method-only tiers)"
        lines.append(
            f"| {tier['tier']} | `{tier['ready']}` | {tier['rationale']} | {missing} |"
        )
    lines.extend(
        [
            "",
            "## Honest Summary",
            "",
            "- The repository is **benchmark infrastructure** with strong no-run governance, not an empirical paper.",
            "- A **methods/architecture preprint** (arXiv) may be feasible if wording stays method-only.",
            "- **Workshop/main conference** tiers require provider evidence, human validation, and supported claims.",
            "",
        ]
    )
    return "\n".join(lines)


def _tier_row(tier: str, state: dict[str, Any]) -> dict[str, Any]:
    empirical = state["paper_eligible_runs"] > 0 and state["eligible_paper_assets"] > 0
    human = state["human_validation_complete"]
    leakage_clear = state["leakage_blocker_clusters"] == 0

    if tier == "arxiv_method_only":
        ready = state["method_docs_complete"] and not empirical
        missing = []
        if not state["method_docs_complete"]:
            missing.append("complete method/design documentation")
        if empirical:
            missing.append("remove unsupported empirical language")
        rationale = "Method-only framing is possible if abstract/conclusion avoid performance claims."
        return {"tier": "arXiv (method-only preprint)", "ready": ready, "rationale": rationale, "missing": missing}

    if tier == "workshop_short":
        ready = empirical and human and leakage_clear
        missing = _empirical_gaps(state)
        return {
            "tier": "Workshop (4–8 pages + results)",
            "ready": ready,
            "rationale": "Typically needs a small completed pilot and honest limitations.",
            "missing": missing,
        }

    if tier == "colm_acl_emnlp_main":
        missing = [
            *_empirical_gaps(state),
            "multi-model main benchmark",
            "human validation for C10",
            "reviewer-grade reproducibility bundle",
        ]
        return {
            "tier": "COLM / ACL / EMNLP (main)",
            "ready": False,
            "rationale": "Requires full empirical study, not current scaffold state.",
            "missing": missing,
        }

    if tier == "neurips_ed":
        missing = [
            *_empirical_gaps(state),
            "artifact evaluation bundle",
            "frozen public dataset release",
        ]
        return {
            "tier": "NeurIPS E&D / benchmark track",
            "ready": False,
            "rationale": "Needs reproducible artifact + completed benchmark runs.",
            "missing": missing,
        }

    if tier == "tmlr":
        missing = [*_empirical_gaps(state), "open review cycle with complete evidence trail"]
        return {
            "tier": "TMLR",
            "ready": False,
            "rationale": "Needs reproducibility, complete experiments, and supported claims over time.",
            "missing": missing,
        }

    return {"tier": tier, "ready": False, "rationale": "Unknown tier.", "missing": ["classification"]}


def _empirical_gaps(state: dict[str, Any]) -> list[str]:
    gaps = []
    if state["paper_eligible_runs"] == 0:
        gaps.append("paper-eligible provider/main runs")
    if state["eligible_paper_assets"] == 0:
        gaps.append("eligible paper assets with metadata")
    if not state["human_validation_complete"]:
        gaps.append("human validation annotations + agreement (C3, C10)")
    if state["leakage_blocker_clusters"] > 0:
        gaps.append(f"clear {state['leakage_blocker_clusters']} true leakage blocker cluster(s)")
    if not state["provider_pilot_complete"]:
        gaps.append("completed reviewed provider pilot")
    gaps.append("supported C1–C8 claims in ledger")
    return gaps


def _evidence_state(root: Path, reports: Path) -> dict[str, Any]:
    run_health = _find_json(reports, "run_health_report.json") or {}
    assets = _find_json(reports, "paper_asset_eligibility.json") or {}
    leakage = _find_json(reports, "static_leakage_report.json") or {}
    summary_raw = leakage.get("summary")
    summary = summary_raw if isinstance(summary_raw, dict) else {}
    return {
        "paper_eligible_runs": int((run_health.get("summary") or {}).get("paper_eligible_count") or 0),
        "eligible_paper_assets": int(assets.get("eligible_count") or 0),
        "leakage_blocker_clusters": int(summary.get("blocker_cluster_count") or 0),
        "human_validation_complete": _human_validation_complete(root),
        "provider_pilot_complete": False,
        "method_docs_complete": (root / "docs/DO_NOT_OVERCLAIM.md").exists()
        and (root / "paper/EVIDENCE_GAP_MAP.md").exists(),
    }


def _human_validation_complete(root: Path) -> bool:
    hv = root / "data/human_validation"
    return any(p.name.startswith("completed") for p in hv.glob("**/*") if p.is_file()) if hv.exists() else False


def _find_json(reports: Path, filename: str) -> dict[str, Any] | None:
    direct = reports / filename
    if direct.exists():
        return _read_json(direct)
    for path in sorted(reports.glob(f"**/{filename}")) if reports.exists() else []:
        return _read_json(path)
    return None


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    return payload if isinstance(payload, dict) else None
