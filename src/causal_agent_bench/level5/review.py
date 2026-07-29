"""Local-first human review contracts, assignment, agreement, and C10 gating."""

from __future__ import annotations

import json
import math
import secrets
import time
from collections import Counter, defaultdict
from contextlib import suppress
from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator

from causal_agent_bench.level5.core import content_hash, utc_now
from causal_agent_bench.level5.registry import SQLiteRegistry


class ReviewerRole(StrEnum):
    REVIEWER = "REVIEWER"
    ADJUDICATOR = "ADJUDICATOR"
    ADMINISTRATOR = "ADMINISTRATOR"


class AssignmentState(StrEnum):
    INVITED = "INVITED"
    QUALIFICATION_PENDING = "QUALIFICATION_PENDING"
    QUALIFIED = "QUALIFIED"
    ACTIVE = "ACTIVE"
    ASSIGNED = "ASSIGNED"
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    AMENDMENT_REQUESTED = "AMENDMENT_REQUESTED"
    SUPERSEDED = "SUPERSEDED"
    ADJUDICATION_PENDING = "ADJUDICATION_PENDING"
    ADJUDICATED = "ADJUDICATED"
    EXCLUDED = "EXCLUDED"
    C10_READY = "C10_READY"
    ARCHIVED = "ARCHIVED"


class Reviewer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reviewer_id: str
    role: ReviewerRole
    qualified: bool
    consented: bool
    human_attestation: bool
    proxy_or_ai_assistance: bool = False
    conflicts: list[str] = Field(default_factory=list)
    expertise: list[str] = Field(default_factory=list)
    compensation_disclosed: bool = False

    @model_validator(mode="after")
    def validate_human(self) -> Reviewer:
        if not self.human_attestation or self.proxy_or_ai_assistance:
            raise ValueError("review evidence requires direct human attestation without AI/proxy")
        if not self.consented:
            raise ValueError("reviewer consent is required")
        return self


class Assignment(BaseModel):
    assignment_id: str
    item_id: str
    reviewer_id: str
    role: ReviewerRole
    assignment_order: int
    receipt_hash: str


class Judgment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    judgment_id: str
    assignment_id: str
    item_id: str
    reviewer_id: str
    valid: bool
    manipulation_passed: bool
    invariant: bool
    solvable: bool
    confidence: float = Field(ge=0, le=1)
    time_seconds: float = Field(gt=0)
    notes: str = ""
    submitted_at: str
    evidence_scope: str = Field(pattern=r"^(GENUINE_HUMAN|FIXTURE_ONLY)$")
    supersedes: str | None = None


class Adjudication(BaseModel):
    adjudication_id: str
    item_id: str
    adjudicator_id: str
    decision: bool
    rationale: str = Field(min_length=1)
    submitted_at: str
    evidence_scope: str = Field(pattern=r"^(GENUINE_HUMAN|FIXTURE_ONLY)$")


def assign_reviews(
    items: list[str],
    reviewers: list[Reviewer],
    *,
    reviews_per_item: int = 2,
) -> list[Assignment]:
    eligible = sorted(
        [
            reviewer
            for reviewer in reviewers
            if reviewer.role is ReviewerRole.REVIEWER and reviewer.qualified
        ],
        key=lambda reviewer: reviewer.reviewer_id,
    )
    if len(eligible) < reviews_per_item:
        raise ValueError("insufficient independent qualified reviewers")
    workload: Counter[str] = Counter()
    assignments: list[Assignment] = []
    for item in sorted(items, key=lambda value: content_hash(value)):
        available = [reviewer for reviewer in eligible if item not in reviewer.conflicts]
        available.sort(key=lambda reviewer: (workload[reviewer.reviewer_id], reviewer.reviewer_id))
        selected = available[:reviews_per_item]
        if len(selected) < reviews_per_item:
            raise ValueError(f"insufficient conflict-free coverage for {item}")
        for order, reviewer in enumerate(selected):
            payload = {
                "item_id": item,
                "reviewer_id": reviewer.reviewer_id,
                "order": order,
            }
            receipt = content_hash(payload)
            assignments.append(
                Assignment(
                    assignment_id=f"assignment.{receipt[:24]}",
                    item_id=item,
                    reviewer_id=reviewer.reviewer_id,
                    role=reviewer.role,
                    assignment_order=order,
                    receipt_hash=receipt,
                )
            )
            workload[reviewer.reviewer_id] += 1
    return assignments


