#!/usr/bin/env python3
"""Lint paper sources for risky or unsupported wording."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PAPER_ROOT = REPO_ROOT / "paper" / "latexpaper"

# (kind, pattern, draft_severity, submission_severity) — severity: warn | error
RISKY_PATTERNS: tuple[tuple[str, re.Pattern[str], str, str], ...] = (
    ("prove", re.compile(r"\bprove[sd]?\b", re.I), "warn", "error"),
    ("guarantee", re.compile(r"\bguarantee[sd]?\b", re.I), "warn", "error"),
    ("state_of_the_art", re.compile(r"\bstate[- ]of[- ]the[- ]art\b|\bSOTA\b", re.I), "warn", "error"),
    ("neurips_ready", re.compile(r"NeurIPS[- ]ready|submission[- ]ready", re.I), "warn", "error"),
    ("significant_improvement", re.compile(r"\bsignificant(ly)?\s+(better|improve|outperform)", re.I), "warn", "error"),
    ("human_validated_unqualified", re.compile(r"\bhuman[- ]validated\b(?!\s+subset|\s+sample|\s+protocol)", re.I), "warn", "error"),
    ("real_world_agents", re.compile(r"\breal[- ]world agents\b|\bdeployed agents\b", re.I), "warn", "warn"),
    ("causal_effect_unbounded", re.compile(r"\bcausal effect\b(?!\s+of\s+the\s+intervention|\s+estimation|\s+in\s+this)", re.I), "warn", "error"),
    ("frontier_models", re.compile(r"\bfrontier models\b|\bGPT-4\b|\bClaude\b|\bGemini\b", re.I), "warn", "warn"),
    ("ranking_claim", re.compile(r"\boutperforms all\b|\bbest agent\b|\bhighest score\b", re.I), "warn", "error"),
    ("result_placeholder", re.compile(r"\[(?:N|M|K|X|rho)\]"), "warn", "error"),
    ("not_yet_run_results", re.compile(r"not yet run", re.I), "warn", "error"),
)

RESULT_SECTIONS = {
    Path("sections/07_results.tex"),
    Path("sections/08_human_validation.tex"),
    Path("sections/09_ablations.tex"),
    Path("generated/07_results.tex"),
}


@dataclass(frozen=True)
class LintFinding:
    kind: str
    path: Path
    line_number: int
    line: str
    severity: str

    def format(self, root: Path) -> str:
        rel = self.path.relative_to(root)
        return f"{rel}:{self.line_number}: {self.severity}: {self.kind}: {self.line.strip()[:120]}"


def lint_paper_claims(
    paper_root: str | Path = PAPER_ROOT,
    *,
    mode: str = "draft",
) -> list[LintFinding]:
    root = Path(paper_root).resolve()
    findings: list[LintFinding] = []
    for path in sorted(root.rglob("*")):
        if path.suffix not in {".tex", ".md"}:
            continue
        rel = path.relative_to(root)
        text = path.read_text(encoding="utf-8")
        for line_number, line in enumerate(text.splitlines(), 1):
            for kind, pattern, draft_sev, sub_sev in RISKY_PATTERNS:
                if not pattern.search(line):
                    continue
                severity = sub_sev if mode == "submission" else draft_sev
                # Placeholders in abstract/setup are OK in draft if labeled planned
                if kind == "result_placeholder" and mode == "draft" and rel == Path("generated/00_abstract.tex"):
                    severity = "warn"
                if kind == "not_yet_run_results" and rel not in RESULT_SECTIONS and mode == "draft":
                    continue
                findings.append(LintFinding(kind, path, line_number, line, severity))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lint paper for risky or unsupported claims.")
    parser.add_argument("--mode", choices=["draft", "submission"], default="draft")
    parser.add_argument("--paper-root", default=str(PAPER_ROOT))
    args = parser.parse_args(argv)

    findings = lint_paper_claims(args.paper_root, mode=args.mode)
    errors = [f for f in findings if f.severity == "error"]
    warnings = [f for f in findings if f.severity == "warn"]

    for finding in warnings:
        print(f"WARNING: {finding.format(Path(args.paper_root))}")
    for finding in errors:
        print(f"ERROR: {finding.format(Path(args.paper_root))}")

    if errors:
        print(f"lint_paper_claims failed: {len(errors)} error(s), {len(warnings)} warning(s)")
        return 1
    if warnings:
        print(f"lint_paper_claims passed with {len(warnings)} warning(s) ({args.mode} mode)")
    else:
        print(f"lint_paper_claims OK ({args.mode} mode)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
