#!/usr/bin/env python3
"""Standalone hostile audit of the committed-review-evidence chain.

Provider-free and self-contained: it builds isolated synthetic workspaces under a
temporary directory, runs the legitimate workflow through the same public
coordinator APIs a real coordinator uses, then executes the full hostile mutation
matrix against them and records which gate refused each attack.

It imports no test-only helper and monkeypatches nothing.  A gate that accepts a
mutated chain makes this exit nonzero.

Nothing private is read or printed.  Every workspace it touches is synthetic,
sealed by the public fixture authority, and stamped
``SYNTHETIC_TEST_FIXTURE_NOT_HUMAN_EVIDENCE``.

    python scripts/audit_final_review_integrity.py
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from causal_agent_bench.review_ready_v2.commitment_integrity import (
    STAGE1_COMMITMENT_SCHEMA_VERSION,
    STAGE1_SNAPSHOT_SCHEMA_VERSION,
    STAGE2_SNAPSHOT_SCHEMA_VERSION,
)
from causal_agent_bench.review_ready_v2.fixture_e2e import FixtureWorkflow
from causal_agent_bench.review_ready_v2.hostile_integrity import (
    attack_matrix,
    run_attack_matrix,
)
from causal_agent_bench.review_ready_v2.workflow import (
    WORKFLOW_SCHEMA_VERSION,
    verify_committed_stage1_snapshot,
    verify_committed_stage2_snapshot,
)

OUT = ROOT / "reports/final_integrity_closure"


def _legitimate_baseline(root: Path) -> dict[str, Any]:
    """Prove the honest path still works before proving the hostile ones fail.

    An audit where every attack is refused because the workflow refuses
    everything would be worthless, so the baseline is part of the result.
    """

    driver = FixtureWorkflow.create(root).advance_to("settle")
    report = driver.finish()
    stage1 = verify_committed_stage1_snapshot(driver.workspace)
    stage2 = verify_committed_stage2_snapshot(driver.workspace)
    return {
        "legitimate_workflow_completes": True,
        "c10_mechanics_status": report["mechanics_status"],
        "c10_status": report["status"],
        "c10_counts_as_genuine_evidence": report["counts_as_genuine_evidence"],
        "c10_failed_checks": report["failed_checks"],
        "stage1_snapshot_checks_all_pass": all(stage1["checks"].values()),
        "stage2_snapshot_checks_all_pass": all(stage2["checks"].values()),
        "stage1_snapshot_manifest_sha256": stage1["stage1_snapshot_manifest_sha256"],
        "stage2_snapshot_manifest_sha256": stage2["stage2_snapshot_manifest_sha256"],
        "baseline_passed": report["mechanics_status"] == "C10_MECHANICS_PASS"
        and report["status"] == "C10_PENDING_GENUINE_REVIEW"
        and report["counts_as_genuine_evidence"] is False,
    }


def _markdown(payload: dict[str, Any]) -> str:
    baseline = payload["legitimate_baseline"]
    lines = [
        "# CAB hostile integrity audit",
        "",
        f"Generated at `{payload['generated_at']}`.  Provider-free, fixture-only.",
        "",
        "Every workspace below is synthetic and sealed by the public fixture",
        "authority.  No private material is read, and no result here is evidence of",
        "anything except that the gates refuse what they are supposed to refuse.",
        "",
        "## Result",
        "",
        f"- attacks attempted: **{payload['attack_count']}**",
        f"- rejected at or before the consuming gate: **{payload['rejected_count']}**",
        f"- falsely accepted: **{payload['falsely_accepted_count']}**",
        f"- status: **{payload['status']}**",
        "",
        "## Legitimate baseline",
        "",
        "| check | value |",
        "| --- | --- |",
        f"| workflow completes | {baseline['legitimate_workflow_completes']} |",
        f"| C10 mechanics | `{baseline['c10_mechanics_status']}` |",
        f"| C10 status | `{baseline['c10_status']}` |",
        f"| counts as genuine evidence | {baseline['c10_counts_as_genuine_evidence']} |",
        f"| Stage-1 snapshot checks | {baseline['stage1_snapshot_checks_all_pass']} |",
        f"| Stage-2 snapshot checks | {baseline['stage2_snapshot_checks_all_pass']} |",
        "",
        "## Schema surface under audit",
        "",
        "| schema | version |",
        "| --- | --- |",
        f"| two-stage workflow | `{payload['workflow_schema_version']}` |",
        f"| Stage-1 commitment | `{payload['stage1_commitment_schema_version']}` |",
        f"| committed Stage-1 snapshot | `{payload['stage1_snapshot_schema_version']}` |",
        f"| committed Stage-2 snapshot | `{payload['stage2_snapshot_schema_version']}` |",
        "",
        "## Attacks by receipt chain",
        "",
        "| receipt chain | attacks |",
        "| --- | --- |",
    ]
    for chain, count in payload["attacks_by_receipt_chain"].items():
        lines.append(f"| `{chain}` | {count} |")
    lines += [
        "",
        "## Every attack",
        "",
        "| attack | receipt chain | mutated after | expected gate | actual gate | scope | result |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in payload["results"]:
        lines.append(
            f"| `{row['attack']}` | `{row['receipt_chain']}` | `{row['mutated_after_stage']}` | "
            f"`{row['expected_rejection_gate']}` | `{row['actual_rejection_gate']}` | "
            f"{row['scope']} | {'REJECTED' if row['passed'] else 'FALSELY ACCEPTED'} |"
        )
    lines += [
        "",
        "## What a rejection means",
        "",
        "Each attack mutates a sealed artifact on disk and re-seals it with a valid",
        "MAC, modelling a coordinator who holds the sealing key.  A rejection means",
        "the workflow noticed that what it committed is no longer what it is",
        "reading — not merely that a signature failed.",
        "",
        "`mutation_refused` means the workflow declined the hostile input before it",
        "could be written at all, which is the earliest possible refusal.",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir", type=Path, default=OUT, help="where to write the audit reports"
    )
    args = parser.parse_args(argv)

    with tempfile.TemporaryDirectory(prefix="cab-hostile-audit-") as scratch:
        root = Path(scratch)
        baseline = _legitimate_baseline(root / "legitimate")
        matrix = run_attack_matrix(root / "attacks", attacks=attack_matrix())

    payload: dict[str, Any] = {
        "schema_version": "cab_hostile_integrity_audit_v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "workflow_schema_version": WORKFLOW_SCHEMA_VERSION,
        "stage1_commitment_schema_version": STAGE1_COMMITMENT_SCHEMA_VERSION,
        "stage1_snapshot_schema_version": STAGE1_SNAPSHOT_SCHEMA_VERSION,
        "stage2_snapshot_schema_version": STAGE2_SNAPSHOT_SCHEMA_VERSION,
        "artifact_origin": "SYNTHETIC_TEST_FIXTURE_NOT_HUMAN_EVIDENCE",
        "counts_as_genuine_evidence": False,
        "legitimate_baseline": baseline,
        **{key: value for key, value in matrix.items() if key != "schema_version"},
    }
    payload["passed"] = bool(matrix["passed"] and baseline["baseline_passed"])
    payload["status"] = (
        "CAB_HOSTILE_INTEGRITY_AUDIT_PASSED"
        if payload["passed"]
        else "CAB_HOSTILE_INTEGRITY_AUDIT_FAILED"
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "HOSTILE_INTEGRITY_AUDIT.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n"
    )
    (args.output_dir / "HOSTILE_INTEGRITY_AUDIT.md").write_text(_markdown(payload))

    print(
        f"{payload['status']}: {payload['rejected_count']}/{payload['attack_count']} attacks "
        f"rejected, {payload['falsely_accepted_count']} falsely accepted"
    )
    for name in payload["falsely_accepted"]:
        print(f"FALSELY ACCEPTED: {name}", file=sys.stderr)
    if not baseline["baseline_passed"]:
        print("BASELINE FAILED: the legitimate fixture workflow no longer completes", file=sys.stderr)
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
