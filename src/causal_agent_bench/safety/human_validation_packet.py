"""No-run human validation protocol packet writer."""

from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from causal_agent_bench.safety.common import write_dual_report

ANNOTATION_COLUMNS = [
    "sample_id",
    "trajectory_id",
    "task_id",
    "intervention_type",
    "clean_or_intervention",
    "predicted_failure_category",
    "task_understandable_yes_no",
    "intervention_isolation_valid_yes_no",
    "gold_answer_correct_yes_no",
    "trajectory_label_valid_yes_no",
    "annotator_failure_category",
    "evidence_span_or_step",
    "confidence_1_to_5",
    "invalid_sample_flag",
    "invalid_sample_reason",
    "notes",
    "adjudication_required",
    "adjudicated_label",
    "annotator_id_hash",
    "timestamp",
]

ADJUDICATION_COLUMNS = [
    "sample_id",
    "annotator_a_label",
    "annotator_b_label",
    "disagreement_type",
    "adjudicator_label",
    "adjudicator_rationale",
    "taxonomy_revision_needed",
    "adjudicator_id_hash",
    "timestamp",
]


def build_human_validation_packet(
    repo_root: str | Path,
    *,
    output_dir: str | Path = "reports/human_validation",
    template_dir: str | Path = "data/human_validation/templates",
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    out = Path(output_dir)
    if not out.is_absolute():
        out = root / out
    templates = Path(template_dir)
    if not templates.is_absolute():
        templates = root / templates
    templates.mkdir(parents=True, exist_ok=True)
    csv_path = templates / "annotation_sheet_template.csv"
    schema_path = templates / "annotation_schema.json"
    adjudication_path = templates / "adjudication_sheet_template.csv"
    agreement_path = templates / "agreement_summary_template.md"
    trajectory_schema_path = templates / "trajectory_packet_schema.json"
    codebook_path = templates / "annotation_codebook.md"
    annotator_readme = templates / "README_ANNOTATOR.md"
    adjudicator_readme = templates / "README_ADJUDICATOR.md"
    _write_template_csv(csv_path)
    _write_adjudication_csv(adjudication_path)
    schema = annotation_schema()
    schema_path.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    trajectory_schema_path.write_text(
        json.dumps(trajectory_packet_schema(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    codebook_path.write_text(_codebook_markdown(), encoding="utf-8")
    agreement_path.write_text(_agreement_summary_template(), encoding="utf-8")
    annotator_readme.write_text(_annotator_readme(), encoding="utf-8")
    adjudicator_readme.write_text(_adjudicator_readme(), encoding="utf-8")
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": "No-run dry-run packet only. No annotations are collected and no models are called.",
        "templates": {
            "csv": str(csv_path),
            "schema": str(schema_path),
            "adjudication_csv": str(adjudication_path),
            "agreement_summary": str(agreement_path),
            "trajectory_packet_schema": str(trajectory_schema_path),
            "codebook": str(codebook_path),
            "annotator_readme": str(annotator_readme),
            "adjudicator_readme": str(adjudicator_readme),
        },
        "claim_state": {
            "C3": "blocked until real completed annotation artifacts and adjudication exist",
            "C10": "blocked until real completed annotation artifacts and adjudication exist",
            "table5": "placeholder only; cannot support claims",
        },
        "summary": {
            "templates_generated": 8,
            "csv_template": str(csv_path),
            "schema_template": str(schema_path),
            "annotations_exist": False,
            "claims_supported": False,
        },
        "verdicts": {
            "annotation_packet_ready_for_dry_run": True,
            "claims_supported_by_packet": False,
            "real_annotations_required_before_C3_C10": True,
        },
    }
    md = human_validation_packet_markdown(payload)
    md_path, json_path = write_dual_report(
        stem="human_validation_dry_run_packet",
        payload=payload,
        markdown=md,
        output_dir=out,
    )
    payload["report_paths"] = {"markdown": str(md_path), "json": str(json_path)}
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def annotation_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Causal Agent Bench Human Validation Annotation",
        "type": "object",
        "required": ANNOTATION_COLUMNS,
        "properties": {
            "sample_id": {"type": "string", "minLength": 1},
            "trajectory_id": {"type": "string", "minLength": 1},
            "task_id": {"type": "string", "minLength": 1},
            "intervention_type": {"type": "string"},
            "clean_or_intervention": {"type": "string", "enum": ["clean", "intervention"]},
            "predicted_failure_category": {"type": "string"},
            "task_understandable_yes_no": {"type": "string", "enum": ["yes", "no", "unsure", ""]},
            "intervention_isolation_valid_yes_no": {"type": "string", "enum": ["yes", "no", "unsure", ""]},
            "gold_answer_correct_yes_no": {"type": "string", "enum": ["yes", "no", "unsure", ""]},
            "trajectory_label_valid_yes_no": {"type": "string", "enum": ["yes", "no", "unsure", ""]},
            "annotator_failure_category": {"type": "string"},
            "evidence_span_or_step": {"type": "string"},
            "invalid_sample_flag": {"type": "string", "enum": ["true", "false", ""]},
            "invalid_sample_reason": {"type": "string"},
            "confidence_1_to_5": {"type": "integer", "minimum": 1, "maximum": 5},
            "notes": {"type": "string"},
            "adjudication_required": {"type": "boolean"},
            "adjudicated_label": {"type": ["string", "null"]},
            "annotator_id_hash": {"type": "string"},
            "timestamp": {"type": "string", "format": "date-time"},
        },
        "additionalProperties": False,
    }


def human_validation_packet_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Human Validation Dry-Run Packet",
            "",
            f"Generated: {payload['generated_at']}",
            "",
            payload["scope"],
            "",
            "## Contents",
            "",
            f"- Annotation CSV template: `{payload['templates']['csv']}`",
            f"- Annotation JSON schema: `{payload['templates']['schema']}`",
            "",
            "## Claim Safety",
            "",
            "- C3 remains blocked until real annotation artifacts, agreement metrics, and adjudication records exist.",
            "- C10 remains blocked until real annotation artifacts verify intervention validity and label quality.",
            "- Table 5 placeholders cannot support claims and must be generated only from real completed annotations.",
            "- This packet is workflow scaffolding, not empirical evidence.",
            "",
            "## Annotation Protocol (planned)",
            "",
            "1. Export a stratified sample from an eligible provider-backed run (not available yet).",
            "2. Two annotators per item complete the CSV using `annotation_sheet_template.csv`.",
            "3. Adjudicate disagreements; record `adjudication_required` and `adjudicated_label`.",
            "4. Compute agreement metrics offline; **do not claim** C3/C10 until artifacts pass claim ledger gates.",
            "",
            "## Dry-Run Sample",
            "",
            "- `human_validation_dry_run_sample` uses **synthetic fixtures only** (non-scientific).",
            "- Use it to test the workflow, not to support paper claims.",
            "",
            "## Agreement Metrics",
            "",
            "- Cohen's kappa / percent agreement are **planned**; no values are reported in this no-run packet.",
            "- `tables/table5_human_validation_agreement.csv` is a **placeholder** until real annotations exist.",
            "",
            "## Reviewer / Advisor Notes",
            "",
            "- You may approve protocol review; do not treat templates as completed human validation.",
            "- Table 5 cannot support empirical claims at the current evidence state.",
            "",
        ]
    )


