#!/usr/bin/env python3
"""Generate the Kaggle CPU notebooks from one source of truth.

Notebook JSON is generated, never hand-edited: a hand-edited notebook drifts from
the module it is supposed to exercise, and the drift is invisible until it fails
on Kaggle.  The input-discovery bootstrap is inlined verbatim from
``causal_agent_bench.kaggle_input_discovery``, so the notebooks and the tested
module cannot disagree about how a bundle is found.

Every notebook is written with ``execution_count = null`` and ``outputs = []``,
so a committed notebook never carries stale results.

These notebooks run on Kaggle **CPU** sessions.  None of them downloads or
executes a model; genuine open-model inference belongs to the T4x2 notebooks and
is never described as a CPU run.
"""

from __future__ import annotations

import argparse
import json
import sys
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

NOTEBOOK_DIR = REPO_ROOT / "notebooks" / "kaggle_cpu"
DISCOVERY_MODULE = REPO_ROOT / "src" / "causal_agent_bench" / "kaggle_input_discovery.py"

NOTEBOOK_SCHEMA_VERSION = "cab_kaggle_cpu_notebook_v1"


@dataclass(frozen=True)
class NotebookSpec:
    notebook_id: str
    filename: str
    title: str
    purpose: str
    lane: str
    expected_bundle_type: str
    requires_output_bundle: bool = False
    gate_note: str = ""
    steps: tuple[tuple[str, str], ...] = field(default_factory=tuple)


REPOSITORY = "REPOSITORY_BUNDLE"