class ReviewStore:
    """In-memory immutable submission ledger used by the local service and tests."""

    def __init__(self) -> None:
        self._judgments: dict[str, Judgment] = {}
        self._amendments: list[dict[str, Any]] = []

    def submit(self, judgment: Judgment) -> Judgment:
        if judgment.judgment_id in self._judgments:
            existing = self._judgments[judgment.judgment_id]
            if existing != judgment:
                raise ValueError("submitted judgments are immutable")
            return existing
        self._judgments[judgment.judgment_id] = judgment
        return judgment

    def amend(self, original_id: str, replacement: Judgment, *, reason: str) -> Judgment:
        if original_id not in self._judgments:
            raise KeyError(original_id)
        if replacement.supersedes != original_id:
            raise ValueError("amendment must name the superseded judgment")
        self.submit(replacement)
        self._amendments.append(
            {
                "original_id": original_id,
                "replacement_id": replacement.judgment_id,
                "reason": reason,
                "created_at": utc_now(),
            }
        )
        return replacement

    @property
    def judgments(self) -> list[Judgment]:
        superseded = {row["original_id"] for row in self._amendments}
        return [
            judgment
            for judgment_id, judgment in self._judgments.items()
            if judgment_id not in superseded
        ]

    @property
    def amendments(self) -> list[dict[str, Any]]:
        return list(self._amendments)


class IdentityProvider(Protocol):
    name: str

    def resolve(self, user_id: str, assertion: str) -> dict[str, str]: ...


class LocalDevelopmentIdentityProvider:
    """Explicitly fixture-only identity adapter for local development."""

    name = "local-development-fixture"

    def resolve(self, user_id: str, assertion: str) -> dict[str, str]:
        expected = f"local-development:{user_id}"
        if not secrets.compare_digest(assertion, expected):
            raise PermissionError("local development identity assertion rejected")
        return {
            "external_subject_hash": content_hash([self.name, user_id]),
            "evidence_scope": "FIXTURE_ONLY",
            "identity_assurance": "LOCAL_DEVELOPMENT_ONLY",
        }


class ExternalIdentityProvider(Protocol):
    """Deployment interface; no real-world provider is claimed by the fixture."""

    name: str

    def resolve(self, user_id: str, assertion: str) -> dict[str, str]: ...


class EncryptedReviewStorage(Protocol):
    def store_private_identity(self, subject_hash: str, encrypted_blob: bytes) -> str: ...

    def load_private_identity(self, reference: str) -> bytes: ...


class ReviewSession(BaseModel):
    session_id: str
    user_id: str
    role: ReviewerRole
    token: str
    csrf_token: str
    expires_at: float


