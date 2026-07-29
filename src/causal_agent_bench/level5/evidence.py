"""Claim-to-evidence graph, certificates, model cards, and result corrections."""

from __future__ import annotations

import hashlib
import hmac
import json
from collections import defaultdict, deque
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from causal_agent_bench.level5.core import (
    EvidenceClass,
    canonical_json,
    content_hash,
    redact_sensitive,
    reject_private_fields,
    utc_now,
)
from causal_agent_bench.level5.registry import SQLiteRegistry
from causal_agent_bench.level5.signing import Signer, Verifier


class NodeType(StrEnum):
    TASK_VERSION = "task_version"
    REVIEW = "review"
    C10_DECISION = "c10_decision"
    SPLIT_LOCK = "split_lock"
    MODEL_VERSION = "model_version"
    POLICY_VERSION = "policy_version"
    RUN = "run"
    SHARD = "shard"
    RAW_TRAJECTORY = "raw_trajectory"
    SCORE = "score"
    AUDIT = "audit"
    ANALYSIS = "analysis"
    FIGURE = "figure"
    TABLE = "table"
    CLAIM = "claim"
    RELEASE = "release"


class EdgeType(StrEnum):
    GENERATED_FROM = "generated_from"
    SCORED_BY = "scored_by"
    REVIEWED_BY = "reviewed_by"
    AUDITED_BY = "audited_by"
    ANALYSED_BY = "analysed_by"
    SUPPORTS = "supports"
    INVALIDATES = "invalidates"
    SUPERSEDES = "supersedes"
    REPRODUCED_BY = "reproduced_by"


EVIDENCE_TRANSITIONS: dict[EvidenceClass, frozenset[EvidenceClass]] = {
    EvidenceClass.DESIGN_ONLY: frozenset(
        {EvidenceClass.ENGINEERING_ONLY, EvidenceClass.HUMAN_INPUT_REQUIRED}
    ),
    EvidenceClass.ENGINEERING_ONLY: frozenset(
        {EvidenceClass.FIXTURE_ONLY, EvidenceClass.HUMAN_INPUT_REQUIRED}
    ),
    EvidenceClass.FIXTURE_ONLY: frozenset({EvidenceClass.HUMAN_INPUT_REQUIRED}),
    EvidenceClass.HUMAN_INPUT_REQUIRED: frozenset({EvidenceClass.EXECUTION_PENDING}),
    EvidenceClass.EXECUTION_PENDING: frozenset(
        {EvidenceClass.PRELIMINARY_REAL_EVIDENCE}
    ),
    EvidenceClass.PRELIMINARY_REAL_EVIDENCE: frozenset(
        {EvidenceClass.AUDITED_REAL_EVIDENCE}
    ),
    EvidenceClass.AUDITED_REAL_EVIDENCE: frozenset(
        {EvidenceClass.PAPER_ELIGIBLE_EVIDENCE}
    ),
    EvidenceClass.PAPER_ELIGIBLE_EVIDENCE: frozenset(),
}


class EvidenceNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node_id: str
    node_type: NodeType
    content_hash: str = Field(min_length=32)
    evidence_class: EvidenceClass
    public: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str


class EvidenceEdge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    edge_id: str
    source: str
    target: str
    relation: EdgeType
    created_at: str


