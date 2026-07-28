from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

from causal_agent_bench.safety.human_review_gate import (
    ADJUDICATION_COLUMNS,
    REVIEW_COLUMNS,
    REVIEW_DIMENSIONS,
    REVIEWER_REGISTRY_COLUMNS,
    validate_compact20_human_reviews,
)
from causal_agent_bench.safety.human_validation_packet import (
    build_c10_review_packet,
)

REPO = Path(__file__).resolve().parents[1]
CONTRACT = REPO / "configs/human_validation/c10_contract_v1.json"
REVIEWER_A = "rvw_aaaaaaaaaaaa"
REVIEWER_B = "rvw_bbbbbbbbbbbb"
ADJUDICATOR = "adj_cccccccccccc"


def _write_csv(
    path: Path,
    header: list[str] | tuple[str, ...],
    rows: list[dict[str, Any]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(header))
        writer.writeheader()
        writer.writerows(rows)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fixture(
    tmp_path: Path,
    *,
    candidate_count: int = 5,
    disagreement_candidates: set[int] | None = None,
    adjudicate: bool = False,
) -> tuple[Path, Path]:
    disagreement_candidates = disagreement_candidates or set()
    manifest = tmp_path / "manifest.json"
    instances = tmp_path / "instances.jsonl"
    candidates = []
    instance_rows = []
    for index in range(candidate_count):
        candidate_id = f"c{index + 1}"
        instance_id = f"task_{index}.tool_removal"
        candidates.append(
            {
                "candidate_id": candidate_id,
                "base_task_id": f"task_{index}",
                "clean_instance_id": f"task_{index}.clean",
                "intervention_instance_id": instance_id,
                "family": "tool_removal",
                "domain": "fixture",
                "difficulty": "fixture",
            }
        )
        instance_rows.append(
            {
                "instance_id": instance_id,
                "available_tools": ["fallback_tool"],
                "intervention": {
                    "family": "tool_removal",
                    "tool_availability_patch": {
                        "removed_tools": ["required_tool"]
                    },
                },
                "base_task": {
                    "task_id": f"task_{index}",
                    "domain": "fixture",
                    "difficulty": "fixture",
                    "user_instruction": "Fixture-only qualification task.",
                },
            }
        )
    manifest.write_text(
        json.dumps({"candidates": candidates}),
        encoding="utf-8",
    )
    instances.write_text(
        "".join(json.dumps(row) + "\n" for row in instance_rows),
        encoding="utf-8",
    )
    review = tmp_path / "reviews"
    build_c10_review_packet(
        tmp_path,
        output_dir=review,
        candidate_manifest=manifest,
        instances_path=instances,
    )

    session_path = review / "review_session.json"
    session = json.loads(session_path.read_text(encoding="utf-8"))
    session.update(
        {
            "review_mode": "fixture",
            "evidence_class": "FIXTURE_ONLY",
            "human_only_attestation": False,
            "completed_at": "2026-01-01T00:00:00Z",
        }
    )
    session_path.write_text(
        json.dumps(session, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    registry_rows = []
    for reviewer_id, role in (
        (REVIEWER_A, "reviewer"),
        (REVIEWER_B, "reviewer"),
        (ADJUDICATOR, "adjudicator"),
    ):
        registry_rows.append(
            {
                "reviewer_id": reviewer_id,
                "role": role,
                "privacy_safe_id_confirmed": "yes",
                "qualification_status": "passed",
                "qualification_score": "4",
                "qualification_total": "5",
                "expertise_disclosure": "fixture_only",
                "conflict_of_interest": "not_applicable_fixture",
                "consent_confirmed": "not_applicable_fixture",
                "human_only_attestation": "no",
                "is_study_author": "not_applicable_fixture",
                "compensation_disclosure_ack": "not_applicable_fixture",
                "registered_at": "2026-01-01T00:00:00Z",
            }
        )
    _write_csv(
        review / "reviewer_registry.csv",
        REVIEWER_REGISTRY_COLUMNS,
        registry_rows,
    )

    review_rows = []
    for index, candidate in enumerate(candidates):
        for slot, reviewer_id in enumerate(
            (REVIEWER_A, REVIEWER_B),
            start=1,
        ):
            row = dict.fromkeys(REVIEW_COLUMNS, "")
            row.update(
                {
                    "candidate_id": candidate["candidate_id"],
                    "reviewer_slot": str(slot),
                    "reviewer_id": reviewer_id,
                    "review_source": "fixture",
                    "ai_assistance_used": "no",
                    "model_output_visible": "no",
                    "model_identity_visible": "no",
                    "confidence_1_to_5": "4",
                    "notes": "FIXTURE STRUCTURE ONLY",
                    "timestamp": f"2026-01-01T00:0{slot}:00Z",
                }
            )
            for dimension in REVIEW_DIMENSIONS:
                if dimension == "ambiguity":
                    row[dimension] = "acceptable"
                elif dimension == "exclusion_recommendation":
                    row[dimension] = "include"
                else:
                    row[dimension] = "yes"
            if index in disagreement_candidates and reviewer_id == REVIEWER_B:
                for dimension in REVIEW_DIMENSIONS[:9]:
                    row[dimension] = "no"
                row["ambiguity"] = "problematic"
                row["exclusion_recommendation"] = "exclude"
            review_rows.append(row)
    _write_csv(review / "review_judgments.csv", REVIEW_COLUMNS, review_rows)

    adjudication_rows = []
    if adjudicate:
        rows_by_candidate = {
            candidate["candidate_id"]: [
                row
                for row in review_rows
                if row["candidate_id"] == candidate["candidate_id"]
            ]
            for candidate in candidates
        }
        for index in sorted(disagreement_candidates):
            candidate_id = candidates[index]["candidate_id"]
            for dimension in REVIEW_DIMENSIONS:
                labels = [
                    row[dimension] for row in rows_by_candidate[candidate_id]
                ]
                adjudication_rows.append(
                    {
                        "candidate_id": candidate_id,
                        "dimension": dimension,
                        "reviewer_ids": f"{REVIEWER_A}|{REVIEWER_B}",
                        "reviewer_labels": "|".join(labels),
                        "final_label": (
                            "acceptable"
                            if dimension == "ambiguity"
                            else "include"
                            if dimension == "exclusion_recommendation"
                            else "yes"
                        ),
                        "adjudicator_id": ADJUDICATOR,
                        "review_source": "fixture",
                        "ai_assistance_used": "no",
                        "rationale": "Fixture-only adjudication path.",
                        "timestamp": "2026-01-01T00:10:00Z",
                    }
                )
    _write_csv(
        review / "adjudication.csv",
        ADJUDICATION_COLUMNS,
        adjudication_rows,
    )

    for name, prerequisite_name in (
        ("leakage", "leakage_gate"),
        ("answer_contract", "answer_contract"),
    ):
        report_path = review / f"{name}_fixture.json"
        report_path.write_text(
            json.dumps(
                {
                    "passed": True,
                    "evidence_class": "FIXTURE_ONLY",
                }
            ),
            encoding="utf-8",
        )
        prerequisites_path = review / "c10_prerequisites.json"
        prerequisites = json.loads(
            prerequisites_path.read_text(encoding="utf-8")
        )
        prerequisites[prerequisite_name] = {
            "passed": True,
            "report_path": report_path.name,
            "report_sha256": _sha256(report_path),
        }
        prerequisites_path.write_text(
            json.dumps(prerequisites, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return review, manifest


def _validate(
    tmp_path: Path,
    review: Path,
    manifest: Path,
) -> dict[str, Any]:
    return validate_compact20_human_reviews(
        tmp_path,
        review_dir=review,
        candidate_manifest=manifest,
        contract_path=CONTRACT,
    )


def test_header_only_repository_packet_fails_closed() -> None:
    payload = validate_compact20_human_reviews(REPO)
    assert payload["genuine_human_row_count"] == 0
    assert payload["blank_template_review_rows"] == 40
    assert payload["human_review_state"] == "HUMAN_REVIEW_INCOMPLETE"
    assert payload["c10_state"] == "C10_PENDING"
    assert payload["slice_lock_allowed"] is False
    assert payload["paper_eligibility_allowed"] is False


def test_header_only_canonical_review_file_fails_closed(
    tmp_path: Path,
) -> None:
    review, manifest = _fixture(tmp_path)
    _write_csv(review / "review_judgments.csv", REVIEW_COLUMNS, [])
    payload = _validate(tmp_path, review, manifest)
    assert payload["fixture_review_row_count"] == 0
    assert payload["complete_review_groups"] == 0
    assert payload["c10_state"] == "C10_PENDING"


def test_complete_fixture_validates_contract_without_becoming_human_evidence(
    tmp_path: Path,
) -> None:
    review, manifest = _fixture(tmp_path)
    payload = _validate(tmp_path, review, manifest)
    assert payload["fixture_review_row_count"] == 10
    assert payload["genuine_human_row_count"] == 0
    assert payload["raw_agreement"] == 1.0
    assert payload["contract_evaluation_state"] == "FIXTURE_CONTRACT_PASS"
    assert payload["fixture_contract_passed"] is True
    assert payload["evidence_class"] == "FIXTURE_ONLY"
    assert payload["c10_state"] == "C10_PENDING"
    assert payload["slice_lock_allowed"] is False


def test_disagreement_requires_separate_adjudication(
    tmp_path: Path,
) -> None:
    review, manifest = _fixture(
        tmp_path,
        disagreement_candidates={0},
    )
    payload = _validate(tmp_path, review, manifest)
    assert payload["human_review_state"] == "ADJUDICATION_PENDING"
    assert payload["c10_state"] == "C10_PENDING"
    assert payload["unresolved_disagreements"]


def test_reviewer_cannot_adjudicate_own_disagreement(
    tmp_path: Path,
) -> None:
    review, manifest = _fixture(
        tmp_path,
        disagreement_candidates={0},
        adjudicate=True,
    )
    path = review / "adjudication.csv"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            ADJUDICATOR,
            REVIEWER_A,
        ),
        encoding="utf-8",
    )
    payload = _validate(tmp_path, review, manifest)
    assert payload["human_review_state"] == "ADJUDICATION_PENDING"
    assert any(
        issue["code"] == "ADJUDICATOR_NOT_SEPARATE"
        for issue in payload["issues"]
    )


def test_adjudication_resolves_labels_but_not_low_raw_agreement(
    tmp_path: Path,
) -> None:
    review, manifest = _fixture(
        tmp_path,
        disagreement_candidates={0, 1},
        adjudicate=True,
    )
    payload = _validate(tmp_path, review, manifest)
    assert payload["adjudication"]["complete"] is True
    assert payload["raw_agreement"] == 0.6
    assert payload["agreement_threshold_met"] is False
    assert payload["contract_evaluation_state"] == "CONTRACT_FAILED"
    assert payload["c10_state"] == "C10_FAILED"


def test_proxy_or_ai_review_never_counts(
    tmp_path: Path,
) -> None:
    review, manifest = _fixture(tmp_path)
    path = review / "review_judgments.csv"
    text = path.read_text(encoding="utf-8").replace(
        ",fixture,no,no,no,",
        ",ai_proxy,yes,no,no,",
        1,
    )
    path.write_text(text, encoding="utf-8")
    payload = _validate(tmp_path, review, manifest)
    assert payload["fixture_review_row_count"] == 9
    assert payload["genuine_human_row_count"] == 0
    assert payload["proxy_rows_counted"] == 0
    assert payload["c10_state"] == "C10_PENDING"
    assert any(
        issue["code"] == "PROXY_OR_AI_REVIEW_REJECTED"
        for issue in payload["issues"]
    )


def test_fake_id_is_rejected(
    tmp_path: Path,
) -> None:
    review, manifest = _fixture(tmp_path)
    path = review / "reviewer_registry.csv"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            REVIEWER_A,
            "reviewer",
        ),
        encoding="utf-8",
    )
    payload = _validate(tmp_path, review, manifest)
    assert payload["complete_review_groups"] == 0
    assert any(
        issue["code"] == "FAKE_OR_INVALID_REVIEWER_ID"
        for issue in payload["issues"]
    )


def test_duplicated_reviewer_is_rejected(
    tmp_path: Path,
) -> None:
    review, manifest = _fixture(tmp_path)
    path = review / "review_judgments.csv"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            REVIEWER_B,
            REVIEWER_A,
            1,
        ),
        encoding="utf-8",
    )
    payload = _validate(tmp_path, review, manifest)
    assert payload["c10_state"] == "C10_PENDING"
    assert any(
        issue["code"] == "DUPLICATED_REVIEWER_FOR_CANDIDATE"
        for issue in payload["issues"]
    )


