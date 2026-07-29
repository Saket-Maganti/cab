from __future__ import annotations

import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor

import pytest

from causal_agent_bench.level5.core import ActorClass, EvidenceClass
from causal_agent_bench.level5.registry import InMemoryRegistry, SQLiteRegistry


def test_registry_init_idempotency_freeze_and_public_export(tmp_path):
    registry = SQLiteRegistry(tmp_path / "registry.sqlite3")
    registry.initialize()
    registry.initialize()
    first = registry.register("project", "project.cab", {"name": "CAB"})
    again = registry.register("project", "project.cab", {"name": "CAB"}, freeze=True)
    assert first.content_hash == again.content_hash
    assert again.frozen is True
    assert registry.verify()["passed"] is True
    exported = registry.export_public()
    assert exported["schema_version"] == 1
    assert exported["entities"][0]["entity_id"] == "project.cab"
    assert [event["event_type"] for event in exported["events"]] == [
        "REGISTERED",
        "FROZEN",
    ]
    assert registry.migrate(1) == 1
    with pytest.raises(ValueError, match="downgrade"):
        registry.migrate(0)


def test_registry_rejects_conflicts_unknown_kinds_and_private_payloads(tmp_path):
    registry = SQLiteRegistry(tmp_path / "registry.sqlite3")
    registry.initialize()
    registry.register("study", "study.fixture", {"title": "fixture"})
    with pytest.raises(ValueError, match="idempotency conflict"):
        registry.register("study", "study.fixture", {"title": "changed"})
    with pytest.raises(ValueError, match="private field"):
        registry.register("study", "study.private", {"gold_answer": "forbidden"})
    with pytest.raises(ValueError, match="unknown"):
        registry.register("made_up", "made.up", {})


def test_registry_frozen_entity_is_immutable(tmp_path):
    registry = SQLiteRegistry(tmp_path / "registry.sqlite3")
    registry.initialize()
    registry.register("dataset", "dataset.fixture", {"version": 1}, freeze=True)
    with pytest.raises(ValueError, match="frozen and immutable"):
        registry.register("dataset", "dataset.fixture", {"version": 2})


def test_registry_transaction_rolls_back(tmp_path):
    registry = SQLiteRegistry(tmp_path / "registry.sqlite3")
    registry.initialize()
    with pytest.raises(RuntimeError), registry.transaction() as connection:
        connection.execute(
            """
            INSERT INTO entities(
                kind, entity_id, payload_json, content_hash, frozen, created_at, updated_at
            ) VALUES (?, ?, ?, ?, 0, ?, ?)
            """,
            ("project", "project.rollback", "{}", "bad", "now", "now"),
        )
        raise RuntimeError("force rollback")
    assert registry.get("project", "project.rollback") is None


def test_registry_concurrent_writers_are_serialized(tmp_path):
    registry = SQLiteRegistry(tmp_path / "registry.sqlite3")
    registry.initialize()

    def register(index: int) -> str:
        return registry.register(
            "artifact",
            f"artifact.concurrent_{index:02d}",
            {"index": index},
            freeze=True,
        ).entity_id

    with ThreadPoolExecutor(max_workers=4) as pool:
        ids = list(pool.map(register, range(20)))
    assert len(set(ids)) == 20
    assert registry.verify()["entities"] == 20


def test_registry_dependencies_use_foreign_keys(tmp_path):
    registry = SQLiteRegistry(tmp_path / "registry.sqlite3")
    registry.initialize()
    registry.register("project", "project.cab", {"name": "CAB"})
    registry.register("study", "study.fixture", {"name": "fixture"})
    registry.link("study", "study.fixture", "project", "project.cab", "belongs_to")
    with pytest.raises(sqlite3.IntegrityError):
        registry.link("study", "study.missing", "project", "project.cab", "belongs_to")


def test_registry_provenance_is_immutable(tmp_path):
    registry = SQLiteRegistry(tmp_path / "registry.sqlite3")
    registry.initialize()
    edge_id = registry.add_provenance(
        output_hash="a" * 64,
        parent_hashes=["b" * 64],
        transformation_command="cab fixture transform",
        code_revision="deadbeef",
        environment_id="env.fixture",
        actor_class=ActorClass.FIXTURE,
        evidence_class=EvidenceClass.FIXTURE_ONLY,
    )
    assert edge_id.startswith("prov.")
    with (
        registry._connect() as connection,
        pytest.raises(sqlite3.IntegrityError, match="immutable"),
    ):
        connection.execute(
            "UPDATE provenance_edges SET output_hash = ? WHERE edge_id = ?",
            ("c" * 64, edge_id),
        )


def test_registry_backup_restore_equivalence(tmp_path):
    registry = SQLiteRegistry(tmp_path / "registry.sqlite3")
    registry.initialize()
    registry.register("project", "project.cab", {"name": "CAB"}, freeze=True)
    backup = registry.backup(tmp_path / "backup.sqlite3")
    restored = SQLiteRegistry.restore(backup, tmp_path / "restored.sqlite3")
    assert restored.export_public()["entities"] == registry.export_public()["entities"]


def test_registry_detects_hash_tampering(tmp_path):
    registry = SQLiteRegistry(tmp_path / "registry.sqlite3")
    registry.initialize()
    registry.register("project", "project.cab", {"name": "CAB"})
    with registry._connect() as connection:
        connection.execute(
            "UPDATE entities SET payload_json = ? WHERE kind = ? AND entity_id = ?",
            (json.dumps({"name": "tampered"}), "project", "project.cab"),
        )
    report = registry.verify()
    assert report["passed"] is False
    assert any("hash mismatch" in error for error in report["errors"])


def test_in_memory_registry_matches_immutability_contract():
    registry = InMemoryRegistry()
    registry.register("project", "project.fixture", {"name": "fixture"}, freeze=True)
    assert registry.get("project", "project.fixture").frozen is True
    with pytest.raises(ValueError, match="immutable"):
        registry.register("project", "project.fixture", {"name": "changed"})
