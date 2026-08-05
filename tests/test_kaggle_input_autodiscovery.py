"""Kaggle input discovery must never depend on a filename.

Every test builds a synthetic bundle, gives it a deliberately hostile name, and
asserts that discovery still finds it — or, where the situation is genuinely
ambiguous, that it fails closed with a readable inventory rather than guessing.

Filenames in these tests are randomised on purpose.  A test that passed because
the archive happened to be called the expected thing would prove nothing.
"""

from __future__ import annotations

import secrets
import zipfile
from pathlib import Path

import pytest

from causal_agent_bench.kaggle_input_discovery import (
    COMPACT20_OUTPUT,
    MIN_CONFIDENCE_SCORE,
    OVERRIDE_ENV_VAR,
    REPOSITORY_BUNDLE,
    UNKNOWN_BUNDLE,
    KaggleInputError,
    classify_archive,
    classify_names,
    common_root_prefix,
    discover_kaggle_input,
    locate_bundle_root,
    safe_extract,
    scan,
    select,
)

REPOSITORY_MEMBERS: tuple[str, ...] = (
    "CAB_KAGGLE_INPUT_MANIFEST.json",
    "pyproject.toml",
    "src/causal_agent_bench/__init__.py",
    "src/causal_agent_bench/kaggle_input_discovery.py",
    "scripts/build_kaggle_input_bundles.py",
    "configs/human_validation/c10_contract_v2.json",
    "environment/kaggle_environment.json",
    "reports/reviewer_ready_v2/ACTIVE_PATH_REGISTRY.json",
    "reports/reviewer_ready_v2/SCIENTIFIC_FREEZE_V2.json",
    "data/manifests/compact20.json",
)

OUTPUT_MEMBERS: tuple[str, ...] = (
    "CAB_KAGGLE_OUTPUT_MANIFEST.json",
    "run_manifest.json",
    "execution_authorization.json",
    "shard_manifest.json",
    "trajectories/compact20_shard_0.jsonl",
)


def _random_name(suffix: str = ".zip") -> str:
    """A name no production code could possibly be matching on."""

    return f"{secrets.token_hex(6)} {secrets.token_hex(3)} (1){suffix}"


def _write_zip(
    path: Path, members: tuple[str, ...], *, root_prefix: str = "", extra: dict[str, bytes] | None = None
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for member in members:
            arcname = f"{root_prefix}/{member}" if root_prefix else member
            info = zipfile.ZipInfo(arcname, date_time=(1980, 1, 1, 0, 0, 0))
            info.external_attr = (0o100644) << 16
            archive.writestr(info, f"content of {member}\n")
        for name, payload in (extra or {}).items():
            arcname = f"{root_prefix}/{name}" if root_prefix else name
            info = zipfile.ZipInfo(arcname, date_time=(1980, 1, 1, 0, 0, 0))
            info.external_attr = (0o100644) << 16
            archive.writestr(info, payload)
    return path


def _kaggle(tmp_path: Path) -> tuple[Path, Path]:
    inputs = tmp_path / "input"
    working = tmp_path / "working"
    inputs.mkdir(parents=True, exist_ok=True)
    working.mkdir(parents=True, exist_ok=True)
    return inputs, working


# --------------------------------------------------------------------------
# name independence
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "filename",
    [
        "CAB_KAGGLE_CPU_PREEXECUTION_INPUT_abc123.zip",  # the expected name
        "archive.zip",
        "my bundle with spaces.zip",
        "ünïcødé-архив-束.zip",
        "UPPERCASE.ZIP",
        "MiXeD.Zip",
        "final_FINAL_v3 (2).zip",
    ],
)
def test_any_filename_is_discovered(tmp_path: Path, filename: str) -> None:
    inputs, working = _kaggle(tmp_path)
    _write_zip(inputs / "dataset" / filename, REPOSITORY_MEMBERS)
    result = discover_kaggle_input(search_root=inputs, working_root=working)
    assert result["bundle_type"] == REPOSITORY_BUNDLE
    assert Path(result["selected"]["path"]).name == filename


