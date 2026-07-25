"""Build Mode Phase 5: paper package, handoff, review simulation."""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def test_phase5_handoff_docs_exist():
    for rel in (
        "handoff/ADVISOR_HANDOFF_PACKET.md",
        "handoff/ONE_PAGE_PROJECT_BRIEF.md",
        "handoff/ADVISOR_MESSAGE_DRAFT.md",
    ):
        assert (REPO / rel).exists(), rel


def test_phase5_paper_planning_docs_exist():
    for rel in (
        "paper/CONTRIBUTION_MAP.md",
        "paper/EVIDENCE_GAP_MAP.md",
        "paper/PAPER_STATUS.md",
        "paper/PAPER_SYNC_MAP.md",
        "paper/latexpaper/main.tex",
        "docs/FIGURE_TABLE_BLUEPRINT.md",
    ):
        assert (REPO / rel).exists(), rel


def test_phase5_review_docs_exist():
    for rel in (
        "reviews/MOCK_REVIEW_1_SUPPORTIVE.md",
        "reviews/MOCK_REVIEW_2_SKEPTICAL.md",
        "reviews/MOCK_REVIEW_3_BORDERLINE.md",
        "reviews/MOCK_REVIEW_SUMMARY.md",
        "reviews/REBUTTAL_PREP.md",
    ):
        assert (REPO / rel).exists(), rel


def test_lint_paper_claims_draft_mode():
    from scripts.lint_paper_claims import lint_paper_claims

    findings = lint_paper_claims(REPO / "paper" / "latexpaper", mode="draft")
    # Draft may warn on placeholders; should not error on every file
    errors = [f for f in findings if f.severity == "error"]
    assert len(errors) == 0


def test_lint_paper_claims_submission_flags_placeholders():
    from scripts.lint_paper_claims import lint_paper_claims

    findings = lint_paper_claims(REPO / "paper" / "latexpaper", mode="submission")
    kinds = {f.kind for f in findings}
    assert "result_placeholder" in kinds or any("placeholder" in f.kind for f in findings)


def test_evidence_gap_map_covers_claims():
    text = (REPO / "paper/EVIDENCE_GAP_MAP.md").read_text(encoding="utf-8")
    for claim in ("C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9", "C10"):
        assert claim in text
