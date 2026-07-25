"""Tests for NeurIPS reviewer proofing artifacts."""

from __future__ import annotations

from pathlib import Path

from scripts.check_reviewer_proofing import EXPECTED_ATTACK_COUNT, validate_matrix

REPO_ROOT = Path(__file__).resolve().parents[1]
MATRIX = REPO_ROOT / "reviews" / "reviewer_attack_response_matrix.md"


def test_reviewer_attack_matrix_complete() -> None:
    issues = validate_matrix(MATRIX)
    assert issues == [], f"Matrix validation issues: {issues}"


def test_matrix_documents_all_twenty_attacks() -> None:
    text = MATRIX.read_text(encoding="utf-8")
    for number in range(1, EXPECTED_ATTACK_COUNT + 1):
        assert f"### {number}." in text
