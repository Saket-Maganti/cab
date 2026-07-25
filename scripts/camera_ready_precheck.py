#!/usr/bin/env python3
"""Run camera-ready / submission packaging checks."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from causal_agent_bench.claim_ledger import validate_claim_ledger
from scripts.check_citation_todos import run_citation_todo_check
from scripts.check_package_import import run_package_import_check
from scripts.check_paper_assets import run_paper_asset_check
from scripts.check_paper_placeholders import find_placeholders
from scripts.check_repo_packaging import run_repo_packaging_check
from scripts.check_reviewer_proofing import validate_matrix
from scripts.check_todos import find_todos


@dataclass(frozen=True)
class StepResult:
    name: str
    passed: bool
    detail: str


def _run_release_check(repo_root: Path) -> StepResult:
    script = repo_root / "scripts" / "release_check.py"
    proc = subprocess.run(
        [sys.executable, str(script)],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    passed = proc.returncode == 0
    detail = (proc.stdout or proc.stderr).strip() or ("ok" if passed else "failed")
    return StepResult("release_check", passed, detail.splitlines()[-1] if detail else "")


def _check_placeholders(repo_root: Path, mode: str) -> StepResult:
    findings = find_placeholders(repo_root / "paper" / "latexpaper")
    if not findings:
        return StepResult("placeholders", True, "no placeholders detected")
    detail = f"{len(findings)} placeholder(s); first: {findings[0].format(repo_root / 'paper')}"
    if mode == "submission":
        return StepResult("placeholders", False, detail)
    return StepResult("placeholders", True, f"draft allowed — {detail}")


def _check_todos(repo_root: Path, mode: str) -> StepResult:
    issues = find_todos(repo_root / "paper")
    if not issues:
        return StepResult("todos", True, "no TODO markers")
    detail = f"{len(issues)} TODO(s); first: {issues[0]}"
    if mode == "submission":
        return StepResult("todos", False, detail)
    return StepResult("todos", True, f"draft allowed — {detail}")


def _check_citations(repo_root: Path) -> StepResult:
    paper_root = repo_root / "paper" / "latexpaper"
    issues = run_citation_todo_check(paper_root, paper_root / "references.bib")
    if issues:
        return StepResult("citations", False, f"{len(issues)} issue(s); first: {issues[0]}")
    return StepResult("citations", True, "all cite keys resolve; no citation TODO markers")


def _check_claim_ledger(repo_root: Path, mode: str) -> StepResult:
    ledger_path = repo_root / "docs" / "claim_ledger.json"
    errors = validate_claim_ledger(ledger_path, repo_root=repo_root)
    if errors:
        return StepResult("claim_ledger", False, errors[0])

    payload = json.loads(ledger_path.read_text(encoding="utf-8"))
    claims = payload.get("claims", [])
    supported = [c for c in claims if c.get("status") == "supported"]
    planned = [c for c in claims if c.get("status") == "planned"]
    if mode == "submission" and supported:
        return StepResult(
            "unsupported_claims",
            True,
            f"{len(supported)} supported claim(s) with evidence",
        )
    if mode == "submission" and not supported and planned:
        return StepResult(
            "unsupported_claims",
            False,
            "submission requires supported empirical claims or narrowed paper scope",
        )
    return StepResult("claim_ledger", True, f"ledger valid; {len(planned)} planned claim(s)")


def _check_paper_assets(repo_root: Path, mode: str) -> StepResult:
    issues = run_paper_asset_check(repo_root, mode=mode)
    hard = [i for i in issues if not i.startswith("WARNING:")]
    warnings = [i for i in issues if i.startswith("WARNING:")]
    if hard:
        return StepResult("paper_assets", False, hard[0])
    if warnings:
        return StepResult("paper_assets", True, warnings[0].removeprefix("WARNING: "))
    return StepResult("paper_assets", True, "inputs and standard assets present")


def _check_paper_compile(repo_root: Path, *, compile_pdf: bool) -> StepResult:
    main_tex = repo_root / "paper" / "latexpaper" / "main.tex"
    if not main_tex.exists():
        return StepResult("paper_compile", False, "missing paper/latexpaper/main.tex")
    if not compile_pdf:
        return StepResult(
            "paper_compile",
            True,
            "skipped PDF build (use --compile-paper to run pdflatex)",
        )
    if shutil.which("pdflatex") is None:
        return StepResult("paper_compile", False, "pdflatex not found on PATH")
    proc = subprocess.run(
        ["make", "paper-draft"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout).splitlines()[-5:]
        return StepResult("paper_compile", False, " | ".join(tail))
    pdf = repo_root / "paper" / "latexpaper" / "main.pdf"
    if not pdf.exists():
        return StepResult("paper_compile", False, "paper/latexpaper/main.pdf not produced")
    return StepResult("paper_compile", True, f"built {pdf.relative_to(repo_root)}")


def run_camera_ready_precheck(
    repo_root: Path = REPO_ROOT,
    *,
    mode: str = "draft",
    compile_paper: bool = False,
    skip_release: bool = False,
) -> list[StepResult]:
    results: list[StepResult] = []

    if not skip_release:
        results.append(_run_release_check(repo_root))
    packaging_issues = run_repo_packaging_check(repo_root)
    results.append(
        StepResult(
            "repo_packaging",
            not packaging_issues,
            packaging_issues[0]
            if packaging_issues
            else "license, README quickstart, ethics, dataset manifest ok",
        )
    )
    import_issues = run_package_import_check()
    results.append(
        StepResult(
            "package_import",
            not import_issues,
            import_issues[0] if import_issues else "imports ok",
        )
    )
    results.append(_check_placeholders(repo_root, mode))
    results.append(_check_todos(repo_root, mode))
    results.append(_check_citations(repo_root))
    results.append(_check_claim_ledger(repo_root, mode))
    results.append(_check_paper_assets(repo_root, mode))

    matrix_issues = validate_matrix(repo_root / "reviews" / "reviewer_attack_response_matrix.md")
    results.append(StepResult(
        "reviewer_matrix",
        not matrix_issues,
        matrix_issues[0] if matrix_issues else "reviewer attack matrix complete",
    ))
    results.append(_check_paper_compile(repo_root, compile_pdf=compile_paper))

    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Camera-ready packaging precheck.")
    parser.add_argument(
        "--mode",
        choices=["draft", "submission"],
        default="draft",
        help="draft allows placeholders/TODOs; submission is strict.",
    )
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    parser.add_argument(
        "--compile-paper",
        action="store_true",
        help="Run make paper-draft if pdflatex is available.",
    )
    parser.add_argument("--skip-release", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    results = run_camera_ready_precheck(
        repo_root,
        mode=args.mode,
        compile_paper=args.compile_paper,
        skip_release=args.skip_release,
    )
    passed = all(step.passed for step in results)

    if args.json:
        print(
            json.dumps(
                {
                    "mode": args.mode,
                    "passed": passed,
                    "steps": [
                        {"name": s.name, "passed": s.passed, "detail": s.detail}
                        for s in results
                    ],
                },
                indent=2,
            )
        )
    else:
        print(f"camera-ready-precheck ({args.mode}): {'PASS' if passed else 'FAIL'}")
        for step in results:
            status = "PASS" if step.passed else "FAIL"
            print(f"  [{status}] {step.name}: {step.detail}")

    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