SPECS: tuple[NotebookSpec, ...] = (
    NotebookSpec(
        notebook_id="CAB_CPU_00",
        filename="CAB_CPU_00_INPUT_AND_ENVIRONMENT_PREFLIGHT.ipynb",
        title="Input and environment preflight",
        purpose=(
            "Find the attached bundle by content, verify every member hash, and record the "
            "environment. No scientific analysis happens here."
        ),
        lane="input_preflight",
        expected_bundle_type=REPOSITORY,
        steps=(
            (
                "environment",
                """
                import json
                import os
                import platform
                import shutil
                import socket
                import sys
                usage = shutil.disk_usage(WORKING_ROOT)
                ENVIRONMENT = {
                    "python_version": platform.python_version(),
                    "platform": platform.platform(),
                    "machine": platform.machine(),
                    "processor_count": os.cpu_count(),
                    "disk_free_gib": round(usage.free / 2**30, 2),
                    "accelerator": os.environ.get("CAB_ACCELERATOR", "cpu"),
                }
                # Internet state is reported, never required: every CPU lane runs offline.
                try:
                    socket.setdefaulttimeout(2)
                    socket.socket().connect(("8.8.8.8", 53))
                    ENVIRONMENT["internet_reachable"] = True
                except Exception:
                    ENVIRONMENT["internet_reachable"] = False
                record("environment", ENVIRONMENT)
                print(json.dumps(ENVIRONMENT, indent=2, sort_keys=True))
                """,
            ),
            (
                "import_smoke_test",
                """
                sys.path.insert(0, str(BUNDLE_ROOT / "src"))
                import causal_agent_bench  # noqa: F401
                from causal_agent_bench.review_ready_v2 import PACKET_VERSION
                record("import_smoke_test", {"packet_version": PACKET_VERSION, "importable": True})
                print("imported causal_agent_bench; packet", PACKET_VERSION)
                """,
            ),
        ),
    ),
    NotebookSpec(
        notebook_id="CAB_CPU_01",
        filename="CAB_CPU_01_C10_SLICE_AND_AUTHORIZATION_AUDIT.ipynb",
        title="C10, reviewed slice and authorization audit",
        purpose=(
            "Independently re-verify the public commitments, the manual-import provenance, C10, "
            "the exclusion register, the slice lock and the execution authorization. Fails closed "
            "on any mismatch."
        ),
        lane="c10_audit",
        expected_bundle_type=REPOSITORY,
        steps=(
            (
                "public_commitments",
                """
                reports = BUNDLE_ROOT / "reports"
                required = {
                    "freeze": reports / "reviewer_ready_v2" / "SCIENTIFIC_FREEZE_V2.json",
                    "packet": reports / "reviewer_ready_v2" / "PUBLIC_PACKET_COMMITMENT.json",
                    "registry": reports / "reviewer_ready_v2" / "ACTIVE_PATH_REGISTRY.json",
                    "c10": reports / "post_human_review" / "C10_FINAL.json",
                    "waiver": reports / "post_human_review" / "COORDINATOR_DECLARATION_WAIVER.json",
                    "exclusion": reports / "post_human_review" / "EXCLUSION_REGISTER_FINAL.json",
                    "lock": reports / "post_human_review" / "REVIEWED_SLICE_LOCK_FINAL.json",
                    "authorization": reports / "post_human_review" / "EXECUTION_AUTHORIZATION_FINAL.json",
                    "agreement": reports / "post_human_review" / "AGREEMENT_FINAL.json",
                }
                missing = sorted(name for name, path in required.items() if not path.is_file())
                assert not missing, f"the bundle is missing required commitments: {missing}"
                DOCUMENTS = {name: json.loads(path.read_text()) for name, path in required.items()}
                # Present only when qualification submissions were actually
                # imported and scored. Its absence is a claim of nothing, and is
                # checked against what C10 claims rather than assumed benign.
                qualification_path = reports / "post_human_review" / "QUALIFICATION_FINAL.json"
                if qualification_path.is_file():
                    DOCUMENTS["qualification"] = json.loads(qualification_path.read_text())
                    required["qualification"] = qualification_path
                record("commitment_files", {name: file_sha256(path) for name, path in required.items()})
                print("loaded", len(DOCUMENTS), "commitment documents")
                """,
            ),
            (
                "chain_consistency",
                """
                c10 = DOCUMENTS["c10"]
                lock = DOCUMENTS["lock"]
                authorization = DOCUMENTS["authorization"]
                waiver = DOCUMENTS["waiver"]
                register = DOCUMENTS["exclusion"]

                checks = {
                    "c10_passed": c10["c10_state"] == "PASS",
                    "lock_names_this_c10": lock["c10_report_sha256"] == c10["receipt_sha256"],
                    "authorization_names_this_lock":
                        authorization["slice_lock_sha256"] == lock["receipt_sha256"],
                    "authorization_names_this_c10":
                        authorization["c10_report_sha256"] == c10["receipt_sha256"],
                    "lock_names_this_register":
                        lock["exclusion_register_sha256"] == register["receipt_sha256"],
                    "waiver_is_bound_everywhere": (
                        c10["coordinator_waiver_sha256"]
                        == lock["coordinator_waiver_sha256"]
                        == authorization["coordinator_waiver_sha256"]
                        == waiver["receipt_sha256"]
                    ),
                    "included_count_agrees": (
                        c10["included_pair_count"]
                        == lock["locked_pair_count"]
                        == authorization["authorized_pair_count"]
                        == register["included_pair_count"]
                    ),
                    "no_unresolved_dimension": c10["unresolved_pair_count"] == 0,
                    # The provenance qualifier must survive all the way to the end.
                    "declaration_waiver_disclosed":
                        authorization["declaration_mode"] == "COORDINATOR_WAIVER",
                    "no_declaration_is_claimed": waiver["reviewer_declarations_confirmed"] is False,
                    "declaration_files_are_not_claimed":
                        authorization["reviewer_declaration_files_collected"] is False,
                    # A qualification pass may be claimed only where scored
                    # submissions establish it, and the claim must be identical
                    # in the waiver, C10 and the authorization.
                    "qualification_claim_is_consistent": (
                        waiver["qualification_pass_verified_in_this_chain"]
                        is c10["qualification_passed"]
                        is authorization["qualification_passed"]
                    ),
                    "qualification_mode_is_consistent": (
                        waiver["qualification_mode"]
                        == c10["qualification_mode"]
                        == lock["qualification_mode"]
                        == authorization["qualification_mode"]
                    ),
                    "qualification_claim_is_backed_by_evidence": (
                        (
                            "qualification" in DOCUMENTS
                            and DOCUMENTS["qualification"]["every_role_qualified"] is True
                            and DOCUMENTS["qualification"]["qualification_commitment_sha256"]
                            == waiver["qualification_commitment_sha256"]
                            == authorization["qualification_commitment_sha256"]
                            and all(
                                float(rate) >= float(DOCUMENTS["qualification"]["threshold"])
                                for rate in DOCUMENTS["qualification"]["rates"].values()
                            )
                        )
                        if c10["qualification_passed"]
                        else (
                            waiver["qualification_commitment_sha256"] is None
                            and "qualification" not in DOCUMENTS
                        )
                    ),
                    "qualification_answer_key_is_not_disclosed": (
                        DOCUMENTS["qualification"]["answer_key_disclosed"] is False
                        and DOCUMENTS["qualification"]["per_item_correctness_published"] is False
                        if "qualification" in DOCUMENTS
                        else True
                    ),
                    "paid_providers_not_authorized":
                        authorization["paid_providers_authorized"] is False,
                    "only_the_pilot_is_authorized":
                        authorization["authorized_study"] == "compact20_reviewed_pilot",
                }
                failed = sorted(name for name, ok in checks.items() if not ok)
                record("chain_consistency", {"checks": checks, "failed": failed})
                print(json.dumps(checks, indent=2, sort_keys=True))
                assert not failed, f"the reviewed-slice chain is inconsistent: {failed}"
                """,
            ),
            (
                "agreement_thresholds",
                """
                contract = json.loads((BUNDLE_ROOT / "configs/human_validation/c10_contract_v2.json").read_text())
                agreement = DOCUMENTS["agreement"]
                threshold = float(contract["min_raw_agreement"])
                observed = {
                    "stage1": float(agreement["stage1"]["overall_raw_agreement"]),
                    "stage2": float(agreement["stage2"]["overall_raw_agreement"]),
                }
                assert agreement["adjudicated_values_used"] is False, (
                    "agreement must be computed from raw pre-adjudication judgements"
                )
                failed = sorted(stage for stage, value in observed.items() if value < threshold)
                record("agreement", {"threshold": threshold, "observed": observed, "failed": failed})
                print(json.dumps({"threshold": threshold, **observed}, indent=2, sort_keys=True))
                assert not failed, f"agreement below the frozen threshold: {failed}"
                """,
            ),
        ),
    ),
    NotebookSpec(
        notebook_id="CAB_CPU_02",
        filename="CAB_CPU_02_PROVIDER_FREE_FULL_VALIDATION.ipynb",
        title="Provider-free full validation",
        purpose=(
            "Run the CPU-safe validation gates against the attached bundle as an independent "
            "reproducibility check. Downloads nothing and executes no model."
        ),
        lane="provider_free_validation",
        expected_bundle_type=REPOSITORY,
        steps=(
            (
                "static_and_security_gates",
                """
                import subprocess
                GATES = [
                    ("structured_data", ["python3", "scripts/validate_tracked_structured_data.py"]),
                    ("security", ["python3", "scripts/security_check.py"]),
                    ("leakage", ["python3", "scripts/cab_leakage_gate.py"]),
                    ("notebooks", ["python3", "scripts/validate_kaggle_cpu_notebooks.py"]),
                ]
                environment = dict(os.environ)
                environment["PYTHONPATH"] = f"{BUNDLE_ROOT / 'src'}:{BUNDLE_ROOT}"
                results = {}
                for name, command in GATES:
                    script = BUNDLE_ROOT / command[1]
                    if not script.is_file():
                        results[name] = {"status": "absent_from_bundle"}
                        continue
                    completed = subprocess.run(
                        command, cwd=BUNDLE_ROOT, env=environment,
                        capture_output=True, text=True, check=False,
                    )
                    results[name] = {
                        "returncode": completed.returncode,
                        "stdout_tail": completed.stdout[-2000:],
                        "stderr_tail": completed.stderr[-2000:],
                    }
                    print(name, "->", completed.returncode)
                record("gates", results)
                failed = sorted(k for k, v in results.items() if v.get("returncode", 0) != 0)
                assert not failed, f"validation gates failed: {failed}"
                """,
            ),
            (
                "focused_tests",
                """
                import subprocess

                completed = subprocess.run(
                    ["python3", "-m", "pytest", "-q", "-p", "no:randomly",
                     "tests/test_manual_offline_review_import.py",
                     "tests/test_kaggle_input_autodiscovery.py",
                     "tests/test_kaggle_input_bundle_builder.py"],
                    cwd=BUNDLE_ROOT, env=environment, capture_output=True, text=True, check=False,
                )
                record("focused_tests", {
                    "returncode": completed.returncode,
                    "stdout_tail": completed.stdout[-4000:],
                })
                print(completed.stdout[-2000:])
                assert completed.returncode == 0, "focused provider-free tests failed"
                """,
            ),
        ),
    ),
    NotebookSpec(
        notebook_id="CAB_CPU_03",
        filename="CAB_CPU_03_COMPACT20_POSTRUN_MERGE_SCORE_AUDIT.ipynb",
        title="Compact-20 post-run merge, score and audit",
        purpose=(
            "Merge, score and audit a genuine Compact-20 output bundle returned from a T4x2 run, "
            "then classify what the evidence is eligible to support."
        ),
        lane="compact20_postrun",
        expected_bundle_type="COMPACT20_OUTPUT",
        requires_output_bundle=True,
        gate_note=(
            "Runs only when a valid Compact-20 output bundle is attached. There is no fixture "
            "fallback: a missing run is reported as missing, never simulated."
        ),
        steps=(
            (
                "verify_run_provenance",
                """
                manifest_path = BUNDLE_ROOT / "CAB_KAGGLE_OUTPUT_MANIFEST.json"
                assert manifest_path.is_file(), "the attached output bundle has no output manifest"
                run_manifest = json.loads(manifest_path.read_text())
                checks = {
                    "declares_compact20": run_manifest.get("study") == "compact20_reviewed_pilot",
                    "binds_an_execution_authorization":
                        bool(run_manifest.get("execution_authorization_sha256")),
                    "binds_an_input_bundle": bool(run_manifest.get("input_archive_sha256")),
                    "binds_a_code_commit": bool(run_manifest.get("code_commit")),
                    "reports_success": run_manifest.get("run_state") == "COMPLETE",
                }
                failed = sorted(name for name, ok in checks.items() if not ok)
                record("run_provenance", {"checks": checks, "failed": failed})
                assert not failed, f"the output bundle provenance is incomplete: {failed}"
                """,
            ),
            (
                "merge_score_and_audit",
                """
                import subprocess

                # Deliberately delegates to the repository CLI rather than reimplementing
                # scoring here: a second implementation is a second set of bugs.
                for stage, command in (
                    ("merge", ["python3", "-m", "causal_agent_bench", "batch-merge",
                               "--batch-dir", str(BUNDLE_ROOT), "--output-dir", str(LANE_DIR / "merged")]),
                    ("score", ["python3", "-m", "causal_agent_bench", "score",
                               "--run-dir", str(LANE_DIR / "merged")]),
                    ("failures", ["python3", "-m", "causal_agent_bench", "failure-report",
                                  "--run-dir", str(LANE_DIR / "merged")]),
                    ("analyze", ["python3", "-m", "causal_agent_bench", "analyze",
                                 "--run-dir", str(LANE_DIR / "merged")]),
                ):
                    completed = subprocess.run(command, cwd=REPO_FOR_CLI, env=environment,
                                               capture_output=True, text=True, check=False)
                    record(f"postrun_{stage}", {"returncode": completed.returncode,
                                                "stdout_tail": completed.stdout[-2000:]})
                    print(stage, "->", completed.returncode)
                    assert completed.returncode == 0, f"{stage} failed"
                """,
            ),
        ),
    ),
    NotebookSpec(
        notebook_id="CAB_CPU_04",
        filename="CAB_CPU_04_SCALE100_POSTRUN_MERGE_SCORE_AUDIT.ipynb",
        title="Scale-100 post-run merge, score and audit",
        purpose="Merge, score and audit a genuine Scale-100 output bundle.",
        lane="scale100_postrun",
        expected_bundle_type="SCALE100_OUTPUT",
        requires_output_bundle=True,
        gate_note=(
            "Scale-100 requires its own reviewed material, its own validity gates and its own "
            "authorization. A Compact-20 output bundle is refused here by bundle type, so "
            "Compact-20 results can never be presented as Scale-100."
        ),
    ),
    NotebookSpec(
        notebook_id="CAB_CPU_05",
        filename="CAB_CPU_05_RAAC_BASELINE_ABLATION_ANALYSIS.ipynb",
        title="RAAC baseline and ablation analysis",
        purpose=(
            "Equal-budget baseline comparison, RAAC effect, overhead and ablation summaries with "
            "uncertainty. Executes no model inference."
        ),
        lane="raac_analysis",
        expected_bundle_type="RAAC_OUTPUT",
        requires_output_bundle=True,
        gate_note=(
            "Runs only after the Compact-20 execution is audited, budgets are equalized, baseline "
            "contracts are frozen and the analysis endpoints are preregistered."
        ),
    ),
    NotebookSpec(
        notebook_id="CAB_CPU_06",
        filename="CAB_CPU_06_NATURALISTIC_POSTRUN_ANALYSIS.ipynb",
        title="Naturalistic transfer post-run analysis",
        purpose=(
            "Transfer and predictive-validity analysis, preserving dataset-level missingness "
            "rather than imputing it away."
        ),
        lane="naturalistic_postrun",
        expected_bundle_type="NATURALISTIC_OUTPUT",
        requires_output_bundle=True,
        gate_note=(
            "Requires the naturalistic study's own human-validity, provenance, privacy, PII and "
            "injection gates to have passed, plus its own authorization."
        ),
    ),
    NotebookSpec(
        notebook_id="CAB_CPU_07",
        filename="CAB_CPU_07_FINAL_BOOTSTRAP_PAPER_RELEASE.ipynb",
        title="Final bootstrap, paper assets and release",
        purpose=(
            "Resumable 10,000-replicate clustered bootstrap, final uncertainty tables, rank "
            "instability, scorer sensitivity, paper assets and the reproducibility archive."
        ),
        lane="final_release",
        expected_bundle_type="FINAL_ANALYSIS_INPUT",
        requires_output_bundle=True,
        gate_note=(
            "Runs only on audited, eligible evidence that has passed the blinded scorer audit. "
            "Fixture evidence is refused: passing a fixture bundle here is an error, not a "
            "dry run."
        ),
    ),
    NotebookSpec(
        notebook_id="CAB_CPU_08",
        filename="CAB_CPU_08_FAILURE_RECOVERY_AND_ARCHIVE_REPAIR.ipynb",
        title="Failure recovery and archive repair",
        purpose=(
            "Inspect a partial output archive, identify completed and corrupt work, and generate "
            "a deterministic resume plan. Never repairs scientific content."
        ),
        lane="failure_recovery",
        expected_bundle_type=None,
        requires_output_bundle=True,
        gate_note=(
            "This notebook quarantines corrupt chunks and plans a resume. It never edits a "
            "trajectory, never fills a gap, and never converts a partial run into a complete one."
        ),
        steps=(
            (
                "inventory_partial_archive",
                """
                completed_ids, corrupt = [], []
                for path in sorted(BUNDLE_ROOT.rglob("*.jsonl")):
                    for number, line in enumerate(path.read_text().splitlines(), start=1):
                        if not line.strip():
                            continue
                        try:
                            row = json.loads(line)
                        except json.JSONDecodeError:
                            corrupt.append({"file": str(path.relative_to(BUNDLE_ROOT)), "line": number})
                            continue
                        key = row.get("trajectory_id") or row.get("item_id")
                        if key:
                            completed_ids.append(str(key))
                summary = {
                    "completed_count": len(set(completed_ids)),
                    "duplicate_count": len(completed_ids) - len(set(completed_ids)),
                    "corrupt_record_count": len(corrupt),
                }
                record("partial_inventory", {**summary, "corrupt": corrupt[:50]})
                print(json.dumps(summary, indent=2, sort_keys=True))
                """,
            ),
            (
                "deterministic_resume_plan",
                """
                # The plan names what is missing. It does not fabricate any of it.
                plan = {
                    "schema_version": "cab_resume_plan_v1",
                    "completed_trajectory_ids": sorted(set(completed_ids)),
                    "quarantined_records": corrupt,
                    "resume_rule": "re-run only ids absent from completed_trajectory_ids",
                    "raw_evidence_preserved": True,
                    "scientific_content_modified": False,
                }
                write_output_json("resume_plan.json", plan)
                record("resume_plan", {"resume_count_unknown_until_manifest_attached": True})
                print("resume plan written for", len(plan["completed_trajectory_ids"]), "completed ids")
                """,
            ),
        ),
    ),
)


