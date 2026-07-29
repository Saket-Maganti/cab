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
    utc_now,
)


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
            "graph_hash": content_hash(self.export_public()),
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


def save_graph(graph: EvidenceGraph, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(graph.export_public(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


__all__ = [
    "CertificateType",
    "EdgeType",
    "EvidenceEdge",
    "EvidenceGraph",
    "EvidenceNode",
    "NodeType",
    "ResultRegistry",
    "compile_claim",
    "issue_certificate",
    "model_card_template",
    "save_graph",
    "verify_certificate",
]
