"""Build the nine governed Kaggle T4x2 notebooks as deterministic JSON.

This is a source generator, not an execution entry point.  Generated notebooks
default to a repository-controlled, model-free fixture path.  Their real-data
cells remain behind a multi-factor activation gate.
"""

from __future__ import annotations

import argparse
import json
import textwrap
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_DIR = REPO_ROOT / "notebooks" / "kaggle"


@dataclass(frozen=True)
class NotebookSpec:
    stem: str
    title: str
    purpose: str
    live_kind: str
    live_config: str | None
    exact_inputs: tuple[str, ...]
    exact_live_outputs: tuple[str, ...]
    requires_model_snapshot: bool
    supports_real_artifacts: bool = True
    carries_raac_matrix: bool = False


SPECS = (
    NotebookSpec(
        stem="CAB_T4X2_00_ENVIRONMENT_PREFLIGHT",
        title="CAB T4x2 00 - Environment Preflight",
        purpose=(
            "Inspect GPU count and VRAM, CUDA visibility, RAM, disk, packages, repository "
            "layout, and internet reachability before any Kaggle execution is considered."
        ),
        live_kind="none",
        live_config=None,
        exact_inputs=("pyproject.toml", "src/causal_agent_bench/kaggle_fixture.py"),
        exact_live_outputs=(),
        requires_model_snapshot=False,
        supports_real_artifacts=False,
    ),
    NotebookSpec(
        stem="CAB_T4X2_01_OFFLINE_FIXTURE_SMOKE",
        title="CAB T4x2 01 - Offline Fixture Smoke",
        purpose=(
            "Exercise deterministic two-worker sharding, append-safe fixture ledgers, "
            "checkpoint/resume, merge, archive export, and hash verification without a model."
        ),
        live_kind="none",
        live_config=None,
        exact_inputs=("src/causal_agent_bench/kaggle_fixture.py",),
        exact_live_outputs=(),
        requires_model_snapshot=False,
        supports_real_artifacts=False,
    ),
    NotebookSpec(
        stem="CAB_T4X2_02_COMPACT20_OPEN_MODEL_RUNNER",
        title="CAB T4x2 02 - Compact-20 Open-Model Runner",
        purpose=(
            "Prepare a gated Compact-20 open-model batch with independent per-GPU workers, "
            "checkpointed shards, deterministic merge, and no automatic evidence promotion."
        ),
        live_kind="runner",
        live_config="configs/compact20_3model_LOCAL_TEMPLATE_NOT_APPROVED.yaml",
        exact_inputs=(
            "configs/compact20_3model_LOCAL_TEMPLATE_NOT_APPROVED.yaml",
            "data/manifests/compact20_v2_public_manifest.json",
            "data/manifests/compact20_review_packet_v2_public_commitment.json",
            "CAB_LOCAL_MODEL_SNAPSHOT (environment-only directory setting)",
        ),
        exact_live_outputs=(
            "live_batch/batch_manifest.json",
            "live_batch/shards/worker-specific run directories",
            "live_batch/merged/run (unscored; audit required)",
            "live_batch/live_integrity_manifest.json",
        ),
        requires_model_snapshot=True,
    ),
    NotebookSpec(
        stem="CAB_T4X2_03_SCALE100_OPEN_MODEL_RUNNER",
        title="CAB T4x2 03 - Scale-100 Open-Model Runner",
        purpose=(
            "Prepare a gated 100-task open-model batch after Compact-20 clears its upstream "
            "gates, with deterministic shards, checkpointing, and a single-GPU fallback."
        ),
        live_kind="runner",
        live_config="configs/iclr/scale100_v2_EXECUTION_TEMPLATE_NOT_APPROVED.yaml",
        exact_inputs=(
            "configs/iclr/scale100_v2_EXECUTION_TEMPLATE_NOT_APPROVED.yaml",
            "data/manifests/scale100_confirmatory_v2_public_manifest.json",
            "CAB_APPROVED_SCALE100_BUNDLE (environment-only approved materialization)",
            "CAB_LOCAL_MODEL_SNAPSHOT (environment-only directory setting)",
        ),
        exact_live_outputs=(
            "live_batch/batch_manifest.json",
            "live_batch/shards/worker-specific run directories",
            "live_batch/merged/run (unscored; audit required)",
            "live_batch/live_integrity_manifest.json",
        ),
        requires_model_snapshot=True,
    ),
    NotebookSpec(
        stem="CAB_T4X2_04_MAIN500_OPEN_MODEL_RUNNER",
        title="CAB T4x2 04 - Main-500 Historical Placeholder (Superseded)",
        purpose=(
            "Preserve notebook numbering while explicitly disabling the obsolete Main-500 "
            "scientific path. No live runner or result artifact is available here."
        ),
        live_kind="none",
        live_config=None,
        exact_inputs=("CURRENT_PROJECT_STATE.md",),
        exact_live_outputs=(),
        requires_model_snapshot=False,
        supports_real_artifacts=False,
    ),
    NotebookSpec(
        stem="CAB_T4X2_05_BASELINES_AND_ABLATIONS",
        title="CAB T4x2 05 - Baselines and Ablations",
        purpose=(
            "Prepare approved open-model baseline and ablation shards while keeping oracle "
            "controls, fixture runs, and future real evidence explicitly separated."
        ),
        live_kind="runner",
        live_config="configs/raac/kaggle_t4x2_raac_TEMPLATE_NOT_APPROVED.yaml",
        exact_inputs=(
            "configs/raac/kaggle_t4x2_raac_TEMPLATE_NOT_APPROVED.yaml",
            "configs/raac/kaggle_t4x2_matrix.yaml",
            "configs/raac/raac_light.yaml",
            "configs/raac/raac_full.yaml",
            "configs/raac/ablations.yaml",
            "configs/raac/baselines.yaml",
            "configs/raac/equal_budget.yaml",
            "CAB_LOCAL_MODEL_SNAPSHOT (environment-only directory setting)",
        ),
        exact_live_outputs=(
            "live_batch/batch_manifest.json",
            "live_batch/shards/worker-specific run directories",
            "live_batch/merged/run (unscored; audit required)",
            "live_batch/live_integrity_manifest.json",
        ),
        requires_model_snapshot=True,
        carries_raac_matrix=True,
    ),
    NotebookSpec(
        stem="CAB_T4X2_06_MERGE_AUDIT_AND_RESCORE",
        title="CAB T4x2 06 - Merge, Audit, and Rescore",
        purpose=(
            "Strictly merge returned shard artifacts, audit completeness and duplicates, then "
            "invoke the canonical scorer only after the merge report passes."
        ),
        live_kind="merge",
        live_config=None,
        exact_inputs=(
            "CAB_LIVE_BATCH_DIR/batch_manifest.json",
            "CAB_LIVE_BATCH_DIR/shards/*/run/*/trajectories.jsonl",
        ),
        exact_live_outputs=(
            "CAB_LIVE_BATCH_DIR/merged/run",
            "CAB_LIVE_BATCH_DIR/merged/run/merge_report.json",
            "CAB_LIVE_BATCH_DIR/merged/run/aggregate_scores.json (only after strict audit)",
            "CAB_LIVE_BATCH_DIR/merged/live_integrity_manifest.json",
        ),
        requires_model_snapshot=False,
    ),
    NotebookSpec(
        stem="CAB_T4X2_07_FAILURE_RECOVERY",
        title="CAB T4x2 07 - Failure Recovery",
        purpose=(
            "Inspect an interrupted batch, resume only incomplete deterministic shards, retain "
            "worker logs, and refuse a merge when any worker still fails."
        ),
        live_kind="recovery",
        live_config=None,
        exact_inputs=(
            "CAB_LIVE_BATCH_DIR/batch_manifest.json",
            "CAB_LIVE_BATCH_DIR/shards/*/config.yaml",
            "CAB_LOCAL_MODEL_SNAPSHOT (environment-only directory setting)",
        ),
        exact_live_outputs=(
            "CAB_LIVE_BATCH_DIR/shards/*/run resumed checkpoints",
            "CAB_LIVE_BATCH_DIR/recovery_logs/",
            "CAB_LIVE_BATCH_DIR/merged/run (unscored; audit required)",
            "CAB_LIVE_BATCH_DIR/live_integrity_manifest.json",
        ),
        requires_model_snapshot=True,
    ),
    NotebookSpec(
        stem="CAB_T4X2_08_NATURALISTIC_TRANSFER_RUNNER",
        title="CAB T4x2 08 - Artifact-Rich Synthetic Transfer Runner",
        purpose=(
            "Prepare the artifact-rich synthetic transfer batch only after materialized-file "
            "hashes, exact gold derivation, human review, and execution approval pass."
        ),
        live_kind="runner",
        live_config="configs/iclr/artifact_rich_transfer_v2_EXECUTION_TEMPLATE_NOT_APPROVED.yaml",
        exact_inputs=(
            "configs/iclr/artifact_rich_transfer_v2_EXECUTION_TEMPLATE_NOT_APPROVED.yaml",
            "data/manifests/naturalistic_transfer_v2_public_manifest.json",
            "CAB_APPROVED_TRANSFER_BUNDLE (environment-only approved materialization)",
            "CAB_LOCAL_MODEL_SNAPSHOT (environment-only directory setting)",
        ),
        exact_live_outputs=(
            "live_batch/batch_manifest.json",
            "live_batch/shards/worker-specific run directories",
            "live_batch/merged/run (unscored; audit required)",
            "live_batch/live_integrity_manifest.json",
        ),
        requires_model_snapshot=True,
    ),
)


