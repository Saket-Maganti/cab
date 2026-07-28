"""No-run human validation protocol packet writer."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from causal_agent_bench.safety.common import write_dual_report
from causal_agent_bench.safety.human_review_gate import (
    ADJUDICATION_COLUMNS as C10_ADJUDICATION_COLUMNS,
)
from causal_agent_bench.safety.human_review_gate import (
    MANIPULATION_CHECK_FILE,
    PREREQUISITES_FILE,
    REVIEW_COLUMNS,
    REVIEW_DIMENSIONS,
    REVIEWER_REGISTRY_COLUMNS,
    candidate_slice_hash,
)
from causal_agent_bench.safety.manipulation_checks import (
    INTERVENTION_CHECK_LINKAGE,
    build_manipulation_check_report,
    write_manipulation_check_report,
)

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

C10_REVIEW_ITEMS_FILE = "review_items.jsonl"
C10_REVIEW_FILE = "review_judgments.csv"
C10_REVIEWER_REGISTRY_FILE = "reviewer_registry.csv"
C10_ADJUDICATION_FILE = "adjudication.csv"
C10_SESSION_FILE = "review_session.json"
C10_PACKET_MANIFEST_FILE = "packet_manifest.json"


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


def build_c10_review_packet(
    repo_root: str | Path,
    *,
    output_dir: str | Path = "data/human_validation/compact20_real_review",
    candidate_manifest: str | Path = (
        "data/compact20_reviewed/compact20_reviewed_manifest.json"
    ),
    instances_path: str | Path = "data/processed/pilot_v0_1/instances.jsonl",
    reviewers_per_candidate: int = 2,
) -> dict[str, Any]:
    """Create a complete blank C10 packet without inventing human inputs.

    Existing completed review, registry, adjudication, or real-session data is
    never overwritten. Candidate and reviewer-slot rows contain only
    deterministic assignment metadata; all human fields remain blank.
    """

    if reviewers_per_candidate < 2:
        raise ValueError("C10 requires at least two independent reviewers")
    root = Path(repo_root).resolve()
    out = _resolve(root, output_dir)
    manifest_path = _resolve(root, candidate_manifest)
    source_path = _resolve(root, instances_path)
    out.mkdir(parents=True, exist_ok=True)

    manifest = _read_json_object(manifest_path)
    raw_candidates = manifest.get("candidates")
    candidates = [
        row
        for row in (raw_candidates if isinstance(raw_candidates, list) else [])
        if isinstance(row, dict) and str(row.get("candidate_id") or "").strip()
    ]
    if not candidates:
        raise ValueError("candidate manifest contains no usable candidates")
    candidate_by_id = {
        str(row["candidate_id"]): row for row in candidates
    }
    manifest_sha256 = _sha256_file(manifest_path)
    slice_hash = candidate_slice_hash(candidate_by_id)
    instances = _read_jsonl(source_path)
    instances_by_id = {
        str(row.get("instance_id") or ""): row
        for row in instances
        if str(row.get("instance_id") or "")
    }

    review_items = [
        _c10_review_item(
            candidate,
            instances_by_id=instances_by_id,
        )
        for candidate in sorted(
            candidates,
            key=lambda row: str(row.get("candidate_id") or ""),
        )
    ]
    review_items_path = out / C10_REVIEW_ITEMS_FILE
    review_items_path.write_text(
        "".join(
            json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n"
            for row in review_items
        ),
        encoding="utf-8",
    )

    review_path = out / C10_REVIEW_FILE
    _refuse_completed_csv_overwrite(
        review_path,
        identity_columns=("reviewer_id", "timestamp"),
    )
    with review_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(REVIEW_COLUMNS),
            lineterminator="\n",
        )
        writer.writeheader()
        for candidate in sorted(
            candidates,
            key=lambda row: str(row.get("candidate_id") or ""),
        ):
            for reviewer_slot in range(1, reviewers_per_candidate + 1):
                row = dict.fromkeys(REVIEW_COLUMNS, "")
                row["candidate_id"] = candidate["candidate_id"]
                row["reviewer_slot"] = str(reviewer_slot)
                writer.writerow(row)

    registry_path = out / C10_REVIEWER_REGISTRY_FILE
    _refuse_completed_csv_overwrite(
        registry_path,
        identity_columns=("reviewer_id", "registered_at"),
    )
    _write_csv_header(registry_path, list(REVIEWER_REGISTRY_COLUMNS))

    adjudication_path = out / C10_ADJUDICATION_FILE
    _refuse_completed_csv_overwrite(
        adjudication_path,
        identity_columns=("adjudicator_id", "timestamp"),
    )
    with adjudication_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(C10_ADJUDICATION_COLUMNS),
            lineterminator="\n",
        )
        writer.writeheader()
        for candidate in sorted(
            candidates,
            key=lambda row: str(row.get("candidate_id") or ""),
        ):
            row = dict.fromkeys(C10_ADJUDICATION_COLUMNS, "")
            row["candidate_id"] = candidate["candidate_id"]
            writer.writerow(row)

    session_path = out / C10_SESSION_FILE
    existing_session = _read_json_object(session_path)
    if existing_session.get("review_mode") in {"real_human", "fixture"}:
        raise FileExistsError(
            f"refusing to overwrite completed review session: {session_path}"
        )
    session = {
        "schema_version": "cab_c10_review_session_v1",
        "review_mode": "pending",
        "evidence_class": "HUMAN_INPUT_REQUIRED",
        "candidate_manifest": _relative(manifest_path, root),
        "candidate_manifest_sha256": manifest_sha256,
        "candidate_slice_hash": slice_hash,
        "model_output_blinded": True,
        "model_identity_blinded": True,
        "ai_or_proxy_review_permitted": False,
        "human_only_attestation": False,
        "human_only_attestation_note": (
            "Set true only after genuine humans complete the registered "
            "independent review without AI/proxy assistance."
        ),
        "completed_at": None,
    }
    session_path.write_text(
        json.dumps(session, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    manipulation_report = build_manipulation_check_report(
        manifest_path,
        source_path,
    )
    manipulation_path = write_manipulation_check_report(
        manipulation_report,
        out / MANIPULATION_CHECK_FILE,
    )
    prerequisites_path = out / PREREQUISITES_FILE
    prerequisites = {
        "schema_version": "cab_c10_prerequisites_v1",
        "evidence_class": "HUMAN_INPUT_REQUIRED",
        "candidate_manifest_sha256": manifest_sha256,
        "leakage_gate": {
            "passed": False,
            "report_path": "",
            "report_sha256": "",
            "status": "PENDING_VERIFIED_REPORT",
        },
        "answer_contract": {
            "passed": False,
            "report_path": "",
            "report_sha256": "",
            "status": "PENDING_VERIFIED_REPORT",
        },
        "slice_freeze": {
            "frozen": True,
            "candidate_count": len(candidates),
            "candidate_manifest_sha256": manifest_sha256,
            "slice_hash": slice_hash,
            "scope": "C10 review slice; regenerate if candidate membership changes.",
        },
        "manipulation_checks": {
            "passed": bool(
                manipulation_report["all_candidates_linked"]
                and manipulation_report["all_applicable_checks_passed"]
            ),
            "report_path": MANIPULATION_CHECK_FILE,
            "report_sha256": _sha256_file(manipulation_path),
        },
    }
    prerequisites_path.write_text(
        json.dumps(prerequisites, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    qualification_path = out / "REVIEWER_QUALIFICATION_EXAMPLES.md"
    qualification_path.write_text(
        _qualification_examples_markdown(),
        encoding="utf-8",
    )

    packet_files = [
        review_items_path,
        review_path,
        registry_path,
        adjudication_path,
        session_path,
        manipulation_path,
        prerequisites_path,
        qualification_path,
    ]
    packet_manifest = {
        "schema_version": "cab_c10_packet_manifest_v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "evidence_class": "HUMAN_INPUT_REQUIRED",
        "candidate_count": len(candidates),
        "reviewers_per_candidate": reviewers_per_candidate,
        "review_assignment_rows": len(candidates)
        * reviewers_per_candidate,
        "genuine_human_review_rows": 0,
        "genuine_human_adjudication_rows": 0,
        "review_dimensions": list(REVIEW_DIMENSIONS),
        "candidate_manifest_sha256": manifest_sha256,
        "candidate_slice_hash": slice_hash,
        "files": {
            path.name: {
                "sha256": _sha256_file(path),
                "path": _relative(path, root),
            }
            for path in packet_files
        },
        "claim_boundary": (
            "Blank packet and deterministic checks are not human evidence. "
            "C10 remains pending until the canonical validator passes genuine "
            "dual review, adjudication, leakage, answer-contract, and freeze gates."
        ),
    }
    packet_manifest_path = out / C10_PACKET_MANIFEST_FILE
    packet_manifest_path.write_text(
        json.dumps(packet_manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        "output_dir": str(out),
        "candidate_count": len(candidates),
        "review_assignment_rows": len(candidates)
        * reviewers_per_candidate,
        "genuine_human_review_rows": 0,
        "genuine_human_adjudication_rows": 0,
        "candidate_slice_hash": slice_hash,
        "manipulation_checks_passed": manipulation_report[
            "all_applicable_checks_passed"
        ],
        "packet_manifest": str(packet_manifest_path),
    }


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
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(ANNOTATION_COLUMNS)


def _write_adjudication_csv(path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
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


def _c10_review_item(
    candidate: dict[str, Any],
    *,
    instances_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    clean_id = str(candidate.get("clean_instance_id") or "")
    intervention_id = str(
        candidate.get("intervention_instance_id") or ""
    )
    clean = instances_by_id.get(clean_id, {})
    intervention_instance = instances_by_id.get(intervention_id, {})
    base_task = intervention_instance.get("base_task")
    if not isinstance(base_task, dict):
        base_task = clean.get("base_task")
    if not isinstance(base_task, dict):
        base_task = {}
    intervention = intervention_instance.get("intervention")
    if not isinstance(intervention, dict):
        intervention = {}
    family = str(candidate.get("family") or intervention.get("family") or "")
    return {
        "schema_version": "cab_c10_review_item_v1",
        "evidence_class": "HUMAN_INPUT_REQUIRED",
        "candidate_id": candidate.get("candidate_id"),
        "base_task_id": candidate.get("base_task_id"),
        "clean_instance_id": clean_id,
        "intervention_instance_id": intervention_id,
        "domain": candidate.get("domain") or base_task.get("domain"),
        "difficulty": candidate.get("difficulty")
        or base_task.get("difficulty"),
        "intervention_family": family,
        "manipulation_check_name": INTERVENTION_CHECK_LINKAGE.get(family),
        "model_output_included": False,
        "model_identity_included": False,
        "reviewer_visible_task": {
            "user_instruction": base_task.get("user_instruction")
            or (base_task.get("goal") or {}).get("user_instruction")
            if isinstance(base_task.get("goal"), dict)
            else base_task.get("user_instruction"),
            "success_criteria": base_task.get("success_criteria")
            or (base_task.get("goal") or {}).get("success_criteria")
            if isinstance(base_task.get("goal"), dict)
            else base_task.get("success_criteria"),
            "required_information": (
                base_task.get("goal") or {}
            ).get("required_information")
            if isinstance(base_task.get("goal"), dict)
            else [],
            "forbidden_assumptions": base_task.get(
                "forbidden_assumptions"
            ),
            "clean_available_tools": clean.get("available_tools"),
            "intervention_available_tools": intervention_instance.get(
                "available_tools"
            ),
        },
        "reviewer_visible_gold_and_scoring": {
            "clean_gold_answer": (base_task.get("goal") or {}).get(
                "expected_final_answer"
            )
            if isinstance(base_task.get("goal"), dict)
            else None,
            "clean_answer_contract": base_task.get("answer_contract"),
            "clean_gold_answer_policy": base_task.get("gold_answer_policy"),
            "clean_scorer_policy": base_task.get("scorer_policy"),
            "intervention_answer_contract": intervention.get(
                "answer_contract"
            ),
            "intervention_gold_answer_policy": intervention.get(
                "gold_answer_policy"
            ),
            "intervention_scorer_policy": intervention.get("scorer_policy"),
        },
        "reviewer_visible_intervention": {
            "description": intervention.get("description"),
            "changed_factor": intervention.get("changed_factor"),
            "target_factor": intervention.get("target_factor"),
            "non_target_factors": intervention.get("non_target_factors"),
            "expected_robust_behavior": intervention.get(
                "expected_robust_behavior"
            )
            or intervention.get("expected_behavior"),
            "expected_final_answer_change": intervention.get(
                "expected_final_answer_change"
            ),
            "tool_availability_patch": intervention.get(
                "tool_availability_patch"
            ),
            "tool_output_patch": intervention.get("tool_output_patch"),
            "memory_patch": intervention.get("memory_patch"),
            "instruction_patch": intervention.get("instruction_patch"),
        },
        "human_fields": dict.fromkeys(REVIEW_DIMENSIONS),
    }


def _qualification_examples_markdown() -> str:
    return """# Reviewer Qualification Examples

