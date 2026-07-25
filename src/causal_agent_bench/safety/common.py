from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from causal_agent_bench.claim_ledger import (
    MOCK_STUB_DRY_EVIDENCE_MARKERS,
    NON_SCIENTIFIC_EVIDENCE_SCOPES,
)
from causal_agent_bench.runners.run_completion import infer_completion_state, load_run_metadata

RUN_CLASSIFICATIONS = frozenset(
    {
        "complete_scientific_evidence",
        "complete_engineering_only",
        "incomplete",
        "interrupted",
        "mock_diagnostic",
        "stub_engineering",
        "local_preliminary",
        "provider_backed_pilot",
        "main_benchmark",
        "unknown_needs_review",
    }
)

ASSET_CLASSIFICATIONS = frozenset(
    {
        "eligible_for_paper_claims",
        "engineering_only",
        "placeholder",
        "missing_metadata",
        "unsafe_for_results_section",
        "needs_human_validation",
        "unknown_needs_review",
    }
)

PLACEHOLDER_TEXT_MARKERS = (
    "placeholder",
    "not yet run",
    "not yet run.",
    "blocked",
    "planned",
    "engineering-only",
    "engineering only",
    "no final scientific",
    "no final scientific results",
    "not complete",
    "not yet complete",
    "not scientific evidence",
    "illustrative scaffold",
    "mock/stub",
    "mock diagnostic",
    "preliminary only",
    "human validation not complete",
    "human validation is not yet complete",
    "ablation results not yet run",
)

PAPER_ASSET_PATH_HINTS = (
    "tables/table",
    "figures/figure",
    "paper/latexpaper/generated",
    "paper/latexpaper/sections",
)

WATERMARK_ENGINEERING_ONLY = "ENGINEERING ONLY — NOT SCIENTIFIC EVIDENCE — NOT SAFE FOR MAIN RESULTS"
WATERMARK_INCOMPLETE = "INCOMPLETE — NOT SCIENTIFIC EVIDENCE"
WATERMARK_MOCK_STUB = "MOCK/STUB ONLY — NOT SCIENTIFIC EVIDENCE"
WATERMARK_PLACEHOLDER = "PLACEHOLDER — NOT SCIENTIFIC EVIDENCE"

TRUE_VALUES = frozenset({"true", "1", "yes"})
FALSE_VALUES = frozenset({"false", "0", "no", ""})
NON_PROVIDER_TYPES = frozenset(
    {
        "",
        "unknown",
        "none",
        "null",
        "default",
        "local",
        "local_stub",
        "stub",
        "mock",
        "oracle",
        "synthetic",
        "fake",
        "dry_run",
    }
)
LOCAL_OR_ENGINEERING_PROVIDER_MARKERS = frozenset(
    {"local", "stub", "mock", "oracle", "synthetic", "fake", "dry"}
)


def load_run_index_entries(
    repo_root: Path,
    *,
    results_root: str | Path = "results",
) -> list[dict[str, Any]]:
    root = Path(results_root)
    if not root.is_absolute():
        root = repo_root / root
    entries: list[dict[str, Any]] = []
    jsonl_path = root / "RUN_INDEX.jsonl"
    json_path = root / "run_index.json"
    if jsonl_path.exists():
        for line in jsonl_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                entries.append(json.loads(line))
    elif json_path.exists():
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        entries = list(payload.get("runs", []))
    return entries


def scan_live_run_dirs(
    repo_root: Path,
    *,
    results_root: str | Path = "results",
) -> list[str]:
    """Return run_id names present in the live results tree (inventory only).

    Mirrors the directory-selection criteria of
    :func:`causal_agent_bench.runners.index_runs.index_runs` so staleness is
    measured against exactly what an index refresh would persist. This is a
    read-only scan: it never classifies, mutates ``results/``, or marks any run
    eligible.
    """
    root = Path(results_root)
    if not root.is_absolute():
        root = repo_root / root
    if not root.exists():
        return []
    run_ids: list[str] = []
    for path in sorted(root.iterdir()):
        if not path.is_dir() or path.name in {"cache", "dry_runs"}:
            continue
        if not (path / "run_metadata.json").exists() and not (path / "metadata.json").exists():
            continue
        run_ids.append(path.name)
    return run_ids