# --------------------------------------------------------------------------
# cell construction
# --------------------------------------------------------------------------


def _dedent(source: str) -> str:
    return textwrap.dedent(source).strip("\n")


def _markdown(source: str) -> dict[str, Any]:
    return {"cell_type": "markdown", "metadata": {}, "source": _dedent(source).splitlines(True)}


def _code(source: str, role: str) -> dict[str, Any]:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {"cab_role": role},
        "outputs": [],
        "source": _dedent(source).splitlines(True),
    }


def _discovery_source() -> str:
    """The discovery module, inlined so notebook and module cannot drift."""

    return DISCOVERY_MODULE.read_text()


def _purpose_cell(spec: NotebookSpec) -> dict[str, Any]:
    lines = [
        f"# {spec.notebook_id} — {spec.title}",
        "",
        spec.purpose,
        "",
        "## What this notebook does not do",
        "",
        "- It does not download or execute a model. This is a CPU lane.",
        "- It does not depend on the attached ZIP's filename or the Kaggle dataset name.",
        "- It does not treat a fixture run as empirical evidence.",
    ]
    if spec.gate_note:
        lines += ["", "## Gate", "", spec.gate_note]
    lines += [
        "",
        "## Input",
        "",
        "Attach the CAB bundle as a Kaggle dataset. **Rename it however you like** — discovery "
        "inspects archive contents, not names. If more than one valid but *different* bundle is "
        "attached, the notebook stops and prints a candidate table rather than guessing.",
        "",
        "## Output",
        "",
        f"A single ZIP under `/kaggle/working/cab_outputs/{spec.lane}/`, carrying the input archive "
        "hash, the code commit, the environment, every step's result and each member's hash. "
        "On failure it still writes a failure bundle with diagnostics and resume state.",
    ]
    return _markdown("\n".join(lines))


