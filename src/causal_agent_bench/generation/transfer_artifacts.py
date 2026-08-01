"""Deterministic artifact-rich synthetic transfer bundle materialization."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from io import StringIO
from pathlib import Path
from typing import Any, Final

from causal_agent_bench.hashing import stable_hash

ARTIFACT_GENERATOR_VERSION: Final[str] = "cab_transfer_artifacts_v1.0.0"
STUDY_NAME: Final[str] = "artifact_rich_synthetic_transfer"
_RECORD_RE = re.compile(r"\bRecord\s+([0-9a-f]{8})\b", re.IGNORECASE)
_DISPOSITION_RE = re.compile(
    r"\b(?:disposition\s+code\s+is|disposition_code[\"']?\s*[:=]\s*[\"']?)"
    r"\s*([0-9a-f]{10})\b",
    re.IGNORECASE,
)

DOMAIN_LAYOUTS: Final[dict[str, tuple[tuple[str, str], ...]]] = {
    "email_casework": (
        ("01_thread.eml", "eml"),
        ("02_policy_excerpt.md", "markdown"),
        ("03_resolution.json", "json"),
    ),
    "policy_packet": (
        ("01_policy.md", "markdown"),
        ("02_amendment.md", "markdown"),
        ("03_resolution.json", "json"),
    ),
    "spreadsheet_export": (
        ("01_export.csv", "csv"),
        ("02_reconciliation.md", "markdown"),
        ("03_resolution.json", "json"),
    ),
    "calendar_bundle": (
        ("01_calendar.csv", "csv"),
        ("02_thread.eml", "eml"),
        ("03_resolution.json", "json"),
    ),
    "repository_debug": (
        ("01_repo/app.py", "python"),
        ("02_repo/FAILURE.log", "log"),
        ("03_resolution.json", "json"),
    ),
    "service_config_logs": (
        ("01_service.yaml", "yaml"),
        ("02_service.log", "log"),
        ("03_resolution.json", "json"),
    ),
    "incident_response": (
        ("01_incident.log", "log"),
        ("02_timeline.md", "markdown"),
        ("03_resolution.json", "json"),
    ),
    "travel_records": (
        ("01_itinerary.csv", "csv"),
        ("02_messages.eml", "eml"),
        ("03_resolution.json", "json"),
    ),
    "support_tickets": (
        ("01_tickets.json", "json"),
        ("02_agent_notes.md", "markdown"),
        ("03_resolution.json", "json"),
    ),
    "data_pipeline": (
        ("01_pipeline.yaml", "yaml"),
        ("02_run.log", "log"),
        ("03_resolution.json", "json"),
    ),
}


def materialize_transfer_bundle(
    task: dict[str, Any],
    output_dir: str | Path,
) -> dict[str, Any]:
    """Write a heterogeneous clean bundle plus every intervention descriptor."""

    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    domain = str(task["domain"])
    layout = DOMAIN_LAYOUTS.get(domain)
    if layout is None:
        raise ValueError(f"no artifact layout registered for domain {domain!r}")
    facts = [str(value) for value in task["artifact_spec"]["facts"]]
    if len(facts) < 3:
        raise ValueError("transfer artifact materialization requires three facts")
    clean_files: list[Path] = []
    for (relative, format_name), fact in zip(layout, facts, strict=True):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            _render_fact(format_name, fact, domain=domain),
            encoding="utf-8",
        )
        clean_files.append(path)

    patch_files: list[Path] = []
    for mapping in task.get("intervention_mapping", []):
        family = str(mapping["family"])
        patch_dir = root / "interventions" / family
        patch_dir.mkdir(parents=True, exist_ok=True)
        patch = _intervention_patch(family, layout[0][0])
        patch_path = patch_dir / "patch.json"
        patch_path.write_text(
            json.dumps(patch, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        patch_files.append(patch_path)
        if patch.get("materialized_companion"):
            companion = patch_dir / str(patch["materialized_companion"])
            companion.write_text(
                "SYNTHETIC INTERVENTION FIXTURE\n"
                f"family={family}\n"
                "This content is generated and contains no real-world records.\n",
                encoding="utf-8",
            )
            patch_files.append(companion)

    derived = parse_transfer_bundle(root)
    expected = task["hidden_answer_key"]
    if derived != expected:
        raise ValueError(
            "artifact parser derivation does not reproduce the private answer key"
        )
    file_rows = [_file_record(path, root) for path in sorted(clean_files + patch_files)]
    root_hash = stable_hash(file_rows, length=64)
    manifest = {
        "schema_version": "cab_transfer_artifact_manifest_v1",
        "study_name": STUDY_NAME,
        "artifact_class": "artifact_rich_synthetic",
        "generator_version": ARTIFACT_GENERATOR_VERSION,
        "source_claim": "repository-authored deterministic synthetic facts only",
        "copyrighted_or_private_source_count": 0,
        "provenance": {
            "synthetic": True,
            "real_world_origin_claimed": False,
            "license": "project DATA_LICENSE.md",
        },
        "clean_files": [row for row in file_rows if not row["path"].startswith("interventions/")],
        "intervention_files": [row for row in file_rows if row["path"].startswith("interventions/")],
        "parser": {
            "name": "parse_transfer_bundle",
            "version": ARTIFACT_GENERATOR_VERSION,
            "actual_file_read_required": True,
            "supported_formats": sorted({row["format"] for row in file_rows}),
        },
        "tool_route": [
            str(tool.get("name"))
            for tool in task.get("tool_schema", [])
            if isinstance(tool, dict) and tool.get("name")
        ],
        "gold_derivation": {
            "algorithm": "extract two decisive record codes and one disposition code from clean files",
            "derived_gold_sha256": stable_hash(derived, length=64),
            "hidden_answer_key_sha256": stable_hash(expected, length=64),
            "matches_hidden_answer_key": True,
        },
        "bundle_root_sha256": root_hash,
        "human_review_state": "HUMAN_INPUT_REQUIRED_AFTER_MATERIALIZATION",
    }
    manifest_path = root / "artifact_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        "manifest": manifest,
        "manifest_path": str(manifest_path),
        "manifest_sha256": _sha256_file(manifest_path),
        "bundle_root_sha256": root_hash,
        "clean_relative_files": [
            path.relative_to(root).as_posix() for path in clean_files
        ],
        "all_file_count": len(file_rows),
        "format_counts": dict(sorted(Counter(row["format"] for row in file_rows).items())),
    }


def parse_transfer_bundle(bundle_dir: str | Path) -> dict[str, Any]:
    """Derive the exact private gold by reading only clean materialized files."""

    root = Path(bundle_dir)
    chunks: list[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or "interventions" in path.relative_to(root).parts:
            continue
        if path.name == "artifact_manifest.json":
            continue
        chunks.append(path.read_text(encoding="utf-8"))
    text = "\n".join(chunks)
    record_codes: list[str] = []
    for code in _RECORD_RE.findall(text):
        normalized = code.lower()
        if normalized not in record_codes:
            record_codes.append(normalized)
    dispositions: list[str] = []
    for code in _DISPOSITION_RE.findall(text):
        normalized = code.lower()
        if normalized not in dispositions:
            dispositions.append(normalized)
    if len(record_codes) != 2 or len(dispositions) != 1:
        raise ValueError(
            "clean artifact bundle must expose exactly two decisive record codes "
            "and one disposition code"
        )
    return {
        "decisive_record_codes": record_codes,
        "disposition_code": dispositions[0],
        "limitation": "none_if_both_records_verified",
    }


def aggregate_artifact_inventory(
    bundles: list[dict[str, Any]],
) -> dict[str, Any]:
    formats: Counter[str] = Counter()
    for bundle in bundles:
        formats.update(bundle["format_counts"])
    return {
        "schema_version": "cab_transfer_artifact_inventory_v1",
        "study_name": STUDY_NAME,
        "artifact_class": "artifact_rich_synthetic",
        "generator_version": ARTIFACT_GENERATOR_VERSION,
        "bundle_count": len(bundles),
        "artifact_file_count": sum(bundle["all_file_count"] for bundle in bundles),
        "format_counts": dict(sorted(formats.items())),
        "bundle_root_commitment_sha256": stable_hash(
            [bundle["bundle_root_sha256"] for bundle in bundles],
            length=64,
        ),
        "manifest_commitment_sha256": stable_hash(
            [bundle["manifest_sha256"] for bundle in bundles],
            length=64,
        ),
        "all_gold_derivations_match": all(
            bundle["manifest"]["gold_derivation"]["matches_hidden_answer_key"]
            for bundle in bundles
        ),
        "real_world_origin_claimed": False,
        "copyrighted_or_private_source_count": 0,
        "human_review_state": "HUMAN_INPUT_REQUIRED_AFTER_MATERIALIZATION",
    }


def _render_fact(format_name: str, fact: str, *, domain: str) -> str:
    if format_name == "eml":
        return (
            "From: synthetic.sender@example.invalid\n"
            "To: synthetic.recipient@example.invalid\n"
            f"Subject: CAB synthetic {domain} evidence\n"
            "Date: Fri, 01 Aug 2026 00:00:00 +0000\n"
            "Message-ID: <cab-synthetic@example.invalid>\n\n"
            f"{fact}\n"
        )
    if format_name == "csv":
        buffer = StringIO()
        writer = csv.writer(buffer, lineterminator="\n")
        writer.writerow(["source", "evidence"])
        writer.writerow(["cab_synthetic", fact])
        return buffer.getvalue()
    if format_name == "json":
        return json.dumps(
            {"source": "cab_synthetic", "evidence": fact},
            indent=2,
            sort_keys=True,
        ) + "\n"
    if format_name == "yaml":
        escaped = json.dumps(fact)
        return f"source: cab_synthetic\nevidence: {escaped}\n"
    if format_name == "python":
        return (
            '"""Synthetic repository fixture; no executable side effects."""\n\n'
            f"EVIDENCE = {fact!r}\n"
        )
    if format_name == "log":
        return f"2026-08-01T00:00:00Z INFO cab_synthetic evidence={fact}\n"
    return f"# CAB synthetic evidence\n\n{fact}\n"


def _intervention_patch(family: str, target_file: str) -> dict[str, Any]:
    operations: dict[str, dict[str, Any]] = {
        "tool_removal": {"operation": "remove_tool_route", "target": target_file},
        "tool_failure": {"operation": "inject_deterministic_read_error", "target": target_file},
        "tool_corruption": {"operation": "replace_one_record_code", "target": target_file},
        "irrelevant_tools": {
            "operation": "add_irrelevant_tool_descriptor",
            "target": target_file,
            "materialized_companion": "irrelevant_tool.txt",
        },
        "memory_corruption": {
            "operation": "add_stale_memory_record",
            "target": target_file,
            "materialized_companion": "stale_memory.txt",
        },
        "observation_conflict": {
            "operation": "add_conflicting_observation",
            "target": target_file,
            "materialized_companion": "conflict.txt",
        },
        "ambiguous_instruction": {
            "operation": "remove_material_selection_criterion",
            "target": target_file,
        },
        "long_horizon_dependency": {
            "operation": "require_cross_file_dependency",
            "target": target_file,
        },
        "premature_success_signal": {
            "operation": "inject_premature_success_marker",
            "target": target_file,
        },
        "distractor_evidence": {
            "operation": "add_distractor_artifact",
            "target": target_file,
            "materialized_companion": "distractor.txt",
        },
    }
    return {
        "schema_version": "cab_transfer_intervention_patch_v1",
        "family": family,
        "deterministic": True,
        "synthetic": True,
        **operations[family],
    }


def _file_record(path: Path, root: Path) -> dict[str, Any]:
    suffix = path.suffix.lower().lstrip(".") or "text"
    aliases = {"md": "markdown", "py": "python", "txt": "text"}
    return {
        "path": path.relative_to(root).as_posix(),
        "sha256": _sha256_file(path),
        "bytes": path.stat().st_size,
        "format": aliases.get(suffix, suffix),
        "synthetic": True,
    }


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


__all__ = [
    "ARTIFACT_GENERATOR_VERSION",
    "STUDY_NAME",
    "aggregate_artifact_inventory",
    "materialize_transfer_bundle",
    "parse_transfer_bundle",
]
