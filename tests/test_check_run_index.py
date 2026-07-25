"""Tests for RUN_INDEX freshness checker script."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def test_check_run_index_fresh_fixture(tmp_path: Path) -> None:
    results = tmp_path / "results"
    results.mkdir()
    run_dir = results / "run_a"
    run_dir.mkdir()
    (run_dir / "run_metadata.json").write_text('{"run_id":"run_a"}\n', encoding="utf-8")
    (results / "RUN_INDEX.jsonl").write_text(json.dumps({"run_id": "run_a"}) + "\n", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(REPO / "scripts/check_run_index.py"), "--json"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env={**__import__("os").environ, "PYTHONPATH": str(REPO / "src")},
    )
    payload = json.loads(proc.stdout)
    assert payload["index_stale"] is False
    assert proc.returncode == 0


def test_check_run_index_stale_fixture(tmp_path: Path) -> None:
    results = tmp_path / "results"
    results.mkdir()
    for name in ("run_a", "run_b"):
        d = results / name
        d.mkdir()
        (d / "run_metadata.json").write_text(f'{{"run_id":"{name}"}}\n', encoding="utf-8")
    (results / "RUN_INDEX.jsonl").write_text(json.dumps({"run_id": "run_a"}) + "\n", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(REPO / "scripts/check_run_index.py")],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env={**__import__("os").environ, "PYTHONPATH": str(REPO / "src")},
    )
    assert proc.returncode == 1
    assert "index_stale=True" in proc.stdout
