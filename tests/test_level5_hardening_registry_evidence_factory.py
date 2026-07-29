from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path

import pytest

from causal_agent_bench.level5.benchmark import (
    BenchmarkAuthoringSpec,
    BenchmarkRepository,
    TaskLifecycle,
    ToolSpec,
    compile_intervention,
    diversity_report,
)
from causal_agent_bench.level5.core import (
    ActorClass,
    EvidenceClass,
    content_hash,
)
from causal_agent_bench.level5.evidence import (
    CertificateRepository,
    CertificateType,
    ClaimRequirement,
    EdgeType,
    NodeType,
    PersistentEvidenceGraph,
    PersistentResultRegistry,
    compile_durable_claim,
    verify_transparency_log,
)
from causal_agent_bench.level5.migrations import (
    MIGRATION_BY_TARGET,
    SCHEMA_VERSION,
    MigrationManager,
)
from causal_agent_bench.level5.plugins import (
    ExampleScorerPlugin,
    PluginManager,
    PluginMetadata,
    PluginPermission,
    PluginRepository,
    PluginType,
)
from causal_agent_bench.level5.registry import InMemoryRegistry, SQLiteRegistry
from causal_agent_bench.level5.reproduction import public_fixture_authoring_spec
from causal_agent_bench.level5.signing import (
    FixtureHMACSigner,
    FixtureHMACVerifier,
)


def test_ordered_migration_backup_interruption_recovery_and_checksums(tmp_path):
    path = tmp_path / "registry.sqlite3"
    manager = MigrationManager(path)
    assert manager.current_version() == 0
    manager.ensure_v1()
    assert manager.current_version() == 1
    plan = manager.plan(3)
    assert [row["target_version"] for row in plan["migrations"]] == [2, 3]
    export = tmp_path / "before.json"
    with pytest.raises(RuntimeError, match="interrupted"):
        manager.migrate(
            3,
            interrupt_after_statement=1,
            export_before_upgrade=export,
        )
    assert export.is_file()
    runtime = manager.runtime_state()
    assert runtime["status"] == "FAILED"
    assert manager.current_version() == 1
    assert manager.recover() == 2
    assert manager.migrate(3) == SCHEMA_VERSION
    assert manager.runtime_state()["status"] == "IDLE"
    history = manager.history()
    assert [row["version"] for row in history] == [1, 2, 3]
    assert manager.verify_applied_checksums() == []
    assert Path(runtime["backup_path"]).is_file()

    with manager.connect() as connection:
        connection.execute(
            "UPDATE schema_migrations SET checksum='tampered' WHERE version=3"
        )
    errors = manager.verify_applied_checksums()
    assert errors == ["migration checksum mismatch at version 3"]
    with pytest.raises(ValueError, match="checksum"):
        manager.migrate(3)
    with manager.connect() as connection:
        connection.execute(
            "UPDATE schema_migrations SET checksum=? WHERE version=3",
            (MIGRATION_BY_TARGET[3].checksum,),
        )
    assert manager.verify_applied_checksums() == []
    with pytest.raises(ValueError, match="unsupported"):
        manager.plan(4)
    with pytest.raises(ValueError, match="downgrade"):
        manager.plan(2)


def test_registry_runtime_events_privacy_dependencies_and_restore(tmp_path):
    registry = SQLiteRegistry(tmp_path / "registry.sqlite3")
    registry.initialize()
    parent = registry.register("project", "project.hardening", {"name": "hardening"})
    child = registry.register("study", "study.hardening", {"name": "study"})
    dependency = registry.link(
        "study",
        child.entity_id,
        "project",
        parent.entity_id,
        "belongs_to",
    )
    assert dependency is None
    provenance = registry.add_provenance(
        output_hash=content_hash("output"),
        parent_hashes=[parent.content_hash],
        transformation_command="fixture",
        code_revision="test",
        environment_id="env.fixture",
        actor_class=ActorClass.FIXTURE,
        evidence_class=EvidenceClass.FIXTURE_ONLY,
    )
    assert provenance.startswith("prov.")
    assert registry.migration_runtime()["status"] == "IDLE"
    assert len(registry.migration_history()) == 3
    assert registry.audit_events()[0]["event_type"] == "REGISTERED"
    backup = registry.backup(tmp_path / "backup.sqlite3")
    restored = SQLiteRegistry.restore(backup, tmp_path / "restored.sqlite3")
    assert restored.get("study", "study.hardening") is not None
    with pytest.raises(ValueError, match="missing parent"):
        registry.link(
            "study",
            child.entity_id,
            "project",
            "project.missing",
            "belongs_to",
        )


