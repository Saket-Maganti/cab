#!/usr/bin/env python3
"""Reproducibility and artifact-evaluation helper for reviewers."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON = os.environ.get("PYTHON", sys.executable)
MIN_PYTHON = (3, 11)

ENGINEERING_BANNER = (
    "ENGINEERING-ONLY: stub/smoke outputs validate pipeline mechanics only. "
    "Do not cite as NeurIPS-scale scientific evidence."
)


@dataclass(frozen=True)
class StepSpec:
    name: str
    description: str
    commands: tuple[str, ...]
    requires_api_keys: bool = False
    scientific_evidence: bool = False


def _cmd(*parts: str) -> str:
    return " ".join((PYTHON, *parts))


DETERMINISTIC_STEPS: tuple[StepSpec, ...] = (
    StepSpec(
        "install",
        "Install package and dev dependencies.",
        (f'{PYTHON} -m pip install -e ".[dev]"',),
    ),
    StepSpec(
        "smoke",
        "Validate CLI, schema, and run the smoke benchmark (sample instances).",
        (
            _cmd("-m", "causal_agent_bench", "--help"),
            _cmd("-m", "causal_agent_bench", "validate-config", "--config", "configs/smoke.yaml"),
            _cmd(
                "-m",
                "causal_agent_bench",
                "validate",
                "data/sample/instances.jsonl",
                "--schema",
                "instances",
            ),
            _cmd("-m", "causal_agent_bench", "run", "--config", "configs/smoke.yaml"),
        ),
    ),
    StepSpec(
        "pilot-stub",
        "Run the 20-task local-stub pilot (no paid APIs).",
        (
            _cmd(
                "-m",
                "causal_agent_bench",
                "validate-config",
                "--config",
                "configs/pilot_20_multi_agent.yaml",
            ),
            _cmd(
                "-m",
                "causal_agent_bench",
                "dry-run",
                "--config",
                "configs/pilot_20_multi_agent.yaml",
                "--output-dir",
                "results/dry_runs",
            ),
            _cmd("-m", "causal_agent_bench", "run", "--config", "configs/pilot_20_multi_agent.yaml"),
            _cmd("-m", "causal_agent_bench", "summarize-run", "--run-dir", "{run_dir}"),
        ),
    ),
    StepSpec(
        "table2",
        "Export paper tables and verify Table 2 (main agent performance).",
        (
            _cmd("-m", "causal_agent_bench", "export-paper-assets", "--run-dir", "{run_dir}"),
            "test -f tables/table2_main_agent_performance.csv",
        ),
    ),
    StepSpec(
        "figure2",
        "Export paper figures and verify Figure 2 (clean vs intervention).",
        (
            _cmd("-m", "causal_agent_bench", "export-paper-assets", "--run-dir", "{run_dir}"),
            "test -f figures/figure2_clean_vs_intervention_success.png",
        ),
    ),
)

API_STEPS: tuple[StepSpec, ...] = (
    StepSpec(
        "api-preflight",
        "Optional provider-backed preflight: list providers, validate config, estimate cost.",
        (
            _cmd("-m", "causal_agent_bench", "list-providers"),
            _cmd(
                "-m",
                "causal_agent_bench",
                "validate-config",
                "--config",
                "configs/pilot_openai_20.yaml",
            ),
            _cmd(
                "-m",
                "causal_agent_bench",
                "dry-run",
                "--config",
                "configs/pilot_openai_20.yaml",
                "--output-dir",
                "results/dry_runs",
            ),
            _cmd(
                "-m",
                "causal_agent_bench",
                "estimate-cost",
                "--config",
                "configs/pilot_openai_20.yaml",
            ),
        ),
        requires_api_keys=True,
    ),
    StepSpec(
        "api-pilot",
        "Optional OpenAI pilot run (requires OPENAI_API_KEY and OPENAI_MODEL_ID).",
        (
            _cmd("-m", "causal_agent_bench", "run", "--config", "configs/pilot_openai_20.yaml"),
            _cmd("-m", "causal_agent_bench", "summarize-run", "--run-dir", "{run_dir}"),
        ),
        requires_api_keys=True,
        scientific_evidence=False,
    ),
)

REQUIRED_PATHS = (
    "configs/smoke.yaml",
    "configs/pilot_20_multi_agent.yaml",
    "configs/pilot_openai_20.yaml",
    "data/sample/instances.jsonl",
    "data/processed/pilot_v0_1/pilot_20_instances.jsonl",
)


def _python_ok() -> list[str]:
    if sys.version_info < MIN_PYTHON:
        return [
            f"Python {sys.version_info.major}.{sys.version_info.minor} found; "
            f"requires >= {MIN_PYTHON[0]}.{MIN_PYTHON[1]}"
        ]
    return []


def check_prerequisites(repo_root: Path = REPO_ROOT) -> list[str]:
    issues: list[str] = []
    issues.extend(_python_ok())
    for rel in REQUIRED_PATHS:
        if not (repo_root / rel).exists():
            issues.append(f"missing required path: {rel}")
    try:
        import causal_agent_bench  # noqa: F401
    except ImportError:
        issues.append(
            "causal_agent_bench not importable; run: python -m pip install -e \".[dev]\""
        )
    return issues


def find_latest_run(results_dir: Path, pattern: str) -> Path | None:
    if not results_dir.exists():
        return None
    candidates = sorted(
        (path for path in results_dir.iterdir() if path.is_dir() and pattern in path.name),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def resolve_run_dir(
    repo_root: Path,
    run_dir: str | None,
    *,
    default_pattern: str = "pilot_20_multi_agent_stub",
) -> Path:
    if run_dir:
        path = Path(run_dir)
        if not path.is_absolute():
            path = repo_root / path
        if not path.exists():
            raise FileNotFoundError(f"run directory not found: {path}")
        return path
    latest = find_latest_run(repo_root / "results", default_pattern)
    if latest is None:
        raise FileNotFoundError(
            "no run directory found; pass --run-dir or run step pilot-stub first"
        )
    return latest


def _expand_command(command: str, run_dir: Path, repo_root: Path) -> str:
    rel_run = run_dir.relative_to(repo_root).as_posix()
    return command.format(run_dir=rel_run)


def run_step(
    step: StepSpec,
    repo_root: Path,
    *,
    run_dir: Path | None = None,
    dry_run: bool = False,
) -> None:
    print(f"\n==> {step.name}: {step.description}")
    if not step.scientific_evidence:
        print(f"    {ENGINEERING_BANNER}")

    resolved_run = run_dir
    if any("{run_dir}" in cmd for cmd in step.commands) and resolved_run is None:
        if dry_run:
            resolved_run = repo_root / "results" / "<timestamp>_pilot_20_multi_agent_stub"
        else:
            resolved_run = resolve_run_dir(repo_root, run_dir=None)

    for command in step.commands:
        expanded = _expand_command(command, resolved_run or repo_root, repo_root)
        print(f"    $ {expanded}")
        if dry_run:
            continue
        if expanded.startswith("test "):
            probe = expanded.removeprefix("test ").strip()
            flags = ""
            target = probe
            if " -f " in probe:
                flags, target = probe.split(" -f ", 1)
            path = repo_root / target.strip()
            if "-f" in flags and not path.is_file():
                raise FileNotFoundError(f"expected file missing: {path}")
            continue
        proc = subprocess.run(
            expanded,
            cwd=repo_root,
            shell=True,
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"command failed ({proc.returncode}): {expanded}")


def write_run_manifest(run_dir: Path, step: str, repo_root: Path) -> Path:
    metadata_path = run_dir / "run_metadata.json"
    metadata = {}
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    manifest = {
        "artifact_step": step,
        "run_dir": str(run_dir.relative_to(repo_root)),
        "engineering_only": True,
        "scientific_evidence": False,
        "banner": ENGINEERING_BANNER,
        "config_hash": metadata.get("config_hash"),
        "seed": metadata.get("seed"),
        "git_commit": metadata.get("git_commit"),
        "evidence_scope": metadata.get("evidence_scope"),
        "scorer": metadata.get("scorer", "deterministic_heuristic_v1"),
    }
    out = run_dir / "artifact_manifest.json"
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    parser.add_argument("--step", choices=[*(s.name for s in DETERMINISTIC_STEPS), *(s.name for s in API_STEPS)])
    parser.add_argument("--run-dir", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--check", action="store_true", help="Validate prerequisites only.")
    parser.add_argument("--list-steps", action="store_true")
    parser.add_argument(
        "--all-deterministic",
        action="store_true",
        help="Run install, smoke, pilot-stub, table2, and figure2 in sequence.",
    )
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()

    if args.list_steps:
        print("Deterministic (API-free) steps:")
        for step in DETERMINISTIC_STEPS:
            print(f"  - {step.name}: {step.description}")
        print("\nOptional API-backed steps:")
        for step in API_STEPS:
            print(f"  - {step.name}: {step.description}")
        return 0

    issues = check_prerequisites(repo_root)
    if issues:
        print("Prerequisite check failed:")
        for issue in issues:
            print(f"  - {issue}")
        if args.check:
            return 1
        if not args.dry_run:
            return 1
    elif args.check:
        print("Prerequisite check passed.")
        return 0

    steps_by_name = {step.name: step for step in (*DETERMINISTIC_STEPS, *API_STEPS)}

    if args.all_deterministic:
        run_dir: Path | None = None
        for step_name in ("install", "smoke", "pilot-stub", "table2", "figure2"):
            step = steps_by_name[step_name]
            if step_name in {"table2", "figure2"} and not args.dry_run:
                run_dir = resolve_run_dir(repo_root, args.run_dir)
            run_step(step, repo_root, run_dir=run_dir, dry_run=args.dry_run)
            if step_name == "pilot-stub" and not args.dry_run:
                run_dir = resolve_run_dir(repo_root, args.run_dir)
                write_run_manifest(run_dir, step_name, repo_root)
        if run_dir and not args.dry_run:
            print(f"\nArtifact manifest: {run_dir / 'artifact_manifest.json'}")
        return 0

    if not args.step:
        parser.error("Specify --step, --all-deterministic, --check, or --list-steps")

    step = steps_by_name[args.step]
    run_dir = None
    if args.step in {"pilot-stub", "table2", "figure2", "api-pilot"}:
        if args.step == "pilot-stub" and not args.dry_run:
            pass
        elif args.step != "pilot-stub":
            run_dir = resolve_run_dir(repo_root, args.run_dir)
    run_step(step, repo_root, run_dir=run_dir, dry_run=args.dry_run)
    if args.step == "pilot-stub" and not args.dry_run:
        run_dir = resolve_run_dir(repo_root, args.run_dir)
        write_run_manifest(run_dir, args.step, repo_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
