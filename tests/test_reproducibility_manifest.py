from __future__ import annotations

from pathlib import Path

from causal_agent_bench.safety.reproducibility_manifest import build_reproducibility_manifest


def _touch(p: Path, text: str = "") -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def test_manifest_missing_license_is_blocker(tmp_path: Path) -> None:
    report = build_reproducibility_manifest(tmp_path, output_dir=tmp_path / "out")
    assert "LICENSE file missing." in report["blockers"]
    assert report["verdicts"]["ready_for_public_reproducibility_packet"] is False


def test_manifest_with_full_setup(tmp_path: Path) -> None:
    _touch(tmp_path / "LICENSE")
    _touch(tmp_path / "DATA_LICENSE.md")
    _touch(tmp_path / "CITATION.cff")
    _touch(tmp_path / "pyproject.toml")
    _touch(tmp_path / "uv.lock")
    _touch(tmp_path / ".python-version", "3.11")
    _touch(tmp_path / "data/frozen/pilot_v0.1/instances.jsonl")
    report = build_reproducibility_manifest(tmp_path, output_dir=tmp_path / "out")
    assert report["verdicts"]["license_complete"] is True
    assert report["verdicts"]["dependency_locked"] is True
    assert report["summary"]["frozen_dataset_count"] == 1
    assert report["verdicts"]["ready_for_public_reproducibility_packet"] is True


def test_manifest_detects_unfrozen_datasets(tmp_path: Path) -> None:
    _touch(tmp_path / "LICENSE")
    _touch(tmp_path / "data/processed/pilot_v0_1/instances.jsonl")
    report = build_reproducibility_manifest(tmp_path, output_dir=tmp_path / "out")
    assert report["summary"]["unfrozen_dataset_count"] == 1
    assert report["verdicts"]["all_datasets_frozen"] is False


def test_manifest_lists_forbidden_run_tests(tmp_path: Path) -> None:
    _touch(tmp_path / "LICENSE")
    _touch(tmp_path / "tests/test_paper_assets.py", "# placeholder")
    _touch(tmp_path / "tests/test_experiment_runner.py", "# placeholder")
    report = build_reproducibility_manifest(tmp_path, output_dir=tmp_path / "out")
    assert "test_paper_assets" in report["forbidden_run_tests"]
    assert "test_experiment_runner" in report["forbidden_run_tests"]
