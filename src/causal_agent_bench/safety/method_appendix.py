"""Generate a method-only appendix scaffold."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

DISCLAIMER = (
    "METHOD SCAFFOLD ONLY: this appendix contains no empirical results, no model "
    "comparisons, no performance numbers, and no claim support for C1-C8/C10."
)


def build_method_appendix(
    repo_root: str | Path,
    *,
    output_dir: str | Path = "paper/latexpaper/generated/no_run_method_appendix",
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    out = Path(output_dir)
    if not out.is_absolute():
        out = root / out
    out.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(UTC).isoformat()
    md = _markdown(generated_at)
    tex = _tex(generated_at)
    md_path = out / "method_appendix.md"
    tex_path = out / "method_appendix.tex"
    manifest_path = out / "method_appendix_manifest.json"
    md_path.write_text(md, encoding="utf-8")
    tex_path.write_text(tex, encoding="utf-8")
    manifest = {
        "generated_at": generated_at,
        "scope": DISCLAIMER,
        "empirical_results": False,
        "paper_claim_support": False,
        "files": {"markdown": str(md_path), "tex": str(tex_path)},
        "summary": {
            "files_generated": 2,
            "markdown_path": str(md_path),
            "tex_path": str(tex_path),
            "method_only_appendix": True,
        },
        "verdicts": {
            "empirical_results_claimed": False,
            "paper_claim_support_implied": False,
            "method_only_safe_to_share": True,
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"report_paths": {"markdown": str(md_path), "tex": str(tex_path), "json": str(manifest_path)}, **manifest}


def _markdown(generated_at: str) -> str:
    return "\n".join(
        [
            "# No-Run Method Appendix",
            "",
            DISCLAIMER,
            "",
            f"Generated: {generated_at}",
            "",
            "## Benchmark Design Overview",
            "The benchmark is organized around paired clean and intervention variants for tool-using agent tasks.",
            "",
            "## Intervention Taxonomy",
            "Intervention families cover tool availability, tool reliability, memory/context, observation conflicts, distractors, and stopping/recovery conditions.",
            "",
            "## Evidence Levels",
            "Engineering scaffolds, synthetic diagnostics, provider-backed runs, human validation, and claim-ledger support are separate evidence levels.",
            "",
            "## No-Run Validation Lane",
            "Static reports inspect metadata, splits, fixtures, configs, and paper assets without running agents.",
            "",
            "## Provider Pilot Safety Flow",
            "Provider execution remains gated by approval, budget caps, dry-run validation, and post-run evidence review.",
            "",
            "## Human Validation Protocol Summary",
            "Human validation requires independent annotations, agreement metrics, and adjudication before C3 or C10 can advance.",
            "",
            "## Claim-Evidence Lifecycle",
            "Claims remain planned until eligible evidence and artifacts pass strict checks.",
            "",
            "## Synthetic Fixture Disclaimer",
            "Synthetic fixtures diagnose metric behavior only and are not real LLM behavior.",
            "",
            "## Method Figure References",
            "See `figures/method/*.mmd` for method-only diagram scaffolds.",
            "",
        ]
    )


def _tex(generated_at: str) -> str:
    return "\n".join(
        [
            "% Auto-generated method scaffold. No empirical results.",
            "\\section{No-Run Method Appendix}",
            "\\textbf{METHOD SCAFFOLD ONLY.} This appendix contains no empirical results, no model comparisons, no performance numbers, and no claim support for C1--C8/C10.",
            f"Generated: {generated_at}.",
            "\\subsection{Benchmark Design Overview}",
            "The benchmark is organized around paired clean and intervention variants for tool-using agent tasks.",
            "\\subsection{Intervention Taxonomy}",
            "Intervention families cover tool availability, tool reliability, memory/context, observation conflicts, distractors, and stopping/recovery conditions.",
            "\\subsection{Evidence Levels And No-Run Validation}",
            "Static reports inspect metadata, splits, fixtures, configs, and paper assets without running agents.",
            "\\subsection{Provider Pilot And Human Validation}",
            "Provider execution remains approval-gated. Human validation requires real annotations, agreement metrics, and adjudication before C3 or C10 can advance.",
            "\\subsection{Synthetic Fixture Disclaimer}",
            "Synthetic fixtures diagnose metric behavior only and are not real LLM behavior.",
            "",
        ]
    )
