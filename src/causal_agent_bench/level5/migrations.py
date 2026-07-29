"""Ordered SQLite migrations for the canonical Level-5 registry.

Schema v1 is the published fixture foundation.  V2 adds the operational
scheduler.  V3 adds durable review, evidence, certificate, evaluator,
benchmark, and plugin repositories.  Protected bodies, reviewer identities,
and signing secrets have no columns in these public-registry schemas.
"""

from __future__ import annotations

import json
import os
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from causal_agent_bench.level5.core import content_hash, file_sha256, utc_now

SCHEMA_VERSION = 3


@dataclass(frozen=True)
class Migration:
    migration_id: str
    source_version: int
    target_version: int
    statements: tuple[str, ...]
    preconditions: tuple[str, ...]
    postconditions: tuple[str, ...]
    reversible: bool
    backup_required: bool

    @property
    def checksum(self) -> str:
        return content_hash(
            {
                "migration_id": self.migration_id,
                "source_version": self.source_version,
                "target_version": self.target_version,
                "statements": self.statements,
                "preconditions": self.preconditions,
                "postconditions": self.postconditions,
                "reversible": self.reversible,
                "backup_required": self.backup_required,
            }
        )


V1_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS schema_migrations (
        version INTEGER PRIMARY KEY,
        applied_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS entities (
        kind TEXT NOT NULL,
        entity_id TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        content_hash TEXT NOT NULL,
        frozen INTEGER NOT NULL DEFAULT 0 CHECK (frozen IN (0, 1)),
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        PRIMARY KEY (kind, entity_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS entity_dependencies (
        child_kind TEXT NOT NULL,
        child_id TEXT NOT NULL,
        parent_kind TEXT NOT NULL,
        parent_id TEXT NOT NULL,
        relation TEXT NOT NULL,
        created_at TEXT NOT NULL,
        PRIMARY KEY (child_kind, child_id, parent_kind, parent_id, relation),
        FOREIGN KEY (child_kind, child_id)
            REFERENCES entities(kind, entity_id) ON DELETE RESTRICT,
        FOREIGN KEY (parent_kind, parent_id)
            REFERENCES entities(kind, entity_id) ON DELETE RESTRICT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS events (
        seq INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id TEXT NOT NULL UNIQUE,
        entity_kind TEXT NOT NULL,
        entity_id TEXT NOT NULL,
        event_type TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (entity_kind, entity_id)
            REFERENCES entities(kind, entity_id) ON DELETE RESTRICT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS provenance_edges (
        edge_id TEXT PRIMARY KEY,
        output_hash TEXT NOT NULL,
        parent_hashes_json TEXT NOT NULL,
        transformation_command TEXT NOT NULL,
        code_revision TEXT NOT NULL,
        environment_id TEXT NOT NULL,
        actor_class TEXT NOT NULL,
        evidence_class TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TRIGGER IF NOT EXISTS events_no_update
    BEFORE UPDATE ON events BEGIN
        SELECT RAISE(ABORT, 'events are append-only');
    END
    """,
    """
    CREATE TRIGGER IF NOT EXISTS events_no_delete
    BEFORE DELETE ON events BEGIN
        SELECT RAISE(ABORT, 'events are append-only');
    END
    """,
    """
    CREATE TRIGGER IF NOT EXISTS provenance_no_update
    BEFORE UPDATE ON provenance_edges BEGIN
        SELECT RAISE(ABORT, 'provenance is immutable');
    END
    """,
    """
    CREATE TRIGGER IF NOT EXISTS provenance_no_delete
    BEFORE DELETE ON provenance_edges BEGIN
        SELECT RAISE(ABORT, 'provenance is immutable');
    END
    """,
)

MIGRATION_V1 = Migration(
    migration_id="registry-v1-fixture-foundation",
    source_version=0,
    target_version=1,
    statements=V1_STATEMENTS,
    preconditions=("database is empty or contains compatible v1 tables",),
    postconditions=("core entity, event, dependency, and provenance tables exist",),
    reversible=False,
    backup_required=False,
)

V2_STATEMENTS = (
    """
    CREATE TABLE schema_migrations_v2 (
        version INTEGER PRIMARY KEY,
        migration_id TEXT NOT NULL,
        source_version INTEGER NOT NULL,
        target_version INTEGER NOT NULL,
        checksum TEXT NOT NULL,
        applied_at TEXT NOT NULL,
        duration_ms REAL NOT NULL,
        preconditions_json TEXT NOT NULL,
        postconditions_json TEXT NOT NULL,
        reversible INTEGER NOT NULL CHECK (reversible IN (0, 1)),
        backup_required INTEGER NOT NULL CHECK (backup_required IN (0, 1)),
        backup_hash TEXT,
        status TEXT NOT NULL,
        failure_record TEXT
    )
    """,
    f"""
    INSERT INTO schema_migrations_v2(
        version, migration_id, source_version, target_version, checksum,
        applied_at, duration_ms, preconditions_json, postconditions_json,
        reversible, backup_required, backup_hash, status, failure_record
    )
    SELECT version, 'registry-v1-fixture-foundation', 0, 1,
           '{MIGRATION_V1.checksum}', applied_at, 0.0,
           '["database is empty or contains compatible v1 tables"]',
           '["core entity, event, dependency, and provenance tables exist"]',
           0, 0, NULL, 'APPLIED', NULL
      FROM schema_migrations
    """,
    "DROP TABLE schema_migrations",
    "ALTER TABLE schema_migrations_v2 RENAME TO schema_migrations",
    """
    CREATE TABLE queue_entries (
        unit_id TEXT PRIMARY KEY,
        manifest_hash TEXT NOT NULL,
        study_id TEXT NOT NULL,
        backend TEXT NOT NULL,
        model_version TEXT NOT NULL,
        priority INTEGER NOT NULL DEFAULT 0,
        state TEXT NOT NULL,
        dependencies_json TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        payload_hash TEXT NOT NULL,
        available_at REAL NOT NULL,
        attempt_count INTEGER NOT NULL DEFAULT 0,
        max_attempts INTEGER NOT NULL,
        quota_key TEXT NOT NULL,
        result_digest TEXT,
        terminal_reason TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE INDEX queue_ready_idx
      ON queue_entries(state, available_at, priority DESC, study_id, unit_id)
    """,
    """
    CREATE TABLE worker_leases (
        unit_id TEXT PRIMARY KEY,
        worker_id TEXT NOT NULL,
        lease_token_hash TEXT NOT NULL,
        generation INTEGER NOT NULL,
        acquired_at REAL NOT NULL,
        expires_at REAL NOT NULL,
        heartbeat_at REAL NOT NULL,
        FOREIGN KEY (unit_id) REFERENCES queue_entries(unit_id) ON DELETE CASCADE
    )
    """,
    """
    CREATE INDEX worker_lease_expiry_idx ON worker_leases(expires_at)
    """,
    """
    CREATE TABLE worker_heartbeats (
        worker_id TEXT PRIMARY KEY,
        backend TEXT NOT NULL,
        last_seen REAL NOT NULL,
        active_unit_id TEXT,
        generation INTEGER NOT NULL,
        metadata_json TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE scheduler_attempts (
        attempt_id TEXT PRIMARY KEY,
        unit_id TEXT NOT NULL,
        attempt_number INTEGER NOT NULL,
        worker_id TEXT NOT NULL,
        state TEXT NOT NULL,
        started_at TEXT NOT NULL,
        finished_at TEXT,
        error_class TEXT,
        error_message TEXT,
        result_digest TEXT,
        duplicate_of TEXT,
        receipt_json TEXT,
        UNIQUE(unit_id, attempt_number),
        FOREIGN KEY (unit_id) REFERENCES queue_entries(unit_id) ON DELETE RESTRICT
    )
    """,
    """
    CREATE TABLE resource_reservations (
        reservation_id TEXT PRIMARY KEY,
        unit_id TEXT NOT NULL,
        backend TEXT NOT NULL,
        model_version TEXT NOT NULL,
        quota_key TEXT NOT NULL,
        cpu_units REAL NOT NULL,
        memory_mb INTEGER NOT NULL,
        acquired_at REAL NOT NULL,
        released_at REAL,
        FOREIGN KEY (unit_id) REFERENCES queue_entries(unit_id) ON DELETE RESTRICT
    )
    """,
    """
    CREATE TABLE scheduler_events (
        seq INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id TEXT NOT NULL UNIQUE,
        unit_id TEXT,
        event_type TEXT NOT NULL,
        previous_state TEXT,
        new_state TEXT,
        payload_json TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE scheduler_quotas (
        quota_key TEXT PRIMARY KEY,
        allowance INTEGER NOT NULL,
        consumed INTEGER NOT NULL DEFAULT 0,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE scheduler_controls (
        manifest_hash TEXT PRIMARY KEY,
        state TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TRIGGER scheduler_events_no_update
    BEFORE UPDATE ON scheduler_events BEGIN
        SELECT RAISE(ABORT, 'scheduler events are append-only');
    END
    """,
    """
    CREATE TRIGGER scheduler_events_no_delete
    BEFORE DELETE ON scheduler_events BEGIN
        SELECT RAISE(ABORT, 'scheduler events are append-only');
    END
    """,
)

MIGRATION_V2 = Migration(
    migration_id="registry-v2-operational-scheduler",
    source_version=1,
    target_version=2,
    statements=V2_STATEMENTS,
    preconditions=("schema v1 integrity passes", "automatic backup is complete"),
    postconditions=("queue, lease, heartbeat, attempt, reservation, and event tables exist",),
    reversible=False,
    backup_required=True,
)

V3_STATEMENTS = (
    """
    CREATE TABLE review_users (
        user_id TEXT PRIMARY KEY,
        external_subject_hash TEXT,
        role TEXT NOT NULL,
        qualified INTEGER NOT NULL DEFAULT 0,
        consented INTEGER NOT NULL DEFAULT 0,
        human_attestation INTEGER NOT NULL DEFAULT 0,
        evidence_scope TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE review_sessions (
        session_id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        token_hash TEXT NOT NULL UNIQUE,
        csrf_hash TEXT NOT NULL,
        expires_at REAL NOT NULL,
        revoked_at TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES review_users(user_id) ON DELETE RESTRICT
    )
    """,
    """
    CREATE TABLE review_assignments (
        assignment_id TEXT PRIMARY KEY,
        item_id TEXT NOT NULL,
        reviewer_id TEXT NOT NULL,
        assignment_version INTEGER NOT NULL,
        blinded_order INTEGER NOT NULL,
        state TEXT NOT NULL,
        conflict_declared INTEGER NOT NULL DEFAULT 0,
        replaces_assignment_id TEXT,
        receipt_hash TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (reviewer_id) REFERENCES review_users(user_id) ON DELETE RESTRICT
    )
    """,
    """
    CREATE TABLE review_judgments (
        judgment_id TEXT PRIMARY KEY,
        assignment_id TEXT NOT NULL,
        item_id TEXT NOT NULL,
        reviewer_id TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        payload_hash TEXT NOT NULL,
        evidence_scope TEXT NOT NULL,
        submitted_at TEXT NOT NULL,
        FOREIGN KEY (assignment_id) REFERENCES review_assignments(assignment_id)
            ON DELETE RESTRICT,
        FOREIGN KEY (reviewer_id) REFERENCES review_users(user_id) ON DELETE RESTRICT
    )
    """,
    """
    CREATE TABLE review_drafts (
        assignment_id TEXT PRIMARY KEY,
        reviewer_id TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        payload_hash TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (assignment_id) REFERENCES review_assignments(assignment_id)
            ON DELETE CASCADE,
        FOREIGN KEY (reviewer_id) REFERENCES review_users(user_id) ON DELETE RESTRICT
    )
    """,
    """
    CREATE TABLE review_amendments (
        amendment_id TEXT PRIMARY KEY,
        original_judgment_id TEXT NOT NULL,
        replacement_judgment_id TEXT NOT NULL,
        requester_id TEXT NOT NULL,
        reason TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (original_judgment_id) REFERENCES review_judgments(judgment_id)
            ON DELETE RESTRICT,
        FOREIGN KEY (replacement_judgment_id) REFERENCES review_judgments(judgment_id)
            ON DELETE RESTRICT
    )
    """,
    """
    CREATE TABLE review_adjudications (
        adjudication_id TEXT PRIMARY KEY,
        item_id TEXT NOT NULL,
        adjudicator_id TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        payload_hash TEXT NOT NULL,
        evidence_scope TEXT NOT NULL,
        submitted_at TEXT NOT NULL,
        FOREIGN KEY (adjudicator_id) REFERENCES review_users(user_id) ON DELETE RESTRICT
    )
    """,
    """
    CREATE TABLE review_audit_events (
        seq INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id TEXT NOT NULL UNIQUE,
        actor_hash TEXT NOT NULL,
        role TEXT NOT NULL,
        event_type TEXT NOT NULL,
        object_id TEXT NOT NULL,
        previous_hash TEXT,
        new_hash TEXT,
        session_id TEXT,
        classification TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE evidence_nodes (
        node_id TEXT PRIMARY KEY,
        node_type TEXT NOT NULL,
        content_hash TEXT NOT NULL,
        node_version INTEGER NOT NULL,
        evidence_class TEXT NOT NULL,
        public INTEGER NOT NULL,
        metadata_json TEXT NOT NULL,
        metadata_hash TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE evidence_edges (
        edge_id TEXT PRIMARY KEY,
        source_id TEXT NOT NULL,
        target_id TEXT NOT NULL,
        relation TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (source_id) REFERENCES evidence_nodes(node_id) ON DELETE RESTRICT,
        FOREIGN KEY (target_id) REFERENCES evidence_nodes(node_id) ON DELETE RESTRICT
    )
    """,
    """
    CREATE INDEX evidence_lineage_target_idx ON evidence_edges(target_id, relation)
    """,
    """
    CREATE TABLE evidence_state_history (
        history_id TEXT PRIMARY KEY,
        node_id TEXT NOT NULL,
        source_class TEXT NOT NULL,
        target_class TEXT NOT NULL,
        policy_hash TEXT NOT NULL,
        event_hash TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (node_id) REFERENCES evidence_nodes(node_id) ON DELETE RESTRICT
    )
    """,
    """
    CREATE TABLE certificates (
        certificate_id TEXT PRIMARY KEY,
        certificate_type TEXT NOT NULL,
        subject_id TEXT NOT NULL,
        supporting_evidence_json TEXT NOT NULL,
        signer_key_id TEXT NOT NULL,
        issued_at TEXT NOT NULL,
        expires_at TEXT,
        certificate_status TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        payload_hash TEXT NOT NULL,
        signature TEXT NOT NULL,
        public INTEGER NOT NULL
    )
    """,
    """
    CREATE TABLE certificate_revocations (
        revocation_id TEXT PRIMARY KEY,
        certificate_id TEXT NOT NULL,
        reason TEXT NOT NULL,
        superseding_certificate_id TEXT,
        revoked_at TEXT NOT NULL,
        FOREIGN KEY (certificate_id) REFERENCES certificates(certificate_id)
            ON DELETE RESTRICT
    )
    """,
    """
    CREATE TABLE transparency_log (
        sequence INTEGER PRIMARY KEY AUTOINCREMENT,
        previous_hash TEXT NOT NULL,
        current_hash TEXT NOT NULL UNIQUE,
        event_type TEXT NOT NULL,
        subject_id TEXT NOT NULL,
        payload_hash TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE result_corrections (
        correction_id TEXT PRIMARY KEY,
        original_result_id TEXT NOT NULL,
        corrected_result_id TEXT,
        reason TEXT NOT NULL,
        reviewer_hash TEXT NOT NULL,
        public_notice TEXT NOT NULL,
        action TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE evaluation_results (
        result_id TEXT PRIMARY KEY,
        payload_json TEXT NOT NULL,
        payload_hash TEXT NOT NULL,
        status TEXT NOT NULL,
        version INTEGER NOT NULL,
        supersedes_result_id TEXT,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE evaluator_submissions (
        submission_id TEXT PRIMARY KEY,
        submitter_hash TEXT NOT NULL,
        package_hash TEXT NOT NULL,
        image_digest TEXT,
        manifest_json TEXT NOT NULL,
        policy_hash TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE evaluator_queue (
        queue_id TEXT PRIMARY KEY,
        submission_id TEXT NOT NULL,
        priority INTEGER NOT NULL,
        status TEXT NOT NULL,
        evaluator_worker_id TEXT,
        approved_by_hash TEXT,
        disqualification_reason TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (submission_id) REFERENCES evaluator_submissions(submission_id)
            ON DELETE RESTRICT
    )
    """,
    """
    CREATE TABLE evaluator_receipts (
        receipt_id TEXT PRIMARY KEY,
        submission_id TEXT NOT NULL,
        signer_key_id TEXT NOT NULL,
        receipt_json TEXT NOT NULL,
        receipt_hash TEXT NOT NULL,
        evidence_class TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (submission_id) REFERENCES evaluator_submissions(submission_id)
            ON DELETE RESTRICT
    )
    """,
    """
    CREATE TABLE evaluator_revocations (
        revocation_id TEXT PRIMARY KEY,
        receipt_id TEXT NOT NULL,
        reason TEXT NOT NULL,
        revoked_at TEXT NOT NULL,
        FOREIGN KEY (receipt_id) REFERENCES evaluator_receipts(receipt_id)
            ON DELETE RESTRICT
    )
    """,
    """
    CREATE TABLE evaluator_quotas (
        submitter_hash TEXT PRIMARY KEY,
        allowance INTEGER NOT NULL,
        consumed INTEGER NOT NULL,
        window_started_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE benchmark_records (
        record_id TEXT PRIMARY KEY,
        benchmark_id TEXT NOT NULL,
        record_type TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        payload_hash TEXT NOT NULL,
        lifecycle TEXT NOT NULL,
        public INTEGER NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE plugin_records (
        plugin_id TEXT PRIMARY KEY,
        metadata_json TEXT NOT NULL,
        metadata_hash TEXT NOT NULL,
        permissions_json TEXT NOT NULL,
        provenance_json TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TRIGGER review_judgments_no_update
    BEFORE UPDATE ON review_judgments BEGIN
        SELECT RAISE(ABORT, 'review judgments are immutable');
    END
    """,
    """
    CREATE TRIGGER review_judgments_no_delete
    BEFORE DELETE ON review_judgments BEGIN
        SELECT RAISE(ABORT, 'review judgments are immutable');
    END
    """,
    """
    CREATE TRIGGER review_audit_no_update
    BEFORE UPDATE ON review_audit_events BEGIN
        SELECT RAISE(ABORT, 'review audit is append-only');
    END
    """,
    """
    CREATE TRIGGER review_audit_no_delete
    BEFORE DELETE ON review_audit_events BEGIN
        SELECT RAISE(ABORT, 'review audit is append-only');
    END
    """,
    """
    CREATE TRIGGER evidence_history_no_update
    BEFORE UPDATE ON evidence_state_history BEGIN
        SELECT RAISE(ABORT, 'evidence history is append-only');
    END
    """,
    """
    CREATE TRIGGER transparency_no_update
    BEFORE UPDATE ON transparency_log BEGIN
        SELECT RAISE(ABORT, 'transparency log is append-only');
    END
    """,
    """
    CREATE TRIGGER transparency_no_delete
    BEFORE DELETE ON transparency_log BEGIN
        SELECT RAISE(ABORT, 'transparency log is append-only');
    END
    """,
    """
    CREATE TRIGGER certificates_no_update
    BEFORE UPDATE ON certificates BEGIN
        SELECT RAISE(ABORT, 'certificates are immutable; append a revocation');
    END
    """,
    """
    CREATE TRIGGER certificates_no_delete
    BEFORE DELETE ON certificates BEGIN
        SELECT RAISE(ABORT, 'certificates are immutable; append a revocation');
    END
    """,
    """
    CREATE TRIGGER certificate_revocations_no_update
    BEFORE UPDATE ON certificate_revocations BEGIN
        SELECT RAISE(ABORT, 'certificate revocations are append-only');
    END
    """,
    """
    CREATE TRIGGER result_corrections_no_update
    BEFORE UPDATE ON result_corrections BEGIN
        SELECT RAISE(ABORT, 'result corrections are append-only');
    END
    """,
    """
    CREATE TRIGGER evaluation_results_no_update
    BEFORE UPDATE ON evaluation_results BEGIN
        SELECT RAISE(ABORT, 'evaluation results are immutable; append a correction');
    END
    """,
    """
    CREATE TRIGGER benchmark_records_no_update
    BEFORE UPDATE ON benchmark_records BEGIN
        SELECT RAISE(ABORT, 'benchmark records are append-only');
    END
    """,
    """
    CREATE TRIGGER benchmark_records_no_delete
    BEFORE DELETE ON benchmark_records BEGIN
        SELECT RAISE(ABORT, 'benchmark records are append-only');
    END
    """,
    """
    CREATE TRIGGER plugin_records_no_update
    BEFORE UPDATE ON plugin_records BEGIN
        SELECT RAISE(ABORT, 'plugin records are immutable');
    END
    """,
    """
    CREATE TRIGGER evaluator_receipts_no_update
    BEFORE UPDATE ON evaluator_receipts BEGIN
        SELECT RAISE(ABORT, 'evaluator receipts are immutable; append a revocation');
    END
    """,
)

MIGRATION_V3 = Migration(
    migration_id="registry-v3-review-evidence-evaluator",
    source_version=2,
    target_version=3,
    statements=V3_STATEMENTS,
    preconditions=("schema v2 integrity passes", "automatic backup is complete"),
    postconditions=(
        "review, evidence, certificate, transparency, evaluator, benchmark, and plugin tables exist",
    ),
    reversible=False,
    backup_required=True,
)

MIGRATIONS = (MIGRATION_V1, MIGRATION_V2, MIGRATION_V3)
MIGRATION_BY_TARGET = {migration.target_version: migration for migration in MIGRATIONS}


class MigrationManager:
    """Apply ordered migrations with backups, checksums, and crash markers."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30.0, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA busy_timeout = 30000")
        return connection

    def current_version(self) -> int:
        if not self.path.exists():
            return 0
        with self.connect() as connection:
            exists = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='schema_migrations'"
            ).fetchone()
            if not exists:
                return 0
            row = connection.execute(
                "SELECT COALESCE(MAX(version), 0) AS version FROM schema_migrations"
            ).fetchone()
        return int(row["version"]) if row else 0

    def ensure_v1(self) -> None:
        if self.current_version() > 0:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                for statement in MIGRATION_V1.statements:
                    connection.execute(statement)
                connection.execute(
                    "INSERT OR IGNORE INTO schema_migrations(version, applied_at) VALUES (?, ?)",
                    (1, utc_now()),
                )
            except BaseException:
                connection.execute("ROLLBACK")
                raise
            else:
                connection.execute("COMMIT")

    def _ensure_runtime_table(self) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS migration_runtime (
                    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
                    migration_id TEXT,
                    source_version INTEGER,
                    target_version INTEGER,
                    status TEXT NOT NULL,
                    backup_path TEXT,
                    backup_hash TEXT,
                    started_at TEXT,
                    failure_record TEXT
                )
                """
            )
            connection.execute(
                """
                INSERT OR IGNORE INTO migration_runtime(singleton, status)
                VALUES (1, 'IDLE')
                """
            )

    def plan(self, target_version: int = SCHEMA_VERSION) -> dict[str, Any]:
        current = self.current_version()
        if target_version < current:
            raise ValueError("in-place registry downgrade is forbidden")
        if target_version > SCHEMA_VERSION:
            raise ValueError(f"unsupported registry schema version: {target_version}")
        planned = [
            migration
            for migration in MIGRATIONS
            if current < migration.target_version <= target_version
        ]
        return {
            "current_version": current,
            "target_version": target_version,
            "dry_run": True,
            "migrations": [
                {
                    "migration_id": migration.migration_id,
                    "source_version": migration.source_version,
                    "target_version": migration.target_version,
                    "checksum": migration.checksum,
                    "preconditions": list(migration.preconditions),
                    "postconditions": list(migration.postconditions),
                    "reversible": migration.reversible,
                    "backup_required": migration.backup_required,
                }
                for migration in planned
            ],
        }

    def verify_applied_checksums(self) -> list[str]:
        if self.current_version() < 2:
            return []
        errors: list[str] = []
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT version, migration_id, checksum, status FROM schema_migrations"
            ).fetchall()
        for row in rows:
            version = int(row["version"])
            expected = MIGRATION_BY_TARGET.get(version)
            if expected is None:
                errors.append(f"unknown applied migration version: {version}")
            elif str(row["migration_id"]) != expected.migration_id:
                errors.append(f"migration ID mismatch at version {version}")
            elif str(row["checksum"]) != expected.checksum:
                errors.append(f"migration checksum mismatch at version {version}")
            elif str(row["status"]) != "APPLIED":
                errors.append(f"migration {version} is not APPLIED")
        return errors

    def _integrity_check(self) -> None:
        with self.connect() as connection:
            result = str(connection.execute("PRAGMA integrity_check").fetchone()[0])
        if result != "ok":
            raise ValueError(f"pre-migration SQLite integrity failure: {result}")

    def _backup(self, source_version: int, target_version: int) -> tuple[Path, str]:
        backup = self.path.with_name(
            f"{self.path.name}.pre-v{source_version}-to-v{target_version}.backup"
        )
        temporary = backup.with_suffix(backup.suffix + ".tmp")
        if temporary.exists():
            temporary.unlink()
        with self.connect() as source, sqlite3.connect(temporary) as destination:
            source.backup(destination)
        os.replace(temporary, backup)
        return backup, file_sha256(backup)

    def migrate(
        self,
        target_version: int = SCHEMA_VERSION,
        *,
        interrupt_after_statement: int | None = None,
        export_before_upgrade: str | Path | None = None,
    ) -> int:
        current = self.current_version()
        if current == 0:
            self.ensure_v1()
            current = 1
        self.plan(target_version)
        if target_version == current:
            checksum_errors = self.verify_applied_checksums()
            if checksum_errors:
                raise ValueError("; ".join(checksum_errors))
            return current
        if export_before_upgrade is not None:
            destination = Path(export_before_upgrade)
            destination.parent.mkdir(parents=True, exist_ok=True)
            with self.connect() as connection:
                rows = [dict(row) for row in connection.execute("SELECT * FROM entities")]
            destination.write_text(
                json.dumps({"schema_version": current, "entities": rows}, indent=2) + "\n",
                encoding="utf-8",
            )
        self._integrity_check()
        self._ensure_runtime_table()
        checksum_errors = self.verify_applied_checksums()
        if checksum_errors:
            raise ValueError("; ".join(checksum_errors))
        for migration in MIGRATIONS:
            if not (current < migration.target_version <= target_version):
                continue
            if migration.source_version != current:
                raise ValueError(
                    f"migration chain gap: have {current}, "
                    f"next requires {migration.source_version}"
                )
            backup_path: Path | None = None
            backup_hash: str | None = None
            if migration.backup_required:
                backup_path, backup_hash = self._backup(current, migration.target_version)
            with self.connect() as marker:
                marker.execute(
                    """
                    UPDATE migration_runtime
                       SET migration_id=?, source_version=?, target_version=?,
                           status='IN_PROGRESS', backup_path=?, backup_hash=?,
                           started_at=?, failure_record=NULL
                     WHERE singleton=1
                    """,
                    (
                        migration.migration_id,
                        current,
                        migration.target_version,
                        str(backup_path) if backup_path else None,
                        backup_hash,
                        utc_now(),
                    ),
                )
            started = time.monotonic()
            try:
                with self.connect() as connection:
                    connection.execute("BEGIN IMMEDIATE")
                    for index, statement in enumerate(migration.statements, start=1):
                        connection.execute(statement)
                        if interrupt_after_statement == index:
                            raise RuntimeError("simulated interrupted migration")
                    duration_ms = (time.monotonic() - started) * 1000
                    connection.execute(
                        """
                        INSERT INTO schema_migrations(
                            version, migration_id, source_version, target_version,
                            checksum, applied_at, duration_ms, preconditions_json,
                            postconditions_json, reversible, backup_required,
                            backup_hash, status, failure_record
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'APPLIED', NULL)
                        """,
                        (
                            migration.target_version,
                            migration.migration_id,
                            migration.source_version,
                            migration.target_version,
                            migration.checksum,
                            utc_now(),
                            duration_ms,
                            json.dumps(migration.preconditions),
                            json.dumps(migration.postconditions),
                            int(migration.reversible),
                            int(migration.backup_required),
                            backup_hash,
                        ),
                    )
                    connection.execute("COMMIT")
            except BaseException as exc:
                with self.connect() as failed:
                    failed.execute(
                        """
                        UPDATE migration_runtime
                           SET status='FAILED', failure_record=?
                         WHERE singleton=1
                        """,
                        (f"{type(exc).__name__}: {exc}",),
                    )
                raise
            current = migration.target_version
            self._verify_postconditions(migration)
            with self.connect() as marker:
                marker.execute(
                    """
                    UPDATE migration_runtime
                       SET status='IDLE', failure_record=NULL
                     WHERE singleton=1
                    """
                )
        return current

    def recover(self) -> int:
        self._ensure_runtime_table()
        with self.connect() as connection:
            row = connection.execute(
                "SELECT * FROM migration_runtime WHERE singleton=1"
            ).fetchone()
        if row is None or str(row["status"]) == "IDLE":
            return self.current_version()
        source = int(row["source_version"])
        target = int(row["target_version"])
        if self.current_version() != source:
            raise ValueError("interrupted migration state does not match database version")
        backup_path = Path(str(row["backup_path"]))
        if not backup_path.is_file() or file_sha256(backup_path) != str(row["backup_hash"]):
            raise ValueError("interrupted migration backup is missing or corrupt")
        return self.migrate(target)

    def runtime_state(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"status": "MISSING"}
        self._ensure_runtime_table()
        with self.connect() as connection:
            row = connection.execute(
                "SELECT * FROM migration_runtime WHERE singleton=1"
            ).fetchone()
        return dict(row) if row else {"status": "UNKNOWN"}

    def history(self) -> list[dict[str, Any]]:
        if self.current_version() < 2:
            with self.connect() as connection:
                rows = connection.execute(
                    "SELECT version, applied_at FROM schema_migrations ORDER BY version"
                ).fetchall()
            return [dict(row) for row in rows]
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM schema_migrations ORDER BY version"
            ).fetchall()
        return [dict(row) for row in rows]

    def _verify_postconditions(self, migration: Migration) -> None:
        required_by_version = {
            1: {"entities", "events", "provenance_edges"},
            2: {"queue_entries", "worker_leases", "scheduler_attempts"},
            3: {
                "review_users",
                "evidence_nodes",
                "certificates",
                "transparency_log",
                "evaluator_submissions",
            },
        }
        with self.connect() as connection:
            tables = {
                str(row["name"])
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
        missing = required_by_version[migration.target_version] - tables
        if missing:
            raise ValueError(
                f"migration {migration.migration_id} postcondition failed: {sorted(missing)}"
            )


__all__ = [
    "MIGRATIONS",
    "MIGRATION_BY_TARGET",
    "SCHEMA_VERSION",
    "Migration",
    "MigrationManager",
]