def test_missing_candidate_coverage_fails_closed(
    tmp_path: Path,
) -> None:
    review, manifest = _fixture(tmp_path)
    path = review / "review_judgments.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    _write_csv(
        path,
        REVIEW_COLUMNS,
        [row for row in rows if row["candidate_id"] != "c5"],
    )
    payload = _validate(tmp_path, review, manifest)
    assert payload["complete_review_groups"] == 4
    assert payload["c10_state"] == "C10_PENDING"


def test_invalid_dimension_value_is_rejected(
    tmp_path: Path,
) -> None:
    review, manifest = _fixture(tmp_path)
    path = review / "review_judgments.csv"
    text = path.read_text(encoding="utf-8").replace(
        ",yes,yes,yes,yes,yes,yes,yes,yes,yes,acceptable,include,",
        ",maybe,yes,yes,yes,yes,yes,yes,yes,yes,acceptable,include,",
        1,
    )
    path.write_text(text, encoding="utf-8")
    payload = _validate(tmp_path, review, manifest)
    assert any(
        issue["code"] == "INVALID_REVIEW_VALUE"
        for issue in payload["issues"]
    )
    assert payload["c10_state"] == "C10_PENDING"


def test_missing_verified_prerequisite_blocks_otherwise_complete_fixture(
    tmp_path: Path,
) -> None:
    review, manifest = _fixture(tmp_path)
    prerequisites_path = review / "c10_prerequisites.json"
    prerequisites = json.loads(
        prerequisites_path.read_text(encoding="utf-8")
    )
    prerequisites["leakage_gate"]["passed"] = False
    prerequisites_path.write_text(
        json.dumps(prerequisites),
        encoding="utf-8",
    )
    payload = _validate(tmp_path, review, manifest)
    assert payload["contract_evaluation_state"] == "CONTRACT_FAILED"
    assert "LEAKAGE_GATE_MISSING_OR_INVALID" in payload["c10_blockers"]
    assert payload["c10_state"] != "PASS"