Status: `DESIGN_ONLY`. These are worked examples, not reviewer identities,
responses, human rows, or C10 evidence.

Reviewers must complete an independently administered calibration derived from
these patterns and achieve at least 80%. The coordinator records only the
privacy-safe reviewer ID and aggregate score in `reviewer_registry.csv`.

## Example 1 — valid tool removal

A required search tool appears in the clean condition and is absent in the
intervention condition. The user goal and gold policy are unchanged, while an
alternate route remains available.

- manipulation success: `yes`
- goal preservation: `yes`
- invariance preservation: `yes`
- exclusion recommendation: `include`

## Example 2 — multi-factor confound

The intervention removes a tool and also rewrites the user's requested output
format.

- manipulation success: `yes`
- goal preservation: `no`
- invariance preservation: `no`
- exclusion recommendation: `exclude`

## Example 3 — deterministic failure but no recovery route

The intended failure is present, but the item requires evidence obtainable
only through the failed tool and the answer contract forbids abstention.

- manipulation success: `yes`
- solvability: `no`
- answer-contract correctness: `no`
- exclusion recommendation: `revise`

## Example 4 — managed ambiguity

Two interpretations are plausible, and the task explicitly permits a
clarification question or a stated assumption.

- task clarity: `yes`
- ambiguity: `acceptable`
- answer-contract correctness: `yes`

## Example 5 — scorer mismatch

The reference permits a calibrated abstention, while the scorer accepts only
the unchanged clean answer.

- clean gold correctness: `yes`
- answer-contract correctness: `yes`
- scorer compatibility: `no`
- exclusion recommendation: `revise`

Do not copy these labels into candidate review rows. Candidate judgments must
be made independently from the blinded packet.
"""


def _refuse_completed_csv_overwrite(
    path: Path,
    *,
    identity_columns: tuple[str, ...],
) -> None:
    if not path.exists():
        return
    try:
        with path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
    except (OSError, csv.Error) as exc:
        raise FileExistsError(
            f"refusing to overwrite unreadable existing review file: {path}"
        ) from exc
    if any(
        any(str(row.get(column) or "").strip() for column in identity_columns)
        for row in rows
    ):
        raise FileExistsError(
            f"refusing to overwrite completed human input: {path}"
        )


def _write_csv_header(path: Path, columns: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        csv.writer(handle, lineterminator="\n").writerow(columns)


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    rows: list[dict[str, Any]] = []
    for line in lines:
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def _sha256_file(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def _resolve(root: Path, path: str | Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else root / candidate


def _relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)