def test_a_randomly_named_archive_in_a_randomly_named_dataset_is_found(tmp_path: Path) -> None:
    inputs, working = _kaggle(tmp_path)
    dataset = inputs / f"dataset-{secrets.token_hex(4)}" / f"nested-{secrets.token_hex(3)}"
    _write_zip(dataset / _random_name(), REPOSITORY_MEMBERS)
    result = discover_kaggle_input(search_root=inputs, working_root=working)
    assert result["bundle_type"] == REPOSITORY_BUNDLE


@pytest.mark.parametrize("root_prefix", ["", "cab", "causal-agent-bench-main", "a b c"])
def test_any_archive_root_folder_name_works(tmp_path: Path, root_prefix: str) -> None:
    inputs, working = _kaggle(tmp_path)
    _write_zip(inputs / "d" / _random_name(), REPOSITORY_MEMBERS, root_prefix=root_prefix)
    result = discover_kaggle_input(search_root=inputs, working_root=working)
    assert result["bundle_type"] == REPOSITORY_BUNDLE
    assert Path(result["bundle_root"]).is_dir()


def test_a_plain_directory_bundle_is_discovered(tmp_path: Path) -> None:
    inputs, working = _kaggle(tmp_path)
    extracted = inputs / f"dataset-{secrets.token_hex(3)}"
    for member in REPOSITORY_MEMBERS:
        target = extracted / member
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("content\n")
    result = discover_kaggle_input(search_root=inputs, working_root=working)
    assert result["bundle_type"] == REPOSITORY_BUNDLE
    assert result["selected"]["kind"] == "directory"


# --------------------------------------------------------------------------
# multiple attachments
# --------------------------------------------------------------------------


def test_an_unrelated_zip_alongside_the_bundle_is_ignored(tmp_path: Path) -> None:
    inputs, working = _kaggle(tmp_path)
    _write_zip(inputs / "d1" / _random_name(), REPOSITORY_MEMBERS)
    _write_zip(inputs / "d2" / _random_name(), ("photos/img1.png", "photos/img2.png", "notes.txt"))
    result = discover_kaggle_input(search_root=inputs, working_root=working)
    assert result["bundle_type"] == REPOSITORY_BUNDLE


def test_two_identical_copies_are_not_an_ambiguity(tmp_path: Path) -> None:
    inputs, working = _kaggle(tmp_path)
    first = _write_zip(inputs / "d1" / _random_name(), REPOSITORY_MEMBERS)
    second = inputs / "d2" / _random_name()
    second.parent.mkdir(parents=True, exist_ok=True)
    second.write_bytes(first.read_bytes())
    result = discover_kaggle_input(search_root=inputs, working_root=working)
    assert result["bundle_type"] == REPOSITORY_BUNDLE


def test_two_conflicting_valid_bundles_fail_closed_with_an_inventory(tmp_path: Path) -> None:
    inputs, working = _kaggle(tmp_path)
    _write_zip(inputs / "d1" / _random_name(), REPOSITORY_MEMBERS, extra={"a.txt": b"one"})
    _write_zip(inputs / "d2" / _random_name(), REPOSITORY_MEMBERS, extra={"a.txt": b"two"})
    with pytest.raises(KaggleInputError) as error:
        discover_kaggle_input(search_root=inputs, working_root=working)
    message = str(error.value)
    assert "FAIL_CLOSED_AMBIGUOUS_KAGGLE_INPUT" in message
    # The operator needs enough to resolve it by hand.
    assert "sentinel_score" in message or "score" in message
    assert "sha256" in message


def test_no_bundle_at_all_fails_with_a_readable_inventory(tmp_path: Path) -> None:
    inputs, working = _kaggle(tmp_path)
    _write_zip(inputs / "d" / _random_name(), ("random/file.txt",))
    with pytest.raises(KaggleInputError, match="NO_MATCHING_KAGGLE_INPUT"):
        discover_kaggle_input(search_root=inputs, working_root=working)


# --------------------------------------------------------------------------
# bundle types are decided by content
# --------------------------------------------------------------------------