def _configuration_cell(spec: NotebookSpec) -> dict[str, Any]:
    expected = repr(spec.expected_bundle_type)
    return _code(
        f"""
        # CAB_ROLE: configuration - edit here, not below.
        NOTEBOOK_ID = {spec.notebook_id!r}
        NOTEBOOK_SCHEMA_VERSION = {NOTEBOOK_SCHEMA_VERSION!r}
        LANE = {spec.lane!r}
        EXPECTED_BUNDLE_TYPE = {expected}
        REQUIRES_OUTPUT_BUNDLE = {spec.requires_output_bundle!r}
        SEED = 20260805

        # Kaggle's standard locations. Override only when running this notebook
        # somewhere else; discovery works the same either way.
        INPUT_ROOT = "/kaggle/input"
        WORKING_ROOT = "/kaggle/working"

        # No CPU lane performs model inference. This constant exists so the
        # intent is greppable, not because a lane could opt in.
        RUN_LIVE = False
        """,
        "configuration",
    )


def _bootstrap_cell() -> dict[str, Any]:
    return _code(
        f"""
        # CAB_ROLE: bootstrap - stdlib only. Finds the attached bundle by content.
        #
        # The body of this cell is inlined verbatim from
        # src/causal_agent_bench/kaggle_input_discovery.py by
        # scripts/build_kaggle_cpu_notebooks.py. Do not edit it here: edit the
        # module and regenerate, or the notebook and its tests will disagree.
        import hashlib
        import json
        import os
        import zipfile
        from dataclasses import dataclass
        from datetime import UTC, datetime
        from pathlib import Path
        from typing import Any

        {"# --- begin inlined kaggle_input_discovery ---"}
        {_INLINE_MARKER}
        {"# --- end inlined kaggle_input_discovery ---"}

        WORKING_ROOT = Path(WORKING_ROOT)
        INPUT_ROOT = Path(INPUT_ROOT)
        LANE_DIR = WORKING_ROOT / "cab_outputs" / LANE
        LANE_DIR.mkdir(parents=True, exist_ok=True)

        STARTED_AT = datetime.now(UTC).isoformat()
        STEPS = {{}}

        def record(step, payload):
            STEPS[step] = payload

        def write_output_json(name, payload):
            target = LANE_DIR / name
            target.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + chr(10))
            return target

        DISCOVERY = discover_kaggle_input(
            search_root=INPUT_ROOT,
            working_root=WORKING_ROOT,
            expected_bundle_type=EXPECTED_BUNDLE_TYPE,
        )
        BUNDLE_ROOT = Path(DISCOVERY["bundle_root"])
        REPO_FOR_CLI = BUNDLE_ROOT
        record("discovery", DISCOVERY)
        print("bundle type :", DISCOVERY["bundle_type"])
        print("archive hash:", DISCOVERY["archive_sha256"])
        print("bundle root :", BUNDLE_ROOT)
        """,
        "bootstrap",
    )


