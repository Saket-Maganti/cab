from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from causal_agent_bench.claim_ledger import (
    CLAIM_ARTIFACT_MAP,
    CLAIM_TEXT_BY_ID,
    CLAIM_VALIDATION_FILES,
    MOCK_STUB_DRY_EVIDENCE_MARKERS,
    SCIENTIFIC_CLAIMS_NO_MOCK_SUPPORT,
    load_ledger,
)
from causal_agent_bench.safety.common import (
    asset_has_placeholder_content,
    classify_run_entry,
    load_run_index_entries,
    read_meta_sidecar,
    strict_bool,
    write_dual_report,
)

CLAIM_SECTIONS: dict[str, list[str]] = {
    "C1": ["abstract", "introduction", "results", "conclusion"],
    "C2": ["results", "conclusion"],
    "C3": ["results", "human_validation"],
    "C4": ["results", "conclusion"],
    "C5": ["results", "ablations"],
    "C6": ["ablations", "results"],
    "C7": ["results"],
    "C8": ["results"],
    "C9": ["ethics/reproducibility", "limitations"],
    "C10": ["human_validation", "benchmark design", "results"],
}

ENGINEERING_ONLY_CLAIM = frozenset({"C9"})


def build_claim_evidence_matrix(
    repo_root: str | Path,
    *,
    ledger_path: str | Path = "docs/claim_ledger.json",
    results_root: str | Path = "results",
    output_dir: str | Path = "reports",
    write_tex: bool = True,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    out = Path(output_dir)
    if not out.is_absolute():
        out = root / out

    ledger = load_ledger(root / ledger_path)
    runs = [classify_run_entry(e, root) for e in load_run_index_entries(root, results_root=results_root)]
    eligible_runs = [r for r in runs if r["paper_eligible"]]
    asset_index = _index_assets(root)

    claims_out: list[dict[str, Any]] = []
    for claim in ledger["claims"]:
        claim_id = str(claim["claim_id"])
        row = _evaluate_claim(claim_id, claim, eligible_runs, runs, asset_index, root)
        claims_out.append(row)

    statuses = {row["claim_id"]: row.get("status") for row in claims_out}
    status_counts: dict[str, int] = {}
    for status in statuses.values():
        key = str(status or "unknown")
        status_counts[key] = status_counts.get(key, 0) + 1
    summary = {
        "eligible_run_count": len(eligible_runs),
        "claim_count": len(claims_out),
        "status_counts": status_counts,
        "supported_count": status_counts.get("supported", 0),
        "supported_claims": sorted([cid for cid, s in statuses.items() if s == "supported"]),
        "engineering_only_count": status_counts.get("engineering_only", 0),
        "planned_count": status_counts.get("planned", 0),
    }
    verdicts = {
        "any_supported_empirical": any(statuses.get(f"C{i}") == "supported" for i in range(1, 9)),
        "C9_engineering_only_acceptable": statuses.get("C9") == "engineering_only",
        "all_other_claims_planned_or_unsupported": all(
            statuses.get(f"C{i}") in {"planned", None, "weakened", "rejected"} for i in range(1, 9)
        )
        and statuses.get("C10") in {"planned", None, "weakened", "rejected"},
    }
    payload: dict[str, Any] = {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": (
            "Static claim-evidence matrix only. No claim is promoted by this report; "
            "supported status requires verified provider-backed runs."
        ),
        "summary": summary,
        "verdicts": verdicts,
        "eligible_run_count": len(eligible_runs),
        "claims": claims_out,
    }
    md = _format_markdown(payload)
    md_path, json_path = write_dual_report(
        stem="claim_evidence_matrix",
        payload=payload,
        markdown=md,
        output_dir=out,
    )
    payload["report_paths"] = {"markdown": str(md_path), "json": str(json_path)}
    if write_tex:
        tex_path = root / "paper/latexpaper/generated/claim_evidence_matrix.tex"
        tex_path.parent.mkdir(parents=True, exist_ok=True)
        tex_path.write_text(_format_tex(payload), encoding="utf-8")
        payload["report_paths"]["tex"] = str(tex_path)
    return payload


def _index_assets(repo_root: Path) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for folder in ("tables", "figures"):
        base = repo_root / folder
        if not base.exists():
            continue
        for meta_path in base.glob("*.meta.json"):
            rel = str(meta_path.relative_to(repo_root))
            index[rel] = {"path": rel, "meta": read_meta_sidecar(meta_path)}
            stem = meta_path.name.replace(".meta.json", "")
            for ext in (".csv", ".png", ".pdf", ".md", ".tex"):
                asset = meta_path.parent / f"{stem}{ext}"
                if asset.exists():
                    index[str(asset.relative_to(repo_root))] = index[rel]
    return index


