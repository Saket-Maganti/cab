"""Hostile tests for the manual offline-import chain.

Every test here builds a *complete* synthetic import chain in a temporary
directory, mutates exactly one thing, and asserts that a real downstream API
refuses.  Nothing is asserted about a hand-written dict: the mutations are
applied to the sealed artifacts on disk, and the refusal has to come from the
same code path production would take.

Everything in this module is fixture-only and provider-free.  The synthetic
judgements are not human evidence and are sealed under a temporary key that
exists only for the duration of the test.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import pytest

from causal_agent_bench.review_ready_v2.adjudication import STAGE1, STAGE2
from causal_agent_bench.review_ready_v2.keys import create_external_key
from causal_agent_bench.review_ready_v2.manual_import import (
    QUALIFICATION_FORM,
    STAGE1_ADJUDICATION,
    STAGE1_REVIEW_FORM,
    STAGE2_ADJUDICATION,
    STAGE2_REVIEW_FORM,
    UNCLASSIFIED,
    ManualImportError,
    classify_file,
    discover_completed_review,
    select_evidence_set,
)
from causal_agent_bench.review_ready_v2.manual_import_chain import (
    ImportChainError,
    ImportWorkspace,
    build_disagreement_queue,
    build_final_adjudicated_records,
    compute_agreement,
    import_adjudication,
    import_review_submissions,
    record_coordinator_waiver,
    verify_imported_snapshot,
)
from causal_agent_bench.review_ready_v2.manual_import_gates import (
    authorize_model_execution,
    build_exclusion_register,
    lock_reviewed_slice,
    run_c10,
)
from causal_agent_bench.review_ready_v2.receipts import (
    COORDINATOR_KEY_ENV,
    MANUAL_IMPORT_ORIGIN,
    PRODUCTION_ORIGIN,
    ReceiptError,
    coordinator_authority,
    manual_import_authority,
    verify_receipt,
)
from causal_agent_bench.review_ready_v2.roles import REVIEW_ROLES, REVIEWER_A, REVIEWER_B
from causal_agent_bench.review_ready_v2.stage1 import REVIEW_FORM_COLUMNS
from causal_agent_bench.review_ready_v2.stage2 import (
    STAGE2_FORM_COLUMNS,
    STAGE2_SUBSTANTIVE_DIMENSIONS,
)

PACKET = "compact20-review-ready-v2"
PAIRS = [f"pair-{index:02d}" for index in range(1, 21)]
FREEZE = "f" * 64
COMMITMENT = "c" * 64
COMMIT = "a" * 40

#: The one pair whose reviewers disagree, so every adjudication path is exercised.
DISPUTED = PAIRS[0]

CONTRACT: dict[str, Any] = {
    "claim_id": "C10",
    "expected_pair_count": 20,
    "min_raw_agreement": 0.8,
    "min_independent_reviewers": 2,
    "packet_version": PACKET,
    "reject_synthetic_fixtures": True,
    "stage2_acceptance_policy_version": "cab_stage2_acceptance_policy_v1",
}


# --------------------------------------------------------------------------
# synthetic evidence
# --------------------------------------------------------------------------


def _stage1_row(item_id: str, *, ambiguity: str) -> str:
    values = {
        "reviewer_item_id": item_id,
        "task_clarity": "5",
        "clean_goal_clear": "yes",
        "clean_evidence_sufficient": "yes",
        "clean_solvable": "yes",
        "intervention_understandable": "yes",
        "intended_factor_identifiable": "yes",
        "goal_preserved": "yes",
        "single_factor_isolation": "yes",
        "preserved_invariants_hold": "yes",
        "primitive_evidence_adequate": "yes",
        "declared_tools_adequate": "yes",
        "intervention_realistic": "4",
        "ambiguity_present": ambiguity,
        "response_space_structurally_valid": "yes",
        "exclude_item": "no",
        "reviewer_confidence": "5",
        "notes": "synthetic fixture note" if ambiguity == "material" else "",
    }
    return ",".join(f'"{values[column]}"' for column in REVIEW_FORM_COLUMNS)


def _stage2_row(item_id: str, *, gold: str) -> str:
    values = {"reviewer_item_id": item_id}
    for dimension in STAGE2_SUBSTANTIVE_DIMENSIONS:
        values[dimension] = "YES"
    values["gold_correct"] = gold
    values["exclude_item"] = "NO"
    values["reviewer_confidence"] = "5"
    values["notes"] = "synthetic fixture note" if gold != "YES" else ""
    return ",".join(f'"{values[column]}"' for column in STAGE2_FORM_COLUMNS)


def _write_csv(path: Path, header: tuple[str, ...], rows: list[str]) -> Path:
    path.write_text(",".join(header) + "\n" + "\n".join(rows) + "\n")
    return path


def _mappings() -> dict[str, dict[str, str]]:
    # Reviewer B sees the same pairs in reverse order, so a role swap is visible.
    return {
        REVIEWER_A: {f"RA-{index + 1:02d}": pair for index, pair in enumerate(PAIRS)},
        REVIEWER_B: {f"RB-{index + 1:02d}": pair for index, pair in enumerate(reversed(PAIRS))},
    }


def _applicability() -> dict[str, dict[str, bool]]:
    return {pair: dict.fromkeys(STAGE2_SUBSTANTIVE_DIMENSIONS, True) for pair in PAIRS}


def _build_evidence(directory: Path) -> dict[str, Path]:
    """Write one complete, internally consistent set of completed forms."""

    directory.mkdir(parents=True, exist_ok=True)
    mappings = _mappings()
    paths: dict[str, Path] = {}

    for role, prefix in ((REVIEWER_A, "RA"), (REVIEWER_B, "RB")):
        mapping = mappings[role]
        stage1_rows = [
            _stage1_row(
                item_id,
                # Only Reviewer B calls the disputed pair materially ambiguous.
                ambiguity=("material" if pair == DISPUTED and role == REVIEWER_B else "none"),
            )
            for item_id, pair in sorted(mapping.items())
        ]
        paths[f"{STAGE1_REVIEW_FORM}:{role}"] = _write_csv(
            directory / f"s1_{prefix}.csv", REVIEW_FORM_COLUMNS, stage1_rows
        )
        stage2_rows = [
            _stage2_row(
                item_id,
                gold=("UNSURE" if pair == DISPUTED and role == REVIEWER_B else "YES"),
            )
            for item_id, pair in sorted(mapping.items())
        ]
        paths[f"{STAGE2_REVIEW_FORM}:{role}"] = _write_csv(
            directory / f"s2_{prefix}.csv", STAGE2_FORM_COLUMNS, stage2_rows
        )

    adjudication_header = (
        "pair_id",
        "dimension",
        "final_value",
        "exclude_item",
        "rationale",
        "evidence_reference",
        "confidence",
    )
    paths[STAGE1_ADJUDICATION] = _write_csv(
        directory / "adj1.csv",
        adjudication_header,
        [f'"{DISPUTED}","ambiguity_present","material","NO","fixture rationale","fixture ref","5"'],
    )
    paths[STAGE2_ADJUDICATION] = _write_csv(
        directory / "adj2.csv",
        adjudication_header,
        [f'"{DISPUTED}","gold_correct","YES","NO","fixture rationale","fixture ref","5"'],
    )
    return paths


@pytest.fixture
def chain(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """A complete, valid, sealed import chain ready to be attacked."""

    repo = tmp_path / "repo"
    repo.mkdir()
    monkeypatch.setenv(COORDINATOR_KEY_ENV, str(tmp_path / "keys" / "coordinator.key"))
    create_external_key(COORDINATOR_KEY_ENV, repo)

    evidence = _build_evidence(tmp_path / "evidence")
    private_root = tmp_path / "packet"
    workspace = ImportWorkspace.open(private_root, repo, packet_version=PACKET)

    result = discover_completed_review([tmp_path / "evidence"])
    chosen = select_evidence_set(result)

    waiver = record_coordinator_waiver(
        workspace,
        evidence_inventory_sha256="0" * 64,
        qualification_discovered=False,
        exact_commit=COMMIT,
        scientific_freeze_sha256=FREEZE,
        packet_commitment=COMMITMENT,
    )
    mappings = _mappings()
    applicability_by_pair = _applicability()
    applicability_by_item = {
        item_id: applicability_by_pair[pair]
        for role in REVIEW_ROLES
        for item_id, pair in mappings[role].items()
    }
    expected_item_ids = {role: sorted(mappings[role]) for role in REVIEW_ROLES}

    for stage, kind in ((STAGE1, STAGE1_REVIEW_FORM), (STAGE2, STAGE2_REVIEW_FORM)):
        import_review_submissions(
            workspace,
            stage=stage,
            candidates={role: chosen[f"{kind}:{role}"] for role in REVIEW_ROLES},
            expected_item_ids=expected_item_ids,
            applicability=applicability_by_item if stage == STAGE2 else None,
            waiver=waiver,
            packet_commitment=COMMITMENT,
            scientific_freeze_sha256=FREEZE,
            exact_commit=COMMIT,
            review_schema_version="cab_stage1_review_form_v2",
        )
    for stage, kind in ((STAGE1, STAGE1_ADJUDICATION), (STAGE2, STAGE2_ADJUDICATION)):
        build_disagreement_queue(
            workspace,
            stage=stage,
            mappings=mappings,
            applicability=applicability_by_pair if stage == STAGE2 else None,
        )
        import_adjudication(workspace, stage=stage, candidate=chosen[kind])

    compute_agreement(workspace, mappings=mappings)
    build_final_adjudicated_records(
        workspace,
        mappings=mappings,
        applicability=applicability_by_pair,
        expected_pair_count=20,
    )
    return {
        "workspace": workspace,
        "repo": repo,
        "private_root": private_root,
        "mappings": mappings,
        "applicability": applicability_by_pair,
        "evidence": evidence,
        "chosen": chosen,
        "tmp_path": tmp_path,
    }


def _c10(chain: dict[str, Any]) -> dict[str, Any]:
    return run_c10(
        chain["workspace"],
        contract=CONTRACT,
        mappings=chain["mappings"],
        applicability=chain["applicability"],
        packet_commitment=COMMITMENT,
        scientific_freeze_sha256=FREEZE,
        exact_commit=COMMIT,
    )


def _tamper(path: Path, mutate) -> None:
    """Rewrite a sealed artifact on disk without re-sealing it."""

    payload = json.loads(path.read_text())
    mutate(payload)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


# --------------------------------------------------------------------------
# positive: the supplied evidence imports and reaches C10
# --------------------------------------------------------------------------


def test_a_complete_import_reaches_c10_and_authorizes_only_the_pilot(chain) -> None:
    workspace = chain["workspace"]
    report = _c10(chain)

    assert report["c10_state"] == "PASS"
    assert report["included_pair_count"] == 20
    assert report["excluded_pair_count"] == 0
    assert report["unresolved_pair_count"] == 0
    # The qualifier travels with the result rather than sitting in a footnote.
    assert report["declaration_mode"] == "COORDINATOR_WAIVER"
    assert report["declaration_files_collected"] is False
    assert report["qualification_pass_verified"] is False
    assert "COORDINATOR_DECLARATION_WAIVER_RECORDED" in report["waiver_statuses"]

    build_exclusion_register(workspace)
    lock_reviewed_slice(
        workspace,
        pair_content_hashes=dict.fromkeys(PAIRS, "d" * 64),
        scorer_version="scorer-v1",
        split_version=PACKET,
        exact_commit=COMMIT,
    )
    authorization = authorize_model_execution(workspace, exact_commit=COMMIT)
    assert authorization["authorized_study"] == "compact20_reviewed_pilot"
    assert authorization["authorized_pair_count"] == 20
    assert authorization["paid_providers_authorized"] is False
    # Nothing larger is authorized by this pilot passing.
    assert "scale100_confirmatory" in authorization["withheld_studies"]
    assert "main500_confirmatory" in authorization["withheld_studies"]


def test_the_chain_never_claims_a_reviewer_declaration_or_a_qualification_pass(chain) -> None:
    report = _c10(chain)
    text = json.dumps(report)
    assert "REVIEWER_DECLARATIONS_CONFIRMED" not in text
    assert report["qualification_mode"] == "COORDINATOR_WAIVER"
    assert report["qualification_evidence_imported"] is False


def test_agreement_is_computed_from_raw_pre_adjudication_judgements(chain) -> None:
    agreement = chain["workspace"].read("agreement")
    assert agreement["adjudicated_values_used"] is False
    # Nineteen of twenty pairs agree on the disputed Stage-2 dimension.
    assert agreement["stage2"]["per_dimension"]["gold_correct"]["agreed"] == 19
    assert agreement["stage1"]["per_dimension"]["exclude_item"]["raw_agreement"] == 1.0


# --------------------------------------------------------------------------
# origin separation
# --------------------------------------------------------------------------


def test_a_manual_import_receipt_cannot_authenticate_as_production(chain, tmp_path) -> None:
    workspace = chain["workspace"]
    receipt = workspace.read("coordinator_waiver")
    assert receipt["artifact_origin"] == MANUAL_IMPORT_ORIGIN

    production = coordinator_authority(chain["repo"])
    with pytest.raises(ReceiptError):
        verify_receipt(production, receipt)


def test_a_production_receipt_cannot_authenticate_as_a_manual_import(chain) -> None:
    from causal_agent_bench.review_ready_v2.receipts import seal_receipt

    production = coordinator_authority(chain["repo"])
    sealed = seal_receipt(production, {"receipt_kind": "stage1_submission"})
    assert sealed["artifact_origin"] == PRODUCTION_ORIGIN
    with pytest.raises(ReceiptError):
        verify_receipt(manual_import_authority(chain["repo"]), sealed)


# --------------------------------------------------------------------------
# mutations of sealed imported artifacts
# --------------------------------------------------------------------------


@pytest.mark.parametrize("stage", [STAGE1, STAGE2])
@pytest.mark.parametrize("role", [REVIEWER_A, REVIEWER_B])
def test_a_changed_judgement_cell_after_import_fails(chain, stage, role) -> None:
    snapshot = chain["workspace"].receipts / f"committed_{stage}" / f"{role}.{stage}_submission.json"
    column = "clean_solvable" if stage == STAGE1 else "scorer_compatible"
    replacement = "no" if stage == STAGE1 else "NO"

    def mutate(payload: dict[str, Any]) -> None:
        first = sorted(payload["judgements"])[0]
        payload["judgements"][first][column] = replacement

    _tamper(snapshot, mutate)
    with pytest.raises(ImportChainError):
        verify_imported_snapshot(chain["workspace"], stage=stage)


@pytest.mark.parametrize("stage", [STAGE1, STAGE2])
def test_a_changed_note_after_import_fails(chain, stage) -> None:
    snapshot = (
        chain["workspace"].receipts / f"committed_{stage}" / f"{REVIEWER_B}.{stage}_submission.json"
    )

    def mutate(payload: dict[str, Any]) -> None:
        first = sorted(payload["judgements"])[0]
        payload["judgements"][first]["notes"] = "a different rationale entirely"

    _tamper(snapshot, mutate)
    with pytest.raises(ImportChainError):
        verify_imported_snapshot(chain["workspace"], stage=stage)


@pytest.mark.parametrize("stage", [STAGE1, STAGE2])
def test_keeping_the_payload_hash_while_editing_content_fails(chain, stage) -> None:
    """The confirmed exploit: retain ``submission_sha256``, change a judgement."""

    snapshot = (
        chain["workspace"].receipts / f"committed_{stage}" / f"{REVIEWER_A}.{stage}_submission.json"
    )
    original = json.loads(snapshot.read_text())["submission_sha256"]

    def mutate(payload: dict[str, Any]) -> None:
        first = sorted(payload["judgements"])[0]
        payload["judgements"][first]["reviewer_confidence"] = "3"
        payload["submission_sha256"] = original  # deliberately unchanged

    _tamper(snapshot, mutate)
    with pytest.raises(ImportChainError):
        verify_imported_snapshot(chain["workspace"], stage=stage)


@pytest.mark.parametrize("stage", [STAGE1, STAGE2])
def test_keeping_the_canonical_hash_while_changing_the_payload_hash_fails(chain, stage) -> None:
    snapshot = (
        chain["workspace"].receipts / f"committed_{stage}" / f"{REVIEWER_A}.{stage}_submission.json"
    )

    def mutate(payload: dict[str, Any]) -> None:
        payload["submission_sha256"] = "9" * 64  # canonical_content_sha256 left alone

    _tamper(snapshot, mutate)
    with pytest.raises(ImportChainError):
        verify_imported_snapshot(chain["workspace"], stage=stage)


@pytest.mark.parametrize("stage", [STAGE1, STAGE2])
def test_swapping_the_two_reviewers_snapshots_fails(chain, stage) -> None:
    directory = chain["workspace"].receipts / f"committed_{stage}"
    a = directory / f"{REVIEWER_A}.{stage}_submission.json"
    b = directory / f"{REVIEWER_B}.{stage}_submission.json"
    a_bytes, b_bytes = a.read_bytes(), b.read_bytes()
    a.write_bytes(b_bytes)
    b.write_bytes(a_bytes)
    with pytest.raises(ImportChainError):
        verify_imported_snapshot(chain["workspace"], stage=stage)


@pytest.mark.parametrize("stage", [STAGE1, STAGE2])
def test_a_changed_snapshot_manifest_fails(chain, stage) -> None:
    manifest = chain["workspace"].receipts / f"committed_{stage}" / "manifest.json"

    def mutate(payload: dict[str, Any]) -> None:
        payload["expected_item_count"] = 19

    _tamper(manifest, mutate)
    with pytest.raises(ImportChainError):
        verify_imported_snapshot(chain["workspace"], stage=stage)


@pytest.mark.parametrize("stage", [STAGE1, STAGE2])
def test_a_changed_adjudication_decision_fails_at_c10(chain, stage) -> None:
    path = chain["workspace"].path_for(f"{stage}_adjudication")

    def mutate(payload: dict[str, Any]) -> None:
        payload["decisions"][0]["rationale"] = "a different rationale"

    _tamper(path, mutate)
    with pytest.raises(ImportChainError):
        _c10(chain)


@pytest.mark.parametrize("stage", [STAGE1, STAGE2])
def test_a_changed_adjudication_verdict_fails_at_c10(chain, stage) -> None:
    path = chain["workspace"].path_for(f"{stage}_adjudication")

    def mutate(payload: dict[str, Any]) -> None:
        payload["decisions"][0]["exclude_item"] = "YES"

    _tamper(path, mutate)
    with pytest.raises(ImportChainError):
        _c10(chain)


def test_a_missing_waiver_fails(chain) -> None:
    chain["workspace"].path_for("coordinator_waiver").unlink()
    with pytest.raises(ImportChainError):
        verify_imported_snapshot(chain["workspace"], stage=STAGE1)


def test_a_changed_waiver_fails(chain) -> None:
    def mutate(payload: dict[str, Any]) -> None:
        payload["declaration_files_collected"] = True

    _tamper(chain["workspace"].path_for("coordinator_waiver"), mutate)
    with pytest.raises(ImportChainError):
        verify_imported_snapshot(chain["workspace"], stage=STAGE1)


def test_a_waiver_that_claims_declarations_were_confirmed_cannot_be_resealed(chain) -> None:
    """Re-sealing needs the key; even with it, the write-once rule refuses."""

    with pytest.raises(ImportChainError):
        record_coordinator_waiver(
            chain["workspace"],
            evidence_inventory_sha256="1" * 64,
            qualification_discovered=True,
            exact_commit=COMMIT,
            scientific_freeze_sha256=FREEZE,
            packet_commitment=COMMITMENT,
        )


def test_a_changed_agreement_report_fails_c10(chain) -> None:
    def mutate(payload: dict[str, Any]) -> None:
        payload["stage2"]["overall_raw_agreement"] = 1.0

    _tamper(chain["workspace"].path_for("agreement"), mutate)
    with pytest.raises(ImportChainError):
        _c10(chain)


def test_a_changed_final_record_fails_c10(chain) -> None:
    def mutate(payload: dict[str, Any]) -> None:
        payload["included_count"] = 19

    _tamper(chain["workspace"].path_for("final_adjudicated_records"), mutate)
    with pytest.raises(ImportChainError):
        _c10(chain)


def test_a_wrong_freeze_fails(chain) -> None:
    with pytest.raises(ImportChainError):
        verify_imported_snapshot(
            chain["workspace"],
            stage=STAGE1,
            expected_scientific_freeze_sha256="e" * 64,
        )


def test_a_wrong_commit_fails(chain) -> None:
    with pytest.raises(ImportChainError):
        verify_imported_snapshot(
            chain["workspace"], stage=STAGE1, expected_frozen_source_commit="b" * 40
        )


def test_a_wrong_packet_commitment_fails(chain) -> None:
    with pytest.raises(ImportChainError):
        verify_imported_snapshot(
            chain["workspace"], stage=STAGE1, expected_packet_commitment="9" * 64
        )


def test_a_live_receipt_that_diverges_from_the_snapshot_is_a_conflict(chain) -> None:
    live = chain["workspace"].path_for(f"{STAGE1}_submission_{REVIEWER_A}")

    def mutate(payload: dict[str, Any]) -> None:
        payload["row_count"] = 19

    _tamper(live, mutate)
    with pytest.raises(ImportChainError):
        verify_imported_snapshot(chain["workspace"], stage=STAGE1)


def test_the_queue_cannot_be_rebuilt_after_adjudication(chain) -> None:
    with pytest.raises(ImportChainError):
        build_disagreement_queue(
            chain["workspace"], stage=STAGE1, mappings=chain["mappings"]
        )


def test_an_adjudication_cannot_be_replaced(chain) -> None:
    with pytest.raises(ImportChainError):
        import_adjudication(
            chain["workspace"], stage=STAGE1, candidate=chain["chosen"][STAGE1_ADJUDICATION]
        )


def test_evidence_cannot_be_reimported_over_a_commitment(chain) -> None:
    with pytest.raises(ImportChainError):
        import_review_submissions(
            chain["workspace"],
            stage=STAGE1,
            candidates={
                role: chain["chosen"][f"{STAGE1_REVIEW_FORM}:{role}"] for role in REVIEW_ROLES
            },
            expected_item_ids={role: sorted(chain["mappings"][role]) for role in REVIEW_ROLES},
            applicability=None,
            waiver=chain["workspace"].read("coordinator_waiver"),
            packet_commitment=COMMITMENT,
            scientific_freeze_sha256=FREEZE,
            exact_commit=COMMIT,
            review_schema_version="cab_stage1_review_form_v2",
        )


def test_a_slice_cannot_be_locked_over_a_mutated_c10(chain) -> None:
    _c10(chain)
    build_exclusion_register(chain["workspace"])

    def mutate(payload: dict[str, Any]) -> None:
        payload["c10_state"] = "PASS"
        payload["included_pair_count"] = 21

    _tamper(chain["workspace"].path_for("c10_report"), mutate)
    with pytest.raises(ImportChainError):
        lock_reviewed_slice(
            chain["workspace"],
            pair_content_hashes=dict.fromkeys(PAIRS, "d" * 64),
            scorer_version="scorer-v1",
            split_version=PACKET,
            exact_commit=COMMIT,
        )


def test_execution_cannot_be_authorized_over_a_mutated_slice_lock(chain) -> None:
    workspace = chain["workspace"]
    _c10(chain)
    build_exclusion_register(workspace)
    lock_reviewed_slice(
        workspace,
        pair_content_hashes=dict.fromkeys(PAIRS, "d" * 64),
        scorer_version="scorer-v1",
        split_version=PACKET,
        exact_commit=COMMIT,
    )

    def mutate(payload: dict[str, Any]) -> None:
        payload["locked_pair_ids"] = PAIRS[:5]

    _tamper(workspace.path_for("slice_lock"), mutate)
    with pytest.raises(ImportChainError):
        authorize_model_execution(workspace, exact_commit=COMMIT)


def test_authorization_refuses_a_lock_taken_at_another_commit(chain) -> None:
    workspace = chain["workspace"]
    _c10(chain)
    build_exclusion_register(workspace)
    lock_reviewed_slice(
        workspace,
        pair_content_hashes=dict.fromkeys(PAIRS, "d" * 64),
        scorer_version="scorer-v1",
        split_version=PACKET,
        exact_commit=COMMIT,
    )
    with pytest.raises(ImportChainError):
        authorize_model_execution(workspace, exact_commit="b" * 40)


def test_a_slice_cannot_be_locked_without_a_pair_content_hash(chain) -> None:
    _c10(chain)
    build_exclusion_register(chain["workspace"])
    with pytest.raises(ImportChainError):
        lock_reviewed_slice(
            chain["workspace"],
            pair_content_hashes=dict.fromkeys(PAIRS[:10], "d" * 64),
            scorer_version="scorer-v1",
            split_version=PACKET,
            exact_commit=COMMIT,
        )


def test_a_symlinked_receipt_is_refused(chain, tmp_path) -> None:
    path = chain["workspace"].path_for("coordinator_waiver")
    target = tmp_path / "elsewhere.json"
    target.write_text(path.read_text())
    path.unlink()
    path.symlink_to(target)
    with pytest.raises(ImportChainError):
        chain["workspace"].read("coordinator_waiver")


# --------------------------------------------------------------------------
# discovery is content-based
# --------------------------------------------------------------------------


def test_arbitrary_filenames_classify_identically(tmp_path) -> None:
    evidence = _build_evidence(tmp_path / "evidence")
    renamed = tmp_path / "renamed"
    renamed.mkdir()
    for index, path in enumerate(sorted(evidence.values())):
        shutil.copy(path, renamed / f"final FINAL v{index} (2).csv")

    original = {
        slot: candidate.canonical_sha256
        for slot, candidate in select_evidence_set(
            discover_completed_review([tmp_path / "evidence"])
        ).items()
    }
    shuffled = {
        slot: candidate.canonical_sha256
        for slot, candidate in select_evidence_set(discover_completed_review([renamed])).items()
    }
    assert original == shuffled


def test_swapping_the_two_reviewers_filenames_changes_nothing(tmp_path) -> None:
    evidence = _build_evidence(tmp_path / "evidence")
    swapped = tmp_path / "swapped"
    swapped.mkdir()
    shutil.copy(evidence[f"{STAGE1_REVIEW_FORM}:{REVIEWER_A}"], swapped / "s1_RB.csv")
    shutil.copy(evidence[f"{STAGE1_REVIEW_FORM}:{REVIEWER_B}"], swapped / "s1_RA.csv")
    for slot in (
        f"{STAGE2_REVIEW_FORM}:{REVIEWER_A}",
        f"{STAGE2_REVIEW_FORM}:{REVIEWER_B}",
        STAGE1_ADJUDICATION,
        STAGE2_ADJUDICATION,
    ):
        shutil.copy(evidence[slot], swapped / evidence[slot].name)

    chosen = select_evidence_set(discover_completed_review([swapped]))
    # The role comes from the opaque namespace inside the file, not the name.
    assert chosen[f"{STAGE1_REVIEW_FORM}:{REVIEWER_A}"].path.name == "s1_RB.csv"
    assert chosen[f"{STAGE1_REVIEW_FORM}:{REVIEWER_A}"].namespace == "RA"


def test_changed_line_endings_preserve_the_canonical_hash(tmp_path) -> None:
    evidence = _build_evidence(tmp_path / "evidence")
    source = evidence[f"{STAGE1_REVIEW_FORM}:{REVIEWER_A}"]
    crlf = tmp_path / "crlf.csv"
    crlf.write_bytes(source.read_bytes().replace(b"\n", b"\r\n"))

    original = classify_file(source)
    converted = classify_file(crlf)
    assert converted.raw_sha256 != original.raw_sha256
    assert converted.canonical_sha256 == original.canonical_sha256


def test_reordered_rows_preserve_the_canonical_hash(tmp_path) -> None:
    evidence = _build_evidence(tmp_path / "evidence")
    source = evidence[f"{STAGE1_REVIEW_FORM}:{REVIEWER_A}"]
    lines = source.read_text().splitlines()
    reordered = tmp_path / "reordered.csv"
    reordered.write_text("\n".join([lines[0], *reversed(lines[1:])]) + "\n")
    assert classify_file(reordered).canonical_sha256 == classify_file(source).canonical_sha256


def test_one_changed_cell_changes_the_canonical_hash(tmp_path) -> None:
    evidence = _build_evidence(tmp_path / "evidence")
    source = evidence[f"{STAGE1_REVIEW_FORM}:{REVIEWER_A}"]
    edited = tmp_path / "edited.csv"
    edited_text = source.read_text().replace('"4","none"', '"3","none"', 1)
    assert edited_text != source.read_text(), "the fixture edit must actually change a cell"
    edited.write_text(edited_text)
    assert classify_file(edited).canonical_sha256 != classify_file(source).canonical_sha256


def test_two_conflicting_files_for_one_role_fail_closed(tmp_path) -> None:
    evidence = _build_evidence(tmp_path / "evidence")
    source = evidence[f"{STAGE1_REVIEW_FORM}:{REVIEWER_A}"]
    conflicting = tmp_path / "evidence" / "another_copy.csv"
    conflicting.write_text(source.read_text().replace('"4","none"', '"3","none"', 1))

    with pytest.raises(ManualImportError, match="AMBIGUOUS"):
        select_evidence_set(discover_completed_review([tmp_path / "evidence"]))


def test_a_byte_identical_duplicate_is_tolerated(tmp_path) -> None:
    evidence = _build_evidence(tmp_path / "evidence")
    shutil.copy(
        evidence[f"{STAGE1_REVIEW_FORM}:{REVIEWER_A}"], tmp_path / "evidence" / "copy.csv"
    )
    chosen = select_evidence_set(discover_completed_review([tmp_path / "evidence"]))
    assert chosen[f"{STAGE1_REVIEW_FORM}:{REVIEWER_A}"].namespace == "RA"


def test_a_mixed_namespace_form_is_refused(tmp_path) -> None:
    evidence = _build_evidence(tmp_path / "evidence")
    source = evidence[f"{STAGE1_REVIEW_FORM}:{REVIEWER_A}"]
    mixed = tmp_path / "mixed.csv"
    mixed.write_text(source.read_text().replace("RA-01", "RB-01", 1))
    assert "rows_span_more_than_one_opaque_namespace" in classify_file(mixed).problems


def test_a_wrong_schema_file_is_unclassified(tmp_path) -> None:
    path = tmp_path / "unrelated.csv"
    path.write_text("a,b,c\n1,2,3\n")
    assert classify_file(path).kind == UNCLASSIFIED


def test_a_formula_injection_cell_is_flagged(tmp_path) -> None:
    evidence = _build_evidence(tmp_path / "evidence")
    source = evidence[f"{STAGE1_REVIEW_FORM}:{REVIEWER_B}"]
    risky = tmp_path / "risky.csv"
    risky.write_text(source.read_text().replace("synthetic fixture note", "=cmd|'/c calc'!A1"))
    assert "cell_would_execute_as_a_spreadsheet_formula" in classify_file(risky).problems


def test_a_qualification_form_is_not_mistaken_for_stage1(tmp_path) -> None:
    rows = [_stage1_row(f"Q4-{index:08X}", ambiguity="none") for index in range(5)]
    path = _write_csv(tmp_path / "q.csv", REVIEW_FORM_COLUMNS, rows)
    candidate = classify_file(path)
    assert candidate.kind == QUALIFICATION_FORM
    assert candidate.role is None


def test_an_incomplete_evidence_set_fails_closed(tmp_path) -> None:
    evidence = _build_evidence(tmp_path / "evidence")
    evidence[STAGE2_ADJUDICATION].unlink()
    with pytest.raises(ManualImportError, match="incomplete"):
        select_evidence_set(discover_completed_review([tmp_path / "evidence"]))


def test_requiring_qualification_blocks_when_none_was_discovered(tmp_path) -> None:
    _build_evidence(tmp_path / "evidence")
    with pytest.raises(ManualImportError, match="QUALIFICATION_EVIDENCE_MISSING"):
        select_evidence_set(
            discover_completed_review([tmp_path / "evidence"]), require_qualification=True
        )


def test_a_stage2_adjudication_cannot_answer_the_stage1_queue(chain, tmp_path) -> None:
    """Decision dimensions decide the stage; a filename cannot override them."""

    workspace = chain["workspace"]
    stage2_file = chain["chosen"][STAGE2_ADJUDICATION]
    assert stage2_file.stage == STAGE2
    # The Stage-1 adjudication receipt is already sealed, so prove the classifier
    # itself refuses the cross-stage substitution.
    with pytest.raises(ImportChainError, match=r"another stage|already sealed"):
        import_adjudication(workspace, stage=STAGE1, candidate=stage2_file)