def _dedent(source: str) -> str:
    return textwrap.dedent(source).strip() + "\n"


def _markdown_cell(source: str, role: str) -> dict[str, object]:
    return {
        "cell_type": "markdown",
        "metadata": {"cab_role": role},
        "source": _dedent(source),
    }


def _code_cell(source: str, role: str) -> dict[str, object]:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {"cab_role": role},
        "outputs": [],
        "source": _dedent(source),
    }


def _purpose_cell(spec: NotebookSpec) -> dict[str, object]:
    input_rows = "\n".join(
        f"| `{value}` | Required as described; never synthesized as evidence. |"
        for value in spec.exact_inputs
    )
    live_rows = (
        "\n".join(
            f"| `{value}` | Real-artifact output; never paper-eligible by existence alone. |"
            for value in spec.exact_live_outputs
        )
        if spec.exact_live_outputs
        else "| None | This notebook never starts real inference or processes real results. |"
    )
    return _markdown_cell(
        f"""
        # {spec.title}

        ## Purpose

        {spec.purpose}

        ## Evidence boundary

        **Default status: `FIXTURE_ONLY`; notebook engineering: `ENGINEERING_ONLY`; scientific
        execution: `EXECUTION_PENDING`.** Run-all is model-free because `RUN_LIVE = False`.
        Fixture receipts are not answers, trajectories, labels, metrics, runtimes, rankings, or
        paper evidence. No output from this notebook may be promoted until the repository merge,
        completeness, scorer-sanity, human-review, evidence, and claim-ledger gates pass.

        No credential value belongs in this notebook. Model snapshots are configured by a
        non-secret environment-only directory setting and are never downloaded here. Setup is
        idempotent and performs no package installation.

        ## Exact inputs

        | Input | Contract |
        |---|---|
        {input_rows}

        ## Exact outputs

        The offline output root is
        `${{CAB_KAGGLE_WORK_ROOT:-artifacts/kaggle}}/{spec.stem}/fixture/`.

        | Output | Contract |
        |---|---|
        | `runtime_preflight.json` | Non-secret runtime inventory. |
        | `fixture/merged/fixture_receipts.jsonl` | Mechanics receipts marked `FIXTURE_ONLY`. |
        | `fixture/integrity_manifest.json` | File sizes and SHA-256 hashes. |
        | `{spec.stem}_FIXTURE_ONLY.zip` | Downloadable fixture archive, never empirical evidence. |
        {live_rows}

        ## T4x2 policy

        Independent data-parallel workers are the default: worker 0 uses GPU 0 and worker 1 uses
        GPU 1, with deterministic non-overlapping item shards and separate directories. A
        one-worker fallback is explicit when only one or zero GPUs are visible to the preflight
        (zero GPUs still refuses real inference). `float16` is preferred on T4; `bfloat16` is not
        assumed. The approved config must select a 4-bit or smaller-model route when fp16 does not
        fit. Tensor parallelism is off unless an adapter is separately audited as compatible.
        """,
        "purpose",
    )


