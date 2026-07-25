from __future__ import annotations

from pathlib import Path

from causal_agent_bench.safety.method_figures import FIGURES, write_method_figure_scaffolds


def test_method_figure_scaffolds_exist_and_are_non_empirical(tmp_path: Path) -> None:
    report = write_method_figure_scaffolds(tmp_path)
    for name in FIGURES:
        path = Path(report["files"][name])
        assert path.exists()
        text = path.read_text(encoding="utf-8").lower()
        assert "accuracy" not in text
        assert "performance" not in text
        assert "%" not in text
    doc = Path(report["files"]["docs/PAPER_METHOD_FIGURES.md"]).read_text(encoding="utf-8").lower()
    assert "method/scaffold figures only" in doc
    assert "do not show empirical results" in doc
    assert "not evidence for c1-c8 or c10" in doc