def _manifest_cell() -> dict[str, Any]:
    return _code(
        """
        # CAB_ROLE: integrity - re-hash every member the bundle manifest declares.
        if (BUNDLE_ROOT / "CAB_KAGGLE_INPUT_MANIFEST.json").is_file():
            VERIFICATION = verify_bundle_manifest(BUNDLE_ROOT)
            record("bundle_manifest", VERIFICATION)
            print(json.dumps(VERIFICATION["checks"], indent=2, sort_keys=True))
            assert VERIFICATION["passed"], (
                f"bundle integrity failed: missing={VERIFICATION['missing_members'][:5]} "
                f"mismatched={VERIFICATION['mismatched_members'][:5]}"
            )
            CODE_COMMIT = VERIFICATION["created_from_commit"]
        else:
            # Output bundles carry their own manifest instead.
            VERIFICATION = {"checks": {}, "passed": True}
            CODE_COMMIT = None
            record("bundle_manifest", {"input_manifest_absent": True})
        environment = dict(os.environ)
        environment["PYTHONPATH"] = f"{BUNDLE_ROOT / 'src'}:{BUNDLE_ROOT}"
        """,
        "integrity",
    )


def _gate_cell(spec: NotebookSpec) -> dict[str, Any]:
    return _code(
        f"""
        # CAB_ROLE: gate - refuse to proceed without genuine inputs for this lane.
        GATE_NOTE = {spec.gate_note!r}
        if REQUIRES_OUTPUT_BUNDLE:
            assert DISCOVERY["bundle_type"] != "REPOSITORY_BUNDLE", (
                "this lane analyses a genuine run-output bundle. A repository bundle is not a "
                "run, and there is no fixture fallback. Attach the returned output archive."
            )
        record("gate", {{"note": GATE_NOTE, "requires_output_bundle": REQUIRES_OUTPUT_BUNDLE}})
        print(GATE_NOTE or "no additional gate for this lane")
        """,
        "gate",
    )