def trajectory_packet_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "AnonymizedTrajectoryPacket",
        "type": "object",
        "required": ["sample_id", "task_metadata", "trajectory_steps", "redaction_notice"],
        "properties": {
            "sample_id": {"type": "string"},
            "task_metadata": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string"},
                    "domain": {"type": "string"},
                    "clean_or_intervention": {"type": "string"},
                    "intervention_type": {"type": "string"},
                    "user_instruction": {"type": "string"},
                    "success_criteria": {"type": "array"},
                },
            },
            "trajectory_steps": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "step_index": {"type": "integer"},
                        "action_type": {"type": "string"},
                        "tool_name": {"type": ["string", "null"]},
                        "observation_excerpt": {"type": "string"},
                    },
                },
            },
            "predicted_failure_category": {"type": "string"},
            "provider_model_redacted": {"type": "boolean", "const": True},
            "synthetic_fixture": {"type": "boolean"},
            "not_real_llm_behavior": {"type": "boolean"},
            "redaction_notice": {"type": "string"},
        },
        "additionalProperties": False,
    }


def _write_template_csv(path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(ANNOTATION_COLUMNS)


def _write_adjudication_csv(path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(ADJUDICATION_COLUMNS)


def _codebook_markdown() -> str:
    return "\n".join(
        [
            "# Annotation Codebook",
            "",
            "Dry-run / protocol scaffolding only. No annotations exist yet.",
            "",
            "## Validity questions",
            "",
            "- `task_understandable_yes_no`: Can a competent annotator understand the task without hidden repo context?",
            "- `intervention_isolation_valid_yes_no`: Does the intervention vary one intended factor only (C10)?",
            "- `gold_answer_correct_yes_no`: Is the reference gold answer plausible and complete?",
            "- `trajectory_label_valid_yes_no`: Does the predicted failure category match visible trajectory evidence (C3)?",
            "",
            "## Invalid sample flags",
            "",
            "Set `invalid_sample_flag=true` for leakage, missing steps, ambiguous instructions, or PII.",
            "Record `invalid_sample_reason`. Invalid items are excluded from agreement metrics.",
            "",
            "## Failure categories",
            "",
            "tool_overuse, premature_stopper, contradiction_blind, memory_blind, argument_sloppy,",
            "recovery_weak, final_answer_hallucinator, retry_loop_agent, other, no_failure_detected",
            "",
        ]
    )


def _agreement_summary_template() -> str:
    return "\n".join(
        [
            "# Agreement Summary Template",
            "",
            "**Status:** PLACEHOLDER — populate only after real completed annotations.",
            "",
            "| Metric | Value |",
            "|---|---|",
            "| Items annotated | TBD |",
            "| Items adjudicated | TBD |",
            "| Percent agreement (failure category) | TBD |",
            "| Cohen's kappa (2 annotators) | TBD |",
            "| Invalid samples excluded | TBD |",
            "",
            "Do not fabricate kappa or agreement values. C3/C10 remain blocked until this file is filled from real data.",
            "",
        ]
    )


def _annotator_readme() -> str:
    return "\n".join(
        [
            "# Annotator README",
            "",
            "You are reviewing **anonymized trajectory packets** for benchmark validity (not model leaderboard claims).",
            "",
            "1. Read task metadata and trajectory steps only — do not access provider configs or API keys.",
            "2. Complete `annotation_sheet_template.csv` independently.",
            "3. Answer validity questions before assigning a failure category.",
            "4. Flag invalid samples; do not guess when evidence is missing.",
            "5. Dry-run synthetic samples are labeled `synthetic_fixture=true` and are **not** scientific evidence.",
            "",
            "C3 and C10 are blocked until real annotations and adjudication exist.",
            "",
        ]
    )


def _adjudicator_readme() -> str:
    return "\n".join(
        [
            "# Adjudicator README",
            "",
            "Review disagreements using `adjudication_sheet_template.csv` only.",
            "",
            "1. Compare annotator labels and evidence spans.",
            "2. Record `adjudicator_label` and `adjudicator_rationale`.",
            "3. Mark `taxonomy_revision_needed` when the failure taxonomy is insufficient.",
            "4. Do not infer model performance or promote paper claims.",
            "",
            "Agreement metrics are computed offline after adjudication — never fabricate kappa values.",
            "",
        ]
    )
