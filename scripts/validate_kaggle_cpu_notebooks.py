#!/usr/bin/env python3
"""Validate the Kaggle CPU notebooks statically, and optionally run them offline.

Static validation checks the things that silently break a notebook between the
laptop it was written on and the Kaggle session it runs in: stale committed
outputs, a notebook that no longer matches its generator, a cell that imports a
model library into a CPU lane, and — the one this project keeps having to
relearn — any dependence on an input's filename.

``--execute-offline`` goes further and actually runs the safe lanes against a
real bundle whose archive has been given a random name, which is the only way to
prove the filename independence rather than assert it.
"""

from __future__ import annotations

import argparse
import ast
import json
import secrets
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

NOTEBOOK_DIR = REPO_ROOT / "notebooks" / "kaggle_cpu"

#: Lanes that can run offline with only a repository bundle attached.  The rest
#: need a genuine run-output bundle and are validated statically only.
OFFLINE_EXECUTABLE_LANES = ("input_preflight", "c10_audit")

#: Substrings that would make a CPU notebook do GPU or provider work.
FORBIDDEN_IMPORTS = (
    "import torch",
    "import transformers",
    "import vllm",
    "from transformers",
    "import openai",
    "import anthropic",
)

#: Literal filename patterns a notebook must never match an input on.  Finding
#: any of these means discovery has been bypassed.
FORBIDDEN_FILENAME_DEPENDENCE = (
    'glob("*/pyproject.toml")',
    "glob('*/pyproject.toml')",
    "CAB_KAGGLE_CPU_PREEXECUTION_INPUT_",
    "/kaggle/input/cab",
)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def notebook_python(notebook: dict[str, Any]) -> str:
    return "\n".join(
        "".join(cell["source"]) for cell in notebook["cells"] if cell["cell_type"] == "code"
    )


def validate_one(path: Path) -> dict[str, Any]:
    notebook = load(path)
    cells = notebook["cells"]
    code_cells = [cell for cell in cells if cell["cell_type"] == "code"]
    source = notebook_python(notebook)

    try:
        ast.parse(source)
        parses = True
        syntax_error = None
    except SyntaxError as error:
        parses = False
        syntax_error = f"{error.msg} at line {error.lineno}"

    roles = [cell.get("metadata", {}).get("cab_role") for cell in code_cells]
    checks = {
        "nbformat_is_4": notebook.get("nbformat") == 4,
        "declares_the_cpu_accelerator": notebook["metadata"].get("cab_accelerator") == "cpu",
        "declares_a_lane": bool(notebook["metadata"].get("cab_lane")),
        "every_cell_has_no_execution_count": all(
            cell.get("execution_count") is None for cell in code_cells
        ),
        "every_cell_has_empty_outputs": all(cell.get("outputs") == [] for cell in code_cells),
        "extracted_python_parses": parses,
        "has_a_configuration_cell": "configuration" in roles,
        "has_a_bootstrap_cell": "bootstrap" in roles,
        "has_an_integrity_cell": "integrity" in roles,
        "has_an_export_cell": "export" in roles,
        "has_a_failure_export_cell": "failure_export" in roles,
        "uses_content_based_discovery": "discover_kaggle_input(" in source,
        "declares_run_live_false": "RUN_LIVE = False" in source,
        "imports_no_model_library": not any(
            marker in source for marker in FORBIDDEN_IMPORTS
        ),
        "depends_on_no_input_filename": not any(
            marker in source for marker in FORBIDDEN_FILENAME_DEPENDENCE
        ),
        "produces_an_output_archive": "build_output_archive(" in source,
        "documents_that_renaming_is_safe": any(
            "rename" in "".join(cell["source"]).casefold()
            for cell in cells
            if cell["cell_type"] == "markdown"
        ),
    }
    failed = sorted(name for name, ok in checks.items() if not ok)
    return {
        "notebook": str(path.relative_to(REPO_ROOT)),
        "lane": notebook["metadata"].get("cab_lane"),
        "code_cell_count": len(code_cells),
        "checks": checks,
        "failed": failed,
        "syntax_error": syntax_error,
        "passed": not failed,
    }


def validate_all() -> dict[str, Any]:
    notebooks = sorted(NOTEBOOK_DIR.glob("*.ipynb"))
    if not notebooks:
        raise SystemExit(f"no notebooks found under {NOTEBOOK_DIR}")
    results = [validate_one(path) for path in notebooks]
    stale = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "build_kaggle_cpu_notebooks.py"), "--check"],
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "schema_version": "cab_kaggle_cpu_notebook_validation_v1",
        "notebook_count": len(results),
        "results": results,
        "generator_is_current": stale.returncode == 0,
        "generator_message": stale.stdout.strip() or stale.stderr.strip(),
        "passed": all(row["passed"] for row in results) and stale.returncode == 0,
    }


