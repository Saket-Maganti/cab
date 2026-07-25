
from causal_agent_bench.analysis.failure_gallery_doc import (
    GALLERY_FAMILY_SPECS,
    build_gallery_examples,
    export_failure_gallery_doc,
    render_failure_gallery_markdown,
)
from causal_agent_bench.runners.config import ExperimentConfig
from causal_agent_bench.runners.experiment import run_experiment
from tests.test_error_analysis import _synthetic_error_run


def test_scaffold_gallery_has_all_families():
    examples, provenance = build_gallery_examples(None)
    assert len(examples) == len(GALLERY_FAMILY_SPECS)
    assert provenance["source"] == "illustrative_scaffold"
    for spec in GALLERY_FAMILY_SPECS:
        example = examples[spec.key]
        assert example["intervention_family"] == spec.intervention_family
        assert example["trajectory_excerpt"]
        assert example["why_final_answer_misses"]
        assert example["paper_short"]


def test_export_failure_gallery_doc_writes_markdown_and_tex(tmp_path):
    doc_path = tmp_path / "FAILURE_GALLERY.md"
    paper_path = tmp_path / "failure_gallery_short.tex"
    paths = export_failure_gallery_doc(doc_path=doc_path, paper_path=paper_path)
    assert doc_path in paths
    text = doc_path.read_text(encoding="utf-8")
    assert "# Agent Failure Gallery" in text
    assert "tool_failure_recovery" in text
    assert "long_horizon_dependency" in text
    assert "illustrative_scaffold" in text
    tex = paper_path.read_text(encoding="utf-8")
    assert "\\paragraph{" in tex
    assert "Do not cite as final results" in tex


def test_mined_gallery_from_synthetic_run(tmp_path):
    data = _synthetic_error_run(tmp_path)
    examples, provenance = build_gallery_examples(data)
    assert provenance["source"] == "mined_from_run"
    markdown = render_failure_gallery_markdown(examples, provenance)
    assert "observation_conflict" in markdown
    assert str(data.run_dir) in markdown


def test_export_with_experiment_run(tmp_path):
    config = ExperimentConfig.model_validate(
        {
            "seed": 41,
            "run_name": "gallery_doc_smoke",
            "benchmark_path": "data/sample/instances.jsonl",
            "agents": ["random_tool_agent"],
            "max_steps": 6,
            "num_repeats": 1,
            "output_dir": str(tmp_path),
            "auto_score": True,
        }
    )
    run_dir = run_experiment(config)["run_dir"]
    doc_path = tmp_path / "gallery.md"
    export_failure_gallery_doc(
        run_dir=run_dir,
        doc_path=doc_path,
        paper_path=tmp_path / "short.tex",
        allow_engineering_only=True,
        allow_mock_stub=True,
    )
    text = doc_path.read_text(encoding="utf-8")
    assert "mined_from_run" in text or "engineering" in text
    assert str(run_dir) in text
