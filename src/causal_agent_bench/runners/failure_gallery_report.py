from __future__ import annotations

import itertools
import json
from pathlib import Path
from typing import Any

from causal_agent_bench.analysis.error_analysis import mine_error_taxonomy
from causal_agent_bench.analysis.load_results import RunResults, load_run_results
from causal_agent_bench.runners.run_completion import infer_completion_state, load_run_metadata
from causal_agent_bench.schemas import BenchmarkInstance, Trajectory
from causal_agent_bench.utils.io import read_jsonl

GALLERY_CATEGORIES = {
    "invalid_tool_calls": ["tool_argument_malformed", "tool_argument_semantically_wrong", "wrong_tool_selected"],
    "missed_required_tools": ["required_tool_omitted"],
    "premature_stops": ["premature_stopping"],
    "contradiction_misses": ["contradiction_missed", "contradiction_noticed_but_unresolved"],
    "memory_verification_failures": ["blind_trust_in_corrupted_memory"],
    "tool_overuse": ["excessive_tool_overuse", "overlong_inefficient_trajectory"],
    "recovery_failures": ["failure_to_recover_from_tool_error", "repeated_failed_calls"],
}


def _load_results_safe(run_dir: Path) -> RunResults | None:
    try:
        if (run_dir / "aggregate_scores.json").exists():
            return load_run_results(run_dir, ensure_scores=False)
        if not (run_dir / "trajectories.jsonl").exists():
            return None
        metadata = load_run_metadata(run_dir)
        trajectories = read_jsonl(run_dir / "trajectories.jsonl", Trajectory)
        instances = (
            read_jsonl(run_dir / "instances.jsonl", BenchmarkInstance)
            if (run_dir / "instances.jsonl").exists()
            else []
        )
        return RunResults(
            run_dir=run_dir,
            run_metadata=metadata,
            aggregate={},
            scores=[],
            instances=instances,
            legacy_tasks=[],
            trajectories=trajectories,
            scores_df=__import__("pandas").DataFrame(),
            instances_df=__import__("pandas").DataFrame(),
            trajectories_df=__import__("pandas").DataFrame(),
        )
    except Exception:
        return None


def build_failure_gallery(run_dir: str | Path, *, max_cases: int = 3) -> dict[str, Any]:
    run_dir = Path(run_dir)
    state = infer_completion_state(run_dir)
    metadata = load_run_metadata(run_dir)
    data = _load_results_safe(run_dir)
    taxonomy: dict[str, list[dict[str, Any]]] = {}
    if data is not None and data.scores:
        taxonomy = mine_error_taxonomy(data, max_cases=max_cases)
    elif data is not None:
        taxonomy = {slug: [] for slug in itertools.chain.from_iterable(GALLERY_CATEGORIES.values())}

    grouped: dict[str, list[dict[str, Any]]] = {key: [] for key in GALLERY_CATEGORIES}
    for category, slugs in GALLERY_CATEGORIES.items():
        for slug in slugs:
            grouped[category].extend(taxonomy.get(slug, []))

    label = "engineering/preliminary"
    agents = metadata.get("agents") or []
    agent_runs = metadata.get("agent_runs") or []
    is_mock = any("mock" in str(name).lower() for name in agents) or any(
        run.get("agent") == "mock_behavior_agent" for run in agent_runs
    )
    is_stub = any("stub" in str(name).lower() for name in agents) or metadata.get("evidence_scope") in {
        "local_stub",
        "engineering_only",
    }
    if is_mock or is_stub:
        label = "engineering/preliminary"
    elif state["completion_state"] == "complete" and state["run_status"] not in {"dry_run"}:
        label = "preliminary" if metadata.get("scientific_evidence_level") == "preliminary_or_engineering" else "candidate"
    if state["completion_state"] != "complete":
        label = "incomplete/engineering"

    return {
        "run_dir": str(run_dir),
        "run_id": run_dir.name,
        "evidence_label": label,
        "completion_state": state["completion_state"],
        "categories": grouped,
        "counts": {key: len(items) for key, items in grouped.items()},
        "caveat": (
            "Failure gallery mined from deterministic diagnostics. "
            "Not final scientific evidence unless backed by completed validated runs."
        ),
    }


def render_failure_gallery_markdown(gallery: dict[str, Any]) -> str:
    lines = [
        "# Failure gallery",
        "",
        f"- **Run:** `{gallery['run_id']}`",
        f"- **Evidence label:** {gallery['evidence_label']}",
        f"- **Completion:** {gallery['completion_state']}",
        "",
        f"> {gallery['caveat']}",
        "",
    ]
    for category, cases in gallery["categories"].items():
        lines.append(f"## {category.replace('_', ' ').title()} ({len(cases)})")
        if not cases:
            lines.append("- none mined")
        else:
            for case in cases[:3]:
                lines.append(
                    f"- `{case.get('instance_id', '?')}` / {case.get('agent_name', '?')}: "
                    f"{case.get('summary', case.get('taxonomy_error_type', 'case'))}"
                )
        lines.append("")
    return "\n".join(lines)


def write_failure_gallery(run_dir: str | Path, *, max_cases: int = 3) -> dict[str, Path]:
    run_dir = Path(run_dir)
    gallery = build_failure_gallery(run_dir, max_cases=max_cases)
    md_path = run_dir / "failure_gallery.md"
    json_path = run_dir / "failure_gallery.json"
    md_path.write_text(render_failure_gallery_markdown(gallery), encoding="utf-8")
    json_path.write_text(json.dumps(gallery, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    return {"markdown": md_path, "json": json_path}