def test_study_author_registry_entry_is_ineligible(
    tmp_path: Path,
) -> None:
    review, manifest = _fixture(tmp_path)
    path = review / "reviewer_registry.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    rows[0]["is_study_author"] = "yes"
    _write_csv(path, REVIEWER_REGISTRY_COLUMNS, rows)
    payload = _validate(tmp_path, review, manifest)
    assert payload["complete_review_groups"] < 5
    assert any(
        issue["code"]
        == "REVIEWER_QUALIFICATION_OR_DISCLOSURE_INVALID"
        for issue in payload["issues"]
    )


def test_protocol_and_resource_docs_cover_required_controls() -> None:
    protocol = (
        REPO / "docs/ICLR_HUMAN_VALIDATION_PROTOCOL.md"
    ).read_text(encoding="utf-8")
    resources = (
        REPO / "docs/HUMAN_REVIEW_RESOURCE_PLAN.md"
    ).read_text(encoding="utf-8")
    ethics = (REPO / "docs/ETHICS_AND_LIMITATIONS.md").read_text(
        encoding="utf-8"
    )
    for phrase in (
        "model-output",
        "model-identity",
        "two independent",
        "separate adjudicator",
        "Cohen's kappa",
        "Krippendorff's alpha",
        "prevalence",
        "fixture-only",
    ):
        assert phrase.lower() in protocol.lower()
    assert "ESTIMATE_NOT_MEASURED" in resources
    assert "Compact-20" in resources and "Scale-100" in resources
    assert "Prospective consent language" in ethics
    assert "Authors as reviewers" in ethics
