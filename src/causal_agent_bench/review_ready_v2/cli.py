"""Canonical CLI for the reviewer-ready V2 packet and two-stage review workflow.

Output is always public-safe: statuses, counts and hashes.  No command prints a
prompt, a record, an answer, a route label, a private identifier, a reviewer
pseudonym, or Stage-2 content, and no command performs model execution or genuine
human review.

Reviewer roles are given as ``--role``.  Any accepted spelling is normalized to
the canonical enum ``REVIEWER_A`` / ``REVIEWER_B`` / ``ADJUDICATOR`` before it is
used, and there are no reviewer-id defaults to disagree with each other.
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
import sys
from pathlib import Path
from typing import Any

from causal_agent_bench.review_ready_v2 import PACKET_VERSION
from causal_agent_bench.review_ready_v2.adjudication import STAGE1, STAGE2
from causal_agent_bench.review_ready_v2.adjudication_packages import (
    BINDING_FIELDS,
    BINDING_SCHEMA_VERSION,
    PACKAGE_FILENAMES,
    STAGE1_PACKAGE_SCHEMA_VERSION,
    STAGE2_CONDITIONAL_EVIDENCE,
    STAGE2_ONLY_KEYS,
    STAGE2_PACKAGE_SCHEMA_VERSION,
    STAGE2_REQUIRED_EVIDENCE,
    build_stage1_adjudicator_package,
    build_stage2_adjudicator_package,
    disputed_pair_ids,
    package_binding,
)
from causal_agent_bench.review_ready_v2.assignments import (
    AssignmentError,
    assignment_for_role,
    create_assignment,
    load_assignments,
    public_assignment_summary,
    verify_registry_complete,
)
from causal_agent_bench.review_ready_v2.common import (
    read_json,
    sha256_bytes,
    sha256_json,
    write_json,
)
from causal_agent_bench.review_ready_v2.declarations import DeclarationError
from causal_agent_bench.review_ready_v2.design import design_audit
from causal_agent_bench.review_ready_v2.fixture_e2e import run_fixture_e2e
from causal_agent_bench.review_ready_v2.freeze import (
    attestation_policy,
    build_freeze,
    current_head,
    generator_provenance,
    verify_attestation,
    verify_freeze,
)
from causal_agent_bench.review_ready_v2.hostile import hostile_route_audit
from causal_agent_bench.review_ready_v2.keys import ExternalKeyError
from causal_agent_bench.review_ready_v2.leakage import stage1_leakage_audit, usability_audit
from causal_agent_bench.review_ready_v2.operators import isolation_audit
from causal_agent_bench.review_ready_v2.packet import (
    build_packet,
    load_pairs,
    private_root_for,
    retire_v3_qualification_directory,
    write_qualification_packages,
)
from causal_agent_bench.review_ready_v2.power import build_power_plan
from causal_agent_bench.review_ready_v2.qualification import (
    QUALIFICATION_DIRNAME,
    QUALIFICATION_KEY_ENV,
    QUALIFICATION_KEY_FILENAME,
    QUALIFICATION_SCHEMA_VERSION,
    QUALIFICATION_SOURCE_ENV,
    QualificationError,
    load_qualification_keys,
    load_qualification_source,
    qualification_source_path,
    qualification_source_schema,
    retired_qualification_registry,
    validate_qualification_source,
)
from causal_agent_bench.review_ready_v2.receipts import (
    COORDINATOR_KEY_ENV,
    ReceiptError,
    coordinator_key_available,
)
from causal_agent_bench.review_ready_v2.registry import (
    active_path_registry,
    retired_packet_registry,
    retirement_enforcement_report,
    verify_active_paths,
)
from causal_agent_bench.review_ready_v2.report import (
    build_readiness_report,
    public_design_summary,
    public_hostile_summary,
    public_isolation_summary,
    public_leakage_summary,
    public_route_summary,
    readiness_markdown,
)
from causal_agent_bench.review_ready_v2.roles import (
    ADJUDICATOR,
    CANONICAL_ROLES,
    REVIEW_ROLES,
    RoleError,
    normalize_role,
    package_basename,
)
from causal_agent_bench.review_ready_v2.routes import validate_pair_routes
from causal_agent_bench.review_ready_v2.stage1 import build_stage1_package, stage1_item, zip_bytes
from causal_agent_bench.review_ready_v2.stage2 import (
    STAGE2_REVIEWER_INSTRUCTIONS,
    acceptance_policy,
    stage2_form_template,
)
from causal_agent_bench.review_ready_v2.stage2_issuance import issuance_schema
from causal_agent_bench.review_ready_v2.vault import (
    KEY_ENV,
    VaultError,
    load_key,
    unlocked_workspace,
    unseal,
    vault_status,
)
from causal_agent_bench.review_ready_v2.workflow import (
    ReviewWorkspace,
    WorkflowError,
    authorize_model_execution,
    build_exclusion_register,
    lock_reviewed_slice,
    run_c10,
    workflow_status,
)

REPORT_DIR = "reports/reviewer_ready_v2"


def _emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def _require(args: argparse.Namespace, *names: str) -> None:
    missing = sorted(name for name in names if getattr(args, name.replace("-", "_"), None) is None)
    if missing:
        raise SystemExit(
            "missing required argument(s): " + ", ".join(f"--{name}" for name in missing)
        )


def _role(args: argparse.Namespace) -> str:
    _require(args, "role")
    return normalize_role(args.role)


def _seed(repo_root: Path, explicit: str | None) -> bytes:
    if explicit:
        return bytes.fromhex(explicit) if len(explicit) == 64 else explicit.encode().ljust(32, b"\0")
    env = os.environ.get("CAB_PACKET_SEED", "").strip()
    if env:
        return bytes.fromhex(env) if len(env) == 64 else env.encode().ljust(32, b"\0")
    seed_path = Path(os.environ.get("CAB_PACKET_SEED_PATH", "")).expanduser()
    if seed_path and seed_path.is_file():
        return seed_path.read_bytes()
    raise SystemExit(
        "No private generation seed. Set CAB_PACKET_SEED (64 hex chars) or CAB_PACKET_SEED_PATH "
        "to an owner-only file outside the repository."
    )


def _private_root(repo_root: Path, args: argparse.Namespace) -> Path:
    return Path(args.private_root) if args.private_root else private_root_for(repo_root)


def _mappings(private_root: Path) -> dict[str, dict[str, str]]:
    """Reviewer-item to pair mappings, keyed by the canonical role."""

    mappings: dict[str, dict[str, str]] = {}
    for role in REVIEW_ROLES:
        path = private_root / "mappings" / f"{package_basename(role)}_mapping.json"
        if path.is_file():
            mappings[role] = read_json(path)["reviewer_item_to_pair"]
    return mappings


def _workspace(repo_root: Path, args: argparse.Namespace) -> ReviewWorkspace:
    root = _private_root(repo_root, args)
    if getattr(args, "fixture", False):
        return ReviewWorkspace.fixture(root)
    return ReviewWorkspace.production(root, repo_root)


def _stage2_records(repo_root: Path, private_root: Path) -> dict[str, dict[str, Any]]:
    _, key = load_key(repo_root)
    vault = (private_root / "stage2" / "stage2_vault.enc").read_bytes()
    return {str(row["pair_id"]): row for row in unseal(vault, key)}


def _applicability_by_pair(repo_root: Path, private_root: Path) -> dict[str, dict[str, bool]]:
    return {
        pair_id: dict(record["stage2_dimension_applicability"])
        for pair_id, record in _stage2_records(repo_root, private_root).items()
    }


def _qualification_dir(private_root: Path) -> Path:
    return private_root / QUALIFICATION_DIRNAME


def _qualification_package_path(private_root: Path, role: str) -> Path:
    return _qualification_dir(private_root) / f"qualification_{role.casefold()}.zip"


def _qualification_keys(repo_root: Path, private_root: Path) -> dict[str, Any]:
    return load_qualification_keys(
        _qualification_dir(private_root) / QUALIFICATION_KEY_FILENAME, repo_root
    )


def _outside_repo(repo_root: Path, raw: str, label: str) -> Path:
    output = Path(raw).expanduser()
    if str(output.resolve()).startswith(str(repo_root.resolve())):
        raise SystemExit(f"{label} must be written outside the repository root")
    output.mkdir(parents=True, exist_ok=True)
    output.chmod(0o700)
    return output


def _frozen_identity(repo_root: Path) -> tuple[str, str, str]:
    """``(packet_commitment, freeze_hash, exact_commit)`` for provenance binding."""

    commitment = read_json(repo_root / REPORT_DIR / "PUBLIC_PACKET_COMMITMENT.json")
    freeze = read_json(repo_root / REPORT_DIR / "SCIENTIFIC_FREEZE_V2.json")
    return commitment["commitment_sha256"], freeze["freeze_sha256"], current_head(repo_root)


# --------------------------------------------------------------------------
# packet generation and validation
# --------------------------------------------------------------------------


def cmd_generate_private_packet(repo_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    seed = _seed(repo_root, args.seed)
    root = Path(args.private_root) if args.private_root else None
    result = build_packet(repo_root, seed, private_root=root)
    write_json(repo_root / REPORT_DIR / "PUBLIC_PACKET_COMMITMENT.json", result["commitment"])
    return {
        "status": result["commitment"]["status"],
        "packet_version": PACKET_VERSION,
        "commitment_sha256": result["commitment"]["commitment_sha256"],
        "gates": result["commitment"]["gates"],
    }


def cmd_validate_private_packet(repo_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    private_root = _private_root(repo_root, args)
    pairs = load_pairs(private_root)
    design = design_audit(pairs)
    isolation = [
        isolation_audit(pair.clean_environment, pair.intervention_environment, pair.intervention_patch)
        for pair in pairs
    ]
    routes = [validate_pair_routes(pair) for pair in pairs]
    hostile = hostile_route_audit(pairs)
    return {
        "status": "CAB_PRIVATE_PACKET_V2_VALID"
        if design["passed"]
        and all(row["passed"] for row in isolation)
        and all(row["passed"] for row in routes)
        and hostile["passed"]
        else "CAB_PRIVATE_PACKET_V2_INVALID",
        "design": public_design_summary(design)["passed"],
        "isolation": public_isolation_summary(isolation),
        "routes": public_route_summary(routes),
        "hostile": public_hostile_summary(hostile),
    }


def cmd_generate_stage1_packages(repo_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    seed = _seed(repo_root, args.seed)
    private_root = _private_root(repo_root, args)
    pairs = load_pairs(private_root)
    hashes: dict[str, str] = {}
    for role in REVIEW_ROLES:
        basename = package_basename(role)
        payload, mapping, _ = build_stage1_package(pairs, seed, basename)
        target = private_root / "stage1" / f"{basename}.zip"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
        target.chmod(0o600)
        write_json(
            private_root / "mappings" / f"{basename}_mapping.json",
            {"reviewer_item_to_pair": mapping},
        )
        hashes[role] = sha256_bytes(payload)
    return {"status": "CAB_STAGE1_PACKAGES_READY", "stage1_package_hashes": hashes}


def cmd_generate_private_qualification_packages(
    repo_root: Path, args: argparse.Namespace
) -> dict[str, Any]:
    private_root = _private_root(repo_root, args)
    source = load_qualification_source(qualification_source_path(private_root))
    manifest = write_qualification_packages(
        _qualification_dir(private_root), repo_root, source=source
    )
    retired = retire_v3_qualification_directory(private_root)
    return {
        "status": "CAB_PRIVATE_QUALIFICATION_PACKAGES_READY",
        "qualification_version": manifest["qualification_version"],
        "source_schema_version": manifest["source_schema_version"],
        "qualification_package_hashes": {
            role: row["sha256"] for role, row in manifest["packages"].items()
        },
        "encrypted_key_sha256": manifest["encrypted_key_sha256"],
        "answer_key_environment_variable": QUALIFICATION_KEY_ENV,
        "source_environment_variable": QUALIFICATION_SOURCE_ENV,
        "plaintext_answer_key_persisted": False,
        "retired_directory_renamed_to": retired,
    }


def cmd_validate_qualification_source(repo_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    """Check privately authored qualification material without disclosing any of it."""

    private_root = _private_root(repo_root, args)
    path = qualification_source_path(private_root)
    source = load_qualification_source(path)
    return {
        "status": "CAB_QUALIFICATION_SOURCE_VALID",
        "source_is_git_ignored": "private_data" in path.parts
        or not str(path.resolve()).startswith(str(repo_root.resolve())),
        **validate_qualification_source(source),
    }


def cmd_qualification_source_schema(repo_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    return qualification_source_schema()


def cmd_validate_stage1_packages(repo_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    private_root = _private_root(repo_root, args)
    pairs = load_pairs(private_root)
    packages: dict[str, bytes] = {}
    for role in REVIEW_ROLES:
        basename = package_basename(role)
        path = private_root / "stage1" / f"{basename}.zip"
        if path.is_file():
            packages[basename] = path.read_bytes()
        qualification = _qualification_package_path(private_root, role)
        if qualification.is_file():
            packages[f"qualification_{role.casefold()}"] = qualification.read_bytes()
    leakage = stage1_leakage_audit(packages, pairs, _mappings_by_basename(private_root))
    usability = usability_audit(packages)
    return {
        "leakage": public_leakage_summary(leakage),
        "usability": usability,
        "passed": leakage["passed"] and usability["passed"],
    }


def _mappings_by_basename(private_root: Path) -> dict[str, dict[str, str]]:
    return {
        package_basename(role): mapping for role, mapping in _mappings(private_root).items()
    }


# --------------------------------------------------------------------------
# reviewer assignment, declarations, qualification
# --------------------------------------------------------------------------


def cmd_create_reviewer_assignment(repo_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    role = _role(args)
    _require(args, "pseudonym")
    private_root = _private_root(repo_root, args)
    stage1_hash = qualification_hash = None
    if role in REVIEW_ROLES:
        stage1_path = private_root / "stage1" / f"{package_basename(role)}.zip"
        qualification_path = _qualification_package_path(private_root, role)
        for label, path in (("Stage-1", stage1_path), ("qualification", qualification_path)):
            if not path.is_file():
                raise SystemExit(
                    f"the {label} package for {role} does not exist yet: generate it first"
                )
        stage1_hash = sha256_bytes(stage1_path.read_bytes())
        qualification_hash = sha256_bytes(qualification_path.read_bytes())
    assignment = create_assignment(
        private_root,
        packet_version=PACKET_VERSION,
        reviewer_pseudonym=args.pseudonym,
        role=role,
        stage1_package_hash=stage1_hash,
        qualification_package_hash=qualification_hash,
    )
    return {
        "status": "CAB_REVIEWER_ASSIGNMENT_CREATED",
        "reviewer_role": assignment["reviewer_role"],
        "stage1_package_hash": assignment["stage1_package_hash"],
        "qualification_package_hash": assignment["qualification_package_hash"],
        "opaque_id_namespace": assignment["stage1_opaque_id_namespace"],
        "assignment_sha256": assignment["assignment_sha256"],
        "reviewer_pseudonym_published": False,
    }


def cmd_show_reviewer_assignments(repo_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    registry = load_assignments(_private_root(repo_root, args), packet_version=PACKET_VERSION)
    return {
        "status": "CAB_REVIEWER_ASSIGNMENTS",
        **public_assignment_summary(registry),
        "completeness": verify_registry_complete(registry),
    }


def cmd_ingest_reviewer_declaration(repo_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    role = _role(args)
    _require(args, "declaration")
    workspace = _workspace(repo_root, args)
    receipt = workspace.ingest_declaration(role, read_json(Path(args.declaration)))
    return {
        "status": "REVIEWER_DECLARATION_RECORDED",
        "reviewer_role": role,
        "declaration_sha256": receipt["declaration_sha256"],
        "requires_coordinator_review": receipt["requires_coordinator_review"],
        "next_step": "accept-reviewer-declaration"
        if receipt["requires_coordinator_review"]
        else "score-private-qualification",
    }


def cmd_accept_reviewer_declaration(repo_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    role = _role(args)
    _require(args, "decision", "rationale")
    workspace = _workspace(repo_root, args)
    receipt = workspace.accept_declaration(
        role, decision=str(args.decision).upper(), rationale=args.rationale
    )
    return {
        "status": "CAB_DECLARATION_DECISION_RECORDED",
        "reviewer_role": role,
        "coordinator_review_decision": receipt["coordinator_review_decision"],
    }


def cmd_score_private_qualification(repo_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    role = _role(args)
    _require(args, "submission")
    workspace = _workspace(repo_root, args)
    keys = _qualification_keys(repo_root, workspace.private_root)
    if role not in keys:
        raise SystemExit(f"the encrypted qualification key holds no answers for {role}")
    receipt = workspace.ingest_qualification(
        role, read_json(Path(args.submission)), keys[role],
        qualification_version=QUALIFICATION_SCHEMA_VERSION,
    )
    return {
        "status": "REVIEWER_QUALIFIED",
        "reviewer_role": role,
        "rate": receipt["rate"],
        "threshold": receipt["threshold"],
        "receipt_sha256": receipt["receipt_sha256"],
        "answer_key_disclosed": False,
    }


# --------------------------------------------------------------------------
# Stage 1
# --------------------------------------------------------------------------


def cmd_ingest_stage1(repo_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    role = _role(args)
    _require(args, "submission")
    workspace = _workspace(repo_root, args)
    private_root = workspace.private_root
    mapping = _mappings(private_root)[role]
    package = (private_root / "stage1" / f"{package_basename(role)}.zip").read_bytes()
    receipt = workspace.ingest_stage1(
        role,
        Path(args.submission).read_bytes(),
        expected_item_ids=sorted(mapping),
        package_sha256=sha256_bytes(package),
    )
    return {
        "status": "STAGE1_SUBMISSION_RECORDED",
        "reviewer_role": role,
        "submission_sha256": receipt["submission_sha256"],
        "row_count": receipt["row_count"],
    }


def cmd_commit_stage1(repo_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    workspace = _workspace(repo_root, args)
    commitment = read_json(repo_root / REPORT_DIR / "PUBLIC_PACKET_COMMITMENT.json")
    freeze = read_json(repo_root / REPORT_DIR / "SCIENTIFIC_FREEZE_V2.json")
    receipt = workspace.commit_stage1(
        packet_commitment=commitment["commitment_sha256"],
        package_hashes=commitment["stage1_package_hashes"],
        review_schema_version="cab_stage1_review_form_v2",
        scientific_freeze_sha256=freeze["freeze_sha256"],
        exact_commit=current_head(repo_root),
    )
    return {"status": "CAB_STAGE1_COMMITTED", "receipt_sha256": receipt["receipt_sha256"]}


# --------------------------------------------------------------------------
# Stage 2
# --------------------------------------------------------------------------


def cmd_unlock_stage2(repo_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    workspace = _workspace(repo_root, args)
    commitment = read_json(repo_root / REPORT_DIR / "PUBLIC_PACKET_COMMITMENT.json")
    freeze = read_json(repo_root / REPORT_DIR / "SCIENTIFIC_FREEZE_V2.json")
    try:
        load_key(repo_root)
        key_available = True
    except VaultError:
        key_available = False
    receipt = workspace.unlock_stage2(
        packet_commitment=commitment["commitment_sha256"],
        scientific_freeze_sha256=freeze["freeze_sha256"],
        exact_commit=current_head(repo_root),
        key_available=key_available,
    )
    return {"status": "CAB_STAGE2_UNLOCKED", "receipt_sha256": receipt["receipt_sha256"]}


def cmd_generate_stage2_packages(repo_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    _require(args, "output_dir")
    workspace = _workspace(repo_root, args)
    workspace.read("stage2_unlock")
    private_root = workspace.private_root
    packet_commitment, freeze_sha256, exact_commit = _frozen_identity(repo_root)
    output = _outside_repo(repo_root, args.output_dir, "Stage-2 packages")
    hashes: dict[str, str] = {}
    with unlocked_workspace(prefix="cab-stage2-build-") as scratch:
        by_pair = _stage2_records(repo_root, private_root)
        for role in REVIEW_ROLES:
            mapping = _mappings(private_root)[role]
            files: dict[str, bytes] = {}
            applicability: dict[str, dict[str, bool]] = {}
            for item_id in sorted(mapping):
                record = by_pair[mapping[item_id]]
                shipped = dict(record)
                shipped["reviewer_item_id"] = item_id
                shipped.pop("pair_id", None)
                applicability[item_id] = dict(record["stage2_dimension_applicability"])
                files[f"items/{item_id}.json"] = (
                    json.dumps(shipped, indent=2, sort_keys=True) + "\n"
                ).encode()
            files["stage2_form.csv"] = stage2_form_template(sorted(mapping))
            files["applicability.json"] = (
                json.dumps(applicability, indent=2, sort_keys=True) + "\n"
            ).encode()
            files["STAGE2_REVIEWER_INSTRUCTIONS.md"] = STAGE2_REVIEWER_INSTRUCTIONS.encode()
            files["acceptance_policy.json"] = (
                json.dumps(acceptance_policy(), indent=2, sort_keys=True) + "\n"
            ).encode()
            payload = zip_bytes(files)
            target = output / f"stage2_{role.casefold()}.zip"
            target.write_bytes(payload)
            target.chmod(0o600)
            hashes[role] = sha256_bytes(payload)
        leftover = sorted(path.name for path in scratch.rglob("*") if path.is_file())
    # Issuance is what makes the hash mean something: nothing downstream accepts a
    # Stage-2 submission that is not backed by one of these sealed receipts.
    issuance: dict[str, str] = {}
    for role in REVIEW_ROLES:
        receipt = workspace.issue_stage2_package(
            role,
            package_sha256=hashes[role],
            packet_commitment=packet_commitment,
            scientific_freeze_sha256=freeze_sha256,
            exact_commit=exact_commit,
        )
        issuance[role] = receipt["receipt_sha256"]
    remaining = sorted(
        path.name
        for path in (private_root / "stage2").iterdir()
        if path.is_file() and path.suffix != ".enc"
    )
    return {
        "status": "CAB_STAGE2_PACKAGES_ISSUED",
        "package_hashes": hashes,
        "issuance_receipt_hashes": issuance,
        "issuance_schema_version": issuance_schema()["issuance_receipt_version"],
        "scratch_files_left_behind": leftover,
        "plaintext_beside_vault": remaining,
        "written_outside_repository": True,
    }


def cmd_ingest_stage2(repo_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    role = _role(args)
    _require(args, "submission", "package")
    workspace = _workspace(repo_root, args)
    private_root = workspace.private_root
    mapping = _mappings(private_root)[role]
    by_pair = _applicability_by_pair(repo_root, private_root)
    packet_commitment, freeze_sha256, exact_commit = _frozen_identity(repo_root)
    package = Path(args.package).expanduser()
    if not package.is_file():
        raise SystemExit(
            "--package must point at the exact Stage-2 archive this reviewer was issued"
        )
    receipt = workspace.ingest_stage2(
        role,
        Path(args.submission).read_bytes(),
        expected_item_ids=sorted(mapping),
        applicability={item_id: by_pair[pair_id] for item_id, pair_id in mapping.items()},
        package_sha256=sha256_bytes(package.read_bytes()),
        packet_commitment=packet_commitment,
        scientific_freeze_sha256=freeze_sha256,
        exact_commit=exact_commit,
    )
    return {
        "status": "STAGE2_SUBMISSION_RECORDED",
        "reviewer_role": role,
        "submission_sha256": receipt["submission_sha256"],
        "stage2_issuance_sha256": receipt["stage2_issuance_sha256"],
        "form_complete": receipt["form_complete"],
        "blocking_value_count": receipt["blocking_value_count"],
        "form_completion_is_not_approval": True,
    }


# --------------------------------------------------------------------------
# disagreement, adjudication, final records
# --------------------------------------------------------------------------


def cmd_build_stage1_disagreements(repo_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    workspace = _workspace(repo_root, args)
    receipt = workspace.build_stage1_disagreements(mappings=_mappings(workspace.private_root))
    return {
        "status": "CAB_STAGE1_DISAGREEMENT_QUEUE_BUILT",
        "pair_count": receipt["pair_count"],
        "disputed_pair_count": receipt["disputed_pair_count"],
        "disputed_dimension_count": receipt["disputed_dimension_count"],
        "next_step": "generate-stage1-adjudicator-package --output-dir <outside-repo>",
    }


def cmd_build_stage2_disagreements(repo_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    workspace = _workspace(repo_root, args)
    receipt = workspace.build_stage2_disagreements(
        mappings=_mappings(workspace.private_root),
        applicability=_applicability_by_pair(repo_root, workspace.private_root),
    )
    return {
        "status": "CAB_STAGE2_DISAGREEMENT_QUEUE_BUILT",
        "pair_count": receipt["pair_count"],
        "disputed_pair_count": receipt["disputed_pair_count"],
        "disputed_dimension_count": receipt["disputed_dimension_count"],
        "next_step": "generate-stage2-adjudicator-package --output-dir <outside-repo>",
    }


def _adjudicator_binding(
    repo_root: Path, workspace: ReviewWorkspace, *, stage: str, queue: dict[str, Any]
) -> dict[str, Any]:
    packet_commitment, freeze_sha256, exact_commit = _frozen_identity(repo_root)
    adjudicator = assignment_for_role(workspace.assignments(), ADJUDICATOR)
    reviewers = {
        str(assignment_for_role(workspace.assignments(), role)["reviewer_pseudonym"])
        for role in REVIEW_ROLES
    }
    if str(adjudicator["reviewer_pseudonym"]) in reviewers:
        raise SystemExit("the adjudicator must be independent of both reviewers")
    return package_binding(
        stage=stage,
        queue=queue,
        private_packet_commitment=packet_commitment,
        adjudicator_assignment_sha256=adjudicator["assignment_sha256"],
        adjudicator_pseudonym_sha256=sha256_json(adjudicator["reviewer_pseudonym"]),
        scientific_freeze_sha256=freeze_sha256,
        exact_commit=exact_commit,
        stage2_issuance_hashes=workspace._stage2_issuance_hashes(),
    )


def _write_adjudicator_package(
    repo_root: Path, args: argparse.Namespace, package: dict[str, Any]
) -> Path:
    output = _outside_repo(repo_root, args.output_dir, "adjudicator packages")
    target = output / package["filename"]
    target.write_bytes(package["package_bytes"])
    target.chmod(0o600)
    return target


def cmd_generate_stage1_adjudicator_package(
    repo_root: Path, args: argparse.Namespace
) -> dict[str, Any]:
    _require(args, "output_dir")
    workspace = _workspace(repo_root, args)
    private_root = workspace.private_root
    queue = workspace.read("stage1_disagreement_queue")
    mappings = _mappings(private_root)
    pairs = {pair.pair_id: pair for pair in load_pairs(private_root)}
    disputed = disputed_pair_ids(queue)
    views = {
        pair_id: stage1_item(pairs[pair_id], f"ADJ-{pair_id}")
        for pair_id in disputed
        if pair_id in pairs
    }
    package = build_stage1_adjudicator_package(
        queue=queue,
        stage1_views=views,
        paired_rows=workspace._paired(mappings, STAGE1),
        binding=_adjudicator_binding(repo_root, workspace, stage=STAGE1, queue=queue),
    )
    target = _write_adjudicator_package(repo_root, args, package)
    receipt = workspace.record_adjudicator_package(stage=STAGE1, package=package)
    return {
        "status": "CAB_STAGE1_ADJUDICATOR_PACKAGE_ISSUED",
        "package_filename": target.name,
        "package_sha256": package["package_sha256"],
        "disputed_item_count": len(package["disputed_pair_ids"]),
        "receipt_sha256": receipt["receipt_sha256"],
        "stage2_material_included": False,
        "written_outside_repository": True,
    }


def cmd_generate_stage2_adjudicator_package(
    repo_root: Path, args: argparse.Namespace
) -> dict[str, Any]:
    _require(args, "output_dir")
    workspace = _workspace(repo_root, args)
    private_root = workspace.private_root
    queue = workspace.read("stage2_disagreement_queue")
    mappings = _mappings(private_root)
    records = _stage2_records(repo_root, private_root)
    applicability = _applicability_by_pair(repo_root, private_root)
    disputed = set(disputed_pair_ids(queue))
    package = build_stage2_adjudicator_package(
        queue=queue,
        stage2_records={
            pair_id: record for pair_id, record in records.items() if pair_id in disputed
        },
        applicability={
            pair_id: row for pair_id, row in applicability.items() if pair_id in disputed
        },
        paired_rows=workspace._paired(mappings, STAGE2),
        binding=_adjudicator_binding(repo_root, workspace, stage=STAGE2, queue=queue),
    )
    target = _write_adjudicator_package(repo_root, args, package)
    receipt = workspace.record_adjudicator_package(stage=STAGE2, package=package)
    return {
        "status": "CAB_STAGE2_ADJUDICATOR_PACKAGE_ISSUED",
        "package_filename": target.name,
        "package_sha256": package["package_sha256"],
        "disputed_item_count": len(package["disputed_pair_ids"]),
        "receipt_sha256": receipt["receipt_sha256"],
        "non_disputed_items_included": False,
        "written_outside_repository": True,
    }


def _ingest_adjudication(repo_root: Path, args: argparse.Namespace, stage: str) -> dict[str, Any]:
    _require(args, "pseudonym", "decisions", "package")
    workspace = _workspace(repo_root, args)
    package = Path(args.package).expanduser()
    if not package.is_file():
        raise SystemExit(
            f"--package must point at the exact {PACKAGE_FILENAMES[stage]} the adjudicator was issued"
        )
    receipt = workspace.ingest_adjudication(
        stage=stage,
        adjudicator_pseudonym=args.pseudonym,
        decisions=json.loads(Path(args.decisions).read_text()),
        package_sha256=sha256_bytes(package.read_bytes()),
    )
    return {
        "status": f"CAB_{stage.upper()}_ADJUDICATION_RECORDED",
        "decision_count": receipt["decision_count"],
        "excluded_pair_count": len(receipt["excluded_pair_ids"]),
        "adjudicator_package_sha256": receipt["adjudicator_package_sha256"],
        "all_disputes_resolved": receipt["all_disputes_resolved"],
    }


def cmd_ingest_stage1_adjudication(repo_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    return _ingest_adjudication(repo_root, args, STAGE1)


def cmd_ingest_stage2_adjudication(repo_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    return _ingest_adjudication(repo_root, args, STAGE2)


def cmd_compute_agreement(repo_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    workspace = _workspace(repo_root, args)
    receipt = workspace.compute_agreement(mappings=_mappings(workspace.private_root))
    return {
        "status": "CAB_AGREEMENT_COMPUTED",
        "computed_from": receipt["computed_from"],
        "adjudicated_values_used": receipt["adjudicated_values_used"],
        "stage1_overall_raw_agreement": receipt["stage1"]["overall_raw_agreement"],
        "stage2_overall_raw_agreement": receipt["stage2"]["overall_raw_agreement"],
        "stage1_per_dimension": receipt["stage1"]["per_dimension"],
        "stage2_per_dimension": receipt["stage2"]["per_dimension"],
    }


def cmd_build_final_adjudicated_records(
    repo_root: Path, args: argparse.Namespace
) -> dict[str, Any]:
    workspace = _workspace(repo_root, args)
    contract = read_json(repo_root / "configs/human_validation/c10_contract_v2.json")
    receipt = workspace.build_final_adjudicated_records(
        mappings=_mappings(workspace.private_root),
        applicability=_applicability_by_pair(repo_root, workspace.private_root),
        expected_pair_count=int(contract["expected_pair_count"]),
    )
    return {
        "status": "CAB_FINAL_ADJUDICATED_RECORDS_BUILT"
        if receipt["passed"]
        else "CAB_FINAL_ADJUDICATED_RECORDS_INCOMPLETE",
        "record_count": receipt["record_count"],
        "included_count": receipt["included_count"],
        "excluded_count": receipt["excluded_count"],
        "provenance_counts": receipt["provenance_counts"],
        "unresolved_count": len(receipt["unresolved"]),
        "checks": receipt["checks"],
    }


# --------------------------------------------------------------------------
# C10, slice lock, execution authorization
# --------------------------------------------------------------------------


def cmd_run_c10(repo_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    workspace = _workspace(repo_root, args)
    contract = read_json(repo_root / "configs/human_validation/c10_contract_v2.json")
    commitment = read_json(repo_root / REPORT_DIR / "PUBLIC_PACKET_COMMITMENT.json")
    freeze = read_json(repo_root / REPORT_DIR / "SCIENTIFIC_FREEZE_V2.json")
    report = run_c10(
        workspace,
        contract=contract,
        mappings=_mappings(workspace.private_root),
        applicability=_applicability_by_pair(repo_root, workspace.private_root),
        prerequisites={
            "retired_packet_registry_enforced": retirement_enforcement_report()["passed"],
            "retired_qualification_registry_enforced": bool(
                retired_qualification_registry()["retired_versions"]
            ),
            "qualification_version_matches_contract": contract["required_qualification_version"]
            == QUALIFICATION_SCHEMA_VERSION,
            "stage2_issuance_schema_matches_contract": contract["required_stage2_issuance_schema"]
            == issuance_schema()["issuance_receipt_version"],
            "adjudicator_package_schemas_match_contract": (
                contract["required_stage1_adjudicator_package_schema"]
                == STAGE1_PACKAGE_SCHEMA_VERSION
                and contract["required_stage2_adjudicator_package_schema"]
                == STAGE2_PACKAGE_SCHEMA_VERSION
                and contract["required_adjudicator_package_binding_schema"]
                == BINDING_SCHEMA_VERSION
            ),
            "scientific_freeze_v2": verify_freeze(repo_root)["passed"],
        },
        packet_commitment=commitment["commitment_sha256"],
        scientific_freeze_sha256=freeze["freeze_sha256"],
    )
    workspace.write("c10_report", report)
    return {
        "status": report["status"],
        "failed_checks": report["failed_checks"],
        "included_count": report["included_count"],
        "excluded_count": report["excluded_count"],
    }


def cmd_build_exclusion_register(repo_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    receipt = build_exclusion_register(_workspace(repo_root, args))
    return {
        "status": "CAB_EXCLUSION_REGISTER_BUILT",
        "included_count": receipt["included_count"],
        "excluded_count": receipt["excluded_count"],
    }


def cmd_lock_reviewed_slice(repo_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    workspace = _workspace(repo_root, args)
    c10 = workspace.read("c10_report")
    commitment = read_json(repo_root / REPORT_DIR / "PUBLIC_PACKET_COMMITMENT.json")
    freeze = read_json(repo_root / REPORT_DIR / "SCIENTIFIC_FREEZE_V2.json")
    receipt = lock_reviewed_slice(
        workspace,
        c10_report=c10,
        packet_commitment=commitment["commitment_sha256"],
        scorer_sha256=freeze["frozen_configs"]["scorer"]["sha256"],
        endpoints_sha256=freeze["frozen_configs"]["endpoints"]["sha256"],
        analysis_plan_sha256=freeze["frozen_configs"]["analysis_plan"]["sha256"],
        system_identity_sha256=freeze["frozen_configs"]["system_identity_schema"]["sha256"],
        scientific_freeze_sha256=freeze["freeze_sha256"],
        exact_commit=current_head(repo_root),
    )
    return {
        "status": "CAB_REVIEWED_SLICE_LOCKED",
        "included_count": len(receipt["included_pair_ids"]),
    }


def cmd_authorize_model_execution(repo_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    workspace = _workspace(repo_root, args)
    freeze = read_json(repo_root / REPORT_DIR / "SCIENTIFIC_FREEZE_V2.json")
    attestation = verify_attestation(repo_root, _attestation_path(repo_root, args))
    receipt = authorize_model_execution(
        workspace,
        exact_commit=current_head(repo_root),
        scientific_freeze_sha256=freeze["freeze_sha256"],
        external_attestation_present=bool(attestation.get("passed")),
    )
    return {
        "status": "CAB_MODEL_EXECUTION_AUTHORIZED",
        "receipt_sha256": receipt["receipt_sha256"],
    }


def cmd_status(repo_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    """Dry-run status.  Reveals stage completion only, never private content."""

    private_root = _private_root(repo_root, args)
    try:
        workspace = _workspace(repo_root, args)
        status = workflow_status(workspace)
    except (ReceiptError, WorkflowError) as error:
        status = {
            "schema_version": "cab_review_ready_v2_workflow_status_v2",
            "artifact_origin": "UNAVAILABLE",
            "reason": str(error),
            "c10_status": "C10_PENDING_GENUINE_REVIEW",
            "model_execution": "MODEL_EXECUTION_BLOCKED",
        }
    return {
        **status,
        "packet_version": PACKET_VERSION,
        "external_keys_configured": {
            KEY_ENV: _key_configured(repo_root, KEY_ENV),
            QUALIFICATION_KEY_ENV: _key_configured(repo_root, QUALIFICATION_KEY_ENV),
            COORDINATOR_KEY_ENV: coordinator_key_available(repo_root),
        },
        "private_root_present": private_root.is_dir(),
        "genuine_human_judgments": 0,
        "genuine_model_trajectories": 0,
    }


def _key_configured(repo_root: Path, env_var: str) -> bool:
    from causal_agent_bench.review_ready_v2.keys import external_key_available

    return external_key_available(env_var, repo_root)


def cmd_coordinator_checklist(repo_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    return {
        "status": "CAB_COORDINATOR_CHECKLIST",
        "canonical_roles": list(CANONICAL_ROLES),
        "external_keys": {
            "CAB_PACKET_SEED_PATH": "private packet generation seed",
            KEY_ENV: "Stage-2 vault key",
            QUALIFICATION_KEY_ENV: "qualification answer key",
            COORDINATOR_KEY_ENV: "coordinator acceptance key that seals production receipts",
        },
        "private_material_authored_outside_git": {
            QUALIFICATION_SOURCE_ENV: (
                "privately authored qualification items and answers; see "
                "qualification-source-schema"
            ),
        },
        "ordered_steps": [
            "qualification-source-schema  # then author the source outside Git",
            "validate-qualification-source",
            "generate-private-packet",
            "validate-private-packet",
            "generate-stage1-packages",
            "generate-private-qualification-packages",
            "validate-stage1-packages",
            "create-reviewer-assignment --role REVIEWER_A --pseudonym <pseudonym>",
            "create-reviewer-assignment --role REVIEWER_B --pseudonym <pseudonym>",
            "create-reviewer-assignment --role ADJUDICATOR --pseudonym <pseudonym>",
            "ingest-reviewer-declaration --role REVIEWER_A --declaration <file>",
            "ingest-reviewer-declaration --role REVIEWER_B --declaration <file>",
            "accept-reviewer-declaration --role <role> --decision ACCEPTED --rationale <text>",
            "score-private-qualification --role <role> --submission <file>",
            "ingest-stage1 --role <role> --submission <file>",
            "commit-stage1",
            "unlock-stage2",
            "generate-stage2-packages --output-dir <outside-repo>",
            "ingest-stage2 --role <role> --submission <file> --package <issued-stage2-zip>",
            "build-stage1-disagreements",
            "generate-stage1-adjudicator-package --output-dir <outside-repo>",
            "build-stage2-disagreements",
            "generate-stage2-adjudicator-package --output-dir <outside-repo>",
            "ingest-stage1-adjudication --pseudonym <pseudonym> --decisions <file> --package <zip>",
            "ingest-stage2-adjudication --pseudonym <pseudonym> --decisions <file> --package <zip>",
            "build-final-adjudicated-records",
            "compute-agreement",
            "run-c10",
            "build-exclusion-register",
            "lock-reviewed-slice",
            "authorize-model-execution",
        ],
        "rules": [
            "Never edit a receipt, a registry, or a queue by hand; every one is content-bound.",
            "accept-reviewer-declaration is required only when a reviewer disclosed a conflict.",
            "Stage-2 material must never be sent before commit-stage1 and unlock-stage2 succeed.",
            "A complete Stage-2 form is not an approval; adjudicate every NO and every UNSURE.",
            (
                "Every Stage-2 submission must be ingested against the exact archive that was "
                "issued to that reviewer; a modified or swapped archive is refused."
            ),
            (
                "Rebuild a disagreement queue and the matching adjudicator package must be "
                "reissued; an adjudication against the stale package is refused."
            ),
            (
                "The qualification source is private material. Author it outside Git, never "
                "commit it, and never quote an item or an expected value in a report."
            ),
            "No genuine review has occurred. C10 has not passed. Model execution is blocked.",
        ],
    }


# --------------------------------------------------------------------------
# audits, freeze, reports
# --------------------------------------------------------------------------


def cmd_fixture_e2e(repo_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    result = run_fixture_e2e()
    write_json(repo_root / REPORT_DIR / "FIXTURE_E2E_WORKFLOW.json", result)
    return {"status": result["status"], "step_count": result["step_count"]}


def cmd_verify_freeze(repo_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    return verify_freeze(repo_root)


def cmd_verify_provenance(repo_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    """Prove the recorded generator provenance resolves from the branch alone."""

    manifest_path = repo_root / REPORT_DIR / "SCIENTIFIC_FREEZE_V2.json"
    recorded = read_json(manifest_path)["generator"] if manifest_path.is_file() else {}
    live = generator_provenance(repo_root)
    checks = {
        "recorded_commit_is_ancestor_of_head": bool(recorded.get("commit_is_ancestor_of_head"))
        and live["commit_is_ancestor_of_head"],
        "recorded_commit_resolves": bool(recorded.get("commit_resolves")),
        "recorded_commit_matches_live_resolution": recorded.get("source_commit")
        == live["source_commit"],
        "generator_content_matches": live["commit_content_matches"],
        "generator_blobs_present": live["generator_blobs_present"],
        "needs_no_unreachable_objects": live["requires_unreachable_objects"] is False,
    }
    return {
        "status": "CAB_GENERATOR_PROVENANCE_PORTABLE"
        if all(checks.values())
        else "CAB_GENERATOR_PROVENANCE_NOT_PORTABLE",
        "head": current_head(repo_root),
        "source_commit": live["source_commit"],
        "checks": checks,
        "passed": all(checks.values()),
    }


def _distribution_schemas() -> dict[str, Any]:
    """The reviewer-distribution contracts, published as shape without content."""

    return {
        "schema_version": "cab_reviewer_distribution_schemas_v1",
        "status": "CAB_REVIEWER_DISTRIBUTION_SCHEMAS_PUBLISHED",
        "qualification_source": qualification_source_schema(),
        "stage2_issuance": issuance_schema(),
        "adjudicator_packages": {
            "schema_version": "cab_adjudicator_package_schema_v1",
            "stage1_package_schema_version": STAGE1_PACKAGE_SCHEMA_VERSION,
            "stage2_package_schema_version": STAGE2_PACKAGE_SCHEMA_VERSION,
            "binding_schema_version": BINDING_SCHEMA_VERSION,
            "binding_fields": list(BINDING_FIELDS),
            "package_filenames": dict(PACKAGE_FILENAMES),
            "stage1_withholds_stage2_material": sorted(STAGE2_ONLY_KEYS),
            "stage2_required_evidence": list(STAGE2_REQUIRED_EVIDENCE),
            "stage2_conditional_evidence": list(STAGE2_CONDITIONAL_EVIDENCE),
            "disputed_items_only": True,
            "adjudicator_must_be_neither_reviewer": True,
        },
        "private_content_disclosed": False,
    }


def cmd_build_reports(repo_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    private_root = _private_root(repo_root, args)
    pairs = load_pairs(private_root)
    design = design_audit(pairs)
    isolation = [
        isolation_audit(pair.clean_environment, pair.intervention_environment, pair.intervention_patch)
        for pair in pairs
    ]
    routes = [validate_pair_routes(pair) for pair in pairs]
    hostile = hostile_route_audit(pairs)
    packages: dict[str, bytes] = {}
    for role in REVIEW_ROLES:
        packages[package_basename(role)] = (
            private_root / "stage1" / f"{package_basename(role)}.zip"
        ).read_bytes()
        packages[f"qualification_{role.casefold()}"] = _qualification_package_path(
            private_root, role
        ).read_bytes()
    leakage = stage1_leakage_audit(packages, pairs, _mappings_by_basename(private_root))
    usability = usability_audit(packages)
    vault = vault_status(private_root / "stage2" / "stage2_vault.enc", repo_root)
    fixture = run_fixture_e2e()
    retirement = retirement_enforcement_report()
    power = build_power_plan(replicates=int(args.power_replicates))

    report_dir = repo_root / REPORT_DIR
    write_json(report_dir / "RETIRED_PACKET_REGISTRY.json", retired_packet_registry())
    write_json(report_dir / "RETIRED_QUALIFICATION_REGISTRY.json", retired_qualification_registry())
    write_json(report_dir / "ACTIVE_PATH_REGISTRY.json", active_path_registry(repo_root))
    write_json(report_dir / "REVIEWER_DISTRIBUTION_SCHEMAS.json", _distribution_schemas())
    write_json(report_dir / "RETIREMENT_ENFORCEMENT.json", retirement)
    write_json(report_dir / "DESIGN_AUDIT.json", public_design_summary(design))
    write_json(report_dir / "INTERVENTION_ISOLATION_AUDIT.json", public_isolation_summary(isolation))
    write_json(report_dir / "CAUSAL_ROUTE_AUDIT.json", public_route_summary(routes))
    write_json(report_dir / "HOSTILE_ROUTE_AUDIT.json", public_hostile_summary(hostile))
    write_json(report_dir / "STAGE1_LEAKAGE_AUDIT.json", public_leakage_summary(leakage))
    write_json(report_dir / "STAGE1_PACKAGE_RECEIPT.json", usability)
    write_json(report_dir / "STAGE2_VAULT_STATUS.json", vault)
    write_json(report_dir / "STAGE2_ACCEPTANCE_POLICY.json", acceptance_policy())
    write_json(report_dir / "FIXTURE_E2E_WORKFLOW.json", fixture)
    write_json(report_dir / "ATTESTATION_POLICY.json", attestation_policy())
    write_json(repo_root / "configs/reviewer_ready_v2/power_plan_v2.json", power)
    write_json(
        repo_root / "configs/reviewer_ready_v2/stage2_acceptance_policy_v1.json",
        acceptance_policy(),
    )

    commitment = read_json(report_dir / "PUBLIC_PACKET_COMMITMENT.json")
    freeze = build_freeze(repo_root, generator_commit=args.generator_commit)
    write_json(report_dir / "SCIENTIFIC_FREEZE_V2.json", freeze)
    freeze_check = verify_freeze(repo_root)
    provenance = cmd_verify_provenance(repo_root, args)
    write_json(report_dir / "GENERATOR_PROVENANCE.json", provenance)
    # The path registry names the freeze, so it can only be verified once the
    # freeze file exists on disk.
    paths = verify_active_paths(repo_root)
    attestation = verify_attestation(repo_root, _attestation_path(repo_root, args))

    readiness = build_readiness_report(
        commitment=commitment,
        design=public_design_summary(design),
        isolation=public_isolation_summary(isolation),
        routes=public_route_summary(routes),
        hostile=public_hostile_summary(hostile),
        leakage=public_leakage_summary(leakage),
        usability=usability,
        vault=vault,
        fixture=fixture,
        retirement=retirement,
        paths=paths,
        power=power,
        freeze=freeze_check,
        attestation=attestation,
    )
    write_json(report_dir / "REVIEWER_READINESS_REPORT.json", readiness)
    (report_dir / "REVIEWER_READINESS_REPORT.md").write_text(readiness_markdown(readiness))
    return {
        "status": readiness["status"],
        "blocking_gates": readiness["blocking_gates"],
        "freeze_sha256": freeze["freeze_sha256"],
        "generator_provenance": provenance["status"],
    }


def _attestation_path(repo_root: Path, args: argparse.Namespace) -> Path | None:
    if getattr(args, "attestation", None):
        return Path(args.attestation).expanduser()
    directory = Path(os.environ.get("CAB_ATTESTATION_DIR", "~/.cab/attestations")).expanduser()
    candidate = directory / f"cab-review-ready-v2-{current_head(repo_root)}.json"
    return candidate if candidate.is_file() else None


def cmd_verify_attestation(repo_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    return verify_attestation(repo_root, _attestation_path(repo_root, args))


def cmd_new_seed(repo_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    return {
        "seed_hex": secrets.token_hex(32),
        "store_at": "an owner-only file outside the repository, referenced by CAB_PACKET_SEED_PATH",
        "never_commit": True,
    }


COMMANDS = {
    # packet
    "generate-private-packet": cmd_generate_private_packet,
    "validate-private-packet": cmd_validate_private_packet,
    "generate-stage1-packages": cmd_generate_stage1_packages,
    "qualification-source-schema": cmd_qualification_source_schema,
    "validate-qualification-source": cmd_validate_qualification_source,
    "generate-private-qualification-packages": cmd_generate_private_qualification_packages,
    "validate-stage1-packages": cmd_validate_stage1_packages,
    # reviewer provenance
    "create-reviewer-assignment": cmd_create_reviewer_assignment,
    "show-reviewer-assignments": cmd_show_reviewer_assignments,
    "ingest-reviewer-declaration": cmd_ingest_reviewer_declaration,
    "accept-reviewer-declaration": cmd_accept_reviewer_declaration,
    "score-private-qualification": cmd_score_private_qualification,
    # stage 1
    "ingest-stage1": cmd_ingest_stage1,
    "commit-stage1": cmd_commit_stage1,
    # stage 2
    "unlock-stage2": cmd_unlock_stage2,
    "generate-stage2-packages": cmd_generate_stage2_packages,
    "ingest-stage2": cmd_ingest_stage2,
    # disagreement and adjudication
    "build-stage1-disagreements": cmd_build_stage1_disagreements,
    "build-stage2-disagreements": cmd_build_stage2_disagreements,
    "generate-stage1-adjudicator-package": cmd_generate_stage1_adjudicator_package,
    "generate-stage2-adjudicator-package": cmd_generate_stage2_adjudicator_package,
    "ingest-stage1-adjudication": cmd_ingest_stage1_adjudication,
    "ingest-stage2-adjudication": cmd_ingest_stage2_adjudication,
    "build-final-adjudicated-records": cmd_build_final_adjudicated_records,
    "compute-agreement": cmd_compute_agreement,
    # C10 and execution
    "run-c10": cmd_run_c10,
    "build-exclusion-register": cmd_build_exclusion_register,
    "lock-reviewed-slice": cmd_lock_reviewed_slice,
    "authorize-model-execution": cmd_authorize_model_execution,
    # status, audits, freeze
    "status": cmd_status,
    "coordinator-checklist": cmd_coordinator_checklist,
    "fixture-e2e": cmd_fixture_e2e,
    "verify-freeze": cmd_verify_freeze,
    "verify-provenance": cmd_verify_provenance,
    "verify-attestation": cmd_verify_attestation,
    "build-reports": cmd_build_reports,
    "new-seed": cmd_new_seed,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cab-review-ready-v2",
        description=(
            "Reviewer-ready V2 packet and two-stage human-review workflow. No command performs "
            "model execution or genuine human review. No genuine review has occurred, C10 has "
            "not passed, and model execution is blocked."
        ),
    )
    parser.add_argument("command", choices=sorted(COMMANDS))
    parser.add_argument("--private-root", default=None, help="override the private packet root")
    parser.add_argument("--seed", default=None, help="private generation seed (hex)")
    parser.add_argument(
        "--role",
        default=None,
        help="canonical reviewer role: REVIEWER_A, REVIEWER_B or ADJUDICATOR",
    )
    parser.add_argument(
        "--pseudonym", default=None, help="reviewer pseudonym, as recorded in the private registry"
    )
    parser.add_argument("--declaration", default=None, help="path to a signed reviewer declaration")
    parser.add_argument("--decision", default=None, help="ACCEPTED or REJECTED")
    parser.add_argument("--rationale", default=None, help="coordinator rationale for a decision")
    parser.add_argument("--submission", default=None, help="path to a reviewer submission file")
    parser.add_argument("--decisions", default=None, help="path to an adjudication decision file")
    parser.add_argument(
        "--package",
        default=None,
        help=(
            "path to the exact issued archive a submission answers: the reviewer's Stage-2 ZIP, "
            "or the adjudicator package for this stage"
        ),
    )
    parser.add_argument("--output-dir", default=None, help="where packages are written")
    parser.add_argument("--attestation", default=None, help="path to the external attestation")
    parser.add_argument("--generator-commit", default=None)
    # Matches the replicate count the tracked power plan was generated with, so
    # `build-reports` reproduces the committed artifact byte-for-byte by default.
    parser.add_argument("--power-replicates", default=1200)
    parser.add_argument(
        "--fixture",
        action="store_true",
        help=(
            "operate in the synthetic fixture namespace. Fixture artifacts are sealed by a public "
            "authority and can never satisfy a production gate."
        ),
    )
    return parser


def main(argv: list[str] | None = None, *, repo_root: Path | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = repo_root or Path(__file__).resolve().parents[3]
    try:
        _emit(COMMANDS[args.command](root, args))
    except (
        AssignmentError,
        DeclarationError,
        ExternalKeyError,
        QualificationError,
        ReceiptError,
        RoleError,
        VaultError,
        ValueError,
        RuntimeError,
        KeyError,
    ) as error:
        _emit({"status": "REFUSED", "command": args.command, "reason": str(error)})
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())


__all__ = ["COMMANDS", "KEY_ENV", "build_parser", "main"]
