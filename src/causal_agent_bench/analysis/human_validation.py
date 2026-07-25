from __future__ import annotations

import csv
import html
import json
import random
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from typing import Any

from causal_agent_bench.analysis.error_analysis import mine_error_cases
from causal_agent_bench.analysis.load_results import RunResults, load_run_results
from causal_agent_bench.hashing import stable_hash
from causal_agent_bench.utils.io import git_commit, write_json, write_jsonl

ANNOTATION_DIMENSIONS = [
    "task_understandable",
    "goal_preserved",
    "changed_factor_isolated",
    "expected_robust_behavior_reasonable",
    "final_answer_label_correct",
    "trajectory_tool_misuse",
    "trajectory_showed_recovery",
    "trajectory_detected_contradiction",
    "trajectory_stopped_prematurely",
    "error_taxonomy_label_correct",
]

ANNOTATION_VALUES = ["yes", "no", "unclear", "not_applicable"]


def export_human_validation_sample(
    run_dir: str | Path,
    *,
    output_dir: str | Path | None = None,
    sample_size: int = 100,
    seed: int = 0,
    annotators_per_item: int = 2,
    include_html: bool = True,
) -> dict[str, Any]:
    """Sample run artifacts into CSV/JSONL annotation packets."""

    data = load_run_results(run_dir)
    out = Path(output_dir) if output_dir is not None else data.run_dir / "human_validation"
    out.mkdir(parents=True, exist_ok=True)
    sampled = sample_validation_items(data, sample_size=sample_size, seed=seed)
    assignments = _annotation_assignments(sampled, annotators_per_item=annotators_per_item)
    csv_path = out / "annotation_export.csv"
    jsonl_path = out / "annotation_export.jsonl"
    _write_annotation_csv(csv_path, assignments)
    write_jsonl(jsonl_path, assignments)
    if include_html:
        (out / "annotation_interface.html").write_text(
            _annotation_html(assignments),
            encoding="utf-8",
        )
    manifest = {
        "run_dir": str(data.run_dir),
        "output_dir": str(out),
        "sample_size_requested": sample_size,
        "items_sampled": len(sampled),
        "annotation_rows": len(assignments),
        "annotators_per_item": annotators_per_item,
        "seed": seed,
        "dimensions": ANNOTATION_DIMENSIONS,
        "allowed_values": ANNOTATION_VALUES,
        "git_commit": git_commit(Path.cwd()),
        "scope": "Human validation export template only; labels remain unvalidated until annotators complete and adjudicate them.",
        "files": {
            "csv": str(csv_path),
            "jsonl": str(jsonl_path),
            "html": str(out / "annotation_interface.html") if include_html else None,
        },
    }
    write_json(out / "annotation_manifest.json", manifest)
    return manifest


