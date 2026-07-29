"""Transactional experiment registry with SQLite and in-memory implementations."""

from __future__ import annotations

import json
import shutil
import sqlite3
import threading
import uuid
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from causal_agent_bench.level5.core import (
    ActorClass,
    EvidenceClass,
    canonical_json,
    content_hash,
    reject_private_fields,
    utc_now,
    validate_typed_id,
)
from causal_agent_bench.level5.migrations import (
    SCHEMA_VERSION,
    MigrationManager,
)

ENTITY_KINDS = frozenset(
    {
        "project",
        "study",
        "preregistration",
        "dataset",
        "task_version",
        "split_version",
        "model_version",
        "policy_version",
        "scorer_version",
        "code_revision",
        "run_manifest",
        "run",
        "shard",
        "attempt",
        "checkpoint",
        "artifact",
        "evidence_record",
        "audit",
        "claim",
        "certification",
        "review_session",
    }
)
@dataclass(frozen=True)
class RegistryRecord:
    kind: str
    entity_id: str
    payload: dict[str, Any]
    content_hash: str
    frozen: bool
    created_at: str
    updated_at: str


class Registry(Protocol):
    def register(
        self,
        kind: str,
        entity_id: str,
        payload: Mapping[str, Any],
        *,
        freeze: bool = False,
    ) -> RegistryRecord: ...

    def get(self, kind: str, entity_id: str) -> RegistryRecord | None: ...

    def freeze(self, kind: str, entity_id: str) -> RegistryRecord: ...

    def export_public(self) -> dict[str, Any]: ...


def _validate_kind(kind: str) -> None:
    if kind not in ENTITY_KINDS:
        raise ValueError(f"unknown registry entity kind: {kind!r}")


def _payload_copy(payload: Mapping[str, Any]) -> dict[str, Any]:
    value = json.loads(canonical_json(dict(payload)))
    if not isinstance(value, dict):
        raise TypeError("registry payload must be an object")
    reject_private_fields(value)
    return value


