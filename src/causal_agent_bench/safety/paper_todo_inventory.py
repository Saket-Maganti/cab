from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from causal_agent_bench.safety.common import (
    PLACEHOLDER_TEXT_MARKERS,
    section_markdown,
    write_dual_report,
)

SCAN_PATHS = (
    "paper/latexpaper/main.tex",
    "paper/latexpaper/sections",
    "paper/latexpaper/generated",
    "paper/PAPER_STATUS.md",
    "paper/EVIDENCE_GAP_MAP.md",
)

SECTION_MAP = {
    "abstract": "abstract",
    "introduction": "introduction",
    "related": "related work",
    "benchmark": "benchmark design",
    "intervention": "interventional framework",
    "metric": "metrics",
    "experiment": "experiments",
    "result": "results",
    "human": "human validation",
    "ablation": "ablations",
    "limitation": "limitations",
    "ethic": "ethics/reproducibility",
    "repro": "ethics/reproducibility",
    "conclusion": "conclusion",
    "generated": "generated files",
}

PATTERNS: list[tuple[str, str, str]] = [
    (r"\bTODO\b", "TODO", "cleanup"),
    (r"\bFIXME\b", "FIXME", "blocker_before_submission"),
    (r"\bplaceholder\b", "placeholder", "blocker_before_empirical_claims"),
    (r"not yet run", "not yet run", "blocker_before_empirical_claims"),
    (r"\bblocked\b", "blocked", "blocker_before_empirical_claims"),
    (r"\bplanned\b", "planned", "cleanup"),
    (r"(\[(N|M|K|X|rho)\]|\bTODO_NUM\b|\bFIXME_NUM\b|\bXX\b|\bXXX\b|\?\?\?|\bTBD\b|\bTBA\b)", "numeric_placeholder", "cleanup"),
    (r"missing compensation", "missing_compensation_text", "blocker_before_submission"),
    (r"human validation.*(not complete|not yet)", "missing_human_validation", "blocker_before_empirical_claims"),
    (r"ablation.*(not yet|placeholder)", "missing_ablations", "blocker_before_empirical_claims"),
    (r"(no final|missing) results?", "missing_results", "blocker_before_empirical_claims"),
    (r"\\includegraphics\{[^}]+\}", "figure_include", "optional"),
    (r"Table~?\\ref|Figure~?\\ref", "table_figure_reference", "optional"),
]

EMPIRICAL_OVERCLAIM = re.compile(
    r"\b(we show|our experiments demonstrate|significantly outperforms|state-of-the-art|main result)\b",
    re.IGNORECASE,
)


def build_paper_todo_inventory(
    repo_root: str | Path,
    *,
    output_dir: str | Path = "reports",
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    out = Path(output_dir)
    if not out.is_absolute():
        out = root / out

    items: list[dict[str, Any]] = []
    for rel in SCAN_PATHS:
        path = root / rel
        if path.is_file():
            items.extend(_scan_file(path, root))
        elif path.is_dir():
            for file in sorted(path.rglob("*")):
                if file.suffix in {".tex", ".md", ".txt"}:
                    items.extend(_scan_file(file, root))

    missing_refs = _find_missing_includes(root, items)
    items.extend(missing_refs)

    by_section: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        by_section.setdefault(item["section"], []).append(item)

    severity_counts = _count_by(items, "severity")
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": "Static paper TODO/placeholder inventory only; no claim is promoted.",
        "summary": {
            "total_items": len(items),
            "blockers": severity_counts.get("blocker", 0),
            "warnings": severity_counts.get("warning", 0),
            "informational": severity_counts.get("informational", 0),
            "by_severity": severity_counts,
            "section_count": len(by_section),
        },
        "verdicts": {
            "todo_clean": severity_counts.get("blocker", 0) == 0 and severity_counts.get("warning", 0) == 0,
            "any_blocker_todos": severity_counts.get("blocker", 0) > 0,
        },
        "total_items": len(items),
        "by_severity": severity_counts,
        "by_section": {k: len(v) for k, v in sorted(by_section.items())},
        "items": items,
    }
    md = _format_markdown(payload, by_section)
    md_path, json_path = write_dual_report(
        stem="paper_todo_inventory",
        payload=payload,
        markdown=md,
        output_dir=out,
    )
    payload["report_paths"] = {"markdown": str(md_path), "json": str(json_path)}
    return payload


