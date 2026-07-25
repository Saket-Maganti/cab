"""Map paper sections to conservative readiness and evidence state."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PAPER_SECTIONS = [
    "abstract",
    "introduction",
    "related work",
    "benchmark design",
    "intervention framework",
    "metrics",
    "experiments",
    "results",
    "human validation",
    "ablations",
    "limitations",
    "ethics/reproducibility",
    "conclusion",
    "appendix",
]


def build_paper_readiness_map(
    repo_root: str | Path,
    *,
    reports_dir: str | Path = "reports",
    output_dir: str | Path = "reports/paper_readiness",
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    reports = Path(reports_dir)
    if not reports.is_absolute():
        reports = root / reports
    out = Path(output_dir)
    if not out.is_absolute():
        out = root / out
    out.mkdir(parents=True, exist_ok=True)
    state = _evidence_state(root, reports)
    sections = [_section_map(section, state) for section in PAPER_SECTIONS]
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": "Static paper readiness map only; no claims are promoted and no empirical results are filled.",
        "current_evidence": state,
        "sections": sections,
        "summary": {
            "ready_method_only": sum(1 for row in sections if row["readiness_status"] == "ready_method_only"),
            "blocked": sum(1 for row in sections if row["readiness_status"] == "blocked"),
            "needs_evidence": sum(1 for row in sections if row["readiness_status"] == "needs_evidence"),
            "claims_promoted": False,
        },
    }
    md = paper_readiness_map_markdown(payload)
    md_path = out / "paper_readiness_map.md"
    json_path = out / "paper_readiness_map.json"
    md_path.write_text(md, encoding="utf-8")
    payload["report_paths"] = {"markdown": str(md_path), "json": str(json_path)}
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def paper_readiness_map_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Paper Readiness Map",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        payload["scope"],
        "",
        "## Sections",
        "",
        "| Section | Status | Current Evidence | Next Action |",
        "|---|---|---|---|",
    ]
    for section in payload["sections"]:
        lines.append(
            f"| {section['section']} | `{section['readiness_status']}` | "
            f"{section['current_evidence']} | {section['next_action']} |"
        )
    lines.extend(
        [
            "",
            "## Evidence Boundary",
            "",
            "- C1-C8 and C10 remain planned / unsupported.",
            "- C9 remains engineering-only.",
            "- Results, human validation, and ablations remain blocked until eligible evidence exists.",
            "- Method sections may use method-only wording.",
            "",
            "## Allowed / Forbidden Wording Examples",
            "",
            "### Abstract",
            "",
            "- **Allowed:** \"We introduce a benchmark scaffold for evaluating tool-using agents under causal interventions…\"",
            "- **Forbidden:** \"We show that agents fail under intervention X with accuracy Y…\"",
            "",
            "### Introduction",
            "",
            "- **Allowed:** Motivation, skill decomposition, planned evaluation protocol.",
            "- **Forbidden:** \"Our experiments demonstrate…\", unsupported rankings.",
            "",
            "### Results",
            "",
            "- **Allowed:** \"Results are not yet available; this section is intentionally blocked.\"",
            "- **Forbidden:** Any performance table, degradation %, or model ranking.",
            "",
            "### Conclusion",
            "",
            "- **Allowed:** Summarize design contributions and list evidence gaps honestly.",
            "- **Forbidden:** \"We validated human agreement\" or \"models ranked by ACRS\" without data.",
            "- **Forbidden:** \"NeurIPS-ready\", \"validated benchmark\", or \"state-of-the-art\" without Tier 4 evidence.",
            "",
            "### Limitations",
            "",
            "- **Allowed:** No provider evidence yet; synthetic tasks; static-only validation limits.",
            "- **Forbidden:** Implying missing studies were completed.",
            "",
            "## NeurIPS paper firewall summary",
            "",
            "- Empirical contribution (C1–C8): **blocked** — 0 paper-eligible runs.",
            "- Human validation (C3, C10): **blocked** — no completed annotations.",
            "- Release contribution: **blocked** — public v1.0 not ready.",
            "- Safe reviewer path: Tier 0–1 static/no-run only; provider run requires approval.",
            "",
            "Canonical artifact docs: `docs/NEURIPS_ARTIFACT_READINESS_CHECKLIST.md`, "
            "`docs/REPRODUCIBILITY_TIERS.md`.",
            "",
        ]
    )
    return "\n".join(lines)


def _section_map(section: str, state: dict[str, Any]) -> dict[str, Any]:
    empirical_blocked = state["paper_eligible_runs"] == 0 or state["eligible_paper_assets"] == 0
    human_blocked = not state["human_validation_complete"]
    base = {
        "section": section,
        "claims_referenced": [],
        "required_evidence": "method description only",
        "current_evidence": "static no-run assets only",
        "allowed_wording": "Describe benchmark design, validation policy, and evidence gaps.",
        "forbidden_wording": "Do not claim model performance, robustness, ranking, or validated human agreement.",
        "next_action": "Keep method-only wording.",
    }
    if section in {"benchmark design", "intervention framework", "metrics", "related work", "appendix"}:
        return {**base, "readiness_status": "ready_method_only"}
    if section in {"limitations", "ethics/reproducibility"}:
        return {
            **base,
            "readiness_status": "ready_method_only",
            "allowed_wording": "Accurately disclose no provider evidence, unsupported claims, and static-validation limits.",
            "forbidden_wording": "Do not imply missing evidence has been collected.",
            "next_action": "Keep disclosures synchronized with no-run reports.",
        }
    if section in {"results", "experiments"}:
        return {
            **base,
            "readiness_status": "blocked" if empirical_blocked else "needs_review",
            "claims_referenced": [*(f"C{i}" for i in range(1, 9))],
            "required_evidence": "paper-eligible provider/main runs and eligible paper assets",
            "current_evidence": f"paper_eligible_runs={state['paper_eligible_runs']}, eligible_assets={state['eligible_paper_assets']}",
            "allowed_wording": "State that empirical results are not yet available.",
            "forbidden_wording": "Do not include performance tables, degradation claims, or rankings.",
            "next_action": "Collect eligible evidence only after provider-pilot approval and post-run review.",
        }
    if section == "human validation":
        return {
            **base,
            "readiness_status": "blocked" if human_blocked else "needs_review",
            "claims_referenced": ["C10"],
            "required_evidence": "completed human annotation artifacts and agreement analysis",
            "current_evidence": "human validation not complete" if human_blocked else "human validation artifacts need review",
            "allowed_wording": "Describe protocol/templates only.",
            "forbidden_wording": "Do not claim agreement, expert validation, or C10 support.",
            "next_action": "Complete and audit human validation before claim promotion.",
        }
    if section == "ablations":
        return {
            **base,
            "readiness_status": "blocked" if empirical_blocked else "needs_review",
            "claims_referenced": ["ablation claims"],
            "required_evidence": "eligible ablation runs and reviewed paper assets",
            "current_evidence": f"paper_eligible_runs={state['paper_eligible_runs']}",
            "allowed_wording": "Mention planned ablations only.",
            "forbidden_wording": "Do not report ablation effects.",
            "next_action": "Run ablations only after main evidence policy is satisfied.",
        }
    if section in {"abstract", "conclusion", "introduction"}:
        return {
            **base,
            "readiness_status": "needs_evidence" if empirical_blocked else "needs_review",
            "claims_referenced": [*(f"C{i}" for i in range(1, 9)), "C10"],
            "required_evidence": "supported claim ledger entries for any empirical language",
            "current_evidence": "C1-C8/C10 planned / unsupported; C9 engineering-only",
            "allowed_wording": "Use method-only contribution language and explicit evidence caveats.",
            "forbidden_wording": "Do not summarize unsupported empirical improvements or validation results.",
            "next_action": "Rewrite any empirical-sounding language as planned or blocked.",
        }
    return {**base, "readiness_status": "needs_review"}


def _evidence_state(root: Path, reports: Path) -> dict[str, Any]:
    run_health = _find_json(reports, "run_health_report.json") or {}
    assets = _find_json(reports, "paper_asset_eligibility.json") or {}
    claims = _find_json(reports, "claim_evidence_matrix.json") or _read_json(root / "docs/claim_ledger.json") or {}
    statuses = {str(row.get("claim_id")): str(row.get("status")) for row in claims.get("claims", []) if isinstance(row, dict)}
    return {
        "paper_eligible_runs": int((run_health.get("summary") or {}).get("paper_eligible_count") or 0),
        "eligible_paper_assets": int(assets.get("eligible_count") or 0),
        "C1_C8": {f"C{i}": statuses.get(f"C{i}", "planned") for i in range(1, 9)},
        "C9": statuses.get("C9", "engineering_only"),
        "C10": statuses.get("C10", "planned"),
        "human_validation_complete": _human_validation_complete(root, reports),
        "claims_promoted_by_readiness_map": False,
    }


def _human_validation_complete(root: Path, reports: Path) -> bool:
    report = _find_json(reports, "human_validation_summary.json")
    if report and report.get("completed"):
        return True
    hv_dir = root / "data/human_validation"
    if not hv_dir.exists():
        return False
    return any(path.name.startswith("completed") for path in hv_dir.glob("**/*") if path.is_file())


def _find_json(reports: Path, filename: str) -> dict[str, Any] | None:
    direct = reports / filename
    if direct.exists():
        return _read_json(direct)
    for path in sorted(reports.glob(f"**/{filename}")) if reports.exists() else []:
        return _read_json(path)
    return None


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None
