from __future__ import annotations

from pathlib import Path

from causal_agent_bench.safety.method_appendix import build_method_appendix


def test_method_appendix_is_disclaimer_only(tmp_path: Path) -> None:
    report = build_method_appendix(tmp_path)
    text = Path(report["report_paths"]["markdown"]).read_text(encoding="utf-8").lower()
    tex = Path(report["report_paths"]["tex"]).read_text(encoding="utf-8").lower()
    combined = text + "\n" + tex
    assert "method scaffold only" in combined
    assert "no empirical results" in combined
    assert "no model comparisons" in combined
    assert "supported c1-c8" not in combined
    assert "accuracy" not in combined
    assert "outperforms" not in combined
    assert "95%" not in combined