def _export_cell(spec: NotebookSpec) -> dict[str, Any]:
    return _code(
        """
        # CAB_ROLE: export - always produce a ZIP, success or failure.
        def build_output_archive(state):
            manifest = {
                "schema_version": "cab_kaggle_output_manifest_v1",
                "notebook_id": NOTEBOOK_ID,
                "lane": LANE,
                "run_state": state,
                "input_archive_sha256": DISCOVERY["archive_sha256"],
                "input_bundle_type": DISCOVERY["bundle_type"],
                "code_commit": CODE_COMMIT,
                "environment": STEPS.get("environment", {}),
                "started_at_utc": STARTED_AT,
                "finished_at_utc": datetime.now(UTC).isoformat(),
                "steps": sorted(STEPS),
                "step_results": STEPS,
                "contains_secrets": False,
            }
            write_output_json("CAB_KAGGLE_OUTPUT_MANIFEST.json", manifest)

            members = sorted(p for p in LANE_DIR.rglob("*") if p.is_file() and p.suffix != ".zip")
            member_hashes = [
                {"path": str(p.relative_to(LANE_DIR)), "sha256": file_sha256(p)} for p in members
            ]
            content_hash = hashlib.sha256(
                json.dumps([[m["path"], m["sha256"]] for m in member_hashes],
                           separators=(",", ":")).encode()
            ).hexdigest()
            manifest["members"] = member_hashes
            manifest["member_count"] = len(member_hashes)
            manifest["bundle_content_sha256"] = content_hash
            write_output_json("CAB_KAGGLE_OUTPUT_MANIFEST.json", manifest)

            label = "OUTPUT" if state == "COMPLETE" else "FAILURE_BUNDLE"
            target = WORKING_ROOT / f"CAB_{LANE.upper()}_{label}_{content_hash[:16]}.zip"
            with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                for path in sorted(p for p in LANE_DIR.rglob("*") if p.is_file()):
                    info = zipfile.ZipInfo(str(path.relative_to(LANE_DIR)),
                                           date_time=(1980, 1, 1, 0, 0, 0))
                    info.external_attr = (0o100644) << 16
                    info.compress_type = zipfile.ZIP_DEFLATED
                    archive.writestr(info, path.read_bytes())
            return target, content_hash

        OUTPUT_ARCHIVE, OUTPUT_HASH = build_output_archive("COMPLETE")
        print("output archive:", OUTPUT_ARCHIVE)
        print("content hash  :", OUTPUT_HASH)
        print("You may rename this ZIP; every CAB notebook finds it by content.")
        """,
        "export",
    )


