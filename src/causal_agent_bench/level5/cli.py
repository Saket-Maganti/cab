"""Command dispatch for the CAB Research OS Level-5 public surface."""

from __future__ import annotations

import json
import platform
import sys
from pathlib import Path
from typing import Any

import yaml

from causal_agent_bench.level5.benchmark import (
    BenchmarkAuthoringSpec,
    TaskLifecycle,
    build_review_packet,
    compile_intervention,
    diversity_report,
    write_compilation,
)
from causal_agent_bench.level5.core import EvidenceClass, content_hash, utc_now
from causal_agent_bench.level5.evaluator import (
    MockSandboxRuntime,
    SubmissionManifest,
    audit_output,
    evaluate_fixture_submission,
)
from causal_agent_bench.level5.evidence import (
    CertificateType,
    EvidenceGraph,
    NodeType,
    issue_certificate,
    model_card_template,
)
from causal_agent_bench.level5.execution import (
    ContentAddressedStore,
    FixtureBackend,
    LocalScheduler,
    RunPlanSpec,
    compile_run_plan,
    fixture_20_spec,
)
from causal_agent_bench.level5.governance import Level5BuildState, level5_check
from causal_agent_bench.level5.plugins import ExampleScorerPlugin, PluginManager
from causal_agent_bench.level5.registry import SQLiteRegistry
from causal_agent_bench.level5.reliability import FaultKind, run_fixture_chaos_campaign
from causal_agent_bench.level5.reproduction import (
    public_fixture_authoring_spec,
    run_internal_fixture_reproduction,
    run_red_team_fixture_campaign,
)

LEVEL5_COMMANDS = {
    "registry",
    "env",
    "benchmark",
    "plan",
    "status",
    "cancel",
    "resume",
    "merge",
    "artifacts",
    "reliability",
    "review",
    "evaluator",
    "evidence",
    "certify",
    "model-card",
    "claims",
    "plugins",
    "reproduce",
    "redteam",
    "level5",
    "release-check",
}


def _print(value: Any) -> None:
    print(json.dumps(value, indent=2, sort_keys=True, default=str))


def _registry(args: Any) -> None:
    registry = SQLiteRegistry(args.path)
    command = args.registry_command
    if command == "init":
        registry.initialize()
        _print({"initialized": True, "path": str(registry.path), "schema_version": 1})
    elif command in {"doctor", "verify"}:
        result = registry.verify()
        _print(result)
        if not result["passed"]:
            raise SystemExit(1)
    elif command == "export":
        result = registry.export_public()
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        _print({"exported": True, "output": str(output), "entities": len(result["entities"])})
    elif command == "backup":
        path = registry.backup(args.output)
        _print({"backed_up": True, "output": str(path)})
    elif command == "restore":
        restored = SQLiteRegistry.restore(args.backup, args.path)
        _print({"restored": True, "path": str(restored.path), "verification": restored.verify()})
    elif command == "results":
        path = Path(args.results_path)
        results = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else []
        _print({"results": results, "point_leaderboard": False, "uncertainty_required": True})


def _env_doctor(args: Any) -> None:
    root = Path(args.repo_root)
    checks = {
        "python_supported": sys.version_info >= (3, 11),
        "constraints_lock": (root / "constraints.txt").is_file(),
        "dockerfile": (root / "Dockerfile").is_file(),
        "apptainer_definition": (root / "Apptainer.def").is_file(),
        "sbom_generator": (root / "scripts/generate_level5_sbom.py").is_file(),
        "licence_report_generator": (root / "scripts/generate_dependency_licenses.py").is_file(),
    }
    _print(
        {
            "passed": all(checks.values()),
            "checks": checks,
            "python": platform.python_version(),
            "platform": platform.platform(),
            "environment_id": content_hash(
                {"python": platform.python_version(), "platform": platform.platform()}
            ),
        }
    )