def _evaluate_claim(
    claim_id: str,
    claim: dict[str, Any],
    eligible_runs: list[dict[str, Any]],
    all_runs: list[dict[str, Any]],
    asset_index: dict[str, dict[str, Any]],
    repo_root: Path,
) -> dict[str, Any]:
    ledger_status = claim.get("status", "planned")
    required = claim.get("required_evidence", "")
    linked_artifacts = list(claim.get("linked_tables_figures") or CLAIM_ARTIFACT_MAP.get(claim_id, []))
    validation_files = list(claim.get("linked_validation_files") or CLAIM_VALIDATION_FILES.get(claim_id, []))

    eligible_artifacts: list[str] = []
    ineligible_artifacts: list[str] = []
    for rel in linked_artifacts:
        eligible, reason = artifact_claim_eligibility(rel, repo_root, asset_index=asset_index)
        if eligible:
            eligible_artifacts.append(rel)
        else:
            ineligible_artifacts.append(f"{rel} ({reason})")

    available_evidence = list(claim.get("current_evidence_paths", [])) + [
        r["run_path"] for r in eligible_runs
    ]
    blocking: list[str] = list(claim.get("blocking_items", []))

    derived_status = _derive_status(
        claim_id=claim_id,
        ledger_status=ledger_status,
        eligible_runs=eligible_runs,
        eligible_artifacts=eligible_artifacts,
        validation_files=validation_files,
        repo_root=repo_root,
    )

    section_allowed = _section_allowed(claim_id, derived_status)
    if derived_status not in {"supported", "partially_supported"}:
        blocking.append("No verified complete provider/main scientific evidence")

    return {
        "claim_id": claim_id,
        "claim_text": claim.get("claim_text") or CLAIM_TEXT_BY_ID.get(claim_id, ""),
        "ledger_status": ledger_status,
        "status": derived_status,
        "required_evidence": required,
        "available_evidence": available_evidence,
        "eligible_artifacts": eligible_artifacts,
        "ineligible_artifacts": ineligible_artifacts,
        "blocking_missing_items": blocking,
        "affected_sections": CLAIM_SECTIONS.get(claim_id, []),
        "section_allowed": section_allowed,
        "linked_runs_scientific": [r["run_id"] for r in eligible_runs],
        "linked_runs_ineligible": [
            r["run_id"]
            for r in all_runs
            if not r["paper_eligible"] and r["classification"] not in {"unknown_needs_review"}
        ][:5],
    }


def _derive_status(
    *,
    claim_id: str,
    ledger_status: str,
    eligible_runs: list[dict[str, Any]],
    eligible_artifacts: list[str],
    validation_files: list[str],
    repo_root: Path,
) -> str:
    if claim_id in ENGINEERING_ONLY_CLAIM:
        if eligible_runs:
            return "partially_supported"
        return "engineering_only"

    if claim_id in SCIENTIFIC_CLAIMS_NO_MOCK_SUPPORT:
        if not eligible_runs:
            if ledger_status == "planned":
                return "planned"
            if ledger_status == "engineering_only":
                return "engineering_only"
            return "blocked"
        missing_hv = [
            vf
            for vf in validation_files
            if not (repo_root / vf).exists() or _artifact_incomplete(repo_root / vf)
        ]
        if claim_id in {"C3", "C10"} and missing_hv:
            return "partially_supported" if eligible_artifacts else "blocked"
        if eligible_artifacts and not missing_hv:
            return "partially_supported"
        return "blocked"

    return "blocked"


def artifact_claim_eligibility(
    rel: str,
    repo_root: Path,
    *,
    asset_index: dict[str, dict[str, Any]] | None = None,
) -> tuple[bool, str]:
    path = repo_root / rel
    if not path.exists():
        return False, "missing"

    index = asset_index or _index_assets(repo_root)
    record = index.get(rel)
    meta = record.get("meta") if record else None
    if meta is None:
        meta = read_meta_sidecar(path.with_suffix(path.suffix + ".meta.json"))
    if meta is None:
        meta = read_meta_sidecar(path.parent / f"{path.stem}.meta.json")
    if not meta:
        return False, "missing metadata"

    if strict_bool(meta.get("placeholder")) or asset_has_placeholder_content(path):
        return False, "placeholder"

    eligibility = meta.get("eligibility") or {}
    eligible_value = eligibility.get("eligible_for_paper_claims", meta.get("eligible_for_paper_claims"))
    if not strict_bool(eligible_value):
        return False, "not eligible_for_paper_claims"

    scientific_value = meta.get("scientific_evidence", eligibility.get("scientific_evidence"))
    if scientific_value is not None and not strict_bool(scientific_value):
        return False, "scientific_evidence=false"

    if strict_bool(meta.get("engineering_only")) or strict_bool(eligibility.get("engineering_only")):
        return False, "engineering-only"

    combined = " ".join(
        str(value or "").lower()
        for value in (
            meta.get("evidence_scope"),
            eligibility.get("evidence_scope"),
            meta.get("evidence_level"),
            meta.get("deployment_class"),
            meta.get("source_classification"),
            meta.get("source_run_classification"),
            meta.get("provenance"),
            meta.get("status"),
        )
    )
    if any(marker in combined for marker in MOCK_STUB_DRY_EVIDENCE_MARKERS):
        return False, "mock/stub/dry metadata"
    if any(marker in combined for marker in ("engineering", "incomplete", "interrupted", "oracle", "synthetic")):
        return False, "non-scientific metadata"
    if strict_bool(meta.get("not_real_llm_behavior")):
        return False, "not_real_llm_behavior=true"
    if str(meta.get("deployment_class") or "").lower() == "mock_diagnostic_only":
        return False, "mock diagnostic deployment"

    return True, "eligible"


