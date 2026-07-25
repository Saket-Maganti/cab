from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from causal_agent_bench.safety.common import (
    PLACEHOLDER_TEXT_MARKERS,
    asset_has_placeholder_content,
    read_meta_sidecar,
    section_markdown,
    strict_bool,
    write_dual_report,
)

SCAN_DIRS = ("tables", "figures", "paper/latexpaper/generated")
KEY_TABLES = ("table2", "table3", "table4", "table5")
RESULT_TEX_HINTS = (
    "result",
    "human_validation",
    "human-validation",
    "ablation",
    "experiment",
    "benchmark_stats",
    "main_agent_performance",
)
EMPIRICAL_TEX_MARKERS = (
    "we show",
    "our experiments",
    "results suggest",
    "mean absolute degradation",
    "spearman",
    "human validation",
    "ablation",
    "main result",
    "\\claimref",
    "\\input{../../tables",
    "\\includegraphics",
)
RECOMMENDATIONS = (
    "safe_for_paper_main_results",
    "safe_only_for_appendix_engineering_validation",
    "not_safe_to_use",
    "needs_verified_provider_run",
    "needs_human_validation",
    "needs_metadata_review",
)


def validate_paper_asset_eligibility(
    repo_root: str | Path,
    *,
    output_dir: str | Path = "reports",
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    out = Path(output_dir)
    if not out.is_absolute():
        out = root / out

    assets: list[dict[str, Any]] = []
    for rel_dir in SCAN_DIRS:
        base = root / rel_dir
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if path.is_dir() or path.name.endswith(".meta.json"):
                continue
            if path.suffix.lower() not in {".csv", ".md", ".tex", ".png", ".pdf", ".json", ".txt"}:
                continue
            assets.append(_classify_asset(path, root))

    for section_dir in (root / "paper/latexpaper/sections",):
        if section_dir.exists():
            for tex in sorted(section_dir.glob("*.tex")):
                assets.append(_classify_generated_tex(tex, root))

    flagged = [a for a in assets if a["classification"] != "eligible_for_paper_claims"]
    classification_counts: dict[str, int] = {}
    for a in assets:
        key = str(a.get("classification") or "unknown")
        classification_counts[key] = classification_counts.get(key, 0) + 1
    eligible_count = sum(1 for a in assets if a["classification"] == "eligible_for_paper_claims")
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": "Static paper asset eligibility check only; no claim is promoted or asset exported.",
        "summary": {
            "total_assets": len(assets),
            "eligible_count": eligible_count,
            "flagged_count": len(flagged),
            "classification_counts": classification_counts,
        },
        "verdicts": {
            "any_eligible_assets": eligible_count > 0,
            "all_flagged": eligible_count == 0,
            "needs_review": len(flagged) > 0,
        },
        "total_assets": len(assets),
        "eligible_count": eligible_count,
        "flagged_count": len(flagged),
        "assets": assets,
        "flagged_assets": flagged,
    }
    md = _format_markdown(payload)
    md_path, json_path = write_dual_report(
        stem="paper_asset_eligibility",
        payload=payload,
        markdown=md,
        output_dir=out,
    )
    payload["report_paths"] = {"markdown": str(md_path), "json": str(json_path)}
    return payload


def _classify_asset(path: Path, repo_root: Path) -> dict[str, Any]:
    rel = str(path.relative_to(repo_root))
    meta = read_meta_sidecar(path.with_suffix(path.suffix + ".meta.json"))
    if meta is None:
        meta_path = path.parent / f"{path.stem}.meta.json"
        meta = read_meta_sidecar(meta_path)

    classification = "unknown_needs_review"
    recommendation = "needs_metadata_review"
    reasons: list[str] = []

    if meta is None:
        classification = "missing_metadata"
        reasons.append("no .meta.json sidecar")
    else:
        eligibility = meta.get("eligibility", {})
        if strict_bool(meta.get("placeholder")):
            classification = "placeholder"
            reasons.append("meta.placeholder=true")
        elif meta.get("empirical_result") is False or (
            "scientific_evidence" in meta and not strict_bool(meta.get("scientific_evidence"))
        ):
            classification = "engineering_only"
            reasons.append("meta marks non-scientific/placeholder")
        elif strict_bool(eligibility.get("engineering_only")) or (
            "eligible_for_paper_claims" in eligibility
            and not strict_bool(eligibility.get("eligible_for_paper_claims"))
        ):
            classification = "engineering_only"
            reasons.append("eligibility.engineering_only or not eligible_for_paper_claims")
        elif strict_bool(eligibility.get("eligible_for_paper_claims")):
            classification = "eligible_for_paper_claims"
            recommendation = "safe_for_paper_main_results"
        else:
            classification = "unknown_needs_review"
            reasons.append("ambiguous eligibility metadata")

    if asset_has_placeholder_content(path):
        if classification == "eligible_for_paper_claims":
            classification = "unsafe_for_results_section"
        elif classification == "unknown_needs_review":
            classification = "placeholder"
        reasons.append("file content contains placeholder/blocked language")

    name_lower = path.name.lower()
    if any(t in name_lower for t in KEY_TABLES) and classification in {
        "placeholder",
        "engineering_only",
        "missing_metadata",
    }:
        recommendation = "not_safe_to_use"
    elif "human_validation" in name_lower or "table5" in name_lower:
        if classification != "eligible_for_paper_claims":
            recommendation = "needs_human_validation"
    elif classification == "engineering_only":
        recommendation = "safe_only_for_appendix_engineering_validation"
    elif classification == "placeholder":
        recommendation = "not_safe_to_use"
    elif classification == "eligible_for_paper_claims":
        recommendation = "safe_for_paper_main_results"
    elif classification == "missing_metadata":
        recommendation = "needs_metadata_review"

    if classification == "eligible_for_paper_claims" and any(
        m in (meta or {}).get("caption", "").lower() for m in PLACEHOLDER_TEXT_MARKERS
    ):
        classification = "unsafe_for_results_section"
        recommendation = "not_safe_to_use"
        reasons.append("caption contains placeholder language")

    return {
        "path": rel,
        "asset_type": path.suffix.lstrip("."),
        "classification": classification,
        "recommendation": recommendation,
        "reasons": reasons,
        "has_meta": meta is not None,
        "meta_summary": _meta_summary(meta),
    }


