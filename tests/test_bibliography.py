"""Tests for paper bibliography hygiene."""

from __future__ import annotations

from pathlib import Path

from scripts.check_bibliography import extract_bib_keys, extract_cite_keys, find_missing_citations

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_related_work_citations_resolve() -> None:
    paper_root = REPO_ROOT / "paper" / "latexpaper"
    missing = find_missing_citations(paper_root, paper_root / "references.bib")
    assert missing == [], f"Missing bibliography keys: {missing}"


def test_extract_cite_keys_splits_comma_separated() -> None:
    tex = r"See \citep{foo,bar} and \citet{baz}."
    assert extract_cite_keys(tex) == {"foo", "bar", "baz"}


def test_extract_bib_keys_finds_entries() -> None:
    bib = "@article{a, title={A}}\n@misc{b, title={B}}"
    assert extract_bib_keys(bib) == {"a", "b"}