def test_in_memory_registry_freeze_conflicts_and_export():
    registry = InMemoryRegistry()
    first = registry.register("project", "project.memory", {"name": "memory"})
    assert registry.get("project", "project.memory") == first
    assert registry.register(
        "project",
        "project.memory",
        {"name": "memory"},
        freeze=True,
    ).frozen
    with pytest.raises(ValueError, match="frozen"):
        registry.register("project", "project.memory", {"name": "changed"})
    with pytest.raises(KeyError, match="missing"):
        registry.freeze("study", "study.missing")
    assert registry.export_public()["entities"][0]["content_hash"] == first.content_hash


def test_benchmark_bounded_parser_persistence_lifecycle_and_diversity(tmp_path):
    spec = public_fixture_authoring_spec()
    compiled = compile_intervention(spec)
    path = tmp_path / "authoring.json"
    path.write_text(spec.model_dump_json(indent=2), encoding="utf-8")
    loaded = BenchmarkAuthoringSpec.from_path(path)
    assert compile_intervention(loaded).receipt.public_hash == compiled.receipt.public_hash

    alias_path = tmp_path / "aliases.yaml"
    alias_path.write_text("a: &a {x: 1}\nb: *a\n", encoding="utf-8")
    with pytest.raises(ValueError, match="aliases"):
        BenchmarkAuthoringSpec.from_path(alias_path)
    multi_path = tmp_path / "multi.yaml"
    multi_path.write_text("{}\n---\n{}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="exactly one"):
        BenchmarkAuthoringSpec.from_path(multi_path)
    deep_path = tmp_path / "deep.json"
    value: dict[str, object] = {}
    cursor = value
    for _ in range(20):
        child_value: dict[str, object] = {}
        cursor["child"] = child_value
        cursor = child_value
    deep_path.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(ValueError, match="depth"):
        BenchmarkAuthoringSpec.from_path(deep_path)
    with pytest.raises(ValueError, match="references"):
        ToolSpec(
            name="unsafe_schema",
            description="fixture",
            input_schema={
                "type": "object",
                "properties": {},
                "$ref": "https://attacker.invalid/schema.json",
            },
        )

    registry = SQLiteRegistry(tmp_path / "registry.sqlite3")
    repository = BenchmarkRepository(registry)
    record_id = repository.record_compilation(compiled)
    assert repository.record_compilation(compiled) == record_id
    assert repository.records(spec.benchmark_id)[0]["lifecycle"] == "STATIC_VALIDATED"
    repository.transition(
        spec.benchmark_id,
        TaskLifecycle.STATIC_VALIDATED,
        TaskLifecycle.HUMAN_REVIEW_REQUIRED,
        evidence={"review_packet": "fixture"},
    )
    with pytest.raises(ValueError, match="certified"):
        repository.transition(
            spec.benchmark_id,
            TaskLifecycle.HUMAN_REVIEW_REQUIRED,
            TaskLifecycle.C10_ELIGIBLE,
            evidence={},
        )
    report = diversity_report(
        [
                {
                    **compiled.public,
                    "instance_id": f"instance.{index}",
                    "prompt": f"{compiled.public['prompt']} Variant {index}.",
                "domain": domain,
                "source_id": source,
                "author_id": author,
                "intervention_family": family,
            }
            for index, (domain, source, author, family) in enumerate(
                [
                    ("math", "s1", "a1", "f1"),
                    ("code", "s2", "a2", "f2"),
                    ("law", "s3", "a3", "f3"),
                    ("science", "s4", "a4", "f4"),
                ]
            )
        ]
    )
    assert report["passed"]
    assert report["split_commitment"]
    assert report["concentration"]["domain"] == 0.25


def test_plugin_repository_permissions_compatibility_timeout_and_failures(tmp_path):
    registry = SQLiteRegistry(tmp_path / "registry.sqlite3")
    repository = PluginRepository(registry)
    manager = PluginManager(repository=repository)
    manager.register(ExampleScorerPlugin())
    assert manager.get("cab.example_exact_scorer").score("x", "x") == 1
    assert manager.capabilities()["cab.example_exact_scorer"] == [
        "exact_match",
        "fixture_safe",
    ]
    assert repository.records()[0]["status"] == "VALIDATED"

    class BadApi:
        metadata = PluginMetadata(
            name="cab.bad_api",
            plugin_type=PluginType.ANALYSIS,
            version="1.0.0",
            api_version="2.0",
            description="fixture",
        )

        def validate(self):
            return []

    with pytest.raises(ValueError, match="incompatible"):
        manager.register(BadApi())

    class Sensitive:
        metadata = PluginMetadata(
            name="cab.sensitive",
            plugin_type=PluginType.ANALYSIS,
            version="1.0.0",
            api_version="1.0",
            permissions=[PluginPermission.READ_PRIVATE_EVIDENCE],
            description="fixture",
        )

        def validate(self):
            return []

    with pytest.raises(ValueError, match="sensitive"):
        manager.register(Sensitive())

    class Invalid:
        metadata = PluginMetadata(
            name="cab.invalid",
            plugin_type=PluginType.ANALYSIS,
            version="1.0.0",
            api_version="1.0",
            description="fixture",
        )

        def validate(self):
            return ["invalid fixture"]

    with pytest.raises(ValueError, match="validation failed"):
        manager.register(Invalid())

    class Slow:
        metadata = PluginMetadata(
            name="cab.slow",
            plugin_type=PluginType.ANALYSIS,
            version="1.0.0",
            api_version="1.0",
            diagnostic_timeout_seconds=0.1,
            description="fixture",
        )

        def validate(self):
            time.sleep(0.15)
            return []

    with pytest.raises(ValueError, match="timeout"):
        manager.register(Slow())
    with pytest.raises(ValueError, match="already"):
        manager.register(ExampleScorerPlugin())
    assert manager.errors == []


def test_persistent_evidence_certification_claim_correction_and_transparency(tmp_path):
    registry = SQLiteRegistry(tmp_path / "registry.sqlite3")
    graph = PersistentEvidenceGraph(registry)
    with pytest.raises(ValueError, match="certified"):
        graph.add_node(
            "node.illegal",
            NodeType.RUN,
            content_hash("illegal"),
            EvidenceClass.PAPER_ELIGIBLE_EVIDENCE,
        )
    audit = graph.add_node(
        "node.audit",
        NodeType.AUDIT,
        content_hash("audit"),
        EvidenceClass.PRELIMINARY_REAL_EVIDENCE,
        metadata={"uncertainty_recorded": True, "fixture_contract": True},
    )
    run = graph.add_node(
        "node.run",
        NodeType.RUN,
        content_hash("run"),
        EvidenceClass.PRELIMINARY_REAL_EVIDENCE,
        metadata={"uncertainty_recorded": True, "fixture_contract": True},
    )
    assert graph.add_node(
        "node.run",
        NodeType.RUN,
        content_hash("run"),
        EvidenceClass.PRELIMINARY_REAL_EVIDENCE,
        metadata={"uncertainty_recorded": True, "fixture_contract": True},
    ) == run
    graph.add_edge(audit.node_id, run.node_id, EdgeType.AUDITED_BY)
    assert graph.add_edge(audit.node_id, run.node_id, EdgeType.AUDITED_BY)
    with pytest.raises(ValueError, match="cycle"):
        graph.add_edge(run.node_id, audit.node_id, EdgeType.GENERATED_FROM)
    assert graph.lineage(run.node_id) == [audit.node_id]
    with pytest.raises(KeyError):
        graph.lineage("node.missing")
    exported_preliminary = graph.export_public()
    imported = PersistentEvidenceGraph(SQLiteRegistry(tmp_path / "import.sqlite3"))
    counts = imported.import_graph(exported_preliminary)
    assert counts == {"nodes_imported": 2, "edges_imported": 1}
    assert imported.verify()["passed"]

    certificates = CertificateRepository(registry)
    signer = FixtureHMACSigner.development()
    verifier = FixtureHMACVerifier.development()
    certificate = certificates.issue(
        CertificateType.RUN_INTEGRITY,
        run.node_id,
        [audit.node_id, run.node_id],
        signer=signer,
    )
    assert certificates.verify(certificate["certificate_id"], verifier=verifier)["passed"]
    graph.transition(
        audit.node_id,
        EvidenceClass.AUDITED_REAL_EVIDENCE,
        audit_node_ids=[audit.node_id],
        certificate_ids=[certificate["certificate_id"]],
    )
    graph.transition(
        run.node_id,
        EvidenceClass.AUDITED_REAL_EVIDENCE,
        audit_node_ids=[audit.node_id],
        certificate_ids=[certificate["certificate_id"]],
    )
    claim = compile_durable_claim(
        ClaimRequirement(
            claim_id="claim.fixture.contract",
            claim_text_hash=content_hash("fixture-only claim contract"),
            required_node_types={NodeType.RUN, NodeType.AUDIT},
            minimum_evidence_class=EvidenceClass.AUDITED_REAL_EVIDENCE,
        ),
        graph,
        [audit.node_id, run.node_id],
    )
    assert claim["eligible"]
    assert graph.verify()["passed"]
    assert graph.export_public()["transparency"]["passed"]

    results = PersistentResultRegistry(registry)
    results.add("result.original", {"estimate": 0.5, "fixture": True})
    correction = results.correct(
        "result.original",
        "result.corrected",
        {"estimate": 0.6, "fixture": True},
        reason="fixture correction",
        reviewer_id="reviewer.fixture",
        public_notice="Fixture correction only.",
    )
    assert correction["version"] == 2
    results.withdraw(
        "result.corrected",
        reason="fixture withdrawal",
        reviewer_id="reviewer.fixture",
        public_notice="Fixture withdrawal only.",
    )
    assert len(results.history("result.original")["records"]) == 2

    revocation = certificates.revoke(
        certificate["certificate_id"],
        reason="fixture key retired",
    )
    assert revocation.startswith("cert-revocation.")
    assert not certificates.verify(
        certificate["certificate_id"],
        verifier=verifier,
    )["passed"]
    assert certificates.list()[0]["effective_status"] == "REVOKED"
    assert certificates.transparency_verify()["passed"]
    with (
        pytest.raises(sqlite3.DatabaseError, match="append-only"),
        registry.transaction() as connection,
    ):
        connection.execute("UPDATE transparency_log SET event_type='TAMPERED'")
    assert verify_transparency_log(registry)["passed"]


def test_persistent_evidence_negative_policy_and_tamper_detection(tmp_path):
    registry = SQLiteRegistry(tmp_path / "registry.sqlite3")
    graph = PersistentEvidenceGraph(registry)
    graph.add_node(
        "node.design",
        NodeType.RUN,
        content_hash("design"),
        EvidenceClass.DESIGN_ONLY,
    )
    with pytest.raises(ValueError, match="immutable"):
        graph.add_node(
            "node.design",
            NodeType.RUN,
            content_hash("changed"),
            EvidenceClass.DESIGN_ONLY,
        )
    with pytest.raises(ValueError, match="missing"):
        graph.add_edge("node.design", "node.missing", EdgeType.SUPPORTS)
    with pytest.raises(KeyError):
        graph.transition("node.missing", EvidenceClass.ENGINEERING_ONLY)
    with pytest.raises(ValueError, match="invalid"):
        graph.transition("node.design", EvidenceClass.PAPER_ELIGIBLE_EVIDENCE)
    graph.transition("node.design", EvidenceClass.ENGINEERING_ONLY)
    graph.transition("node.design", EvidenceClass.FIXTURE_ONLY)
    graph.transition("node.design", EvidenceClass.HUMAN_INPUT_REQUIRED)
    graph.transition("node.design", EvidenceClass.EXECUTION_PENDING)
    graph.transition("node.design", EvidenceClass.PRELIMINARY_REAL_EVIDENCE)
    with pytest.raises(ValueError, match="require audits"):
        graph.transition("node.design", EvidenceClass.AUDITED_REAL_EVIDENCE)

    certificates = CertificateRepository(registry)
    signer = FixtureHMACSigner.development()
    verifier = FixtureHMACVerifier.development()
    with pytest.raises(PermissionError, match="protected"):
        certificates.issue(
            CertificateType.RUN_INTEGRITY,
            "node.design",
            ["node.design"],
            signer=signer,
            protected_mode=True,
        )
    with pytest.raises(ValueError, match="missing"):
        certificates.issue(
            CertificateType.RUN_INTEGRITY,
            "node.missing",
            ["node.missing"],
            signer=signer,
        )
    assert not certificates.verify("cert.missing", verifier=verifier)["passed"]
    with pytest.raises(KeyError):
        certificates.revoke("cert.missing", reason="missing")
    with pytest.raises(ValueError, match="reason"):
        certificates.revoke("cert.missing", reason="")

    with registry.transaction() as connection:
        connection.execute(
            """
            INSERT INTO transparency_log(
                previous_hash, current_hash, event_type, subject_id,
                payload_hash, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("wrong", content_hash("wrong"), "FORGED", "node.design", "wrong", "now"),
        )
    tampered = verify_transparency_log(registry)
    assert not tampered["passed"]
    assert any("previous hash" in error for error in tampered["errors"])
