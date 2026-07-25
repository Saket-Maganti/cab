"""Validate CAB's nine Kaggle notebooks without providers or model inference.

The offline executor is an ``nbclient``-equivalent for these deliberately plain
Python notebooks: it compiles and executes code cells in order in one isolated
namespace while forcing a temporary output root and the fixture-only mode.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sys
import tempfile
from collections.abc import Iterable, Mapping
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_DIR = REPO_ROOT / "notebooks" / "kaggle"

EXPECTED_NOTEBOOKS = (
    "CAB_T4X2_00_ENVIRONMENT_PREFLIGHT.ipynb",
    "CAB_T4X2_01_OFFLINE_FIXTURE_SMOKE.ipynb",
    "CAB_T4X2_02_COMPACT20_OPEN_MODEL_RUNNER.ipynb",
    "CAB_T4X2_03_SCALE100_OPEN_MODEL_RUNNER.ipynb",
    "CAB_T4X2_04_MAIN500_OPEN_MODEL_RUNNER.ipynb",
    "CAB_T4X2_05_BASELINES_AND_ABLATIONS.ipynb",
    "CAB_T4X2_06_MERGE_AUDIT_AND_RESCORE.ipynb",
    "CAB_T4X2_07_FAILURE_RECOVERY.ipynb",
    "CAB_T4X2_08_NATURALISTIC_TRANSFER_RUNNER.ipynb",
)

EXPECTED_ROLES = (
    "purpose",
    "configuration",
    "setup",
    "preflight",
    "fixture_sharding",
    "checkpoint_resume",
    "activation_guard",
    "live_plan",
    "export_integrity",
    "final_status",
)

REQUIRED_TEXT = (
    "## Purpose",
    "## Evidence boundary",
    "## Exact inputs",
    "## Exact outputs",
    "FIXTURE_ONLY",
    "ENGINEERING_ONLY",
    "EXECUTION_PENDING",
    "RUN_LIVE = False",
    "FIXTURE_WORKERS = 2",
    "deterministic_shards",
    "checkpoint",
    "resume",
    "single_gpu_fallback",
    "float16",
    "4bit",
    "MODEL_ESTIMATED_VRAM_GIB",
    "two_gpu_placement",
    "cuda_version",
    "sanitized_subprocess_environment",
    "LIVE_EXECUTION_REFUSED",
    "APPROVED_FOR_LIVE_RUN: YES",
    "integrity_manifest.json",
    "live_integrity_manifest.json",
)

FORBIDDEN_HOME_PATTERNS = (
    re.compile(r"/Users/[A-Za-z0-9._-]+/"),
    re.compile(r"/home/[A-Za-z0-9._-]+/"),
    re.compile(r"[A-Za-z]:\\\\Users\\\\[^\\\\]+\\\\"),
)

SECRET_VALUE_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{12,}\b"),
    re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bhf_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)

FORBIDDEN_OFFLINE_CODE = (
    "pip install",
    "from_pretrained(",
    "snapshot_download(",
    "requests.get(",
    "requests.post(",
    "urllib.request",
    "huggingface_hub",
    "wget ",
    "curl ",
)

FORBIDDEN_FIXTURE_FIELDS = {
    "answer",
    "final_answer",
    "label",
    "metric",
    "model_output",
    "prediction",
    "score",
    "trajectory",
}


@dataclass(frozen=True)
class ValidationIssue:
    notebook: str
    check: str
    message: str


@dataclass(frozen=True)
class NotebookValidation:
    notebook: str
    static_checks: int
    offline_executed: bool
    offline_receipts: int
    issues: tuple[ValidationIssue, ...]

    @property
    def ok(self) -> bool:
        return not self.issues


def _cell_source(cell: Mapping[str, Any]) -> str:
    source = cell.get("source", "")
    if isinstance(source, list):
        return "".join(str(line) for line in source)
    return str(source)


def _load_notebook(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("notebook root must be a JSON object")
    return payload


def _assignment_values(tree: ast.AST, name: str) -> list[ast.expr]:
    values: list[ast.expr] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets: list[ast.expr]
        if isinstance(node, ast.Assign):
            targets = list(node.targets)
            value = node.value
        else:
            targets = [node.target]
            value = node.value
        if value is None:
            continue
        for target in targets:
            if isinstance(target, ast.Name) and target.id == name:
                values.append(value)
    return values


def _sensitive_assignments(tree: ast.AST) -> list[str]:
    findings: list[str] = []
    sensitive_name = re.compile(r"(?i)(?:api_?key|password|private_?key|access_?token|auth_?token|secret)")
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        value = node.value
        if not isinstance(value, ast.Constant) or not isinstance(value.value, str) or not value.value:
            continue
        for target in targets:
            if isinstance(target, ast.Name) and sensitive_name.search(target.id):
                findings.append(target.id)
    return sorted(set(findings))


def _subprocess_calls(tree: ast.AST) -> list[str]:
    findings: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if (
            isinstance(node.func.value, ast.Name)
            and node.func.value.id == "subprocess"
            and node.func.attr in {"call", "check_call", "check_output", "Popen", "run"}
        ):
            findings.append(node.func.attr)
    return findings


def _schema_issues(path: Path, notebook: Mapping[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    def add(check: str, message: str) -> None:
        issues.append(ValidationIssue(path.name, check, message))

    if notebook.get("nbformat") != 4:
        add("json_schema", "nbformat must be 4")
    minor = notebook.get("nbformat_minor")
    if not isinstance(minor, int) or minor < 0:
        add("json_schema", "nbformat_minor must be a non-negative integer")
    if not isinstance(notebook.get("metadata"), dict):
        add("json_schema", "metadata must be a JSON object")
    cells = notebook.get("cells")
    if not isinstance(cells, list):
        add("json_schema", "cells must be a JSON array")
        return issues
    observed_ids: set[str] = set()
    for index, cell in enumerate(cells):
        if not isinstance(cell, dict):
            add("json_schema", f"cell {index} must be a JSON object")
            continue
        if cell.get("cell_type") not in {"markdown", "code", "raw"}:
            add("json_schema", f"cell {index} has an invalid cell_type")
        if not isinstance(cell.get("metadata"), dict):
            add("json_schema", f"cell {index} metadata must be a JSON object")
        if not isinstance(cell.get("source"), (str, list)):
            add("json_schema", f"cell {index} source must be text or a text array")
        cell_id = cell.get("id")
        if not isinstance(cell_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", cell_id):
            add("json_schema", f"cell {index} must have a valid nbformat 4.5 cell id")
        elif cell_id in observed_ids:
            add("json_schema", f"cell {index} repeats cell id {cell_id!r}")
        else:
            observed_ids.add(cell_id)
        if cell.get("cell_type") == "code":
            if not isinstance(cell.get("outputs"), list):
                add("json_schema", f"code cell {index} outputs must be an array")
            if cell.get("execution_count") is not None:
                add("clean_notebook", f"code cell {index} has a stored execution count")
            if cell.get("outputs"):
                add("clean_notebook", f"code cell {index} has stored outputs")
    return issues


def validate_notebook_static(path: str | Path) -> tuple[NotebookValidation, dict[str, Any] | None]:
    notebook_path = Path(path)
    issues: list[ValidationIssue] = []
    checks = 0

    def add(check: str, message: str) -> None:
        issues.append(ValidationIssue(notebook_path.name, check, message))

    try:
        notebook = _load_notebook(notebook_path)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        add("json", f"{type(exc).__name__}: {exc}")
        return NotebookValidation(notebook_path.name, checks, False, 0, tuple(issues)), None
    checks += 1

    schema_findings = _schema_issues(notebook_path, notebook)
    issues.extend(schema_findings)
    checks += 1

    cells = notebook.get("cells", [])
    roles = [
        str(cell.get("metadata", {}).get("cab_role", ""))
        for cell in cells
        if isinstance(cell, dict)
    ]
    if tuple(roles) != EXPECTED_ROLES:
        add("cell_order", f"expected roles {EXPECTED_ROLES}, observed {tuple(roles)}")
    checks += 1

    all_source = "\n".join(
        _cell_source(cell) for cell in cells if isinstance(cell, Mapping)
    )
    for required in REQUIRED_TEXT:
        if required not in all_source:
            add("required_content", f"missing required text: {required!r}")
    checks += len(REQUIRED_TEXT)

    for pattern in FORBIDDEN_HOME_PATTERNS:
        match = pattern.search(all_source)
        if match:
            add("paths", f"hard-coded user home path: {match.group(0)!r}")
    if "Path('..')" in all_source or 'Path("..")' in all_source:
        add("paths", "parent-directory path traversal is forbidden")
    checks += 1

    for pattern in SECRET_VALUE_PATTERNS:
        match = pattern.search(all_source)
        if match:
            add("secrets", f"possible embedded credential matched {pattern.pattern!r}")
    checks += 1

    code_cells: list[tuple[int, str, str, ast.AST]] = []
    for index, cell in enumerate(cells):
        if not isinstance(cell, Mapping) or cell.get("cell_type") != "code":
            continue
        source = _cell_source(cell)
        role = str(cell.get("metadata", {}).get("cab_role", ""))
        try:
            tree = ast.parse(source, filename=f"{notebook_path.name}:cell_{index}")
        except SyntaxError as exc:
            add("python_syntax", f"cell {index}: {exc.msg} at line {exc.lineno}")
            continue
        code_cells.append((index, role, source, tree))
        sensitive = _sensitive_assignments(tree)
        if sensitive:
            add("secrets", f"cell {index} embeds values in sensitive names: {sensitive}")
        subprocess_calls = _subprocess_calls(tree)
        if subprocess_calls and role != "live_plan":
            add(
                "activation_order",
                f"cell {index} calls subprocess before/away from live_plan: {subprocess_calls}",
            )
        lowered = source.lower()
        for forbidden in FORBIDDEN_OFFLINE_CODE:
            if forbidden.lower() in lowered:
                add("offline_safety", f"cell {index} contains forbidden operation {forbidden!r}")
    checks += len(code_cells)

    config_trees = [tree for _, role, _, tree in code_cells if role == "configuration"]
    if len(config_trees) != 1:
        add("configuration", f"expected one configuration cell, found {len(config_trees)}")
    else:
        run_live_values = _assignment_values(config_trees[0], "RUN_LIVE")
        if len(run_live_values) != 1:
            add("live_default", f"RUN_LIVE must be assigned once, found {len(run_live_values)}")
        elif not (
            isinstance(run_live_values[0], ast.Constant) and run_live_values[0].value is False
        ):
            add("live_default", "RUN_LIVE must be the literal boolean False")
        confirmation_values = _assignment_values(config_trees[0], "LIVE_CONFIRMATION")
        if len(confirmation_values) != 1:
            add(
                "live_default",
                f"LIVE_CONFIRMATION must be assigned once, found {len(confirmation_values)}",
            )
        elif not (
            isinstance(confirmation_values[0], ast.Constant)
            and confirmation_values[0].value == ""
        ):
            add("live_default", "LIVE_CONFIRMATION must default to the empty string")
    checks += 1

    config_source = "\n".join(source for _, role, source, _ in code_cells if role == "configuration")
    work_root_match = re.search(r'WORK_ROOT_SETTING\s*=\s*"([^"]+)"', config_source)
    if work_root_match is None:
        add("output_paths", "WORK_ROOT_SETTING is missing or not a literal string")
    else:
        work_root = Path(work_root_match.group(1))
        if work_root.is_absolute() or ".." in work_root.parts:
            add("output_paths", "WORK_ROOT_SETTING must be a safe relative path")
        if work_root.parts[:2] != ("artifacts", "kaggle"):
            add("output_paths", "WORK_ROOT_SETTING must stay below artifacts/kaggle")
    checks += 1

    live_source = "\n".join(source for _, role, source, _ in code_cells if role == "live_plan")
    index = EXPECTED_NOTEBOOKS.index(notebook_path.name) if notebook_path.name in EXPECTED_NOTEBOOKS else -1
    if index in {2, 3, 4, 5, 8}:
        for required in ("CUDA_VISIBLE_DEVICES", "subprocess.Popen", "batch-plan", "--no-score"):
            if required not in live_source:
                add("t4x2_live_plan", f"runner live plan is missing {required!r}")
    if index == 6:
        for required in ("batch-merge", "merge_report.json", "score"):
            if required not in live_source:
                add("merge_audit", f"merge notebook is missing {required!r}")
    if index == 7:
        for required in ("--resume", "--retry-failed", "recovery_logs", "--no-score"):
            if required not in live_source:
                add("recovery", f"recovery notebook is missing {required!r}")
    checks += 1

    return (
        NotebookValidation(notebook_path.name, checks, False, 0, tuple(issues)),
        notebook,
    )


@contextmanager
def _offline_environment(output_root: Path) -> Iterable[None]:
    updates = {
        "CAB_KAGGLE_WORK_ROOT": str(output_root),
        "CAB_NOTEBOOK_VALIDATE": "1",
        "CAB_ENABLE_LIVE_OPEN_MODEL_RUN": "NO",
    }
    previous = {key: os.environ.get(key) for key in updates}
    os.environ.update(updates)
    try:
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _flatten_keys(value: object) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, Mapping):
        for key, nested in value.items():
            keys.add(str(key))
            keys.update(_flatten_keys(nested))
    elif isinstance(value, list):
        for nested in value:
            keys.update(_flatten_keys(nested))
    return keys


def execute_notebook_offline(path: str | Path, notebook: Mapping[str, Any]) -> int:
    notebook_path = Path(path)
    namespace: dict[str, Any] = {
        "__builtins__": __builtins__,
        "__name__": f"offline_notebook_{notebook_path.stem}",
    }
    prior_cwd = Path.cwd()
    with tempfile.TemporaryDirectory(prefix=f"{notebook_path.stem}_") as temporary:
        output_root = Path(temporary).resolve()
        with _offline_environment(output_root):
            os.chdir(REPO_ROOT)
            try:
                for index, cell in enumerate(notebook.get("cells", [])):
                    if not isinstance(cell, Mapping) or cell.get("cell_type") != "code":
                        continue
                    source = _cell_source(cell)
                    compiled = compile(
                        source,
                        filename=f"{notebook_path.name}:cell_{index}",
                        mode="exec",
                    )
                    exec(compiled, namespace)
            finally:
                os.chdir(prior_cwd)

        if namespace.get("RUN_LIVE") is not False:
            raise AssertionError("offline execution changed RUN_LIVE away from False")
        if namespace.get("LIVE_AUTHORIZED") is not False:
            raise AssertionError("offline execution unexpectedly authorized a live action")
        if namespace.get("LIVE_EXECUTED") is not False:
            raise AssertionError("offline execution claims a live action ran")
        integrity = namespace.get("FINAL_INTEGRITY")
        if not isinstance(integrity, dict) or integrity.get("ok") is not True:
            raise AssertionError(f"offline integrity did not pass: {integrity!r}")

        fixture_root = Path(namespace["FIXTURE_ROOT"]).resolve()
        archive_path = Path(namespace["ARCHIVE_PATH"]).resolve()
        fixture_root.relative_to(output_root)
        archive_path.relative_to(output_root)
        if not archive_path.is_file():
            raise AssertionError("fixture archive was not exported")

        merged_receipts = fixture_root / "merged" / "fixture_receipts.jsonl"
        rows = [
            json.loads(line)
            for line in merged_receipts.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        expected_count = int(namespace["OFFLINE_FIXTURE_ITEMS"])
        if len(rows) != expected_count:
            raise AssertionError(
                f"expected {expected_count} fixture receipts, observed {len(rows)}"
            )
        for row in rows:
            forbidden = _flatten_keys(row) & FORBIDDEN_FIXTURE_FIELDS
            if forbidden:
                raise AssertionError(f"fixture receipt has model/result-shaped fields: {forbidden}")
            if row.get("evidence_class") != "FIXTURE_ONLY":
                raise AssertionError("fixture receipt lost FIXTURE_ONLY classification")

        status = json.loads(
            (fixture_root / "notebook_status.json").read_text(encoding="utf-8")
        )
        if status.get("claim_promotion_allowed") is not False:
            raise AssertionError("fixture status permits claim promotion")
        if status.get("paper_asset_eligible") is not False:
            raise AssertionError("fixture status permits paper assets")
        return len(rows)


def validate_notebook(path: str | Path, *, execute_offline: bool = False) -> NotebookValidation:
    static, notebook = validate_notebook_static(path)
    issues = list(static.issues)
    receipt_count = 0
    executed = False
    if execute_offline and notebook is not None and not issues:
        try:
            receipt_count = execute_notebook_offline(path, notebook)
            executed = True
        except Exception as exc:
            issues.append(
                ValidationIssue(
                    Path(path).name,
                    "offline_execution",
                    f"{type(exc).__name__}: {exc}",
                )
            )
    return NotebookValidation(
        notebook=static.notebook,
        static_checks=static.static_checks,
        offline_executed=executed,
        offline_receipts=receipt_count,
        issues=tuple(issues),
    )


def _resolve_paths(selected: list[str] | None) -> tuple[list[Path], list[ValidationIssue]]:
    issues: list[ValidationIssue] = []
    expected_set = set(EXPECTED_NOTEBOOKS)
    if selected:
        paths = []
        for raw in selected:
            path = Path(raw)
            if not path.is_absolute():
                path = REPO_ROOT / path
            if not path.is_file():
                issues.append(
                    ValidationIssue(path.name, "inventory", "selected notebook is missing")
                )
            else:
                paths.append(path)
        return paths, issues

    observed = {path.name for path in NOTEBOOK_DIR.glob("*.ipynb")} if NOTEBOOK_DIR.is_dir() else set()
    for missing in sorted(expected_set - observed):
        issues.append(ValidationIssue(missing, "inventory", "required notebook is missing"))
    for extra in sorted(observed - expected_set):
        issues.append(ValidationIssue(extra, "inventory", "unexpected Kaggle notebook is present"))
    return [NOTEBOOK_DIR / name for name in EXPECTED_NOTEBOOKS if name in observed], issues


def validate_all(
    *,
    selected: list[str] | None = None,
    execute_offline: bool = False,
) -> dict[str, Any]:
    paths, inventory_issues = _resolve_paths(selected)
    results = [
        validate_notebook(path, execute_offline=execute_offline)
        for path in paths
        if path.is_file()
    ]
    issues = [*inventory_issues, *(issue for result in results for issue in result.issues)]
    return {
        "ok": not issues,
        "evidence_class": "FIXTURE_ONLY",
        "scientific_execution_performed": False,
        "executor": (
            "sequential plain-Python code-cell execution in a temporary output root"
            if execute_offline
            else "not requested"
        ),
        "expected_notebooks": len(EXPECTED_NOTEBOOKS),
        "validated_notebooks": len(results),
        "offline_executed_notebooks": sum(result.offline_executed for result in results),
        "offline_fixture_receipts": sum(result.offline_receipts for result in results),
        "results": [
            {
                **asdict(result),
                "ok": result.ok,
                "issues": [asdict(issue) for issue in result.issues],
            }
            for result in results
        ],
        "issues": [asdict(issue) for issue in issues],
    }


def _print_text_report(report: Mapping[str, Any]) -> None:
    verdict = "PASS" if report["ok"] else "FAIL"
    print(f"KAGGLE_NOTEBOOK_VALIDATION_{verdict}")
    print(f"expected_notebooks={report['expected_notebooks']}")
    print(f"validated_notebooks={report['validated_notebooks']}")
    print(f"offline_executed_notebooks={report['offline_executed_notebooks']}")
    print(f"offline_fixture_receipts={report['offline_fixture_receipts']}")
    print("scientific_execution_performed=false")
    for issue in report["issues"]:
        print(f"ERROR {issue['notebook']} [{issue['check']}] {issue['message']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--execute-offline",
        action="store_true",
        help="Execute all plain-Python cells with RUN_LIVE=False in temporary directories.",
    )
    parser.add_argument(
        "--notebook",
        action="append",
        default=None,
        help="Validate only this notebook path (repeatable).",
    )
    parser.add_argument("--json", action="store_true", help="Print the report as JSON.")
    args = parser.parse_args(argv)
    report = validate_all(
        selected=args.notebook,
        execute_offline=args.execute_offline,
    )
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_text_report(report)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