def _configuration_cell(spec: NotebookSpec) -> dict[str, object]:
    live_config = f'Path("{spec.live_config}")' if spec.live_config else "None"
    exact_paths = [
        value for value in spec.exact_inputs if not value.startswith("CAB_") and "*" not in value
    ]
    required_paths = "".join(f'    Path("{value}"),\n' for value in exact_paths)
    raac_matrix = "\n"
    if spec.carries_raac_matrix:
        raac_matrix = """
# Frozen RAAC treatment matrix. These are config selectors, not result claims.
RAAC_MATRIX_ENABLED = True
RAAC_MATRIX_CONFIG_PATH = Path("configs/raac/kaggle_t4x2_matrix.yaml")
RAAC_STANDARD_ARM = "STANDARD_TOOL_USE"
RAAC_PRIMARY_ARMS = ("STANDARD_TOOL_USE", "RAAC_LIGHT", "RAAC_FULL")
RAAC_ABLATION_ARMS = (
    "VERIFY_ONLY",
    "RETRY_ONLY",
    "ABSTAIN_ONLY",
    "NO_CROSS_CHECK",
    "NO_ALTERNATE_ROUTE",
    "NO_FINAL_VERIFY",
)
RAAC_BUDGET_MODES = ("equal_budget", "practical_budget")
RAAC_SELECTED_BUDGET_MODE = "practical_budget"
RAAC_REQUIRED_COMPUTE_FIELDS = (
    "max_extra_model_calls",
    "max_extra_tool_calls",
    "max_retries",
    "max_alternate_routes",
    "max_verification_steps",
    "max_clarification_steps",
    "token_budget",
    "wall_clock_budget_seconds",
    "termination_rule",
)
"""
    return _code_cell(
        f"""# CAB_ROLE: configuration - edit only this cell before an approved real-artifact session.
from pathlib import Path

RUN_LIVE = False
LIVE_CONFIRMATION = ""
REQUIRED_LIVE_CONFIRMATION = "I_UNDERSTAND_CAB_EXECUTION_IS_PENDING"

NOTEBOOK_ID = "{spec.stem}"
SEED = 20270723
REQUESTED_GPU_WORKERS = 2
FIXTURE_WORKERS = 2
OFFLINE_FIXTURE_ITEMS = 8
CHECK_INTERNET = True
MODEL_ESTIMATED_VRAM_GIB = None
MODEL_QUANTIZATION_MODE = "none"
MODEL_PLACEMENT_MODE = "single_gpu"
TWO_GPU_PLACEMENT_ADAPTER_AUDITED = False

WORK_ROOT_SETTING = "artifacts/kaggle"
LIVE_BATCH_DIR_SETTING = "artifacts/kaggle/live_batch"
LIVE_CONFIG_PATH = {live_config}
APPROVAL_RECEIPT = Path("private_data/approval/cryptographic_approval_receipt.json")
REQUIRED_REPOSITORY_INPUTS = [
{required_paths}]{raac_matrix}
LIVE_KIND = "{spec.live_kind}"
SUPPORTS_REAL_ARTIFACTS = {spec.supports_real_artifacts!r}
REQUIRES_MODEL_SNAPSHOT = {spec.requires_model_snapshot!r}
MODEL_SNAPSHOT_ENV = "CAB_LOCAL_MODEL_SNAPSHOT"
ACTIVATION_ENV = "CAB_ENABLE_LIVE_OPEN_MODEL_RUN"

MODEL_LOAD_POLICY = {{
    "preferred_dtype": "float16",
    "assume_bfloat16": False,
    "quantization_fallback": "4bit_when_fp16_preflight_fails",
    "two_gpu_placement_route": "requires_two_visible_gpus_and_an_audited_adapter",
    "optional_two_gpu_placement_default": False,
    "smaller_model_fallback": "required_when_4bit_is_unsupported_or_still_does_not_fit",
    "tensor_parallel_default": False,
}}
""",
        "configuration",
    )


def _setup_cell(spec: NotebookSpec) -> dict[str, object]:
    source = """
        # CAB_ROLE: setup - stdlib only; no installs, downloads, providers, or model imports.
        import hashlib
        import os
        import random
        import subprocess
        import sys
        from pathlib import Path

        random.seed(SEED)
        os.environ.setdefault("PYTHONHASHSEED", str(SEED))

        def locate_repo_root(start: Path) -> Path:
            # Find the repository, working or attached, without trusting any name.
            # An already-checked-out tree wins when we are standing in one. Failing
            # that, the bundle is found under /kaggle/input by inspecting archive
            # *contents* - the same content-addressed discovery the CPU notebooks
            # use - so the attached ZIP and the Kaggle dataset can both be renamed
            # to anything without breaking this cell.
            for candidate in [start.resolve(), *start.resolve().parents]:
                if (candidate / "pyproject.toml").is_file() and (
                    candidate / "src" / "causal_agent_bench"
                ).is_dir():
                    return candidate

            kaggle_input = Path("/kaggle/input")
            if kaggle_input.is_dir():
                # Prefer the shared module when an extracted copy is importable.
                for parent in sorted(kaggle_input.rglob("kaggle_input_discovery.py")):
                    sys.path.insert(0, str(parent.parents[2]))
                    break
                try:
                    from causal_agent_bench.kaggle_input_discovery import (
                        discover_kaggle_input,
                    )
                except Exception:
                    discover_kaggle_input = None
                if discover_kaggle_input is not None:
                    found = discover_kaggle_input(
                        search_root=kaggle_input,
                        working_root=Path("/kaggle/working"),
                        expected_bundle_type="REPOSITORY_BUNDLE",
                    )
                    return Path(found["bundle_root"])

                # Self-contained fallback: score archives by their member names.
                import zipfile

                sentinels = (
                    ("CAB_KAGGLE_INPUT_MANIFEST.json", 6),
                    ("reports/reviewer_ready_v2/ACTIVE_PATH_REGISTRY.json", 5),
                    ("src/causal_agent_bench/", 4),
                    ("configs/", 2),
                    ("scripts/", 2),
                    ("pyproject.toml", 1),
                )
                best_path, best_score = None, 0
                for archive_path in sorted(kaggle_input.rglob("*")):
                    if archive_path.suffix.casefold() != ".zip" or archive_path.is_symlink():
                        continue
                    try:
                        with zipfile.ZipFile(archive_path) as archive:
                            names = archive.namelist()
                    except (zipfile.BadZipFile, OSError):
                        continue
                    tops = {n.split("/", 1)[0] for n in names if n}
                    root = tops.pop() if len(tops) == 1 else ""
                    prefix = f"{root}/" if root else ""
                    relative = [n[len(prefix):] if prefix and n.startswith(prefix) else n for n in names]
                    score = sum(
                        weight
                        for marker, weight in sentinels
                        if (any(n.startswith(marker) for n in relative) if marker.endswith("/")
                            else marker in relative)
                    )
                    if score > best_score:
                        best_path, best_score = archive_path, score
                if best_path is not None and best_score >= 8:
                    destination = Path("/kaggle/working") / f"cab_input_{best_path.stat().st_size}"
                    if not destination.is_dir():
                        with zipfile.ZipFile(best_path) as archive:
                            for info in archive.infolist():
                                # chr(92) is a backslash: written this way so the
                                # generated notebook source needs no escaping.
                                parts = Path(info.filename.replace(chr(92), "/")).parts
                                if info.filename.startswith("/") or ".." in parts:
                                    raise RuntimeError(
                                        f"refusing to extract unsafe member {info.filename!r}"
                                    )
                                archive.extract(info, destination)
                    for depth in range(4):
                        for candidate in sorted(destination.glob("/".join(["*"] * depth) or "*")):
                            base = destination if depth == 0 else candidate
                            if (base / "pyproject.toml").is_file() and (
                                base / "src" / "causal_agent_bench"
                            ).is_dir():
                                return base
            raise RuntimeError(
                "Repository root not found. Attach the CAB bundle as a Kaggle dataset (any name), "
                "or clone the repository, then rerun setup."
            )

        REPO_ROOT = locate_repo_root(Path.cwd())
        SOURCE_ROOT = REPO_ROOT / "src"
        if str(SOURCE_ROOT) not in sys.path:
            sys.path.insert(0, str(SOURCE_ROOT))

        from causal_agent_bench.kaggle_fixture import (  # noqa: E402
            FIXTURE_EVIDENCE_CLASS,
            assert_shards_complete_and_disjoint,
            build_fixture_work_items,
            choose_worker_count,
            deterministic_shards,
            export_fixture_archive,
            initialize_fixture_workspace,
            merge_fixture_shards,
            model_snapshot_record,
            read_json,
            run_fixture_worker,
            runtime_preflight,
            verify_integrity_manifest,
            write_integrity_manifest,
            write_json,
            write_jsonl,
        )

        work_root_raw = os.environ.get("CAB_KAGGLE_WORK_ROOT", WORK_ROOT_SETTING)
        work_root = Path(work_root_raw).expanduser()
        if not work_root.is_absolute():
            work_root = REPO_ROOT / work_root
        FIXTURE_ROOT = initialize_fixture_workspace(work_root, NOTEBOOK_ID)
        NOTEBOOK_OUTPUT_DIR = FIXTURE_ROOT.parent

        def file_sha256(path: Path) -> str:
            digest = hashlib.sha256()
            with path.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
            return digest.hexdigest()

        def sanitized_subprocess_environment() -> dict:
            environment = os.environ.copy()
            sensitive_markers = (
                "api_key",
                "apikey",
                "auth_token",
                "access_token",
                "password",
                "private_key",
                "secret",
                "credential",
            )
            for name in list(environment):
                lowered = name.lower()
                if any(marker in lowered for marker in sensitive_markers):
                    environment.pop(name, None)
            environment["PYTHONHASHSEED"] = str(SEED)
            return environment

        def write_live_integrity_manifest(root: Path) -> dict:
            root = root.resolve()
            manifest_path = root / "live_integrity_manifest.json"
            file_rows = []
            for path in sorted(root.rglob("*")):
                if not path.is_file() or path.resolve() == manifest_path.resolve():
                    continue
                file_rows.append(
                    {
                        "path": path.relative_to(root).as_posix(),
                        "bytes": path.stat().st_size,
                        "sha256": file_sha256(path),
                    }
                )
            payload = {
                "evidence_class": "PRELIMINARY_REAL_EVIDENCE",
                "claim_promotion_allowed": False,
                "paper_asset_eligible": False,
                "file_count": len(file_rows),
                "files": file_rows,
            }
            write_json(manifest_path, payload)
            verified = all(
                (root / row["path"]).is_file()
                and (root / row["path"]).stat().st_size == row["bytes"]
                and file_sha256(root / row["path"]) == row["sha256"]
                for row in file_rows
            )
            if not verified:
                raise RuntimeError("live artifact size verification failed")
            return {
                "performed": True,
                "ok": True,
                "manifest_path": manifest_path.relative_to(root).as_posix(),
                "checked_files": len(file_rows),
                "evidence_class": "PRELIMINARY_REAL_EVIDENCE",
            }

        print("IDEMPOTENT_SETUP_OK", NOTEBOOK_ID)
        """
    if spec.live_kind == "none":
        source = source.replace("        import subprocess\n", "")
    if spec.carries_raac_matrix:
        source += """
        from causal_agent_bench.raac.kaggle import (  # noqa: E402
            load_raac_kaggle_matrix,
            materialize_raac_kaggle_config,
        )

        RAAC_MATRIX = load_raac_kaggle_matrix(REPO_ROOT / RAAC_MATRIX_CONFIG_PATH)
        if set(RAAC_PRIMARY_ARMS) != set(RAAC_MATRIX["primary_arms"]):
            raise RuntimeError("notebook RAAC primary arms differ from the frozen matrix")
        if set(RAAC_ABLATION_ARMS) != set(RAAC_MATRIX["ablation_arms"]):
            raise RuntimeError("notebook RAAC ablations differ from the frozen matrix")
        if set(RAAC_BUDGET_MODES) != set(RAAC_MATRIX["budget_modes"]):
            raise RuntimeError("notebook RAAC budget modes differ from the frozen matrix")
        if set(RAAC_REQUIRED_COMPUTE_FIELDS) != set(RAAC_MATRIX["required_compute_fields"]):
            raise RuntimeError("notebook RAAC compute fields differ from the frozen matrix")
        if RAAC_SELECTED_BUDGET_MODE not in RAAC_BUDGET_MODES:
            raise RuntimeError("selected RAAC budget mode is not declared")
        """
    return _code_cell(source, "setup")


