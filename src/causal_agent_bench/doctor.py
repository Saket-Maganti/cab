from __future__ import annotations

import os
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from causal_agent_bench import __version__
from causal_agent_bench.safety.common import compute_run_index_freshness
from causal_agent_bench.utils.io import load_yaml
from causal_agent_bench.validation import validate_jsonl_file


@dataclass(frozen=True)
class DoctorCheck:
    name: str
    passed: bool
    detail: str


EXPECTED_DIRS = [
    "src/causal_agent_bench",
    "tests",
    "configs",
    "data/sample",
    "docs",
    "paper",
    "results",
    "figures",
    "tables",
]

EXPECTED_DOCS = [
    "docs/BENCHMARK_CARD.md",
    "docs/DATASET_CARD.md",
    "docs/METRICS.md",
    "docs/INTERVENTIONS.md",
    "docs/RUNNING_EXPERIMENTS.md",
    "docs/REPRODUCIBILITY.md",
    "docs/ETHICS_AND_LIMITATIONS.md",
    "docs/CLAIM_LEDGER.md",
    "docs/claim_ledger.json",
]

OPTIONAL_SECRET_ENV_VARS = [
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "HF_TOKEN",
    "HUGGINGFACEHUB_API_TOKEN",
]


def run_doctor(repo_root: str | Path | None = None) -> list[DoctorCheck]:
    root = Path(repo_root or Path.cwd())
    checks: list[DoctorCheck] = []
    checks.append(_check("python_version", _python_version_check))
    checks.append(DoctorCheck("package_import", True, f"causal_agent_bench {__version__}"))
    checks.append(_check_paths("expected_directories", root, EXPECTED_DIRS))
    checks.append(_check_paths("required_docs", root, EXPECTED_DOCS))
    checks.append(_check_sample_data(root))
    checks.append(_check_configs(root))
    checks.append(_check_tests_discoverable(root))
    checks.append(_check_optional_api_keys())
    checks.append(_check_governance_docs(root))
    checks.append(_check_constraints_lockfile(root))
    checks.append(_check_run_index_freshness(root))
    return checks


def print_doctor_report(checks: list[DoctorCheck]) -> None:
    print("CausalAgentBench doctor")
    for check in checks:
        status = "ok" if check.passed else "FAIL"
        print(f"[{status}] {check.name}: {check.detail}")


def doctor_failed(checks: list[DoctorCheck]) -> bool:
    return any(not check.passed for check in checks)


def _check(name: str, fn: Callable[[], str]) -> DoctorCheck:
    try:
        return DoctorCheck(name, True, fn())
    except Exception as exc:
        return DoctorCheck(name, False, str(exc))


def _python_version_check() -> str:
    version = sys.version_info
    if version < (3, 11):
        raise RuntimeError(f"Python >=3.11 required, found {version.major}.{version.minor}")
    return f"{version.major}.{version.minor}.{version.micro}"


def _check_paths(name: str, root: Path, paths: list[str]) -> DoctorCheck:
    missing = [path for path in paths if not (root / path).exists()]
    if missing:
        return DoctorCheck(name, False, f"missing: {', '.join(missing)}")
    return DoctorCheck(name, True, f"{len(paths)} present")


def _check_sample_data(root: Path) -> DoctorCheck:
    path = root / "data/sample/instances.jsonl"
    if not path.exists():
        return DoctorCheck("sample_schema_validation", False, f"missing {path}")
    try:
        summary = validate_jsonl_file(path, "instances")
    except Exception as exc:
        return DoctorCheck("sample_schema_validation", False, str(exc))
    if summary["invalid"]:
        return DoctorCheck(
            "sample_schema_validation",
            False,
            f"{summary['invalid']} invalid records out of {summary['total']}",
        )
    return DoctorCheck(
        "sample_schema_validation",
        True,
        f"{summary['valid']} valid instance records",
    )


def _check_configs(root: Path) -> DoctorCheck:
    config_paths = sorted((root / "configs").glob("*.yaml"))
    if not config_paths:
        return DoctorCheck("configs_load", False, "no YAML configs found")
    failures = []
    for path in config_paths:
        try:
            payload = load_yaml(path)
        except Exception as exc:
            failures.append(f"{path.name}: {exc}")
            continue
        if not isinstance(payload, dict):
            failures.append(f"{path.name}: top-level YAML value is not a mapping")
    if failures:
        return DoctorCheck("configs_load", False, "; ".join(failures))
    return DoctorCheck("configs_load", True, f"{len(config_paths)} YAML configs loaded")


def _check_tests_discoverable(root: Path) -> DoctorCheck:
    tests = sorted((root / "tests").glob("test_*.py"))
    if not tests:
        return DoctorCheck("tests_discoverable", False, "no tests/test_*.py files found")
    return DoctorCheck("tests_discoverable", True, f"{len(tests)} test modules found")


def _check_optional_api_keys() -> DoctorCheck:
    configured = sum(1 for name in OPTIONAL_SECRET_ENV_VARS if os.environ.get(name))
    detail = (
        f"{configured} optional provider credential(s) configured; "
        "values intentionally not displayed"
    )
    return DoctorCheck("optional_api_keys", True, detail)


def _check_governance_docs(root: Path) -> DoctorCheck:
    paths = [
        "GOD_TIER_MANIFEST.md",
        "PROJECT_FULL_CURRENT_AUDIT_FOR_OPUS.md",
        "docs/NO_RUN_REPORTS_GUIDE.md",
        "docs/RUN_INDEX_FRESHNESS.md",
        "reports/INDEX.md",
    ]
    missing = [p for p in paths if not (root / p).exists()]
    if missing:
        return DoctorCheck("governance_docs", False, f"missing: {', '.join(missing)}")
    return DoctorCheck("governance_docs", True, f"{len(paths)} governance docs present")


def _check_constraints_lockfile(root: Path) -> DoctorCheck:
    if (root / "constraints.txt").exists():
        return DoctorCheck("constraints_lockfile", True, "constraints.txt present (pip-tools pin)")
    return DoctorCheck(
        "constraints_lockfile",
        True,
        "constraints.txt missing — run `make lock` for reproducible installs",
    )


def _check_run_index_freshness(root: Path) -> DoctorCheck:
    freshness = compute_run_index_freshness(root)
    if freshness.get("index_stale"):
        return DoctorCheck(
            "run_index_freshness",
            True,
            (
                f"STALE: {freshness.get('indexed_run_count')} indexed vs "
                f"{freshness.get('live_run_count')} live — "
                f"{freshness.get('refresh_command', 'index-runs')}"
            ),
        )
    return DoctorCheck(
        "run_index_freshness",
        True,
        f"fresh ({freshness.get('indexed_run_count')} indexed)",
    )