class DurableReviewStore:
    """Private SQLite review repository with hashed sessions and immutable finals."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with suppress(OSError):
            self.path.parent.chmod(0o700)
        self.registry = SQLiteRegistry(self.path)
        self.registry.initialize()

    def directory_permissions(self) -> dict[str, Any]:
        mode = self.path.parent.stat().st_mode & 0o777
        return {
            "path": str(self.path.parent),
            "mode": oct(mode),
            "private": mode & 0o077 == 0,
        }

    @staticmethod
    def _token_hash(token: str) -> str:
        return content_hash(["review-session-token", token])

    @staticmethod
    def _csrf_hash(token: str) -> str:
        return content_hash(["review-csrf-token", token])

    @staticmethod
    def _audit(
        connection: Any,
        *,
        actor: str,
        role: str,
        event_type: str,
        object_id: str,
        previous_hash: str | None,
        new_hash: str | None,
        session_id: str | None,
        classification: str,
    ) -> None:
        connection.execute(
            """
            INSERT INTO review_audit_events(
                event_id, actor_hash, role, event_type, object_id,
                previous_hash, new_hash, session_id, classification, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"review-event.{secrets.token_hex(16)}",
                content_hash(actor),
                role,
                event_type,
                object_id,
                previous_hash,
                new_hash,
                session_id,
                classification,
                utc_now(),
            ),
        )

    def register_user(
        self,
        user_id: str,
        role: ReviewerRole,
        *,
        evidence_scope: str = "FIXTURE_ONLY",
        external_subject_hash: str | None = None,
    ) -> dict[str, Any]:
        if evidence_scope not in {"FIXTURE_ONLY", "GENUINE_HUMAN"}:
            raise ValueError("invalid review evidence scope")
        now = utc_now()
        with self.registry.transaction() as connection:
            existing = connection.execute(
                "SELECT * FROM review_users WHERE user_id=?",
                (user_id,),
            ).fetchone()
            if existing:
                if (
                    str(existing["role"]) != role.value
                    or str(existing["evidence_scope"]) != evidence_scope
                ):
                    raise ValueError("review user registration conflict")
                return dict(existing)
            connection.execute(
                """
                INSERT INTO review_users(
                    user_id, external_subject_hash, role, qualified, consented,
                    human_attestation, evidence_scope, status, created_at, updated_at
                ) VALUES (?, ?, ?, 0, 0, 0, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    external_subject_hash,
                    role.value,
                    evidence_scope,
                    AssignmentState.QUALIFICATION_PENDING.value,
                    now,
                    now,
                ),
            )
            self._audit(
                connection,
                actor="system",
                role=ReviewerRole.ADMINISTRATOR.value,
                event_type="USER_REGISTERED",
                object_id=user_id,
                previous_hash=None,
                new_hash=content_hash([user_id, role.value, evidence_scope]),
                session_id=None,
                classification="PRIVATE",
            )
            row = connection.execute(
                "SELECT * FROM review_users WHERE user_id=?",
                (user_id,),
            ).fetchone()
        return dict(row)

    def qualify_user(
        self,
        user_id: str,
        *,
        consented: bool,
        human_attestation: bool,
        proxy_or_ai_assistance: bool,
    ) -> dict[str, Any]:
        if not consented:
            raise ValueError("reviewer consent is required")
        if not human_attestation or proxy_or_ai_assistance:
            raise ValueError("direct human attestation without AI/proxy is required")
        with self.registry.transaction() as connection:
            row = connection.execute(
                "SELECT * FROM review_users WHERE user_id=?",
                (user_id,),
            ).fetchone()
            if row is None:
                raise KeyError(user_id)
            previous = content_hash(dict(row))
            connection.execute(
                """
                UPDATE review_users
                   SET qualified=1, consented=1, human_attestation=1,
                       status=?, updated_at=?
                 WHERE user_id=?
                """,
                (AssignmentState.QUALIFIED.value, utc_now(), user_id),
            )
            updated = connection.execute(
                "SELECT * FROM review_users WHERE user_id=?",
                (user_id,),
            ).fetchone()
            self._audit(
                connection,
                actor=user_id,
                role=str(updated["role"]),
                event_type="USER_QUALIFIED",
                object_id=user_id,
                previous_hash=previous,
                new_hash=content_hash(dict(updated)),
                session_id=None,
                classification="PRIVATE",
            )
        return dict(updated)

    def create_session(
        self,
        user_id: str,
        *,
        ttl_seconds: float = 3600,
    ) -> ReviewSession:
        if ttl_seconds <= 0 or ttl_seconds > 86400:
            raise ValueError("session TTL must be within one day")
        token = secrets.token_urlsafe(32)
        csrf = secrets.token_urlsafe(32)
        expires_at = time.time() + ttl_seconds
        session_id = f"session.{secrets.token_hex(16)}"
        with self.registry.transaction() as connection:
            user = connection.execute(
                "SELECT * FROM review_users WHERE user_id=?",
                (user_id,),
            ).fetchone()
            if user is None:
                raise KeyError(user_id)
            connection.execute(
                """
                INSERT INTO review_sessions(
                    session_id, user_id, token_hash, csrf_hash,
                    expires_at, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    user_id,
                    self._token_hash(token),
                    self._csrf_hash(csrf),
                    expires_at,
                    utc_now(),
                ),
            )
            self._audit(
                connection,
                actor=user_id,
                role=str(user["role"]),
                event_type="SESSION_CREATED",
                object_id=session_id,
                previous_hash=None,
                new_hash=content_hash([session_id, expires_at]),
                session_id=session_id,
                classification="PRIVATE",
            )
        return ReviewSession(
            session_id=session_id,
            user_id=user_id,
            role=ReviewerRole(str(user["role"])),
            token=token,
            csrf_token=csrf,
            expires_at=expires_at,
        )

    def authenticate(
        self,
        token: str,
        *,
        csrf_token: str | None = None,
        allowed_roles: set[ReviewerRole] | None = None,
    ) -> dict[str, Any]:
        with self.registry._connect() as connection:
            row = connection.execute(
                """
                SELECT s.*, u.role, u.qualified, u.evidence_scope
                  FROM review_sessions s
                  JOIN review_users u ON u.user_id=s.user_id
                 WHERE s.token_hash=?
                """,
                (self._token_hash(token),),
            ).fetchone()
        if row is None or row["revoked_at"] is not None:
            raise PermissionError("invalid or revoked review session")
        if float(row["expires_at"]) <= time.time():
            raise PermissionError("review session expired")
        if csrf_token is not None and not secrets.compare_digest(
            str(row["csrf_hash"]),
            self._csrf_hash(csrf_token),
        ):
            raise PermissionError("CSRF token rejected")
        role = ReviewerRole(str(row["role"]))
        if allowed_roles and role not in allowed_roles:
            raise PermissionError("review role is not authorised")
        return dict(row)

    def logout(self, token: str) -> None:
        session = self.authenticate(token)
        with self.registry.transaction() as connection:
            connection.execute(
                "UPDATE review_sessions SET revoked_at=? WHERE session_id=?",
                (utc_now(), session["session_id"]),
            )
            self._audit(
                connection,
                actor=str(session["user_id"]),
                role=str(session["role"]),
                event_type="SESSION_REVOKED",
                object_id=str(session["session_id"]),
                previous_hash=content_hash([session["session_id"], "ACTIVE"]),
                new_hash=content_hash([session["session_id"], "REVOKED"]),
                session_id=str(session["session_id"]),
                classification="PRIVATE",
            )

    def assign(
        self,
        admin_token: str,
        item_ids: list[str],
        reviewer_ids: list[str],
        *,
        reviews_per_item: int = 2,
    ) -> list[dict[str, Any]]:
        admin = self.authenticate(
            admin_token,
            allowed_roles={ReviewerRole.ADMINISTRATOR},
        )
        if len(set(reviewer_ids)) < reviews_per_item:
            raise ValueError("insufficient independent reviewers")
        assignments: list[dict[str, Any]] = []
        workload: Counter[str] = Counter()
        with self.registry.transaction() as connection:
            users = {
                str(row["user_id"]): row
                for row in connection.execute(
                    "SELECT * FROM review_users WHERE user_id IN "
                    f"({','.join('?' for _ in reviewer_ids)})",
                    tuple(reviewer_ids),
                )
            }
            for reviewer_id in reviewer_ids:
                user = users.get(reviewer_id)
                if (
                    user is None
                    or str(user["role"]) != ReviewerRole.REVIEWER.value
                    or not bool(user["qualified"])
                ):
                    raise ValueError(f"reviewer is not qualified: {reviewer_id}")
            for item_id in sorted(item_ids, key=content_hash):
                selected = sorted(
                    reviewer_ids,
                    key=lambda value: (workload[value], content_hash([item_id, value])),
                )[:reviews_per_item]
                for order, reviewer_id in enumerate(selected):
                    payload = {
                        "item_id": item_id,
                        "reviewer_id": reviewer_id,
                        "assignment_version": 1,
                        "blinded_order": order,
                    }
                    receipt = content_hash(payload)
                    assignment_id = f"assignment.{receipt[:24]}"
                    connection.execute(
                        """
                        INSERT INTO review_assignments(
                            assignment_id, item_id, reviewer_id, assignment_version,
                            blinded_order, state, receipt_hash, created_at, updated_at
                        ) VALUES (?, ?, ?, 1, ?, ?, ?, ?, ?)
                        """,
                        (
                            assignment_id,
                            item_id,
                            reviewer_id,
                            order,
                            AssignmentState.ASSIGNED.value,
                            receipt,
                            utc_now(),
                            utc_now(),
                        ),
                    )
                    self._audit(
                        connection,
                        actor=str(admin["user_id"]),
                        role=ReviewerRole.ADMINISTRATOR.value,
                        event_type="ASSIGNMENT_CREATED",
                        object_id=assignment_id,
                        previous_hash=None,
                        new_hash=receipt,
                        session_id=str(admin["session_id"]),
                        classification="PRIVATE",
                    )
                    assignments.append(
                        {
                            **payload,
                            "assignment_id": assignment_id,
                            "state": AssignmentState.ASSIGNED.value,
                            "receipt_hash": receipt,
                        }
                    )
                    workload[reviewer_id] += 1
        return assignments

    def declare_conflict(
        self,
        token: str,
        csrf_token: str,
        assignment_id: str,
    ) -> None:
        session = self.authenticate(
            token,
            csrf_token=csrf_token,
            allowed_roles={ReviewerRole.REVIEWER},
        )
        with self.registry.transaction() as connection:
            row = connection.execute(
                "SELECT * FROM review_assignments WHERE assignment_id=?",
                (assignment_id,),
            ).fetchone()
            if row is None or str(row["reviewer_id"]) != str(session["user_id"]):
                raise PermissionError("assignment is not owned by this reviewer")
            connection.execute(
                "UPDATE review_assignments SET conflict_declared=1, state=?, "
                "updated_at=? WHERE assignment_id=?",
                (AssignmentState.EXCLUDED.value, utc_now(), assignment_id),
            )
            self._audit(
                connection,
                actor=str(session["user_id"]),
                role=ReviewerRole.REVIEWER.value,
                event_type="CONFLICT_DECLARED",
                object_id=assignment_id,
                previous_hash=str(row["receipt_hash"]),
                new_hash=content_hash([row["receipt_hash"], "conflict"]),
                session_id=str(session["session_id"]),
                classification="PRIVATE",
            )

    def autosave_draft(
        self,
        token: str,
        csrf_token: str,
        assignment_id: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        session = self.authenticate(
            token,
            csrf_token=csrf_token,
            allowed_roles={ReviewerRole.REVIEWER},
        )
        payload_json = json.dumps(payload, sort_keys=True)
        payload_hash = content_hash(payload)
        with self.registry.transaction() as connection:
            assignment = connection.execute(
                "SELECT * FROM review_assignments WHERE assignment_id=?",
                (assignment_id,),
            ).fetchone()
            if assignment is None or str(assignment["reviewer_id"]) != str(
                session["user_id"]
            ):
                raise PermissionError("assignment is not owned by this reviewer")
            if str(assignment["state"]) not in {
                AssignmentState.ASSIGNED.value,
                AssignmentState.DRAFT.value,
            }:
                raise ValueError("assignment no longer accepts draft changes")
            previous = connection.execute(
                "SELECT payload_hash FROM review_drafts WHERE assignment_id=?",
                (assignment_id,),
            ).fetchone()
            connection.execute(
                """
                INSERT INTO review_drafts(
                    assignment_id, reviewer_id, payload_json, payload_hash, updated_at
                ) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(assignment_id) DO UPDATE SET
                    payload_json=excluded.payload_json,
                    payload_hash=excluded.payload_hash,
                    updated_at=excluded.updated_at
                """,
                (
                    assignment_id,
                    session["user_id"],
                    payload_json,
                    payload_hash,
                    utc_now(),
                ),
            )
            connection.execute(
                "UPDATE review_assignments SET state=?, updated_at=? WHERE assignment_id=?",
                (AssignmentState.DRAFT.value, utc_now(), assignment_id),
            )
            self._audit(
                connection,
                actor=str(session["user_id"]),
                role=ReviewerRole.REVIEWER.value,
                event_type="DRAFT_AUTOSAVED",
                object_id=assignment_id,
                previous_hash=str(previous["payload_hash"]) if previous else None,
                new_hash=payload_hash,
                session_id=str(session["session_id"]),
                classification="PRIVATE",
            )
        return {"assignment_id": assignment_id, "payload_hash": payload_hash, "saved": True}

    def submit_judgment(
        self,
        token: str,
        csrf_token: str,
        judgment: Judgment,
    ) -> Judgment:
        session = self.authenticate(
            token,
            csrf_token=csrf_token,
            allowed_roles={ReviewerRole.REVIEWER},
        )
        if judgment.reviewer_id != session["user_id"]:
            raise PermissionError("judgment reviewer does not match session")
        if judgment.evidence_scope != session["evidence_scope"]:
            raise ValueError("judgment evidence scope does not match reviewer identity scope")
        payload = judgment.model_dump(mode="json")
        payload_hash = content_hash(payload)
        with self.registry.transaction() as connection:
            assignment = connection.execute(
                "SELECT * FROM review_assignments WHERE assignment_id=?",
                (judgment.assignment_id,),
            ).fetchone()
            if (
                assignment is None
                or str(assignment["reviewer_id"]) != judgment.reviewer_id
                or str(assignment["item_id"]) != judgment.item_id
            ):
                raise PermissionError("judgment assignment mismatch")
            if bool(assignment["conflict_declared"]):
                raise ValueError("conflicted assignment cannot be submitted")
            existing = connection.execute(
                "SELECT payload_hash FROM review_judgments WHERE judgment_id=?",
                (judgment.judgment_id,),
            ).fetchone()
            if existing:
                if str(existing["payload_hash"]) != payload_hash:
                    raise ValueError("submitted judgments are immutable")
                return judgment
            if str(assignment["state"]) not in {
                AssignmentState.ASSIGNED.value,
                AssignmentState.DRAFT.value,
                AssignmentState.AMENDMENT_REQUESTED.value,
            }:
                raise ValueError("assignment is not open for submission")
            connection.execute(
                """
                INSERT INTO review_judgments(
                    judgment_id, assignment_id, item_id, reviewer_id,
                    payload_json, payload_hash, evidence_scope, submitted_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    judgment.judgment_id,
                    judgment.assignment_id,
                    judgment.item_id,
                    judgment.reviewer_id,
                    json.dumps(payload, sort_keys=True),
                    payload_hash,
                    judgment.evidence_scope,
                    judgment.submitted_at,
                ),
            )
            connection.execute(
                "DELETE FROM review_drafts WHERE assignment_id=?",
                (judgment.assignment_id,),
            )
            connection.execute(
                "UPDATE review_assignments SET state=?, updated_at=? WHERE assignment_id=?",
                (
                    AssignmentState.SUBMITTED.value,
                    utc_now(),
                    judgment.assignment_id,
                ),
            )
            self._audit(
                connection,
                actor=judgment.reviewer_id,
                role=ReviewerRole.REVIEWER.value,
                event_type="JUDGMENT_SUBMITTED",
                object_id=judgment.judgment_id,
                previous_hash=None,
                new_hash=payload_hash,
                session_id=str(session["session_id"]),
                classification="PRIVATE",
            )
        return judgment

    def adjudicate(
        self,
        token: str,
        csrf_token: str,
        adjudication: Adjudication,
    ) -> Adjudication:
        session = self.authenticate(
            token,
            csrf_token=csrf_token,
            allowed_roles={ReviewerRole.ADJUDICATOR},
        )
        if adjudication.adjudicator_id != session["user_id"]:
            raise PermissionError("adjudicator does not match session")
        if adjudication.evidence_scope != session["evidence_scope"]:
            raise ValueError("adjudication evidence scope mismatch")
        payload = adjudication.model_dump(mode="json")
        payload_hash = content_hash(payload)
        with self.registry.transaction() as connection:
            reviewer_overlap = connection.execute(
                "SELECT 1 FROM review_assignments WHERE item_id=? AND reviewer_id=?",
                (adjudication.item_id, adjudication.adjudicator_id),
            ).fetchone()
            if reviewer_overlap:
                raise PermissionError("adjudicator must be independent of item reviewers")
            connection.execute(
                """
                INSERT INTO review_adjudications(
                    adjudication_id, item_id, adjudicator_id, payload_json,
                    payload_hash, evidence_scope, submitted_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    adjudication.adjudication_id,
                    adjudication.item_id,
                    adjudication.adjudicator_id,
                    json.dumps(payload, sort_keys=True),
                    payload_hash,
                    adjudication.evidence_scope,
                    adjudication.submitted_at,
                ),
            )
            connection.execute(
                "UPDATE review_assignments SET state=?, updated_at=? WHERE item_id=? "
                "AND state=?",
                (
                    AssignmentState.ADJUDICATED.value,
                    utc_now(),
                    adjudication.item_id,
                    AssignmentState.SUBMITTED.value,
                ),
            )
            self._audit(
                connection,
                actor=adjudication.adjudicator_id,
                role=ReviewerRole.ADJUDICATOR.value,
                event_type="ITEM_ADJUDICATED",
                object_id=adjudication.adjudication_id,
                previous_hash=None,
                new_hash=payload_hash,
                session_id=str(session["session_id"]),
                classification="PRIVATE",
            )
        return adjudication

    def request_amendment(
        self,
        admin_token: str,
        original_judgment_id: str,
        *,
        reason: str,
    ) -> None:
        admin = self.authenticate(
            admin_token,
            allowed_roles={ReviewerRole.ADMINISTRATOR},
        )
        if not reason.strip():
            raise ValueError("amendment reason is required")
        with self.registry.transaction() as connection:
            row = connection.execute(
                "SELECT * FROM review_judgments WHERE judgment_id=?",
                (original_judgment_id,),
            ).fetchone()
            if row is None:
                raise KeyError(original_judgment_id)
            connection.execute(
                "UPDATE review_assignments SET state=?, updated_at=? WHERE assignment_id=?",
                (
                    AssignmentState.AMENDMENT_REQUESTED.value,
                    utc_now(),
                    row["assignment_id"],
                ),
            )
            self._audit(
                connection,
                actor=str(admin["user_id"]),
                role=ReviewerRole.ADMINISTRATOR.value,
                event_type="AMENDMENT_REQUESTED",
                object_id=original_judgment_id,
                previous_hash=str(row["payload_hash"]),
                new_hash=content_hash([row["payload_hash"], reason]),
                session_id=str(admin["session_id"]),
                classification="PRIVATE",
            )

    def record_amendment(
        self,
        token: str,
        csrf_token: str,
        original_judgment_id: str,
        replacement: Judgment,
        *,
        reason: str,
    ) -> Judgment:
        if replacement.supersedes != original_judgment_id:
            raise ValueError("replacement must name the superseded judgment")
        self.submit_judgment(token, csrf_token, replacement)
        session = self.authenticate(token)
        amendment_id = f"amendment.{content_hash([original_judgment_id, replacement.judgment_id])[:24]}"
        with self.registry.transaction() as connection:
            connection.execute(
                """
                INSERT INTO review_amendments(
                    amendment_id, original_judgment_id, replacement_judgment_id,
                    requester_id, reason, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    amendment_id,
                    original_judgment_id,
                    replacement.judgment_id,
                    session["user_id"],
                    reason,
                    utc_now(),
                ),
            )
            self._audit(
                connection,
                actor=str(session["user_id"]),
                role=str(session["role"]),
                event_type="JUDGMENT_SUPERSEDED",
                object_id=original_judgment_id,
                previous_hash=content_hash(original_judgment_id),
                new_hash=content_hash(replacement.judgment_id),
                session_id=str(session["session_id"]),
                classification="PRIVATE",
            )
        return replacement

    def assignments_for(self, user_id: str) -> list[dict[str, Any]]:
        with self.registry._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM review_assignments WHERE reviewer_id=? "
                "ORDER BY state, blinded_order, assignment_id",
                (user_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def dashboard(self) -> dict[str, Any]:
        with self.registry._connect() as connection:
            coverage = [
                dict(row)
                for row in connection.execute(
                    """
                    SELECT item_id,
                           COUNT(*) AS assignment_count,
                           SUM(state IN ('SUBMITTED','ADJUDICATED')) AS submitted_count
                      FROM review_assignments
                     GROUP BY item_id ORDER BY item_id
                    """
                )
            ]
            workload = [
                dict(row)
                for row in connection.execute(
                    """
                    SELECT reviewer_id, COUNT(*) AS assigned,
                           SUM(state IN ('SUBMITTED','ADJUDICATED')) AS submitted
                      FROM review_assignments
                     GROUP BY reviewer_id ORDER BY reviewer_id
                    """
                )
            ]
            judgments = [
                Judgment.model_validate_json(str(row["payload_json"]))
                for row in connection.execute("SELECT payload_json FROM review_judgments")
            ]
        return {
            "coverage": coverage,
            "workload": workload,
            "agreement": agreement_report(judgments),
            "scientific_state": "HUMAN_VALIDATION_REQUIRED",
        }

    def _active_judgments(self) -> list[Judgment]:
        with self.registry._connect() as connection:
            superseded = {
                str(row["original_judgment_id"])
                for row in connection.execute(
                    "SELECT original_judgment_id FROM review_amendments"
                )
            }
            rows = connection.execute(
                "SELECT judgment_id, payload_json FROM review_judgments"
            ).fetchall()
        return [
            Judgment.model_validate_json(str(row["payload_json"]))
            for row in rows
            if str(row["judgment_id"]) not in superseded
        ]

    def adjudications(self) -> list[Adjudication]:
        with self.registry._connect() as connection:
            rows = connection.execute(
                "SELECT payload_json FROM review_adjudications ORDER BY adjudication_id"
            ).fetchall()
        return [Adjudication.model_validate_json(str(row["payload_json"])) for row in rows]

    def c10_status(self, item_ids: list[str]) -> dict[str, Any]:
        return evaluate_c10(item_ids, self._active_judgments(), self.adjudications())

    def export_public(self) -> dict[str, Any]:
        dashboard = self.dashboard()
        judgments = self._active_judgments()
        return {
            "schema_version": "1.0",
            "reviewer_count": len({content_hash(row.reviewer_id) for row in judgments}),
            "judgment_count": len(judgments),
            "genuine_judgment_count": sum(
                row.evidence_scope == "GENUINE_HUMAN" for row in judgments
            ),
            "fixture_judgment_count": sum(
                row.evidence_scope == "FIXTURE_ONLY" for row in judgments
            ),
            "coverage": [
                {
                    "item_id_hash": content_hash(str(row["item_id"])),
                    "assignment_count": row["assignment_count"],
                    "submitted_count": row["submitted_count"],
                }
                for row in dashboard["coverage"]
            ],
            "agreement": dashboard["agreement"],
            "identity_fields_exported": False,
            "notes_exported": False,
            "scientific_state": "HUMAN_VALIDATION_REQUIRED",
        }

    def export_private(self) -> dict[str, Any]:
        with self.registry._connect() as connection:
            return {
                "users": [
                    {
                        **dict(row),
                        "user_id": content_hash(str(row["user_id"])),
                        "external_subject_hash": row["external_subject_hash"],
                    }
                    for row in connection.execute("SELECT * FROM review_users ORDER BY user_id")
                ],
                "assignments": [
                    dict(row)
                    for row in connection.execute(
                        "SELECT * FROM review_assignments ORDER BY assignment_id"
                    )
                ],
                "audit": [
                    dict(row)
                    for row in connection.execute(
                        "SELECT * FROM review_audit_events ORDER BY seq"
                    )
                ],
                "raw_identity_exported": False,
            }

    def backup(self, destination: str | Path) -> Path:
        return self.registry.backup(destination)

    @classmethod
    def restore(cls, backup: str | Path, destination: str | Path) -> DurableReviewStore:
        SQLiteRegistry.restore(backup, destination)
        return cls(destination)


def _wilson(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total == 0:
        return (0.0, 0.0)
    proportion = successes / total
    denominator = 1 + z * z / total
    centre = (proportion + z * z / (2 * total)) / denominator
    margin = (
        z
        * math.sqrt(
            proportion * (1 - proportion) / total + z * z / (4 * total * total)
        )
        / denominator
    )
    return (max(0.0, centre - margin), min(1.0, centre + margin))


def agreement_report(judgments: list[Judgment]) -> dict[str, Any]:
    by_item: dict[str, list[Judgment]] = defaultdict(list)
    for judgment in judgments:
        by_item[judgment.item_id].append(judgment)
    paired = [rows[:2] for rows in by_item.values() if len(rows) >= 2]
    agreements = sum(rows[0].valid == rows[1].valid for rows in paired)
    total = len(paired)
    raw = agreements / total if total else 0.0
    labels_a = [rows[0].valid for rows in paired]
    labels_b = [rows[1].valid for rows in paired]
    p_yes_a = sum(labels_a) / total if total else 0.0
    p_yes_b = sum(labels_b) / total if total else 0.0
    expected = p_yes_a * p_yes_b + (1 - p_yes_a) * (1 - p_yes_b)
    kappa = (raw - expected) / (1 - expected) if total and expected < 1 else 0.0
    observed_disagreement = 1 - raw
    all_labels = labels_a + labels_b
    prevalence = sum(all_labels) / len(all_labels) if all_labels else 0.0
    expected_disagreement = 2 * prevalence * (1 - prevalence)
    alpha = (
        1 - observed_disagreement / expected_disagreement
        if expected_disagreement
        else 0.0
    )
    interval = _wilson(agreements, total)
    times = [judgment.time_seconds for judgment in judgments]
    median_time = sorted(times)[len(times) // 2] if times else 0.0
    return {
        "paired_items": total,
        "raw_agreement": raw,
        "wilson_95": list(interval),
        "cohen_kappa": kappa,
        "krippendorff_alpha_nominal": alpha,
        "positive_prevalence": prevalence,
        "median_time_seconds": median_time,
        "time_anomaly_count": sum(
            value < max(1.0, median_time * 0.1) for value in times
        ),
        "straight_line_reviewers": sorted(
            reviewer_id
            for reviewer_id, rows in _by_reviewer(judgments).items()
            if len(rows) >= 5 and len({row.valid for row in rows}) == 1
        ),
    }


def _by_reviewer(judgments: list[Judgment]) -> dict[str, list[Judgment]]:
    grouped: dict[str, list[Judgment]] = defaultdict(list)
    for judgment in judgments:
        grouped[judgment.reviewer_id].append(judgment)
    return grouped


def evaluate_c10(
    item_ids: list[str],
    judgments: list[Judgment],
    adjudications: list[Adjudication],
) -> dict[str, Any]:
    """Fail-closed C10 readiness; fixtures can never pass."""

    blockers: list[str] = []
    if not judgments:
        blockers.append("no genuine human judgments")
    if any(row.evidence_scope != "GENUINE_HUMAN" for row in judgments):
        blockers.append("fixture or non-genuine judgment present")
    if any(row.evidence_scope != "GENUINE_HUMAN" for row in adjudications):
        blockers.append("fixture or non-genuine adjudication present")
    by_item: dict[str, list[Judgment]] = defaultdict(list)
    for judgment in judgments:
        by_item[judgment.item_id].append(judgment)
    for item_id in item_ids:
        reviewers = {row.reviewer_id for row in by_item[item_id]}
        if len(reviewers) < 2:
            blockers.append(f"{item_id}: fewer than two independent judgments")
            continue
        decisions = {row.valid for row in by_item[item_id]}
        if len(decisions) > 1 and not any(row.item_id == item_id for row in adjudications):
            blockers.append(f"{item_id}: unresolved adjudication")
        for row in by_item[item_id]:
            if not (row.manipulation_passed and row.invariant and row.solvable):
                blockers.append(f"{item_id}: validity contract failed")
                break
    passed = not blockers
    return {
        "passed": passed,
        "state": "C10_PASSED" if passed else "HUMAN_VALIDATION_REQUIRED",
        "blockers": sorted(set(blockers)),
        "item_count": len(item_ids),
        "judgment_count": len(judgments),
        "adjudication_count": len(adjudications),
        "certificate_hash": (
            content_hash(
                {
                    "items": sorted(item_ids),
                    "judgments": [
                        judgment.model_dump(mode="json") for judgment in judgments
                    ],
                    "adjudications": [
                        row.model_dump(mode="json") for row in adjudications
                    ],
                }
            )
            if passed
            else None
        ),
    }


__all__ = [
    "Adjudication",
    "Assignment",
    "AssignmentState",
    "DurableReviewStore",
    "EncryptedReviewStorage",
    "ExternalIdentityProvider",
    "IdentityProvider",
    "Judgment",
    "LocalDevelopmentIdentityProvider",
    "ReviewSession",
    "ReviewStore",
    "Reviewer",
    "ReviewerRole",
    "agreement_report",
    "assign_reviews",
    "evaluate_c10",
]
