#!/usr/bin/env python3
"""Verify paper figure/table assets and run-evidence linkage."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PAPER_ROOT = REPO_ROOT / "paper" / "latexpaper"
DEFAULT_EVIDENCE = REPO_ROOT / "docs" / "PAPER_EVIDENCE_MAPPING.json"

INPUT_RE = re.compile(r"\\input\{([^}]+)\}")
INCLUDEGRAPHICS_RE = re.compile(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}")
REF_RE = re.compile(r"\\ref\{(fig|tab):([^}]+)\}")
LABEL_RE = re.compile(r"\\label\{(fig|tab):([^}]+)\}")

STANDARD_FIGURES = (
    "figures/figure2_clean_vs_intervention_success.png",
    "figures/figure3_intervention_family_degradation.png",
    "figures/figure4_ranking_instability.png",
    "figures/figure5_cost_vs_robustness.png",
    "figures/figure6_trajectory_failure_taxonomy.png",
)

STANDARD_TABLES = (
    "tables/table1_benchmark_statistics.csv",
    "tables/table2_main_agent_performance.csv",
    "tables/table3_intervention_family_performance.csv",
    "tables/table4_ablation_results.csv",
    "tables/table5_human_validation_agreement.csv",
)


def _collect_tex_paths(paper_root: Path) -> list[Path]:
    return sorted(paper_root.rglob("*.tex"))


def _resolve_input_path(paper_root: Path, target: str) -> Path:
    candidate = paper_root / target
    if candidate.suffix == "":
        for suffix in (".tex", ""):
            path = paper_root / f"{target}{suffix}"
            if path.exists():
                return path
    return candidate


def find_missing_inputs(paper_root: Path = PAPER_ROOT) -> list[str]:
    issues: list[str] = []
    for tex_path in _collect_tex_paths(paper_root):
        rel = tex_path.relative_to(paper_root)
        text = tex_path.read_text(encoding="utf-8")
        for match in INPUT_RE.finditer(text):
            target = match.group(1).strip()
            if target.startswith("/"):
                issues.append(f"{rel}: absolute input path not allowed: {target}")
                continue
            resolved = _resolve_input_path(paper_root, target)
            if not resolved.exists():
                issues.append(f"{rel}: missing input file: {target}")
    return issues


def find_missing_standard_assets(repo_root: Path = REPO_ROOT) -> list[str]:
    issues: list[str] = []
    for rel in (*STANDARD_FIGURES, *STANDARD_TABLES):
        if not (repo_root / rel).exists():
            issues.append(f"missing standard asset: {rel}")
    return issues


def find_unresolved_figure_table_refs(
    paper_root: Path = PAPER_ROOT,
    *,
    mode: str = "draft",
) -> list[str]:
    labels: set[str] = set()
    for tex_path in _collect_tex_paths(paper_root):
        for prefix, name in LABEL_RE.findall(tex_path.read_text(encoding="utf-8")):
            labels.add(f"{prefix}:{name}")

    issues: list[str] = []
    for tex_path in _collect_tex_paths(paper_root):
        rel = tex_path.relative_to(paper_root)
        for prefix, name in REF_RE.findall(tex_path.read_text(encoding="utf-8")):
            key = f"{prefix}:{name}"
            if key not in labels:
                message = f"{rel}: unresolved ref: {key}"
                if mode == "submission":
                    issues.append(message)
                else:
                    issues.append(f"WARNING: {message}")
    return issues


def find_includegraphics_missing(paper_root: Path = PAPER_ROOT) -> list[str]:
    issues: list[str] = []
    for tex_path in _collect_tex_paths(paper_root):
        rel = tex_path.relative_to(paper_root)
        for target in INCLUDEGRAPHICS_RE.findall(tex_path.read_text(encoding="utf-8")):
            path = (paper_root / target).resolve()
            if not path.exists():
                issues.append(f"{rel}: missing graphics file: {target}")
    return issues


def check_evidence_mapping(
    evidence_path: Path = DEFAULT_EVIDENCE,
    repo_root: Path = REPO_ROOT,
    *,
    mode: str = "draft",
) -> list[str]:
    issues: list[str] = []
    if not evidence_path.exists():
        return [f"missing evidence mapping file: {evidence_path.relative_to(repo_root)}"]

    payload = json.loads(evidence_path.read_text(encoding="utf-8"))
    status = str(payload.get("status", "unfilled")).lower()
    run_dir = payload.get("run_dir")

    if status != "filled":
        message = (
            "paper evidence mapping is not filled "
            f"(status={payload.get('status')!r}); run fill-paper-from-run after a verified pilot"
        )
        if mode == "submission":
            issues.append(message)
        else:
            issues.append(f"WARNING: {message}")
        return issues

    if not run_dir:
        issues.append("filled evidence mapping missing run_dir")
        return issues

    run_path = Path(run_dir)
    if not run_path.is_absolute():
        run_path = repo_root / run_path
    if not run_path.exists():
        issues.append(f"evidence run_dir does not exist: {run_dir}")

    for rel in payload.get("claim_artifacts", {}).values():
        if isinstance(rel, str):
            artifact = Path(rel)
            if not artifact.is_absolute():
                artifact = repo_root / artifact
            if not artifact.exists():
                issues.append(f"claim artifact missing: {rel}")

    return issues


def run_paper_asset_check(
    repo_root: Path = REPO_ROOT,
    *,
    mode: str = "draft",
) -> list[str]:
    paper_root = repo_root / "paper" / "latexpaper"
    issues: list[str] = []
    issues.extend(find_missing_inputs(paper_root))
    issues.extend(find_missing_standard_assets(repo_root))
    issues.extend(find_unresolved_figure_table_refs(paper_root, mode=mode))
    issues.extend(find_includegraphics_missing(paper_root))
    issues.extend(check_evidence_mapping(DEFAULT_EVIDENCE, repo_root, mode=mode))
    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check paper figures/tables and evidence linkage.")
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    parser.add_argument(
        "--mode",
        choices=["draft", "submission"],
        default="draft",
        help="submission mode fails on unfilled evidence mapping.",
    )
    args = parser.parse_args(argv)

    issues = run_paper_asset_check(Path(args.repo_root).resolve(), mode=args.mode)
    hard_failures = [issue for issue in issues if not issue.startswith("WARNING:")]
    warnings = [issue for issue in issues if issue.startswith("WARNING:")]

    for warning in warnings:
        print(f"- {warning}")
    if hard_failures:
        print(f"Paper asset check failed ({len(hard_failures)} issue(s)):")
        for issue in hard_failures:
            print(f"- {issue}")
        return 1
    if warnings:
        print(f"Paper asset check passed with {len(warnings)} warning(s).")
    else:
        print("Paper asset check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
