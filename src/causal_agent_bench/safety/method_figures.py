"""Method figure scaffold writer."""

from __future__ import annotations

from pathlib import Path
from typing import Any

FIGURES: dict[str, str] = {
    "benchmark_pipeline.mmd": """flowchart LR
    A["Task specifications"] --> B["Clean instances"]
    A --> C["Intervention instances"]
    B --> D["Static validation"]
    C --> D
    D --> E["No-run reports"]
    E --> F["Provider pilot review gate"]
""",
    "clean_intervention_pair.mmd": """flowchart TB
    A["Base task goal"] --> B["Clean variant"]
    A --> C["Intervention variant"]
    C --> D["Intended causal factor"]
    B --> E["Paired static metadata"]
    C --> E
    E --> F["Isolation review"]
""",
    "evidence_lifecycle.mmd": """flowchart LR
    A["Planned claim"] --> B["Engineering scaffold"]
    B --> C["Provider-backed run"]
    C --> D["Eligibility review"]
    D --> E["Human validation when required"]
    E --> F["Claim ledger update"]
""",
    "provider_pilot_safety_flow.mmd": """flowchart TB
    A["Template config"] --> B["Cost estimate"]
    B --> C["Static safety reports"]
    C --> D["Manual approval"]
    D --> E["Provider execution"]
    E --> F["Post-run evidence gates"]
""",
    "human_validation_workflow.mmd": """flowchart LR
    A["Static annotation packet"] --> B["Independent annotators"]
    B --> C["Agreement metrics"]
    C --> D["Adjudication"]
    D --> E["Eligible validation artifact"]
    E --> F["Claim evidence matrix"]
""",
}


def write_method_figure_scaffolds(
    repo_root: str | Path,
    *,
    output_dir: str | Path = "figures/method",
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    out = Path(output_dir)
    if not out.is_absolute():
        out = root / out
    out.mkdir(parents=True, exist_ok=True)
    paths: dict[str, str] = {}
    for name, text in FIGURES.items():
        path = out / name
        path.write_text(text.rstrip() + "\n", encoding="utf-8")
        paths[name] = str(path)
    doc_path = root / "docs/PAPER_METHOD_FIGURES.md"
    doc_path.parent.mkdir(parents=True, exist_ok=True)
    doc_path.write_text(method_figures_doc(paths), encoding="utf-8")
    paths["docs/PAPER_METHOD_FIGURES.md"] = str(doc_path)
    return {
        "output_dir": str(out),
        "scope": "Method/scaffold figures only; no empirical result figures are generated.",
        "files": paths,
    }


def method_figures_doc(paths: dict[str, str]) -> str:
    lines = [
        "# Paper Method Figure Scaffolds",
        "",
        "These files are method/scaffold figures only. They show workflow, governance, and validation structure.",
        "",
        "They do not show empirical results, performance plots, degradation estimates, rankings, or human-validation outcomes.",
        "",
        "They are safe for paper method sections as process diagrams, but they are not evidence for C1-C8 or C10.",
        "",
        "Convert the Mermaid files to PDF or SVG later only after checking captions preserve the non-empirical status.",
        "",
        "## Files",
        "",
    ]
    for name in sorted(paths):
        if name.startswith("docs/"):
            continue
        lines.append(f"- `{name}`")
    lines.append("")
    return "\n".join(lines)