def _artifact_incomplete(path: Path) -> bool:
    if not path.exists():
        return True
    if path.suffix == ".csv":
        text = path.read_text(encoding="utf-8").lower()
        return "not yet run" in text or "placeholder" in text
    return False


def _section_allowed(claim_id: str, status: str) -> dict[str, bool]:
    fully_supported = status == "supported"
    empirical_ok = status in {"supported", "partially_supported"}
    partially_only = status == "partially_supported"
    engineering_ok = status in {"engineering_only", "partially_supported"}
    return {
        "abstract": fully_supported and claim_id not in ENGINEERING_ONLY_CLAIM,
        "introduction": empirical_ok or claim_id in ENGINEERING_ONLY_CLAIM,
        "results": empirical_ok,
        "human_validation": empirical_ok and claim_id in {"C3", "C10"},
        "ablations": empirical_ok and claim_id in {"C5", "C6"},
        "conclusion": fully_supported and claim_id not in ENGINEERING_ONLY_CLAIM,
        "limitations/future_work_only": (
            not empirical_ok
            or status in {"planned", "blocked", "engineering_only"}
            or partially_only
        ),
        "ethics/reproducibility": claim_id in ENGINEERING_ONLY_CLAIM and engineering_ok,
    }


def _format_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    verdicts = payload.get("verdicts") or {}
    lines = [
        "# Claim–evidence matrix",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        f"Eligible scientific runs in index: {payload['eligible_run_count']}",
        "",
        "Conservative matrix: C1–C8 and C10 require verified non-mock complete provider/main evidence.",
        "",
        "## Evidence-to-paper firewall",
        "",
        "- **Paper-eligible runs:** "
        f"{summary.get('eligible_run_count', payload['eligible_run_count'])} "
        "(must be >0 before any empirical claim promotion).",
        "- **Supported empirical claims:** "
        f"{summary.get('supported_claims') or []} "
        f"(count={summary.get('supported_count', 0)}).",
        "- **Planned claims:** C1–C8, C10 must remain `planned` until provider/main audit passes.",
        "- **C9 only:** `engineering_only` — reproducibility scaffolding, not LLM benchmark results.",
        "- **Abstract/conclusion guard:** No performance numbers, rankings, or human-agreement language.",
        "- **Provider path:** Requires signed approval + `*_APPROVED.yaml`; template alone is not runnable evidence.",
        "",
        "### NeurIPS reviewer checks",
        "",
        f"- any_supported_empirical: `{verdicts.get('any_supported_empirical', False)}`",
        f"- C9_engineering_only_acceptable: `{verdicts.get('C9_engineering_only_acceptable', False)}`",
        f"- all_other_claims_planned_or_unsupported: "
        f"`{verdicts.get('all_other_claims_planned_or_unsupported', False)}`",
        "",
        "See `docs/DO_NOT_OVERCLAIM.md` and `docs/REVIEWER_QUICKSTART_NEURIPS.md`.",
        "",
    ]
    for row in payload["claims"]:
        lines.append(f"## {row['claim_id']}: {row['claim_text']}")
        lines.append(f"- Status: **{row['status']}** (ledger: `{row['ledger_status']}`)")
        lines.append(f"- Blocking: {', '.join(row['blocking_missing_items'][:3]) or '(none listed)'}")
        lines.append(f"- Eligible artifacts: {', '.join(row['eligible_artifacts']) or '(none)'}")
        lines.append(f"- Ineligible: {', '.join(row['ineligible_artifacts'][:3]) or '(none)'}")
        allowed = [k for k, v in row["section_allowed"].items() if v]
        lines.append(f"- May appear in: {', '.join(allowed) or 'limitations/future work only'}")
        lines.append("")
    return "\n".join(lines)


def _format_tex(payload: dict[str, Any]) -> str:
    lines = [
        "% Auto-generated claim-evidence matrix — NOT FOR FINAL EMPIRICAL CLAIMS WITHOUT REVIEW",
        "\\begin{itemize}",
    ]
    for row in payload["claims"]:
        lines.append(
            f"  \\item \\textbf{{{row['claim_id']}}}: status={row['status']}; "
            f"eligible artifacts={len(row['eligible_artifacts'])}."
        )
    lines.append("\\end{itemize}\n")
    return "\n".join(lines)