class SQLiteRegistry:
    """SQLite registry with append-only events and immutable freeze semantics."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30.0, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA busy_timeout = 30000")
        return connection

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        with self._lock, self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                yield connection
            except BaseException:
                connection.execute("ROLLBACK")
                raise
            else:
                connection.execute("COMMIT")

    def initialize(self) -> None:
        """Create a new v1 registry and apply every ordered migration to v3."""

        with self._lock:
            manager = MigrationManager(self.path)
            manager.ensure_v1()
            manager.migrate(SCHEMA_VERSION)

    def schema_version(self) -> int:
        return MigrationManager(self.path).current_version()

    def migration_plan(self, target_version: int = SCHEMA_VERSION) -> dict[str, Any]:
        return MigrationManager(self.path).plan(target_version)

    def migrate(
        self,
        target_version: int = SCHEMA_VERSION,
        *,
        interrupt_after_statement: int | None = None,
        export_before_upgrade: str | Path | None = None,
    ) -> int:
        """Apply checksum-pinned migrations with backup and crash recovery."""

        with self._lock:
            return MigrationManager(self.path).migrate(
                target_version,
                interrupt_after_statement=interrupt_after_statement,
                export_before_upgrade=export_before_upgrade,
            )

    def recover_migration(self) -> int:
        with self._lock:
            return MigrationManager(self.path).recover()

    def migration_history(self) -> list[dict[str, Any]]:
        return MigrationManager(self.path).history()

    def migration_runtime(self) -> dict[str, Any]:
        return MigrationManager(self.path).runtime_state()

    def register(
        self,
        kind: str,
        entity_id: str,
        payload: Mapping[str, Any],
        *,
        freeze: bool = False,
    ) -> RegistryRecord:
        _validate_kind(kind)
        validate_typed_id(entity_id, label=f"{kind} id")
        clean = _payload_copy(payload)
        payload_json = canonical_json(clean)
        digest = content_hash(clean)
        now = utc_now()
        with self.transaction() as connection:
            existing = connection.execute(
                "SELECT * FROM entities WHERE kind = ? AND entity_id = ?",
                (kind, entity_id),
            ).fetchone()
            if existing:
                if str(existing["content_hash"]) == digest:
                    if freeze and not bool(existing["frozen"]):
                        connection.execute(
                            "UPDATE entities SET frozen = 1, updated_at = ? "
                            "WHERE kind = ? AND entity_id = ?",
                            (now, kind, entity_id),
                        )
                        self._append_event(
                            connection, kind, entity_id, "FROZEN", {"content_hash": digest}
                        )
                    row = connection.execute(
                        "SELECT * FROM entities WHERE kind = ? AND entity_id = ?",
                        (kind, entity_id),
                    ).fetchone()
                    assert row is not None
                    return self._row_to_record(row)
                if bool(existing["frozen"]):
                    raise ValueError(f"{kind}/{entity_id} is frozen and immutable")
                raise ValueError(f"idempotency conflict for {kind}/{entity_id}")
            connection.execute(
                """
                INSERT INTO entities(
                    kind, entity_id, payload_json, content_hash, frozen, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (kind, entity_id, payload_json, digest, int(freeze), now, now),
            )
            self._append_event(
                connection,
                kind,
                entity_id,
                "REGISTERED",
                {"content_hash": digest, "frozen": freeze},
            )
        record = self.get(kind, entity_id)
        assert record is not None
        return record

    def get(self, kind: str, entity_id: str) -> RegistryRecord | None:
        _validate_kind(kind)
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM entities WHERE kind = ? AND entity_id = ?",
                (kind, entity_id),
            ).fetchone()
        return self._row_to_record(row) if row else None

    def freeze(self, kind: str, entity_id: str) -> RegistryRecord:
        record = self.get(kind, entity_id)
        if record is None:
            raise KeyError(f"missing registry entity: {kind}/{entity_id}")
        return self.register(kind, entity_id, record.payload, freeze=True)

    def link(
        self,
        child_kind: str,
        child_id: str,
        parent_kind: str,
        parent_id: str,
        relation: str,
    ) -> None:
        _validate_kind(child_kind)
        _validate_kind(parent_kind)
        validate_typed_id(relation, label="relation")
        with self.transaction() as connection:
            for kind, entity_id, label in (
                (child_kind, child_id, "child"),
                (parent_kind, parent_id, "parent"),
            ):
                if connection.execute(
                    "SELECT 1 FROM entities WHERE kind=? AND entity_id=?",
                    (kind, entity_id),
                ).fetchone() is None:
                    raise ValueError(f"missing {label} entity: {kind}/{entity_id}")
            connection.execute(
                """
                INSERT OR IGNORE INTO entity_dependencies(
                    child_kind, child_id, parent_kind, parent_id, relation, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (child_kind, child_id, parent_kind, parent_id, relation, utc_now()),
            )
            self._append_event(
                connection,
                child_kind,
                child_id,
                "LINKED",
                {
                    "parent_kind": parent_kind,
                    "parent_id": parent_id,
                    "relation": relation,
                },
            )

    def add_provenance(
        self,
        *,
        output_hash: str,
        parent_hashes: list[str],
        transformation_command: str,
        code_revision: str,
        environment_id: str,
        actor_class: ActorClass,
        evidence_class: EvidenceClass,
    ) -> str:
        payload = {
            "output_hash": output_hash,
            "parent_hashes": sorted(parent_hashes),
            "transformation_command": transformation_command,
            "code_revision": code_revision,
            "environment_id": environment_id,
            "actor_class": actor_class.value,
            "evidence_class": evidence_class.value,
        }
        edge_id = f"prov.{content_hash(payload)[:24]}"
        with self.transaction() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO provenance_edges(
                    edge_id, output_hash, parent_hashes_json, transformation_command,
                    code_revision, environment_id, actor_class, evidence_class, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    edge_id,
                    output_hash,
                    canonical_json(sorted(parent_hashes)),
                    transformation_command,
                    code_revision,
                    environment_id,
                    actor_class.value,
                    evidence_class.value,
                    utc_now(),
                ),
            )
        return edge_id

    def audit_events(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM events ORDER BY seq").fetchall()
        return [
            {
                "seq": int(row["seq"]),
                "event_id": str(row["event_id"]),
                "entity_kind": str(row["entity_kind"]),
                "entity_id": str(row["entity_id"]),
                "event_type": str(row["event_type"]),
                "payload": json.loads(str(row["payload_json"])),
                "created_at": str(row["created_at"]),
            }
            for row in rows
        ]

    def export_public(self) -> dict[str, Any]:
        with self._connect() as connection:
            entity_rows = connection.execute(
                "SELECT * FROM entities ORDER BY kind, entity_id"
            ).fetchall()
            dependency_rows = connection.execute(
                "SELECT * FROM entity_dependencies "
                "ORDER BY child_kind, child_id, parent_kind, parent_id, relation"
            ).fetchall()
            provenance_rows = connection.execute(
                "SELECT * FROM provenance_edges ORDER BY edge_id"
            ).fetchall()
        return {
            "schema_version": self.schema_version(),
            "entities": [self._record_dict(self._row_to_record(row)) for row in entity_rows],
            "dependencies": [dict(row) for row in dependency_rows],
            "events": self.audit_events(),
            "provenance": [
                {
                    **dict(row),
                    "parent_hashes": json.loads(str(row["parent_hashes_json"])),
                }
                for row in provenance_rows
            ],
        }

    def verify(self) -> dict[str, Any]:
        errors: list[str] = []
        if not self.path.exists():
            return {"passed": False, "errors": ["registry file is missing"], "entities": 0}
        with self._connect() as connection:
            integrity = str(connection.execute("PRAGMA integrity_check").fetchone()[0])
            foreign_keys = connection.execute("PRAGMA foreign_key_check").fetchall()
            rows = connection.execute("SELECT * FROM entities").fetchall()
        if integrity != "ok":
            errors.append(f"sqlite integrity: {integrity}")
        if foreign_keys:
            errors.append(f"foreign key violations: {len(foreign_keys)}")
        for row in rows:
            payload = json.loads(str(row["payload_json"]))
            if content_hash(payload) != str(row["content_hash"]):
                errors.append(f"hash mismatch: {row['kind']}/{row['entity_id']}")
            try:
                reject_private_fields(payload)
            except ValueError as exc:
                errors.append(str(exc))
        errors.extend(MigrationManager(self.path).verify_applied_checksums())
        runtime = MigrationManager(self.path).runtime_state()
        if runtime.get("status") not in {"IDLE", None}:
            errors.append(f"migration runtime is {runtime.get('status')}")
        return {
            "passed": not errors,
            "errors": errors,
            "entities": len(rows),
            "schema_version": self.schema_version(),
            "migration_runtime": runtime,
        }

    def backup(self, destination: str | Path) -> Path:
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as source, sqlite3.connect(destination) as target:
            source.backup(target)
        return destination

    @classmethod
    def restore(cls, backup_path: str | Path, destination: str | Path) -> SQLiteRegistry:
        backup_path = Path(backup_path)
        destination = Path(destination)
        if not backup_path.is_file():
            raise FileNotFoundError(backup_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(backup_path, destination)
        registry = cls(destination)
        result = registry.verify()
        if not result["passed"]:
            raise ValueError(f"restored registry failed verification: {result['errors']}")
        return registry

    @staticmethod
    def _append_event(
        connection: sqlite3.Connection,
        kind: str,
        entity_id: str,
        event_type: str,
        payload: Mapping[str, Any],
    ) -> None:
        connection.execute(
            """
            INSERT INTO events(
                event_id, entity_kind, entity_id, event_type, payload_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                f"evt.{uuid.uuid4().hex}",
                kind,
                entity_id,
                event_type,
                canonical_json(dict(payload)),
                utc_now(),
            ),
        )

    @staticmethod
    def _row_to_record(row: sqlite3.Row) -> RegistryRecord:
        return RegistryRecord(
            kind=str(row["kind"]),
            entity_id=str(row["entity_id"]),
            payload=json.loads(str(row["payload_json"])),
            content_hash=str(row["content_hash"]),
            frozen=bool(row["frozen"]),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )

    @staticmethod
    def _record_dict(record: RegistryRecord) -> dict[str, Any]:
        return {
            "kind": record.kind,
            "entity_id": record.entity_id,
            "payload": record.payload,
            "content_hash": record.content_hash,
            "frozen": record.frozen,
            "created_at": record.created_at,
            "updated_at": record.updated_at,
        }


