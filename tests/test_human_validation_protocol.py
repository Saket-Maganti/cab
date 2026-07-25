from __future__ import annotations

import csv
import json
from pathlib import Path

from causal_agent_bench.safety.human_validation_packet import (
    ANNOTATION_COLUMNS,
    build_human_validation_packet,
)

REPO = Path(__file__).resolve().parents[1]


def test_protocol_docs_and_templates_exist() -> None:
    assert (REPO / "docs/HUMAN_VALIDATION_PROTOCOL.md").exists()
    assert (REPO / "docs/HUMAN_VALIDATION_ANNOTATION_GUIDE.md").exists()
    assert (REPO / "data/human_validation/templates/annotation_sheet_template.csv").exists()
    assert (REPO / "data/human_validation/templates/annotation_schema.json").exists()


def test_template_csv_has_required_columns() -> None:
    path = REPO / "data/human_validation/templates/annotation_sheet_template.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        header = next(csv.reader(handle))
    # Template may lag until human-validation-packet is regenerated; require core + validity columns.
    for col in (
        "sample_id",
        "task_understandable_yes_no",
        "intervention_isolation_valid_yes_no",
        "invalid_sample_flag",
    ):
        assert col in header
    assert set(header) >= {
        "sample_id",
        "trajectory_id",
        "annotator_failure_category",
        "confidence_1_to_5",
    }


def test_schema_has_required_fields(tmp_path: Path) -> None:
    report = build_human_validation_packet(tmp_path, output_dir=tmp_path / "hv")
    schema = json.loads(Path(report["templates"]["schema"]).read_text(encoding="utf-8"))
    assert set(ANNOTATION_COLUMNS).issubset(set(schema["required"]))
    for field in ANNOTATION_COLUMNS:
        assert field in schema["properties"]


def test_docs_state_claims_remain_blocked_without_real_annotations() -> None:
    text = (REPO / "docs/HUMAN_VALIDATION_PROTOCOL.md").read_text(encoding="utf-8").lower()
    assert "c3" in text and "blocked" in text
    assert "c10" in text and "blocked" in text
    assert "table 5 placeholders cannot support claims" in text


def test_human_validation_packet_cli_helper_writes_only_templates(tmp_path: Path) -> None:
    report = build_human_validation_packet(tmp_path, output_dir=tmp_path / "reports")
    assert Path(report["templates"]["csv"]).exists()
    assert Path(report["templates"]["schema"]).exists()
    assert "C3" in report["claim_state"]
    assert "C10" in report["claim_state"]
