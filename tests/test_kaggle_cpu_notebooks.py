"""The generated Kaggle CPU notebooks must stay clean, current and CPU-only."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import build_kaggle_cpu_notebooks as generator
from scripts import validate_kaggle_cpu_notebooks as validator

REPO_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_DIR = REPO_ROOT / "notebooks" / "kaggle_cpu"

NOTEBOOKS = sorted(NOTEBOOK_DIR.glob("*.ipynb"))


def test_every_expected_notebook_exists() -> None:
    expected = {spec.filename for spec in generator.SPECS}
    assert {path.name for path in NOTEBOOKS} == expected
    assert len(expected) == 9


def test_the_committed_notebooks_match_the_generator() -> None:
    """A hand-edited notebook drifts from the module it exercises."""

    generator.write_notebooks(check=True)


@pytest.mark.parametrize("path", NOTEBOOKS, ids=lambda path: path.name)
def test_each_notebook_passes_static_validation(path: Path) -> None:
    result = validator.validate_one(path)
    assert result["passed"], result["failed"]


@pytest.mark.parametrize("path", NOTEBOOKS, ids=lambda path: path.name)
def test_no_notebook_carries_committed_output(path: Path) -> None:
    notebook = json.loads(path.read_text())
    for cell in notebook["cells"]:
        if cell["cell_type"] != "code":
            continue
        assert cell["execution_count"] is None
        assert cell["outputs"] == []


@pytest.mark.parametrize("path", NOTEBOOKS, ids=lambda path: path.name)
def test_no_cpu_notebook_imports_a_model_library(path: Path) -> None:
    source = validator.notebook_python(json.loads(path.read_text()))
    for marker in validator.FORBIDDEN_IMPORTS:
        assert marker not in source, f"{path.name} imports a model library into a CPU lane"


@pytest.mark.parametrize("path", NOTEBOOKS, ids=lambda path: path.name)
def test_no_notebook_matches_an_input_by_filename(path: Path) -> None:
    source = validator.notebook_python(json.loads(path.read_text()))
    for marker in validator.FORBIDDEN_FILENAME_DEPENDENCE:
        assert marker not in source, f"{path.name} depends on an input filename"
    assert "discover_kaggle_input(" in source


@pytest.mark.parametrize("path", NOTEBOOKS, ids=lambda path: path.name)
def test_every_notebook_emits_an_output_archive_and_a_failure_bundle(path: Path) -> None:
    source = validator.notebook_python(json.loads(path.read_text()))
    assert 'build_output_archive("COMPLETE")' in source
    assert 'build_output_archive("FAILED")' in source
    assert "CAB_KAGGLE_OUTPUT_MANIFEST.json" in source


@pytest.mark.parametrize("path", NOTEBOOKS, ids=lambda path: path.name)
def test_the_inlined_discovery_matches_the_module(path: Path) -> None:
    """The notebooks carry the same discovery logic the tests exercise."""

    source = validator.notebook_python(json.loads(path.read_text()))
    assert "def discover_kaggle_input(" in source
    assert "FAIL_CLOSED_AMBIGUOUS_KAGGLE_INPUT" in source
    assert "path_traversal_member" in source


def test_the_postrun_lanes_refuse_a_repository_bundle() -> None:
    """A repository bundle is not a run, and no lane may pretend otherwise."""

    for spec in generator.SPECS:
        if not spec.requires_output_bundle:
            continue
        source = validator.notebook_python(json.loads((NOTEBOOK_DIR / spec.filename).read_text()))
        assert "REQUIRES_OUTPUT_BUNDLE = True" in source
        assert 'DISCOVERY["bundle_type"] != "REPOSITORY_BUNDLE"' in source


def test_the_scale100_lane_cannot_consume_compact20_output() -> None:
    scale100 = next(spec for spec in generator.SPECS if spec.lane == "scale100_postrun")
    compact20 = next(spec for spec in generator.SPECS if spec.lane == "compact20_postrun")
    assert scale100.expected_bundle_type == "SCALE100_OUTPUT"
    assert compact20.expected_bundle_type == "COMPACT20_OUTPUT"
    assert scale100.expected_bundle_type != compact20.expected_bundle_type


def test_validation_reports_a_stale_notebook(tmp_path: Path, monkeypatch) -> None:
    """A tampered notebook must be reported, not silently accepted."""

    target = tmp_path / "tampered.ipynb"
    notebook = json.loads(NOTEBOOKS[0].read_text())
    notebook["cells"][1]["outputs"] = [{"output_type": "stream", "text": ["stale"]}]
    notebook["cells"][1]["execution_count"] = 7
    target.write_text(json.dumps(notebook, indent=1, sort_keys=True))

    monkeypatch.setattr(validator, "REPO_ROOT", tmp_path)
    result = validator.validate_one(target)
    assert not result["passed"]
    assert "every_cell_has_empty_outputs" in result["failed"]
    assert "every_cell_has_no_execution_count" in result["failed"]


def test_the_offline_runner_picks_the_cpu_bundle_by_content(tmp_path, monkeypatch) -> None:
    """A newer T4x2 archive must not be mistaken for the CPU input.

    Selecting the newest file by modification time picks whichever bundle was
    built last.  A T4x2 bundle carries a narrower slice of the reports, so the
    lanes then fail on a missing commitment and the wrong input reads as a broken
    chain.
    """

    import json
    import zipfile

    from scripts import validate_kaggle_cpu_notebooks as validator

    directory = tmp_path / "dist" / "kaggle_inputs"
    directory.mkdir(parents=True)

    def write(name: str, bundle_type: str, digest: str) -> Path:
        path = directory / name
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr(
                "CAB_KAGGLE_INPUT_MANIFEST.json",
                json.dumps({"bundle_type": bundle_type, "bundle_content_sha256": digest}),
            )
        return path

    cpu = write("anything.zip", "cpu-preexecution", "a" * 64)
    # Written second, so it is the newest by mtime.
    write("newer.zip", "compact20-t4x2", "b" * 64)

    monkeypatch.setattr(validator, "REPO_ROOT", tmp_path)
    assert validator._cpu_bundle() == cpu


def test_two_different_cpu_bundles_fail_closed(tmp_path, monkeypatch) -> None:
    import json
    import zipfile

    import pytest

    from scripts import validate_kaggle_cpu_notebooks as validator

    directory = tmp_path / "dist" / "kaggle_inputs"
    directory.mkdir(parents=True)
    for name, digest in (("one.zip", "a" * 64), ("two.zip", "c" * 64)):
        with zipfile.ZipFile(directory / name, "w") as archive:
            archive.writestr(
                "CAB_KAGGLE_INPUT_MANIFEST.json",
                json.dumps(
                    {"bundle_type": "cpu-preexecution", "bundle_content_sha256": digest}
                ),
            )

    monkeypatch.setattr(validator, "REPO_ROOT", tmp_path)
    with pytest.raises(SystemExit, match="no honest way"):
        validator._cpu_bundle()
