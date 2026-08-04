"""Canonical CLI for the reviewer-ready V2 packet and two-stage review workflow.

Output is always public-safe: statuses, counts and hashes.  No command prints a
prompt, a record, an answer, a route label, a private identifier, or Stage-2
content, and no command performs model execution or genuine human review.
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
from causal_agent_bench.review_ready_v2.common import read_json, sha256_bytes, write_json
from causal_agent_bench.review_ready_v2.design import design_audit
from causal_agent_bench.review_ready_v2.fixture_e2e import run_fixture_e2e
from causal_agent_bench.review_ready_v2.freeze import (
    attestation_policy,
    build_freeze,
    current_head,
    verify_attestation,
    verify_freeze,
)
from causal_agent_bench.review_ready_v2.hostile import hostile_route_audit
from causal_agent_bench.review_ready_v2.leakage import stage1_leakage_audit, usability_audit
from causal_agent_bench.review_ready_v2.operators import isolation_audit
from causal_agent_bench.review_ready_v2.packet import build_packet, load_pairs, private_root_for
from causal_agent_bench.review_ready_v2.power import build_power_plan
from causal_agent_bench.review_ready_v2.qualification import build_qualification_package
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
from causal_agent_bench.review_ready_v2.routes import validate_pair_routes
from causal_agent_bench.review_ready_v2.stage1 import build_stage1_package, zip_bytes
from causal_agent_bench.review_ready_v2.vault import (
    KEY_ENV,
    VaultError,
    load_key,
    unlocked_workspace,
    unseal,
    vault_status,
)
from causal_agent_bench.review_ready_v2.workflow import (
    STAGE2_FORM_COLUMNS,
    ReviewWorkspace,
    authorize_model_execution,
    build_exclusion_register,
    lock_reviewed_slice,
    parse_review_csv,
    run_c10,
    validate_stage1_submission,
    validate_stage2_submission,
    workflow_status,
)

REPORT_DIR = "reports/reviewer_ready_v2"
REVIEWERS = ("stage1_reviewer_a", "stage1_reviewer_b")


def _emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


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


def _mappings(private_root: Path) -> dict[str, dict[str, str]]:
    mappings: dict[str, dict[str, str]] = {}
    for role in REVIEWERS:
        path = private_root / "mappings" / f"{role}_mapping.json"
        if path.is_file():
            mappings[role] = read_json(path)["reviewer_item_to_pair"]
    return mappings


def _workspace(repo_root: Path, args: argparse.Namespace) -> ReviewWorkspace:
    root = Path(args.private_root) if args.private_root else private_root_for(repo_root)
    return ReviewWorkspace(root, fixture=bool(getattr(args, "fixture", False)))


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
    private_root = Path(args.private_root) if args.private_root else private_root_for(repo_root)
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
    private_root = Path(args.private_root) if args.private_root else private_root_for(repo_root)
    pairs = load_pairs(private_root)
    hashes: dict[str, str] = {}
    for role in REVIEWERS:
        payload, mapping, _ = build_stage1_package(pairs, seed, role)
        target = private_root / "stage1" / f"{role}.zip"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
        target.chmod(0o600)
        write_json(private_root / "mappings" / f"{role}_mapping.json", {"reviewer_item_to_pair": mapping})
        hashes[f"{role}.zip"] = sha256_bytes(payload)
    qualification = build_qualification_package()
    (private_root / "qualification" / "qualification_packet.zip").write_bytes(qualification)
    return {
        "status": "CAB_STAGE1_PACKAGES_READY",
        "stage1_package_hashes": hashes,
        "qualification_package_sha256": sha256_bytes(qualification),
    }


def cmd_validate_stage1_packages(repo_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    private_root = Path(args.private_root) if args.private_root else private_root_for(repo_root)
    pairs = load_pairs(private_root)
    packages = {
        role: (private_root / "stage1" / f"{role}.zip").read_bytes()
        for role in REVIEWERS
        if (private_root / "stage1" / f"{role}.zip").is_file()
    }
    qualification_path = private_root / "qualification" / "qualification_packet.zip"
    if qualification_path.is_file():
        packages["qualification_packet"] = qualification_path.read_bytes()
    leakage = stage1_leakage_audit(packages, pairs, _mappings(private_root))
    usability = usability_audit(packages)
    return {
        "leakage": public_leakage_summary(leakage),
        "usability": usability,
        "passed": leakage["passed"] and usability["passed"],
    }


# --------------------------------------------------------------------------
# two-stage workflow
# --------------------------------------------------------------------------


def cmd_ingest_reviewer_qualification(repo_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    workspace = _workspace(repo_root, args)
    submission = read_json(Path(args.submission))
    receipt = workspace.ingest_qualification(args.reviewer_id, submission)
    return {"status": "REVIEWER_QUALIFIED", "receipt_sha256": receipt["receipt_sha256"]}


def cmd_ingest_stage1(repo_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    workspace = _workspace(repo_root, args)
    private_root = workspace.private_root
    mapping = _mappings(private_root)[args.package_role]
    package = (private_root / "stage1" / f"{args.package_role}.zip").read_bytes()
    receipt = workspace.ingest_stage1(
        args.reviewer_id,
        Path(args.submission).read_bytes(),
        expected_item_ids=sorted(mapping),
        package_sha256=sha256_bytes(package),
    )
    return {"status": "STAGE1_SUBMISSION_RECORDED", "submission_sha256": receipt["submission_sha256"]}


def cmd_validate_stage1_submissions(repo_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    private_root = (
        Path(args.private_root) if args.private_root else private_root_for(repo_root)
    )
    mappings = _mappings(private_root)
    rows = parse_review_csv(Path(args.submission).read_bytes(), tuple(_stage1_columns()))
    validation = validate_stage1_submission(rows, sorted(mappings[args.package_role]))
    return {"status": "STAGE1_SUBMISSION_VALID" if validation["passed"] else "STAGE1_SUBMISSION_INVALID", **validation}


def _stage1_columns() -> list[str]:
    from causal_agent_bench.review_ready_v2.stage1 import REVIEW_FORM_COLUMNS

    return list(REVIEW_FORM_COLUMNS)


def cmd_commit_stage1(repo_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    workspace = _workspace(repo_root, args)
    commitment = read_json(repo_root / REPORT_DIR / "PUBLIC_PACKET_COMMITMENT.json")
    freeze = read_json(repo_root / REPORT_DIR / "SCIENTIFIC_FREEZE_V2.json")
    receipt = workspace.commit_stage1(
        reviewer_ids=(args.reviewer_a, args.reviewer_b),
        packet_commitment=commitment["commitment_sha256"],
        package_hashes=commitment["stage1_package_hashes"],
        review_schema_version="cab_stage1_review_form_v2",
        scientific_freeze_sha256=freeze["freeze_sha256"],
        exact_commit=current_head(repo_root),
    )
    return {"status": "CAB_STAGE1_COMMITTED", "receipt_sha256": receipt["receipt_sha256"]}


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
    workspace = _workspace(repo_root, args)
    workspace.read("stage2_unlock")
    private_root = workspace.private_root
    _, key = load_key(repo_root)
    vault = (private_root / "stage2" / "stage2_vault.enc").read_bytes()
    output = Path(args.output_dir).expanduser()
    if str(output.resolve()).startswith(str(repo_root.resolve())):
        raise SystemExit("Stage-2 packages must be written outside the repository root")
    output.mkdir(parents=True, exist_ok=True)
    output.chmod(0o700)
    hashes: dict[str, str] = {}
    with unlocked_workspace(prefix="cab-stage2-build-") as scratch:
        records = unseal(vault, key)
        by_pair = {str(row["pair_id"]): row for row in records}
        for role in REVIEWERS:
            mapping = _mappings(private_root)[role]
            files: dict[str, bytes] = {}
            rows = [",".join(STAGE2_FORM_COLUMNS)]
            for item_id in sorted(mapping):
                record = by_pair[mapping[item_id]]
                shipped = dict(record)
                shipped["reviewer_item_id"] = item_id
                shipped.pop("pair_id", None)
                files[f"items/{item_id}.json"] = (
                    json.dumps(shipped, indent=2, sort_keys=True) + "\n"
                ).encode()
                rows.append(item_id + "," * (len(STAGE2_FORM_COLUMNS) - 1))
            files["stage2_form.csv"] = ("\n".join(rows) + "\n").encode()
            payload = zip_bytes(files)
            target = output / f"stage2_{role}.zip"
            target.write_bytes(payload)
            target.chmod(0o600)
            hashes[target.name] = sha256_bytes(payload)
        leftover = sorted(path.name for path in scratch.rglob("*") if path.is_file())
    remaining = sorted(
        path.name
        for path in (private_root / "stage2").iterdir()
        if path.is_file() and path.suffix != ".enc"
    )
    return {
        "status": "CAB_STAGE2_PACKAGES_GENERATED",
        "package_hashes": hashes,
        "scratch_files_left_behind": leftover,
        "plaintext_beside_vault": remaining,
        "written_outside_repository": True,
    }


def cmd_ingest_stage2(repo_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    workspace = _workspace(repo_root, args)
    mapping = _mappings(workspace.private_root)[args.package_role]
    receipt = workspace.ingest_stage2(
        args.reviewer_id, Path(args.submission).read_bytes(), expected_item_ids=sorted(mapping)
    )
    return {"status": "STAGE2_SUBMISSION_RECORDED", "submission_sha256": receipt["submission_sha256"]}


def cmd_validate_stage2_submissions(repo_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    private_root = Path(args.private_root) if args.private_root else private_root_for(repo_root)
    mapping = _mappings(private_root)[args.package_role]
    rows = parse_review_csv(Path(args.submission).read_bytes(), STAGE2_FORM_COLUMNS)
    validation = validate_stage2_submission(rows, sorted(mapping))
    return {
        "status": "STAGE2_SUBMISSION_VALID" if validation["passed"] else "STAGE2_SUBMISSION_INVALID",
        **validation,
    }


def cmd_build_disagreement_queue(repo_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    workspace = _workspace(repo_root, args)
    receipt = workspace.build_disagreement_queue(
        reviewer_ids=(args.reviewer_a, args.reviewer_b), mappings=_mappings(workspace.private_root)
    )
    return {
        "status": "CAB_DISAGREEMENT_QUEUE_BUILT",
        "pair_count": receipt["pair_count"],
        "disputed_pair_count": receipt["disputed_pair_count"],
    }


def cmd_ingest_adjudication(repo_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    workspace = _workspace(repo_root, args)
    decisions = json.loads(Path(args.decisions).read_text())
    receipt = workspace.ingest_adjudication(
        adjudicator_id=args.adjudicator_id,
        decisions=decisions,
        reviewer_ids=(args.reviewer_a, args.reviewer_b),
    )
    return {"status": "CAB_ADJUDICATION_RECORDED", "decision_count": receipt["decision_count"]}


def cmd_compute_agreement(repo_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    workspace = _workspace(repo_root, args)
    receipt = workspace.compute_agreement(
        reviewer_ids=(args.reviewer_a, args.reviewer_b), mappings=_mappings(workspace.private_root)
    )
    return {
        "status": "CAB_AGREEMENT_COMPUTED",
        "overall_raw_agreement": receipt["overall_raw_agreement"],
        "per_dimension": receipt["per_dimension"],
    }


def cmd_run_c10(repo_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    workspace = _workspace(repo_root, args)
    contract = read_json(repo_root / "configs/human_validation/c10_contract_v2.json")
    commitment = read_json(repo_root / REPORT_DIR / "PUBLIC_PACKET_COMMITMENT.json")
    freeze = read_json(repo_root / REPORT_DIR / "SCIENTIFIC_FREEZE_V2.json")
    report = run_c10(
        workspace,
        contract=contract,
        reviewer_ids=(args.reviewer_a, args.reviewer_b),
        mappings=_mappings(workspace.private_root),
        prerequisites={
            "retired_packet_registry_enforced": retirement_enforcement_report()["passed"],
            "scientific_freeze_v2": verify_freeze(repo_root)["passed"],
        },
        packet_commitment=commitment["commitment_sha256"],
        scientific_freeze_sha256=freeze["freeze_sha256"],
    )
    workspace.write("c10_report", report)
    return {"status": report["status"], "failed_checks": report["failed_checks"]}


def cmd_build_exclusion_register(repo_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    workspace = _workspace(repo_root, args)
    receipt = build_exclusion_register(
        workspace, reviewer_ids=(args.reviewer_a, args.reviewer_b), mappings=_mappings(workspace.private_root)
    )
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
    return {"status": "CAB_REVIEWED_SLICE_LOCKED", "included_count": len(receipt["included_pair_ids"])}


def cmd_authorize_model_execution(repo_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    workspace = _workspace(repo_root, args)
    freeze = read_json(repo_root / REPORT_DIR / "SCIENTIFIC_FREEZE_V2.json")
    receipt = authorize_model_execution(
        workspace, exact_commit=current_head(repo_root), scientific_freeze_sha256=freeze["freeze_sha256"]
    )
    return {"status": "CAB_MODEL_EXECUTION_AUTHORIZED", "receipt_sha256": receipt["receipt_sha256"]}


def cmd_status(repo_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    workspace = _workspace(repo_root, args)
    return workflow_status(workspace)


# --------------------------------------------------------------------------
# audits, freeze, reports
# --------------------------------------------------------------------------


def cmd_fixture_e2e(repo_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    result = run_fixture_e2e()
    write_json(repo_root / REPORT_DIR / "FIXTURE_E2E_WORKFLOW.json", result)
    return {"status": result["status"], "step_count": result["step_count"]}


def cmd_verify_freeze(repo_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    return verify_freeze(repo_root)


def cmd_build_reports(repo_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    private_root = Path(args.private_root) if args.private_root else private_root_for(repo_root)
    pairs = load_pairs(private_root)
    design = design_audit(pairs)
    isolation = [
        isolation_audit(pair.clean_environment, pair.intervention_environment, pair.intervention_patch)
        for pair in pairs
    ]
    routes = [validate_pair_routes(pair) for pair in pairs]
    hostile = hostile_route_audit(pairs)
    packages = {
        role: (private_root / "stage1" / f"{role}.zip").read_bytes() for role in REVIEWERS
    }
    packages["qualification_packet"] = (
        private_root / "qualification" / "qualification_packet.zip"
    ).read_bytes()
    leakage = stage1_leakage_audit(packages, pairs, _mappings(private_root))
    usability = usability_audit(packages)
    vault = vault_status(private_root / "stage2" / "stage2_vault.enc", repo_root)
    fixture = run_fixture_e2e()
    retirement = retirement_enforcement_report()
    power = build_power_plan(replicates=int(args.power_replicates))

    report_dir = repo_root / REPORT_DIR
    write_json(report_dir / "RETIRED_PACKET_REGISTRY.json", retired_packet_registry())
    write_json(report_dir / "ACTIVE_PATH_REGISTRY.json", active_path_registry(repo_root))
    write_json(report_dir / "RETIREMENT_ENFORCEMENT.json", retirement)
    write_json(report_dir / "DESIGN_AUDIT.json", public_design_summary(design))
    write_json(report_dir / "INTERVENTION_ISOLATION_AUDIT.json", public_isolation_summary(isolation))
    write_json(report_dir / "CAUSAL_ROUTE_AUDIT.json", public_route_summary(routes))
    write_json(report_dir / "HOSTILE_ROUTE_AUDIT.json", public_hostile_summary(hostile))
    write_json(report_dir / "STAGE1_LEAKAGE_AUDIT.json", public_leakage_summary(leakage))
    write_json(report_dir / "STAGE1_PACKAGE_RECEIPT.json", usability)
    write_json(report_dir / "STAGE2_VAULT_STATUS.json", vault)
    write_json(report_dir / "FIXTURE_E2E_WORKFLOW.json", fixture)
    write_json(report_dir / "ATTESTATION_POLICY.json", attestation_policy())
    write_json(repo_root / "configs/reviewer_ready_v2/power_plan_v2.json", power)

    commitment = read_json(report_dir / "PUBLIC_PACKET_COMMITMENT.json")
    freeze = build_freeze(repo_root, generator_commit=args.generator_commit)
    write_json(report_dir / "SCIENTIFIC_FREEZE_V2.json", freeze)
    freeze_check = verify_freeze(repo_root)
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
    "generate-private-packet": cmd_generate_private_packet,
    "validate-private-packet": cmd_validate_private_packet,
    "generate-stage1-packages": cmd_generate_stage1_packages,
    "validate-stage1-packages": cmd_validate_stage1_packages,
    "ingest-reviewer-qualification": cmd_ingest_reviewer_qualification,
    "ingest-stage1": cmd_ingest_stage1,
    "validate-stage1-submissions": cmd_validate_stage1_submissions,
    "commit-stage1": cmd_commit_stage1,
    "unlock-stage2": cmd_unlock_stage2,
    "generate-stage2-packages": cmd_generate_stage2_packages,
    "ingest-stage2": cmd_ingest_stage2,
    "validate-stage2-submissions": cmd_validate_stage2_submissions,
    "build-disagreement-queue": cmd_build_disagreement_queue,
    "ingest-adjudication": cmd_ingest_adjudication,
    "compute-agreement": cmd_compute_agreement,
    "run-c10": cmd_run_c10,
    "build-exclusion-register": cmd_build_exclusion_register,
    "lock-reviewed-slice": cmd_lock_reviewed_slice,
    "authorize-model-execution": cmd_authorize_model_execution,
    "status": cmd_status,
    "fixture-e2e": cmd_fixture_e2e,
    "verify-freeze": cmd_verify_freeze,
    "verify-attestation": cmd_verify_attestation,
    "build-reports": cmd_build_reports,
    "new-seed": cmd_new_seed,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cab-review-ready-v2",
        description=(
            "Reviewer-ready V2 packet and two-stage human-review workflow. No command performs "
            "model execution or genuine human review."
        ),
    )
    parser.add_argument("command", choices=sorted(COMMANDS))
    parser.add_argument("--private-root", default=None, help="override the private packet root")
    parser.add_argument("--seed", default=None, help="private generation seed (hex)")
    parser.add_argument("--reviewer-id", default=None)
    parser.add_argument("--reviewer-a", default="reviewer-a")
    parser.add_argument("--reviewer-b", default="reviewer-b")
    parser.add_argument("--adjudicator-id", default="adjudicator")
    parser.add_argument("--package-role", default="stage1_reviewer_a", choices=list(REVIEWERS))
    parser.add_argument("--submission", default=None, help="path to a reviewer submission file")
    parser.add_argument("--decisions", default=None, help="path to an adjudication decision file")
    parser.add_argument("--output-dir", default=None, help="where Stage-2 packages are written")
    parser.add_argument("--attestation", default=None, help="path to the external attestation")
    parser.add_argument("--generator-commit", default=None)
    parser.add_argument("--power-replicates", default=800)
    parser.add_argument(
        "--fixture",
        action="store_true",
        help="operate on the synthetic fixture namespace; never counts as genuine evidence",
    )
    return parser


def main(argv: list[str] | None = None, *, repo_root: Path | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = repo_root or Path(__file__).resolve().parents[3]
    try:
        _emit(COMMANDS[args.command](root, args))
    except (VaultError, ValueError, RuntimeError, KeyError) as error:
        _emit({"status": "REFUSED", "command": args.command, "reason": str(error)})
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())


__all__ = ["COMMANDS", "KEY_ENV", "build_parser", "main"]