class EvidenceGraph:
    def __init__(self) -> None:
        self.nodes: dict[str, EvidenceNode] = {}
        self.edges: dict[str, EvidenceEdge] = {}

    def add_node(
        self,
        node_id: str,
        node_type: NodeType,
        payload_hash: str,
        evidence_class: EvidenceClass,
        *,
        public: bool = True,
        metadata: dict[str, Any] | None = None,
    ) -> EvidenceNode:
        node = EvidenceNode(
            node_id=node_id,
            node_type=node_type,
            content_hash=payload_hash,
            evidence_class=evidence_class,
            public=public,
            metadata=metadata or {},
            created_at=utc_now(),
        )
        existing = self.nodes.get(node_id)
        if existing:
            unchanged = (
                existing.node_type == node.node_type
                and existing.content_hash == node.content_hash
                and existing.evidence_class == node.evidence_class
                and existing.public == node.public
                and existing.metadata == node.metadata
            )
            if not unchanged:
                raise ValueError(f"immutable node conflict: {node_id}")
            return existing
        self.nodes[node_id] = node
        return self.nodes[node_id]

    def add_edge(self, source: str, target: str, relation: EdgeType) -> EvidenceEdge:
        if source not in self.nodes or target not in self.nodes:
            missing = [node for node in (source, target) if node not in self.nodes]
            raise ValueError(f"missing evidence parent/node: {missing}")
        payload = {"source": source, "target": target, "relation": relation.value}
        edge_id = f"edge.{content_hash(payload)[:24]}"
        edge = EvidenceEdge(
            edge_id=edge_id,
            source=source,
            target=target,
            relation=relation,
            created_at=utc_now(),
        )
        self.edges[edge_id] = edge
        if self._has_cycle():
            del self.edges[edge_id]
            raise ValueError("evidence graph cycle detected")
        return edge

    def transition(self, node_id: str, target: EvidenceClass) -> EvidenceNode:
        node = self.nodes[node_id]
        if target not in EVIDENCE_TRANSITIONS[node.evidence_class]:
            raise ValueError(
                "invalid evidence transition: "
                f"{node.evidence_class.value} -> {target.value}"
            )
        updated = node.model_copy(update={"evidence_class": target})
        self.nodes[node_id] = updated
        return updated

    def lineage(self, node_id: str) -> list[str]:
        if node_id not in self.nodes:
            raise KeyError(node_id)
        parents: dict[str, list[str]] = defaultdict(list)
        for edge in self.edges.values():
            parents[edge.target].append(edge.source)
        seen: set[str] = set()
        queue = deque([node_id])
        while queue:
            current = queue.popleft()
            for parent in parents[current]:
                if parent not in seen:
                    seen.add(parent)
                    queue.append(parent)
        return sorted(seen)

    def export_public(self) -> dict[str, Any]:
        public_ids = {node_id for node_id, node in self.nodes.items() if node.public}
        return {
            "schema_version": "1.0",
            "nodes": [
                redact_sensitive(node.model_dump(mode="json"))
                for node_id, node in sorted(self.nodes.items())
                if node_id in public_ids
            ],
            "redacted_node_count": len(self.nodes) - len(public_ids),
            "edges": [
                edge.model_dump(mode="json")
                for edge in sorted(self.edges.values(), key=lambda row: row.edge_id)
                if edge.source in public_ids and edge.target in public_ids
            ],
        }

    def verify(self) -> dict[str, Any]:
        errors: list[str] = []
        for edge in self.edges.values():
            if edge.source not in self.nodes or edge.target not in self.nodes:
                errors.append(f"edge {edge.edge_id} has missing endpoint")
        if self._has_cycle():
            errors.append("cycle detected")
        return {
            "passed": not errors,
            "errors": errors,
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
            "graph_hash": content_hash(
                {
                    "nodes": [
                        {
                            "node_id": node.node_id,
                            "node_type": node.node_type.value,
                            "content_hash": node.content_hash,
                            "evidence_class": node.evidence_class.value,
                            "public": node.public,
                            "metadata": node.metadata,
                        }
                        for node in sorted(
                            self.nodes.values(),
                            key=lambda value: value.node_id,
                        )
                    ],
                    "edges": [
                        {
                            "edge_id": edge.edge_id,
                            "source": edge.source,
                            "target": edge.target,
                            "relation": edge.relation.value,
                        }
                        for edge in sorted(
                            self.edges.values(),
                            key=lambda value: value.edge_id,
                        )
                    ],
                }
            ),
        }

    def _has_cycle(self) -> bool:
        adjacency: dict[str, list[str]] = defaultdict(list)
        indegree = dict.fromkeys(self.nodes, 0)
        for edge in self.edges.values():
            adjacency[edge.source].append(edge.target)
            indegree[edge.target] = indegree.get(edge.target, 0) + 1
        queue = deque(node for node, degree in indegree.items() if degree == 0)
        visited = 0
        while queue:
            node = queue.popleft()
            visited += 1
            for child in adjacency[node]:
                indegree[child] -= 1
                if indegree[child] == 0:
                    queue.append(child)
        return visited != len(indegree)


class CertificateType(StrEnum):
    TASK_VALIDITY = "task_validity"
    SPLIT_INTEGRITY = "split_integrity"
    RUN_INTEGRITY = "run_integrity"
    SCORER_AUDIT = "scorer_audit"
    ANALYSIS_REPRODUCIBILITY = "analysis_reproducibility"
    MODEL_ROBUSTNESS_PROFILE = "model_robustness_profile"
    PAPER_ASSET_ELIGIBILITY = "paper_asset_eligibility"
    RELEASE_REPRODUCIBILITY = "release_reproducibility"


def issue_certificate(
    certificate_type: CertificateType,
    subject_id: str,
    evidence_nodes: list[EvidenceNode],
    *,
    issuer: str = "cab-foundation-fixture",
    signing_key: bytes = b"cab-certificate-development-fixture",
) -> dict[str, Any]:
    classes = {node.evidence_class for node in evidence_nodes}
    unsigned = {
        "schema_version": "1.0",
        "certificate_type": certificate_type.value,
        "subject_id": subject_id,
        "issuer": issuer,
        "evidence_node_ids": sorted(node.node_id for node in evidence_nodes),
        "evidence_classes": sorted(value.value for value in classes),
        "scientific_claim": False,
        "created_at": utc_now(),
    }
    certificate_id = f"cert.{content_hash(unsigned)[:24]}"
    signature = hmac.new(
        signing_key, canonical_json(unsigned).encode("utf-8"), hashlib.sha256
    ).hexdigest()
    return {**unsigned, "certificate_id": certificate_id, "signature": signature}


def verify_certificate(
    certificate: dict[str, Any],
    *,
    signing_key: bytes = b"cab-certificate-development-fixture",
) -> bool:
    unsigned = {
        key: value
        for key, value in certificate.items()
        if key not in {"certificate_id", "signature"}
    }
    expected_id = f"cert.{content_hash(unsigned)[:24]}"
    expected_signature = hmac.new(
        signing_key, canonical_json(unsigned).encode("utf-8"), hashlib.sha256
    ).hexdigest()
    return certificate.get("certificate_id") == expected_id and hmac.compare_digest(
        str(certificate.get("signature", "")), expected_signature
    )


