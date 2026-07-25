#!/usr/bin/env python3
"""Fast repository consistency audit — links, CLI, claims, evidence wording."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from causal_agent_bench.runners.index_runs import index_runs

OUT_DIR = ROOT / "audits" / "repo_consistency"
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
BACKTICK_PATH_RE = re.compile(
    r"`((?:configs|scripts|docs|handoff|paper|experiments|release|benchmark_specs)/[^\s`]+)`"
)
CLAIM_ID_RE = re.compile(r"\bC(?:[1-9]|10)\b")
SUBMISSION_READY_RE = re.compile(r"submission[- ]ready|submission_ready", re.I)
REAL_LLM_RE = re.compile(
    r"\b(?:frontier models?|SOTA|state[- ]of[- ]the[- ]art|GPT[- ]4|Claude|Gemini)\b.*"
    r"(?:achiev|outperform|rank|score|success rate|\d+%)",
    re.I,
)
PLACEHOLDER_RE = re.compile(r"\[(?:N|M|K|X|rho|domains|agents/models|main finding placeholder)\]")
CANONICAL_EVIDENCE_LEVELS = frozenset(
    {
        "dry_run",
        "stub_engineering",
        "mock_diagnostic",
        "local_model_preliminary",
        "free_tier_preliminary",
        "provider_pilot",
        "main_experiment",
        "human_validated",
        "submission_ready",
        "preliminary_or_engineering",
        "engineering_only",
        "engineering_scaffold",
        "deterministic_prototype",
        "local_preliminary",
        "main_experiment_ready",
    }
)
DOC_SCAN_PATHS = [
    ROOT / "README.md",
    ROOT / "docs" / "README.md",
    ROOT / "CONTRIBUTING.md",
    ROOT / "handoff" / "ADVISOR_DEMO_SCRIPT.md",
    ROOT / "handoff" / "PROFESSOR_READY_CHECKLIST.md",
]


ROOT_PREFIXES = ("configs/", "scripts/", "docs/", "handoff/", "paper/", "experiments/", "release/", "data/", "benchmark_specs/")


def _resolve_link(target: str, source: Path) -> Path | None:
    target = target.split("#", 1)[0].strip()
    if not target or target.startswith(("http://", "https://", "mailto:")):
        return None
    if any(target.startswith(prefix) for prefix in ROOT_PREFIXES):
        path = (ROOT / target).resolve()
    elif target.startswith("/"):
        path = Path(target)
    else:
        path = (source.parent / target).resolve()
    try:
        path.relative_to(ROOT)
    except ValueError:
        return None
    return path


def _extract_links(text: str, source: Path) -> list[tuple[str, Path]]:
    links: list[tuple[str, Path]] = []
    for match in LINK_RE.finditer(text):
        resolved = _resolve_link(match.group(1), source)
        if resolved is not None:
            links.append((match.group(1), resolved))
    for match in BACKTICK_PATH_RE.finditer(text):
        resolved = _resolve_link(match.group(1), source)
        if resolved is not None:
            links.append((match.group(1), resolved))
    return links


def _cli_commands() -> set[str]:
    proc = subprocess.run(
        [sys.executable, "-m", "causal_agent_bench", "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    commands: set[str] = set()
    for line in proc.stdout.splitlines():
        match = re.search(r"\{([^}]+)\}", line)
        if match and "validate" in match.group(1):
            commands.update(part.strip() for part in match.group(1).split(",") if part.strip())
            break
    if not commands:
        for line in proc.stdout.splitlines():
            line = line.strip()
            if line and not line.startswith("-") and "  " in line:
                commands.add(line.split()[0])
    return commands


def _readme_cli_mentions(readme_text: str) -> list[str]:
    pattern = re.compile(
        r"causal_agent_bench\s+(?:--help|[\w-]+)|python3?\s+-m\s+causal_agent_bench\s+([\w-]+)"
    )
    found: list[str] = []
    for match in pattern.finditer(readme_text):
        cmd = match.group(1) or "--help"
        if cmd != "--help":
            found.append(cmd)
    return sorted(set(found))


def _load_claim_ids() -> set[str]:
    ledger_path = ROOT / "docs" / "claim_ledger.json"
    if not ledger_path.exists():
        return set()
    data = json.loads(ledger_path.read_text(encoding="utf-8"))
    return {row["claim_id"] for row in data.get("claims", []) if "claim_id" in row}


def _load_readiness() -> dict:
    import importlib.util

    path = ROOT / "scripts" / "check_submission_readiness.py"
    spec = importlib.util.spec_from_file_location("check_submission_readiness", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.classify_readiness(ROOT)


def run_audit() -> dict:
    issues: list[dict] = []
    warnings: list[dict] = []
    stats = {
        "files_scanned": 0,
        "links_checked": 0,
        "broken_links": 0,
        "cli_commands_checked": 0,
    }

    claim_ids = _load_claim_ids()
    readiness = _load_readiness()
    submission_ready = readiness.get("submission_ready", False)
    cli_commands = _cli_commands()

    for doc_path in DOC_SCAN_PATHS:
        if not doc_path.exists():
            warnings.append({"kind": "missing_doc", "path": str(doc_path.relative_to(ROOT))})
            continue
        text = doc_path.read_text(encoding="utf-8", errors="replace")
        stats["files_scanned"] += 1
        rel = str(doc_path.relative_to(ROOT))

        for target, resolved in _extract_links(text, doc_path):
            stats["links_checked"] += 1
            if not resolved.exists():
                stats["broken_links"] += 1
                issues.append(
                    {
                        "kind": "broken_link",
                        "source": rel,
                        "target": target,
                        "resolved": str(resolved.relative_to(ROOT)),
                    }
                )

        if doc_path.name == "README.md" and doc_path.parent == ROOT:
            for cmd in _readme_cli_mentions(text):
                stats["cli_commands_checked"] += 1
                if cmd not in cli_commands:
                    issues.append({"kind": "unknown_cli_command", "source": rel, "command": cmd})

        for match in CLAIM_ID_RE.finditer(text):
            cid = match.group(0)
            if cid not in claim_ids:
                warnings.append({"kind": "unknown_claim_id", "source": rel, "claim_id": cid})

        if not submission_ready and SUBMISSION_READY_RE.search(text):
            if "not submission-ready" not in text.lower() and "not submission ready" not in text.lower():
                warnings.append(
                    {
                        "kind": "submission_ready_wording",
                        "source": rel,
                        "note": "mentions submission-ready while readiness checker says False",
                    }
                )

        if REAL_LLM_RE.search(text) and "forbidden" not in text.lower():
            if "what not to claim" not in text.lower() and "do not claim" not in text.lower():
                warnings.append(
                {
                    "kind": "possible_real_llm_claim",
                    "source": rel,
                    "note": "may imply real LLM performance; verify wording",
                }
            )

    runs = index_runs(ROOT / "results")
    for entry in runs:
        if entry["status"] in {"interrupted", "incomplete", "dry_run"} and entry.get("key_metrics"):
            warnings.append(
                {
                    "kind": "incomplete_run_has_metrics",
                    "run": entry.get("run_name"),
                    "status": entry["status"],
                }
            )

    paper_dir = ROOT / "paper"
    for tex in paper_dir.rglob("*.tex"):
        text = tex.read_text(encoding="utf-8", errors="replace")
        if PLACEHOLDER_RE.search(text):
            stats.setdefault("paper_placeholder_files", []).append(str(tex.relative_to(ROOT)))

    evidence_hits: dict[str, int] = {}
    for path in list((ROOT / "docs").rglob("*.md")) + list((ROOT / "configs").glob("*.yaml")):
        content = path.read_text(encoding="utf-8", errors="replace")
        for token in CANONICAL_EVIDENCE_LEVELS:
            if token in content:
                evidence_hits[token] = evidence_hits.get(token, 0) + 1

    non_canonical = []
    alias_pattern = re.compile(
        r"\b(?:zero_cost_preliminary|scientific_evidence|preliminary_only|stub_only)\b"
    )
    for path in (ROOT / "docs").rglob("*.md"):
        for match in alias_pattern.finditer(path.read_text(encoding="utf-8", errors="replace")):
            non_canonical.append({"path": str(path.relative_to(ROOT)), "token": match.group(0)})

    passed = not issues
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "passed": passed,
        "submission_ready": submission_ready,
        "readiness_classification": readiness.get("level"),
        "stats": stats,
        "issues": issues,
        "warnings": warnings,
        "evidence_level_usage": evidence_hits,
        "non_canonical_evidence_tokens": non_canonical[:20],
        "claim_ids_in_ledger": sorted(claim_ids),
    }


def _markdown_report(report: dict) -> str:
    lines = [
        "# Repository Consistency Audit",
        "",
        f"**Generated:** {report['generated_at']}",
        f"**Passed:** {report['passed']}",
        f"**Readiness:** {report['readiness_classification']} "
        f"(submission_ready={report['submission_ready']})",
        "",
        "## Stats",
        "",
        json.dumps(report["stats"], indent=2),
        "",
    ]
    if report["issues"]:
        lines.extend(["## Issues", ""])
        for item in report["issues"]:
            lines.append(f"- **{item['kind']}**: {json.dumps(item)}")
        lines.append("")
    if report["warnings"]:
        lines.extend(["## Warnings", ""])
        for item in report["warnings"][:50]:
            lines.append(f"- **{item['kind']}**: {json.dumps(item)}")
        if len(report["warnings"]) > 50:
            lines.append(f"- … and {len(report['warnings']) - 50} more")
        lines.append("")
    lines.extend(
        [
            "## Evidence level usage (sample counts)",
            "",
            json.dumps(report["evidence_level_usage"], indent=2, sort_keys=True),
            "",
            "## Non-canonical tokens (use aliases in policy)",
            "",
        ]
    )
    for item in report["non_canonical_evidence_tokens"]:
        lines.append(f"- `{item['token']}` in {item['path']}")
    if not report["non_canonical_evidence_tokens"]:
        lines.append("- none detected in docs scan")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit repo link/CLI/claim consistency.")
    parser.add_argument("--output-dir", default=str(OUT_DIR))
    args = parser.parse_args(argv)

    report = run_audit()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "repo_consistency_audit.json"
    md_path = out_dir / "REPO_CONSISTENCY_AUDIT.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(_markdown_report(report), encoding="utf-8")
    print(f"wrote {md_path}")
    print(f"wrote {json_path}")
    print(
        f"audit: {'PASS' if report['passed'] else 'FAIL'} "
        f"({len(report['issues'])} issues, {len(report['warnings'])} warnings)"
    )
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