def _preflight_cell() -> dict[str, object]:
    return _code_cell(
        """
        # CAB_ROLE: preflight - inventory only; package presence checks do not import ML stacks.
        VALIDATOR_MODE = os.environ.get("CAB_NOTEBOOK_VALIDATE") == "1"
        PREFLIGHT = runtime_preflight(
            REPO_ROOT,
            probe_internet=CHECK_INTERNET and not VALIDATOR_MODE,
        )
        LIVE_WORKER_PLAN = choose_worker_count(
            int(PREFLIGHT["gpu_count"]),
            requested_workers=REQUESTED_GPU_WORKERS,
        )
        if MODEL_PLACEMENT_MODE == "two_gpu_placement":
            if (
                int(PREFLIGHT["gpu_count"]) >= 2
                and TWO_GPU_PLACEMENT_ADAPTER_AUDITED is True
            ):
                LIVE_WORKER_PLAN = {
                    "requested_workers": REQUESTED_GPU_WORKERS,
                    "active_workers": 1,
                    "gpu_count": int(PREFLIGHT["gpu_count"]),
                    "parallel_mode": "optional_two_gpu_model_placement",
                    "single_gpu_fallback": False,
                    "worker_to_gpu": {"0": [0, 1]},
                }
        MODEL_SNAPSHOT = model_snapshot_record(os.environ.get(MODEL_SNAPSHOT_ENV))
        visible_vram_gib = [
            round(float(gpu["memory_total_mib"]) / 1024, 3)
            for gpu in PREFLIGHT["gpus"]
            if gpu.get("memory_total_mib") is not None
        ]

        input_status = []
        for relative in REQUIRED_REPOSITORY_INPUTS:
            target = REPO_ROOT / relative
            input_status.append(
                {
                    "path": relative.as_posix(),
                    "exists": target.exists(),
                    "kind": "directory" if target.is_dir() else "file",
                }
            )
        PREFLIGHT["live_worker_plan"] = LIVE_WORKER_PLAN
        PREFLIGHT["model_load_policy"] = MODEL_LOAD_POLICY
        PREFLIGHT["model_estimated_vram_gib"] = MODEL_ESTIMATED_VRAM_GIB
        PREFLIGHT["model_quantization_mode"] = MODEL_QUANTIZATION_MODE
        PREFLIGHT["model_placement_mode"] = MODEL_PLACEMENT_MODE
        PREFLIGHT["visible_vram_gib"] = visible_vram_gib
        PREFLIGHT["model_snapshot"] = MODEL_SNAPSHOT
        PREFLIGHT["required_repository_inputs"] = input_status
        PREFLIGHT["actionable_live_failures"] = []
        PREFLIGHT["warnings"] = []
        if SUPPORTS_REAL_ARTIFACTS and LIVE_KIND in {"runner", "recovery"}:
            missing_inputs = [row["path"] for row in input_status if not row["exists"]]
            if missing_inputs:
                PREFLIGHT["actionable_live_failures"].append(
                    "Missing required repository inputs: " + ", ".join(missing_inputs)
                )
            if int(PREFLIGHT["gpu_count"]) == 0:
                PREFLIGHT["actionable_live_failures"].append(
                    "No NVIDIA GPU is visible; attach a GPU accelerator before live execution."
                )
            missing_packages = [
                name
                for name in ("torch", "transformers")
                if not bool(PREFLIGHT["packages"].get(name))
            ]
            if missing_packages:
                PREFLIGHT["actionable_live_failures"].append(
                    "Missing packages: " + ", ".join(missing_packages)
                )
            if not MODEL_SNAPSHOT["exists"]:
                PREFLIGHT["actionable_live_failures"].append(
                    "Set CAB_LOCAL_MODEL_SNAPSHOT to an attached, approved offline model directory."
                )
            if MODEL_ESTIMATED_VRAM_GIB is None:
                PREFLIGHT["actionable_live_failures"].append(
                    "Set MODEL_ESTIMATED_VRAM_GIB from the approved model card before activation."
                )
            elif visible_vram_gib and max(visible_vram_gib) < float(MODEL_ESTIMATED_VRAM_GIB):
                if MODEL_QUANTIZATION_MODE == "4bit":
                    if not bool(PREFLIGHT["packages"].get("bitsandbytes")):
                        PREFLIGHT["actionable_live_failures"].append(
                            "The selected 4-bit route requires an installed bitsandbytes package."
                        )
                elif MODEL_PLACEMENT_MODE == "two_gpu_placement":
                    if int(PREFLIGHT["gpu_count"]) < 2:
                        PREFLIGHT["actionable_live_failures"].append(
                            "Two-GPU placement requires two visible GPUs."
                        )
                    if TWO_GPU_PLACEMENT_ADAPTER_AUDITED is not True:
                        PREFLIGHT["actionable_live_failures"].append(
                            "Two-GPU placement requires a separately audited adapter."
                        )
                else:
                    PREFLIGHT["actionable_live_failures"].append(
                        "Estimated fp16 memory exceeds one GPU: select the approved 4-bit route, "
                        "audited two-GPU placement, or a smaller model."
                    )
            if MODEL_PLACEMENT_MODE not in {"single_gpu", "two_gpu_placement"}:
                PREFLIGHT["actionable_live_failures"].append(
                    "MODEL_PLACEMENT_MODE must be single_gpu or two_gpu_placement."
                )
            if MODEL_QUANTIZATION_MODE not in {"none", "4bit"}:
                PREFLIGHT["actionable_live_failures"].append(
                    "MODEL_QUANTIZATION_MODE must be none or 4bit."
                )
        if bool(LIVE_WORKER_PLAN["single_gpu_fallback"]):
            PREFLIGHT["warnings"].append(
                "T4x2 unavailable; live plan will use one isolated worker when one GPU exists."
            )

        write_json(NOTEBOOK_OUTPUT_DIR / "runtime_preflight.json", PREFLIGHT)
        write_json(NOTEBOOK_OUTPUT_DIR / "model_snapshot_record.json", MODEL_SNAPSHOT)
        print(
            "PREFLIGHT_COMPLETE",
            {
                "gpu_count": PREFLIGHT["gpu_count"],
                "cuda_status": PREFLIGHT["cuda_status"],
                "cuda_version": PREFLIGHT["cuda_version"],
                "internet_status": PREFLIGHT["internet_status"],
                "live_workers": LIVE_WORKER_PLAN["active_workers"],
            },
        )
        """,
        "preflight",
    )


