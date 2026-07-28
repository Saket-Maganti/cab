from __future__ import annotations

import json

from scripts.release_check import REPO_ROOT, run_release_check


def test_release_check_passes_on_repository_manifest():
    report = run_release_check(REPO_ROOT / "release" / "release_manifest.json")
    assert report["passed"] is True, report.get("errors")
    assert report["inventory_file_count"] > 10
    assert report["release_bundle_hash"]


def test_release_check_flags_missing_card_section(tmp_path):
    manifest_path = tmp_path / "manifest.json"
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    bad_card = docs_dir / "bad_card.md"
    bad_card.write_text("# Bad\n\n## Intended Use\n\nOnly one section.\n", encoding="utf-8")
    (tmp_path / "LICENSE").write_text("MIT\n", encoding="utf-8")
    manifest = {
        "release_id": "test",
        "package_version": "0.1.0",
        "cards": ["docs/bad_card.md"],
        "docs": [],
        "configs": [],
        "scripts": [],
        "source_packages": [],
        "license_file": "LICENSE",
        "required_card_sections": ["Intended Use", "License", "Contamination Risk"],
    }
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    report = run_release_check(manifest_path, repo_root=tmp_path)
    assert report["passed"] is False
    assert any("missing section" in error for error in report["errors"])


def test_release_check_flags_missing_inventory_file(tmp_path):
    manifest_path = tmp_path / "manifest.json"
    manifest = {
        "release_id": "test",
        "package_version": "0.1.0",
        "cards": [],
        "docs": ["does_not_exist.md"],
        "configs": [],
        "scripts": [],
        "source_packages": [],
        "required_card_sections": [],
    }
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    report = run_release_check(manifest_path, repo_root=tmp_path)
    assert report["passed"] is False
    assert any("missing release file" in error for error in report["errors"])


def test_release_check_flags_incomplete_canonical_inventory(tmp_path):
    manifest_path = tmp_path / "manifest.json"
    source_dir = tmp_path / "src" / "causal_agent_bench"
    source_dir.mkdir(parents=True)
    (source_dir / "included.py").write_text("", encoding="utf-8")
    (source_dir / "omitted.py").write_text("", encoding="utf-8")
    manifest = {
        "release_id": "test",
        "package_version": "0.1.0",
        "cards": [],
        "docs": [],
        "configs": [],
        "scripts": [],
        "source_packages": ["src/causal_agent_bench/included.py"],
        "required_card_sections": [],
        "inventory_policy": {
            "completeness_enforced": True,
            "categories": {
                "source_packages": ["src/causal_agent_bench/**/*.py"],
            },
        },
    }
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    report = run_release_check(manifest_path, repo_root=tmp_path)

    assert report["passed"] is False
    assert any("incomplete source_packages inventory" in error for error in report["errors"])


def test_release_check_rejects_private_payload_path(tmp_path):
    manifest_path = tmp_path / "manifest.json"
    private_path = tmp_path / "private_data/heldout_challenge_v2/tasks.jsonl"
    private_path.parent.mkdir(parents=True)
    private_path.write_text('{"task_text": "must not ship"}\n', encoding="utf-8")
    manifest = {
        "release_id": "test",
        "package_version": "0.1.0",
        "cards": [],
        "docs": [],
        "configs": [],
        "scripts": [],
        "source_packages": [],
        "data_manifests": [
            "private_data/heldout_challenge_v2/tasks.jsonl"
        ],
        "required_card_sections": [],
    }
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    report = run_release_check(manifest_path, repo_root=tmp_path)

    assert report["passed"] is False
    assert any(
        "forbidden private/protected release payload" in error
        for error in report["errors"]
    )