# --------------------------------------------------------------------------
# offline execution
# --------------------------------------------------------------------------


def _newest_bundle() -> Path:
    bundles = sorted((REPO_ROOT / "dist" / "kaggle_inputs").glob("*.zip"))
    if not bundles:
        raise SystemExit(
            "no input bundle to execute against. Build one first:\n"
            "  python3 scripts/build_kaggle_input_bundles.py --bundle-type cpu-preexecution"
        )
    return max(bundles, key=lambda path: path.stat().st_mtime)


def execute_offline(lane_filter: tuple[str, ...] = OFFLINE_EXECUTABLE_LANES) -> dict[str, Any]:
    """Run the safe lanes against a bundle with a deliberately random filename."""

    bundle = _newest_bundle()
    results: list[dict[str, Any]] = []
    for path in sorted(NOTEBOOK_DIR.glob("*.ipynb")):
        notebook = load(path)
        lane = notebook["metadata"].get("cab_lane")
        if lane not in lane_filter:
            results.append({"notebook": path.name, "lane": lane, "status": "skipped_needs_run_output"})
            continue

        with tempfile.TemporaryDirectory() as raw:
            sandbox = Path(raw)
            # A random dataset name and a random archive name, every run.
            dataset = sandbox / "input" / f"ds-{secrets.token_hex(5)}" / f"sub-{secrets.token_hex(3)}"
            dataset.mkdir(parents=True)
            renamed = dataset / f"{secrets.token_hex(8)} renamed ({secrets.token_hex(2)}).ZIP"
            shutil.copy(bundle, renamed)
            working = sandbox / "working"
            working.mkdir()

            script = notebook_python(notebook)
            script = script.replace('INPUT_ROOT = "/kaggle/input"', f"INPUT_ROOT = {str(sandbox / 'input')!r}")
            script = script.replace('WORKING_ROOT = "/kaggle/working"', f"WORKING_ROOT = {str(working)!r}")
            # The trailing failure-export cell is only meant to run after a failure.
            script = script.split("# CAB_ROLE: failure_export")[0]

            runner = sandbox / "runner.py"
            runner.write_text(script)
            completed = subprocess.run(
                [sys.executable, str(runner)],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
                timeout=900,
            )
            archives = sorted(working.glob("CAB_*.zip"))
            results.append(
                {
                    "notebook": path.name,
                    "lane": lane,
                    "status": "passed" if completed.returncode == 0 else "failed",
                    "returncode": completed.returncode,
                    "randomised_archive_name": renamed.name,
                    "output_archive": archives[0].name if archives else None,
                    "stdout_tail": completed.stdout[-1500:],
                    "stderr_tail": completed.stderr[-2000:] if completed.returncode else "",
                }
            )
    executed = [row for row in results if row["status"] in ("passed", "failed")]
    return {
        "schema_version": "cab_kaggle_cpu_notebook_offline_execution_v1",
        "bundle": bundle.name,
        "executed_count": len(executed),
        "results": results,
        "every_executed_lane_passed": all(row["status"] == "passed" for row in executed),
        "every_executed_lane_produced_an_archive": all(
            row["output_archive"] for row in executed if row["status"] == "passed"
        ),
        "filename_independence_proven": bool(executed),
        "passed": bool(executed) and all(row["status"] == "passed" for row in executed),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-offline", action="store_true")
    parser.add_argument("--write-json", type=Path, default=None)
    args = parser.parse_args(argv)

    payload = validate_all()
    if args.execute_offline:
        payload["offline_execution"] = execute_offline()
        payload["passed"] = payload["passed"] and payload["offline_execution"]["passed"]

    if args.write_json:
        args.write_json.parent.mkdir(parents=True, exist_ok=True)
        args.write_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    summary = {
        "passed": payload["passed"],
        "notebook_count": payload["notebook_count"],
        "generator_is_current": payload["generator_is_current"],
        "failed_notebooks": [row["notebook"] for row in payload["results"] if not row["passed"]],
    }
    if "offline_execution" in payload:
        summary["offline"] = {
            key: payload["offline_execution"][key]
            for key in ("executed_count", "every_executed_lane_passed", "passed")
        }
        summary["offline_failures"] = [
            {k: row[k] for k in ("notebook", "returncode", "stderr_tail")}
            for row in payload["offline_execution"]["results"]
            if row["status"] == "failed"
        ]
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