def _fixture_sharding_cell() -> dict[str, object]:
    return _code_cell(
        """
        # CAB_ROLE: fixture_sharding - exactly two CPU-safe mechanics shards for validation.
        FIXTURE_ITEMS = build_fixture_work_items(NOTEBOOK_ID, OFFLINE_FIXTURE_ITEMS)
        FIXTURE_ITEM_IDS = {str(row["item_id"]) for row in FIXTURE_ITEMS}
        FIXTURE_SHARDS = deterministic_shards(
            FIXTURE_ITEMS,
            worker_count=FIXTURE_WORKERS,
        )
        assert_shards_complete_and_disjoint(
            FIXTURE_SHARDS,
            expected_ids=FIXTURE_ITEM_IDS,
        )
        write_jsonl(FIXTURE_ROOT / "inputs" / "fixture_work_items.jsonl", FIXTURE_ITEMS)
        write_json(
            FIXTURE_ROOT / "inputs" / "shard_plan.json",
            {
                "evidence_class": FIXTURE_EVIDENCE_CLASS,
                "strategy": "stable_sort_round_robin",
                "worker_count": FIXTURE_WORKERS,
                "worker_to_item_ids": {
                    str(worker): [str(row["item_id"]) for row in shard]
                    for worker, shard in enumerate(FIXTURE_SHARDS)
                },
            },
        )
        print("FIXTURE_SHARDS_DISJOINT_AND_COMPLETE", [len(shard) for shard in FIXTURE_SHARDS])
        """,
        "fixture_sharding",
    )


def _checkpoint_cell(spec: NotebookSpec) -> dict[str, object]:
    first_pass = "1" if spec.live_kind == "recovery" else "None"
    return _code_cell(
        f"""
        # CAB_ROLE: checkpoint_resume - mechanics receipts only; never model-shaped output.
        FIRST_PASS_RESULTS = []
        RESUME_RESULTS = []
        IDEMPOTENCE_RESULTS = []
        for worker_id, shard in enumerate(FIXTURE_SHARDS):
            first = run_fixture_worker(
                FIXTURE_ROOT,
                worker_id=worker_id,
                rows=shard,
                max_new_items={first_pass},
            )
            FIRST_PASS_RESULTS.append(first)
            resumed = run_fixture_worker(
                FIXTURE_ROOT,
                worker_id=worker_id,
                rows=shard,
            )
            RESUME_RESULTS.append(resumed)
            repeated = run_fixture_worker(
                FIXTURE_ROOT,
                worker_id=worker_id,
                rows=shard,
            )
            IDEMPOTENCE_RESULTS.append(repeated)
            if repeated["processed_this_call"] != 0:
                raise AssertionError("completed fixture work was not skipped on idempotent resume")

        FIXTURE_MERGE_REPORT = merge_fixture_shards(
            FIXTURE_ROOT,
            expected_item_ids=FIXTURE_ITEM_IDS,
            worker_count=FIXTURE_WORKERS,
        )
        if FIXTURE_MERGE_REPORT["merged"] != len(FIXTURE_ITEM_IDS):
            raise AssertionError("fixture merge did not cover every expected item")
        print(
            "CHECKPOINT_RESUME_MERGE_OK",
            {{
                "first_pass": [row["processed_this_call"] for row in FIRST_PASS_RESULTS],
                "resume": [row["processed_this_call"] for row in RESUME_RESULTS],
                "repeat": [row["processed_this_call"] for row in IDEMPOTENCE_RESULTS],
            }},
        )
        """,
        "checkpoint_resume",
    )