def test_an_output_bundle_renamed_as_an_input_is_not_accepted_as_a_repository(tmp_path: Path) -> None:
    inputs, working = _kaggle(tmp_path)
    _write_zip(
        inputs / "d" / "CAB_KAGGLE_CPU_PREEXECUTION_INPUT_deadbeef.zip",
        tuple(name.replace("compact20", "compact20") for name in OUTPUT_MEMBERS),
    )
    with pytest.raises(KaggleInputError, match="NO_MATCHING_KAGGLE_INPUT"):
        discover_kaggle_input(search_root=inputs, working_root=working)


def test_an_input_bundle_renamed_as_an_output_is_not_accepted_as_an_output(tmp_path: Path) -> None:
    inputs, working = _kaggle(tmp_path)
    _write_zip(inputs / "d" / "CAB_COMPACT20_OUTPUT_cafe.zip", REPOSITORY_MEMBERS)
    with pytest.raises(KaggleInputError):
        discover_kaggle_input(
            search_root=inputs, working_root=working, expected_bundle_type=COMPACT20_OUTPUT
        )


def test_a_compact20_output_bundle_is_classified_by_manifest_content(tmp_path: Path) -> None:
    inputs, working = _kaggle(tmp_path)
    _write_zip(inputs / "d" / _random_name(), OUTPUT_MEMBERS)
    result = discover_kaggle_input(
        search_root=inputs, working_root=working, expected_bundle_type=COMPACT20_OUTPUT
    )
    assert result["bundle_type"] == COMPACT20_OUTPUT


def test_an_output_naming_two_studies_is_not_classified_as_either(tmp_path: Path) -> None:
    names = [*OUTPUT_MEMBERS, "trajectories/scale100_shard_0.jsonl"]
    bundle_type, _, _ = classify_names(names)
    assert bundle_type == UNKNOWN_BUNDLE


# --------------------------------------------------------------------------
# malicious and malformed archives
# --------------------------------------------------------------------------


def test_a_path_traversal_member_is_refused(tmp_path: Path) -> None:
    inputs, working = _kaggle(tmp_path)
    path = _write_zip(inputs / "d" / _random_name(), REPOSITORY_MEMBERS)
    with zipfile.ZipFile(path, "a") as archive:
        archive.writestr("../../escaped.txt", "nope")
    assert "path_traversal_member" in classify_archive(path).problems
    with pytest.raises(KaggleInputError):
        discover_kaggle_input(search_root=inputs, working_root=working)


def test_an_absolute_path_member_is_refused(tmp_path: Path) -> None:
    inputs, _ = _kaggle(tmp_path)
    path = _write_zip(inputs / "d" / _random_name(), REPOSITORY_MEMBERS)
    with zipfile.ZipFile(path, "a") as archive:
        archive.writestr("/etc/passwd", "nope")
    assert "absolute_path_member" in classify_archive(path).problems


def test_a_symlink_member_is_refused(tmp_path: Path) -> None:
    inputs, _ = _kaggle(tmp_path)
    path = _write_zip(inputs / "d" / _random_name(), REPOSITORY_MEMBERS)
    with zipfile.ZipFile(path, "a") as archive:
        info = zipfile.ZipInfo("link")
        info.external_attr = (0o120777) << 16  # S_IFLNK
        archive.writestr(info, "/etc/passwd")
    assert "non_regular_member" in classify_archive(path).problems


def test_a_zip_bomb_expansion_ratio_is_refused(tmp_path: Path) -> None:
    inputs, _ = _kaggle(tmp_path)
    path = inputs / "d" / _random_name()
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for member in REPOSITORY_MEMBERS:
            archive.writestr(member, "x")
        archive.writestr("bomb.bin", b"\0" * (60 * 1024 * 1024))
    assert "expansion_ratio_beyond_the_ceiling" in classify_archive(path).problems


