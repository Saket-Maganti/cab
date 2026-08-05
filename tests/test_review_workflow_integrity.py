"""Hostile regression tests for the reviewer-workflow integrity repair.

Every test in the first half reproduces one step of the independent audit that
produced a false production ``C10_PASS`` at commit ``b4977c4``.  Each one must
fail closed.  The final test reproduces the complete original exploit chain end
to end and asserts that it can no longer reach a pass.

Nothing here creates genuine evidence: the fixture authority is public by
construction, and the production authority needs an external key that these
tests generate inside a temporary directory and throw away.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from causal_agent_bench.review_ready_v2 import PACKET_VERSION
from causal_agent_bench.review_ready_v2.adjudication import (
    STAGE2,
    AdjudicationError,
    build_stage2_queue,
    validate_adjudication,
)
from causal_agent_bench.review_ready_v2.assignments import (
    AssignmentError,
    create_assignment,
    load_assignments,
    verify_assignment,
    verify_registry_complete,
)
from causal_agent_bench.review_ready_v2.common import FIXTURE_MARKER, sha256_bytes
from causal_agent_bench.review_ready_v2.declarations import (
    REQUIRED_CONFIRMATIONS,
    DeclarationError,
    declaration_template,
    parse_declaration,
)
from causal_agent_bench.review_ready_v2.final_records import build_final_records
from causal_agent_bench.review_ready_v2.fixture_e2e import (
    FIXTURE_C10_CONTRACT,
    FIXTURE_PAIR_COUNT,
    FIXTURE_PSEUDONYMS,
    fixture_applicability,
    fixture_pair_ids,
    fixture_qualification_source,
    run_fixture_e2e,
)
from causal_agent_bench.review_ready_v2.freeze import (
    GENERATOR_SOURCES,
    commit_is_ancestor,
    generator_provenance,
    last_commit_touching,
)
from causal_agent_bench.review_ready_v2.keys import create_external_key
from causal_agent_bench.review_ready_v2.qualification import (
    QUALIFICATION_SCHEMA_VERSION,
    RETIRED_QUALIFICATION_VERSIONS,
    QualificationError,
    build_qualification_package,
    enforce_active_qualification,
    score_qualification,
)
from causal_agent_bench.review_ready_v2.receipts import (
    COORDINATOR_KEY_ENV,
    FIXTURE_ORIGIN,
    PRODUCTION_ORIGIN,
    ReceiptError,
    fixture_authority,
    seal_receipt,
    verify_receipt,
)
from causal_agent_bench.review_ready_v2.roles import (
    ADJUDICATOR,
    REVIEWER_A,
    REVIEWER_B,
    RoleError,
    normalize_role,
)
from causal_agent_bench.review_ready_v2.stage1 import REVIEW_DIMENSIONS
from causal_agent_bench.review_ready_v2.stage2 import (
    NO,
    NOT_APPLICABLE,
    STAGE2_CONDITIONAL_DIMENSIONS,
    STAGE2_FORM_COLUMNS,
    STAGE2_SUBSTANTIVE_DIMENSIONS,
    UNSURE,
    YES,
    validate_stage2_submission,
)
from causal_agent_bench.review_ready_v2.workflow import (
    ReviewWorkspace,
    WorkflowError,
    run_c10,
)

REPO_ROOT = Path(__file__).resolve().parents[1]

PAIR_IDS = fixture_pair_ids()
APPLICABILITY = fixture_applicability()
ITEM_IDS = {
    REVIEWER_A: [f"RA-{index:02d}" for index in range(1, FIXTURE_PAIR_COUNT + 1)],
    REVIEWER_B: [f"RB-{index:02d}" for index in range(1, FIXTURE_PAIR_COUNT + 1)],
}
MAPPINGS = {
    REVIEWER_A: {item: PAIR_IDS[index] for index, item in enumerate(ITEM_IDS[REVIEWER_A])},
    REVIEWER_B: {
        item: PAIR_IDS[FIXTURE_PAIR_COUNT - 1 - index]
        for index, item in enumerate(ITEM_IDS[REVIEWER_B])
    },
}


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------


def _stage2_row(pair_id: str, *, value: str = YES, notes: str = "") -> list[str]:
    cells: list[str] = []
    for dimension in STAGE2_SUBSTANTIVE_DIMENSIONS:
        applicable = APPLICABILITY[pair_id].get(dimension, True)
        if dimension in STAGE2_CONDITIONAL_DIMENSIONS and not applicable:
            cells.append(NOT_APPLICABLE)
        else:
            cells.append(value)
    return cells


def stage2_csv(role: str, *, value: str = YES, notes: str = "") -> bytes:
    lines = [",".join(STAGE2_FORM_COLUMNS)]
    for item_id in sorted(MAPPINGS[role]):
        pair_id = MAPPINGS[role][item_id]
        lines.append(",".join([item_id, *_stage2_row(pair_id, value=value), "NO", "4", notes]))
    return ("\n".join(lines) + "\n").encode()


def stage2_rows(role: str, *, value: str = YES, notes: str = "") -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    for item_id in sorted(MAPPINGS[role]):
        pair_id = MAPPINGS[role][item_id]
        cells = _stage2_row(pair_id, value=value)
        row = dict(zip(STAGE2_SUBSTANTIVE_DIMENSIONS, cells, strict=True))
        row.update({"reviewer_item_id": item_id, "exclude_item": "NO", "reviewer_confidence": "4", "notes": notes})
        rows[item_id] = row
    return rows


def stage2_paired(*, value: str = YES, notes: str = "") -> dict[str, dict[str, dict[str, str]]]:
    paired: dict[str, dict[str, dict[str, str]]] = {}
    for role in (REVIEWER_A, REVIEWER_B):
        for item_id, row in stage2_rows(role, value=value, notes=notes).items():
            paired.setdefault(MAPPINGS[role][item_id], {})[role] = row
    return paired


QUALIFICATION_SOURCE = fixture_qualification_source()


def qualification_package(role: str) -> dict[str, Any]:
    """A package built from synthetic material; the real source stays private."""

    return build_qualification_package(QUALIFICATION_SOURCE, role)


def complete_qualification_row(**overrides: str) -> dict[str, str]:
    row = {name: (values[0] if values else "") for name, values, _ in REVIEW_DIMENSIONS}
    row.update(overrides)
    return row


def qualification_submission(key: dict[str, Any], *, correct: bool = True) -> dict[str, Any]:
    submission: dict[str, Any] = {}
    for item, entry in key.items():
        expected = str(entry["expected_value"])
        value = expected if correct else ("no" if expected == "yes" else "yes")
        submission[item] = complete_qualification_row(
            **{str(entry["decisive_dimension"]): value}
        )
    return submission


def good_declaration(role: str, *, stage1: str, qualification: str, **overrides: Any) -> dict[str, Any]:
    payload = {
        **declaration_template(),
        "reviewer_pseudonym": FIXTURE_PSEUDONYMS[role],
        "package_role": role,
        "qualification_package_hash": qualification,
        "stage1_package_hash": stage1,
        **dict.fromkeys(REQUIRED_CONFIRMATIONS, True),
        "conflict_of_interest_disclosed": False,
        "conflict_of_interest_details": "",
        "signed_name_or_approved_signature_field": FIXTURE_PSEUDONYMS[role],
        "signed_at": "2026-01-01T00:00:00+00:00",
    }
    payload.update(overrides)
    return payload


@pytest.fixture
def production_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> ReviewWorkspace:
    """A production workspace with a throwaway coordinator key outside the repo."""

    key_path = tmp_path / "keys" / "coordinator.key"
    monkeypatch.setenv(COORDINATOR_KEY_ENV, str(key_path))
    create_external_key(COORDINATOR_KEY_ENV, tmp_path / "repo")
    return ReviewWorkspace.production(tmp_path / "packet", tmp_path / "repo")


# --------------------------------------------------------------------------
# Exploit 1 — the public qualification key
# --------------------------------------------------------------------------


def test_tracked_source_carries_no_qualification_answers() -> None:
    """The audit recovered every expected answer from tracked source. It cannot now."""

    source = (REPO_ROOT / "src/causal_agent_bench/review_ready_v2/qualification.py").read_text()
    from causal_agent_bench.review_ready_v2 import qualification

    assert not hasattr(qualification, "QUALIFICATION_KEY")
    assert not hasattr(qualification, "QUALIFICATION_ITEMS")
    # V3 kept the scenario table, the defect constructions and the mapping from a
    # construction to its dimension and value.  None of them survives.
    for removed in ("_SCENARIOS", "_DEFECT_KINDS", "_apply_defect", "build_private_qualification"):
        assert not hasattr(qualification, removed), removed
        assert removed not in source, removed
    assert "QUALIFICATION_KEY: dict" not in source
    assert '"expected_value": "yes"' not in source
    assert '"expected_value": "no"' not in source


def test_public_qualification_version_is_retired_and_rejected() -> None:
    assert "cab_stage1_qualification_v2" in RETIRED_QUALIFICATION_VERSIONS
    with pytest.raises(QualificationError, match="retired"):
        enforce_active_qualification("cab_stage1_qualification_v2")
    enforce_active_qualification(QUALIFICATION_SCHEMA_VERSION)


def test_retired_qualification_is_rejected_even_when_renamed() -> None:
    """Copying the exposed items under the active name still fails."""

    with pytest.raises(QualificationError):
        enforce_active_qualification("cab_stage1_qualification_v2_renamed")


def test_qualification_content_requires_the_private_source() -> None:
    """Different authored material produces different items and different answers."""

    other = json.loads(json.dumps(QUALIFICATION_SOURCE))
    for index, entry in enumerate(other["roles"][REVIEWER_A]):
        entry["reviewer_item_id"] = f"ALT-{index:03d}"
        entry["item"]["task_objective"] = f"A different authored objective {index}."
    first = qualification_package(REVIEWER_A)
    second = build_qualification_package(other, REVIEWER_A)
    assert first["package_sha256"] != second["package_sha256"]
    assert set(first["answer_key"]) != set(second["answer_key"])


def test_each_reviewer_gets_a_different_qualification_package() -> None:
    first = qualification_package(REVIEWER_A)
    second = qualification_package(REVIEWER_B)
    assert first["package_sha256"] != second["package_sha256"]
    assert set(first["answer_key"]) != set(second["answer_key"])


def test_qualification_package_ships_no_expected_values() -> None:
    import zipfile
    from io import BytesIO

    package = qualification_package(REVIEWER_A)
    archive = zipfile.ZipFile(BytesIO(package["package_bytes"]))
    for name in archive.namelist():
        blob = archive.read(name)
        assert b"expected_value" not in blob, name
        assert b"decisive_dimension" not in blob, name
        assert b"defect_kind" not in blob, name
        assert b"explanation" not in blob, name


# --------------------------------------------------------------------------
# Exploit 2 / 9 — synthetic submissions and the fixture=False bypass
# --------------------------------------------------------------------------


def test_production_authority_is_unavailable_without_the_external_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv(COORDINATOR_KEY_ENV, raising=False)
    with pytest.raises(ReceiptError):
        ReviewWorkspace.production(tmp_path / "packet", tmp_path / "repo")


def test_no_boolean_converts_a_fixture_receipt_into_production_evidence(
    production_workspace: ReviewWorkspace,
) -> None:
    """Exploit 9: prove the authenticity boundary is not a flag."""

    fixture_receipt = seal_receipt(fixture_authority(), {"receipt_kind": "stage1_submission"})
    assert fixture_receipt["artifact_origin"] == FIXTURE_ORIGIN
    assert fixture_receipt["counts_as_genuine_evidence"] is False

    # 1. As-is: refused on origin.
    with pytest.raises(ReceiptError):
        verify_receipt(production_workspace.authority, fixture_receipt)

    # 2. Rewrite every field a caller could reach for. The MAC no longer matches.
    forged = {
        **fixture_receipt,
        "artifact_origin": PRODUCTION_ORIGIN,
        "counts_as_genuine_evidence": True,
        "receipt_schema_version": production_workspace.authority.schema_version,
    }
    with pytest.raises(ReceiptError, match="authentication failed"):
        verify_receipt(production_workspace.authority, forged)

    # 3. Re-hash the content too. Still refused: the MAC needs the external key.
    from causal_agent_bench.review_ready_v2.common import sha256_json

    forged["receipt_sha256"] = sha256_json(
        {k: v for k, v in forged.items() if k not in ("receipt_mac", "receipt_sha256")}
    )
    with pytest.raises(ReceiptError, match="authentication failed"):
        verify_receipt(production_workspace.authority, forged)


def test_production_workspace_refuses_a_copied_fixture_receipt(
    production_workspace: ReviewWorkspace,
) -> None:
    """Exploit 10: a stale or copied receipt is refused, not silently trusted."""

    fixture = ReviewWorkspace.fixture(production_workspace.private_root)
    fixture.write("stage1_commitment", {"receipt_kind": "stage1_commitment", "stage1_final": True})
    source = fixture.receipts / "stage1_commitment.json"
    (production_workspace.receipts / "stage1_commitment.json").write_bytes(source.read_bytes())
    with pytest.raises(WorkflowError, match="synthetic test fixture"):
        production_workspace.read("stage1_commitment")


def test_tampering_with_a_production_receipt_is_detected(
    production_workspace: ReviewWorkspace,
) -> None:
    production_workspace.write("agreement", {"receipt_kind": "agreement", "overall": 0.5})
    path = production_workspace.receipts / "agreement.json"
    receipt = json.loads(path.read_text())
    receipt["overall"] = 0.99
    path.write_text(json.dumps(receipt))
    with pytest.raises(WorkflowError, match="failed verification"):
        production_workspace.read("agreement")


def test_fixture_evidence_never_satisfies_the_production_bindings(tmp_path: Path) -> None:
    fixture = ReviewWorkspace.fixture(tmp_path / "packet")
    eligibility = fixture.evidence_eligibility()
    assert eligibility["counts_as_genuine_evidence"] is False
    assert "coordinator_acceptance_receipt" in eligibility["missing_bindings"]


# --------------------------------------------------------------------------
# Exploit 3 / 4 — Stage-2 all UNSURE and all NO
# --------------------------------------------------------------------------


def test_stage2_all_unsure_is_complete_but_never_accepted() -> None:
    """Exploit 3: a complete form full of UNSURE is not an approval."""

    rows = stage2_rows(REVIEWER_A, value=UNSURE, notes="unresolved")
    applicability = {item: APPLICABILITY[MAPPINGS[REVIEWER_A][item]] for item in rows}
    result = validate_stage2_submission(rows, list(rows), applicability)
    assert result["form_complete"] is True
    assert result["substantively_accepted_without_adjudication"] is False
    assert result["blocking_value_count"] > 0


def test_stage2_all_unsure_without_notes_is_malformed() -> None:
    rows = stage2_rows(REVIEWER_A, value=UNSURE, notes="")
    applicability = {item: APPLICABILITY[MAPPINGS[REVIEWER_A][item]] for item in rows}
    result = validate_stage2_submission(rows, list(rows), applicability)
    assert result["form_complete"] is False
    assert any(problem["column"] == "notes" for problem in result["malformed"])


@pytest.mark.parametrize("value", [UNSURE, NO])
def test_unresolved_stage2_values_block_the_final_record(value: str) -> None:
    """Exploits 3 and 4: unresolved NO/UNSURE cannot reach an included pair."""

    final = build_final_records(
        stage1_paired=_accepting_stage1_paired(),
        stage2_paired=stage2_paired(value=value, notes="objection"),
        stage1_adjudication=None,
        stage2_adjudication=None,
        applicability=APPLICABILITY,
        expected_pair_count=FIXTURE_PAIR_COUNT,
    )
    assert final["passed"] is False
    assert final["included_count"] == 0
    assert final["unresolved"]


def test_every_unresolved_stage2_value_reaches_the_disagreement_queue() -> None:
    queue = build_stage2_queue(stage2_paired(value=UNSURE, notes="unresolved"), APPLICABILITY)
    assert queue["disputed_pair_count"] == FIXTURE_PAIR_COUNT
    reasons = {reason for row in queue["disputes"] for reason in row["reasons"]}
    assert "unresolved_uncertainty" in reasons


# --------------------------------------------------------------------------
# Exploit 5 — Stage-2 reviewer disagreement
# --------------------------------------------------------------------------


def test_stage2_disagreement_produces_a_queue_and_requires_adjudication() -> None:
    paired = stage2_paired()
    disputed_pair = PAIR_IDS[0]
    paired[disputed_pair][REVIEWER_A]["gold_correct"] = NO
    paired[disputed_pair][REVIEWER_A]["notes"] = "the expected result does not follow"
    queue = build_stage2_queue(paired, APPLICABILITY)
    assert queue["disputed_dimension_count"] >= 1
    dispute = next(row for row in queue["disputes"] if row["dimension"] == "gold_correct")
    assert {"reviewer_disagreement", "substantive_objection"} <= set(dispute["reasons"])

    with pytest.raises(AdjudicationError, match="undecided"):
        validate_adjudication(stage=STAGE2, queue=queue, decisions=[])


def test_adjudicator_cannot_leave_an_objection_unresolved() -> None:
    paired = stage2_paired()
    paired[PAIR_IDS[0]][REVIEWER_A]["gold_correct"] = NO
    paired[PAIR_IDS[0]][REVIEWER_A]["notes"] = "objection"
    queue = build_stage2_queue(paired, APPLICABILITY)
    decisions = [
        {
            "pair_id": row["pair_id"],
            "dimension": row["dimension"],
            "final_value": UNSURE,
            "rationale": "still unsure",
            "evidence_reference": "ref",
            "confidence": "3",
            "exclude_item": "NO",
        }
        for row in queue["disputes"]
    ]
    with pytest.raises(AdjudicationError, match="neither resolves"):
        validate_adjudication(stage=STAGE2, queue=queue, decisions=decisions)


def test_adjudication_requires_rationale_evidence_and_confidence() -> None:
    paired = stage2_paired()
    paired[PAIR_IDS[0]][REVIEWER_A]["gold_correct"] = NO
    paired[PAIR_IDS[0]][REVIEWER_A]["notes"] = "objection"
    queue = build_stage2_queue(paired, APPLICABILITY)
    base = {
        "pair_id": queue["disputes"][0]["pair_id"],
        "dimension": queue["disputes"][0]["dimension"],
        "final_value": YES,
        "rationale": "resolved",
        "evidence_reference": "ref",
        "confidence": "4",
        "exclude_item": "NO",
    }
    for field in ("rationale", "evidence_reference"):
        with pytest.raises(AdjudicationError):
            validate_adjudication(
                stage=STAGE2, queue=queue, decisions=[{**base, field: "   "}]
            )
    with pytest.raises(AdjudicationError, match="confidence"):
        validate_adjudication(stage=STAGE2, queue=queue, decisions=[{**base, "confidence": "9"}])


# --------------------------------------------------------------------------
# Exploit 6 — adjudication ignored
# --------------------------------------------------------------------------


def test_agreement_uses_raw_judgements_while_eligibility_uses_adjudicated_values() -> None:
    """Exploit 6: resolving a dispute must not improve reported agreement."""

    result = run_fixture_e2e()
    assert result["passed"], result["steps"]
    agreement_step = next(
        step for step in result["steps"] if step["step"] == "agreement_computed_from_raw"
    )
    assert agreement_step["passed"]
    # Stage-1 raw agreement is strictly below 1.0 because the fixture plants a
    # genuine disagreement, and it stays there after the adjudicator resolves it.
    assert "stage1=0.9" in agreement_step["detail"] or "stage1=0.8" in agreement_step["detail"]
    final_step = next(step for step in result["steps"] if step["step"] == "final_adjudicated_records")
    assert "8 included" in final_step["detail"]


def test_final_records_record_provenance_for_every_dimension() -> None:
    paired = stage2_paired()
    paired[PAIR_IDS[0]][REVIEWER_A]["gold_correct"] = NO
    paired[PAIR_IDS[0]][REVIEWER_A]["notes"] = "objection"
    queue = build_stage2_queue(paired, APPLICABILITY)
    adjudication = validate_adjudication(
        stage=STAGE2,
        queue=queue,
        decisions=[
            {
                "pair_id": row["pair_id"],
                "dimension": row["dimension"],
                "final_value": "NO" if row["dimension"] == "exclude_item" else YES,
                "rationale": "resolved on the evidence",
                "evidence_reference": "stage2-record",
                "confidence": "4",
                "exclude_item": "NO",
            }
            for row in queue["disputes"]
        ],
    )
    final = build_final_records(
        stage1_paired=_accepting_stage1_paired(),
        stage2_paired=paired,
        stage1_adjudication=None,
        stage2_adjudication=adjudication,
        applicability=APPLICABILITY,
        expected_pair_count=FIXTURE_PAIR_COUNT,
    )
    assert final["passed"]
    assert final["provenance_counts"]["resolved_by_adjudicator"] >= 1
    assert final["provenance_counts"]["agreed_by_reviewers"] >= 1
    resolved = final["records"][0]["stage2"]["gold_correct"]
    assert resolved["provenance"] == "resolved_by_adjudicator"
    assert resolved["reviewer_values"][REVIEWER_A] == NO


# --------------------------------------------------------------------------
# Exploit 7 — hardcoded declarations
# --------------------------------------------------------------------------


def test_declaration_fields_are_never_supplied_by_ingestion() -> None:
    """Exploit 7: the audited code wrote these two values itself."""

    from causal_agent_bench.review_ready_v2 import workflow

    source = Path(workflow.__file__).read_text()
    assert "ai_assistance_declared" not in source
    assert "conflict_of_interest_declared" not in source


@pytest.mark.parametrize("field", REQUIRED_CONFIRMATIONS)
def test_a_missing_confirmation_is_a_refusal_not_a_false(field: str) -> None:
    payload = good_declaration(REVIEWER_A, stage1="a" * 64, qualification="b" * 64)
    payload.pop(field)
    with pytest.raises(DeclarationError, match="missing required fields"):
        parse_declaration(payload)


@pytest.mark.parametrize("field", REQUIRED_CONFIRMATIONS)
def test_an_unaffirmed_confirmation_blocks_the_review(field: str) -> None:
    payload = good_declaration(REVIEWER_A, stage1="a" * 64, qualification="b" * 64, **{field: False})
    with pytest.raises(DeclarationError, match="did not affirm"):
        parse_declaration(payload)


def test_a_non_boolean_confirmation_is_refused() -> None:
    payload = good_declaration(
        REVIEWER_A, stage1="a" * 64, qualification="b" * 64, no_ai_assistance_confirmed="yes"
    )
    with pytest.raises(DeclarationError, match="literal true or false"):
        parse_declaration(payload)


def test_a_disclosed_conflict_cannot_silently_pass() -> None:
    payload = good_declaration(
        REVIEWER_A,
        stage1="a" * 64,
        qualification="b" * 64,
        conflict_of_interest_disclosed=True,
        conflict_of_interest_details="co-authored an unrelated paper with an author",
    )
    declaration = parse_declaration(payload)
    assert declaration["requires_coordinator_review"] is True
    from causal_agent_bench.review_ready_v2.declarations import declaration_blocks_qualification

    assert "disclosed_conflict_awaiting_coordinator_decision" in declaration_blocks_qualification(
        declaration
    )
    declaration["coordinator_review_decision"] = "REJECTED"
    assert "coordinator_rejected_declaration" in declaration_blocks_qualification(declaration)


def test_the_declaration_receipt_never_carries_the_disclosure_text() -> None:
    payload = good_declaration(
        REVIEWER_A,
        stage1="a" * 64,
        qualification="b" * 64,
        conflict_of_interest_disclosed=True,
        conflict_of_interest_details="a very specific private disclosure",
    )
    declaration = parse_declaration(payload)
    assert "a very specific private disclosure" not in json.dumps(declaration)
    assert declaration["conflict_of_interest_details_sha256"]


def test_a_synthetic_declaration_is_flagged_and_blocks_qualification() -> None:
    payload = good_declaration(
        REVIEWER_A,
        stage1="a" * 64,
        qualification="b" * 64,
        notes=FIXTURE_MARKER,
    )
    declaration = parse_declaration(payload)
    assert declaration["declaration_is_synthetic"] is True
    from causal_agent_bench.review_ready_v2.declarations import declaration_blocks_qualification

    assert "declaration_is_synthetic" in declaration_blocks_qualification(declaration)


def test_qualification_without_a_declaration_is_refused(tmp_path: Path) -> None:
    workspace = ReviewWorkspace.fixture(tmp_path / "packet")
    with pytest.raises(WorkflowError, match="required receipt is missing"):
        workspace.ingest_qualification(REVIEWER_A, {}, {})


# --------------------------------------------------------------------------
# Exploit 8 — reviewer / package swap
# --------------------------------------------------------------------------


@pytest.fixture
def registry(tmp_path: Path) -> dict[str, Any]:
    root = tmp_path / "packet"
    create_assignment(
        root,
        packet_version=PACKET_VERSION,
        reviewer_pseudonym="alpha",
        role=REVIEWER_A,
        stage1_package_hash="a" * 64,
        qualification_package_hash="1" * 64,
    )
    create_assignment(
        root,
        packet_version=PACKET_VERSION,
        reviewer_pseudonym="beta",
        role=REVIEWER_B,
        stage1_package_hash="b" * 64,
        qualification_package_hash="2" * 64,
    )
    create_assignment(
        root, packet_version=PACKET_VERSION, reviewer_pseudonym="gamma", role=ADJUDICATOR
    )
    return load_assignments(root, packet_version=PACKET_VERSION)


def test_registry_is_complete_and_roles_are_distinct(registry: dict[str, Any]) -> None:
    assert verify_registry_complete(registry)["passed"]


def test_swapped_package_is_rejected(registry: dict[str, Any]) -> None:
    with pytest.raises(AssignmentError, match="does not match the package bound"):
        verify_assignment(
            registry,
            role=REVIEWER_A,
            reviewer_pseudonym="alpha",
            stage1_package_hash="b" * 64,
        )


def test_wrong_reviewer_id_is_rejected(registry: dict[str, Any]) -> None:
    with pytest.raises(AssignmentError, match="is not the reviewer assigned"):
        verify_assignment(registry, role=REVIEWER_A, reviewer_pseudonym="beta")


def test_reviewer_a_using_reviewer_b_namespace_is_rejected(registry: dict[str, Any]) -> None:
    with pytest.raises(AssignmentError, match="item namespace"):
        verify_assignment(
            registry,
            role=REVIEWER_A,
            reviewer_pseudonym="alpha",
            item_ids=["RB-01", "RB-02"],
        )


def test_duplicate_reviewer_is_rejected(tmp_path: Path) -> None:
    root = tmp_path / "packet"
    create_assignment(
        root,
        packet_version=PACKET_VERSION,
        reviewer_pseudonym="alpha",
        role=REVIEWER_A,
        stage1_package_hash="a" * 64,
        qualification_package_hash="1" * 64,
    )
    with pytest.raises(AssignmentError, match="already holds"):
        create_assignment(
            root,
            packet_version=PACKET_VERSION,
            reviewer_pseudonym="alpha",
            role=REVIEWER_B,
            stage1_package_hash="b" * 64,
            qualification_package_hash="2" * 64,
        )


def test_reviewer_cannot_also_adjudicate(tmp_path: Path) -> None:
    root = tmp_path / "packet"
    create_assignment(
        root,
        packet_version=PACKET_VERSION,
        reviewer_pseudonym="alpha",
        role=REVIEWER_A,
        stage1_package_hash="a" * 64,
        qualification_package_hash="1" * 64,
    )
    with pytest.raises(AssignmentError, match="cannot hold"):
        create_assignment(
            root, packet_version=PACKET_VERSION, reviewer_pseudonym="alpha", role=ADJUDICATOR
        )


def test_assignments_are_immutable(tmp_path: Path) -> None:
    root = tmp_path / "packet"
    create_assignment(
        root,
        packet_version=PACKET_VERSION,
        reviewer_pseudonym="alpha",
        role=REVIEWER_A,
        stage1_package_hash="a" * 64,
        qualification_package_hash="1" * 64,
    )
    with pytest.raises(AssignmentError, match="immutable"):
        create_assignment(
            root,
            packet_version=PACKET_VERSION,
            reviewer_pseudonym="delta",
            role=REVIEWER_A,
            stage1_package_hash="c" * 64,
            qualification_package_hash="3" * 64,
        )


def test_two_reviewers_cannot_share_one_package(tmp_path: Path) -> None:
    root = tmp_path / "packet"
    create_assignment(
        root,
        packet_version=PACKET_VERSION,
        reviewer_pseudonym="alpha",
        role=REVIEWER_A,
        stage1_package_hash="a" * 64,
        qualification_package_hash="1" * 64,
    )
    with pytest.raises(AssignmentError, match="independently ordered"):
        create_assignment(
            root,
            packet_version=PACKET_VERSION,
            reviewer_pseudonym="beta",
            role=REVIEWER_B,
            stage1_package_hash="a" * 64,
            qualification_package_hash="2" * 64,
        )


def test_hand_edited_registry_is_detected(tmp_path: Path, registry: dict[str, Any]) -> None:
    from causal_agent_bench.review_ready_v2.assignments import registry_path

    path = registry_path(tmp_path / "packet")
    payload = json.loads(path.read_text())
    payload["assignments"][REVIEWER_A]["stage1_package_hash"] = "f" * 64
    path.write_text(json.dumps(payload))
    with pytest.raises(AssignmentError, match="integrity digest"):
        load_assignments(tmp_path / "packet", packet_version=PACKET_VERSION)


# --------------------------------------------------------------------------
# canonical role enum
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("spelling", "expected"),
    [
        ("reviewer-a", REVIEWER_A),
        ("stage1_reviewer_a", REVIEWER_A),
        ("Reviewer A", REVIEWER_A),
        ("REVIEWER_A", REVIEWER_A),
        ("stage2_reviewer_b", REVIEWER_B),
        ("adjudicator", ADJUDICATOR),
    ],
)
def test_every_accepted_spelling_normalizes_to_one_enum(spelling: str, expected: str) -> None:
    assert normalize_role(spelling) == expected


def test_an_unknown_role_is_a_hard_error() -> None:
    with pytest.raises(RoleError):
        normalize_role("reviewer-c")


# --------------------------------------------------------------------------
# freeze portability
# --------------------------------------------------------------------------


def test_recorded_generator_commit_is_an_ancestor_of_head() -> None:
    provenance = generator_provenance(REPO_ROOT)
    assert provenance["commit_is_ancestor_of_head"] is True
    assert provenance["commit_content_matches"] is True
    assert provenance["requires_unreachable_objects"] is False


def test_generator_provenance_resolves_in_a_single_branch_clone(tmp_path: Path) -> None:
    """A branch-only clone has no reflog and no unreachable objects."""

    clone = tmp_path / "clone"
    subprocess.run(
        ["git", "clone", "--single-branch", "--branch", "main", "--no-local", str(REPO_ROOT), str(clone)],
        check=True,
        capture_output=True,
    )
    subprocess.run(["git", "reflog", "expire", "--expire=now", "--all"], cwd=clone, check=True)
    subprocess.run(["git", "gc", "--prune=now", "--aggressive"], cwd=clone, check=True, capture_output=True)

    commit = last_commit_touching(clone, GENERATOR_SOURCES)
    assert commit, "the generator has no reachable commit in a fresh clone"
    assert commit_is_ancestor(clone, commit)
    for relative in GENERATOR_SOURCES:
        shown = subprocess.run(
            ["git", "show", f"{commit}:{relative}"], cwd=clone, check=False, capture_output=True
        )
        assert shown.returncode == 0, relative


def test_the_orphaned_sibling_commit_style_provenance_is_refused() -> None:
    """The audited freeze named a commit that no clone could resolve."""

    provenance = generator_provenance(REPO_ROOT, generator_commit="0" * 40)
    assert provenance["commit_is_ancestor_of_head"] is False
    assert provenance["commit_content_matches"] is False


# --------------------------------------------------------------------------
# the complete original exploit chain
# --------------------------------------------------------------------------


def _accepting_stage1_paired() -> dict[str, dict[str, dict[str, str]]]:
    from causal_agent_bench.review_ready_v2.fixture_e2e import _STAGE1_ACCEPTING_ROW

    paired: dict[str, dict[str, dict[str, str]]] = {}
    for pair_id in PAIR_IDS:
        paired[pair_id] = {
            REVIEWER_A: dict(_STAGE1_ACCEPTING_ROW),
            REVIEWER_B: dict(_STAGE1_ACCEPTING_ROW),
        }
    return paired


def test_the_audited_false_c10_pass_now_fails_closed(
    production_workspace: ReviewWorkspace,
) -> None:
    """Reproduce the audit's exact chain against production APIs.

    The audit qualified two synthetic reviewers with the public key, submitted
    all-accepting Stage-1 rows against a fabricated package hash, marked every
    Stage-2 cell UNSURE, and obtained ``C10_PASS`` with zero failed checks.
    Every step of that chain now refuses.
    """

    workspace = production_workspace
    blocked_at: list[str] = []

    # Step 1: the public answer key no longer exists.
    from causal_agent_bench.review_ready_v2 import qualification as qualification_module

    if not hasattr(qualification_module, "QUALIFICATION_KEY"):
        blocked_at.append("no_public_qualification_key")

    # Step 2: qualification without a declaration is refused.
    with pytest.raises(WorkflowError):
        workspace.ingest_qualification(REVIEWER_A, {"Q-01": {}}, {"Q-01": {}})
    blocked_at.append("qualification_requires_a_declaration")

    # Step 3: a declaration without an assignment is refused.
    with pytest.raises(WorkflowError):
        workspace.ingest_declaration(
            REVIEWER_A, good_declaration(REVIEWER_A, stage1="a" * 64, qualification="b" * 64)
        )
    blocked_at.append("declaration_requires_an_assignment")

    # Step 4: Stage-1 ingestion without qualification is refused.
    with pytest.raises(WorkflowError, match="not qualified"):
        workspace.ingest_stage1(
            REVIEWER_A, b"", expected_item_ids=[], package_sha256="a" * 64
        )
    blocked_at.append("stage1_requires_qualification")

    # Step 5: C10 cannot even be evaluated without the receipt chain.
    with pytest.raises(WorkflowError, match="required receipt is missing"):
        run_c10(
            workspace,
            contract=FIXTURE_C10_CONTRACT,
            mappings=MAPPINGS,
            applicability=APPLICABILITY,
            prerequisites={},
            packet_commitment=sha256_bytes(b"attacker-chosen"),
            scientific_freeze_sha256="a" * 64,
        )
    blocked_at.append("c10_requires_the_full_receipt_chain")

    assert blocked_at == [
        "no_public_qualification_key",
        "qualification_requires_a_declaration",
        "declaration_requires_an_assignment",
        "stage1_requires_qualification",
        "c10_requires_the_full_receipt_chain",
    ]


def test_c10_refuses_when_prerequisites_are_empty() -> None:
    """The audit passed ``prerequisites={}``; ``all({}.values())`` returned True."""

    probe = run_fixture_e2e(prerequisites={})
    assert probe["c10"]["status"] == "C10_PENDING_GENUINE_REVIEW"
    assert "prerequisites_satisfied" in probe["c10"]["failed_checks"]
    assert probe["c10"]["mechanics_status"] == "C10_MECHANICS_FAIL"


def test_c10_refuses_when_a_prerequisite_is_false() -> None:
    probe = run_fixture_e2e(prerequisites={"scientific_freeze_v2": False})
    assert "prerequisites_satisfied" in probe["c10"]["failed_checks"]


def test_fixture_end_to_end_still_passes_and_never_claims_evidence() -> None:
    result = run_fixture_e2e()
    assert result["passed"], [step for step in result["steps"] if not step["passed"]]
    assert result["counts_as_genuine_evidence"] is False
    assert result["genuine_human_judgments"] == 0
    assert result["genuine_model_trajectories"] == 0


def test_stage2_form_completion_is_not_approval_in_the_frozen_policy() -> None:
    policy = json.loads(
        (REPO_ROOT / "configs/reviewer_ready_v2/stage2_acceptance_policy_v1.json").read_text()
    )
    assert policy["form_completion_is_not_approval"] is True
    assert set(policy["blocking_values"]) == {"NO", "UNSURE"}
    assert set(policy["accepting_values"]) == {"YES", "NOT_APPLICABLE"}
    assert policy["not_applicable_allowed_dimensions"] == list(STAGE2_CONDITIONAL_DIMENSIONS)


def test_not_applicable_is_refused_where_the_dimension_applies() -> None:
    rows = stage2_rows(REVIEWER_A)
    item = sorted(rows)[0]
    rows[item]["gold_correct"] = NOT_APPLICABLE
    applicability = {name: APPLICABILITY[MAPPINGS[REVIEWER_A][name]] for name in rows}
    result = validate_stage2_submission(rows, list(rows), applicability)
    assert result["form_complete"] is False
    assert any(
        problem["issue"] == "not_applicable_forbidden_for_core_dimension"
        for problem in result["malformed"]
    )


def test_qualification_scoring_rejects_incomplete_and_malformed_rows() -> None:
    key = qualification_package(REVIEWER_A)["answer_key"]
    perfect = qualification_submission(key)
    assert score_qualification(perfect, key, reviewer_role=REVIEWER_A)["qualified"]

    incomplete = dict(perfect)
    incomplete.pop(sorted(incomplete)[0])
    with pytest.raises(QualificationError, match="incomplete"):
        score_qualification(incomplete, key, reviewer_role=REVIEWER_A)

    malformed = {item: dict(row) for item, row in perfect.items()}
    first = sorted(malformed)[0]
    malformed[first][str(key[first]["decisive_dimension"])] = "maybe"
    with pytest.raises(QualificationError, match="invalid value"):
        score_qualification(malformed, key, reviewer_role=REVIEWER_A)

    # "Complete every requested field" is now enforced, not merely requested.
    blank = {item: dict(row) for item, row in perfect.items()}
    blank[first]["task_clarity"] = ""
    with pytest.raises(QualificationError, match="blank"):
        score_qualification(blank, key, reviewer_role=REVIEWER_A)

    extra = {**perfect, "Q-NOT-YOURS": complete_qualification_row()}
    with pytest.raises(QualificationError, match="not in this reviewer"):
        score_qualification(extra, key, reviewer_role=REVIEWER_A)


def test_qualification_threshold_is_enforced() -> None:
    key = qualification_package(REVIEWER_B)["answer_key"]
    result = score_qualification(
        qualification_submission(key, correct=False), key, reviewer_role=REVIEWER_B
    )
    assert result["qualified"] is False
    assert result["rate"] == 0.0
    assert result["answer_key_disclosed"] is False
    assert "expected_value" not in json.dumps(result)
