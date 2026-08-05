"""The hostile mutation matrix for committed review evidence.

Every case here models the same adversary: a coordinator who holds the sealing
key.  That is the only interesting adversary, because anyone without the key is
already stopped by the receipt MAC.  A key-holder can rewrite any receipt and
re-seal it so that it authenticates perfectly — so the question each attack asks
is not "does the MAC still verify?" but "does the workflow notice that what it
committed is no longer what it is reading?".

Attacks mutate sealed artifacts on disk directly rather than through the
workflow, then push every remaining coordinator API and record the first gate
that refuses.  A gate that *accepts* a mutated chain is a failure of this module,
so it fails closed: any acceptance makes the whole audit fail.

Shared by ``tests/test_final_integrity_closure.py`` and
``scripts/audit_final_review_integrity.py`` so that the suite and the standalone
audit exercise one matrix through one set of public APIs.
"""

from __future__ import annotations

import json
import shutil
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from causal_agent_bench.review_ready_v2.adjudication import STAGE1, STAGE2
from causal_agent_bench.review_ready_v2.commitment_integrity import (
    MANIFEST_FILENAME,
    CommitmentIntegrityError,
    snapshot_directory,
    snapshot_filename,
)
from causal_agent_bench.review_ready_v2.common import sha256_bytes
from causal_agent_bench.review_ready_v2.fixture_e2e import (
    FIXTURE_COMMIT,
    FIXTURE_FREEZE_SHA,
    FIXTURE_PAIR_COUNT,
    FIXTURE_PSEUDONYMS,
    FixtureWorkflow,
)
from causal_agent_bench.review_ready_v2.receipts import (
    ReceiptError,
    fixture_authority,
    seal_receipt,
)
from causal_agent_bench.review_ready_v2.roles import REVIEWER_A, REVIEWER_B
from causal_agent_bench.review_ready_v2.stage2 import NOT_APPLICABLE
from causal_agent_bench.review_ready_v2.workflow import (
    ReviewWorkspace,
    WorkflowError,
    authorize_model_execution,
    build_exclusion_register,
    lock_reviewed_slice,
    verify_committed_stage1_snapshot,
    verify_committed_stage2_snapshot,
)

#: Errors a gate is allowed to refuse with.  Anything else is a crash, not a
#: refusal, and is reported as such rather than counted as a rejection.
REFUSALS = (WorkflowError, CommitmentIntegrityError, ReceiptError, ValueError, KeyError)

#: Every gate, in the order a coordinator reaches it.
GATE_ORDER: tuple[str, ...] = (
    "committed_stage1_snapshot",
    "committed_stage2_snapshot",
    "stage2_unlock",
    "stage2_issuance",
    "stage2_ingestion",
    "pairing",
    "stage1_queue",
    "stage2_queue",
    "agreement",
    "adjudicator_package",
    "adjudication",
    "final_records",
    "c10",
    "exclusion_register",
    "slice_lock",
    "execution_authorization",
)

ACCEPTED = "accepted"
REJECTED = "rejected"
UNREACHABLE = "unreachable"


# --------------------------------------------------------------------------
# mutation primitives
# --------------------------------------------------------------------------


def receipts_dir(driver: FixtureWorkflow) -> Path:
    return driver.workspace.receipts


def receipt_path(driver: FixtureWorkflow, name: str) -> Path:
    return receipts_dir(driver) / f"{name}.json"


def snapshot_receipt_path(driver: FixtureWorkflow, role: str, stage: str) -> Path:
    return snapshot_directory(receipts_dir(driver), stage) / snapshot_filename(role, stage)


def snapshot_manifest_path(driver: FixtureWorkflow, stage: str) -> Path:
    return snapshot_directory(receipts_dir(driver), stage) / MANIFEST_FILENAME