def _activation_cell() -> dict[str, object]:
    return _code_cell(
        """
        # CAB_ROLE: activation_guard - fail closed before any real-artifact subprocess.
        activation_reasons = []
        if RUN_LIVE is not True:
            activation_reasons.append("RUN_LIVE is not the literal boolean True")
        if LIVE_CONFIRMATION != REQUIRED_LIVE_CONFIRMATION:
            activation_reasons.append("LIVE_CONFIRMATION does not match the required phrase")
        if os.environ.get(ACTIVATION_ENV) != "YES":
            activation_reasons.append(f"{ACTIVATION_ENV} is not YES")
        if not SUPPORTS_REAL_ARTIFACTS:
            activation_reasons.append("this notebook never operates on real artifacts")
        if not APPROVAL_RECEIPT.is_absolute():
            approval_path = REPO_ROOT / APPROVAL_RECEIPT
        else:
            approval_path = APPROVAL_RECEIPT
        if not approval_path.is_file():
            activation_reasons.append("cryptographic approval receipt is missing")
        else:
            from causal_agent_bench.safety.approval_receipt import verify_approval_receipt
            approval_verification = verify_approval_receipt(
                approval_path,
                repo_root=REPO_ROOT,
                allowed_scope="scientific",
            )
            if not approval_verification["passed"]:
                activation_reasons.append(
                    "cryptographic approval receipt is invalid: "
                    + ",".join(approval_verification["errors"])
                )

        if LIVE_KIND == "runner":
            if LIVE_CONFIG_PATH is None:
                activation_reasons.append("live config path is not configured")
            else:
                config_path = LIVE_CONFIG_PATH if LIVE_CONFIG_PATH.is_absolute() else REPO_ROOT / LIVE_CONFIG_PATH
                if not config_path.is_file():
                    activation_reasons.append("live config is missing")
                else:
                    config_text = config_path.read_text(encoding="utf-8").lower()
                    if "template_only: true" in config_text:
                        activation_reasons.append("template-only config cannot run")
                    if "approval_receipt_path:" not in config_text:
                        activation_reasons.append("config lacks approval_receipt_path binding")
                    if "allow_paid_calls: false" not in config_text:
                        activation_reasons.append("open-model config must explicitly forbid paid calls")
                    if "api_key_env:" in config_text:
                        activation_reasons.append(
                            "open-model Kaggle config must not request a credential variable"
                        )
                    forbidden_providers = (
                        "provider: openai",
                        "provider: anthropic",
                        "provider: gemini",
                        "provider: openrouter",
                    )
                    if any(provider in config_text for provider in forbidden_providers):
                        activation_reasons.append(
                            "open-model Kaggle config contains an external provider"
                        )
                    if not (
                        config_text.lstrip().startswith("seed:")
                        or "\\nseed:" in config_text
                    ):
                        activation_reasons.append("live config lacks a deterministic seed")
        if LIVE_KIND in {"runner", "recovery"}:
            if int(PREFLIGHT["gpu_count"]) == 0:
                activation_reasons.append("no NVIDIA GPU is visible")
            if REQUIRES_MODEL_SNAPSHOT and not bool(MODEL_SNAPSHOT["exists"]):
                activation_reasons.append("approved offline model snapshot is not configured")
            for failure in PREFLIGHT["actionable_live_failures"]:
                if failure not in activation_reasons:
                    activation_reasons.append(str(failure))
        if LIVE_KIND in {"merge", "recovery"}:
            live_batch_raw = os.environ.get("CAB_LIVE_BATCH_DIR", LIVE_BATCH_DIR_SETTING)
            LIVE_BATCH_DIR = Path(live_batch_raw).expanduser()
            if not LIVE_BATCH_DIR.is_absolute():
                LIVE_BATCH_DIR = REPO_ROOT / LIVE_BATCH_DIR
            live_manifest_path = LIVE_BATCH_DIR / "batch_manifest.json"
            if not live_manifest_path.is_file():
                activation_reasons.append("batch_manifest.json is missing from CAB_LIVE_BATCH_DIR")
            elif LIVE_KIND == "recovery":
                try:
                    live_manifest = read_json(live_manifest_path)
                except (OSError, ValueError) as error:
                    activation_reasons.append(
                        "recovery batch manifest is unreadable: " + type(error).__name__
                    )
                else:
                    shard_rows = live_manifest.get("shards", [])
                    shard_ids = [str(row.get("shard_id", "")) for row in shard_rows]
                    if not shard_ids or "" in shard_ids or len(shard_ids) != len(set(shard_ids)):
                        activation_reasons.append("recovery batch has invalid or duplicate shard IDs")
                    missing_shard_configs = [
                        shard_id
                        for shard_id in shard_ids
                        if not (LIVE_BATCH_DIR / "shards" / shard_id / "config.yaml").is_file()
                    ]
                    if missing_shard_configs:
                        activation_reasons.append(
                            "recovery shard configs are missing: "
                            + ", ".join(missing_shard_configs)
                        )
        else:
            LIVE_BATCH_DIR = NOTEBOOK_OUTPUT_DIR / "live_batch"

        LIVE_AUTHORIZED = not activation_reasons
        if RUN_LIVE and not LIVE_AUTHORIZED:
            raise RuntimeError("LIVE_EXECUTION_REFUSED: " + "; ".join(activation_reasons))
        if not LIVE_AUTHORIZED:
            print("LIVE_EXECUTION_REFUSED", activation_reasons)
        else:
            print("LIVE_EXECUTION_EXPLICITLY_AUTHORIZED")
        """,
        "activation_guard",
    )