def _scan_file(path: Path, repo_root: Path) -> list[dict[str, Any]]:
    rel = str(path.relative_to(repo_root))
    section = _infer_section(rel)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []
    lines = text.splitlines()
    found: list[dict[str, Any]] = []
    for idx, line in enumerate(lines, 1):
        lower = line.lower()
        for pattern, kind, severity in PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                found.append(
                    {
                        "file": rel,
                        "line": idx,
                        "section": section,
                        "kind": kind,
                        "severity": severity,
                        "excerpt": line.strip()[:200],
                    }
                )
        if (
            EMPIRICAL_OVERCLAIM.search(line)
            and not _quoted_policy_example(rel, line)
            and not any(m in lower for m in PLACEHOLDER_TEXT_MARKERS)
        ):
            found.append(
                {
                    "file": rel,
                    "line": idx,
                    "section": section,
                    "kind": "empirical_claim_without_eligible_evidence",
                    "severity": "blocker_before_empirical_claims",
                    "excerpt": line.strip()[:200],
                }
            )
    return found


def _quoted_policy_example(rel: str, line: str) -> bool:
    lower = line.lower()
    rel_lower = rel.lower()
    if "evidence_gap_map.md" in rel_lower and (
        "forbidden wording" in lower or "avoid" in lower or "example" in lower
    ):
        return True
    return any(
        marker in lower
        for marker in (
            "forbidden wording",
            "allowed wording",
            "do not write",
            "avoid phrases",
            "examples of overclaiming",
        )
    )


def _infer_section(rel_path: str) -> str:
    lower = rel_path.lower()
    if "generated" in lower:
        return "generated files"
    for key, label in SECTION_MAP.items():
        if key in lower:
            return label
    if "main.tex" in lower:
        return "experiments"
    return "unknown"


def _find_missing_includes(root: Path, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    extra: list[dict[str, Any]] = []
    figures_dir = root / "paper/latexpaper/figures"
    for tex in (root / "paper/latexpaper").rglob("*.tex"):
        for match in re.finditer(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", tex.read_text(encoding="utf-8")):
            target = match.group(1)
            if not target.endswith((".pdf", ".png", ".jpg")):
                target = f"{target}.pdf"
            candidate = root / "paper/latexpaper" / target
            if not candidate.exists() and not (figures_dir / Path(target).name).exists():
                extra.append(
                    {
                        "file": str(tex.relative_to(root)),
                        "line": 0,
                        "section": "experiments",
                        "kind": "missing_figure_include",
                        "severity": "blocker_before_submission",
                        "excerpt": f"Missing graphics: {target}",
                    }
                )
    return extra


def _count_by(items: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        counts[item[key]] = counts.get(item[key], 0) + 1
    return counts


def _format_markdown(payload: dict[str, Any], by_section: dict[str, list[dict[str, Any]]]) -> str:
    lines = [
        "# Paper TODO / placeholder inventory",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        section_markdown(
            "Summary",
            [
                f"- Total items: {payload['total_items']}",
                f"- By severity: {payload['by_severity']}",
            ],
        ),
    ]
    for section, section_items in sorted(by_section.items()):
        lines.append(f"## {section}\n")
        for item in section_items[:30]:
            loc = f"{item['file']}:{item['line']}" if item["line"] else item["file"]
            lines.append(
                f"- [{item['severity']}] **{item['kind']}** @ `{loc}` — {item['excerpt']}"
            )
        if len(section_items) > 30:
            lines.append(f"- ... and {len(section_items) - 30} more")
        lines.append("")
    return "\n".join(lines)