def sample_validation_items(
    data: RunResults,
    *,
    sample_size: int,
    seed: int,
) -> list[dict[str, Any]]:
    joined = _joined_rows(data)
    if not joined:
        return []
    by_stratum: dict[tuple[str, str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in joined:
        by_stratum[
            (
                str(row.get("domain") or "unknown"),
                str(row.get("difficulty") or "unknown"),
                str(row.get("intervention_family") or "clean"),
                str(row.get("agent_name") or "unknown"),
                str(row.get("outcome") or "unknown"),
            )
        ].append(row)
    rng = random.Random(seed)
    for rows in by_stratum.values():
        rows.sort(key=lambda item: item["item_id"])
        rng.shuffle(rows)

    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    strata = sorted(by_stratum)
    while len(selected) < sample_size and strata:
        progressed = False
        for stratum in strata:
            rows = by_stratum[stratum]
            while rows:
                row = rows.pop(0)
                if row["item_id"] in selected_ids:
                    continue
                selected.append(row)
                selected_ids.add(row["item_id"])
                progressed = True
                break
            if len(selected) >= sample_size:
                break
        strata = [stratum for stratum in strata if by_stratum[stratum]]
        if not progressed:
            break
    return selected[:sample_size]


def summarize_human_validation_annotations(
    annotations_path: str | Path,
    *,
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    rows = _read_annotation_rows(Path(annotations_path))
    out = Path(output_dir) if output_dir is not None else Path(annotations_path).parent
    out.mkdir(parents=True, exist_ok=True)
    agreement = compute_agreement(rows)
    disagreements = _disagreement_examples(rows)
    summary = {
        "annotations_path": str(annotations_path),
        "output_dir": str(out),
        "n_annotation_rows": len(rows),
        "n_items": len({row.get("item_id") for row in rows if row.get("item_id")}),
        "agreement": agreement,
        "disagreement_examples": disagreements,
        "adjudication": _adjudication_summary(rows),
        "scope": "Human validation summary; do not cite as scientific evidence unless completed annotations and adjudication are documented.",
    }
    write_json(out / "validation_agreement.json", summary)
    _write_agreement_table(out, agreement)
    (out / "validation_report.md").write_text(
        _validation_report_markdown(summary),
        encoding="utf-8",
    )
    write_jsonl(out / "disagreement_examples.jsonl", disagreements)
    return summary


def compute_agreement(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_dimension: dict[str, dict[str, Any]] = {}
    for dimension in ANNOTATION_DIMENSIONS:
        item_labels: dict[str, list[str]] = defaultdict(list)
        for row in rows:
            label = _normalized_label(row.get(dimension))
            if label is None:
                continue
            item_id = str(row.get("item_id") or "")
            if not item_id:
                continue
            item_labels[item_id].append(label)
        comparable = {item: labels for item, labels in item_labels.items() if len(labels) >= 2}
        by_dimension[dimension] = {
            "items_with_two_or_more_annotations": len(comparable),
            "percent_agreement": _percent_agreement(comparable),
            "cohens_kappa": _cohens_kappa(comparable),
            "krippendorffs_alpha": _krippendorff_alpha(comparable),
            "label_counts": dict(sorted(Counter(label for labels in item_labels.values() for label in labels).items())),
        }
    return by_dimension


def _joined_rows(data: RunResults) -> list[dict[str, Any]]:
    scores = data.scores_df.copy()
    if scores.empty:
        return []
    instances = data.instances_df.copy()
    trajectories = data.trajectories_df.copy()
    if not instances.empty:
        scores = scores.merge(instances, on="instance_id", how="left", suffixes=("", "_instance"))
    if not trajectories.empty:
        scores = scores.merge(
            trajectories,
            on=["instance_id", "agent_name"],
            how="left",
            suffixes=("", "_trajectory"),
        )
    error_labels = _error_taxonomy_labels(data)
    contexts_by_id = {instance.instance_id: instance for instance in data.instances}
    rows: list[dict[str, Any]] = []
    for row in scores.to_dict(orient="records"):
        instance_id = row.get("instance_id")
        agent_name = row.get("agent_name")
        context = contexts_by_id.get(instance_id)
        intervention = context.intervention if context is not None else None
        item_id = stable_hash(
            {
                "run_id": row.get("run_id"),
                "instance_id": instance_id,
                "agent_name": agent_name,
                "repeat": row.get("repeat", 0),
            }
        )
        final_success = row.get("final_success_binary")
        trajectory_success = row.get("trajectory_success_binary")
        outcome = _outcome_label(final_success, trajectory_success)
        score_details = {
            key: row.get(key)
            for key in [
                "final_success_binary",
                "trajectory_success_binary",
                "tool_error_recovery_binary",
                "contradiction_detected_binary",
                "premature_stop_binary",
                "unnecessary_tool_call_rate",
                "invalid_tool_call_count",
                "argument_error_count",
            ]
            if key in row
        }
        rows.append(
            {
                "item_id": item_id,
                "run_id": row.get("run_id"),
                "instance_id": instance_id,
                "base_task_id": row.get("diagnostic_base_task_id") or row.get("base_task_id"),
                "agent_name": agent_name,
                "model_name": row.get("model_name") or row.get("metadata_model_name"),
                "domain": row.get("domain"),
                "difficulty": row.get("difficulty"),
                "condition": row.get("diagnostic_condition") or row.get("condition"),
                "intervention_family": row.get("diagnostic_intervention_family") or row.get("intervention_family"),
                "expected_final_answer_change": intervention.expected_final_answer_change if intervention else None,
                "error_taxonomy_label": error_labels.get((instance_id, agent_name), "none"),
                "outcome": outcome,
                "user_instruction": row.get("user_instruction"),
                "success_criteria": json.dumps(context.base_task.goal.success_criteria if context else []),
                "expected_final_answer": json.dumps(context.base_task.goal.expected_final_answer if context else None, sort_keys=True),
                "intervention_description": intervention.description if intervention else None,
                "changed_factor": intervention.changed_factor if intervention else None,
                "expected_robust_behavior": intervention.expected_robust_behavior if intervention else None,
                "final_answer": row.get("final_answer"),
                "tool_calls": ", ".join(row.get("tool_calls") or []),
                "terminated_reason": row.get("terminated_reason"),
                "score_details": json.dumps(score_details, sort_keys=True, default=str),
                "annotation_instructions": (
                    "Use yes/no/unclear/not_applicable for each label. Leave adjudicated_* blank "
                    "until adjudication."
                ),
            }
        )
    return rows


def _annotation_assignments(
    items: list[dict[str, Any]],
    *,
    annotators_per_item: int,
) -> list[dict[str, Any]]:
    assignments: list[dict[str, Any]] = []
    for item in items:
        for annotator_slot in range(1, max(1, annotators_per_item) + 1):
            row = {
                "annotation_id": f"{item['item_id']}.a{annotator_slot}",
                "annotator_slot": annotator_slot,
                "annotator_id": "",
                **item,
            }
            for dimension in ANNOTATION_DIMENSIONS:
                row[dimension] = ""
                row[f"adjudicated_{dimension}"] = ""
            row["disagreement_flag"] = ""
            row["annotator_notes"] = ""
            row["adjudication_notes"] = ""
            assignments.append(row)
    return assignments


def _error_taxonomy_labels(data: RunResults) -> dict[tuple[str, str], str]:
    labels: dict[tuple[str, str], str] = {}
    for category, cases in mine_error_cases(data, max_cases=10_000).items():
        for case in cases:
            labels.setdefault((case["instance_id"], case["agent"]), category)
    return labels


def _outcome_label(final_success: Any, trajectory_success: Any) -> str:
    if final_success in {1} and trajectory_success in {1}:
        return "success"
    if final_success in {1} and trajectory_success in {0}:
        return "final_success_trajectory_failure"
    if final_success in {0}:
        return "failure"
    return "unknown"


def _write_annotation_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = _annotation_fieldnames(rows)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def _annotation_fieldnames(rows: list[dict[str, Any]]) -> list[str]:
    preferred = [
        "annotation_id",
        "annotator_slot",
        "annotator_id",
        "item_id",
        "run_id",
        "instance_id",
        "base_task_id",
        "agent_name",
        "model_name",
        "domain",
        "difficulty",
        "condition",
        "intervention_family",
        "expected_final_answer_change",
        "error_taxonomy_label",
        "outcome",
        "user_instruction",
        "success_criteria",
        "expected_final_answer",
        "intervention_description",
        "changed_factor",
        "expected_robust_behavior",
        "final_answer",
        "tool_calls",
        "terminated_reason",
        "score_details",
        "annotation_instructions",
    ]
    adjudicated = [f"adjudicated_{dimension}" for dimension in ANNOTATION_DIMENSIONS]
    trailing = ["disagreement_flag", "annotator_notes", "adjudication_notes"]
    all_keys = set().union(*(row.keys() for row in rows)) if rows else set()
    ordered = preferred + ANNOTATION_DIMENSIONS + adjudicated + trailing
    return ordered + sorted(all_keys - set(ordered))


def _annotation_html(rows: list[dict[str, Any]]) -> str:
    cards = []
    for row in rows:
        labels = "\n".join(
            f"<label>{html.escape(dimension)}: <select name='{html.escape(row['annotation_id'])}_{dimension}'>"
            + "".join(f"<option>{html.escape(value)}</option>" for value in ["", *ANNOTATION_VALUES])
            + "</select></label>"
            for dimension in ANNOTATION_DIMENSIONS
        )
        cards.append(
            f"""
            <section class="item">
              <h2>{html.escape(str(row.get("annotation_id")))}</h2>
              <p><strong>Instance:</strong> {html.escape(str(row.get("instance_id")))} |
                 <strong>Agent:</strong> {html.escape(str(row.get("agent_name")))} |
                 <strong>Outcome:</strong> {html.escape(str(row.get("outcome")))}</p>
              <p><strong>Instruction:</strong> {html.escape(str(row.get("user_instruction") or ""))}</p>
              <p><strong>Intervention:</strong> {html.escape(str(row.get("intervention_description") or "clean"))}</p>
              <p><strong>Expected robust behavior:</strong> {html.escape(str(row.get("expected_robust_behavior") or "not applicable"))}</p>
              <p><strong>Final answer:</strong> {html.escape(str(row.get("final_answer") or ""))}</p>
              <p><strong>Tool calls:</strong> {html.escape(str(row.get("tool_calls") or ""))}</p>
              <div class="labels">{labels}</div>
              <textarea placeholder="Annotator notes"></textarea>
            </section>
            """
        )
    return (
        "<!doctype html><html><head><meta charset='utf-8'><title>CausalAgentBench Human Validation</title>"
        "<style>body{font-family:sans-serif;max-width:960px;margin:2rem auto;line-height:1.4}.item{border:1px solid #ccc;padding:1rem;margin:1rem 0}.labels label{display:block;margin:.25rem 0}textarea{width:100%;min-height:4rem}</style>"
        "</head><body><h1>CausalAgentBench Human Validation</h1>"
        "<p>This static page is an annotation aid. Record labels in the CSV/JSONL export.</p>"
        + "\n".join(cards)
        + "</body></html>\n"
    )


def _read_annotation_rows(path: Path) -> list[dict[str, Any]]:
    if path.suffix == ".jsonl":
        rows = []
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    rows.append(json.loads(line))
        return rows
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _normalized_label(value: Any) -> str | None:
    if value is None:
        return None
    label = str(value).strip().lower()
    if not label:
        return None
    aliases = {"n/a": "not_applicable", "na": "not_applicable", "not applicable": "not_applicable"}
    return aliases.get(label, label)


def _percent_agreement(item_labels: dict[str, list[str]]) -> float | None:
    if not item_labels:
        return None
    agreed = sum(1 for labels in item_labels.values() if len(set(labels)) == 1)
    return round(agreed / len(item_labels), 6)


def _cohens_kappa(item_labels: dict[str, list[str]]) -> float | None:
    pairs = [labels[:2] for labels in item_labels.values() if len(labels) == 2]
    if not pairs:
        return None
    observed = sum(1 for first, second in pairs if first == second) / len(pairs)
    first_counts = Counter(first for first, _ in pairs)
    second_counts = Counter(second for _, second in pairs)
    labels = set(first_counts) | set(second_counts)
    expected = sum(
        (first_counts[label] / len(pairs)) * (second_counts[label] / len(pairs))
        for label in labels
    )
    if expected == 1:
        return 1.0
    return round((observed - expected) / (1 - expected), 6)


def _krippendorff_alpha(item_labels: dict[str, list[str]]) -> float | None:
    pair_disagreements = []
    label_counts: Counter[str] = Counter()
    for labels in item_labels.values():
        label_counts.update(labels)
        if len(labels) < 2:
            continue
        for first, second in combinations(labels, 2):
            pair_disagreements.append(0 if first == second else 1)
    if not pair_disagreements:
        return None
    observed = sum(pair_disagreements) / len(pair_disagreements)
    total = sum(label_counts.values())
    if total <= 1:
        return None
    expected = 1 - sum(count * (count - 1) for count in label_counts.values()) / (total * (total - 1))
    if expected == 0:
        return 1.0
    return round(1 - observed / expected, 6)


def _disagreement_examples(rows: list[dict[str, Any]], limit: int = 20) -> list[dict[str, Any]]:
    by_item: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("item_id"):
            by_item[str(row["item_id"])].append(row)
    examples = []
    for item_id, item_rows in sorted(by_item.items()):
        disagreements = {}
        for dimension in ANNOTATION_DIMENSIONS:
            labels = sorted(
                {
                    label
                    for row in item_rows
                    if (label := _normalized_label(row.get(dimension))) is not None
                }
            )
            if len(labels) > 1:
                disagreements[dimension] = labels
        if disagreements:
            first = item_rows[0]
            examples.append(
                {
                    "item_id": item_id,
                    "instance_id": first.get("instance_id"),
                    "agent_name": first.get("agent_name"),
                    "disagreements": disagreements,
                    "adjudicated": {
                        dimension: _normalized_label(first.get(f"adjudicated_{dimension}"))
                        for dimension in ANNOTATION_DIMENSIONS
                        if _normalized_label(first.get(f"adjudicated_{dimension}")) is not None
                    },
                }
            )
        if len(examples) >= limit:
            break
    return examples


def _adjudication_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    adjudicated_counts = {
        dimension: sum(
            1 for row in rows if _normalized_label(row.get(f"adjudicated_{dimension}")) is not None
        )
        for dimension in ANNOTATION_DIMENSIONS
    }
    return {
        "two_annotators_per_item_recommended": True,
        "adjudicated_label_columns": [f"adjudicated_{dimension}" for dimension in ANNOTATION_DIMENSIONS],
        "adjudicated_label_counts": adjudicated_counts,
    }


def _write_agreement_table(out: Path, agreement: dict[str, dict[str, Any]]) -> None:
    rows = [
        {
            "dimension": dimension,
            "items": stats["items_with_two_or_more_annotations"],
            "percent_agreement": stats["percent_agreement"],
            "cohens_kappa": stats["cohens_kappa"],
            "krippendorffs_alpha": stats["krippendorffs_alpha"],
        }
        for dimension, stats in agreement.items()
    ]
    csv_path = out / "table5_human_validation_agreement.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["dimension", "items", "percent_agreement", "cohens_kappa", "krippendorffs_alpha"],
        )
        writer.writeheader()
        writer.writerows(rows)
    _write_markdown_table(out / "table5_human_validation_agreement.md", rows)
    _write_latex_table(out / "table5_human_validation_agreement.tex", rows)


def _write_markdown_table(path: Path, rows: list[dict[str, Any]]) -> None:
    lines = [
        "| Dimension | Items | Percent agreement | Cohen's kappa | Krippendorff's alpha |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['dimension']}` | {row['items']} | {_fmt(row['percent_agreement'])} | {_fmt(row['cohens_kappa'])} | {_fmt(row['krippendorffs_alpha'])} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_latex_table(path: Path, rows: list[dict[str, Any]]) -> None:
    lines = [
        "\\begin{tabular}{lrrrr}",
        "\\toprule",
        "Dimension & Items & Agreement & $\\kappa$ & $\\alpha$ \\\\",
        "\\midrule",
    ]
    for row in rows:
        lines.append(
            f"{row['dimension'].replace('_', ' ')} & {row['items']} & {_fmt(row['percent_agreement'])} & {_fmt(row['cohens_kappa'])} & {_fmt(row['krippendorffs_alpha'])} \\\\"
        )
    lines.extend(["\\bottomrule", "\\end{tabular}", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def _validation_report_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Human Validation Report",
        "",
        "This report summarizes completed annotation files. It is not scientific evidence unless the annotation protocol, adjudication, and claim ledger cite the artifacts.",
        "",
        f"- Annotation rows: {summary['n_annotation_rows']}",
        f"- Items: {summary['n_items']}",
        "",
        "## Agreement",
        "",
        "| Dimension | Items | Percent agreement | Cohen's kappa | Krippendorff's alpha |",
        "|---|---:|---:|---:|---:|",
    ]
    for dimension, stats in summary["agreement"].items():
        lines.append(
            f"| `{dimension}` | {stats['items_with_two_or_more_annotations']} | {_fmt(stats['percent_agreement'])} | {_fmt(stats['cohens_kappa'])} | {_fmt(stats['krippendorffs_alpha'])} |"
        )
    lines.extend(["", "## Disagreement Examples", ""])
    examples = summary.get("disagreement_examples", [])
    if not examples:
        lines.append("No disagreements found in comparable annotated rows.")
    for example in examples[:10]:
        lines.append(
            f"- `{example['item_id']}` (`{example.get('instance_id')}`, `{example.get('agent_name')}`): {example['disagreements']}"
        )
    lines.extend(
        [
            "",
            "## Ethics And Compensation Placeholder",
            "",
            "Before using human labels in claims, document annotator qualifications, consent, compensation, instructions, time estimates, and an escalation path for ambiguous or uncomfortable examples.",
        ]
    )
    return "\n".join(lines) + "\n"


def _fmt(value: Any) -> str:
    if value is None:
        return "NA"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)
