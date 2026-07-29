"""Safe, provider-free adversarial fixtures for the hardened Level-5 boundary."""

from __future__ import annotations

import sqlite3
import tempfile
from collections.abc import Callable
from enum import StrEnum
from pathlib import Path
from typing import Any

from causal_agent_bench.level5.benchmark import ToolSpec
from causal_agent_bench.level5.core import EvidenceClass, content_hash, utc_now
from causal_agent_bench.level5.evaluator import (
    ArchiveMember,
    SubmissionManifest,
    audit_output,
    inspect_submission,
)
from causal_agent_bench.level5.evidence import (
    CertificateRepository,
    CertificateType,
    NodeType,
    PersistentEvidenceGraph,
    PersistentResultRegistry,
)
from causal_agent_bench.level5.execution import ContentAddressedStore
from causal_agent_bench.level5.plugins import (
    PluginManager,
    PluginMetadata,
    PluginType,
)
from causal_agent_bench.level5.registry import SQLiteRegistry
from causal_agent_bench.level5.reliability import run_fixture_chaos_campaign
from causal_agent_bench.level5.review import DurableReviewStore, ReviewerRole
from causal_agent_bench.level5.signing import (
    FixtureHMACSigner,
    FixtureHMACVerifier,
)


class RedTeamOutcome(StrEnum):
    PREVENTED = "PREVENTED"
    DETECTED = "DETECTED"
    CONTAINED = "CONTAINED"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    NOT_MITIGATED = "NOT_MITIGATED"
    NOT_EXECUTED = "NOT_EXECUTED"
    ACCEPTED_RISK = "ACCEPTED_RISK"


def _submission() -> SubmissionManifest:
    return SubmissionManifest(
        submission_id="submission.redteam.fixture",
        package_hash=content_hash("redteam-package"),
        model_declaration="safe adversarial fixture",
        policy_declaration="fixture policy",
        runtime_image="cab/fixture:local",
        entry_point=["agent.py"],
        licence="MIT",
        authorship_attestation=True,
    )


def _case(
    attack: str,
    severity: str,
    exercise: Callable[[], tuple[RedTeamOutcome, dict[str, Any]]],
) -> dict[str, Any]:
    try:
        outcome, evidence = exercise()
        error = None
    except Exception as exc:  # an unexpected harness error is never a pass
        outcome = RedTeamOutcome.NOT_MITIGATED
        evidence = {}
        error = f"{type(exc).__name__}: {exc}"
    return {
        "attack": attack,
        "severity": severity,
        "outcome": outcome.value,
        "automatically_mitigated": outcome
        in {
            RedTeamOutcome.PREVENTED,
            RedTeamOutcome.DETECTED,
            RedTeamOutcome.CONTAINED,
        },
        "error": error,
        "evidence": evidence,
    }


def _archive_case(member: ArchiveMember, finding: str) -> tuple[RedTeamOutcome, dict[str, Any]]:
    report = inspect_submission(_submission(), [member])
    found = finding in {row["kind"] for row in report["findings"]}
    return (
        RedTeamOutcome.PREVENTED if found and not report["passed"] else RedTeamOutcome.NOT_MITIGATED,
        {"policy_hash": report["policy_hash"], "findings": report["findings"]},
    )


def _audit_case(text: str, finding: str, *, limit: int = 1024) -> tuple[RedTeamOutcome, dict[str, Any]]:
    report = audit_output(text, output_limit=limit)
    found = finding in {row["kind"] for row in report["findings"]}
    return (
        RedTeamOutcome.DETECTED if found else RedTeamOutcome.NOT_MITIGATED,
        {"findings": report["findings"], "output_bytes": report["output_bytes"]},
    )


def _manual_case(risk: str) -> tuple[RedTeamOutcome, dict[str, Any]]:
    return (
        RedTeamOutcome.MANUAL_REVIEW,
        {
            "review_checklist": [
                "inspect raw fixture evidence",
                "compare policy and prior decisions",
                "record independent human disposition",
            ],
            "evidence_packet": content_hash(["manual-redteam-fixture", risk]),
            "decision_state": "PENDING_GENUINE_HUMAN_REVIEW",
            "residual_risk": risk,
        },
    )


