from __future__ import annotations

import json
from pathlib import Path

from causal_agent_bench.safety.benchmark_cards import build_benchmark_cards


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def _dataset(root: Path) -> Path:
    data = root / "data/processed/tiny"
    task = {
        "task_id": "task_1",
        "domain": "policy",
        "goal": {"user_instruction": "Check threshold.", "expected_final_answer": "500"},
        "available_tools": ["lookup"],
    }
    _write_jsonl(data / "base_tasks.jsonl", [task])
    _write_jsonl(
        data / "instances.jsonl",
        [{"instance_id": "task_1.clean", "condition": "clean", "base_task": task, "available_tools": ["lookup"]}],
    )
    _write_jsonl(
        data / "interventions.jsonl",
        [{"intervention_id": "task_1.memory_corruption", "base_task_id": "task_1", "family": "memory_corruption"}],
    )
    (data / "splits.json").write_text(json.dumps({"splits": {"heldout": {"base_task_ids": ["task_1"], "instance_ids": ["task_1.clean"]}}}), encoding="utf-8")
    return data


def test_cards_generated(tmp_path: Path) -> None:
    dataset = _dataset(tmp_path)
    report = build_benchmark_cards(tmp_path, benchmark_dir=dataset, output_dir=tmp_path / "cards")
    for path in report["files"].values():
        assert Path(path).exists()
    assert Path(report["manifest_path"]).exists()


def test_cards_contain_no_empirical_result_claims(tmp_path: Path) -> None:
    dataset = _dataset(tmp_path)
    report = build_benchmark_cards(tmp_path, benchmark_dir=dataset, output_dir=tmp_path / "cards")
    text = Path(report["files"]["benchmark_card"]).read_text(encoding="utf-8")
    assert "No empirical results are claimed" in text
    assert "C1-C8: planned / unsupported" in text
    assert "C9: engineering_only" in text
    assert "C10: planned / unsupported" in text


def test_cards_mention_zero_paper_eligible_or_no_provider_evidence(tmp_path: Path) -> None:
    dataset = _dataset(tmp_path)
    report = build_benchmark_cards(tmp_path, benchmark_dir=dataset, output_dir=tmp_path / "cards")
    combined = "\n".join(Path(path).read_text(encoding="utf-8") for path in report["files"].values())
    assert "Paper-eligible runs: 0" in combined or "No current provider-backed evidence" in combined


def test_limitations_and_manifest_generated(tmp_path: Path) -> None:
    dataset = _dataset(tmp_path)
    report = build_benchmark_cards(tmp_path, benchmark_dir=dataset, output_dir=tmp_path / "cards")
    limitations = Path(report["files"]["limitations_card"]).read_text(encoding="utf-8")
    manifest = json.loads(Path(report["manifest_path"]).read_text(encoding="utf-8"))
    assert "No current provider-backed evidence" in limitations
    assert manifest["hard_rules"]["claims_promoted"] is False
