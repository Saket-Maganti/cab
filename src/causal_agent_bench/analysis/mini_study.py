from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from scipy import stats

from causal_agent_bench.analysis.load_results import RunResults, load_run_results
from causal_agent_bench.analysis.tables import (
    dataframe_to_markdown,
    intervention_family_performance_table,
    write_table_bundle,
)
from causal_agent_bench.utils.io import write_json


def compare_mini_study(
    template_run_dir: str | Path,
    naturalistic_run_dir: str | Path,
    *,
    output_dir: str | Path,
) -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    template_data = load_run_results(template_run_dir)
    naturalistic_data = load_run_results(naturalistic_run_dir)

    template_families = _mean_family_degradation(template_data)
    naturalistic_families = _mean_family_degradation(naturalistic_data)
    comparison = _compare_family_patterns(template_families, naturalistic_families)
    examples = _qualitative_examples(template_data, naturalistic_data, comparison)
    report = {
        "schema_version": "mini_study_v1",
        "template_run_dir": str(template_data.run_dir),
        "naturalistic_run_dir": str(naturalistic_data.run_dir),
        "template_evidence_scope": template_data.run_metadata.get("evidence_scope"),
        "naturalistic_evidence_scope": naturalistic_data.run_metadata.get("evidence_scope"),
        "comparison": comparison,
        "qualitative_examples": examples,
        "limitations": _limitations_note(comparison),
        "scope": (
            "Engineering comparison of intervention-family degradation patterns. "
            "Not a scientific external-validity claim unless both runs use validated models and datasets."
        ),
    }

    table = _comparison_table(template_families, naturalistic_families, comparison)
    table_paths = write_table_bundle(table, output_path / "table_mini_study_family_comparison")
    write_json(output_path / "mini_study_comparison.json", report)
    (output_path / "mini_study_comparison.md").write_text(
        _mini_study_markdown(report, table),
        encoding="utf-8",
    )
    _write_paper_paragraph(output_path / "mini_study_paper_paragraph.tex", report, comparison)
    report["output_paths"] = [str(path) for path in [*table_paths, output_path / "mini_study_comparison.json", output_path / "mini_study_comparison.md", output_path / "mini_study_paper_paragraph.tex"]]
    return report


def _mean_family_degradation(data: RunResults) -> dict[str, float]:
    frame = intervention_family_performance_table(data)
    if frame.empty or "intervention_family" not in frame.columns:
        return {}
    grouped = (
        frame.groupby("intervention_family", as_index=False)["absolute_degradation"]
        .mean(numeric_only=True)
        .dropna()
    )
    return {
        str(row["intervention_family"]): float(row["absolute_degradation"])
        for _, row in grouped.iterrows()
    }


def _compare_family_patterns(
    template: dict[str, float],
    naturalistic: dict[str, float],
) -> dict[str, Any]:
    families = sorted(set(template) & set(naturalistic))
    if len(families) < 2:
        return {
            "families_compared": families,
            "pattern_similarity": "insufficient_overlap",
            "spearman_degradation_correlation": None,
            "mean_absolute_difference": None,
            "families_with_large_divergence": [],
        }
    template_values = [template[family] for family in families]
    naturalistic_values = [naturalistic[family] for family in families]
    if len(set(template_values)) < 2 or len(set(naturalistic_values)) < 2:
        spearman = None
    else:
        spearman_result = stats.spearmanr(template_values, naturalistic_values)
        spearman = (
            float(spearman_result.statistic)
            if spearman_result.statistic == spearman_result.statistic
            else None
        )
    diffs = {
        family: round(abs(template[family] - naturalistic[family]), 6) for family in families
    }
    large = [family for family, diff in diffs.items() if diff >= 0.15]
    mean_diff = round(sum(diffs.values()) / len(diffs), 6)
    if spearman is None:
        similarity = "insufficient_variance"
    elif spearman >= 0.6 and mean_diff < 0.12:
        similarity = "similar"
    elif spearman < 0.3:
        similarity = "different"
    else:
        similarity = "mixed"
    return {
        "families_compared": families,
        "pattern_similarity": similarity,
        "spearman_degradation_correlation": round(spearman, 6) if spearman is not None else None,
        "mean_absolute_difference": mean_diff,
        "per_family_absolute_difference": diffs,
        "families_with_large_divergence": large,
        "template_family_degradation": {family: template[family] for family in families},
        "naturalistic_family_degradation": {family: naturalistic[family] for family in families},
    }


def _comparison_table(
    template: dict[str, float],
    naturalistic: dict[str, float],
    comparison: dict[str, Any],
) -> pd.DataFrame:
    rows = []
    for family in comparison.get("families_compared", []):
        rows.append(
            {
                "intervention_family": family,
                "template_absolute_degradation": template.get(family),
                "naturalistic_absolute_degradation": naturalistic.get(family),
                "absolute_difference": comparison.get("per_family_absolute_difference", {}).get(family),
            }
        )
    if not rows:
        rows.append(
            {
                "intervention_family": "n/a",
                "template_absolute_degradation": None,
                "naturalistic_absolute_degradation": None,
                "absolute_difference": None,
            }
        )
    summary = pd.DataFrame(rows)
    summary["pattern_similarity"] = comparison.get("pattern_similarity")
    summary["spearman_degradation_correlation"] = comparison.get("spearman_degradation_correlation")
    summary["mean_absolute_difference"] = comparison.get("mean_absolute_difference")
    return summary