def _runner_live_cell(spec: NotebookSpec) -> dict[str, object]:
    raac_materialization = ""
    if spec.carries_raac_matrix:
        raac_materialization = """            config_path = materialize_raac_kaggle_config(
                config_path,
                live_batch_root / "selected_raac_config.yaml",
                comparison_mode=RAAC_SELECTED_BUDGET_MODE,
            )

"""
    source = """
        # CAB_ROLE: live_plan - unreachable on run-all defaults; starts real inference if authorized.
        LIVE_EXECUTED = False
        LIVE_COMMANDS = []
        LIVE_INTEGRITY = {"performed": False, "ok": None}
        if LIVE_AUTHORIZED:
            config_path = LIVE_CONFIG_PATH if LIVE_CONFIG_PATH.is_absolute() else REPO_ROOT / LIVE_CONFIG_PATH
            live_batch_root = NOTEBOOK_OUTPUT_DIR / "live_batch"
            live_batch_root.mkdir(parents=True, exist_ok=True)
__RAAC_MATERIALIZATION__            active_workers = int(LIVE_WORKER_PLAN["active_workers"])
            plan_command = [
                sys.executable,
                "-m",
                "causal_agent_bench",
                "batch-plan",
                "--config",
                str(config_path),
                "--shard-by",
                "instance",
                "--shard-count",
                str(active_workers),
                "--output-dir",
                str(live_batch_root),
            ]
            LIVE_COMMANDS.append(plan_command)
            base_environment = sanitized_subprocess_environment()
            subprocess.run(plan_command, cwd=REPO_ROOT, env=base_environment, check=True)

            processes = []
            log_handles = []
            try:
                for worker_id in range(active_workers):
                    shard_dir = live_batch_root / "shards" / f"shard_{worker_id:03d}"
                    shard_config = shard_dir / "config.yaml"
                    worker_command = [
                        sys.executable,
                        "-m",
                        "causal_agent_bench",
                        "run",
                        "--config",
                        str(shard_config),
                        "--checkpoint-every",
                        "1",
                    ]
                    run_root = shard_dir / "run"
                    prior_runs = (
                        sorted(
                            (path for path in run_root.iterdir() if path.is_dir()),
                            key=lambda path: path.stat().st_mtime,
                            reverse=True,
                        )
                        if run_root.is_dir()
                        else []
                    )
                    if prior_runs:
                        worker_command.extend(["--resume", str(prior_runs[0]), "--retry-failed"])
                    worker_environment = base_environment.copy()
                    if LIVE_WORKER_PLAN["parallel_mode"] == "optional_two_gpu_model_placement":
                        worker_environment["CUDA_VISIBLE_DEVICES"] = "0,1"
                    else:
                        worker_environment["CUDA_VISIBLE_DEVICES"] = str(worker_id)
                    log_path = shard_dir / "worker.log"
                    log_handle = log_path.open("a", encoding="utf-8")
                    log_handles.append(log_handle)
                    LIVE_COMMANDS.append(worker_command)
                    processes.append(
                        subprocess.Popen(
                            worker_command,
                            cwd=REPO_ROOT,
                            env=worker_environment,
                            stdout=log_handle,
                            stderr=subprocess.STDOUT,
                            text=True,
                        )
                    )
                return_codes = [process.wait() for process in processes]
            finally:
                for log_handle in log_handles:
                    log_handle.close()
            if any(code != 0 for code in return_codes):
                raise RuntimeError(f"one or more live workers failed: {return_codes}")

            merge_command = [
                sys.executable,
                "-m",
                "causal_agent_bench",
                "batch-merge",
                "--batch-dir",
                str(live_batch_root),
                "--no-score",
            ]
            LIVE_COMMANDS.append(merge_command)
            subprocess.run(merge_command, cwd=REPO_ROOT, env=base_environment, check=True)
            LIVE_INTEGRITY = write_live_integrity_manifest(live_batch_root)
            LIVE_EXECUTED = True
        else:
            print("NO_LIVE_COMMAND_EXECUTED")
        """
    return _code_cell(
        source.replace("__RAAC_MATERIALIZATION__", raac_materialization),
        "live_plan",
    )


def _merge_live_cell() -> dict[str, object]:
    return _code_cell(
        """
        # CAB_ROLE: live_plan - strict merge must pass before the canonical scorer is invoked.
        LIVE_EXECUTED = False
        LIVE_COMMANDS = []
        LIVE_INTEGRITY = {"performed": False, "ok": None}
        if LIVE_AUTHORIZED:
            base_environment = sanitized_subprocess_environment()
            merge_command = [
                sys.executable,
                "-m",
                "causal_agent_bench",
                "batch-merge",
                "--batch-dir",
                str(LIVE_BATCH_DIR),
                "--no-score",
            ]
            LIVE_COMMANDS.append(merge_command)
            subprocess.run(merge_command, cwd=REPO_ROOT, env=base_environment, check=True)

            merge_manifest_path = LIVE_BATCH_DIR / "merged" / "merge_manifest.json"
            merge_manifest = read_json(merge_manifest_path)
            merged_run = Path(str(merge_manifest["merged_run_dir"]))
            merge_report = read_json(merged_run / "merge_report.json")
            audit_failures = {
                key: int(merge_report.get(key, 0))
                for key in ("n_duplicate_keys", "n_missing_keys", "n_extra_keys")
            }
            if any(audit_failures.values()):
                raise RuntimeError(f"strict merge audit refused scoring: {audit_failures}")

            failure_command = [
                sys.executable,
                "-m",
                "causal_agent_bench",
                "failure-report",
                "--run-dir",
                str(merged_run),
            ]
            score_command = [
                sys.executable,
                "-m",
                "causal_agent_bench",
                "score",
                "--run-dir",
                str(merged_run),
            ]
            LIVE_COMMANDS.extend([failure_command, score_command])
            subprocess.run(failure_command, cwd=REPO_ROOT, env=base_environment, check=True)
            subprocess.run(score_command, cwd=REPO_ROOT, env=base_environment, check=True)
            LIVE_INTEGRITY = write_live_integrity_manifest(LIVE_BATCH_DIR / "merged")
            LIVE_EXECUTED = True
        else:
            print("NO_REAL_ARTIFACT_MERGE_OR_SCORE_EXECUTED")
        """,
        "live_plan",
    )


def _recovery_live_cell() -> dict[str, object]:
    return _code_cell(
        """
        # CAB_ROLE: live_plan - resume existing shard configs; never repartition an interrupted batch.
        LIVE_EXECUTED = False
        LIVE_COMMANDS = []
        LIVE_INTEGRITY = {"performed": False, "ok": None}
        if LIVE_AUTHORIZED:
            manifest = read_json(LIVE_BATCH_DIR / "batch_manifest.json")
            shard_rows = sorted(manifest.get("shards", []), key=lambda row: int(row["shard_index"]))
            if not shard_rows:
                raise RuntimeError("batch manifest contains no shards")
            available_gpus = max(1, int(PREFLIGHT["gpu_count"]))
            recovery_log_dir = LIVE_BATCH_DIR / "recovery_logs"
            recovery_log_dir.mkdir(parents=True, exist_ok=True)
            base_environment = sanitized_subprocess_environment()

            worker_jobs = []
            for position, shard in enumerate(shard_rows):
                shard_index = int(shard["shard_index"])
                shard_dir = LIVE_BATCH_DIR / "shards" / str(shard["shard_id"])
                shard_config = shard_dir / "config.yaml"
                run_root = shard_dir / "run"
                prior_runs = (
                    sorted(
                        (path for path in run_root.iterdir() if path.is_dir()),
                        key=lambda path: path.stat().st_mtime,
                        reverse=True,
                    )
                    if run_root.is_dir()
                    else []
                )
                worker_command = [
                    sys.executable,
                    "-m",
                    "causal_agent_bench",
                    "run",
                    "--config",
                    str(shard_config),
                    "--checkpoint-every",
                    "1",
                ]
                if prior_runs:
                    worker_command.extend(["--resume", str(prior_runs[0]), "--retry-failed"])
                worker_environment = base_environment.copy()
                if LIVE_WORKER_PLAN["parallel_mode"] == "optional_two_gpu_model_placement":
                    worker_environment["CUDA_VISIBLE_DEVICES"] = "0,1"
                else:
                    worker_environment["CUDA_VISIBLE_DEVICES"] = str(position % available_gpus)
                worker_jobs.append(
                    (
                        worker_command,
                        worker_environment,
                        recovery_log_dir / f"shard_{shard_index:03d}.log",
                    )
                )
                LIVE_COMMANDS.append(worker_command)

            if LIVE_WORKER_PLAN["parallel_mode"] == "optional_two_gpu_model_placement":
                return_codes = []
                for worker_command, worker_environment, log_path in worker_jobs:
                    with log_path.open("a", encoding="utf-8") as log_handle:
                        result = subprocess.run(
                            worker_command,
                            cwd=REPO_ROOT,
                            env=worker_environment,
                            stdout=log_handle,
                            stderr=subprocess.STDOUT,
                            text=True,
                            check=False,
                        )
                    return_codes.append(result.returncode)
            else:
                processes = []
                log_handles = []
                try:
                    for worker_command, worker_environment, log_path in worker_jobs:
                        log_handle = log_path.open("a", encoding="utf-8")
                        log_handles.append(log_handle)
                        processes.append(
                            subprocess.Popen(
                                worker_command,
                                cwd=REPO_ROOT,
                                env=worker_environment,
                                stdout=log_handle,
                                stderr=subprocess.STDOUT,
                                text=True,
                            )
                        )
                    return_codes = [process.wait() for process in processes]
                finally:
                    for log_handle in log_handles:
                        log_handle.close()
            if any(code != 0 for code in return_codes):
                raise RuntimeError(f"recovery workers still failed: {return_codes}")

            merge_command = [
                sys.executable,
                "-m",
                "causal_agent_bench",
                "batch-merge",
                "--batch-dir",
                str(LIVE_BATCH_DIR),
                "--no-score",
            ]
            LIVE_COMMANDS.append(merge_command)
            subprocess.run(merge_command, cwd=REPO_ROOT, env=base_environment, check=True)
            LIVE_INTEGRITY = write_live_integrity_manifest(LIVE_BATCH_DIR)
            LIVE_EXECUTED = True
        else:
            print("NO_FAILURE_RECOVERY_EXECUTED")
        """,
        "live_plan",
    )


