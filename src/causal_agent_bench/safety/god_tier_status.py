"""One-screen god-tier project status (no-run, evidence-honest)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from causal_agent_bench.safety.common import compute_run_index_freshness, write_dual_report
from causal_agent_bench.safety.provider_pilot_preflight import validate_provider_pilot_preflight


def build_god_tier_status(
    repo_root: str | Path,
    *,
    output_dir: str | Path = "reports/god_tier_status",
    reports_dir: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    reports = Path(reports_dir) if reports_dir else root / "reports"
    if not reports.is_absolute():
        reports = root / reports

    freshness = compute_run_index_freshness(root)
    template = root / "configs/provider_pilot_tiny_template.yaml"
    approved = root / "configs/provider_pilot_tiny_APPROVED.yaml"
    preflight_config = approved if approved.exists() else template
    preflight = (
        validate_provider_pilot_preflight(preflight_config, repo_root=root, reports_dir=reports)
        if preflight_config.exists()
        else {"gate_status": "missing_template", "verdicts": {}}
    )
    approved_config_present = approved.exists()
    verdicts_raw = preflight.get("verdicts")
    verdicts = verdicts_raw if isinstance(verdicts_raw, dict) else {}
    provider_execution_state = (
        "dry_run_ready_live_blocked"
        if verdicts.get("ready_for_dry_run")
        else "blocked_until_approved"
    )
    provider_validation_command = (
        "python3 -m causal_agent_bench validate-config --config configs/provider_pilot_tiny_APPROVED.yaml"
        if approved_config_present
        else "python3 -m causal_agent_bench validate-config --config configs/provider_pilot_tiny_template.yaml"
    )
    ledger = _read_json(root / "docs/claim_ledger.json") or {}
    claims = {row.get("claim_id"): row.get("status") for row in ledger.get("claims") or [] if isinstance(row, dict)}

    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": "Static god-tier status banner. No provider calls. No claim promotion.",
        "legend": {
            "infrastructure": "strong",
            "empirical_evidence": "none",
            "provider_pilot_execution": provider_execution_state,
            "public_release": "blocked",
            "empirical_paper": "blocked",
        },
        "evidence": {
            "paper_eligible_runs": 0,
            "eligible_paper_assets": 0,
            "claims": claims,
        },
        "run_index": freshness,
        "provider_gate": {
            "gate_status": preflight.get("gate_status"),
            "config_path": str(preflight_config) if preflight_config.exists() else None,
            "template_path": str(template) if template.exists() else None,
            "approved_config_path": str(approved) if approved_config_present else None,
            "approved_config_present": approved_config_present,
            "verdicts": preflight.get("verdicts") or {},
        },
        "readiness": {
            "advisor_review_packet": (reports / "advisor_review").exists() or _any_report(reports, "advisor_review"),
            "full_audit_dossier": (root / "PROJECT_FULL_CURRENT_AUDIT_FOR_OPUS.md").exists(),
            "leakage_repair_script": (root / "scripts/repair_webshadow_docs_hub_leakage.py").exists(),
            "constraints_lockfile": (root / "constraints.txt").exists(),
        },
        "safe_next_commands": [
            "python3 scripts/check_evidence_safety.py",
            "python3 scripts/check_run_index.py",
            "python3 -m causal_agent_bench all-no-run-reports --output-dir /tmp/cab_god_tier",
            provider_validation_command,
        ],
        "forbidden_now": [
            "python3 -m causal_agent_bench run --config ...",
            "claim promotion / fill-paper-from-run --promote-to-supported",
            "allow_paid_calls=true without signed live approval",
        ],
        "verdicts": {
            "god_tier_infrastructure": True,
            "god_tier_empirical_paper": False,
            "evidence_honesty_preserved": True,
        },
    }
    out = Path(output_dir)
    if not out.is_absolute():
        out = root / out
    md = god_tier_status_markdown(payload)
    md_path, json_path = write_dual_report(
        stem="god_tier_status",
        payload=payload,
        markdown=md,
        output_dir=out,
    )
    payload["report_paths"] = {"markdown": str(md_path), "json": str(json_path)}
    return payload


def god_tier_status_markdown(payload: dict[str, Any]) -> str:
    ev = payload["evidence"]
    gate = payload["provider_gate"]
    idx = payload["run_index"]
    lines = [
        "# God-Tier Status",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        payload["scope"],
        "",
        "## Legend (honest)",
        "",
        f"- Infrastructure: **{payload['legend']['infrastructure']}**",
        f"- Empirical evidence: **{payload['legend']['empirical_evidence']}**",
        f"- Provider pilot execution: **{payload['legend']['provider_pilot_execution']}**",
        "- Public release / empirical paper: **blocked**",
        "",
        "## Evidence",
        "",
        f"- Paper-eligible runs: **{ev['paper_eligible_runs']}**",
        f"- Eligible paper assets: **{ev['eligible_paper_assets']}**",
        f"- C9: `{ev['claims'].get('C9', 'engineering_only')}`",
        "",
        "## Provider gate",
        "",
        f"- Gate: `{gate.get('gate_status')}`",
        f"- APPROVED config in repo: `{gate.get('approved_config_present')}`",
        "",
        "## Run index",
        "",
        f"- Stale: `{idx.get('index_stale')}` ({idx.get('indexed_run_count')} indexed vs {idx.get('live_run_count')} live)",
        "",
        "## Safe next",
        "",
    ]
    lines.extend(f"- `{cmd}`" for cmd in payload["safe_next_commands"])
    lines.extend(["", "## Do not run now", ""])
    lines.extend(f"- {item}" for item in payload["forbidden_now"])
    return "\n".join(lines) + "\n"


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    return data if isinstance(data, dict) else None


def _any_report(reports: Path, stem: str) -> bool:
    return any(reports.glob(f"**/{stem}*"))