def _qualitative_examples(
    template_data: RunResults,
    naturalistic_data: RunResults,
    comparison: dict[str, Any],
) -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    divergent = comparison.get("families_with_large_divergence", [])[:2]
    for family in divergent:
        examples.append(
            _example_for_family(template_data, family, cohort="template")
        )
        examples.append(
            _example_for_family(naturalistic_data, family, cohort="naturalistic")
        )
    if not examples:
        examples.append(_example_for_family(template_data, None, cohort="template"))
        examples.append(_example_for_family(naturalistic_data, None, cohort="naturalistic"))
    return examples


def _example_for_family(data: RunResults, family: str | None, *, cohort: str) -> dict[str, Any]:
    scores = data.scores_df
    if scores.empty:
        return {"cohort": cohort, "note": "no scores available"}
    filtered = scores
    if family is not None and "diagnostic_intervention_family" in scores.columns:
        filtered = scores[scores["diagnostic_intervention_family"].eq(family)]
    if filtered.empty:
        filtered = scores
    row = filtered.iloc[0]
    instance_id = str(row.get("instance_id"))
    instruction = None
    if not data.instances_df.empty and "user_instruction" in data.instances_df.columns:
        match = data.instances_df[data.instances_df["instance_id"] == instance_id]
        if not match.empty:
            instruction = str(match.iloc[0]["user_instruction"])[:500]
    return {
        "cohort": cohort,
        "intervention_family": family or row.get("diagnostic_intervention_family"),
        "instance_id": instance_id,
        "agent_name": row.get("agent_name"),
        "final_success_binary": row.get("final_success_binary"),
        "instruction_excerpt": instruction,
    }


def _limitations_note(comparison: dict[str, Any]) -> str:
    similarity = comparison.get("pattern_similarity")
    if similarity == "similar":
        return (
            "Within this controlled mini-study, template-generated and naturalistic synthetic tasks "
            "show broadly similar intervention-family degradation ordering. This supports using the "
            "controlled generator for causal attribution while still requiring validation on messier deployments."
        )
    if similarity == "different":
        return (
            "Template-generated and naturalistic synthetic tasks diverge on several intervention families. "
            "Do not treat template-only degradation curves as sufficient external-validity evidence; "
            "report naturalistic tasks separately and prioritize human validation on divergent families."
        )
    return (
        "The mini-study overlap is limited or mixed. Treat comparisons as exploratory engineering evidence "
        "until paired runs on validated models and audited naturalistic tasks are complete."
    )


def _mini_study_markdown(report: dict[str, Any], table: pd.DataFrame) -> str:
    comparison = report["comparison"]
    lines = [
        "# Synthetic-to-Realistic Mini-Study Comparison",
        "",
        report["scope"],
        "",
        f"- Template run: `{report['template_run_dir']}`",
        f"- Naturalistic run: `{report['naturalistic_run_dir']}`",
        f"- Pattern similarity: `{comparison.get('pattern_similarity')}`",
        f"- Spearman degradation correlation: `{comparison.get('spearman_degradation_correlation')}`",
        f"- Mean absolute family difference: `{comparison.get('mean_absolute_difference')}`",
        "",
        "## Family Comparison",
        "",
        dataframe_to_markdown(table).strip(),
        "",
        "## Qualitative Examples",
        "",
    ]
    for example in report.get("qualitative_examples", []):
        lines.append(
            f"- **{example.get('cohort')}** / `{example.get('intervention_family')}` / "
            f"`{example.get('instance_id')}`: success={example.get('final_success_binary')}"
        )
        if example.get("instruction_excerpt"):
            lines.append(f"  - Instruction excerpt: {example['instruction_excerpt']}")
    lines.extend(["", "## Limitations", "", report.get("limitations", ""), ""])
    return "\n".join(lines)


def _write_paper_paragraph(path: Path, report: dict[str, Any], comparison: dict[str, Any]) -> None:
    spearman = comparison.get("spearman_degradation_correlation")
    similarity = comparison.get("pattern_similarity")
    text = (
        "\\paragraph{Synthetic-to-realistic mini-study.}\n"
        "To address concerns that template-generated tasks may not transfer to more realistic agent settings, "
        "we added a small external-validity study that keeps the environment local and deterministic. "
        "The study compares template-generated synthetic tasks with naturalistic synthetic tasks built from mock emails, "
        "calendars, spreadsheets, policy documents, bug reports, and product-database artifacts. "
        f"Engineering comparison reports pattern similarity as \\texttt{{{similarity}}} "
        f"(Spearman correlation of family-level absolute degradation = {spearman}). "
        "This is not a deployment claim: all artifacts remain synthetic, locally controlled, and auditable. "
        f"{report['limitations']} "
        "See Table~\\ref{{tab:mini-study-family-comparison}} and the generated artifact "
        "\\texttt{{tables/table\\_mini\\_study\\_family\\_comparison.*}}.\n"
    )
    path.write_text(text, encoding="utf-8")