def compute_run_index_freshness(
    repo_root: Path,
    *,
    results_root: str | Path = "results",
    max_listed: int = 25,
) -> dict[str, Any]:
    """Compare the persisted run index against the live results tree.

    Detects when ``RUN_INDEX.jsonl`` undercounts (runs on disk but not indexed)
    or overcounts (indexed runs whose directory is gone). Pure inventory
    comparison: it does NOT regenerate the index, mutate ``results/``, or change
    any run's eligibility. Refreshing the index is a separate, explicit
    ``index-runs`` operation and never alters evidence state because run
    classification gates run independently of index membership.
    """
    indexed_entries = load_run_index_entries(repo_root, results_root=results_root)
    indexed_ids = [
        str(entry.get("run_id") or Path(str(entry.get("path") or "")).name)
        for entry in indexed_entries
    ]
    indexed_set = {rid for rid in indexed_ids if rid}
    live_ids = scan_live_run_dirs(repo_root, results_root=results_root)
    live_set = set(live_ids)

    unindexed = sorted(live_set - indexed_set)  # on disk, missing from index (undercount)
    orphaned = sorted(indexed_set - live_set)  # in index, no live directory (overcount/moved)

    root = Path(results_root)
    if not root.is_absolute():
        root = repo_root / root
    index_present = (root / "RUN_INDEX.jsonl").exists() or (root / "run_index.json").exists()

    listed_unindexed = unindexed[:max_listed]
    # Defensive safety probe: read-only classify the (capped) un-indexed runs so we
    # can prove an index refresh is inventory-only. If any would be paper-eligible,
    # that is the dangerous case (a real run invisible to the reviewed inventory).
    eligible_unindexed: list[str] = []
    for run_id in listed_unindexed:
        classified = classify_run_entry(
            {"run_id": run_id, "path": f"{results_root}/{run_id}"}, repo_root
        )
        if classified.get("paper_eligible"):
            eligible_unindexed.append(run_id)

    return {
        "results_root": str(results_root),
        "index_present": index_present,
        "indexed_run_count": len(indexed_set),
        "live_run_count": len(live_set),
        "unindexed_run_count": len(unindexed),
        "orphaned_index_run_count": len(orphaned),
        "unindexed_run_ids": listed_unindexed,
        "orphaned_index_run_ids": orphaned[:max_listed],
        "unindexed_run_ids_truncated": max(0, len(unindexed) - max_listed),
        "orphaned_index_run_ids_truncated": max(0, len(orphaned) - max_listed),
        "unindexed_paper_eligible_count": len(eligible_unindexed),
        "unindexed_paper_eligible_run_ids": eligible_unindexed,
        "index_stale": bool(unindexed or orphaned),
        "refresh_command": "python3 -m causal_agent_bench index-runs",
        "note": (
            "Inventory-only comparison. Refreshing the index never changes run "
            "eligibility or evidence state — classification gates run independently."
        ),
    }


def _normalize_scope(value: str | None) -> str:
    return str(value or "").strip().lower()


def strict_bool(value: Any) -> bool:
    """Parse booleans conservatively for evidence gates.

    Unknown strings are deliberately false so a typo cannot promote evidence.
    """

    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, int | float):
        if value == 1:
            return True
        if value == 0:
            return False
        return False
    normalized = str(value).strip().lower()
    if normalized in TRUE_VALUES:
        return True
    if normalized in FALSE_VALUES:
        return False
    return False


