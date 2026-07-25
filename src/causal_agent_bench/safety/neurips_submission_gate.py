"""Conservative NeurIPS submission readiness gate (static, no-run)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from causal_agent_bench.claim_ledger import load_ledger
from causal_agent_bench.safety.common import write_dual_report

GATE_IDS = (
    "dataset_leakage_clear",
    "main_dataset_ready",
    "provider_runs_complete",
    "paper_assets_eligible",
    "human_validation_complete",
    "claim_ledger_supported",
    "release_artifact_packaged",
    "reproducibility_passed",
    "paper_no_overclaim_check",
    "advisor_coauthor_signoff",
)


def build_neurips_submission_gate(
    repo_root: str | Path,
    *,
    reports_dir: str | Path = "reports",
    output_dir: str | Path = "reports/neurips_submission_gate",
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    reports = Path(reports_dir)
    if not reports.is_absolute():
        reports = root / reports
    out = Path(output_dir)
    if not out.is_absolute():
        out = root / out
    state = _evidence_state(root, reports)
    gates = [_evaluate_gate(gate_id, state) for gate_id in GATE_IDS]
    passed = sum(1 for gate in gates if gate["status"] == "pass")
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": (
            "Static NeurIPS submission gate only. Does not promote claims or imply paper readiness. "
            "Verdict remains NOT READY until all gates pass with eligible evidence."
        ),
        "verdict": "NOT_READY" if passed < len(gates) else "READY_PENDING_HUMAN_REVIEW",
        "submission_ready": False,
        "neurips_ready": False,
        "paper_ready": False,
        "gates_passed": passed,
        "gates_total": len(gates),
        "evidence_state": state,
        "gates": gates,
        "blockers": [gate for gate in gates if gate["status"] != "pass"],
    }
    md = submission_gate_markdown(payload)
    md_path, json_path = write_dual_report(
        stem="neurips_submission_gate",
        payload=payload,
        markdown=md,
        output_dir=out,
    )
    payload["report_paths"] = {"markdown": str(md_path), "json": str(json_path)}
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def _evidence_state(root: Path, reports: Path) -> dict[str, Any]:
    ledger = load_ledger(root / "docs/claim_ledger.json")
    statuses = {str(c["claim_id"]): str(c.get("status", "planned")) for c in ledger.get("claims", [])}
    run_health = _read_json(reports, "run_health_report.json") or {}
    assets = _read_json(reports, "paper_asset_eligibility.json") or {}
    leakage = _read_json(reports, "static_leakage/static_leakage_report.json") or _read_json(
        reports, "static_leakage_report.json"
    ) or {}
    return {
        "paper_eligible_runs": int((run_health.get("summary") or {}).get("paper_eligible_count") or 0),
        "eligible_empirical_assets": int(assets.get("eligible_count") or 0),
        "leakage_blocker_clusters": int((leakage.get("summary") or {}).get("blocker_cluster_count") or 0),
        "claims": statuses,
        "human_annotations_exist": _human_annotations_exist(root),
        "main_frozen": (root / "data/frozen/main_v0.1").exists() or (root / "data/frozen/main_200").exists(),
        "approved_provider_config": any(root.glob("configs/*_APPROVED.yaml")),
        "provider_gate": "template_safe_but_not_runnable",
    }


def _evaluate_gate(gate_id: str, state: dict[str, Any]) -> dict[str, Any]:
    checks: dict[str, tuple[bool, str]] = {
        "dataset_leakage_clear": (
            state["leakage_blocker_clusters"] == 0,
            f"blocker_cluster_count={state['leakage_blocker_clusters']}",
        ),
        "main_dataset_ready": (
            state["main_frozen"],
            "main_200/main_v0_1_500 not frozen",
        ),
        "provider_runs_complete": (
            state["paper_eligible_runs"] > 0,
            f"paper_eligible_runs={state['paper_eligible_runs']}",
        ),
        "paper_assets_eligible": (
            state["paper_eligible_runs"] > 0 and state["eligible_empirical_assets"] > 0,
            (
                f"eligible_empirical_assets={state['eligible_empirical_assets']}; "
                f"paper_eligible_runs={state['paper_eligible_runs']}"
            ),
        ),
        "human_validation_complete": (
            state["human_annotations_exist"],
            "no completed human-validation annotations",
        ),
        "claim_ledger_supported": (
            all(state["claims"].get(f"C{i}") == "supported" for i in range(1, 9))
            and state["claims"].get("C10") == "supported",
            "C1-C8/C10 not supported in claim ledger",
        ),
        "release_artifact_packaged": (
            False,
            "public v1.0 release bundle not shipped",
        ),
        "reproducibility_passed": (
            state["claims"].get("C9") == "engineering_only",
            "C9 engineering reproducibility only; provider repro not demonstrated",
        ),
        "paper_no_overclaim_check": (
            state["paper_eligible_runs"] == 0,
            "overclaim risk if empirical tables filled without eligible runs",
        ),
        "advisor_coauthor_signoff": (
            state["approved_provider_config"] and state["paper_eligible_runs"] > 0,
            "signed approval + completed runs required",
        ),
    }
    ok, detail = checks[gate_id]
    return {
        "gate_id": gate_id,
        "status": "pass" if ok else "fail",
        "detail": detail,
        "required_for_submission": True,
    }


def submission_gate_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# NeurIPS Submission Gate",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        payload["scope"],
        "",
        f"**Verdict:** `{payload['verdict']}`",
        f"**Gates passed:** {payload['gates_passed']}/{payload['gates_total']}",
        "",
        "## Gates",
        "",
        "| Gate | Status | Detail |",
        "|---|---|---|",
    ]
    for gate in payload["gates"]:
        lines.append(f"| {gate['gate_id']} | `{gate['status']}` | {gate['detail']} |")
    lines.extend(
        [
            "",
            "## Evidence boundary",
            "",
            "- This gate does **not** certify NeurIPS acceptance.",
            "- `NOT_READY` is the expected verdict until Stage F–H complete.",
            "- Tiny pilot (≤5 trajectories) cannot satisfy this gate.",
            "",
        ]
    )
    return "\n".join(lines)


def _human_annotations_exist(root: Path) -> bool:
    hv = root / "data/human_validation"
    if not hv.exists():
        return False
    return any(p.name.startswith("completed") for p in hv.rglob("*") if p.is_file())


def _read_json(reports: Path, filename: str) -> dict[str, Any] | None:
    for path in (reports / filename,):
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                return None
            return data if isinstance(data, dict) else None
    for path in sorted(reports.glob(f"**/{filename}")) if reports.exists() else []:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
        return data if isinstance(data, dict) else None
    return None