def compile_claim(
    claim_id: str,
    required_node_types: set[NodeType],
    support_nodes: list[EvidenceNode],
) -> dict[str, Any]:
    observed_types = {node.node_type for node in support_nodes}
    missing = sorted(value.value for value in required_node_types - observed_types)
    ineligible = sorted(
        node.node_id
        for node in support_nodes
        if node.evidence_class is not EvidenceClass.PAPER_ELIGIBLE_EVIDENCE
    )
    return {
        "claim_id": claim_id,
        "eligible": not missing and not ineligible,
        "missing_node_types": missing,
        "ineligible_evidence_nodes": ineligible,
        "support_node_ids": sorted(node.node_id for node in support_nodes),
    }


def model_card_template(model_id: str, revision: str) -> dict[str, Any]:
    blocked = "BLOCKED_PENDING_AUDITED_REAL_EVIDENCE"
    return {
        "model_id": model_id,
        "revision": revision,
        "tool_adapter": blocked,
        "policy": blocked,
        "task_versions": [],
        "clean_success": blocked,
        "paired_robustness": blocked,
        "recovery": blocked,
        "abstention": blocked,
        "false_abstention": blocked,
        "worst_family": blocked,
        "uncertainty": blocked,
        "overhead": blocked,
        "missingness": blocked,
        "scorer_audit": blocked,
        "limitations": ["No audited real model evidence is registered."],
        "evidence_status": "EXECUTION_PENDING",
    }