def _unknown_bool_string(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    normalized = value.strip().lower()
    return normalized not in TRUE_VALUES and normalized not in FALSE_VALUES


def _has_marker(haystack: str, markers: frozenset[str] | tuple[str, ...]) -> bool:
    lower = haystack.lower()
    return any(marker in lower for marker in markers)


def _combined_scope(evidence_level: str, metadata: dict[str, Any], entry: dict[str, Any]) -> str:
    parts = [
        evidence_level,
        _normalize_scope(entry.get("evidence_scope")),
        _normalize_scope(metadata.get("evidence_scope")),
        _normalize_scope(metadata.get("scientific_evidence_level")),
        _normalize_scope(metadata.get("deployment_class")),
    ]
    return " ".join(part for part in dict.fromkeys(parts) if part)


def _provider_type_from(entry: dict[str, Any], metadata: dict[str, Any]) -> str:
    provider_type = entry.get("provider_type") or metadata.get("provider_type")
    if provider_type:
        return str(provider_type).strip().lower()
    providers = metadata.get("providers") or []
    if isinstance(providers, list) and len(providers) == 1:
        return str(providers[0]).strip().lower()
    return "unknown"


def is_real_provider_type(provider_type: str | None) -> bool:
    provider = str(provider_type or "").strip().lower()
    if provider in NON_PROVIDER_TYPES:
        return False
    return not any(marker in provider for marker in LOCAL_OR_ENGINEERING_PROVIDER_MARKERS)


def _trajectory_counts_consistent(
    completed_trajectories: Any,
    expected_trajectories: Any,
) -> bool:
    if completed_trajectories is None or expected_trajectories is None:
        return True
    try:
        completed = int(completed_trajectories)
        expected = int(expected_trajectories)
    except (TypeError, ValueError):
        return False
    if expected < 0 or completed < 0:
        return False
    return completed >= expected


def _oracle_only(agents: list[Any], metadata: dict[str, Any]) -> bool:
    agent_names = [str(agent).lower() for agent in agents]
    if agent_names and all("oracle" in agent for agent in agent_names):
        return True
    agent_runs = metadata.get("agent_runs") or []
    run_agents = [
        str(run.get("agent") or run.get("name") or "").lower()
        for run in agent_runs
        if isinstance(run, dict)
    ]
    return bool(run_agents) and all("oracle" in agent for agent in run_agents)


def _provider_backed_scientific_candidate(
    *,
    metadata: dict[str, Any],
    run_status: str,
    completion_state: str,
    scientific_evidence: bool,
    provider_type: str,
    combined_scope: str,
    agents: list[Any],
    completed_trajectories: Any,
    expected_trajectories: Any,
    run_path: Path,
) -> bool:
    if not metadata:
        return False
    if run_status != "complete" or completion_state != "complete":
        return False
    if (run_path / "INCOMPLETE_RUN.json").exists():
        return False
    if not scientific_evidence:
        return False
    if not is_real_provider_type(provider_type):
        return False
    if _has_marker(combined_scope, MOCK_STUB_DRY_EVIDENCE_MARKERS):
        return False
    if combined_scope in NON_SCIENTIFIC_EVIDENCE_SCOPES:
        return False
    if strict_bool(metadata.get("not_real_llm_behavior")):
        return False
    if _normalize_scope(metadata.get("deployment_class")) == "mock_diagnostic_only":
        return False
    if _oracle_only(agents, metadata):
        return False
    return _trajectory_counts_consistent(completed_trajectories, expected_trajectories)


def classify_run_entry(entry: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    run_path = Path(str(entry.get("path") or entry.get("run_dir") or ""))
    if not run_path.is_absolute():
        run_path = repo_root / run_path
    metadata = load_run_metadata(run_path) if run_path.exists() else {}
    state = infer_completion_state(run_path) if run_path.exists() else {}

    run_status = str(entry.get("status") or state.get("run_status") or "unknown")
    completion_state = str(entry.get("completion_state") or state.get("completion_state") or "incomplete")
    evidence_level = _normalize_scope(
        entry.get("evidence_level") or metadata.get("scientific_evidence_level") or metadata.get("evidence_scope")
    )
    provider_type = _provider_type_from(entry, metadata)
    scientific_evidence_raw = (
        metadata.get("scientific_evidence", entry.get("scientific_evidence", False))
        if metadata
        else entry.get("scientific_evidence", False)
    )
    scientific_evidence = strict_bool(scientific_evidence_raw)
    agents = entry.get("agents") or metadata.get("agents") or []
    run_name = str(entry.get("run_name") or entry.get("config") or metadata.get("run_name") or run_path.name)
    config_hash = metadata.get("config_hash")
    config_name = entry.get("config") or metadata.get("run_name")
    completed_trajectories = entry.get("completed_trajectories", state.get("completed_trajectories"))
    expected_trajectories = entry.get("expected_trajectories", state.get("expected_trajectories"))
    combined_scope = _combined_scope(evidence_level, metadata, entry)
    parse_warnings: list[str] = []
    if _unknown_bool_string(scientific_evidence_raw):
        parse_warnings.append(
            f"scientific_evidence has unknown boolean value {scientific_evidence_raw!r}; treated as false"
        )

    classification = _run_classification(
        run_status=run_status,
        completion_state=completion_state,
        evidence_level=evidence_level,
        combined_scope=combined_scope,
        scientific_evidence=scientific_evidence,
        run_name=run_name,
        agents=agents,
        metadata=metadata,
        provider_type=provider_type,
        completed_trajectories=completed_trajectories,
        expected_trajectories=expected_trajectories,
        run_path=run_path,
    )

    paper_eligible, eligibility_reason = _paper_eligibility(
        classification=classification,
        scientific_evidence=scientific_evidence,
        completion_state=completion_state,
        evidence_level=evidence_level,
        combined_scope=combined_scope,
        metadata=metadata,
        run_path=run_path,
        provider_type=provider_type,
    )

    return {
        "run_id": entry.get("run_id") or run_path.name,
        "run_path": str(run_path),
        "status": run_status,
        "completion_state": completion_state,
        "completed_trajectories": completed_trajectories,
        "expected_trajectories": expected_trajectories,
        "provider_type": provider_type,
        "evidence_level": evidence_level or "unknown",
        "evidence_scope": _normalize_scope(metadata.get("evidence_scope") or entry.get("evidence_scope")) or "unknown",
        "scientific_evidence": scientific_evidence,
        "config_name": config_name,
        "config_hash": config_hash,
        "classification": classification,
        "paper_eligible": paper_eligible,
        "paper_eligibility_reason": eligibility_reason,
        "missing_metadata": _missing_metadata_fields(metadata, run_path),
        "parse_warnings": parse_warnings,
    }


def _run_classification(
    *,
    run_status: str,
    completion_state: str,
    evidence_level: str,
    combined_scope: str,
    scientific_evidence: bool,
    run_name: str,
    agents: list[Any],
    metadata: dict[str, Any],
    provider_type: str,
    completed_trajectories: Any,
    expected_trajectories: Any,
    run_path: Path,
) -> str:
    scope = combined_scope or evidence_level or _normalize_scope(metadata.get("evidence_scope"))
    agent_names = {str(a) for a in agents}
    name_lower = run_name.lower()

    if run_status in {"interrupted"} or (run_status == "incomplete" and completion_state != "complete"):
        return "interrupted" if run_status == "interrupted" else "incomplete"
    if run_status == "dry_run":
        return "mock_diagnostic"
    if (
        "mock_diagnostic_only" in scope
        or "mock_diagnostic" in scope
        or strict_bool(metadata.get("not_real_llm_behavior"))
        or "mock_behavior" in " ".join(agent_names).lower()
    ):
        return "mock_diagnostic"
    if scope in NON_SCIENTIFIC_EVIDENCE_SCOPES or _has_marker(scope, MOCK_STUB_DRY_EVIDENCE_MARKERS):
        if "stub" in scope or "stub" in name_lower:
            return "stub_engineering"
        return "mock_diagnostic" if "mock" in scope else "stub_engineering"
    if "stub" in name_lower or "smoke" in name_lower or scope in {"stub_engineering", "pilot_stub_engineering_only"}:
        return "stub_engineering"
    if scope in {"local_model_preliminary", "local_open_weight_unvalidated", "preliminary_or_engineering"}:
        return "local_preliminary"
    if completion_state != "complete":
        return "incomplete"
    provider_candidate = _provider_backed_scientific_candidate(
        metadata=metadata,
        run_status=run_status,
        completion_state=completion_state,
        scientific_evidence=scientific_evidence,
        provider_type=provider_type,
        combined_scope=scope,
        agents=agents,
        completed_trajectories=completed_trajectories,
        expected_trajectories=expected_trajectories,
        run_path=run_path,
    )
    if scope in {"main_experiment", "commercial_api_experiment_unvalidated"} or "main" in name_lower:
        if provider_candidate:
            return "main_benchmark"
        return "unknown_needs_review"
    if "pilot" in scope or "pilot" in name_lower or is_real_provider_type(provider_type):
        if provider_candidate:
            return "provider_backed_pilot"
        return "unknown_needs_review"
    if scientific_evidence and completion_state == "complete":
        return "complete_scientific_evidence"
    if completion_state == "complete":
        return "complete_engineering_only"
    return "unknown_needs_review"


def _paper_eligibility(
    *,
    classification: str,
    scientific_evidence: bool,
    completion_state: str,
    evidence_level: str,
    combined_scope: str,
    metadata: dict[str, Any],
    run_path: Path,
    provider_type: str,
) -> tuple[bool, str]:
    if not run_path.exists():
        return False, "run directory missing"
    if not metadata:
        return False, "missing run metadata"
    missing = _missing_metadata_fields(metadata, run_path)
    if missing:
        return False, "missing metadata fields: " + ", ".join(missing)
    if classification in {
        "incomplete",
        "interrupted",
        "mock_diagnostic",
        "stub_engineering",
        "local_preliminary",
        "unknown_needs_review",
    }:
        return False, f"classification={classification}"
    if completion_state != "complete":
        return False, "run not complete"
    if not scientific_evidence:
        return False, "scientific_evidence=false"
    if _has_marker(combined_scope or evidence_level, MOCK_STUB_DRY_EVIDENCE_MARKERS):
        return False, f"non-scientific evidence_level={combined_scope or evidence_level}"
    if (run_path / "INCOMPLETE_RUN.json").exists():
        return False, "INCOMPLETE_RUN.json present"
    if strict_bool(metadata.get("not_real_llm_behavior")) or metadata.get("deployment_class") == "mock_diagnostic_only":
        return False, "mock diagnostic metadata"
    agents = metadata.get("agents") or []
    if _oracle_only(agents, metadata):
        return False, "oracle-only run"
    if not is_real_provider_type(provider_type) and classification in {"provider_backed_pilot", "main_benchmark"}:
        return False, f"provider_type={provider_type} is not provider-backed evidence"
    return True, "complete verified non-mock non-stub evidence (review provider validation separately)"


def _missing_metadata_fields(metadata: dict[str, Any], run_path: Path) -> list[str]:
    missing: list[str] = []
    if not run_path.exists():
        missing.append("run_directory")
        return missing
    if not metadata:
        missing.append("run_metadata.json")
        return missing
    for field in ("config_hash", "run_name", "evidence_scope", "provider_type"):
        if not metadata.get(field):
            missing.append(field)
    return missing


def read_meta_sidecar(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def asset_has_placeholder_content(path: Path) -> bool:
    if not path.exists() or path.suffix not in {".md", ".tex", ".csv", ".txt"}:
        return False
    try:
        text = path.read_text(encoding="utf-8").lower()
    except OSError:
        return False
    return any(marker in text for marker in PLACEHOLDER_TEXT_MARKERS)


def write_dual_report(
    *,
    stem: str,
    payload: dict[str, Any],
    markdown: str,
    output_dir: Path,
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"{stem}.json"
    md_path = output_dir / f"{stem}.md"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(markdown, encoding="utf-8")
    return md_path, json_path


def section_markdown(title: str, lines: list[str]) -> str:
    body = "\n".join(lines) if lines else "- (none)"
    return f"## {title}\n\n{body}\n"
