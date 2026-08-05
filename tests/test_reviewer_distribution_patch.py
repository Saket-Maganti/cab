"""Hostile regression tests for the final reviewer-distribution patch.

Three defects are closed here, and every test in this module is an attempt to
reopen one of them:

1. The active qualification was reconstructible.  V3 kept its scenario table and
   its construction-to-answer mapping in tracked source, so a reviewer holding
   the ZIP could classify each item against public code.  V4 keeps only schema,
   transport and scoring; the proof is that two private sources with identical
   item bodies and different answers produce byte-identical packages.
2. Adjudicator packages carried disputes without the evidence to decide them.
3. Stage-2 package hashes were computed and then honoured by nothing.

Nothing here creates genuine evidence, runs a model, or performs human review.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Any

import pytest

from causal_agent_bench.review_ready_v2.adjudication import STAGE1, STAGE2
from causal_agent_bench.review_ready_v2.adjudication_packages import (
    BINDING_FIELDS,
    STAGE2_CONDITIONAL_EVIDENCE,
    STAGE2_ONLY_KEYS,
    STAGE2_REQUIRED_EVIDENCE,
    AdjudicationPackageError,
    build_stage1_adjudicator_package,
    build_stage2_adjudicator_package,
    disputed_pair_ids,
    package_binding,
)
from causal_agent_bench.review_ready_v2.common import sha256_bytes
from causal_agent_bench.review_ready_v2.fixture_e2e import (
    FIXTURE_COMMIT,
    FIXTURE_FREEZE_SHA,
    FIXTURE_PAIR_COUNT,
    FIXTURE_PSEUDONYMS,
    _fixture_stage1_view,
    _fixture_stage2_record,
    fixture_applicability,
    fixture_qualification_source,
    run_fixture_e2e,
)
from causal_agent_bench.review_ready_v2.qualification import (
    QUALIFICATION_DIRNAME,
    QUALIFICATION_SCHEMA_VERSION,
    QUALIFICATION_SOURCE_FILENAME,
    RETIRED_QUALIFICATION_VERSIONS,
    QualificationError,
    build_qualification_package,
    enforce_active_qualification,
    validate_qualification_source,
)
from causal_agent_bench.review_ready_v2.roles import ADJUDICATOR, REVIEWER_A, REVIEWER_B
from causal_agent_bench.review_ready_v2.stage2_issuance import (
    REQUIRED_ISSUANCE_FIELDS,
    Stage2IssuanceError,
    build_stage2_issuance,
    verify_stage2_issuance,
)
from causal_agent_bench.review_ready_v2.workflow import WorkflowError

REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = REPO_ROOT / "reports/reviewer_ready_v2"
PRIVATE_ROOT = REPO_ROOT / "private_data/human_review/compact20-review-ready-v2"

#: The scientific kernel this patch must not touch, pinned from the commitment
#: that existed before the patch was written.
FROZEN_STAGE1_PACKAGE_HASHES = {
    "stage1_reviewer_a.zip": "3fcd2192c68cc356b2a1506a2ca32f191caf00ccf5dc7769a87bcd47db618113",
    "stage1_reviewer_b.zip": "0185fcfbe89402e6284999fa6ed472fb0e1f90d28335a8ccfc6094e158a2d6cf",
}
FROZEN_PAIR_CONTENT_DIGEST = (
    "01a2ed72c58d052cc36e64907b3ac5f2b19de5f314ad63915c4d975c51d6973d"
)

SOURCE = fixture_qualification_source()


def _report(name: str) -> dict[str, Any]:
    path = REPORT_DIR / name
    if not path.is_file():
        pytest.skip(f"{name} has not been generated in this working tree")
    return json.loads(path.read_text())


def _archive(payload: bytes) -> dict[str, bytes]:
    with zipfile.ZipFile(BytesIO(payload)) as handle:
        return {info.filename: handle.read(info) for info in handle.infolist()}


# --------------------------------------------------------------------------
# 1-3 — the private qualification V4
# --------------------------------------------------------------------------


def test_v3_qualification_is_retired_and_rejected() -> None:
    assert QUALIFICATION_SCHEMA_VERSION == "cab_qualification_v4"
    assert "cab_qualification_v3" in RETIRED_QUALIFICATION_VERSIONS
    with pytest.raises(QualificationError, match="retired"):
        enforce_active_qualification("cab_qualification_v3")
    # A retired source renamed to the active version is still refused, because
    # the version travels inside the private material rather than beside it.
    renamed = {**SOURCE, "qualification_version": "cab_qualification_v3"}
    with pytest.raises(QualificationError, match="retired"):
        validate_qualification_source(renamed)


def test_v4_answers_are_independent_of_everything_that_is_shipped() -> None:
    """The proof that the answer is not recoverable from tracked source + ZIP.

    Two private sources whose item bodies are identical and whose answers differ
    produce byte-identical packages.  No function of the tracked repository and
    the reviewer's archive can therefore distinguish them, so no such function
    can recover the answer.
    """

    flipped = json.loads(json.dumps(SOURCE))
    for entry in flipped["roles"][REVIEWER_A]:
        expected = entry["answer"]["expected_value"]
        entry["answer"]["expected_value"] = "no" if expected == "yes" else "yes"

    original = build_qualification_package(SOURCE, REVIEWER_A)
    altered = build_qualification_package(flipped, REVIEWER_A)
    assert original["package_bytes"] == altered["package_bytes"]
    assert original["package_sha256"] == altered["package_sha256"]
    assert original["answer_key"] != altered["answer_key"]


def test_no_tracked_source_carries_item_templates_or_answer_mappings() -> None:
    source = (REPO_ROOT / "src/causal_agent_bench/review_ready_v2/qualification.py").read_text()
    for banned in (
        "_SCENARIOS",
        "_DEFECT_KINDS",
        "_apply_defect",
        "_POSITIVE_KIND",
        "build_private_qualification",
    ):
        assert banned not in source, banned
    # No tracked module may pair a review dimension with a literal answer value.
    for name, value in (
        ("single_factor_isolation", "yes"),
        ("goal_preserved", "no"),
        ("primitive_evidence_adequate", "no"),
    ):
        assert f'"{name}", "{value}"' not in source
        assert f'"decisive_dimension": "{name}"' not in source
        assert f'"expected_value": "{value}"' not in source


def test_qualification_packages_contain_no_answer_key() -> None:
    for role in (REVIEWER_A, REVIEWER_B):
        files = _archive(build_qualification_package(SOURCE, role)["package_bytes"])
        blob = b"".join(files.values()).lower()
        for banned in (
            b"decisive_dimension",
            b"expected_value",
            b"explanation",
            b"answer_key",
            b"construction",
        ):
            assert banned not in blob, (role, banned)
        assert not any("answer" in name.casefold() for name in files)
        assert not any("key" in name.casefold() for name in files)


def test_the_active_private_qualification_answers_are_not_in_tracked_files() -> None:
    """The real thing: nothing authored privately appears in any tracked file."""

    path = PRIVATE_ROOT / QUALIFICATION_DIRNAME / QUALIFICATION_SOURCE_FILENAME
    if not path.is_file():
        pytest.skip("the private qualification source is not present in this working tree")
    source = json.loads(path.read_text())
    needles: set[str] = set()
    for items in source["roles"].values():
        for entry in items:
            needles.add(str(entry["reviewer_item_id"]))
            needles.add(str(entry["item"]["task_objective"]))
            needles.add(str(entry["answer"].get("explanation", "")))
            needles.add(str(entry["answer"].get("construction", "")))
    needles = {value for value in needles if len(value) > 8}
    assert needles

    tracked = subprocess.run(
        ["git", "ls-files", "-z"], cwd=REPO_ROOT, check=True, capture_output=True
    ).stdout.split(b"\0")
    hits: list[str] = []
    for raw in tracked:
        if not raw:
            continue
        target = REPO_ROOT / raw.decode()
        if not target.is_file() or target.stat().st_size > 4_000_000:
            continue
        try:
            text = target.read_text(errors="ignore")
        except OSError:  # pragma: no cover - unreadable tracked file
            continue
        hits.extend(raw.decode() for needle in needles if needle in text)
    assert not hits, f"private qualification material appears in tracked files: {sorted(set(hits))}"


def test_no_private_qualification_or_reviewer_material_is_tracked() -> None:
    tracked = subprocess.run(
        ["git", "ls-files"], cwd=REPO_ROOT, check=True, capture_output=True, text=True
    ).stdout.split()
    for path in tracked:
        assert not path.startswith("private_data/"), path
        assert QUALIFICATION_SOURCE_FILENAME not in path, path
        assert "reviewer_assignments.json" not in path, path
        assert not path.endswith("qualification_key.enc"), path
        assert not path.endswith("stage2_vault.enc"), path
    ignored = (REPO_ROOT / ".gitignore").read_text()
    assert "private_data/" in ignored


# --------------------------------------------------------------------------
# 4-7 — adjudicator packages
# --------------------------------------------------------------------------


@pytest.fixture(scope="module")
def workspace_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """One complete fixture run whose sealed receipts survive for inspection."""

    root = tmp_path_factory.mktemp("cab-distribution") / "run"
    result = run_fixture_e2e(root=root)
    assert result["passed"], [step for step in result["steps"] if not step["passed"]]
    return root / "fixture_packet" / "fixture_receipts"


def _receipt(workspace_root: Path, name: str) -> dict[str, Any]:
    return json.loads((workspace_root / f"{name}.json").read_text())


def _queue_and_binding(stage: str) -> tuple[dict[str, Any], dict[str, Any]]:
    pair_ids = [f"fixture-pair-{index:02d}" for index in range(1, FIXTURE_PAIR_COUNT + 1)]
    disputed = pair_ids[0]
    queue = {
        "schema_version": f"cab_{stage}_disagreement_queue_v1",
        "stage": stage,
        "receipt_sha256": "a" * 64,
        "pair_count": len(pair_ids),
        "disputed_pair_count": 1,
        "disputed_dimension_count": 1,
        "disputes": [
            {
                "stage": stage,
                "pair_id": disputed,
                "dimension": "single_factor_isolation" if stage == STAGE1 else "gold_correct",
                "applicable": True,
                "reasons": ["reviewer_disagreement"],
                "reviewer_values": {REVIEWER_A: "yes", REVIEWER_B: "no"},
            }
        ],
    }
    binding = package_binding(
        stage=stage,
        queue=queue,
        private_packet_commitment="b" * 64,
        adjudicator_assignment_sha256="c" * 64,
        adjudicator_pseudonym_sha256="d" * 64,
        scientific_freeze_sha256=FIXTURE_FREEZE_SHA,
        exact_commit=FIXTURE_COMMIT,
    )
    return queue, binding


def _paired_rows(stage: str, pair_id: str) -> dict[str, dict[str, dict[str, str]]]:
    dimension = "single_factor_isolation" if stage == STAGE1 else "gold_correct"
    return {
        pair_id: {
            REVIEWER_A: {dimension: "yes", "reviewer_confidence": "4", "notes": ""},
            REVIEWER_B: {dimension: "no", "reviewer_confidence": "3", "notes": "objection"},
        }
    }


def test_stage1_adjudicator_package_includes_only_disputed_items() -> None:
    queue, binding = _queue_and_binding(STAGE1)
    disputed = disputed_pair_ids(queue)
    package = build_stage1_adjudicator_package(
        queue=queue,
        stage1_views={pair_id: _fixture_stage1_view(pair_id) for pair_id in disputed},
        paired_rows=_paired_rows(STAGE1, disputed[0]),
        binding=binding,
    )
    files = _archive(package["package_bytes"])
    items = sorted(name for name in files if name.startswith("items/"))
    assert items == [f"items/{disputed[0]}.json"]
    assert len(disputed) < FIXTURE_PAIR_COUNT
    blob = b"".join(files.values()).decode()
    for pair_id in (f"fixture-pair-{index:02d}" for index in range(2, FIXTURE_PAIR_COUNT + 1)):
        assert pair_id not in blob, pair_id
    manifest = json.loads(files["manifest.json"])
    assert manifest["non_disputed_items_included"] is False
    assert manifest["disputed_item_count"] == 1


def test_stage1_adjudicator_package_carries_evidence_and_no_stage2_leakage() -> None:
    queue, binding = _queue_and_binding(STAGE1)
    disputed = disputed_pair_ids(queue)
    package = build_stage1_adjudicator_package(
        queue=queue,
        stage1_views={pair_id: _fixture_stage1_view(pair_id) for pair_id in disputed},
        paired_rows=_paired_rows(STAGE1, disputed[0]),
        binding=binding,
    )
    files = _archive(package["package_bytes"])
    item = json.loads(files[f"items/{disputed[0]}.json"])
    for required in (
        "clean_instance",
        "intervention_instance",
        "controlled_difference",
        "intended_changed_factor",
        "claimed_preserved_invariants",
        "primitive_evidence_manifest",
        "declared_tool_capabilities",
        "disputed_dimensions",
    ):
        assert item[required], required
    reviewers = item["disputed_dimensions"][0]["reviewers"]
    assert set(reviewers) == {REVIEWER_A, REVIEWER_B}
    for row in reviewers.values():
        assert set(row) == {"value", "reviewer_confidence", "notes"}
    assert files["adjudication_form.json"]

    blob = b"".join(files.values()).decode()
    for banned in sorted(STAGE2_ONLY_KEYS):
        assert f'"{banned}"' not in blob, banned


def test_stage1_adjudicator_package_refuses_smuggled_stage2_material() -> None:
    queue, binding = _queue_and_binding(STAGE1)
    disputed = disputed_pair_ids(queue)
    view = _fixture_stage1_view(disputed[0])
    view["clean_instance"]["clean_gold"] = "smuggled"
    with pytest.raises(AdjudicationPackageError, match="Stage-2 material"):
        build_stage1_adjudicator_package(
            queue=queue,
            stage1_views={disputed[0]: view},
            paired_rows=_paired_rows(STAGE1, disputed[0]),
            binding=binding,
        )


def test_stage2_adjudicator_package_includes_the_required_private_evidence() -> None:
    queue, binding = _queue_and_binding(STAGE2)
    disputed = disputed_pair_ids(queue)
    applicability = fixture_applicability()
    package = build_stage2_adjudicator_package(
        queue=queue,
        stage2_records={
            pair_id: _fixture_stage2_record(pair_id, applicability[pair_id])
            for pair_id in disputed
        },
        applicability={pair_id: applicability[pair_id] for pair_id in disputed},
        paired_rows=_paired_rows(STAGE2, disputed[0]),
        binding=binding,
    )
    files = _archive(package["package_bytes"])
    assert sorted(name for name in files if name.startswith("items/")) == [
        f"items/{disputed[0]}.json"
    ]
    item = json.loads(files[f"items/{disputed[0]}.json"])
    for required in STAGE2_REQUIRED_EVIDENCE:
        assert required in item, required
    assert item["applicability"]
    assert item["disputed_dimensions"][0]["reviewers"].keys() == {REVIEWER_A, REVIEWER_B}
    # Conditional policy is present when the item has one and named as absent
    # when it does not, so silence is never mistaken for approval.
    present = [field for field in STAGE2_CONDITIONAL_EVIDENCE if field in item]
    assert set(present) | set(item["conditional_policies_absent"]) == set(
        STAGE2_CONDITIONAL_EVIDENCE
    )


def test_stage2_adjudicator_package_refuses_an_incomplete_record() -> None:
    queue, binding = _queue_and_binding(STAGE2)
    disputed = disputed_pair_ids(queue)
    applicability = fixture_applicability()
    record = _fixture_stage2_record(disputed[0], applicability[disputed[0]])
    record.pop("clean_scorer_contract")
    with pytest.raises(AdjudicationPackageError, match="required adjudication evidence"):
        build_stage2_adjudicator_package(
            queue=queue,
            stage2_records={disputed[0]: record},
            applicability={disputed[0]: applicability[disputed[0]]},
            paired_rows=_paired_rows(STAGE2, disputed[0]),
            binding=binding,
        )


def test_every_adjudicator_package_is_bound_to_its_identity(workspace_root: Path) -> None:
    for stage in (STAGE1, STAGE2):
        receipt = _receipt(workspace_root, f"{stage}_adjudicator_package")
        for field in BINDING_FIELDS:
            assert field in receipt, (stage, field)
            assert receipt[field] not in ("", None), (stage, field)
        assert len(receipt["package_sha256"]) == 64
        assert receipt["disagreement_queue_sha256"] == _receipt(
            workspace_root, f"{stage}_disagreement_queue"
        )["receipt_sha256"]
        assert receipt["adjudicator_is_neither_reviewer"] is True


def test_a_stale_adjudicator_package_is_rejected(workspace_root: Path) -> None:
    """The fixture run proves the live refusal; this pins the recorded evidence."""

    result = run_fixture_e2e()
    step = next(
        row for row in result["steps"] if row["step"] == "stale_adjudicator_package_refused"
    )
    assert step["passed"]
    for stage in (STAGE1, STAGE2):
        adjudication = _receipt(workspace_root, f"{stage}_adjudication")
        issued = _receipt(workspace_root, f"{stage}_adjudicator_package")
        assert adjudication["adjudicator_package_sha256"] == issued["package_sha256"]
        assert all(adjudication["adjudicator_package_checks"].values())


def test_the_adjudicator_cannot_be_either_reviewer() -> None:
    assert FIXTURE_PSEUDONYMS[ADJUDICATOR] not in (
        FIXTURE_PSEUDONYMS[REVIEWER_A],
        FIXTURE_PSEUDONYMS[REVIEWER_B],
    )
    result = run_fixture_e2e()
    step = next(
        row
        for row in result["steps"]
        if row["step"] == "assignment_registry_refuses_role_overlap"
    )
    assert step["passed"]


# --------------------------------------------------------------------------
# 8-11 — Stage-2 issuance
# --------------------------------------------------------------------------


def _issuance_arguments(**overrides: str) -> dict[str, str]:
    arguments = {
        "reviewer_role": REVIEWER_A,
        "reviewer_pseudonym_sha256": "1" * 64,
        "stage1_commitment_sha256": "2" * 64,
        # Issuance is bound to the immutable Stage-1 snapshot as well as to the
        # commitment, so a resealed Stage-1 receipt cannot authorise Stage 2.
        "stage1_snapshot_manifest_sha256": "a" * 64,
        "stage1_canonical_judgements_sha256": "b" * 64,
        "stage1_snapshot_receipt_sha256": "c" * 64,
        "stage2_package_sha256": "3" * 64,
        "stage2_opaque_id_namespace": "RA",
        "private_packet_commitment": "4" * 64,
        "qualification_receipt_sha256": "5" * 64,
        "reviewer_declaration_sha256": "6" * 64,
        "scientific_freeze_sha256": "7" * 64,
        "exact_commit": "8" * 40,
    }
    arguments.update(overrides)
    return arguments


@pytest.mark.parametrize(
    ("field", "wrong"),
    [
        ("reviewer_role", REVIEWER_B),
        ("reviewer_pseudonym_sha256", "9" * 64),
        ("stage1_commitment_sha256", "9" * 64),
        ("stage1_snapshot_manifest_sha256", "9" * 64),
        ("stage1_canonical_judgements_sha256", "9" * 64),
        ("stage1_snapshot_receipt_sha256", "9" * 64),
        ("stage2_package_sha256", "9" * 64),
        ("stage2_opaque_id_namespace", "RB"),
        ("private_packet_commitment", "9" * 64),
        ("qualification_receipt_sha256", "9" * 64),
        ("reviewer_declaration_sha256", "9" * 64),
        ("scientific_freeze_sha256", "9" * 64),
        ("exact_commit", "9" * 40),
    ],
)
def test_every_stage2_issuance_binding_fails_closed(field: str, wrong: str) -> None:
    """Modified ZIP, package swap, copied receipt, wrong reviewer, wrong freeze."""

    issued = build_stage2_issuance(**_issuance_arguments())
    with pytest.raises(Stage2IssuanceError):
        verify_stage2_issuance(issued, **_issuance_arguments(**{field: wrong}))
    # The unmodified binding still verifies, so the refusals above are specific.
    verify_stage2_issuance(issued, **_issuance_arguments())


def test_stage2_issuance_refuses_rows_from_another_namespace() -> None:
    issued = build_stage2_issuance(**_issuance_arguments())
    with pytest.raises(Stage2IssuanceError, match="namespace"):
        verify_stage2_issuance(
            issued, **_issuance_arguments(), submitted_item_ids=["RB-01", "RB-02"]
        )
    verify_stage2_issuance(
        issued, **_issuance_arguments(), submitted_item_ids=["RA-01", "RA-02"]
    )


def test_an_issuance_receipt_missing_a_required_field_is_refused() -> None:
    issued = build_stage2_issuance(**_issuance_arguments())
    assert set(REQUIRED_ISSUANCE_FIELDS) <= set(issued)
    for field in REQUIRED_ISSUANCE_FIELDS:
        stripped = {key: value for key, value in issued.items() if key != field}
        with pytest.raises(Stage2IssuanceError):
            verify_stage2_issuance(stripped, **_issuance_arguments())


def test_a_missing_stage2_issuance_receipt_blocks_ingestion(tmp_path: Path) -> None:
    from causal_agent_bench.review_ready_v2.workflow import ReviewWorkspace

    workspace = ReviewWorkspace.fixture(tmp_path / "packet")
    with pytest.raises(WorkflowError):
        workspace.ingest_stage2(
            REVIEWER_A,
            b"reviewer_item_id\n",
            expected_item_ids=[],
            applicability={},
            package_sha256="0" * 64,
            packet_commitment="1" * 64,
            scientific_freeze_sha256="2" * 64,
            exact_commit="3" * 40,
        )


def test_a_modified_stage2_package_and_a_package_swap_are_rejected() -> None:
    result = run_fixture_e2e()
    step = next(row for row in result["steps"] if row["step"] == "stage2_package_swap_refused")
    assert step["passed"], step


def test_stage2_issuance_is_bound_into_every_downstream_artifact(
    workspace_root: Path,
) -> None:
    issuance = {
        role: _receipt(workspace_root, f"stage2_issuance_{role}")
        for role in (REVIEWER_A, REVIEWER_B)
    }
    hashes = {role: receipt["receipt_sha256"] for role, receipt in issuance.items()}
    commitment = _receipt(workspace_root, "stage1_commitment")
    for role, receipt in issuance.items():
        assert receipt["reviewer_role"] == role
        assert receipt["stage1_commitment_sha256"] == commitment["receipt_sha256"]
        assert _receipt(workspace_root, f"stage2_submission_{role}")[
            "stage2_issuance_sha256"
        ] == hashes[role]
    for name in (
        "stage2_disagreement_queue",
        "final_adjudicated_records",
        "slice_lock",
        "stage1_adjudication",
        "stage2_adjudication",
    ):
        assert _receipt(workspace_root, name)["stage2_issuance_hashes"] == hashes, name

    c10 = _receipt(workspace_root, "c10_report")
    for check in (
        "stage2_issuance_receipts_issued",
        "stage2_issuance_bound_to_submissions",
        "stage2_issuance_matches_stage1_commitment",
        "stage2_issuance_bound_into_queue",
        "stage2_issuance_bound_into_final_records",
        "stage2_issuance_bound_into_adjudication",
        "adjudicator_packages_bound_to_their_queues",
    ):
        assert c10["checks"][check] is True, check

    lock = _receipt(workspace_root, "slice_lock")
    assert set(lock["stage2_package_hashes"]) == {REVIEWER_A, REVIEWER_B}
    assert lock["stage1_adjudicator_package_sha256"]
    assert lock["stage2_adjudicator_package_sha256"]
    authorization = _receipt(workspace_root, "execution_authorization")
    assert authorization["checks"]["stage2_issuance_bound_into_lock"] is True
    assert authorization["checks"]["stage2_issuance_unchanged_since_lock"] is True


# --------------------------------------------------------------------------
# 12-14 — the kernel, the false pass, and the freeze
# --------------------------------------------------------------------------


def test_the_false_c10_pass_remains_closed() -> None:
    result = run_fixture_e2e()
    assert result["c10"]["status"] == "C10_PENDING_GENUINE_REVIEW"
    assert result["c10"]["counts_as_genuine_evidence"] is False
    assert result["counts_as_genuine_evidence"] is False
    assert result["genuine_human_judgments"] == 0
    assert set(result["c10"]["failed_checks"]) == {
        "artifact_origin_is_production",
        "every_required_evidence_binding_present",
        "evidence_counts_as_genuine",
    }


def test_the_scientific_kernel_is_unchanged_by_this_patch() -> None:
    commitment = _report("PUBLIC_PACKET_COMMITMENT.json")
    assert commitment["stage1_package_hashes"] == FROZEN_STAGE1_PACKAGE_HASHES
    assert len(commitment["pair_content_hashes"]) == 20
    digest = sha256_bytes(
        json.dumps(commitment["pair_content_hashes"], sort_keys=True, separators=(",", ":")).encode()
    )
    assert digest == FROZEN_PAIR_CONTENT_DIGEST
    assert commitment["pair_count"] == 20
    assert commitment["qualification_version"] == QUALIFICATION_SCHEMA_VERSION


def test_the_freeze_verifies_in_a_single_branch_fresh_clone(tmp_path: Path) -> None:
    """Clone the branch alone, drop every unreachable object, verify in place.

    The clone runs its *own* checked-out code against its *own* checked-out
    freeze, so the test proves the committed pair verifies, not that this working
    tree happens to agree with itself.
    """

    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()
    clone = tmp_path / "clone"
    subprocess.run(
        ["git", "clone", "--single-branch", "--branch", "main", str(REPO_ROOT), str(clone)],
        check=True,
        capture_output=True,
    )
    subprocess.run(["git", "reset", "--hard", head], cwd=clone, check=True, capture_output=True)
    subprocess.run(
        ["git", "reflog", "expire", "--expire=now", "--all"], cwd=clone, check=True, capture_output=True
    )
    subprocess.run(["git", "gc", "--prune=now", "--aggressive"], cwd=clone, check=True, capture_output=True)

    if not (clone / "reports/reviewer_ready_v2/SCIENTIFIC_FREEZE_V2.json").is_file():
        pytest.skip("the freeze is not committed on this branch yet")
    result = subprocess.run(
        [sys.executable, "scripts/cab_review_ready_v2.py", "verify-freeze"],
        cwd=clone,
        check=False,
        capture_output=True,
        text=True,
        env={
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            # Only the clone's own sources, so the freeze is checked by the code
            # it was written against rather than by this working tree.
            "PYTHONPATH": str(clone / "src"),
            "HOME": str(tmp_path),
        },
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert report["passed"], report["checks"]
    assert report["status"] == "CAB_SCIENTIFIC_FREEZE_V2_VALID"