def _benchmark(args: Any) -> None:
    command = args.benchmark_command
    path = Path(args.spec)
    if command == "init":
        if path.exists() and not args.force:
            raise SystemExit(f"refusing to overwrite existing authoring spec: {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            yaml.safe_dump(
                public_fixture_authoring_spec().model_dump(mode="json"),
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        _print({"initialized": True, "spec": str(path), "evidence_class": "FIXTURE_ONLY"})
        return
    spec = BenchmarkAuthoringSpec.from_path(path)
    compiled = compile_intervention(spec)
    if command == "compile":
        paths = write_compilation(
            compiled, args.output_dir, allow_private=args.allow_private_output
        )
        _print({"compiled": True, "paths": [str(value) for value in paths], "receipt": compiled.receipt})
    elif command == "validate":
        _print(
            {
                "valid": True,
                "instance_id": compiled.receipt.instance_id,
                "lifecycle": TaskLifecycle.STATIC_VALIDATED.value,
            }
        )
    elif command == "diversity":
        _print(diversity_report([compiled.public]))
    elif command == "review-packet":
        packet = build_review_packet([compiled])
        output = Path(args.output_dir) / "review_packet.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        _print({"output": str(output), "items": len(packet["items"])})
    elif command == "freeze":
        _print(
            {
                "frozen": False,
                "state": "HUMAN_REVIEW_REQUIRED",
                "reason": "genuine C10 certificate is required before freeze",
            }
        )
        raise SystemExit(2)
    elif command == "retire":
        _print(
            {
                "planned": True,
                "transition": "ACTIVE_OR_DEPRECATED -> RETIRED",
                "versioned_decision_required": True,
            }
        )
    elif command == "contamination-audit":
        report = diversity_report([compiled.public])
        _print({**report, "contamination_propagation": "versioned_fail-closed"})


def _plan(args: Any) -> None:
    spec = (
        RunPlanSpec.model_validate_json(Path(args.spec).read_text(encoding="utf-8"))
        if args.spec
        else fixture_20_spec()
    )
    manifest = compile_run_plan(spec, shard_count=args.shards)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(manifest.model_dump_json(indent=2) + "\n", encoding="utf-8")
    _print(
        {
            "dry_run": True,
            "manifest": str(output),
            "manifest_hash": manifest.manifest_hash,
            "units": len(manifest.units),
            "approval_requirements": manifest.approval_requirements,
        }
    )


def _level5_run(args: Any) -> None:
    manifest = compile_run_plan(fixture_20_spec(), shard_count=2)
    if args.dry_run:
        _print(
            {
                "dry_run": True,
                "manifest_hash": manifest.manifest_hash,
                "units": len(manifest.units),
                "will_call_models": False,
            }
        )
        return
    run_dir = Path(args.level5_fixture_dir)
    store = ContentAddressedStore(run_dir / "artifacts")
    report = LocalScheduler(FixtureBackend(), store).run(manifest, run_dir)
    _print(report)


def _run_status(run_dir: str | Path) -> dict[str, Any]:
    run_dir = Path(run_dir)
    report_path = run_dir / "run_report.json"
    checkpoint_path = run_dir / "checkpoint.json"
    return {
        "exists": run_dir.is_dir(),
        "report": (
            json.loads(report_path.read_text(encoding="utf-8"))
            if report_path.is_file()
            else None
        ),
        "checkpoint": (
            json.loads(checkpoint_path.read_text(encoding="utf-8"))
            if checkpoint_path.is_file()
            else None
        ),
    }


def _artifacts(args: Any) -> None:
    store = ContentAddressedStore(args.store)
    if args.artifacts_command == "verify":
        result = store.verify(args.digest)
    elif args.artifacts_command == "export":
        result = {
            "output": str(store.export_bundle(args.digest, args.output)),
            "digests": args.digest,
        }
    else:
        result = store.gc_dry_run(set(args.referenced))
    _print(result)


def _reliability(args: Any) -> None:
    selected = {FaultKind(value) for value in args.fault} if args.fault else None
    report = run_fixture_chaos_campaign(injected_failures=selected)
    if args.reliability_command in {"campaign", "report"}:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        report = {**report, "output": str(output)}
    _print(report)


def _review(args: Any) -> None:
    command = args.review_command
    if command == "serve":
        readiness = {
            "ready": args.host in {"127.0.0.1", "localhost", "::1"},
            "bind": f"http://{args.host}:{args.port}",
            "local_only": args.host in {"127.0.0.1", "localhost", "::1"},
            "scientific_state": "HUMAN_VALIDATION_REQUIRED",
        }
        if args.check:
            _print(readiness)
            return
        from causal_agent_bench.level5.review_server import serve_review_app

        _print({**readiness, "starting": True})
        serve_review_app(args.host, args.port, data_dir=args.data_dir)
        return
    payload = (
        json.loads(Path(args.input).read_text(encoding="utf-8"))
        if args.input and Path(args.input).is_file()
        else {}
    )
    result = {
        "command": command,
        "accepted": False,
        "input_rows": len(payload) if isinstance(payload, list) else int(bool(payload)),
        "state": "HUMAN_VALIDATION_REQUIRED",
        "reason": "genuine human review operations require versioned attestations",
    }
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _print(result)


def _fixture_submission() -> SubmissionManifest:
    return SubmissionManifest(
        submission_id="submission.fixture.v1",
        package_hash=content_hash("fixture-package"),
        model_declaration="deterministic fixture",
        policy_declaration="fixture policy",
        runtime_image="cab/fixture:local",
        entry_point=["python", "-m", "fixture_agent"],
        licence="MIT",
        authorship_attestation=True,
    )


def _evaluator(args: Any) -> None:
    command = args.evaluator_command
    if command == "audit":
        _print(audit_output(args.text, output_limit=1_000_000))
        return
    submission = (
        SubmissionManifest.model_validate_json(
            Path(args.submission).read_text(encoding="utf-8")
        )
        if args.submission
        else _fixture_submission()
    )
    if command == "validate-submission":
        _print({"valid": True, "submission": submission.model_dump(mode="json")})
        return
    receipt = evaluate_fixture_submission(
        submission,
        MockSandboxRuntime(),
        task_set_hash=content_hash(["fixture-task"]),
    )
    if command in {"run-fixture", "receipt"}:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        receipt = {**receipt, "output": str(output)}
    _print(receipt)


def _evidence(args: Any) -> None:
    path = Path(args.graph)
    if not path.is_file():
        _print({"passed": False, "error": f"graph not found: {path}"})
        raise SystemExit(1)
    graph = json.loads(path.read_text(encoding="utf-8"))
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    if args.evidence_command == "trace":
        node_id = args.node_id
        related = [
            edge for edge in edges if node_id in {edge.get("source"), edge.get("target")}
        ]
        _print({"node_id": node_id, "related_edges": related})
    else:
        node_ids = {node.get("node_id") for node in nodes}
        errors = [
            edge
            for edge in edges
            if edge.get("source") not in node_ids or edge.get("target") not in node_ids
        ]
        _print({"passed": not errors, "nodes": len(nodes), "edges": len(edges), "errors": errors})


def _certify(args: Any) -> None:
    graph = EvidenceGraph()
    node = graph.add_node(
        "node.fixture.run",
        NodeType.RUN,
        content_hash("fixture-run"),
        EvidenceClass.FIXTURE_ONLY,
    )
    certificate = issue_certificate(CertificateType.RUN_INTEGRITY, node.node_id, [node])
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(certificate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _print({**certificate, "output": str(output)})


def _gate(state_path: str) -> dict[str, Any]:
    state = Level5BuildState.from_path(state_path)
    return level5_check(state)


def handle_level5_command(args: Any) -> bool:
    """Dispatch a Level-5 command and return whether it was handled."""

    command = args.command
    if command == "run" and (args.dry_run or args.level5_fixture_dir):
        _level5_run(args)
        return True
    if command not in LEVEL5_COMMANDS:
        return False
    if command == "registry":
        _registry(args)
    elif command == "env":
        _env_doctor(args)
    elif command == "benchmark":
        _benchmark(args)
    elif command == "plan":
        _plan(args)
    elif command == "status":
        _print(_run_status(args.run_dir))
    elif command == "cancel":
        path = Path(args.run_dir) / "cancellation_receipt.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        receipt = {
            "unit_id": args.unit_id,
            "cancelled": True,
            "fixture_only": True,
            "created_at": utc_now(),
        }
        path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        _print({**receipt, "path": str(path)})
    elif command == "resume":
        manifest = compile_run_plan(fixture_20_spec(), shard_count=2)
        store = ContentAddressedStore(Path(args.run_dir) / "artifacts")
        _print(LocalScheduler(FixtureBackend(), store).run(manifest, args.run_dir))
    elif command == "merge":
        _print(_run_status(args.run_dir))
    elif command == "artifacts":
        _artifacts(args)
    elif command == "reliability":
        _reliability(args)
    elif command == "review":
        _review(args)
    elif command == "evaluator":
        _evaluator(args)
    elif command == "evidence":
        _evidence(args)
    elif command == "certify":
        _certify(args)
    elif command == "model-card":
        card = model_card_template(args.model_id, args.revision)
        if args.output:
            output = Path(args.output)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(card, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        _print(card)
    elif command == "claims":
        gate = _gate(args.state)
        _print(
            {
                "eligible": gate["level5_complete"],
                "supported_empirical_claims": gate["genuine_evidence"][
                    "supported_empirical_claims"
                ],
                "blocked_states": gate["blocked_states"],
            }
        )
    elif command == "plugins":
        manager = PluginManager()
        manager.register(ExampleScorerPlugin())
        discovered = manager.discover()
        _print(
            {
                "registered": manager.capabilities(),
                "discovered": [row.__dict__ for row in discovered],
                "isolated_errors": [row.__dict__ for row in manager.errors],
            }
        )
    elif command == "reproduce":
        _print(run_internal_fixture_reproduction(args.workdir))
    elif command == "redteam":
        report = run_red_team_fixture_campaign()
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        _print({**report, "output": str(output)})
    elif command == "level5":
        _print(_gate(args.state))
    elif command == "release-check":
        from scripts.release_check import run_release_check

        legacy = run_release_check()
        gate = _gate(args.state)
        result = {
            "passed": legacy["passed"] and gate["foundation_complete"],
            "legacy_release": legacy,
            "level5_gate": gate,
        }
        _print(result)
        if not result["passed"]:
            raise SystemExit(1)
    return True


__all__ = ["LEVEL5_COMMANDS", "handle_level5_command"]