def read_raw(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def write_raw(path: Path, payload: dict[str, Any]) -> None:
    """Write as an attacker would: straight to disk, around the workflow."""

    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    path.chmod(0o600)


def reseal(path: Path, mutate: Callable[[dict[str, Any]], None]) -> dict[str, Any]:
    """Mutate a sealed receipt and re-seal it with a valid fixture MAC.

    This is the whole threat model in four lines: the attacker's edit
    authenticates, so nothing downstream can rely on the MAC alone.
    """

    receipt = read_raw(path)
    mutate(receipt)
    for field_name in (
        "receipt_sha256",
        "receipt_mac",
        "receipt_schema_version",
        "artifact_origin",
        "counts_as_genuine_evidence",
        "recorded_at",
    ):
        receipt.pop(field_name, None)
    resealed = seal_receipt(fixture_authority(), receipt)
    write_raw(path, resealed)
    return resealed


def first_item(receipt: dict[str, Any]) -> str:
    return sorted(receipt["judgements"])[0]


def sibling_workflow(driver: FixtureWorkflow, name: str, *, stage: str) -> FixtureWorkflow:
    """A second, independent fixture workspace to steal valid receipts from."""

    other = FixtureWorkflow.create(driver.root / name)
    other.advance_to(stage)
    return other


# --------------------------------------------------------------------------
# gate probes
# --------------------------------------------------------------------------


def _probe(fn: Callable[[], Any]) -> tuple[str, str]:
    try:
        result = fn()
    except REFUSALS as error:
        return REJECTED, f"{type(error).__name__}: {error}"
    if isinstance(result, dict) and result.get("mechanics_status") == "C10_MECHANICS_FAIL":
        return REJECTED, f"C10_MECHANICS_FAIL {result.get('failed_checks')}"
    return ACCEPTED, "the gate accepted the mutated chain"


def _gate_probes(driver: FixtureWorkflow) -> dict[str, Callable[[], Any]]:
    workspace = driver.workspace

    def _lock() -> Any:
        report = driver.c10() if not workspace.has("c10_report") else workspace.read("c10_report")
        if not workspace.has("exclusion_register"):
            build_exclusion_register(workspace)
        return lock_reviewed_slice(
            workspace,
            c10_report=report,
            packet_commitment=driver.packet_commitment,
            scorer_sha256="0" * 64,
            endpoints_sha256="1" * 64,
            analysis_plan_sha256="2" * 64,
            system_identity_sha256="3" * 64,
            scientific_freeze_sha256=FIXTURE_FREEZE_SHA,
            exact_commit=FIXTURE_COMMIT,
        )

    def _authorize() -> Any:
        return authorize_model_execution(
            workspace,
            exact_commit=FIXTURE_COMMIT,
            scientific_freeze_sha256=FIXTURE_FREEZE_SHA,
            c10_report=workspace.read("c10_report"),
        )

    return {
        "committed_stage1_snapshot": lambda: verify_committed_stage1_snapshot(workspace),
        "committed_stage2_snapshot": lambda: verify_committed_stage2_snapshot(workspace),
        "stage2_unlock": driver.open_stage2,
        "stage2_issuance": driver.open_stage2,
        "stage2_ingestion": driver.submit_stage2,
        "pairing": lambda: workspace._paired(driver.mappings, STAGE1),
        "stage1_queue": lambda: workspace.build_stage1_disagreements(mappings=driver.mappings),
        "stage2_queue": lambda: workspace.build_stage2_disagreements(
            mappings=driver.mappings, applicability=driver.applicability
        ),
        "agreement": lambda: workspace.compute_agreement(mappings=driver.mappings),
        "adjudicator_package": driver.issue_adjudicator_packages,
        "adjudication": driver.adjudicate,
        "final_records": lambda: workspace.build_final_adjudicated_records(
            mappings=driver.mappings,
            applicability=driver.applicability,
            expected_pair_count=FIXTURE_PAIR_COUNT,
        ),
        "c10": driver.c10,
        "exclusion_register": lambda: build_exclusion_register(workspace),
        "slice_lock": _lock,
        "execution_authorization": _authorize,
    }


#: Which gates are still ahead of a mutation made at each fixture stage.  A gate
#: already behind the mutation cannot be re-run without tripping the write-once
#: guard, which would report a refusal for the wrong reason.
_GATES_AFTER: dict[str, tuple[str, ...]] = {
    "commit_stage1": (
        "committed_stage1_snapshot",
        "stage2_unlock",
        "pairing",
    ),
    "submit_stage2": (
        "committed_stage1_snapshot",
        "committed_stage2_snapshot",
        "pairing",
        "stage1_queue",
        "stage2_queue",
        "agreement",
        "final_records",
        "c10",
    ),
    "build_queues": (
        "committed_stage1_snapshot",
        "committed_stage2_snapshot",
        "pairing",
        "adjudicator_package",
        "adjudication",
        "agreement",
        "final_records",
        "c10",
    ),
    "adjudicate": (
        "committed_stage1_snapshot",
        "committed_stage2_snapshot",
        "agreement",
        "final_records",
        "c10",
    ),
    "settle": (
        "committed_stage1_snapshot",
        "committed_stage2_snapshot",
        "c10",
        "exclusion_register",
        "slice_lock",
    ),
    "lock": (
        "committed_stage1_snapshot",
        "committed_stage2_snapshot",
        "execution_authorization",
    ),
}


@dataclass(frozen=True)
class Attack:
    """One hostile mutation and the gate that must refuse it."""

    name: str
    chain: str
    stage: str
    expected_gate: str
    mutate: Callable[[FixtureWorkflow], None]
    scope: str = "production_invariant"
    #: Gates to probe, when the stage default is not the right set.
    gates: tuple[str, ...] = field(default=())

    def probe_order(self) -> tuple[str, ...]:
        return self.gates or _GATES_AFTER[self.stage]


def _advance(driver: FixtureWorkflow, stage: str) -> None:
    """Take a fresh driver to the point just before the mutation."""

    if stage in FixtureWorkflow.STAGES:
        driver.advance_to(stage)
        return
    driver.advance_to("settle")
    report = driver.c10()
    if stage == "lock":
        driver.lock(report)
        return
    if stage != "c10":
        raise ValueError(f"unknown fixture stage {stage!r}")


def run_attack(attack: Attack, root: Path) -> dict[str, Any]:
    """Build a clean fixture chain, mutate it, and push every remaining gate."""

    driver = FixtureWorkflow.create(root)
    _advance(driver, attack.stage)
    try:
        attack.mutate(driver)
    except REFUSALS as error:
        # The mutation itself was refused — the workflow never even accepted the
        # hostile input.  That is a rejection at the earliest possible gate.
        return {
            "attack": attack.name,
            "receipt_chain": attack.chain,
            "mutated_after_stage": attack.stage,
            "expected_rejection_gate": attack.expected_gate,
            "actual_rejection_gate": "mutation_refused",
            "gate_results": {},
            "scope": attack.scope,
            "detail": f"{type(error).__name__}: {error}",
            "passed": True,
        }

    probes = _gate_probes(driver)
    order = attack.probe_order()
    results: dict[str, str] = {}
    details: dict[str, str] = {}
    first_rejection: str | None = None
    accepted: list[str] = []
    for gate in order:
        if first_rejection is not None:
            results[gate] = UNREACHABLE
            continue
        outcome, detail = _probe(probes[gate])
        results[gate] = outcome
        details[gate] = detail
        if outcome == REJECTED:
            first_rejection = gate
        else:
            accepted.append(gate)

    # A pass means the refusal came no later than the first gate that actually
    # consumes the changed artifact.  Gates *before* that one are allowed to
    # accept: an untouched Stage-1 chain should still verify when the mutation
    # was in Stage 2, and pretending otherwise would hide which gate is load
    # bearing.
    expected_index = order.index(attack.expected_gate) if attack.expected_gate in order else -1
    passed = (
        first_rejection is not None
        and expected_index >= 0
        and order.index(first_rejection) <= expected_index
    )
    return {
        "attack": attack.name,
        "receipt_chain": attack.chain,
        "mutated_after_stage": attack.stage,
        "expected_rejection_gate": attack.expected_gate,
        "actual_rejection_gate": first_rejection,
        "gate_results": results,
        "gates_that_accepted_before_the_expected_gate": [
            gate for gate in accepted if order.index(gate) < expected_index
        ],
        "scope": attack.scope,
        "detail": details.get(first_rejection or "", ""),
        "passed": passed,
    }


# --------------------------------------------------------------------------
# 14.1 — Stage-1 post-commit replacement attacks
# --------------------------------------------------------------------------


def _live1(driver: FixtureWorkflow, role: str = REVIEWER_A) -> Path:
    return receipt_path(driver, f"stage1_submission_{role}")


def _snap1(driver: FixtureWorkflow, role: str = REVIEWER_A) -> Path:
    return snapshot_receipt_path(driver, role, STAGE1)


def _cell(path: Path, column: str, value: str) -> None:
    def mutate(receipt: dict[str, Any]) -> None:
        receipt["judgements"][first_item(receipt)][column] = value

    reseal(path, mutate)


def _stage1_attacks() -> list[Attack]:
    def snapshot_cell(column: str, value: str) -> Callable[[FixtureWorkflow], None]:
        return lambda driver: _cell(_snap1(driver), column, value)

    def live_cell(column: str, value: str) -> Callable[[FixtureWorkflow], None]:
        return lambda driver: _cell(_live1(driver), column, value)

    def add_row(driver: FixtureWorkflow) -> None:
        def mutate(receipt: dict[str, Any]) -> None:
            extra = dict(receipt["judgements"][first_item(receipt)])
            extra["reviewer_item_id"] = "RA-99"
            receipt["judgements"]["RA-99"] = extra

        reseal(_snap1(driver), mutate)

    def remove_row(driver: FixtureWorkflow) -> None:
        reseal(
            _snap1(driver),
            lambda receipt: receipt["judgements"].pop(first_item(receipt)),
        )

    def reorder_rows(driver: FixtureWorkflow) -> None:
        def mutate(receipt: dict[str, Any]) -> None:
            receipt["judgements"] = dict(reversed(list(receipt["judgements"].items())))

        reseal(_snap1(driver), mutate)

    def duplicate_item_id(driver: FixtureWorkflow) -> None:
        def mutate(receipt: dict[str, Any]) -> None:
            item = first_item(receipt)
            receipt["judgements"][f"{item} "] = dict(receipt["judgements"][item])

        reseal(_snap1(driver), mutate)

    def change_role(driver: FixtureWorkflow) -> None:
        reseal(_snap1(driver), lambda receipt: receipt.update({"reviewer_role": REVIEWER_B}))

    def change_pseudonym(driver: FixtureWorkflow) -> None:
        reseal(
            receipt_path(driver, f"declaration_{REVIEWER_A}"),
            lambda receipt: receipt.update({"reviewer_pseudonym": "someone-else"}),
        )

    def change_package_hash(driver: FixtureWorkflow) -> None:
        reseal(_snap1(driver), lambda receipt: receipt.update({"package_sha256": "9" * 64}))

    def change_declaration_hash(driver: FixtureWorkflow) -> None:
        reseal(_snap1(driver), lambda receipt: receipt.update({"declaration_sha256": "9" * 64}))

    def change_qualification_hash(driver: FixtureWorkflow) -> None:
        reseal(
            _snap1(driver),
            lambda receipt: receipt.update({"qualification_receipt_sha256": "9" * 64}),
        )

    def change_validation(driver: FixtureWorkflow) -> None:
        reseal(
            _snap1(driver),
            lambda receipt: receipt["validation"].update({"no_malformed_cells": False}),
        )

    def change_row_count(driver: FixtureWorkflow) -> None:
        reseal(_snap1(driver), lambda receipt: receipt.update({"row_count": 99}))

    def retain_payload_hash_change_content(driver: FixtureWorkflow) -> None:
        """The confirmed exploit, verbatim: edit content, keep ``submission_sha256``."""

        original = read_raw(_snap1(driver))["submission_sha256"]

        def mutate(receipt: dict[str, Any]) -> None:
            receipt["judgements"][first_item(receipt)]["notes"] = "POST-COMMIT TAMPERING"
            receipt["submission_sha256"] = original

        reseal(_snap1(driver), mutate)

    def retain_content_change_envelope(driver: FixtureWorkflow) -> None:
        reseal(_snap1(driver), lambda receipt: receipt.update({"submission_sha256": "9" * 64}))

    def swap_reviewers(driver: FixtureWorkflow) -> None:
        a = _snap1(driver, REVIEWER_A)
        b = _snap1(driver, REVIEWER_B)
        a_bytes, b_bytes = a.read_bytes(), b.read_bytes()
        a.write_bytes(b_bytes)
        b.write_bytes(a_bytes)

    def replay_older_receipt(driver: FixtureWorkflow) -> None:
        """Replay a validly sealed earlier receipt for the same reviewer.

        Its parsed content is identical, so only the sealed envelope differs.
        The commitment binds the exact receipt file, not just the judgements, so
        an otherwise indistinguishable earlier receipt is still refused.
        """

        other = sibling_workflow(driver, "replay_stage1", stage="submit_stage1")
        shutil.copyfile(_live1(other), _snap1(driver))

    def copy_from_another_workspace(driver: FixtureWorkflow) -> None:
        other = sibling_workflow(driver, "other_workspace", stage="commit_stage1")
        shutil.copyfile(_snap1(other), _snap1(driver))

    def production_refuses_a_fixture_receipt(driver: FixtureWorkflow) -> None:
        """A fixture receipt cannot be verified by the production authority.

        Production sealing needs the external coordinator key, so this attack is
        refused at authority construction on any machine that does not hold it —
        and refused on origin, schema and MAC on any machine that does.
        """

        production = ReviewWorkspace.production(driver.private_root, driver.root)
        production.packet_version = driver.workspace.packet_version
        target = production.receipts / f"stage1_submission_{REVIEWER_A}.json"
        target.write_bytes(_snap1(driver).read_bytes())
        target.chmod(0o600)
        production.read(f"stage1_submission_{REVIEWER_A}")

    def replace_snapshot_file(driver: FixtureWorkflow) -> None:
        write_raw(_snap1(driver), {"receipt_kind": "stage1_submission", "judgements": {}})

    def replace_snapshot_manifest(driver: FixtureWorkflow) -> None:
        reseal(
            snapshot_manifest_path(driver, STAGE1),
            lambda manifest: manifest["reviewers"][REVIEWER_A].update(
                {"canonical_judgements_sha256": "9" * 64}
            ),
        )

    def delete_snapshot_file(driver: FixtureWorkflow) -> None:
        _snap1(driver).unlink()

    def conflicting_live_receipt(driver: FixtureWorkflow) -> None:
        _cell(_live1(driver), "notes", "a conflicting live receipt written after commitment")

    def symlinked_snapshot(driver: FixtureWorkflow) -> None:
        target = _snap1(driver)
        elsewhere = driver.root / "elsewhere.json"
        shutil.copyfile(target, elsewhere)
        target.unlink()
        target.symlink_to(elsewhere)

    def world_readable_snapshot(driver: FixtureWorkflow) -> None:
        """Only meaningful in production, where private mode is enforced."""

        _snap1(driver).chmod(0o644)
        production = ReviewWorkspace.production(driver.private_root, driver.root)
        verify_committed_stage1_snapshot(production)

    stage = "commit_stage1"
    chain = "stage1_submission"
    cases: list[tuple[str, Callable[[FixtureWorkflow], None], str]] = [
        ("stage1_notes_modified_and_resealed", snapshot_cell("notes", "tampered"), chain),
        ("stage1_confidence_modified_and_resealed", snapshot_cell("reviewer_confidence", "1"), chain),
        ("stage1_non_gating_judgement_modified", snapshot_cell("intervention_realistic", "1"), chain),
        ("stage1_gating_judgement_modified", snapshot_cell("single_factor_isolation", "no"), chain),
        ("stage1_row_added", add_row, chain),
        ("stage1_row_removed", remove_row, chain),
        ("stage1_rows_reordered", reorder_rows, chain),
        ("stage1_item_id_duplicated", duplicate_item_id, chain),
        ("stage1_reviewer_role_changed", change_role, chain),
        ("stage1_pseudonym_binding_changed", change_pseudonym, "reviewer_declaration"),
        ("stage1_package_hash_changed", change_package_hash, chain),
        ("stage1_declaration_hash_changed", change_declaration_hash, chain),
        ("stage1_qualification_hash_changed", change_qualification_hash, chain),
        ("stage1_validation_result_changed", change_validation, chain),
        ("stage1_row_count_changed", change_row_count, chain),
        ("stage1_payload_hash_retained_content_changed", retain_payload_hash_change_content, chain),
        ("stage1_content_retained_envelope_changed", retain_content_change_envelope, chain),
        ("stage1_reviewer_a_receipt_replaced_with_b", swap_reviewers, chain),
        ("stage1_older_valid_receipt_replayed", replay_older_receipt, chain),
        ("stage1_receipt_copied_from_another_workspace", copy_from_another_workspace, chain),
        ("stage1_snapshot_file_replaced", replace_snapshot_file, "committed_stage1_snapshot"),
        ("stage1_snapshot_manifest_replaced", replace_snapshot_manifest, "committed_stage1_snapshot"),
        ("stage1_snapshot_file_deleted", delete_snapshot_file, "committed_stage1_snapshot"),
        ("stage1_conflicting_live_receipt_created", conflicting_live_receipt, chain),
        ("stage1_snapshot_replaced_by_symlink", symlinked_snapshot, "committed_stage1_snapshot"),
    ]
    attacks = [
        Attack(
            name=name,
            chain=receipt_chain,
            stage=stage,
            expected_gate="committed_stage1_snapshot",
            mutate=mutate,
        )
        for name, mutate, receipt_chain in cases
    ]
    attacks.append(
        Attack(
            name="stage1_fixture_receipt_copied_into_production_verification",
            chain="artifact_origin",
            stage=stage,
            expected_gate="committed_stage1_snapshot",
            mutate=production_refuses_a_fixture_receipt,
            scope="production_invariant",
            gates=("committed_stage1_snapshot",),
        )
    )
    attacks.append(
        Attack(
            name="stage1_snapshot_made_world_readable_in_production",
            chain="committed_stage1_snapshot",
            stage=stage,
            expected_gate="committed_stage1_snapshot",
            mutate=world_readable_snapshot,
            scope="production_invariant",
            gates=("committed_stage1_snapshot",),
        )
    )
    return attacks


# --------------------------------------------------------------------------
# 14.2 — Stage-2 attacks
# --------------------------------------------------------------------------


def _snap2(driver: FixtureWorkflow, role: str = REVIEWER_A) -> Path:
    return snapshot_receipt_path(driver, role, STAGE2)


def _stage2_attacks() -> list[Attack]:
    def swap_issuance(driver: FixtureWorkflow) -> None:
        a = receipt_path(driver, f"stage2_issuance_{REVIEWER_A}")
        b = receipt_path(driver, f"stage2_issuance_{REVIEWER_B}")
        a_bytes, b_bytes = a.read_bytes(), b.read_bytes()
        a.write_bytes(b_bytes)
        b.write_bytes(a_bytes)

    def swap_archive_hash(driver: FixtureWorkflow) -> None:
        reseal(
            receipt_path(driver, f"stage2_issuance_{REVIEWER_A}"),
            lambda receipt: receipt.update(
                {"stage2_package_sha256": sha256_bytes(driver.stage2_archives[REVIEWER_B])}
            ),
        )

    def swap_namespace(driver: FixtureWorkflow) -> None:
        reseal(
            receipt_path(driver, f"stage2_issuance_{REVIEWER_A}"),
            lambda receipt: receipt.update({"stage2_opaque_id_namespace": "RB"}),
        )

    def swap_reviewers(driver: FixtureWorkflow) -> None:
        a = _snap2(driver, REVIEWER_A)
        b = _snap2(driver, REVIEWER_B)
        a_bytes, b_bytes = a.read_bytes(), b.read_bytes()
        a.write_bytes(b_bytes)
        b.write_bytes(a_bytes)

    def stale_stage1_commitment(driver: FixtureWorkflow) -> None:
        reseal(
            receipt_path(driver, "stage1_commitment"),
            lambda receipt: receipt.update({"expected_item_count": 99}),
        )

    def changed_stage1_snapshot(driver: FixtureWorkflow) -> None:
        _cell(_snap1(driver), "notes", "changed after Stage 2 was issued")

    def altered_stage2_judgement(driver: FixtureWorkflow) -> None:
        _cell(_snap2(driver), "gold_correct", "NO")

    def altered_applicability(driver: FixtureWorkflow) -> None:
        def mutate(receipt: dict[str, Any]) -> None:
            for row in receipt["judgements"].values():
                if row.get("abstention_policy_valid_or_not_applicable") == NOT_APPLICABLE:
                    row["abstention_policy_valid_or_not_applicable"] = "YES"
                    return
            raise AssertionError("the fixture no longer contains a NOT_APPLICABLE cell to alter")

        reseal(_snap2(driver), mutate)

    def altered_not_applicable(driver: FixtureWorkflow) -> None:
        _cell(_snap2(driver), "recovery_authorization_valid_or_not_applicable", NOT_APPLICABLE)

    def altered_package_hash(driver: FixtureWorkflow) -> None:
        reseal(_snap2(driver), lambda receipt: receipt.update({"stage2_package_sha256": "9" * 64}))

    def replayed_issuance(driver: FixtureWorkflow) -> None:
        other = sibling_workflow(driver, "replay_workspace", stage="open_stage2")
        shutil.copyfile(
            receipt_path(other, f"stage2_issuance_{REVIEWER_A}"),
            receipt_path(driver, f"stage2_issuance_{REVIEWER_A}"),
        )

    def copied_issuance(driver: FixtureWorkflow) -> None:
        shutil.copyfile(
            receipt_path(driver, f"stage2_issuance_{REVIEWER_B}"),
            receipt_path(driver, f"stage2_issuance_{REVIEWER_A}"),
        )

    def retained_payload_hash(driver: FixtureWorkflow) -> None:
        original = read_raw(_snap2(driver))["submission_sha256"]

        def mutate(receipt: dict[str, Any]) -> None:
            receipt["judgements"][first_item(receipt)]["notes"] = "stage-2 tampering"
            receipt["submission_sha256"] = original

        reseal(_snap2(driver), mutate)

    def replacement_after_queue(driver: FixtureWorkflow) -> None:
        _cell(_snap2(driver), "notes", "replaced after the queue was generated")

    def third_submission_after_commit(driver: FixtureWorkflow) -> None:
        driver.submit_stage2()

    cases: list[tuple[str, Callable[[FixtureWorkflow], None], str, str]] = [
        ("stage2_issuance_swapped", swap_issuance, "stage2_issuance", "submit_stage2"),
        ("stage2_archive_hash_swapped", swap_archive_hash, "stage2_issuance", "submit_stage2"),
        ("stage2_namespace_swapped", swap_namespace, "stage2_issuance", "submit_stage2"),
        ("stage2_reviewers_swapped", swap_reviewers, "stage2_submission", "submit_stage2"),
        ("stage2_stale_stage1_commitment", stale_stage1_commitment, "stage1_commitment", "submit_stage2"),
        ("stage2_changed_stage1_snapshot", changed_stage1_snapshot, "committed_stage1_snapshot", "submit_stage2"),
        ("stage2_judgement_altered", altered_stage2_judgement, "stage2_submission", "submit_stage2"),
        ("stage2_applicability_altered", altered_applicability, "stage2_submission", "submit_stage2"),
        ("stage2_not_applicable_value_altered", altered_not_applicable, "stage2_submission", "submit_stage2"),
        ("stage2_package_hash_altered", altered_package_hash, "stage2_submission", "submit_stage2"),
        ("stage2_issuance_replayed_from_another_workspace", replayed_issuance, "stage2_issuance", "submit_stage2"),
        ("stage2_issuance_copied_between_reviewers", copied_issuance, "stage2_issuance", "submit_stage2"),
        ("stage2_payload_hash_retained_content_changed", retained_payload_hash, "stage2_submission", "submit_stage2"),
        ("stage2_submission_replaced_after_queue", replacement_after_queue, "stage2_submission", "build_queues"),
        ("stage2_third_submission_after_commitment", third_submission_after_commit, "stage2_submission", "submit_stage2"),
    ]
    return [
        Attack(
            name=name,
            chain=chain,
            stage=stage,
            expected_gate="committed_stage1_snapshot"
            if chain in ("stage1_commitment", "committed_stage1_snapshot")
            else "committed_stage2_snapshot",
            mutate=mutate,
        )
        for name, mutate, chain, stage in cases
    ]


# --------------------------------------------------------------------------
# 14.3 — adjudication attacks
# --------------------------------------------------------------------------


def _adjudication_attacks() -> list[Attack]:
    def wrong_queue(driver: FixtureWorkflow) -> None:
        reseal(
            receipt_path(driver, f"{STAGE1}_disagreement_queue"),
            lambda queue: queue.update({"pair_count": 99}),
        )

    def changed_disputed_set(driver: FixtureWorkflow) -> None:
        def mutate(queue: dict[str, Any]) -> None:
            queue["disputes"] = queue["disputes"][:-1]
            queue["disputed_dimension_count"] = len(queue["disputes"])

        reseal(receipt_path(driver, f"{STAGE1}_disagreement_queue"), mutate)

    def omitted_decision(driver: FixtureWorkflow) -> None:
        def mutate(adjudication: dict[str, Any]) -> None:
            adjudication["decisions"] = adjudication["decisions"][:-1]
            adjudication["decision_count"] = len(adjudication["decisions"])

        reseal(receipt_path(driver, f"{STAGE1}_adjudication"), mutate)

    def extra_decision(driver: FixtureWorkflow) -> None:
        def mutate(adjudication: dict[str, Any]) -> None:
            extra = dict(adjudication["decisions"][0])
            extra["pair_id"] = "fixture-pair-99"
            adjudication["decisions"] = [*adjudication["decisions"], extra]
            adjudication["decision_count"] = len(adjudication["decisions"])

        reseal(receipt_path(driver, f"{STAGE1}_adjudication"), mutate)

    def _decision_field(stage: str, key: str, value: str) -> Callable[[FixtureWorkflow], None]:
        def mutate_driver(driver: FixtureWorkflow) -> None:
            reseal(
                receipt_path(driver, f"{stage}_adjudication"),
                lambda receipt: receipt["decisions"][0].update({key: value}),
            )

        return mutate_driver

    def wrong_adjudicator(driver: FixtureWorkflow) -> None:
        reseal(
            receipt_path(driver, f"{STAGE1}_adjudication"),
            lambda receipt: receipt.update({"adjudicator_pseudonym_sha256": "9" * 64}),
        )

    def reviewer_acting_as_adjudicator(driver: FixtureWorkflow) -> None:
        driver.workspace.ingest_adjudication(
            stage=STAGE2,
            adjudicator_pseudonym=FIXTURE_PSEUDONYMS[REVIEWER_A],
            decisions=[],
            package_sha256=driver.adjudicator_packages[STAGE2]["package_sha256"],
        )

    def copied_adjudication(driver: FixtureWorkflow) -> None:
        other = sibling_workflow(driver, "adjudication_source", stage="adjudicate")
        shutil.copyfile(
            receipt_path(other, f"{STAGE1}_adjudication"),
            receipt_path(driver, f"{STAGE1}_adjudication"),
        )

    def post_final_record_replacement(driver: FixtureWorkflow) -> None:
        reseal(
            receipt_path(driver, f"{STAGE1}_adjudication"),
            lambda receipt: receipt["decisions"][0].update({"rationale": "rewritten afterwards"}),
        )

    cases: list[tuple[str, Callable[[FixtureWorkflow], None], str]] = [
        ("adjudication_against_a_changed_queue", wrong_queue, "adjudicate"),
        ("adjudication_queue_disputed_set_changed", changed_disputed_set, "adjudicate"),
        ("adjudication_decision_omitted", omitted_decision, "adjudicate"),
        ("adjudication_decision_added", extra_decision, "adjudicate"),
        (
            "adjudication_final_value_changed",
            _decision_field(STAGE1, "final_value", "yes-but-different"),
            "adjudicate",
        ),
        (
            "adjudication_exclusion_decision_changed",
            _decision_field(STAGE1, "exclude_item", "YES"),
            "adjudicate",
        ),
        (
            "adjudication_rationale_changed",
            _decision_field(STAGE1, "rationale", "a different rationale"),
            "adjudicate",
        ),
        (
            "adjudication_evidence_reference_changed",
            _decision_field(STAGE1, "evidence_reference", "fixture://elsewhere"),
            "adjudicate",
        ),
        ("adjudication_adjudicator_changed", wrong_adjudicator, "adjudicate"),
        ("adjudication_by_a_reviewer", reviewer_acting_as_adjudicator, "issue_adjudicator_packages"),
        ("adjudication_copied_from_another_workspace", copied_adjudication, "adjudicate"),
        ("adjudication_replaced_after_final_records", post_final_record_replacement, "settle"),
    ]
    return [
        Attack(
            name=name,
            chain="adjudication",
            stage=stage,
            expected_gate="c10" if stage == "settle" else "final_records",
            mutate=mutate,
            gates=("c10", "exclusion_register", "slice_lock") if stage == "settle" else (),
        )
        for name, mutate, stage in cases
    ]


# --------------------------------------------------------------------------
# 14.4 — final record, C10 and lock attacks
# --------------------------------------------------------------------------


def _late_attacks() -> list[Attack]:
    def final_record_replacement(driver: FixtureWorkflow) -> None:
        reseal(
            receipt_path(driver, "final_adjudicated_records"),
            lambda receipt: receipt.update({"included_count": 99}),
        )

    def stale_agreement(driver: FixtureWorkflow) -> None:
        reseal(
            receipt_path(driver, "agreement"),
            lambda receipt: receipt["stage1"].update({"overall_raw_agreement": 1.0}),
        )

    def changed_included_pairs(driver: FixtureWorkflow) -> None:
        reseal(
            receipt_path(driver, "final_adjudicated_records"),
            lambda receipt: receipt["included_pair_ids"].append("fixture-pair-99"),
        )

    def changed_exclusion_reason(driver: FixtureWorkflow) -> None:
        def mutate(receipt: dict[str, Any]) -> None:
            receipt["excluded_pairs"] = [
                {"pair_id": "fixture-pair-01", "reasons": ["invented_reason"]}
            ]
            receipt["excluded_count"] = 1

        reseal(receipt_path(driver, "final_adjudicated_records"), mutate)

    def c10_copied_from_another_workspace(driver: FixtureWorkflow) -> None:
        other = sibling_workflow(driver, "c10_source", stage="settle")
        other.c10()
        shutil.copyfile(receipt_path(other, "c10_report"), receipt_path(driver, "c10_report"))

    def c10_changed_after_lock(driver: FixtureWorkflow) -> None:
        reseal(
            receipt_path(driver, "c10_report"),
            lambda receipt: receipt.update({"included_count": 99}),
        )

    def exclusion_register_replacement(driver: FixtureWorkflow) -> None:
        reseal(
            receipt_path(driver, "exclusion_register"),
            lambda receipt: receipt.update({"included_count": 99}),
        )

    def slice_lock_replacement(driver: FixtureWorkflow) -> None:
        reseal(
            receipt_path(driver, "slice_lock"),
            lambda receipt: receipt.update({"stage1_snapshot_manifest_sha256": "9" * 64}),
        )

    def source_commit_mismatch(driver: FixtureWorkflow) -> None:
        reseal(
            receipt_path(driver, "slice_lock"),
            lambda receipt: receipt.update({"exact_commit": "9" * 40}),
        )

    def freeze_mismatch(driver: FixtureWorkflow) -> None:
        reseal(
            receipt_path(driver, "slice_lock"),
            lambda receipt: receipt.update({"scientific_freeze_sha256": "9" * 64}),
        )

    def packet_mismatch(driver: FixtureWorkflow) -> None:
        reseal(
            receipt_path(driver, "stage1_commitment"),
            lambda receipt: receipt.update({"private_packet_commitment": "9" * 64}),
        )

    def execution_authorization_replay(driver: FixtureWorkflow) -> None:
        other = sibling_workflow(driver, "authorization_source", stage="settle")
        report = other.c10()
        other.lock(report)
        other.authorize(report)
        shutil.copyfile(
            receipt_path(other, "execution_authorization"),
            receipt_path(driver, "execution_authorization"),
        )
        _cell(_snap1(driver), "notes", "changed under a replayed authorization")

    settle_cases: list[tuple[str, Callable[[FixtureWorkflow], None], str]] = [
        ("final_records_replaced", final_record_replacement, "final_adjudicated_records"),
        ("agreement_report_made_stale", stale_agreement, "agreement"),
        ("final_records_included_pairs_changed", changed_included_pairs, "final_adjudicated_records"),
        ("final_records_exclusion_reason_changed", changed_exclusion_reason, "final_adjudicated_records"),
    ]
    lock_cases: list[tuple[str, Callable[[FixtureWorkflow], None], str]] = [
        ("c10_report_copied_from_another_workspace", c10_copied_from_another_workspace, "c10_report"),
        ("c10_report_changed_after_lock", c10_changed_after_lock, "c10_report"),
        ("exclusion_register_replaced", exclusion_register_replacement, "exclusion_register"),
        ("slice_lock_replaced", slice_lock_replacement, "reviewed_slice_lock"),
        ("slice_lock_source_commit_mismatch", source_commit_mismatch, "reviewed_slice_lock"),
        ("slice_lock_freeze_mismatch", freeze_mismatch, "reviewed_slice_lock"),
        ("slice_lock_packet_mismatch", packet_mismatch, "stage1_commitment"),
        ("execution_authorization_replayed", execution_authorization_replay, "execution_authorization"),
    ]
    attacks = [
        Attack(
            name=name,
            chain=chain,
            stage="settle",
            expected_gate="c10",
            mutate=mutate,
            gates=("c10", "exclusion_register", "slice_lock"),
        )
        for name, mutate, chain in settle_cases
    ]
    attacks += [
        Attack(
            name=name,
            chain=chain,
            stage="lock",
            expected_gate="execution_authorization",
            mutate=mutate,
            gates=("execution_authorization",),
        )
        for name, mutate, chain in lock_cases
    ]
    return attacks


def attack_matrix() -> list[Attack]:
    """Every hostile case, in the order the integrity closure specifies them."""

    return [
        *_stage1_attacks(),
        *_stage2_attacks(),
        *_adjudication_attacks(),
        *_late_attacks(),
    ]


def run_attack_matrix(root: Path, *, attacks: list[Attack] | None = None) -> dict[str, Any]:
    """Run every attack in its own isolated workspace and summarise."""

    cases = attacks if attacks is not None else attack_matrix()
    results = []
    for index, attack in enumerate(cases, 1):
        workspace_root = root / f"attack_{index:03d}_{attack.name[:48]}"
        results.append(run_attack(attack, workspace_root))
    failed = [row for row in results if not row["passed"]]
    by_chain: dict[str, int] = {}
    for row in results:
        by_chain[row["receipt_chain"]] = by_chain.get(row["receipt_chain"], 0) + 1
    return {
        "schema_version": "cab_hostile_integrity_audit_v1",
        "attack_count": len(results),
        "rejected_count": len(results) - len(failed),
        "falsely_accepted_count": len(failed),
        "attacks_by_receipt_chain": dict(sorted(by_chain.items())),
        "results": results,
        "falsely_accepted": [row["attack"] for row in failed],
        "passed": not failed,
    }


__all__ = [
    "ACCEPTED",
    "GATE_ORDER",
    "REJECTED",
    "UNREACHABLE",
    "Attack",
    "attack_matrix",
    "first_item",
    "read_raw",
    "receipt_path",
    "reseal",
    "run_attack",
    "run_attack_matrix",
    "snapshot_manifest_path",
    "snapshot_receipt_path",
    "write_raw",
]
