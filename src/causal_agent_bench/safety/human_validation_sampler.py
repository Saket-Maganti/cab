"""Create synthetic-only human-validation dry-run sample packets."""

from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from causal_agent_bench.safety.human_validation_packet import (
    ANNOTATION_COLUMNS,
    trajectory_packet_schema,
)
from causal_agent_bench.safety.synthetic_fixtures import load_synthetic_fixtures

EXTRA_COLUMNS = ["synthetic_fixture", "not_real_llm_behavior", "scientific_evidence", "paper_eligible"]


def build_human_validation_dry_run_sample(
    repo_root: str | Path,
    *,
    fixtures_dir: str | Path = "tests/fixtures/synthetic_trajectories",
    output_dir: str | Path = "reports/human_validation_dry_run",
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    fixture_root = Path(fixtures_dir)
    if not fixture_root.is_absolute():
        fixture_root = root / fixture_root
    out = Path(output_dir)
    if not out.is_absolute():
        out = root / out
    out.mkdir(parents=True, exist_ok=True)
    fixtures = load_synthetic_fixtures(fixture_root)
    rows = [_row(name, fixture) for name, fixture in sorted(fixtures.items())]
    csv_path = out / "sample_sheet.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=ANNOTATION_COLUMNS + EXTRA_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    manifest = {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": "Synthetic dry-run sample only; not real LLM behavior, not paper-eligible, no claim promoted.",
        "source": "synthetic fixtures only",
        "sample_count": len(rows),
        "scientific_evidence": False,
        "paper_eligible": False,
        "claims": {"C3": "blocked", "C10": "blocked"},
        "sample_sheet": str(csv_path),
        "summary": {
            "sample_count": len(rows),
            "is_synthetic": True,
            "scientific_evidence": False,
            "paper_eligible": False,
        },
        "verdicts": {
            "real_llm_behavior": False,
            "paper_eligible": False,
            "claims_supported": False,
            "annotation_flow_dry_run_only": True,
        },
    }
    manifest_path = out / "sample_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    packet_path = out / "sample_packet.md"
    packet_path.write_text(_packet_markdown(manifest, rows), encoding="utf-8")
    trajectory_packets = [_trajectory_packet(name, fixture) for name, fixture in sorted(fixtures.items())]
    traj_schema_path = out / "trajectory_packet_schema.json"
    traj_schema_path.write_text(json.dumps(trajectory_packet_schema(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    traj_dir = out / "trajectory_packets"
    traj_dir.mkdir(parents=True, exist_ok=True)
    traj_paths = []
    for packet in trajectory_packets[:8]:
        path = traj_dir / f"{packet['sample_id']}.json"
        path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        traj_paths.append(str(path))
    manifest["trajectory_packet_paths"] = traj_paths
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "report_paths": {
            "csv": str(csv_path),
            "markdown": str(packet_path),
            "json": str(manifest_path),
            "trajectory_schema": str(traj_schema_path),
            "trajectory_packets": traj_paths,
        },
        **manifest,
    }


def _row(name: str, fixture: dict[str, Any]) -> dict[str, Any]:
    metadata_raw = fixture.get("metadata")
    metadata = metadata_raw if isinstance(metadata_raw, dict) else {}
    return {
        "sample_id": f"synthetic_{name}",
        "trajectory_id": str(fixture.get("instance_id") or name),
        "task_id": str(fixture.get("base_task_id") or fixture.get("instance_id") or name),
        "intervention_type": "synthetic_metric_fixture",
        "clean_or_intervention": "intervention",
        "predicted_failure_category": str(metadata.get("expected_failure_category") or ""),
        "task_understandable_yes_no": "",
        "intervention_isolation_valid_yes_no": "",
        "gold_answer_correct_yes_no": "",
        "trajectory_label_valid_yes_no": "",
        "annotator_failure_category": "",
        "evidence_span_or_step": "synthetic fixture steps",
        "confidence_1_to_5": "",
        "invalid_sample_flag": "",
        "invalid_sample_reason": "",
        "notes": "Dry-run synthetic sample; not real LLM behavior.",
        "adjudication_required": "",
        "adjudicated_label": "",
        "annotator_id_hash": "",
        "timestamp": "",
        "synthetic_fixture": True,
        "not_real_llm_behavior": True,
        "scientific_evidence": False,
        "paper_eligible": False,
    }


def _trajectory_packet(name: str, fixture: dict[str, Any]) -> dict[str, Any]:
    steps_raw = fixture.get("steps")
    steps = steps_raw if isinstance(steps_raw, list) else []
    packet_steps = []
    for index, step in enumerate(steps[:12]):
        if not isinstance(step, dict):
            continue
        packet_steps.append(
            {
                "step_index": index,
                "action_type": str(step.get("action_type") or step.get("type") or "unknown"),
                "tool_name": step.get("tool_name"),
                "observation_excerpt": str(step.get("observation") or step.get("content") or "")[:240],
            }
        )
    return {
        "sample_id": f"synthetic_{name}",
        "task_metadata": {
            "task_id": str(fixture.get("base_task_id") or fixture.get("instance_id") or name),
            "domain": "synthetic_fixture",
            "clean_or_intervention": "intervention",
            "intervention_type": "synthetic_metric_fixture",
            "user_instruction": "Synthetic dry-run packet for workflow rehearsal only.",
            "success_criteria": ["Demonstrate annotation workflow."],
        },
        "trajectory_steps": packet_steps or [{"step_index": 0, "action_type": "synthetic", "tool_name": None, "observation_excerpt": "synthetic"}],
        "predicted_failure_category": str((fixture.get("metadata") or {}).get("expected_failure_category") or ""),
        "provider_model_redacted": True,
        "synthetic_fixture": True,
        "not_real_llm_behavior": True,
        "redaction_notice": "Synthetic fixture only. Not real LLM behavior. Not paper-eligible.",
    }


def _packet_markdown(manifest: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Human Validation Dry-Run Sample Packet",
        "",
        "Synthetic fixtures only. This packet is for annotation workflow rehearsal and metric-label calibration.",
        "",
        "It is not real LLM behavior, not scientific evidence, not paper-eligible, and does not support C3 or C10.",
        "",
        "C3 and C10 remain blocked until real annotations, agreement metrics, and adjudication artifacts exist.",
        "",
        "## Annotator Instructions",
        "",
        "Review the predicted failure category, identify the supporting synthetic step span, assign a label, and record confidence.",
        "",
        "## Example Rows",
        "",
    ]
    for row in rows[:8]:
        lines.append(f"- `{row['sample_id']}` predicted `{row['predicted_failure_category']}`")
    lines.append("")
    return "\n".join(lines)
