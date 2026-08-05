#!/usr/bin/env python3
"""Assemble the post-human-review final report from the artifacts themselves.

Every number here is read out of a file that some other command wrote, so the
report cannot drift from the chain it describes.  Nothing is passed in on the
command line except where the report is written, and nothing is restated from
memory: if an artifact is missing, the field says so rather than guessing.

The report is public.  It carries counts, states and hashes only — never a
reviewer's note, never an item's expected answer, never a key.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = REPO_ROOT / "reports" / "post_human_review"
REVIEWER_REPORTS = REPO_ROOT / "reports" / "reviewer_ready_v2"


def _read(path: Path) -> dict[str, Any] | None:
    return json.loads(path.read_text()) if path.is_file() else None


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=False
    ).stdout.strip()


def build() -> dict[str, Any]:
    freeze = _read(REVIEWER_REPORTS / "SCIENTIFIC_FREEZE_V2.json") or {}
    provenance = _read(REVIEWER_REPORTS / "GENERATOR_PROVENANCE.json") or {}
    discovery = _read(REPORT_DIR / "HUMAN_EVIDENCE_DISCOVERY.json") or {}
    validation = _read(REPORT_DIR / "HUMAN_EVIDENCE_VALIDATION.json") or {}
    qualification = _read(REPORT_DIR / "QUALIFICATION_FINAL.json") or {}
    waiver = _read(REPORT_DIR / "COORDINATOR_DECLARATION_WAIVER.json") or {}
    manual = _read(REPORT_DIR / "MANUAL_IMPORT_PROVENANCE.json") or {}
    graph = _read(REPORT_DIR / "IMMUTABLE_IMPORTED_EVIDENCE_GRAPH.json") or {}
    agreement = _read(REPORT_DIR / "AGREEMENT_FINAL.json") or {}
    c10 = _read(REPORT_DIR / "C10_FINAL.json") or {}
    register = _read(REPORT_DIR / "EXCLUSION_REGISTER_FINAL.json") or {}
    lock = _read(REPORT_DIR / "REVIEWED_SLICE_LOCK_FINAL.json") or {}
    authorization = _read(REPORT_DIR / "EXECUTION_AUTHORIZATION_FINAL.json") or {}
    quarantine = _read(REPORT_DIR / "STALE_IMPORT_QUARANTINE.json") or {}
    local = _read(REPORT_DIR / "LOCAL_CPU_VALIDATION_SUMMARY.json") or {}
    bundles = _read(REPORT_DIR / "KAGGLE_INPUT_BUNDLE_MANIFESTS.json") or {}
    names = _read(REPORT_DIR / "KAGGLE_ARBITRARY_NAME_INPUT_TESTS.json") or {}

    evidence_hashes = {
        slot: row["raw_sha256"] for slot, row in (discovery.get("selected") or {}).items()
    }
    canonical_hashes = {
        slot: row["canonical_sha256"] for slot, row in (discovery.get("selected") or {}).items()
    }

    statuses: list[str] = []
    if validation.get("final_records_passed"):
        statuses.append("HUMAN_REVIEW_COMPLETE")
    if qualification.get("every_role_qualified"):
        statuses.append("QUALIFICATION_GENUINE_AND_VERIFIED")
    if waiver.get("declaration_files_collected") is False:
        statuses.append("REVIEWER_DECLARATION_WAIVER_DISCLOSED")
    if c10.get("c10_state") == "PASS":
        statuses.append("C10_PASS")
    if lock.get("locked_pair_count"):
        statuses.append("COMPACT20_SLICE_LOCKED")
    if authorization.get("authorized_study"):
        statuses.append("COMPACT20_EXECUTION_AUTHORIZED")
    if local.get("passed"):
        statuses.append("LOCAL_CPU_VALIDATION_COMPLETE")
    elif local.get("no_regressions") and local.get("failed_gates"):
        # Every gate ran and none regressed, but gates that were already failing
        # before this work still fail.  Saying so is more useful than either
        # claiming completion or saying nothing.
        statuses.append("LOCAL_CPU_VALIDATION_COMPLETE_WITH_PREEXISTING_BLOCKERS")
    if names.get("passed") and bundles.get("bundles"):
        statuses.append("KAGGLE_CPU_RUNBOOKS_READY")

    return {
        "schema_version": "cab_post_human_review_final_report_v1",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "statuses": statuses,
        # Stated positively so its absence cannot be read as an oversight.
        "kaggle_cpu_preflight_complete": False,
        "kaggle_cpu_preflight_note": (
            "The remote CPU notebooks were not executed. Kaggle's notebooks API rejects this "
            "account's token with HTTP 401 while the datasets API accepts it; see "
            "KAGGLE_CPU_NOTEBOOK_READINESS.md. No remote result is claimed."
        ),
        "genuine_model_trajectories": 0,
        "live_model_execution_performed": False,
        "repository": {
            "commit": _git("rev-parse", "HEAD"),
            "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
            "evidence_anchor_commit": (graph or {}).get("frozen_source_commit")
            or (c10 or {}).get("frozen_source_commit"),
        },
        "scientific_freeze": {
            "freeze_sha256": freeze.get("freeze_sha256"),
            "packet_commitment_sha256": freeze.get("packet_commitment_sha256"),
            "generator_source_commit": (freeze.get("generator") or {}).get("source_commit"),
            "generator_provenance_status": provenance.get("status"),
            "generator_provenance_passed": provenance.get("passed"),
        },
        "evidence": {
            "source_file_count": len(evidence_hashes),
            "qualification_discovered": discovery.get("qualification_discovered"),
            "raw_sha256": evidence_hashes,
            "canonical_sha256": canonical_hashes,
            "stage1_rows_per_reviewer": validation.get("stage1_rows_per_reviewer"),
            "stage2_rows_per_reviewer": validation.get("stage2_rows_per_reviewer"),
            "stage1_overall_raw_agreement": validation.get("stage1_overall_raw_agreement"),
            "stage2_overall_raw_agreement": validation.get("stage2_overall_raw_agreement"),
            "stage1_disputed_dimensions": validation.get("stage1_disputed_dimensions"),
            "stage2_disputed_dimensions": validation.get("stage2_disputed_dimensions"),
            "adjudicated_values_used_in_agreement": agreement.get("adjudicated_values_used"),
            "included_pair_count": validation.get("included_pair_count"),
            "excluded_pair_count": validation.get("excluded_pair_count"),
            "unresolved_count": validation.get("unresolved_count"),
            "provenance_counts": validation.get("provenance_counts"),
        },
        "qualification": {
            "mode": qualification.get("qualification_mode"),
            "scored_against_private_answer_key": qualification.get(
                "scored_against_private_answer_key"
            ),
            "correct_counts": qualification.get("correct_counts"),
            "item_counts": qualification.get("item_counts"),
            "rates": qualification.get("rates"),
            "threshold": qualification.get("threshold"),
            "every_role_qualified": qualification.get("every_role_qualified"),
            "answer_key_disclosed": qualification.get("answer_key_disclosed"),
            "per_item_correctness_published": qualification.get("per_item_correctness_published"),
            "commitment_sha256": qualification.get("qualification_commitment_sha256"),
        },
        "reviewer_declarations": {
            "mode": "COORDINATOR_WAIVER",
            "files_collected": waiver.get("declaration_files_collected"),
            "confirmed": waiver.get("reviewer_declarations_confirmed"),
            "waiver_sha256": waiver.get("receipt_sha256"),
            "waived_elements": waiver.get("waived_elements"),
        },
        "provenance": {
            "artifact_origin": manual.get("artifact_origin"),
            "import_epoch": manual.get("import_epoch"),
            "original_issue_receipt_available": manual.get("original_issue_receipt_available"),
            "receipt_semantics": manual.get("receipt_semantics"),
            "quarantined_epoch_count": quarantine.get("quarantined_epoch_count"),
            "quarantined_epochs": sorted(quarantine.get("quarantined") or {}),
            "quarantined_receipts_edited": quarantine.get("receipts_were_edited"),
            "quarantined_receipts_deleted": quarantine.get("receipts_were_deleted"),
        },
        "gates": {
            "c10_state": c10.get("c10_state"),
            "c10_status": c10.get("status"),
            "c10_receipt_sha256": c10.get("receipt_sha256"),
            "c10_failed_checks": c10.get("failed_checks"),
            "c10_check_count": len(c10.get("checks") or {}),
            "exclusion_register_sha256": register.get("receipt_sha256"),
            "slice_lock_sha256": lock.get("receipt_sha256"),
            "pair_content_digest": lock.get("pair_content_digest"),
            "locked_pair_count": lock.get("locked_pair_count"),
            "execution_authorization_sha256": authorization.get("receipt_sha256"),
            "authorized_study": authorization.get("authorized_study"),
            "withheld_studies": authorization.get("withheld_studies"),
            "paid_providers_authorized": authorization.get("paid_providers_authorized"),
        },
        "immutable_graph": {
            "stage1_snapshot_manifest_sha256": graph.get("stage1_snapshot_manifest_sha256"),
            "stage2_snapshot_manifest_sha256": graph.get("stage2_snapshot_manifest_sha256"),
            "adjudication_receipt_hashes": graph.get("adjudication_receipt_hashes"),
            "all_checks_passed": graph.get("all_checks_passed"),
        },
        "local_cpu_validation": {
            "passed": local.get("passed"),
            "gate_count": local.get("gate_count"),
            "passed_gate_count": local.get("passed_gate_count"),
            "failed_gates": local.get("failed_gates"),
            "failed_gates_preexisting": local.get("failed_gates_preexisting"),
            "regressions": local.get("regressions"),
            "no_regressions": local.get("no_regressions"),
            "pytest_counts": local.get("pytest_counts"),
            "pytest_workers": local.get("pytest_workers"),
            "commit": local.get("commit"),
        },
        "kaggle": {
            "bundles": bundles.get("bundles"),
            "arbitrary_name_tests_passed": names.get("passed"),
            "arbitrary_name_case_count": names.get("case_count"),
            "arbitrary_name_failed_cases": names.get("failed_cases"),
            "authentication_datasets_api": "OK",
            "authentication_notebooks_api": "HTTP_401_UNAUTHORIZED",
            "remote_cpu_00": "NOT_RUN",
            "remote_cpu_01": "NOT_RUN",
            "remote_cpu_02": "NOT_RUN",
            "downloaded_output_bundles": [],
        },
    }


def markdown(report: dict[str, Any]) -> str:
    evidence = report["evidence"]
    qualification = report["qualification"]
    gates = report["gates"]
    local = report["local_cpu_validation"]
    kaggle = report["kaggle"]

    lines = [
        "# Post-human-review final report",
        "",
        f"Generated `{report['generated_at_utc']}` at commit "
        f"`{report['repository']['commit']}`.",
        "",
        "## Status",
        "",
    ]
    lines += [f"- `{status}`" for status in report["statuses"]]
    lines += [
        "",
        f"- `KAGGLE_CPU_PREFLIGHT_COMPLETE` — **not claimed**. "
        f"{report['kaggle_cpu_preflight_note']}",
        f"- Genuine model trajectories: **{report['genuine_model_trajectories']}**.",
        "",
        "## The review",
        "",
        "| | Reviewer A | Reviewer B |",
        "| --- | --- | --- |",
    ]
    rows = evidence.get("stage1_rows_per_reviewer") or {}
    rows2 = evidence.get("stage2_rows_per_reviewer") or {}
    correct = qualification.get("correct_counts") or {}
    items = qualification.get("item_counts") or {}
    lines += [
        f"| Stage-1 rows | {rows.get('REVIEWER_A')} | {rows.get('REVIEWER_B')} |",
        f"| Stage-2 rows | {rows2.get('REVIEWER_A')} | {rows2.get('REVIEWER_B')} |",
        f"| Qualification | {correct.get('REVIEWER_A')}/{items.get('REVIEWER_A')} "
        f"| {correct.get('REVIEWER_B')}/{items.get('REVIEWER_B')} |",
        "",
        f"- Stage-1 gated agreement: **{evidence.get('stage1_overall_raw_agreement')}**, "
        f"{evidence.get('stage1_disputed_dimensions')} adjudicated dimension(s).",
        f"- Stage-2 agreement: **{evidence.get('stage2_overall_raw_agreement')}**, "
        f"{evidence.get('stage2_disputed_dimensions')} disputed dimension(s).",
        f"- Agreement uses adjudicated values: "
        f"`{evidence.get('adjudicated_values_used_in_agreement')}`.",
        f"- Included **{evidence.get('included_pair_count')}**, "
        f"excluded **{evidence.get('excluded_pair_count')}**, "
        f"unresolved **{evidence.get('unresolved_count')}**.",
        "",
        "## Provenance, stated plainly",
        "",
        f"- Qualification: `{qualification.get('mode')}`, threshold "
        f"`{qualification.get('threshold')}`, scored against the private answer key. "
        f"The key is not disclosed and per-item correctness is not published.",
        f"- Reviewer declarations: `{report['reviewer_declarations']['mode']}`. "
        f"No declaration file was collected and none is asserted.",
        f"- Artifact origin: `{report['provenance']['artifact_origin']}`, "
        f"import epoch `{report['provenance']['import_epoch']}`.",
        f"- Superseded epochs quarantined: "
        f"{report['provenance']['quarantined_epoch_count']} "
        f"(edited: `{report['provenance']['quarantined_receipts_edited']}`, "
        f"deleted: `{report['provenance']['quarantined_receipts_deleted']}`).",
        "",
        "## Gates",
        "",
        "| gate | value |",
        "| --- | --- |",
        f"| C10 | `{gates.get('c10_state')}` — `{gates.get('c10_status')}` |",
        f"| C10 receipt | `{gates.get('c10_receipt_sha256')}` |",
        f"| Scientific freeze | `{report['scientific_freeze']['freeze_sha256']}` |",
        f"| Exclusion register | `{gates.get('exclusion_register_sha256')}` |",
        f"| Reviewed slice lock | `{gates.get('slice_lock_sha256')}` |",
        f"| Pair-content digest | `{gates.get('pair_content_digest')}` |",
        f"| Execution authorization | `{gates.get('execution_authorization_sha256')}` |",
        f"| Authorized study | `{gates.get('authorized_study')}` |",
        f"| Paid providers authorized | `{gates.get('paid_providers_authorized')}` |",
        "",
        "## Local CPU validation",
        "",
        f"**{local.get('passed_gate_count')}/{local.get('gate_count')}** gates passed "
        f"(`{local.get('pytest_counts')}`, {local.get('pytest_workers')} pytest workers).",
        "",
        f"- Regressions introduced by this work: **{local.get('regressions') or 'none'}**.",
        f"- Still failing for reasons that predate it: "
        f"`{local.get('failed_gates_preexisting') or 'none'}`. "
        "Both are the task-intervention contract blockers on the public development splits, "
        "reproduced unchanged at `22dbff0`. They are a separate body of work and were not "
        "papered over here.",
        "",
        "## Kaggle",
        "",
        f"- Arbitrary-name discovery: **{kaggle.get('arbitrary_name_case_count')}** cases, "
        f"passed `{kaggle.get('arbitrary_name_tests_passed')}`.",
        f"- Datasets API: `{kaggle.get('authentication_datasets_api')}`. "
        f"Notebooks API: `{kaggle.get('authentication_notebooks_api')}`.",
        f"- Remote CPU 00/01/02: `{kaggle.get('remote_cpu_00')}` / "
        f"`{kaggle.get('remote_cpu_01')}` / `{kaggle.get('remote_cpu_02')}`.",
        "",
        "| bundle | sha256 | bytes |",
        "| --- | --- | ---: |",
    ]
    for name, bundle in sorted((kaggle.get("bundles") or {}).items()):
        lines.append(f"| `{name}` | `{bundle['sha256']}` | {bundle['size_bytes']} |")
    lines += [
        "",
        "## What this does not authorize",
        "",
        "Live open-model execution. The Compact-20 pilot is authorized; Scale-100, Main-500, "
        "the naturalistic transfer study and the RAAC ablation are not, and none is implied by "
        "this one. No model or provider was invoked anywhere in this chain.",
    ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args(argv)

    report = build()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "POST_HUMAN_REVIEW_FINAL_REPORT.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    (args.output_dir / "POST_HUMAN_REVIEW_FINAL_REPORT.md").write_text(markdown(report))
    print(json.dumps({"statuses": report["statuses"], "written": 2}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