def run_hardening_redteam_campaign() -> dict[str, Any]:
    """Execute safe attack fixtures; never infer mitigation from declarations."""

    with tempfile.TemporaryDirectory(prefix="cab-redteam-") as temp_name:
        root = Path(temp_name)
        registry = SQLiteRegistry(root / "registry.sqlite3")
        registry.initialize()
        chaos = run_fixture_chaos_campaign(workdir=root / "chaos")
        chaos_by_fault = {row["fault"]: row for row in chaos["cases"]}

        def duplicate_result() -> tuple[RedTeamOutcome, dict[str, Any]]:
            results = PersistentResultRegistry(registry)
            results.add("result.redteam", {"score": 1})
            try:
                results.add("result.redteam", {"score": 0})
            except sqlite3.IntegrityError:
                return RedTeamOutcome.PREVENTED, {"constraint": "PRIMARY_KEY"}
            return RedTeamOutcome.NOT_MITIGATED, {}

        def artifact_substitution() -> tuple[RedTeamOutcome, dict[str, Any]]:
            store = ContentAddressedStore(root / "cas")
            metadata = store.put_bytes(b"original", artifact_class="fixture")
            store._object_path(metadata.digest).write_bytes(b"substitute")
            verification = store.verify(metadata.digest)
            return (
                RedTeamOutcome.DETECTED
                if not verification["passed"]
                else RedTeamOutcome.NOT_MITIGATED,
                verification,
            )

        def evidence_tampering() -> tuple[RedTeamOutcome, dict[str, Any]]:
            graph = PersistentEvidenceGraph(registry)
            graph.add_node(
                "node.redteam",
                NodeType.RUN,
                content_hash("untampered"),
                EvidenceClass.FIXTURE_ONLY,
            )
            with registry.transaction() as connection:
                connection.execute(
                    "UPDATE evidence_nodes SET metadata_json=? WHERE node_id=?",
                    ('{"tampered":true}', "node.redteam"),
                )
            verification = graph.verify()
            return (
                RedTeamOutcome.DETECTED
                if not verification["passed"]
                else RedTeamOutcome.NOT_MITIGATED,
                verification,
            )

        def certificate_tampering() -> tuple[RedTeamOutcome, dict[str, Any]]:
            graph = PersistentEvidenceGraph(registry)
            node_id = "node.redteam.certificate"
            graph.add_node(
                node_id,
                NodeType.RUN,
                content_hash("certificate-fixture"),
                EvidenceClass.FIXTURE_ONLY,
            )
            certificates = CertificateRepository(registry)
            certificate = certificates.issue(
                CertificateType.RUN_INTEGRITY,
                node_id,
                [node_id],
                signer=FixtureHMACSigner.development(),
            )
            try:
                with registry.transaction() as connection:
                    connection.execute(
                        "UPDATE certificates SET payload_json=? WHERE certificate_id=?",
                        ('{"tampered":true}', certificate["certificate_id"]),
                    )
            except sqlite3.DatabaseError as exc:
                return RedTeamOutcome.PREVENTED, {"database_guard": str(exc)}
            verification = certificates.verify(
                certificate["certificate_id"],
                verifier=FixtureHMACVerifier.development(),
            )
            return (
                RedTeamOutcome.DETECTED
                if not verification["passed"]
                else RedTeamOutcome.NOT_MITIGATED,
                verification,
            )

        def plugin_override() -> tuple[RedTeamOutcome, dict[str, Any]]:
            class MaliciousPlugin:
                metadata = PluginMetadata(
                    name="cab.malicious_gate",
                    plugin_type=PluginType.ANALYSIS,
                    version="1.0.0",
                    api_version="1.0",
                    capabilities=["gate_override"],
                    description="Safe malicious fixture.",
                )

                def validate(self) -> list[str]:
                    return []

            try:
                PluginManager().register(MaliciousPlugin())
            except ValueError as exc:
                return RedTeamOutcome.PREVENTED, {"reason": str(exc)}
            return RedTeamOutcome.NOT_MITIGATED, {}

        review = DurableReviewStore(root / "review" / "review.sqlite3")
        review.register_user("admin.redteam", ReviewerRole.ADMINISTRATOR)
        session = review.create_session("admin.redteam")

        def session_forgery() -> tuple[RedTeamOutcome, dict[str, Any]]:
            try:
                review.authenticate("forged-session-token")
            except PermissionError:
                return RedTeamOutcome.PREVENTED, {"token_storage": "HASH_ONLY"}
            return RedTeamOutcome.NOT_MITIGATED, {}

        def csrf() -> tuple[RedTeamOutcome, dict[str, Any]]:
            try:
                review.authenticate(session.token, csrf_token="forged-csrf")
            except PermissionError:
                return RedTeamOutcome.PREVENTED, {"csrf": "REJECTED"}
            return RedTeamOutcome.NOT_MITIGATED, {}

        def sql_injection() -> tuple[RedTeamOutcome, dict[str, Any]]:
            payload = "user'; DROP TABLE review_users;--"
            review.register_user(payload, ReviewerRole.REVIEWER)
            with review.registry._connect() as connection:
                table = connection.execute(
                    "SELECT 1 FROM review_users WHERE user_id=?",
                    (payload,),
                ).fetchone()
            return (
                RedTeamOutcome.CONTAINED if table else RedTeamOutcome.NOT_MITIGATED,
                {"parameterized_query": bool(table)},
            )

        def malicious_schema() -> tuple[RedTeamOutcome, dict[str, Any]]:
            try:
                ToolSpec(
                    name="malicious_schema",
                    description="fixture",
                    input_schema={
                        "type": "object",
                        "properties": {},
                        "$ref": "file://../../protected.json",
                    },
                )
            except ValueError as exc:
                return RedTeamOutcome.PREVENTED, {"reason": str(exc)}
            return RedTeamOutcome.NOT_MITIGATED, {}

        def chaos_case(fault: str) -> tuple[RedTeamOutcome, dict[str, Any]]:
            row = chaos_by_fault[fault]
            outcome = (
                RedTeamOutcome.CONTAINED
                if row["outcome"]
                in {"PREVENTED", "DETECTED_AND_CONTAINED", "RECOVERED", "FAILED_CLOSED"}
                else RedTeamOutcome.NOT_MITIGATED
            )
            return outcome, {
                "fault_outcome": row["outcome"],
                "expected_invariants": row["expected_invariants"],
                "observations": row["observations"],
                "receipt": row["receipt"],
            }

        def correction_abuse() -> tuple[RedTeamOutcome, dict[str, Any]]:
            results = PersistentResultRegistry(registry)
            results.add("result.correction.original", {"score": 1})
            results.correct(
                "result.correction.original",
                "result.correction.v2",
                {"score": 0},
                reason="fixture correction",
                reviewer_id="reviewer.fixture",
                public_notice="Fixture-only correction.",
            )
            try:
                results.correct(
                    "result.correction.original",
                    "result.correction.v2",
                    {"score": 2},
                    reason="overwrite attempt",
                    reviewer_id="attacker.fixture",
                    public_notice="Overwrite.",
                )
            except sqlite3.IntegrityError:
                history = results.history("result.correction.original")
                return RedTeamOutcome.PREVENTED, {
                    "record_count": len(history["records"]),
                    "correction_count": len(history["corrections"]),
                }
            return RedTeamOutcome.NOT_MITIGATED, {}

        cases = [
            _case(
                "archive_traversal",
                "CRITICAL",
                lambda: _archive_case(
                    ArchiveMember(path="../../escape", size_bytes=1),
                    "archive_traversal",
                ),
            ),
            _case(
                "symlink_escape",
                "CRITICAL",
                lambda: _archive_case(
                    ArchiveMember(
                        path="agent.py",
                        size_bytes=1,
                        is_symlink=True,
                        link_target="../../escape",
                    ),
                    "unsafe_symlink",
                ),
            ),
            _case(
                "environment_scraping",
                "CRITICAL",
                lambda: _audit_case("cat /proc/self/environ", "filesystem_enumeration"),
            ),
            _case(
                "output_flooding",
                "HIGH",
                lambda: _audit_case("x" * 2_048, "oversized_output", limit=1_024),
            ),
            _case(
                "prompt_echo",
                "CRITICAL",
                lambda: _audit_case("BEGIN_PRIVATE_TASK", "prompt_echo"),
            ),
            _case(
                "encoded_exfiltration",
                "CRITICAL",
                lambda: _audit_case("base64 private_payload", "encoded_dump"),
            ),
            _case("duplicate_result_injection", "CRITICAL", duplicate_result),
            _case("artifact_substitution", "CRITICAL", artifact_substitution),
            _case("certificate_tampering", "CRITICAL", certificate_tampering),
            _case("evidence_graph_tampering", "CRITICAL", evidence_tampering),
            _case("plugin_gate_override", "CRITICAL", plugin_override),
            _case("session_forgery", "CRITICAL", session_forgery),
            _case("csrf", "HIGH", csrf),
            _case("sql_injection", "CRITICAL", sql_injection),
            _case("malicious_benchmark_schema", "CRITICAL", malicious_schema),
            _case(
                "stale_lease_takeover",
                "CRITICAL",
                lambda: chaos_case("stale_heartbeat"),
            ),
            _case(
                "retry_amplification",
                "HIGH",
                lambda: chaos_case("network_disconnect"),
            ),
            _case("quota_bypass", "HIGH", lambda: chaos_case("quota_exhaustion")),
            _case(
                "abstention_abuse",
                "MEDIUM",
                lambda: _manual_case(
                    "Abstention distributions require real cohort baselines and human review."
                ),
            ),
            _case("scorer_failure", "HIGH", lambda: chaos_case("scorer_crash")),
            _case(
                "score_oracle_request",
                "CRITICAL",
                lambda: _audit_case("query_score_oracle", "score_oracle"),
            ),
            _case("correction_history_abuse", "CRITICAL", correction_abuse),
        ]
        critical_unresolved = [
            row
            for row in cases
            if row["severity"] == "CRITICAL"
            and row["outcome"] == RedTeamOutcome.NOT_MITIGATED.value
        ]
        report = {
            "schema_version": "1.0",
            "campaign_id": f"redteam.hardening.{content_hash(cases)[:24]}",
            "executed_cases": len(cases),
            "outcomes": {
                outcome.value: sum(row["outcome"] == outcome.value for row in cases)
                for outcome in RedTeamOutcome
            },
            "critical_unresolved_count": len(critical_unresolved),
            "manual_policy_count": sum(
                row["outcome"] == RedTeamOutcome.MANUAL_REVIEW.value for row in cases
            ),
            "passed": not critical_unresolved,
            "evidence_class": "FIXTURE_ONLY",
            "cases": cases,
            "created_at": utc_now(),
        }
        report["report_hash"] = content_hash(report)
        return report


__all__ = ["RedTeamOutcome", "run_hardening_redteam_campaign"]