def _none_live_cell() -> dict[str, object]:
    return _code_cell(
        """
        # CAB_ROLE: live_plan - this notebook intentionally has no real-execution path.
        LIVE_EXECUTED = False
        LIVE_COMMANDS = []
        LIVE_INTEGRITY = {"performed": False, "ok": None}
        if LIVE_AUTHORIZED:
            raise RuntimeError("this notebook is offline/preflight-only by contract")
        print("NO_LIVE_INFERENCE_PATH_PRESENT")
        """,
        "live_plan",
    )


def _live_cell(spec: NotebookSpec) -> dict[str, object]:
    if spec.live_kind == "runner":
        return _runner_live_cell(spec)
    if spec.live_kind == "merge":
        return _merge_live_cell()
    if spec.live_kind == "recovery":
        return _recovery_live_cell()
    return _none_live_cell()


def _export_cell(spec: NotebookSpec) -> dict[str, object]:
    return _code_cell(
        f"""
        # CAB_ROLE: export_integrity - fixture export only on defaults.
        NOTEBOOK_STATUS = {{
            "notebook_id": NOTEBOOK_ID,
            "evidence_class": FIXTURE_EVIDENCE_CLASS,
            "offline_fixture_status": FIXTURE_MERGE_REPORT["status"],
            "live_authorized": LIVE_AUTHORIZED,
            "live_executed": LIVE_EXECUTED,
            "live_integrity": LIVE_INTEGRITY,
            "claim_promotion_allowed": False,
            "paper_asset_eligible": False,
        }}
        if LIVE_EXECUTED and LIVE_INTEGRITY.get("ok") is not True:
            raise RuntimeError("real-artifact session ended without a passing integrity manifest")
        write_json(FIXTURE_ROOT / "notebook_status.json", NOTEBOOK_STATUS)
        FIXTURE_INTEGRITY_MANIFEST = write_integrity_manifest(FIXTURE_ROOT)
        FINAL_INTEGRITY = verify_integrity_manifest(FIXTURE_ROOT)
        if not FINAL_INTEGRITY["ok"]:
            raise RuntimeError("fixture integrity verification failed: " + repr(FINAL_INTEGRITY))
        ARCHIVE_PATH = export_fixture_archive(
            FIXTURE_ROOT,
            NOTEBOOK_OUTPUT_DIR / "{spec.stem}_FIXTURE_ONLY",
        )
        print(
            "FINAL_FIXTURE_INTEGRITY_PASS",
            {{
                "checked_files": FINAL_INTEGRITY["checked_files"],
                "archive_name": ARCHIVE_PATH.name,
                "evidence_class": FIXTURE_EVIDENCE_CLASS,
            }},
        )
        """,
        "export_integrity",
    )


def _final_cell(spec: NotebookSpec) -> dict[str, object]:
    return _markdown_cell(
        f"""
        ## Final status and export instructions

        A successful default run proves only the repository-controlled fixture mechanics for
        `{spec.stem}`. Download `{spec.stem}_FIXTURE_ONLY.zip` with
        `integrity_manifest.json`; verify every listed SHA-256 after transfer. Do not import the
        fixture archive into a results directory or claim ledger.

        For a later approved real-artifact session, edit only the configuration cell, attach
        immutable inputs, satisfy the repository approval record, set the non-secret activation
        environment marker, and enter the exact confirmation phrase. A live run remains
        `PRELIMINARY_REAL_EVIDENCE` at most until independent merge, completeness, scorer sanity,
        human-review, evidence-promotion, and claim-ledger gates pass. Third-party model or package
        availability is never guaranteed by this offline validation.
        """,
        "final_status",
    )


def build_notebook(spec: NotebookSpec) -> dict[str, object]:
    cells = [
        _purpose_cell(spec),
        _configuration_cell(spec),
        _setup_cell(spec),
        _preflight_cell(),
        _fixture_sharding_cell(),
        _checkpoint_cell(spec),
        _activation_cell(),
        _live_cell(spec),
        _export_cell(spec),
        _final_cell(spec),
    ]
    for cell in cells:
        metadata = cell["metadata"]
        if not isinstance(metadata, dict):
            raise TypeError("generated cell metadata must be a dictionary")
        role = str(metadata["cab_role"])
        cell["id"] = f"cab-{role.replace('_', '-')}"
    return {
        "cells": cells,
        "metadata": {
            "cab_notebook_contract": {
                "version": 1,
                "evidence_default": "FIXTURE_ONLY",
                "live_default": False,
                "parallel_default": "GPU_T4X2_DATA_PARALLEL",
                "single_gpu_fallback": True,
            },
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "name": "python",
                "version": "3.11",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def write_notebooks(*, check: bool = False) -> list[Path]:
    if check:
        if not NOTEBOOK_DIR.is_dir():
            raise SystemExit(f"generated notebook directory is missing: {NOTEBOOK_DIR}")
    else:
        NOTEBOOK_DIR.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for spec in SPECS:
        path = NOTEBOOK_DIR / f"{spec.stem}.ipynb"
        rendered = json.dumps(build_notebook(spec), indent=1, ensure_ascii=False) + "\n"
        if check:
            if not path.is_file() or path.read_text(encoding="utf-8") != rendered:
                raise SystemExit(f"generated notebook is stale: {path.relative_to(REPO_ROOT)}")
        else:
            path.write_text(rendered, encoding="utf-8")
        paths.append(path)
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail when committed notebook JSON differs from this generator.",
    )
    args = parser.parse_args()
    paths = write_notebooks(check=args.check)
    action = "verified" if args.check else "wrote"
    print(f"{action} {len(paths)} Kaggle notebooks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