def test_a_truncated_archive_is_refused(tmp_path: Path) -> None:
    inputs, _ = _kaggle(tmp_path)
    path = _write_zip(inputs / "d" / _random_name(), REPOSITORY_MEMBERS)
    data = path.read_bytes()
    path.write_bytes(data[: len(data) // 2])
    assert "not_a_readable_zip_archive" in classify_archive(path).problems


def test_extraction_refuses_to_escape_the_destination(tmp_path: Path) -> None:
    inputs, working = _kaggle(tmp_path)
    path = _write_zip(inputs / "d" / _random_name(), REPOSITORY_MEMBERS)
    candidate = classify_archive(path)
    with zipfile.ZipFile(path, "a") as archive:
        archive.writestr("../escaped.txt", "nope")
    with pytest.raises(KaggleInputError):
        safe_extract(candidate, working)


# --------------------------------------------------------------------------
# the override
# --------------------------------------------------------------------------


def test_an_explicit_override_is_honoured(tmp_path: Path, monkeypatch) -> None:
    inputs, working = _kaggle(tmp_path)
    _write_zip(inputs / "d1" / _random_name(), REPOSITORY_MEMBERS, extra={"a.txt": b"one"})
    chosen = _write_zip(inputs / "d2" / _random_name(), REPOSITORY_MEMBERS, extra={"a.txt": b"two"})
    monkeypatch.setenv(OVERRIDE_ENV_VAR, str(chosen))
    result = discover_kaggle_input(search_root=inputs, working_root=working)
    assert result["override_used"] is True
    assert Path(result["selected"]["path"]) == chosen


def test_an_override_pointing_at_the_wrong_bundle_type_is_refused(
    tmp_path: Path, monkeypatch
) -> None:
    inputs, working = _kaggle(tmp_path)
    wrong = _write_zip(inputs / "d" / _random_name(), OUTPUT_MEMBERS)
    monkeypatch.setenv(OVERRIDE_ENV_VAR, str(wrong))
    with pytest.raises(KaggleInputError):
        discover_kaggle_input(
            search_root=inputs, working_root=working, expected_bundle_type=REPOSITORY_BUNDLE
        )


def test_an_override_pointing_nowhere_is_refused(tmp_path: Path, monkeypatch) -> None:
    inputs, working = _kaggle(tmp_path)
    monkeypatch.setenv(OVERRIDE_ENV_VAR, str(tmp_path / "does-not-exist.zip"))
    with pytest.raises(KaggleInputError, match="does not exist"):
        discover_kaggle_input(search_root=inputs, working_root=working)


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------


def test_common_root_prefix_detects_a_single_wrapping_folder() -> None:
    assert common_root_prefix(["cab/pyproject.toml", "cab/src/x.py"]) == "cab"
    assert common_root_prefix(["pyproject.toml", "src/x.py"]) == ""


def test_one_weak_sentinel_alone_does_not_qualify() -> None:
    bundle_type, score, _ = classify_names(["pyproject.toml"])
    assert bundle_type == REPOSITORY_BUNDLE
    assert score < MIN_CONFIDENCE_SCORE
    with pytest.raises(KaggleInputError):
        select([classify_archive(Path("/nonexistent"))])


def test_extraction_is_idempotent_and_hash_named(tmp_path: Path) -> None:
    inputs, working = _kaggle(tmp_path)
    path = _write_zip(inputs / "d" / _random_name(), REPOSITORY_MEMBERS)
    candidate = classify_archive(path)
    first = safe_extract(candidate, working)
    second = safe_extract(candidate, working)
    assert first == second
    assert candidate.sha256[:16] in first.name


def test_locate_bundle_root_finds_a_wrapped_repository(tmp_path: Path) -> None:
    extracted = tmp_path / "extracted"
    (extracted / "wrapper" / "src" / "causal_agent_bench").mkdir(parents=True)
    (extracted / "wrapper" / "pyproject.toml").write_text("[project]\n")
    assert locate_bundle_root(extracted) == extracted / "wrapper"


def test_scan_reports_every_candidate_for_the_inventory(tmp_path: Path) -> None:
    inputs, _ = _kaggle(tmp_path)
    _write_zip(inputs / "d1" / _random_name(), REPOSITORY_MEMBERS)
    _write_zip(inputs / "d2" / _random_name(), ("unrelated.txt",))
    candidates = scan(inputs)
    assert len(candidates) >= 2
    assert any(candidate.bundle_type == REPOSITORY_BUNDLE for candidate in candidates)
