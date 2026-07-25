from __future__ import annotations

import csv
import json
from pathlib import Path

from causal_agent_bench.safety.human_validation_packet import ANNOTATION_COLUMNS
from causal_agent_bench.safety.human_validation_sampler import build_human_validation_dry_run_sample

REPO = Path(__file__).resolve().parents[1]


def test_human_validation_dry_run_sample_outputs_non_scientific_rows(tmp_path: Path) -> None:
    report = build_human_validation_dry_run_sample(
        tmp_path,
        fixtures_dir=REPO / "tests/fixtures/synthetic_trajectories",
        output_dir=tmp_path / "reports",
    )
    csv_path = Path(report["report_paths"]["csv"])
    rows = list(csv.DictReader(csv_path.open(encoding="utf-8")))
    assert rows
    assert set(ANNOTATION_COLUMNS).issubset(rows[0].keys())
    assert all(row["synthetic_fixture"] == "True" for row in rows)
    assert all(row["scientific_evidence"] == "False" for row in rows)
    manifest = json.loads(Path(report["report_paths"]["json"]).read_text(encoding="utf-8"))
    assert manifest["claims"]["C3"] == "blocked"
    assert manifest["claims"]["C10"] == "blocked"
    text = Path(report["report_paths"]["markdown"]).read_text(encoding="utf-8").lower()
    assert "not scientific evidence" in text
    assert "c3 and c10 remain blocked" in text