class ResultRegistry:
    """Versioned public-safe result records with corrections and withdrawal."""

    def __init__(self) -> None:
        self._records: dict[str, dict[str, Any]] = {}

    def add(self, result_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        if result_id in self._records:
            raise ValueError(f"result already exists: {result_id}")
        record = {
            "result_id": result_id,
            "version": 1,
            "status": "ACTIVE",
            "payload": payload,
            "created_at": utc_now(),
            "supersedes": None,
        }
        self._records[result_id] = record
        return record

    def correct(
        self, result_id: str, corrected_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        original = self._records[result_id]
        original["status"] = "SUPERSEDED"
        corrected = self.add(corrected_id, payload)
        corrected["version"] = int(original["version"]) + 1
        corrected["supersedes"] = result_id
        return corrected

    def withdraw(self, result_id: str, *, reason: str) -> dict[str, Any]:
        record = self._records[result_id]
        record["status"] = "WITHDRAWN"
        record["withdrawal_reason"] = reason
        return record

    def export(self) -> list[dict[str, Any]]:
        return [self._records[key] for key in sorted(self._records)]


def _append_transparency(
    connection: Any,
    *,
    event_type: str,
    subject_id: str,
    payload_hash: str,
) -> dict[str, Any]:
    previous = connection.execute(
        "SELECT current_hash FROM transparency_log ORDER BY sequence DESC LIMIT 1"
    ).fetchone()
    previous_hash = str(previous["current_hash"]) if previous else "0" * 64
    created_at = utc_now()
    current_hash = content_hash(
        {
            "previous_hash": previous_hash,
            "event_type": event_type,
            "subject_id": subject_id,
            "payload_hash": payload_hash,
            "created_at": created_at,
        }
    )
    connection.execute(
        """
        INSERT INTO transparency_log(
            previous_hash, current_hash, event_type, subject_id,
            payload_hash, created_at
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            previous_hash,
            current_hash,
            event_type,
            subject_id,
            payload_hash,
            created_at,
        ),
    )
    sequence = int(connection.execute("SELECT last_insert_rowid()").fetchone()[0])
    return {
        "sequence": sequence,
        "previous_hash": previous_hash,
        "current_hash": current_hash,
        "event_type": event_type,
        "subject_id": subject_id,
        "payload_hash": payload_hash,
        "created_at": created_at,
    }


def verify_transparency_log(registry: SQLiteRegistry) -> dict[str, Any]:
    with registry._connect() as connection:
        rows = connection.execute(
            "SELECT * FROM transparency_log ORDER BY sequence"
        ).fetchall()
    errors: list[str] = []
    previous_hash = "0" * 64
    for expected_sequence, row in enumerate(rows, start=1):
        payload = {
            "previous_hash": previous_hash,
            "event_type": str(row["event_type"]),
            "subject_id": str(row["subject_id"]),
            "payload_hash": str(row["payload_hash"]),
            "created_at": str(row["created_at"]),
        }
        expected_hash = content_hash(payload)
        if int(row["sequence"]) != expected_sequence:
            errors.append(f"transparency sequence gap at {expected_sequence}")
        if str(row["previous_hash"]) != previous_hash:
            errors.append(f"transparency previous hash mismatch at {expected_sequence}")
        if str(row["current_hash"]) != expected_hash:
            errors.append(f"transparency current hash mismatch at {expected_sequence}")
        previous_hash = str(row["current_hash"])
    return {
        "passed": not errors,
        "entry_count": len(rows),
        "head_hash": previous_hash,
        "errors": errors,
    }


class PersistentEvidenceGraph:
    """Durable acyclic evidence graph integrated with the canonical registry."""

    def __init__(self, registry: SQLiteRegistry) -> None:
        self.registry = registry
        self.registry.initialize()

    @staticmethod
    def _node_from_row(row: Any) -> EvidenceNode:
        return EvidenceNode(
            node_id=str(row["node_id"]),
            node_type=NodeType(str(row["node_type"])),
            content_hash=str(row["content_hash"]),
            evidence_class=EvidenceClass(str(row["evidence_class"])),
            public=bool(row["public"]),
            metadata=json.loads(str(row["metadata_json"])),
            created_at=str(row["created_at"]),
        )

    def add_node(
        self,
        node_id: str,
        node_type: NodeType,
        payload_hash: str,
        evidence_class: EvidenceClass,
        *,
        public: bool = True,
        metadata: dict[str, Any] | None = None,
    ) -> EvidenceNode:
        metadata = metadata or {}
        if evidence_class in {
            EvidenceClass.AUDITED_REAL_EVIDENCE,
            EvidenceClass.PAPER_ELIGIBLE_EVIDENCE,
        }:
            raise ValueError(
                "audited and paper-eligible evidence must be reached through "
                "a certified atomic transition"
            )
        if public:
            reject_private_fields(metadata)
        metadata_json = canonical_json(metadata)
        metadata_hash = content_hash(metadata)
        now = utc_now()
        with self.registry.transaction() as connection:
            existing = connection.execute(
                "SELECT * FROM evidence_nodes WHERE node_id=?",
                (node_id,),
            ).fetchone()
            if existing:
                node = self._node_from_row(existing)
                if (
                    node.node_type != node_type
                    or node.content_hash != payload_hash
                    or node.evidence_class != evidence_class
                    or node.public != public
                    or node.metadata != metadata
                ):
                    raise ValueError(f"immutable evidence node conflict: {node_id}")
                return node
            connection.execute(
                """
                INSERT INTO evidence_nodes(
                    node_id, node_type, content_hash, node_version,
                    evidence_class, public, metadata_json, metadata_hash,
                    created_at, updated_at
                ) VALUES (?, ?, ?, 1, ?, ?, ?, ?, ?, ?)
                """,
                (
                    node_id,
                    node_type.value,
                    payload_hash,
                    evidence_class.value,
                    int(public),
                    metadata_json,
                    metadata_hash,
                    now,
                    now,
                ),
            )
            _append_transparency(
                connection,
                event_type="EVIDENCE_NODE_ADDED",
                subject_id=node_id,
                payload_hash=payload_hash,
            )
        return EvidenceNode(
            node_id=node_id,
            node_type=node_type,
            content_hash=payload_hash,
            evidence_class=evidence_class,
            public=public,
            metadata=metadata,
            created_at=now,
        )

    def get_node(self, node_id: str) -> EvidenceNode | None:
        with self.registry._connect() as connection:
            row = connection.execute(
                "SELECT * FROM evidence_nodes WHERE node_id=?",
                (node_id,),
            ).fetchone()
        return self._node_from_row(row) if row is not None else None

    def _load_graph(self, connection: Any) -> EvidenceGraph:
        graph = EvidenceGraph()
        for row in connection.execute("SELECT * FROM evidence_nodes"):
            node = self._node_from_row(row)
            graph.nodes[node.node_id] = node
        for row in connection.execute("SELECT * FROM evidence_edges"):
            edge = EvidenceEdge(
                edge_id=str(row["edge_id"]),
                source=str(row["source_id"]),
                target=str(row["target_id"]),
                relation=EdgeType(str(row["relation"])),
                created_at=str(row["created_at"]),
            )
            graph.edges[edge.edge_id] = edge
        return graph

    def add_edge(self, source: str, target: str, relation: EdgeType) -> EvidenceEdge:
        payload = {"source": source, "target": target, "relation": relation.value}
        edge_id = f"edge.{content_hash(payload)[:24]}"
        now = utc_now()
        with self.registry.transaction() as connection:
            existing = connection.execute(
                "SELECT * FROM evidence_edges WHERE edge_id=?",
                (edge_id,),
            ).fetchone()
            if existing:
                return EvidenceEdge(
                    edge_id=edge_id,
                    source=source,
                    target=target,
                    relation=relation,
                    created_at=str(existing["created_at"]),
                )
            for node_id in (source, target):
                if not connection.execute(
                    "SELECT 1 FROM evidence_nodes WHERE node_id=?",
                    (node_id,),
                ).fetchone():
                    raise ValueError(f"missing evidence parent/node: {node_id}")
            connection.execute(
                """
                INSERT INTO evidence_edges(
                    edge_id, source_id, target_id, relation, created_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (edge_id, source, target, relation.value, now),
            )
            graph = self._load_graph(connection)
            if graph._has_cycle():
                raise ValueError("evidence graph cycle detected")
            _append_transparency(
                connection,
                event_type="EVIDENCE_EDGE_ADDED",
                subject_id=edge_id,
                payload_hash=content_hash(payload),
            )
        return EvidenceEdge(
            edge_id=edge_id,
            source=source,
            target=target,
            relation=relation,
            created_at=now,
        )

    def transition(
        self,
        node_id: str,
        target: EvidenceClass,
        *,
        audit_node_ids: list[str] | None = None,
        certificate_ids: list[str] | None = None,
    ) -> EvidenceNode:
        audit_node_ids = audit_node_ids or []
        certificate_ids = certificate_ids or []
        with self.registry.transaction() as connection:
            row = connection.execute(
                "SELECT * FROM evidence_nodes WHERE node_id=?",
                (node_id,),
            ).fetchone()
            if row is None:
                raise KeyError(node_id)
            node = self._node_from_row(row)
            if target not in EVIDENCE_TRANSITIONS[node.evidence_class]:
                raise ValueError(
                    "invalid evidence transition: "
                    f"{node.evidence_class.value} -> {target.value}"
                )
            if target in {
                EvidenceClass.AUDITED_REAL_EVIDENCE,
                EvidenceClass.PAPER_ELIGIBLE_EVIDENCE,
            }:
                if not audit_node_ids or not certificate_ids:
                    raise ValueError(
                        "audited and paper-eligible transitions require audits and certificates"
                    )
                placeholders = ",".join("?" for _ in audit_node_ids)
                audit_rows = connection.execute(
                    f"SELECT node_id, node_type FROM evidence_nodes "
                    f"WHERE node_id IN ({placeholders})",
                    tuple(audit_node_ids),
                ).fetchall()
                if len(audit_rows) != len(set(audit_node_ids)) or any(
                    str(value["node_type"]) != NodeType.AUDIT.value
                    for value in audit_rows
                ):
                    raise ValueError("required audit evidence is missing or invalid")
                cert_placeholders = ",".join("?" for _ in certificate_ids)
                cert_rows = connection.execute(
                    f"SELECT certificate_id FROM certificates "
                    f"WHERE certificate_id IN ({cert_placeholders})",
                    tuple(certificate_ids),
                ).fetchall()
                revoked = connection.execute(
                    f"SELECT certificate_id FROM certificate_revocations "
                    f"WHERE certificate_id IN ({cert_placeholders})",
                    tuple(certificate_ids),
                ).fetchall()
                if len(cert_rows) != len(set(certificate_ids)) or revoked:
                    raise ValueError("required certificate is missing or revoked")
            policy_hash = content_hash(
                {
                    "source": node.evidence_class.value,
                    "target": target.value,
                    "audits": sorted(audit_node_ids),
                    "certificates": sorted(certificate_ids),
                }
            )
            created_at = utc_now()
            history_id = f"history.{content_hash([node_id, policy_hash, created_at])[:24]}"
            event_hash = content_hash(
                {
                    "history_id": history_id,
                    "node_id": node_id,
                    "source": node.evidence_class.value,
                    "target": target.value,
                    "policy_hash": policy_hash,
                }
            )
            connection.execute(
                """
                INSERT INTO evidence_state_history(
                    history_id, node_id, source_class, target_class,
                    policy_hash, event_hash, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    history_id,
                    node_id,
                    node.evidence_class.value,
                    target.value,
                    policy_hash,
                    event_hash,
                    created_at,
                ),
            )
            connection.execute(
                """
                UPDATE evidence_nodes
                   SET evidence_class=?, node_version=node_version+1, updated_at=?
                 WHERE node_id=?
                """,
                (target.value, created_at, node_id),
            )
            _append_transparency(
                connection,
                event_type="EVIDENCE_TRANSITION",
                subject_id=node_id,
                payload_hash=event_hash,
            )
            updated = connection.execute(
                "SELECT * FROM evidence_nodes WHERE node_id=?",
                (node_id,),
            ).fetchone()
        return self._node_from_row(updated)

    def lineage(self, node_id: str) -> list[str]:
        with self.registry._connect() as connection:
            if not connection.execute(
                "SELECT 1 FROM evidence_nodes WHERE node_id=?",
                (node_id,),
            ).fetchone():
                raise KeyError(node_id)
            rows = connection.execute(
                """
                WITH RECURSIVE lineage(node_id) AS (
                    SELECT source_id FROM evidence_edges WHERE target_id=?
                    UNION
                    SELECT e.source_id
                      FROM evidence_edges e
                      JOIN lineage l ON e.target_id=l.node_id
                )
                SELECT node_id FROM lineage ORDER BY node_id
                """,
                (node_id,),
            ).fetchall()
        return [str(row["node_id"]) for row in rows]

    def export_public(self) -> dict[str, Any]:
        with self.registry._connect() as connection:
            node_rows = connection.execute(
                "SELECT * FROM evidence_nodes ORDER BY node_id"
            ).fetchall()
            public_ids = {
                str(row["node_id"]) for row in node_rows if bool(row["public"])
            }
            edges = connection.execute(
                "SELECT * FROM evidence_edges ORDER BY edge_id"
            ).fetchall()
        return {
            "schema_version": "2.0",
            "nodes": [
                redact_sensitive(self._node_from_row(row).model_dump(mode="json"))
                for row in node_rows
                if str(row["node_id"]) in public_ids
            ],
            "redacted_node_count": len(node_rows) - len(public_ids),
            "edges": [
                {
                    "edge_id": str(row["edge_id"]),
                    "source": str(row["source_id"]),
                    "target": str(row["target_id"]),
                    "relation": str(row["relation"]),
                    "created_at": str(row["created_at"]),
                }
                for row in edges
                if str(row["source_id"]) in public_ids
                and str(row["target_id"]) in public_ids
            ],
            "transparency": verify_transparency_log(self.registry),
        }

    def import_graph(self, payload: dict[str, Any]) -> dict[str, int]:
        node_count = 0
        edge_count = 0
        for raw in payload.get("nodes", []):
            node = EvidenceNode.model_validate(raw)
            self.add_node(
                node.node_id,
                node.node_type,
                node.content_hash,
                node.evidence_class,
                public=node.public,
                metadata=node.metadata,
            )
            node_count += 1
        for raw in payload.get("edges", []):
            edge = EvidenceEdge.model_validate(raw)
            self.add_edge(edge.source, edge.target, edge.relation)
            edge_count += 1
        return {"nodes_imported": node_count, "edges_imported": edge_count}

    def verify(self) -> dict[str, Any]:
        errors: list[str] = []
        with self.registry._connect() as connection:
            graph = self._load_graph(connection)
            for row in connection.execute("SELECT * FROM evidence_nodes"):
                metadata = json.loads(str(row["metadata_json"]))
                if content_hash(metadata) != str(row["metadata_hash"]):
                    errors.append(f"metadata hash mismatch: {row['node_id']}")
            history = connection.execute(
                "SELECT * FROM evidence_state_history ORDER BY created_at"
            ).fetchall()
        graph_report = graph.verify()
        errors.extend(graph_report["errors"])
        transparency = verify_transparency_log(self.registry)
        errors.extend(transparency["errors"])
        return {
            "passed": not errors,
            "errors": errors,
            "node_count": len(graph.nodes),
            "edge_count": len(graph.edges),
            "transition_count": len(history),
            "graph_hash": graph_report["graph_hash"],
            "transparency": transparency,
        }


class CertificateRepository:
    def __init__(self, registry: SQLiteRegistry) -> None:
        self.registry = registry
        self.registry.initialize()

    def issue(
        self,
        certificate_type: CertificateType,
        subject_id: str,
        evidence_node_ids: list[str],
        *,
        signer: Signer,
        expires_at: str | None = None,
        public: bool = True,
        protected_mode: bool = False,
    ) -> dict[str, Any]:
        if protected_mode and signer.development_only:
            raise PermissionError("protected certificates reject development signers")
        with self.registry.transaction() as connection:
            placeholders = ",".join("?" for _ in evidence_node_ids)
            nodes = connection.execute(
                f"SELECT node_id, evidence_class FROM evidence_nodes "
                f"WHERE node_id IN ({placeholders})",
                tuple(evidence_node_ids),
            ).fetchall()
            if len(nodes) != len(set(evidence_node_ids)):
                raise ValueError("certificate supporting evidence is missing")
            issued_at = utc_now()
            unsigned = {
                "schema_version": "2.0",
                "certificate_type": certificate_type.value,
                "subject_id": subject_id,
                "supporting_evidence": sorted(evidence_node_ids),
                "evidence_classes": sorted(
                    {str(row["evidence_class"]) for row in nodes}
                ),
                "signer_key_id": signer.key_id,
                "signature_algorithm": signer.algorithm,
                "issued_at": issued_at,
                "expires_at": expires_at,
                "status": "ACTIVE",
                "public": public,
                "scientific_claim": False,
            }
            certificate_id = f"cert.{content_hash(unsigned)[:24]}"
            signed = {**unsigned, "certificate_id": certificate_id}
            signature = signer.sign(canonical_json(signed).encode("utf-8"))
            certificate = {**signed, "signature": signature}
            connection.execute(
                """
                INSERT INTO certificates(
                    certificate_id, certificate_type, subject_id,
                    supporting_evidence_json, signer_key_id, issued_at, expires_at,
                    certificate_status, payload_json, payload_hash, signature, public
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'ACTIVE', ?, ?, ?, ?)
                """,
                (
                    certificate_id,
                    certificate_type.value,
                    subject_id,
                    canonical_json(sorted(evidence_node_ids)),
                    signer.key_id,
                    issued_at,
                    expires_at,
                    canonical_json(certificate),
                    content_hash(certificate),
                    signature,
                    int(public),
                ),
            )
            _append_transparency(
                connection,
                event_type="CERTIFICATE_ISSUED",
                subject_id=certificate_id,
                payload_hash=content_hash(certificate),
            )
        return certificate

    def verify(self, certificate_id: str, *, verifier: Verifier) -> dict[str, Any]:
        with self.registry._connect() as connection:
            row = connection.execute(
                "SELECT * FROM certificates WHERE certificate_id=?",
                (certificate_id,),
            ).fetchone()
            revoked = connection.execute(
                "SELECT * FROM certificate_revocations WHERE certificate_id=?",
                (certificate_id,),
            ).fetchone()
        if row is None:
            return {"passed": False, "errors": ["certificate missing"]}
        certificate = json.loads(str(row["payload_json"]))
        unsigned = {key: value for key, value in certificate.items() if key != "signature"}
        errors: list[str] = []
        if content_hash(certificate) != str(row["payload_hash"]):
            errors.append("certificate payload hash mismatch")
        if str(row["signer_key_id"]) != verifier.key_id:
            errors.append("certificate signer key mismatch")
        signature = certificate.get("signature") if isinstance(certificate, dict) else None
        if not isinstance(signature, str) or not verifier.verify(
            canonical_json(unsigned).encode("utf-8"),
            signature,
        ):
            errors.append("certificate signature invalid")
        if revoked:
            errors.append(f"certificate revoked: {revoked['reason']}")
        return {
            "passed": not errors,
            "certificate_id": certificate_id,
            "revoked": bool(revoked),
            "errors": errors,
        }

    def revoke(
        self,
        certificate_id: str,
        *,
        reason: str,
        superseding_certificate_id: str | None = None,
    ) -> str:
        if not reason.strip():
            raise ValueError("certificate revocation reason is required")
        revocation_id = f"cert-revocation.{content_hash([certificate_id, reason])[:24]}"
        with self.registry.transaction() as connection:
            if not connection.execute(
                "SELECT 1 FROM certificates WHERE certificate_id=?",
                (certificate_id,),
            ).fetchone():
                raise KeyError(certificate_id)
            connection.execute(
                """
                INSERT INTO certificate_revocations(
                    revocation_id, certificate_id, reason,
                    superseding_certificate_id, revoked_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    revocation_id,
                    certificate_id,
                    reason,
                    superseding_certificate_id,
                    utc_now(),
                ),
            )
            _append_transparency(
                connection,
                event_type="CERTIFICATE_REVOKED",
                subject_id=certificate_id,
                payload_hash=content_hash(
                    [revocation_id, reason, superseding_certificate_id]
                ),
            )
        return revocation_id

    def list(self) -> list[dict[str, Any]]:
        with self.registry._connect() as connection:
            rows = connection.execute(
                """
                SELECT c.*, r.reason AS revocation_reason, r.revoked_at
                  FROM certificates c
                  LEFT JOIN certificate_revocations r
                    ON r.certificate_id=c.certificate_id
                 ORDER BY c.certificate_id
                """
            ).fetchall()
        return [
            {
                **json.loads(str(row["payload_json"])),
                "effective_status": "REVOKED"
                if row["revocation_reason"]
                else "ACTIVE",
                "revocation_reason": row["revocation_reason"],
                "revoked_at": row["revoked_at"],
            }
            for row in rows
        ]

    def transparency_verify(self) -> dict[str, Any]:
        return verify_transparency_log(self.registry)


class PersistentResultRegistry:
    """Durable results whose correction history is append-only."""

    def __init__(self, registry: SQLiteRegistry) -> None:
        self.registry = registry
        self.registry.initialize()

    def add(self, result_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        reject_private_fields(payload)
        now = utc_now()
        record = {
            "result_id": result_id,
            "payload": payload,
            "payload_hash": content_hash(payload),
            "status": "ACTIVE",
            "version": 1,
            "supersedes_result_id": None,
            "created_at": now,
        }
        with self.registry.transaction() as connection:
            connection.execute(
                """
                INSERT INTO evaluation_results(
                    result_id, payload_json, payload_hash, status,
                    version, supersedes_result_id, created_at
                ) VALUES (?, ?, ?, 'ACTIVE', 1, NULL, ?)
                """,
                (result_id, canonical_json(payload), record["payload_hash"], now),
            )
            _append_transparency(
                connection,
                event_type="RESULT_ADDED",
                subject_id=result_id,
                payload_hash=str(record["payload_hash"]),
            )
        return record

    def correct(
        self,
        original_result_id: str,
        corrected_result_id: str,
        payload: dict[str, Any],
        *,
        reason: str,
        reviewer_id: str,
        public_notice: str,
    ) -> dict[str, Any]:
        reject_private_fields(payload)
        with self.registry.transaction() as connection:
            original = connection.execute(
                "SELECT * FROM evaluation_results WHERE result_id=?",
                (original_result_id,),
            ).fetchone()
            if original is None:
                raise KeyError(original_result_id)
            version = int(original["version"]) + 1
            now = utc_now()
            payload_hash = content_hash(payload)
            connection.execute(
                """
                INSERT INTO evaluation_results(
                    result_id, payload_json, payload_hash, status,
                    version, supersedes_result_id, created_at
                ) VALUES (?, ?, ?, 'ACTIVE', ?, ?, ?)
                """,
                (
                    corrected_result_id,
                    canonical_json(payload),
                    payload_hash,
                    version,
                    original_result_id,
                    now,
                ),
            )
            correction_id = (
                f"correction.{content_hash([original_result_id, corrected_result_id, reason])[:24]}"
            )
            connection.execute(
                """
                INSERT INTO result_corrections(
                    correction_id, original_result_id, corrected_result_id,
                    reason, reviewer_hash, public_notice, action, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, 'CORRECT', ?)
                """,
                (
                    correction_id,
                    original_result_id,
                    corrected_result_id,
                    reason,
                    content_hash(reviewer_id),
                    public_notice,
                    now,
                ),
            )
            _append_transparency(
                connection,
                event_type="RESULT_CORRECTED",
                subject_id=corrected_result_id,
                payload_hash=content_hash([correction_id, payload_hash]),
            )
        return {
            "result_id": corrected_result_id,
            "version": version,
            "supersedes_result_id": original_result_id,
            "payload": payload,
            "correction_id": correction_id,
        }

    def withdraw(
        self,
        result_id: str,
        *,
        reason: str,
        reviewer_id: str,
        public_notice: str,
    ) -> str:
        correction_id = f"correction.{content_hash([result_id, reason, 'withdraw'])[:24]}"
        with self.registry.transaction() as connection:
            if not connection.execute(
                "SELECT 1 FROM evaluation_results WHERE result_id=?",
                (result_id,),
            ).fetchone():
                raise KeyError(result_id)
            connection.execute(
                """
                INSERT INTO result_corrections(
                    correction_id, original_result_id, corrected_result_id,
                    reason, reviewer_hash, public_notice, action, created_at
                ) VALUES (?, ?, NULL, ?, ?, ?, 'WITHDRAW', ?)
                """,
                (
                    correction_id,
                    result_id,
                    reason,
                    content_hash(reviewer_id),
                    public_notice,
                    utc_now(),
                ),
            )
            _append_transparency(
                connection,
                event_type="RESULT_WITHDRAWN",
                subject_id=result_id,
                payload_hash=content_hash([correction_id, reason]),
            )
        return correction_id

    def history(self, result_id: str) -> dict[str, Any]:
        with self.registry._connect() as connection:
            records = connection.execute(
                """
                WITH RECURSIVE chain(result_id) AS (
                    SELECT ?
                    UNION ALL
                    SELECT r.result_id FROM evaluation_results r
                    JOIN chain c ON r.supersedes_result_id=c.result_id
                )
                SELECT * FROM evaluation_results
                WHERE result_id IN (SELECT result_id FROM chain)
                ORDER BY version, created_at
                """,
                (result_id,),
            ).fetchall()
            corrections = connection.execute(
                "SELECT * FROM result_corrections "
                "WHERE original_result_id=? OR corrected_result_id=? "
                "ORDER BY created_at",
                (result_id, result_id),
            ).fetchall()
        return {
            "records": [
                {
                    **dict(row),
                    "payload": json.loads(str(row["payload_json"])),
                }
                for row in records
            ],
            "corrections": [dict(row) for row in corrections],
        }


class ClaimRequirement(BaseModel):
    claim_id: str
    claim_text_hash: str
    required_node_types: set[NodeType]
    minimum_evidence_class: EvidenceClass
    common_support_required: bool = True
    scorer_audit_required: bool = True
    uncertainty_required: bool = True
    external_reproduction_required: bool = False
    invalidating_node_ids: set[str] = Field(default_factory=set)


EVIDENCE_RANK = {
    EvidenceClass.DESIGN_ONLY: 0,
    EvidenceClass.ENGINEERING_ONLY: 1,
    EvidenceClass.FIXTURE_ONLY: 2,
    EvidenceClass.HUMAN_INPUT_REQUIRED: 3,
    EvidenceClass.EXECUTION_PENDING: 4,
    EvidenceClass.PRELIMINARY_REAL_EVIDENCE: 5,
    EvidenceClass.AUDITED_REAL_EVIDENCE: 6,
    EvidenceClass.PAPER_ELIGIBLE_EVIDENCE: 7,
}


def compile_durable_claim(
    requirement: ClaimRequirement,
    graph: PersistentEvidenceGraph,
    support_node_ids: list[str],
) -> dict[str, Any]:
    with graph.registry._connect() as connection:
        placeholders = ",".join("?" for _ in support_node_ids)
        rows = (
            connection.execute(
                f"SELECT * FROM evidence_nodes WHERE node_id IN ({placeholders})",
                tuple(support_node_ids),
            ).fetchall()
            if support_node_ids
            else []
        )
        durable_graph = graph._load_graph(connection)
    nodes = [graph._node_from_row(row) for row in rows]
    observed_types = {node.node_type for node in nodes}
    missing_types = sorted(
        value.value for value in requirement.required_node_types - observed_types
    )
    below_minimum = sorted(
        node.node_id
        for node in nodes
        if EVIDENCE_RANK[node.evidence_class]
        < EVIDENCE_RANK[requirement.minimum_evidence_class]
    )
    invalidators = sorted(
        requirement.invalidating_node_ids & {node.node_id for node in nodes}
    )
    missing_prerequisites = []
    if requirement.scorer_audit_required and NodeType.AUDIT not in observed_types:
        missing_prerequisites.append("scorer audit")
    if requirement.uncertainty_required and not any(
        node.metadata.get("uncertainty_recorded") is True for node in nodes
    ):
        missing_prerequisites.append("uncertainty")
    if requirement.external_reproduction_required and not any(
        edge.relation is EdgeType.REPRODUCED_BY
        for edge in durable_graph.edges.values()
    ):
        missing_prerequisites.append("external reproduction")
    common_support = all(
        node.node_id in graph.lineage(support_node_ids[-1]) or node.node_id == support_node_ids[-1]
        for node in nodes
    ) if requirement.common_support_required and support_node_ids else True
    if not common_support:
        missing_prerequisites.append("common support")
    eligible = not (
        missing_types or below_minimum or invalidators or missing_prerequisites
    )
    return {
        "claim_id": requirement.claim_id,
        "claim_text_hash": requirement.claim_text_hash,
        "eligible": eligible,
        "support_node_ids": sorted(support_node_ids),
        "missing_node_types": missing_types,
        "below_minimum_evidence": below_minimum,
        "invalidating_nodes": invalidators,
        "missing_prerequisites": sorted(missing_prerequisites),
        "fixture_evidence_blocked": any(
            node.evidence_class is EvidenceClass.FIXTURE_ONLY for node in nodes
        ),
    }


def save_graph(graph: EvidenceGraph, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(graph.export_public(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


__all__ = [
    "EVIDENCE_RANK",
    "CertificateRepository",
    "CertificateType",
    "ClaimRequirement",
    "EdgeType",
    "EvidenceEdge",
    "EvidenceGraph",
    "EvidenceNode",
    "NodeType",
    "PersistentEvidenceGraph",
    "PersistentResultRegistry",
    "ResultRegistry",
    "compile_claim",
    "compile_durable_claim",
    "issue_certificate",
    "model_card_template",
    "save_graph",
    "verify_certificate",
    "verify_transparency_log",
]