def _classify_generated_tex(path: Path, repo_root: Path) -> dict[str, Any]:
    rel = str(path.relative_to(repo_root))
    text = path.read_text(encoding="utf-8").lower()
    rel_lower = rel.lower()
    classification = "missing_metadata"
    recommendation = "needs_metadata_review"
    reasons: list[str] = ["generated/section TeX has no eligibility metadata"]

    empirical_or_results = any(marker in text for marker in EMPIRICAL_TEX_MARKERS) or any(
        hint in rel_lower for hint in RESULT_TEX_HINTS
    )
    if empirical_or_results:
        classification = "unsafe_for_results_section"
        recommendation = "needs_metadata_review"
        reasons.append("TeX contains empirical/results-like content without eligible metadata")
    elif not text.strip() or "\\section" in text or "\\subsection" in text:
        classification = "unknown_needs_review"
        recommendation = "needs_metadata_review"
        reasons.append("non-results boilerplate still cannot support paper claims without metadata")

    if any(marker in text for marker in PLACEHOLDER_TEXT_MARKERS):
        classification = "placeholder"
        recommendation = "not_safe_to_use"
        reasons.append("generated TeX contains placeholder/blocked language")
    if classification != "placeholder" and (
        "human_validation" in rel_lower or "human-validation" in rel_lower or "human validation" in text
    ):
        if "not complete" in text or "not yet" in text or "placeholder" in text:
            classification = "needs_human_validation"
            recommendation = "needs_human_validation"
            reasons.append("human-validation text is incomplete or placeholder")
    if classification != "placeholder" and "ablation" in rel_lower and ("not yet run" in text or "placeholder" in text):
        classification = "placeholder"
        recommendation = "not_safe_to_use"
        reasons.append("ablation result text is not complete")
    if classification != "placeholder" and "human validation" in rel_lower and (
        "not complete" in text or "not yet" in text
    ):
        classification = "needs_human_validation"
        recommendation = "needs_human_validation"
    return {
        "path": rel,
        "asset_type": "tex_generated",
        "classification": classification,
        "recommendation": recommendation,
        "reasons": reasons,
        "has_meta": False,
        "meta_summary": {},
    }


def _meta_summary(meta: dict[str, Any] | None) -> dict[str, Any]:
    if not meta:
        return {}
    elig = meta.get("eligibility") or {}
    return {
        "placeholder": meta.get("placeholder"),
        "scientific_evidence": meta.get("scientific_evidence", elig.get("eligible_for_paper_claims")),
        "evidence_scope": elig.get("evidence_scope") or meta.get("evidence_scope"),
        "engineering_only": elig.get("engineering_only"),
    }


def _format_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Paper asset eligibility",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "Zero-compute scan of tables/, figures/, and generated LaTeX. Missing metadata is never eligible.",
        "",
        section_markdown(
            "Summary",
            [
                f"- Total assets scanned: {payload['total_assets']}",
                f"- Eligible for paper claims: {payload['eligible_count']}",
                f"- Flagged: {payload['flagged_count']}",
            ],
        ),
        "## Flagged assets\n",
    ]
    for asset in payload["flagged_assets"]:
        lines.append(f"### `{asset['path']}`")
        lines.append(f"- Classification: `{asset['classification']}`")
        lines.append(f"- Recommendation: `{asset['recommendation']}`")
        if asset["reasons"]:
            lines.append(f"- Reasons: {'; '.join(asset['reasons'])}")
        lines.append("")
    return "\n".join(lines)