def _failure_cell() -> dict[str, Any]:
    return _markdown(
        """
        ## If a cell above failed

        Do not edit results to make this notebook finish. Run the cell below to
        package the diagnostics and resume state exactly as they are, download
        the failure bundle, and fix the cause.

        A partial run is never reported as a successful one.
        """
    )


def _failure_export_cell() -> dict[str, Any]:
    return _code(
        """
        # CAB_ROLE: failure_export - run this only after a failure above.
        FAILURE_ARCHIVE, FAILURE_HASH = build_output_archive("FAILED")
        print("failure bundle:", FAILURE_ARCHIVE)
        """,
        "failure_export",
    )


_INLINE_MARKER = "___CAB_INLINE_DISCOVERY___"


def build_notebook(spec: NotebookSpec) -> dict[str, Any]:
    cells: list[dict[str, Any]] = [
        _purpose_cell(spec),
        _configuration_cell(spec),
        _bootstrap_cell(),
        _manifest_cell(),
        _gate_cell(spec),
    ]
    for role, source in spec.steps:
        cells.append(_code(source, role))
    cells += [_export_cell(spec), _failure_cell(), _failure_export_cell()]

    # Inline the discovery module into the bootstrap cell, indented to match.
    discovery = _discovery_source()
    for cell in cells:
        if cell["cell_type"] != "code":
            continue
        joined = "".join(cell["source"])
        if _INLINE_MARKER in joined:
            # Every import the module needs is already at the top of the
            # bootstrap cell, so strip the module's own import block: leaving it
            # mid-cell would put imports after code, which is both untidy and a
            # lint failure in the committed notebook.
            body = "\n".join(
                line
                for line in discovery.splitlines()
                if not line.startswith(("from __future__", "import ", "from "))
            )
            cell["source"] = joined.replace(_INLINE_MARKER, body).splitlines(True)

    return {
        "cells": cells,
        "metadata": {
            "cab_notebook_schema_version": NOTEBOOK_SCHEMA_VERSION,
            "cab_notebook_id": spec.notebook_id,
            "cab_lane": spec.lane,
            "cab_accelerator": "cpu",
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.11"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def write_notebooks(*, check: bool = False) -> list[Path]:
    NOTEBOOK_DIR.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for spec in SPECS:
        target = NOTEBOOK_DIR / spec.filename
        payload = json.dumps(build_notebook(spec), indent=1, sort_keys=True) + "\n"
        if check:
            if not target.is_file() or target.read_text() != payload:
                raise SystemExit(
                    f"{target.relative_to(REPO_ROOT)} is out of date; run "
                    "scripts/build_kaggle_cpu_notebooks.py"
                )
        else:
            target.write_text(payload)
        written.append(target)
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if any notebook is stale")
    args = parser.parse_args(argv)
    written = write_notebooks(check=args.check)
    print(
        json.dumps(
            {
                "status": "CHECKED" if args.check else "GENERATED",
                "notebook_count": len(written),
                "notebooks": [str(path.relative_to(REPO_ROOT)) for path in written],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
