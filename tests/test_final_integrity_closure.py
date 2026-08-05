"""Hostile regression suite for the final integrity closure.

The defect this closes was real and was reproduced against commit ``131cd10``:
Stage-1 commitment bound only the reviewer's uploaded CSV hash, so a coordinator
could edit the parsed judgements inside the sealed submission receipt, keep the
original ``submission_sha256``, re-seal with a valid MAC, and leave every
downstream gate — up to and including ``C10_MECHANICS_PASS`` — satisfied.

Every test here drives the real coordinator APIs.  Nothing monkeypatches a gate,
nothing reaches into a private helper to shortcut a check, and every mutation is
written to disk the way an attacker with the sealing key would write it.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from causal_agent_bench.review_ready_v2.adjudication import STAGE1, STAGE2
from causal_agent_bench.review_ready_v2.commitment_integrity import (
    RETIRED_STAGE1_COMMITMENT_SCHEMA_VERSIONS,
    STAGE1_COMMITMENT_SCHEMA_VERSION,
    CommitmentIntegrityError,
    canonical_adjudication_digest,
    canonical_assignment_registry_digest,
    canonical_declaration_digest,
    canonical_qualification_digest,
    canonical_queue_digest,
    canonical_stage1_judgements_digest,
    canonical_stage2_judgements_digest,
    receipt_content_sha256,
    reject_non_json,
    write_private_json,
)
from causal_agent_bench.review_ready_v2.fixture_e2e import (
    FIXTURE_PAIR_COUNT,
    FixtureWorkflow,
    run_fixture_e2e,
)
from causal_agent_bench.review_ready_v2.hostile_integrity import (
    Attack,
    attack_matrix,
    first_item,
    read_raw,
    receipt_path,
    reseal,
    run_attack,
    snapshot_receipt_path,
)
from causal_agent_bench.review_ready_v2.roles import REVIEW_ROLES, REVIEWER_A, REVIEWER_B
from causal_agent_bench.review_ready_v2.workflow import (
    RETIRED_WORKFLOW_SCHEMA_VERSIONS,
    WORKFLOW_SCHEMA_VERSION,
    ReviewWorkspace,
    WorkflowError,
    verify_committed_stage1_snapshot,
    verify_committed_stage2_snapshot,
)

REPO_ROOT = Path(__file__).resolve().parents[1]

ATTACKS = attack_matrix()


# --------------------------------------------------------------------------
# the confirmed exploit
# --------------------------------------------------------------------------


def test_the_confirmed_post_commit_mutation_exploit_is_closed(tmp_path: Path) -> None:
    """The exact independently reproduced attack, start to finish.

    Complete the workflow, then edit a committed judgement, retain the original
    ``submission_sha256``, and re-seal.  Before the repair this chain still
    reached ``C10_MECHANICS_PASS``.
    """

    driver = FixtureWorkflow.create(tmp_path).advance_to("settle")
    baseline = driver.c10()
    assert baseline["mechanics_status"] == "C10_MECHANICS_PASS"

    commitment_before = read_raw(receipt_path(driver, "stage1_commitment"))
    snapshot = snapshot_receipt_path(driver, REVIEWER_A, STAGE1)
    original_payload_hash = read_raw(snapshot)["submission_sha256"]
    before_receipt_sha = read_raw(snapshot)["receipt_sha256"]

    def mutate(receipt: dict[str, Any]) -> None:
        receipt["judgements"][first_item(receipt)]["notes"] = "POST-COMMIT TAMPERING"
        receipt["submission_sha256"] = original_payload_hash

    resealed = reseal(snapshot, mutate)

    # The attacker's preconditions all hold: the commitment is untouched, the
    # payload hash still matches, and the forged receipt authenticates.
    commitment_after = read_raw(receipt_path(driver, "stage1_commitment"))
    assert commitment_before == commitment_after
    assert resealed["submission_sha256"] == original_payload_hash
    assert resealed["receipt_sha256"] != before_receipt_sha

    # And it changes nothing downstream, because the canonical judgement digest
    # and the sealed receipt file hash are both bound by the commitment.
    with pytest.raises(WorkflowError, match="changed since it was committed"):
        verify_committed_stage1_snapshot(driver.workspace)
    with pytest.raises(WorkflowError):
        driver.workspace._paired(driver.mappings, STAGE1)

    report = driver.c10()
    assert report["mechanics_status"] == "C10_MECHANICS_FAIL"
    assert report["status"] == "C10_PENDING_GENUINE_REVIEW"
    assert report["counts_as_genuine_evidence"] is False


def test_a_conflicting_live_receipt_after_commitment_is_detected(tmp_path: Path) -> None:
    """Tampering must be visible even where nothing downstream would read it."""

    driver = FixtureWorkflow.create(tmp_path).advance_to("commit_stage1")
    live = receipt_path(driver, f"stage1_submission_{REVIEWER_A}")
    reseal(live, lambda receipt: receipt.update({"row_count": 99}))
    with pytest.raises(WorkflowError, match="stage1_live_receipts_not_conflicting"):
        verify_committed_stage1_snapshot(driver.workspace)


# --------------------------------------------------------------------------
# the full hostile matrix
# --------------------------------------------------------------------------


@pytest.mark.parametrize("attack", ATTACKS, ids=lambda attack: attack.name)
def test_hostile_attack_is_rejected(attack: Attack, tmp_path: Path) -> None:
    """Every attack fails no later than the first gate that consumes it."""

    result = run_attack(attack, tmp_path / "workspace")
    assert result["passed"], (
        f"{attack.name}: expected rejection by {attack.expected_gate!r}, got "
        f"{result['actual_rejection_gate']!r}; gates={result['gate_results']}"
    )
    # Not merely "something refused": the refusal is at the gate that consumes
    # the changed artifact, or the workflow refused the hostile input outright.
    assert result["actual_rejection_gate"] in ("mutation_refused", attack.expected_gate)


def test_the_matrix_covers_every_required_receipt_chain() -> None:
    """The matrix is not allowed to quietly drop a chain."""

    chains = {attack.chain for attack in ATTACKS}
    required = {
        "stage1_submission",
        "committed_stage1_snapshot",
        "stage1_commitment",
        "reviewer_declaration",
        "stage2_issuance",
        "stage2_submission",
        "adjudication",
        "agreement",
        "final_adjudicated_records",
        "exclusion_register",
        "reviewed_slice_lock",
        "c10_report",
        "execution_authorization",
        "artifact_origin",
    }
    assert required <= chains, sorted(required - chains)
    assert len(ATTACKS) >= 60


# --------------------------------------------------------------------------
# 14.5 — positive tests
# --------------------------------------------------------------------------


def test_a_normal_fixture_workflow_still_reaches_mechanics_pass(tmp_path: Path) -> None:
    driver = FixtureWorkflow.create(tmp_path).advance_to("settle")
    report = driver.finish()
    assert report["mechanics_status"] == "C10_MECHANICS_PASS"
    assert report["status"] == "C10_PENDING_GENUINE_REVIEW"
    assert report["failed_checks"] == [
        "artifact_origin_is_production",
        "every_required_evidence_binding_present",
        "evidence_counts_as_genuine",
    ]


def test_a_fixture_never_reaches_a_genuine_c10_pass() -> None:
    result = run_fixture_e2e()
    assert result["passed"], [step for step in result["steps"] if not step["passed"]]
    assert result["c10"]["status"] == "C10_PENDING_GENUINE_REVIEW"
    assert result["c10"]["counts_as_genuine_evidence"] is False
    assert result["genuine_human_judgments"] == 0
    assert result["genuine_model_trajectories"] == 0


def test_the_committed_snapshot_reverifies_from_a_fresh_process(tmp_path: Path) -> None:
    """A snapshot is verifiable from bytes on disk alone, with no live state."""

    driver = FixtureWorkflow.create(tmp_path).advance_to("settle")
    driver.finish()

    fresh = ReviewWorkspace.fixture(driver.private_root)
    fresh.packet_version = driver.workspace.packet_version
    stage1 = verify_committed_stage1_snapshot(fresh)
    stage2 = verify_committed_stage2_snapshot(fresh)
    assert sorted(stage1["receipts"]) == sorted(REVIEW_ROLES)
    assert sorted(stage2["receipts"]) == sorted(REVIEW_ROLES)
    assert all(stage1["checks"].values())
    assert all(stage2["checks"].values())


def test_canonical_digests_are_pure_functions_of_their_input(tmp_path: Path) -> None:
    """The same receipt always digests to the same value, however it is re-read."""

    driver = FixtureWorkflow.create(tmp_path).advance_to("adjudicate")
    for path, digest in (
        (snapshot_receipt_path(driver, REVIEWER_A, STAGE1), canonical_stage1_judgements_digest),
        (snapshot_receipt_path(driver, REVIEWER_A, STAGE2), canonical_stage2_judgements_digest),
        (receipt_path(driver, f"{STAGE1}_disagreement_queue"), canonical_queue_digest),
        (receipt_path(driver, f"{STAGE1}_adjudication"), canonical_adjudication_digest),
        (receipt_path(driver, f"declaration_{REVIEWER_A}"), canonical_declaration_digest),
        (receipt_path(driver, f"qualification_{REVIEWER_A}"), canonical_qualification_digest),
    ):
        first = digest(read_raw(path))
        assert first == digest(read_raw(path))
        assert first == digest(json.loads(json.dumps(read_raw(path))))
    registry = driver.workspace.assignments()
    assert canonical_assignment_registry_digest(registry) == (
        canonical_assignment_registry_digest(json.loads(json.dumps(registry)))
    )


def test_two_independent_runs_agree_on_content_derived_digests(tmp_path: Path) -> None:
    """Determinism holds exactly where the digest is a function of content.

    The queue digest is derived from the judgements alone, so two independent
    fixture runs must agree on it.  The judgement and adjudication digests
    deliberately bind sealed receipt hashes, which carry an issuance timestamp,
    so they differ across runs — that is the binding doing its job, not drift.
    """

    first = FixtureWorkflow.create(tmp_path / "a").advance_to("adjudicate")
    second = FixtureWorkflow.create(tmp_path / "b").advance_to("adjudicate")

    for role in REVIEW_ROLES:
        left = verify_committed_stage1_snapshot(first.workspace)["receipts"][role]
        right = verify_committed_stage1_snapshot(second.workspace)["receipts"][role]
        assert left["judgements"] == right["judgements"]
        assert left["submission_sha256"] == right["submission_sha256"]
    for stage in (STAGE1, STAGE2):
        assert canonical_queue_digest(
            first.workspace.read(f"{stage}_disagreement_queue")
        ) == canonical_queue_digest(second.workspace.read(f"{stage}_disagreement_queue"))


def test_canonical_content_digests_ignore_serialisation_but_not_content(
    tmp_path: Path,
) -> None:
    """Key order is not content; a single changed cell is."""

    driver = FixtureWorkflow.create(tmp_path).advance_to("commit_stage1")
    receipt = read_raw(snapshot_receipt_path(driver, REVIEWER_A, STAGE1))
    baseline = canonical_stage1_judgements_digest(receipt)

    reordered = json.loads(json.dumps(receipt))
    reordered["judgements"] = dict(reversed(list(reordered["judgements"].items())))
    assert canonical_stage1_judgements_digest(reordered) == baseline

    changed = json.loads(json.dumps(receipt))
    changed["judgements"][first_item(changed)]["notes"] = "a note that gates nothing"
    assert canonical_stage1_judgements_digest(changed) != baseline


def test_role_isolation_survives_the_committed_snapshot(tmp_path: Path) -> None:
    driver = FixtureWorkflow.create(tmp_path).advance_to("commit_stage1")
    verified = verify_committed_stage1_snapshot(driver.workspace)
    a_items = set(verified["receipts"][REVIEWER_A]["judgements"])
    b_items = set(verified["receipts"][REVIEWER_B]["judgements"])
    assert a_items and b_items
    assert not a_items & b_items
    assert all(item.startswith("RA-") for item in a_items)
    assert all(item.startswith("RB-") for item in b_items)
    assert (
        verified["canonical_judgement_hashes"][REVIEWER_A]
        != verified["canonical_judgement_hashes"][REVIEWER_B]
    )


def test_scientific_kernel_hashes_are_unchanged_by_this_repair() -> None:
    """The repair touches workflow integrity, never the twenty pairs."""

    baseline_path = (
        REPO_ROOT / "reports/final_integrity_closure/SCIENTIFIC_KERNEL_PRESERVATION_BASELINE.json"
    )
    if not baseline_path.is_file():
        pytest.skip("the preservation baseline has not been generated in this working tree")
    baseline = json.loads(baseline_path.read_text())
    commitment = json.loads(
        (REPO_ROOT / "reports/reviewer_ready_v2/PUBLIC_PACKET_COMMITMENT.json").read_text()
    )
    assert commitment["pair_content_hashes"] == baseline["pair_content_hashes"]
    assert commitment["commitment_sha256"] == baseline["public_packet_commitment_sha256"]
    assert commitment["qualification_package_hashes"] == baseline["qualification_package_hashes"]
    assert commitment["seed_commitment"] == baseline["seed_commitment"]


def test_active_private_material_remains_untracked() -> None:
    import subprocess

    tracked = subprocess.run(
        ["git", "ls-files", "private_data"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert tracked == "", tracked


# --------------------------------------------------------------------------
# schema policy
# --------------------------------------------------------------------------


def test_the_retired_commitment_schema_is_rejected_not_migrated(tmp_path: Path) -> None:
    driver = FixtureWorkflow.create(tmp_path).advance_to("commit_stage1")
    reseal(
        receipt_path(driver, "stage1_commitment"),
        lambda receipt: receipt.update(
            {"commitment_schema_version": "cab_stage1_commitment_v2"}
        ),
    )
    with pytest.raises(WorkflowError, match="retired schema"):
        verify_committed_stage1_snapshot(driver.workspace)


def test_a_commitment_with_no_schema_field_is_rejected(tmp_path: Path) -> None:
    """The pre-repair shape carried no schema field at all."""

    driver = FixtureWorkflow.create(tmp_path).advance_to("commit_stage1")
    reseal(
        receipt_path(driver, "stage1_commitment"),
        lambda receipt: receipt.pop("commitment_schema_version", None),
    )
    with pytest.raises(WorkflowError, match="retired schema"):
        verify_committed_stage1_snapshot(driver.workspace)


def test_the_active_schema_versions_are_the_new_ones() -> None:
    assert WORKFLOW_SCHEMA_VERSION == "cab_review_ready_v2_two_stage_workflow_v3"
    assert WORKFLOW_SCHEMA_VERSION not in RETIRED_WORKFLOW_SCHEMA_VERSIONS
    assert "cab_review_ready_v2_two_stage_workflow_v2" in RETIRED_WORKFLOW_SCHEMA_VERSIONS
    assert STAGE1_COMMITMENT_SCHEMA_VERSION == "cab_stage1_commitment_v3"
    assert STAGE1_COMMITMENT_SCHEMA_VERSION not in RETIRED_STAGE1_COMMITMENT_SCHEMA_VERSIONS
    assert None in RETIRED_STAGE1_COMMITMENT_SCHEMA_VERSIONS


def test_the_ambiguous_submission_hashes_field_is_gone(tmp_path: Path) -> None:
    """``submission_hashes`` meant the payload hash and was read as the receipt."""

    driver = FixtureWorkflow.create(tmp_path).advance_to("commit_stage1")
    commitment = driver.workspace.read("stage1_commitment")
    assert "submission_hashes" not in commitment
    for name in (
        "stage1_submission_payload_hashes",
        "stage1_submission_receipt_hashes",
        "stage1_canonical_judgement_hashes",
        "stage1_snapshot_manifest_sha256",
        "stage1_snapshot_receipt_file_hashes",
    ):
        assert commitment[name], name


# --------------------------------------------------------------------------
# one-way state transitions
# --------------------------------------------------------------------------


def test_stage1_cannot_be_committed_twice(tmp_path: Path) -> None:
    driver = FixtureWorkflow.create(tmp_path).advance_to("commit_stage1")
    with pytest.raises(WorkflowError, match="already been committed"):
        driver.commit_stage1()


def test_stage1_cannot_be_resubmitted_after_commitment(tmp_path: Path) -> None:
    driver = FixtureWorkflow.create(tmp_path).advance_to("commit_stage1")
    with pytest.raises(WorkflowError, match="already committed"):
        driver.submit_stage1()


def test_a_sealed_receipt_is_never_rewritten_in_place(tmp_path: Path) -> None:
    driver = FixtureWorkflow.create(tmp_path).advance_to("commit_stage1")
    with pytest.raises(WorkflowError, match="write-once"):
        driver.workspace.write("stage1_commitment", {"receipt_kind": "stage1_commitment"})


def test_a_queue_cannot_be_regenerated_after_adjudication(tmp_path: Path) -> None:
    driver = FixtureWorkflow.create(tmp_path).advance_to("adjudicate")
    with pytest.raises(WorkflowError, match="cannot be regenerated"):
        driver.workspace.build_stage1_disagreements(mappings=driver.mappings)


def test_an_adjudication_cannot_be_replaced_after_final_records(tmp_path: Path) -> None:
    driver = FixtureWorkflow.create(tmp_path).advance_to("settle")
    with pytest.raises(WorkflowError, match="already sealed"):
        driver.adjudicate()


def test_c10_cannot_be_rewritten_after_the_slice_is_locked(tmp_path: Path) -> None:
    driver = FixtureWorkflow.create(tmp_path).advance_to("settle")
    report = driver.c10()
    driver.lock(report)
    with pytest.raises(WorkflowError, match="after the reviewed slice was locked"):
        driver.workspace.write("c10_report", report)


# --------------------------------------------------------------------------
# canonicalisation contracts
# --------------------------------------------------------------------------


def test_a_stored_digest_field_is_never_trusted(tmp_path: Path) -> None:
    """``receipt_content_sha256`` recomputes rather than reading the field."""

    driver = FixtureWorkflow.create(tmp_path).advance_to("commit_stage1")
    receipt = read_raw(snapshot_receipt_path(driver, REVIEWER_A, STAGE1))
    forged = json.loads(json.dumps(receipt))
    forged["receipt_sha256"] = "0" * 64
    assert receipt_content_sha256(forged) == receipt_content_sha256(receipt)
    forged["row_count"] = 99
    assert receipt_content_sha256(forged) != receipt_content_sha256(receipt)


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
def test_non_json_values_cannot_be_committed(bad: float) -> None:
    with pytest.raises(CommitmentIntegrityError):
        reject_non_json({"value": bad})


def test_a_noncanonical_role_alias_is_refused(tmp_path: Path) -> None:
    driver = FixtureWorkflow.create(tmp_path).advance_to("commit_stage1")
    receipt = read_raw(snapshot_receipt_path(driver, REVIEWER_A, STAGE1))
    receipt["reviewer_role"] = "reviewer-a"
    with pytest.raises(CommitmentIntegrityError, match="canonical role"):
        canonical_stage1_judgements_digest(receipt)


def test_an_unknown_receipt_kind_is_refused(tmp_path: Path) -> None:
    driver = FixtureWorkflow.create(tmp_path).advance_to("submit_stage2")
    stage1 = read_raw(snapshot_receipt_path(driver, REVIEWER_A, STAGE1))
    with pytest.raises(CommitmentIntegrityError, match="expected a 'stage2_submission' receipt"):
        canonical_stage2_judgements_digest(stage1)


def test_a_missing_expected_field_is_refused(tmp_path: Path) -> None:
    driver = FixtureWorkflow.create(tmp_path).advance_to("commit_stage1")
    receipt = read_raw(snapshot_receipt_path(driver, REVIEWER_A, STAGE1))
    receipt.pop("validation")
    with pytest.raises(CommitmentIntegrityError, match="missing"):
        canonical_stage1_judgements_digest(receipt)


def test_the_declaration_and_qualification_digests_cover_their_content(
    tmp_path: Path,
) -> None:
    driver = FixtureWorkflow.create(tmp_path).advance_to("commit_stage1")
    for name, digest in (
        (f"declaration_{REVIEWER_A}", canonical_declaration_digest),
        (f"qualification_{REVIEWER_A}", canonical_qualification_digest),
    ):
        receipt = driver.workspace.read(name)
        baseline = digest(receipt)
        changed = json.loads(json.dumps(receipt))
        changed["reviewer_role"] = REVIEWER_B
        assert digest(changed) != baseline


# --------------------------------------------------------------------------
# filesystem hardening
# --------------------------------------------------------------------------


def test_an_immutable_artifact_is_never_silently_replaced(tmp_path: Path) -> None:
    target = tmp_path / "artifact.json"
    write_private_json(target, {"a": 1})
    with pytest.raises(CommitmentIntegrityError, match="write-once"):
        write_private_json(target, {"a": 2})
    write_private_json(target, {"a": 3}, allow_replace=True)
    assert json.loads(target.read_text()) == {"a": 3}


def test_an_atomic_write_leaves_no_temporary_file(tmp_path: Path) -> None:
    write_private_json(tmp_path / "artifact.json", {"a": 1})
    assert sorted(path.name for path in tmp_path.iterdir()) == ["artifact.json"]


def test_a_symlinked_receipt_is_refused(tmp_path: Path) -> None:
    driver = FixtureWorkflow.create(tmp_path).advance_to("commit_stage1")
    target = receipt_path(driver, "stage1_commitment")
    elsewhere = tmp_path / "elsewhere.json"
    elsewhere.write_bytes(target.read_bytes())
    target.unlink()
    target.symlink_to(elsewhere)
    with pytest.raises(WorkflowError, match="symbolic link"):
        driver.workspace.read("stage1_commitment")


def test_the_committed_snapshot_is_private_on_disk(tmp_path: Path) -> None:
    import stat as stat_module

    driver = FixtureWorkflow.create(tmp_path).advance_to("commit_stage1")
    directory = driver.workspace.snapshot_path(STAGE1)
    assert stat_module.S_IMODE(directory.stat().st_mode) == 0o700
    for path in directory.iterdir():
        assert stat_module.S_IMODE(path.stat().st_mode) == 0o600


def test_the_stage2_snapshot_appears_only_once_both_submissions_land(
    tmp_path: Path,
) -> None:
    driver = FixtureWorkflow.create(tmp_path).advance_to("open_stage2")
    assert not driver.workspace.has_committed_snapshot(STAGE2)
    driver.submit_stage2()
    assert driver.workspace.has_committed_snapshot(STAGE2)
    assert driver.workspace.snapshot_path(STAGE2).is_dir()


def test_the_fixture_slice_size_is_what_the_matrix_assumes(tmp_path: Path) -> None:
    driver = FixtureWorkflow.create(tmp_path).advance_to("commit_stage1")
    verified = verify_committed_stage1_snapshot(driver.workspace)
    assert verified["commitment"]["expected_item_count"] == FIXTURE_PAIR_COUNT
