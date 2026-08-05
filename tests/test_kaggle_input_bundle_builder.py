"""The Kaggle bundle builder must be deterministic and must never leak private material."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from scripts import build_kaggle_input_bundles as builder

REPO_ROOT = Path(__file__).resolve().parents[1]


def _members(root: Path, names: list[str]) -> list:
    made = []
    for name in names:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"content of {name}\n")
        made.append(
            builder.Member(arcname=name, source=path, sha256=builder.sha256_file(path))
        )
    return made


def test_the_bundle_is_byte_identical_across_rebuilds(tmp_path: Path) -> None:
    source = tmp_path / "src"
    source.mkdir()
    members = _members(source, ["a.txt", "nested/b.json", "nested/deeper/c.py"])
    manifest = builder.build_manifest(members, bundle_type="cpu-preexecution")

    first = builder.write_bundle(members, manifest, tmp_path / "out1", bundle_type="cpu-preexecution")
    second = builder.write_bundle(members, manifest, tmp_path / "out2", bundle_type="cpu-preexecution")
    assert first.read_bytes() == second.read_bytes()
    assert first.name == second.name


def test_archive_timestamps_and_permissions_are_normalized(tmp_path: Path) -> None:
    source = tmp_path / "src"
    source.mkdir()
    members = _members(source, ["a.txt", "b.txt"])
    manifest = builder.build_manifest(members, bundle_type="cpu-preexecution")
    target = builder.write_bundle(members, manifest, tmp_path / "out", bundle_type="cpu-preexecution")

    with zipfile.ZipFile(target) as archive:
        for info in archive.infolist():
            assert info.date_time == builder.FIXED_TIMESTAMP
            # Regular file with 0o644, independent of the build machine's umask.
            assert (info.external_attr >> 16) == 0o100644


def test_members_are_sorted_inside_the_archive(tmp_path: Path) -> None:
    source = tmp_path / "src"
    source.mkdir()
    members = _members(source, ["z.txt", "a.txt", "m/n.txt"])
    manifest = builder.build_manifest(members, bundle_type="cpu-preexecution")
    target = builder.write_bundle(members, manifest, tmp_path / "out", bundle_type="cpu-preexecution")
    with zipfile.ZipFile(target) as archive:
        names = archive.namelist()
    assert names == sorted(names)


def test_the_manifest_content_hash_does_not_include_itself(tmp_path: Path) -> None:
    source = tmp_path / "src"
    source.mkdir()
    members = _members(source, ["a.txt"])
    manifest = builder.build_manifest(members, bundle_type="cpu-preexecution")
    assert builder.MANIFEST_NAME not in [row["path"] for row in manifest["members"]]
    # Recomputing from the recorded pairs reproduces the declared hash.
    import hashlib

    payload = json.dumps(
        [[row["path"], row["sha256"]] for row in manifest["members"]], separators=(",", ":")
    ).encode()
    assert manifest["bundle_content_sha256"] == hashlib.sha256(payload).hexdigest()


def test_the_manifest_declares_no_private_material(tmp_path: Path) -> None:
    source = tmp_path / "src"
    source.mkdir()
    manifest = builder.build_manifest(_members(source, ["a.txt"]), bundle_type="cpu-preexecution")
    assert manifest["private_material_included"] is False
    assert manifest["schema_version"] == builder.BUNDLE_SCHEMA_VERSION


@pytest.mark.parametrize(
    "arcname",
    [
        "private_data/human_review/x.json",
        "human_review_files/stage1_a.csv",
        ".git/config",
        ".env",
    ],
)
def test_never_bundle_paths_are_refused(arcname: str) -> None:
    assert builder._forbidden(arcname, tracked=set()) is not None


@pytest.mark.parametrize(
    "arcname",
    [
        "somewhere/qualification_key.enc",
        "somewhere/stage2_vault.enc",
        "somewhere/reviewer_assignments.json",
        "somewhere/stage1_reviewer_a_mapping.json",
        "somewhere/kaggle.json",
    ],
)
def test_untracked_private_looking_names_are_refused(arcname: str) -> None:
    assert builder._forbidden(arcname, tracked=set()) is not None


def test_a_tracked_public_report_is_allowed_despite_its_name() -> None:
    """``STAGE2_VAULT_STATUS.json`` records checks and a ciphertext hash, not a key."""

    arcname = "reports/reviewer_ready_v2/STAGE2_VAULT_STATUS.json"
    assert builder._forbidden(arcname, tracked={arcname}) is None
    assert builder._forbidden(arcname, tracked=set()) is not None


def test_the_real_preexecution_bundle_contains_no_private_material(tmp_path: Path) -> None:
    result = builder.build(builder.PREEXECUTION, tmp_path)
    with zipfile.ZipFile(Path(result["path"])) as archive:
        names = archive.namelist()
    assert names, "the bundle is empty"
    for name in names:
        assert not name.startswith(("private_data/", "human_review_files/", ".git/"))
        assert "qualification_key" not in name
        assert "qualification_source" not in name
        assert not name.endswith((".key", ".enc"))
        assert "_mapping.json" not in name
    assert builder.MANIFEST_NAME in names


def test_a_postrun_bundle_refuses_to_invent_results(tmp_path: Path) -> None:
    with pytest.raises(builder.BundleError, match="nothing to bundle before a run exists"):
        builder.build("compact20-postrun", tmp_path, run_dir=tmp_path / "no-such-run")


def test_a_postrun_bundle_requires_a_run_dir(tmp_path: Path) -> None:
    with pytest.raises(builder.BundleError, match="--run-dir is required"):
        builder.build("compact20-postrun", tmp_path)


def test_an_unknown_bundle_type_is_refused(tmp_path: Path) -> None:
    with pytest.raises(builder.BundleError, match="unknown bundle type"):
        builder.build("not-a-bundle-type", tmp_path)


def test_the_bundle_is_discoverable_by_content_after_renaming(tmp_path: Path) -> None:
    """The builder and the discovery module must agree, end to end."""

    from causal_agent_bench.kaggle_input_discovery import (
        REPOSITORY_BUNDLE,
        discover_kaggle_input,
        verify_bundle_manifest,
    )

    result = builder.build(builder.PREEXECUTION, tmp_path / "built")
    inputs = tmp_path / "input" / "some-dataset"
    inputs.mkdir(parents=True)
    renamed = inputs / "totally different name.ZIP"
    renamed.write_bytes(Path(result["path"]).read_bytes())

    discovery = discover_kaggle_input(
        search_root=tmp_path / "input", working_root=tmp_path / "working"
    )
    assert discovery["bundle_type"] == REPOSITORY_BUNDLE
    assert discovery["archive_sha256"] == result["sha256"]
    verification = verify_bundle_manifest(Path(discovery["bundle_root"]))
    assert verification["passed"], verification


def test_the_bundle_index_is_never_a_member_of_a_bundle() -> None:
    """The index describes bundles; bundling it makes each one describe the last.

    The include patterns deliberately cover the whole report directory, so the
    exclusion has to be enforced rather than left to the glob.
    """

    index = "reports/post_human_review/KAGGLE_INPUT_BUNDLE_MANIFESTS.json"
    if not (REPO_ROOT / index).is_file():
        pytest.skip("no bundle index has been written in this working tree")
    members = builder.collect(builder.PREEXECUTION_INCLUDES)
    assert index not in {member.arcname for member in members}
    # And it really would have been caught by the glob otherwise.
    assert any(
        member.arcname.startswith("reports/post_human_review/") for member in members
    )


def test_two_real_builds_over_an_unchanged_repository_agree(tmp_path: Path) -> None:
    """Determinism over the real tree, not only over a synthetic member list.

    The synthetic case cannot see a member that the build itself rewrites, which
    is exactly how a self-referential include escapes notice.
    """

    first = builder.build(builder.PREEXECUTION, tmp_path / "one")
    second = builder.build(builder.PREEXECUTION, tmp_path / "two")
    assert first["bundle_content_sha256"] == second["bundle_content_sha256"]
    assert first["sha256"] == second["sha256"]
    assert first["member_count"] == second["member_count"]
