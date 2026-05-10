from __future__ import annotations

import argparse
from pathlib import Path

from pydantic import ValidationError

from causal_agent_bench.analysis.reports import analyze_run, export_paper_assets
from causal_agent_bench.generation.instances import generate_benchmark_from_config
from causal_agent_bench.metrics.scoring import score_run
from causal_agent_bench.runners.config import is_experiment_config
from causal_agent_bench.runners.experiment import run_experiment_from_config
from causal_agent_bench.runners.runner import run_from_config
from causal_agent_bench.schemas import BenchmarkTask
from causal_agent_bench.task import generate_from_config
from causal_agent_bench.utils.io import load_yaml, read_jsonl
from causal_agent_bench.validation import validate_jsonl_file

DEFAULT_CONFIG = "configs/smoke.yaml"
DEFAULT_TASKS = "data/sample/tasks.jsonl"
DEFAULT_RUN_DIR = "results/smoke"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="causal_agent_bench",
        description="CausalAgentBench bootstrap CLI.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="Validate a JSONL task file.")
    validate_parser.add_argument("tasks_path", nargs="?", default=DEFAULT_TASKS)
    validate_parser.add_argument(
        "--schema",
        default="tasks",
        help="Schema type: tasks, base_tasks, interventions, instances, trajectories, or scores.",
    )

    generate_parser = subparsers.add_parser("generate", help="Generate benchmark tasks from YAML.")
    generate_parser.add_argument("--config", default=DEFAULT_CONFIG)

    run_parser = subparsers.add_parser("run", help="Run agents on benchmark tasks.")
    run_parser.add_argument("--config", default=DEFAULT_CONFIG)
    run_parser.add_argument("--resume", default=None, help="Resume an existing experiment run dir.")

    score_parser = subparsers.add_parser("score", help="Score a run directory.")
    score_parser.add_argument("--run-dir", default=DEFAULT_RUN_DIR)

    analyze_parser = subparsers.add_parser("analyze", help="Create an analysis report.")
    analyze_parser.add_argument("--run-dir", default=DEFAULT_RUN_DIR)

    export_parser = subparsers.add_parser(
        "export-paper-assets",
        help="Export small tables/assets for paper wiring.",
    )
    export_parser.add_argument("--run-dir", default=DEFAULT_RUN_DIR)

    args = parser.parse_args(argv)
    repo_root = Path.cwd()

    if args.command == "validate":
        _validate(args.tasks_path, args.schema)
    elif args.command == "generate":
        raw_config = load_yaml(args.config)
        if "num_base_tasks" in raw_config:
            result = generate_benchmark_from_config(args.config)
            counts = result["generation_report"]["counts"]
            print(
                f"generated {counts['base_tasks']} base tasks, "
                f"{counts['interventions']} interventions, "
                f"{counts['instances']} instances in {result['output_dir']}"
            )
        else:
            tasks = generate_from_config(args.config)
            print(f"generated {len(tasks)} tasks")
    elif args.command == "run":
        raw_config = load_yaml(args.config)
        if is_experiment_config(raw_config):
            result = run_experiment_from_config(args.config, resume_dir=args.resume)
            print(f"wrote {len(result['trajectories'])} trajectories to {result['run_dir']}")
        else:
            trajectories = run_from_config(args.config, repo_root=repo_root, resume_dir=args.resume)
            print(f"wrote {len(trajectories)} trajectories")
    elif args.command == "score":
        if not _run_dir_exists(args.run_dir):
            return
        summary = score_run(args.run_dir)
        print(f"wrote scores for {len(summary.by_agent)} agents")
    elif args.command == "analyze":
        if not _run_dir_exists(args.run_dir):
            return
        report_path = analyze_run(args.run_dir)
        print(f"wrote {report_path}")
    elif args.command == "export-paper-assets":
        if not _run_dir_exists(args.run_dir):
            return
        paths = export_paper_assets(args.run_dir)
        for path in paths:
            print(f"wrote {path}")


def _validate(tasks_path: str, schema: str = "tasks") -> None:
    if not Path(tasks_path).exists():
        print(
            f"No task file found at {tasks_path}. Run `python -m causal_agent_bench generate` first, "
            "or pass a JSONL path."
        )
        return
    if schema != "tasks":
        try:
            summary = validate_jsonl_file(Path(tasks_path), schema)
        except ValueError as exc:
            raise SystemExit(f"validation failed: {exc}") from exc
        if summary["invalid"]:
            for item in summary["errors"][:5]:
                print(f"line {item['line']}: {'; '.join(item['errors'])}")
            raise SystemExit(
                f"validation failed: {summary['invalid']} invalid / {summary['total']} total"
            )
        print(
            f"validated {summary['valid']} {schema} records from {tasks_path} "
            f"({summary['invalid']} invalid)"
        )
        return
    try:
        tasks = read_jsonl(tasks_path, BenchmarkTask)
    except (ValidationError, ValueError) as exc:
        raise SystemExit(f"validation failed: {exc}") from exc
    ids = [task.task_id for task in tasks]
    duplicate_ids = sorted({task_id for task_id in ids if ids.count(task_id) > 1})
    if duplicate_ids:
        raise SystemExit(f"validation failed: duplicate task ids: {duplicate_ids}")
    print(f"validated {len(tasks)} tasks")


def _run_dir_exists(run_dir: str) -> bool:
    if Path(run_dir).exists():
        return True
    print(
        f"No run directory found at {run_dir}. Run `python -m causal_agent_bench run` first, "
        "or pass --run-dir."
    )
    return False


if __name__ == "__main__":
    main()