class InMemoryRegistry:
    """Small fixture implementation matching the registry mutation contract."""

    def __init__(self) -> None:
        self._records: dict[tuple[str, str], RegistryRecord] = {}
        self._events: list[dict[str, Any]] = []

    def register(
        self,
        kind: str,
        entity_id: str,
        payload: Mapping[str, Any],
        *,
        freeze: bool = False,
    ) -> RegistryRecord:
        _validate_kind(kind)
        validate_typed_id(entity_id, label=f"{kind} id")
        clean = _payload_copy(payload)
        digest = content_hash(clean)
        key = (kind, entity_id)
        existing = self._records.get(key)
        if existing:
            if existing.content_hash != digest:
                message = (
                    f"{kind}/{entity_id} is frozen and immutable"
                    if existing.frozen
                    else f"idempotency conflict for {kind}/{entity_id}"
                )
                raise ValueError(message)
            if freeze and not existing.frozen:
                existing = RegistryRecord(
                    **{**existing.__dict__, "frozen": True, "updated_at": utc_now()}
                )
                self._records[key] = existing
            return existing
        now = utc_now()
        record = RegistryRecord(kind, entity_id, clean, digest, freeze, now, now)
        self._records[key] = record
        self._events.append(
            {
                "seq": len(self._events) + 1,
                "entity_kind": kind,
                "entity_id": entity_id,
                "event_type": "REGISTERED",
                "created_at": now,
            }
        )
        return record

    def get(self, kind: str, entity_id: str) -> RegistryRecord | None:
        _validate_kind(kind)
        return self._records.get((kind, entity_id))

    def freeze(self, kind: str, entity_id: str) -> RegistryRecord:
        record = self.get(kind, entity_id)
        if record is None:
            raise KeyError(f"missing registry entity: {kind}/{entity_id}")
        return self.register(kind, entity_id, record.payload, freeze=True)

    def export_public(self) -> dict[str, Any]:
        records = sorted(self._records.values(), key=lambda row: (row.kind, row.entity_id))
        return {
            "schema_version": SCHEMA_VERSION,
            "entities": [SQLiteRegistry._record_dict(record) for record in records],
            "events": list(self._events),
            "dependencies": [],
            "provenance": [],
        }


__all__ = [
    "ENTITY_KINDS",
    "SCHEMA_VERSION",
    "InMemoryRegistry",
    "Registry",
    "RegistryRecord",
    "SQLiteRegistry",
]
