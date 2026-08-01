"""Argument-parser construction for the CausalAgentBench CLI.

Split out of cli.py so the entry point (main + command dispatch) stays separate
from the large, mechanical subparser definitions."""

from __future__ import annotations

import argparse

from causal_agent_bench import __version__

DEFAULT_CONFIG = "configs/smoke.yaml"
DEFAULT_TASKS = "data/sample/tasks.jsonl"
DEFAULT_RUN_DIR = "results/smoke"


def build_parser() -> argparse.ArgumentParser:
    """Construct the full CausalAgentBench argument parser."""

    parser = argparse.ArgumentParser(
        prog="causal_agent_bench",
        description="CausalAgentBench bootstrap CLI.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="Validate a JSONL task file.")
    validate_parser.add_argument("tasks_path", nargs="?", default=DEFAULT_TASKS)
    validate_parser.add_argument(
        "--schema",
        default="tasks",
        help=(
            "Schema type: tasks, base_tasks, interventions, instances, trajectories, "
            "trajectories_v2, or scores."
        ),
    )

    generate_parser = subparsers.add_parser("generate", help="Generate benchmark tasks from YAML.")
    generate_parser.add_argument("--config", default=DEFAULT_CONFIG)

    run_parser = subparsers.add_parser("run", help="Run agents on benchmark tasks.")
    run_parser.add_argument("--config", default=DEFAULT_CONFIG)
    run_parser.add_argument("--resume", default=None, help="Resume an existing experiment run dir.")
    run_parser.add_argument(
        "--retry-failed",
        action="store_true",
        help="On resume, retry retriable failed pairs that have no trajectory.",
    )
    run_parser.add_argument(
        "--checkpoint-every",
        type=int,
        default=1,
        help="Write checkpoint.json after every N completed trajectories (0 disables).",
    )
    run_parser.add_argument(
        "--force-resume",
        action="store_true",
        help="Resume even when config hash differs (unsafe; use with care).",
    )
    run_parser.add_argument("--max-trajectories", type=int, default=None)
    run_parser.add_argument("--max-runtime-minutes", type=float, default=None)
    run_parser.add_argument("--stop-after-trajectories", type=int, default=None)

    run_status_parser = subparsers.add_parser(
        "run-status", help="Inspect run progress and evidence status."
    )
    run_status_parser.add_argument("--run-dir", default=None)
    run_status_parser.add_argument("--latest", action="store_true")

    mark_interrupted_parser = subparsers.add_parser(
        "mark-interrupted",
        help="Mark a run directory as interrupted/incomplete without deleting artifacts.",
    )
    mark_interrupted_parser.add_argument("--run-dir", required=True)
    mark_interrupted_parser.add_argument("--reason", default="user stopped long local run")

    monitor_parser = subparsers.add_parser("monitor", help="Print run progress (optionally watch).")
    monitor_parser.add_argument("--run-dir", default=None)
    monitor_parser.add_argument("--latest", action="store_true")
    monitor_parser.add_argument("--watch", action="store_true")
    monitor_parser.add_argument("--interval", type=float, default=5.0)
    monitor_parser.add_argument(
        "--max-iterations",
        type=int,
        default=None,
        help="Cap watch refreshes (default: refresh until the run reaches a terminal state).",
    )

    plan_run_parser = subparsers.add_parser(
        "plan-run", help="Estimate trajectories, cost, and runtime risk."
    )
    plan_run_parser.add_argument("--config", required=True)

    index_runs_parser = subparsers.add_parser(
        "index-runs", help="Build results run index JSON/JSONL."
    )
    index_runs_parser.add_argument("--results-root", default="results")
    index_runs_parser.add_argument(
        "--verify",
        action="store_true",
        help="Read-only: report whether the persisted index is stale vs the live results tree. "
        "Writes nothing and never changes evidence state.",
    )

    build_manifest_parser = subparsers.add_parser(
        "build-release-manifest",
        help="Generate release/release_manifest.json and .md.",
    )
    build_manifest_parser.add_argument("--output-dir", default="release")

    subparsers.add_parser(
        "plan-repro-bundle",
        help="Plan a future public reproducibility bundle (no zip).",
    )

    command_plan_parser = subparsers.add_parser(
        "command-plan",
        help="Print safe command blocks for an experiment stage (does not run).",
    )
    command_plan_parser.add_argument(
        "--experiment",
        choices=["micro_stub", "micro_local", "provider_pilot", "main_500", "all"],
        required=True,
    )
    command_plan_parser.add_argument("--write-all", action="store_true")

    subparsers.add_parser(
        "capture-env",
        help="Capture environment metadata without secrets.",
    )

    generate_report_parser = subparsers.add_parser(
        "generate-report",
        help="Generate report.md/json/html for a run directory.",
    )
    generate_report_parser.add_argument("--run-dir", default=None)
    generate_report_parser.add_argument("--latest", action="store_true")
    generate_report_parser.add_argument("--no-html", action="store_true")

    compare_runs_parser = subparsers.add_parser("compare-runs", help="Compare two experiment runs.")
    compare_runs_parser.add_argument("--run-dir", action="append", default=None)
    compare_runs_parser.add_argument(
        "--latest", action="store_true", help="Compare two most recent runs."
    )
    compare_runs_parser.add_argument(
        "--count", type=int, default=2, help="Number of latest runs (with --latest)."
    )
    compare_runs_parser.add_argument(
        "--output", default=None, help="Output directory for run_comparison files."
    )

    failure_gallery_parser = subparsers.add_parser(
        "failure-gallery",
        help="Generate failure_gallery.md/json for a run directory.",
    )
    failure_gallery_parser.add_argument("--run-dir", default=None)
    failure_gallery_parser.add_argument("--latest", action="store_true")
    failure_gallery_parser.add_argument("--max-cases", type=int, default=3)

    audit_dataset_parser = subparsers.add_parser(
        "audit-dataset",
        help="Audit dataset quality for an instances JSONL file.",
    )
    audit_dataset_group = audit_dataset_parser.add_mutually_exclusive_group(required=True)
    audit_dataset_group.add_argument("--dataset")
    audit_dataset_group.add_argument("--config")
    audit_dataset_parser.add_argument("--output", default=None)

    batch_plan_parser = subparsers.add_parser(
        "batch-plan",
        help="Plan sharded experiment configs for parallel batch execution.",
    )
    batch_plan_parser.add_argument("--config", default=DEFAULT_CONFIG)
    batch_plan_parser.add_argument(
        "--shard-by",
        choices=["instance", "agent", "intervention_family"],
        required=True,
    )
    batch_plan_parser.add_argument("--shard-count", type=int, required=True)
    batch_plan_parser.add_argument("--output-dir", default=None)

    batch_merge_parser = subparsers.add_parser(
        "batch-merge",
        help="Merge shard run directories into one scored run.",
    )
    batch_merge_parser.add_argument(
        "--batch-dir",
        required=True,
        help="Directory containing batch_manifest.json and shards/.",
    )
    batch_merge_parser.add_argument("--output-dir", default=None)
    batch_merge_parser.add_argument(
        "--no-strict",
        action="store_true",
        help="Merge even when duplicates or missing keys are detected.",
    )
    batch_merge_parser.add_argument("--no-score", action="store_true")

    failure_report_parser = subparsers.add_parser(
        "failure-report",
        help="Summarize errors, missing pairs, and duplicates for a run directory.",
    )
    failure_report_parser.add_argument("--run-dir", required=True)
    failure_report_parser.add_argument("--output-dir", default=None)

    score_parser = subparsers.add_parser("score", help="Score a run directory.")
    score_parser.add_argument("--run-dir", default=DEFAULT_RUN_DIR)
    score_parser.add_argument(
        "--allow-incomplete",
        action="store_true",
        help="Allow scoring incomplete runs (outputs labeled preliminary/incomplete).",
    )

    analyze_parser = subparsers.add_parser("analyze", help="Create an analysis report.")
    analyze_parser.add_argument("--run-dir", default=DEFAULT_RUN_DIR)
    analyze_parser.add_argument(
        "--allow-incomplete",
        action="store_true",
        help="Allow analysis on incomplete runs (report labeled preliminary).",
    )

    export_parser = subparsers.add_parser(
        "export-paper-assets",
        help="Export small tables/assets for paper wiring.",
    )
    export_parser.add_argument("--run-dir", default=DEFAULT_RUN_DIR)
    export_parser.add_argument(
        "--allow-engineering-only",
        action="store_true",
        help="Allow export from stub/smoke/local-stub runs (assets marked engineering-only).",
    )
    export_parser.add_argument(
        "--allow-incomplete",
        action="store_true",
        help="Allow export from incomplete runs (engineering/preliminary only).",
    )
    export_parser.add_argument(
        "--no-write-global",
        action="store_true",
        help="Skip copying assets to repo-level figures/ and tables/.",
    )
    export_parser.add_argument("--allow-placeholder", action="store_true")
    export_parser.add_argument("--allow-mock-stub", action="store_true")

    ablation_export_parser = subparsers.add_parser(
        "export-ablation-table",
        help="Export Table 4 prompt/scaffold ablation results from a run directory.",
    )
    ablation_export_parser.add_argument("--run-dir", required=True)
    ablation_export_parser.add_argument(
        "--output-dir",
        default=None,
        help="Defaults to <run-dir>/paper_assets/tables.",
    )
    ablation_export_parser.add_argument("--allow-engineering-only", action="store_true")
    ablation_export_parser.add_argument("--allow-incomplete", action="store_true")
    ablation_export_parser.add_argument("--allow-placeholder", action="store_true")
    ablation_export_parser.add_argument("--allow-mock-stub", action="store_true")

    ablation_matrix_parser = subparsers.add_parser(
        "ablation-matrix",
        help="Plan or execute a factorial ablation matrix from one YAML config.",
    )
    ablation_matrix_parser.add_argument(
        "--config",
        default="configs/ablation_matrix_local_stub.yaml",
        help="Ablation matrix YAML (see configs/ablation_matrix_local_stub.yaml).",
    )
    ablation_matrix_parser.add_argument(
        "--output-dir",
        default=None,
        help="Override matrix output root (defaults to output_dir/run_name in config).",
    )
    ablation_matrix_parser.add_argument(
        "--execute",
        action="store_true",
        help="Run each matrix cell after planning (default is plan-only dry-run).",
    )
    ablation_matrix_parser.add_argument(
        "--replan",
        action="store_true",
        help="Regenerate cell configs even when require_dry_run_before_execute is set.",
    )
    ablation_matrix_parser.add_argument(
        "--no-skip-existing",
        action="store_true",
        help="Re-run cells that already have aggregate_scores.json.",
    )
    ablation_matrix_parser.add_argument(
        "--aggregate-only",
        action="store_true",
        help="Skip planning/execution; aggregate and export from an existing matrix root.",
    )

    leaderboard_export_parser = subparsers.add_parser(
        "export-leaderboard",
        help="Export versioned leaderboard JSON/CSV/Markdown (oracle excluded).",
    )
    leaderboard_export_parser.add_argument("--run-dir", required=True)
    leaderboard_export_parser.add_argument(
        "--output-dir",
        default=None,
        help="Defaults to <run-dir>/leaderboard.",
    )
    leaderboard_export_parser.add_argument(
        "--eval-split",
        default="unfiltered",
        help="Split filter: unfiltered, public_dev, dev, pilot, validation, test, heldout_templates.",
    )
    leaderboard_export_parser.add_argument(
        "--splits-path",
        default=None,
        help="Path to splits.json for eval-split filtering.",
    )
    leaderboard_export_parser.add_argument("--allow-engineering-only", action="store_true")
    leaderboard_export_parser.add_argument("--allow-incomplete", action="store_true")
    leaderboard_export_parser.add_argument("--allow-placeholder", action="store_true")
    leaderboard_export_parser.add_argument("--allow-mock-stub", action="store_true")

    gallery_doc_parser = subparsers.add_parser(
        "export-failure-gallery",
        help="Export docs/FAILURE_GALLERY.md and paper-ready qualitative snippets.",
    )
    gallery_doc_parser.add_argument("--run-dir", default=None)
    gallery_doc_parser.add_argument("--doc-path", default="docs/FAILURE_GALLERY.md")
    gallery_doc_parser.add_argument(
        "--paper-path", default="paper/latexpaper/generated/failure_gallery_short.tex"
    )
    gallery_doc_parser.add_argument("--max-per-family", type=int, default=1)
    gallery_doc_parser.add_argument("--allow-engineering-only", action="store_true")
    gallery_doc_parser.add_argument("--allow-incomplete", action="store_true")
    gallery_doc_parser.add_argument("--allow-placeholder", action="store_true")
    gallery_doc_parser.add_argument("--allow-mock-stub", action="store_true")

    mine_errors_parser = subparsers.add_parser(
        "mine-errors",
        help="Mine trajectory failures into a taxonomy gallery.",
    )
    mine_errors_parser.add_argument("--run-dir", default=DEFAULT_RUN_DIR)
    mine_errors_parser.add_argument("--output-dir", default=None)
    mine_errors_parser.add_argument("--max-cases", type=int, default=5)
    mine_errors_parser.add_argument("--no-filters", action="store_true")

    subparsers.add_parser("doctor", help="Run repository health checks.")
    subparsers.add_parser(
        "list-providers", help="List LLM providers and local configuration status."
    )

    estimate_parser = subparsers.add_parser("estimate-cost", help="Estimate pilot run cost bounds.")
    estimate_parser.add_argument("--config", default=DEFAULT_CONFIG)

    validate_config_parser = subparsers.add_parser(
        "validate-config", help="Validate a YAML config."
    )
    validate_config_parser.add_argument("--config", required=True)

    dry_run_parser = subparsers.add_parser(
        "dry-run",
        help="Validate and locally simulate an experiment config without provider calls.",
    )
    dry_run_parser.add_argument("--config", required=True)
    dry_run_parser.add_argument(
        "--output-dir",
        default="results/dry_runs",
        help="Directory for dry-run reports. Use an empty string to skip writing reports.",
    )

    contamination_parser = subparsers.add_parser(
        "audit-contamination",
        help="Audit template fingerprints, canaries, near-duplicates, and prompt leakage.",
    )
    contamination_parser.add_argument("--benchmark-dir", required=True)
    contamination_parser.add_argument("--splits-path", default=None)
    contamination_parser.add_argument(
        "--output-dir",
        default=None,
        help="Defaults to <benchmark-dir>.",
    )
    contamination_parser.add_argument(
        "--near-duplicate-threshold",
        type=float,
        default=0.85,
    )

    audit_parser = subparsers.add_parser(
        "audit-interventions",
        help="Run automated quality checks over a generated benchmark.",
    )
    audit_parser.add_argument("--benchmark-dir", default=None)
    audit_parser.add_argument("--base-tasks", default=None)
    audit_parser.add_argument("--interventions", default=None)
    audit_parser.add_argument("--instances", default=None)
    audit_parser.add_argument("--output-dir", default=None)

    freeze_parser = subparsers.add_parser(
        "freeze-dataset",
        help="Copy a generated dataset into a versioned frozen folder with a manifest.",
    )
    freeze_parser.add_argument("--source-dir", required=True)
    freeze_parser.add_argument("--version", required=True)
    freeze_parser.add_argument("--output-dir", default="data/frozen")
    freeze_parser.add_argument("--force", action="store_true")

    summarize_parser = subparsers.add_parser("summarize-run", help="Summarize a run directory.")
    summarize_parser.add_argument("--run-dir", required=True)
    summarize_parser.add_argument("--output", default=None)

    human_export_parser = subparsers.add_parser(
        "export-human-validation",
        help="Sample a run and export human annotation CSV/JSONL packets.",
    )
    human_export_parser.add_argument("--run-dir", required=True)
    human_export_parser.add_argument("--output-dir", default=None)
    human_export_parser.add_argument("--sample-size", type=int, default=100)
    human_export_parser.add_argument("--seed", type=int, default=0)
    human_export_parser.add_argument("--annotators-per-item", type=int, default=2)
    human_export_parser.add_argument("--no-html", action="store_true")

    human_summary_parser = subparsers.add_parser(
        "summarize-human-validation",
        help="Compute agreement and adjudication summaries from annotation CSV/JSONL.",
    )
    human_summary_parser.add_argument("--annotations", required=True)
    human_summary_parser.add_argument("--output-dir", default=None)

    judge_parser = subparsers.add_parser(
        "run-llm-judge",
        help="Run optional model-judge labels into separate artifacts.",
    )
    judge_parser.add_argument("--run-dir", required=True)
    judge_parser.add_argument("--config", required=True)
    judge_parser.add_argument("--output-dir", default=None)

    judge_calibration_parser = subparsers.add_parser(
        "calibrate-llm-judge",
        help="Compare judge labels against completed human annotations.",
    )
    judge_calibration_parser.add_argument("--judge-labels", required=True)
    judge_calibration_parser.add_argument("--human-annotations", required=True)
    judge_calibration_parser.add_argument("--output-dir", default=None)

    ledger_parser = subparsers.add_parser(
        "update-claim-ledger",
        help="List or safely update docs/claim_ledger.json.",
    )
    ledger_parser.add_argument("--ledger", default="docs/claim_ledger.json")
    ledger_parser.add_argument("--repo-root", default=None)
    ledger_parser.add_argument(
        "--run-dir",
        default=None,
        help="Link all empirical claims to a verified run directory.",
    )
    ledger_parser.add_argument("--claim-id", default=None)
    ledger_parser.add_argument("--status", default=None)
    ledger_parser.add_argument("--evidence-path", action="append", default=[])
    ledger_parser.add_argument("--linked-run-dir", action="append", default=[])
    ledger_parser.add_argument("--notes", default=None)
    ledger_parser.add_argument("--promote-to-supported", action="store_true")
    ledger_parser.add_argument(
        "--force-manual-supported",
        action="store_true",
        help=(
            "Allow --status supported without strict claim-evidence validation. "
            "Adds a visible ledger warning; not safe for paper claims."
        ),
    )
    ledger_parser.add_argument("--blocking-item", action="append", default=[])

    mini_study_parser = subparsers.add_parser(
        "compare-mini-study",
        help="Compare template vs naturalistic mini-study degradation patterns.",
    )
    mini_study_parser.add_argument("--template-run-dir", required=True)
    mini_study_parser.add_argument("--naturalistic-run-dir", required=True)
    mini_study_parser.add_argument("--output-dir", required=True)

    web_shadow_parser = subparsers.add_parser(
        "compare-web-shadow",
        help="Compare simulated API vs static web snapshot tool interfaces.",
    )
    web_shadow_parser.add_argument("--api-run-dir", required=True)
    web_shadow_parser.add_argument("--web-run-dir", required=True)
    web_shadow_parser.add_argument("--output-dir", required=True)

    fill_paper_parser = subparsers.add_parser(
        "fill-paper-from-run",
        help="Fill paper/latexpaper/generated fragments from a verified experiment run.",
    )
    fill_paper_parser.add_argument("--run-dir", required=True)
    fill_paper_parser.add_argument("--repo-root", default=None)
    fill_paper_parser.add_argument("--allow-engineering-only", action="store_true")
    fill_paper_parser.add_argument("--promote-to-supported", action="store_true")
    fill_paper_parser.add_argument("--no-export", action="store_true")
    fill_paper_parser.add_argument("--no-ledger", action="store_true")
    fill_paper_parser.add_argument("--allow-incomplete", action="store_true")
    fill_paper_parser.add_argument("--allow-placeholder", action="store_true")
    fill_paper_parser.add_argument("--allow-mock-stub", action="store_true")

    run_health_parser = subparsers.add_parser(
        "run-health",
        help="Zero-compute run health report from RUN_INDEX (no model calls).",
    )
    run_health_parser.add_argument("--repo-root", default=None)
    run_health_parser.add_argument("--results-root", default="results")
    run_health_parser.add_argument("--output-dir", default="reports")

    validate_assets_parser = subparsers.add_parser(
        "validate-paper-assets",
        help="Scan tables/figures/generated TeX for paper eligibility.",
    )
    validate_assets_parser.add_argument("--repo-root", default=None)
    validate_assets_parser.add_argument("--output-dir", default="reports")

    claim_evidence_parser = subparsers.add_parser(
        "claim-evidence",
        help="Build conservative claim-evidence matrix (C1–C10).",
    )
    claim_evidence_parser.add_argument("--repo-root", default=None)
    claim_evidence_parser.add_argument("--ledger", default="docs/claim_ledger.json")
    claim_evidence_parser.add_argument("--results-root", default="results")
    claim_evidence_parser.add_argument("--output-dir", default="reports")
    claim_evidence_parser.add_argument("--no-tex", action="store_true")

    paper_todo_parser = subparsers.add_parser(
        "paper-todo-inventory",
        help="Inventory TODOs, placeholders, and blocked paper language.",
    )
    paper_todo_parser.add_argument("--repo-root", default=None)
    paper_todo_parser.add_argument("--output-dir", default="reports")

    repro_report_parser = subparsers.add_parser(
        "reproducibility-report",
        help="Low-compute Python/environment reproducibility report.",
    )
    repro_report_parser.add_argument("--repo-root", default=None)
    repro_report_parser.add_argument("--output-dir", default="reports")

    benchmark_quality_parser = subparsers.add_parser(
        "benchmark-quality",
        help="Static benchmark/data quality audit (no runs, no providers).",
    )
    benchmark_quality_parser.add_argument("--repo-root", default=None)
    benchmark_quality_parser.add_argument("--benchmark-dir", default=None)
    benchmark_quality_parser.add_argument("--output-dir", default="reports/benchmark_quality")

    isolation_parser = subparsers.add_parser(
        "intervention-isolation-audit",
        help="Static clean/intervention isolation audit (no runs, no providers).",
    )
    isolation_parser.add_argument("--repo-root", default=None)
    isolation_parser.add_argument("--benchmark-dir", default=None)
    isolation_parser.add_argument("--instances-path", default=None)
    isolation_parser.add_argument("--output-dir", default="reports/intervention_isolation")
    isolation_parser.add_argument("--taxonomy", default=None)

    synthetic_fixture_parser = subparsers.add_parser(
        "synthetic-fixture-check",
        help="Validate synthetic metric-diagnostic trajectory fixtures.",
    )
    synthetic_fixture_parser.add_argument("--repo-root", default=None)
    synthetic_fixture_parser.add_argument(
        "--fixtures-dir", default="tests/fixtures/synthetic_trajectories"
    )
    synthetic_fixture_parser.add_argument("--output-dir", default="reports/synthetic_fixtures")

    human_packet_parser = subparsers.add_parser(
        "human-validation-packet",
        help="Write human validation templates and dry-run packet only.",
    )
    human_packet_parser.add_argument("--repo-root", default=None)
    human_packet_parser.add_argument("--output-dir", default="reports/human_validation")

    estimate_run_cost_parser = subparsers.add_parser(
        "estimate-run-cost",
        help="No-run provider pilot cost estimator and planner.",
    )
    estimate_run_cost_parser.add_argument("--repo-root", default=None)
    estimate_run_cost_parser.add_argument(
        "--config", default="configs/provider_pilot_tiny_template.yaml"
    )
    estimate_run_cost_parser.add_argument("--output-dir", default="reports/cost_estimates")

    method_figures_parser = subparsers.add_parser(
        "method-figure-scaffolds",
        help="Write non-empirical Mermaid method figure scaffolds.",
    )
    method_figures_parser.add_argument("--repo-root", default=None)
    method_figures_parser.add_argument("--output-dir", default="figures/method")

    release_readiness_parser = subparsers.add_parser(
        "release-readiness",
        help="Static release readiness report (no builds, no runs, no providers).",
    )
    release_readiness_parser.add_argument("--repo-root", default=None)
    release_readiness_parser.add_argument("--output-dir", default="reports/release_readiness")
    release_readiness_parser.add_argument("--results-root", default="results")

    dataset_triage_parser = subparsers.add_parser(
        "dataset-issue-triage",
        help="Aggregate benchmark quality and isolation issues into repair tasks.",
    )
    dataset_triage_parser.add_argument("--repo-root", default=None)
    dataset_triage_parser.add_argument("--benchmark-dir", default=None)
    dataset_triage_parser.add_argument("--output-dir", default="reports/dataset_triage")

    provider_preflight_parser = subparsers.add_parser(
        "provider-pilot-preflight",
        help="Static preflight validator for an approved provider-pilot config.",
    )
    provider_preflight_parser.add_argument("--repo-root", default=None)
    provider_preflight_parser.add_argument("--config", required=True)
    provider_preflight_parser.add_argument(
        "--output-dir", default="reports/provider_pilot_preflight"
    )

    hv_sample_parser = subparsers.add_parser(
        "human-validation-dry-run-sample",
        help="Build a synthetic-only human-validation dry-run sample packet.",
    )
    hv_sample_parser.add_argument("--repo-root", default=None)
    hv_sample_parser.add_argument("--fixtures-dir", default="tests/fixtures/synthetic_trajectories")
    hv_sample_parser.add_argument("--output-dir", default="reports/human_validation_dry_run")

    validity_scorecard_parser = subparsers.add_parser(
        "validity-scorecard",
        help="Conservative static benchmark validity scorecard (no runs, no providers).",
    )
    validity_scorecard_parser.add_argument("--repo-root", default=None)
    validity_scorecard_parser.add_argument("--benchmark-dir", default=None)
    validity_scorecard_parser.add_argument("--taxonomy", default=None)
    validity_scorecard_parser.add_argument(
        "--config", default="configs/provider_pilot_tiny_template.yaml"
    )
    validity_scorecard_parser.add_argument("--output-dir", default="reports/validity_scorecard")

    high_risk_parser = subparsers.add_parser(
        "high-risk-intervention-queue",
        help="Build manual-review queue for high-risk intervention families.",
    )
    high_risk_parser.add_argument("--repo-root", default=None)
    high_risk_parser.add_argument("--benchmark-dir", default=None)
    high_risk_parser.add_argument("--taxonomy", default=None)
    high_risk_parser.add_argument("--output-dir", default="reports/high_risk_interventions")

    submission_gate_parser = subparsers.add_parser(
        "neurips-submission-gate",
        help="Conservative NeurIPS submission readiness gate (static, no-run).",
    )
    submission_gate_parser.add_argument("--repo-root", default=None)
    submission_gate_parser.add_argument("--reports-dir", default="reports")
    submission_gate_parser.add_argument("--output-dir", default="reports/neurips_submission_gate")

    method_appendix_parser = subparsers.add_parser(
        "method-appendix",
        help="Generate method-only appendix scaffold with no empirical results.",
    )
    method_appendix_parser.add_argument("--repo-root", default=None)
    method_appendix_parser.add_argument(
        "--output-dir",
        default="paper/latexpaper/generated/no_run_method_appendix",
    )

    evidence_dashboard_parser = subparsers.add_parser(
        "evidence-dashboard",
        help="Build an index over static no-run governance reports.",
    )
    evidence_dashboard_parser.add_argument("--repo-root", default=None)
    evidence_dashboard_parser.add_argument("--reports-dir", default="reports")
    evidence_dashboard_parser.add_argument("--output-dir", default="reports/evidence_dashboard")

    config_lint_parser = subparsers.add_parser(
        "lint-config-metadata",
        help="Static lint for configs and run metadata templates.",
    )
    config_lint_parser.add_argument("--repo-root", default=None)
    config_lint_parser.add_argument("--config-dir", default="configs")
    config_lint_parser.add_argument("--output-dir", default="reports/config_lint")

    repair_plan_parser = subparsers.add_parser(
        "repair-plan",
        help="Build a ranked repair plan from existing no-run reports.",
    )
    repair_plan_parser.add_argument("--repo-root", default=None)
    repair_plan_parser.add_argument("--input-dir", default="reports")
    repair_plan_parser.add_argument("--output-dir", default="reports/repair_plan")

    benchmark_cards_parser = subparsers.add_parser(
        "benchmark-cards",
        help="Generate pre-provider-pilot benchmark/dataset/intervention/limitations cards.",
    )
    benchmark_cards_parser.add_argument("--repo-root", default=None)
    benchmark_cards_parser.add_argument("--benchmark-dir", default=None)
    benchmark_cards_parser.add_argument("--output-dir", default="reports/benchmark_cards")

    gold_outputs_parser = subparsers.add_parser(
        "validate-gold-outputs",
        help="Static gold-answer and expected-output validator.",
    )
    gold_outputs_parser.add_argument("--repo-root", default=None)
    gold_outputs_parser.add_argument("--benchmark-dir", default=None)
    gold_outputs_parser.add_argument("--taxonomy", default=None)
    gold_outputs_parser.add_argument("--output-dir", default="reports/gold_outputs")

    tool_schemas_parser = subparsers.add_parser(
        "validate-tool-schemas",
        help="Static simulated tool schema and task-tool reference validator.",
    )
    tool_schemas_parser.add_argument("--repo-root", default=None)
    tool_schemas_parser.add_argument("--benchmark-dir", default=None)
    tool_schemas_parser.add_argument("--output-dir", default="reports/tool_schemas")

    static_leakage_parser = subparsers.add_parser(
        "static-leakage-check",
        help="Deterministic static leakage and near-duplicate checker.",
    )
    static_leakage_parser.add_argument("--repo-root", default=None)
    static_leakage_parser.add_argument("--benchmark-dir", default=None)
    static_leakage_parser.add_argument("--output-dir", default="reports/static_leakage")
    static_leakage_parser.add_argument("--near-duplicate-threshold", type=float, default=0.88)

    benchmark_manifest_parser = subparsers.add_parser(
        "benchmark-manifest",
        help="Generate benchmark version/provenance manifest.",
    )
    benchmark_manifest_parser.add_argument("--repo-root", default=None)
    benchmark_manifest_parser.add_argument("--output-dir", default="reports/benchmark_manifest")
    benchmark_manifest_parser.add_argument("--results-root", default="results")

    config_profiles_parser = subparsers.add_parser(
        "config-profiles",
        help="Classify configs into no-run safety profiles.",
    )
    config_profiles_parser.add_argument("--repo-root", default=None)
    config_profiles_parser.add_argument("--config-dir", default="configs")
    config_profiles_parser.add_argument("--output-dir", default="reports/config_profiles")

    advisor_packet_parser = subparsers.add_parser(
        "advisor-review-packet",
        help="Generate pre-provider-pilot advisor review packet.",
    )
    advisor_packet_parser.add_argument("--repo-root", default=None)
    advisor_packet_parser.add_argument("--reports-dir", default="reports")
    advisor_packet_parser.add_argument("--output-dir", default="reports/advisor_review")

    paper_readiness_parser = subparsers.add_parser(
        "paper-readiness-map",
        help="Map paper sections to evidence/readiness state.",
    )
    paper_readiness_parser.add_argument("--repo-root", default=None)
    paper_readiness_parser.add_argument("--reports-dir", default="reports")
    paper_readiness_parser.add_argument("--output-dir", default="reports/paper_readiness")

    report_quality_parser = subparsers.add_parser(
        "report-quality-check",
        help="Static actionability/noise check for no-run report bundles.",
    )
    report_quality_parser.add_argument("--repo-root", default=None)
    report_quality_parser.add_argument("--input-dir", required=True)
    report_quality_parser.add_argument("--output-dir", default="reports/report_quality")

    leakage_repair_parser = subparsers.add_parser(
        "leakage-repair-plan",
        help="Build a no-run leakage repair plan and proposed patch manifest.",
    )
    leakage_repair_parser.add_argument("--repo-root", default=None)
    leakage_repair_parser.add_argument("--input-dir", default="reports")
    leakage_repair_parser.add_argument("--output-dir", default="reports/leakage_repair_plan")

    leakage_patch_parser = subparsers.add_parser(
        "validate-leakage-patch-manifest",
        help="Validate a leakage patch manifest without applying patches.",
    )
    leakage_patch_parser.add_argument("--repo-root", default=None)
    leakage_patch_parser.add_argument("--manifest", required=True)
    leakage_patch_parser.add_argument("--output-dir", default=None)

    war_room_parser = subparsers.add_parser(
        "readiness-war-room",
        help="Generate a no-run readiness war-room packet from static reports.",
    )
    war_room_parser.add_argument("--repo-root", default=None)
    war_room_parser.add_argument("--reports-dir", default="reports")
    war_room_parser.add_argument("--output-dir", default="reports/readiness_war_room")

    governance_os_parser = subparsers.add_parser(
        "governance-os",
        help="Generate a no-run governance operating-system packet with release/provider/paper control-plane artifacts.",
    )
    governance_os_parser.add_argument("--repo-root", default=None)
    governance_os_parser.add_argument("--reports-dir", default="reports")
    governance_os_parser.add_argument("--output-dir", default="reports/governance_os")

    leakage_apply_parser = subparsers.add_parser(
        "apply-leakage-patch",
        help=(
            "Preview or apply approved leakage patches. Default is preview-only; "
            "apply mode requires reviewed-ops, reviewed-by, and approval-note."
        ),
    )
    leakage_apply_parser.add_argument("--repo-root", default=None)
    leakage_apply_parser.add_argument("--manifest", required=True)
    leakage_apply_parser.add_argument(
        "--selected-op",
        action="append",
        default=[],
        help="Explicit operation_id to consider. May be repeated.",
    )
    leakage_apply_parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply the reviewed operations. Requires --reviewed-ops, --reviewed-by, and --approval-note.",
    )
    leakage_apply_parser.add_argument("--reviewed-ops", default=None)
    leakage_apply_parser.add_argument("--reviewed-by", default=None)
    leakage_apply_parser.add_argument("--approval-note", default=None)
    leakage_apply_parser.add_argument("--output-dir", default="reports/leakage_repair_apply")

    leakage_suppression_parser = subparsers.add_parser(
        "leakage-suppression-registry",
        help="Validate and report the static leakage suppression registry (no dataset edits).",
    )
    leakage_suppression_parser.add_argument("--repo-root", default=None)
    leakage_suppression_parser.add_argument(
        "--path",
        default=None,
        help="Optional path to a suppression YAML file (defaults to configs/static_leakage_suppressions.yaml).",
    )
    leakage_suppression_parser.add_argument("--output-dir", default="reports/leakage_suppressions")

    reviewed_ops_template_parser = subparsers.add_parser(
        "reviewed-ops-template",
        help="Emit an advisor-facing review worksheet for a leakage patch manifest (no approval given).",
    )
    reviewed_ops_template_parser.add_argument("--repo-root", default=None)
    reviewed_ops_template_parser.add_argument("--manifest", required=True)
    reviewed_ops_template_parser.add_argument(
        "--output-dir", default="reports/leakage_repair_apply"
    )
    reviewed_ops_template_parser.add_argument(
        "--include",
        choices=["safe_to_auto_patch", "all"],
        default="safe_to_auto_patch",
        help="Which manifest operations to include in the template (default: safe_to_auto_patch).",
    )

    manual_repair_preview_parser = subparsers.add_parser(
        "manual-repair-preview",
        help="Emit a reviewer-facing manual repair preview for content/split clusters (no file edits).",
    )
    manual_repair_preview_parser.add_argument("--repo-root", default=None)
    manual_repair_preview_parser.add_argument("--manifest", required=True)
    manual_repair_preview_parser.add_argument(
        "--output-dir", default="reports/manual_repair_preview"
    )

    pair_link_parser = subparsers.add_parser(
        "validate-pair-links",
        help="Validate clean↔intervention pair-link consistency across instances/splits (no run).",
    )
    pair_link_parser.add_argument("--repo-root", default=None)
    pair_link_parser.add_argument("--benchmark-dir", default=None)
    pair_link_parser.add_argument("--output-dir", default="reports/pair_link_validator")

    next_action_parser = subparsers.add_parser(
        "next-action-plan",
        help="Synthesize blockers from no-run reports into a ranked, dependency-aware plan.",
    )
    next_action_parser.add_argument("--repo-root", default=None)
    next_action_parser.add_argument("--reports-dir", default="reports/no_run")
    next_action_parser.add_argument("--output-dir", default="reports/next_action_plan")

    config_hardening_parser = subparsers.add_parser(
        "harden-provider-pilot-config",
        help="Validate a candidate provider-pilot config has all required safety fields before preflight.",
    )
    config_hardening_parser.add_argument("--repo-root", default=None)
    config_hardening_parser.add_argument("--config", required=True)
    config_hardening_parser.add_argument(
        "--output-dir", default="reports/provider_pilot_config_hardening"
    )

    repro_manifest_parser = subparsers.add_parser(
        "reproducibility-manifest",
        help="Generate the static reproducibility manifest (frozen datasets, lockfiles, license, forbidden tests).",
    )
    repro_manifest_parser.add_argument("--repo-root", default=None)
    repro_manifest_parser.add_argument("--output-dir", default="reports/reproducibility_manifest")

    release_blocker_parser = subparsers.add_parser(
        "release-blockers",
        help="Synthesize all public-release blockers from the no-run reports into one canonical report.",
    )
    release_blocker_parser.add_argument("--repo-root", default=None)
    release_blocker_parser.add_argument("--reports-dir", default="reports/no_run")
    release_blocker_parser.add_argument("--output-dir", default="reports/release_blockers")

    all_safety_parser = subparsers.add_parser(
        "all-safety-reports",
        help="Generate all low-compute safety reports under reports/.",
    )
    all_safety_parser.add_argument("--repo-root", default=None)
    all_safety_parser.add_argument("--output-dir", default="reports")
    all_safety_parser.add_argument("--results-root", default="results")

    all_no_run_parser = subparsers.add_parser(
        "all-no-run-reports",
        help="Generate static no-run reports only; excludes benchmark/provider execution.",
    )
    all_no_run_parser.add_argument("--repo-root", default=None)
    all_no_run_parser.add_argument("--output-dir", default="reports/no_run")
    all_no_run_parser.add_argument("--results-root", default="results")
    all_no_run_parser.add_argument("--config", default="configs/provider_pilot_tiny_template.yaml")
    all_no_run_parser.add_argument("--benchmark-dir", default=None)
    all_no_run_parser.add_argument(
        "--fixtures-dir", default="tests/fixtures/synthetic_trajectories"
    )
    all_no_run_parser.add_argument("--taxonomy", default="configs/intervention_taxonomy.yaml")

    _add_level5_parsers(subparsers)

    return parser


def _add_level5_parsers(subparsers: argparse._SubParsersAction) -> None:
    """Add the CAB Research OS public CLI without replacing legacy commands."""

    registry = subparsers.add_parser("registry", help="Manage the Level-5 experiment registry.")
    registry_sub = registry.add_subparsers(dest="registry_command", required=True)
    for name, help_text in (
        ("init", "Initialize or migrate a SQLite registry."),
        ("version", "Print the current and supported schema versions."),
        ("migrate", "Plan or execute an ordered registry migration."),
        ("events", "Inspect the append-only registry event stream."),
        ("doctor", "Check registry schema, integrity, hashes, and privacy."),
        ("export", "Export a deterministic public-safe registry snapshot."),
        ("verify", "Verify registry integrity without mutation."),
        ("backup", "Create a consistent SQLite registry backup."),
        ("restore", "Restore and verify a SQLite registry backup."),
        ("results", "Inspect the public-safe evaluation result registry."),
    ):
        child = registry_sub.add_parser(name, help=help_text)
        child.add_argument("--path", default=".cab/registry.sqlite3")
        if name == "export":
            child.add_argument("--output", default=".cab/registry.public.json")
        if name == "backup":
            child.add_argument("--output", default=".cab/backups/registry.sqlite3")
        if name == "restore":
            child.add_argument("--backup", required=True)
        if name == "migrate":
            child.add_argument("--target-version", type=int, default=3)
            child.add_argument("--dry-run", action="store_true")
            child.add_argument("--export-before-upgrade", default=None)
        if name == "results":
            child.add_argument("--results-path", default="reports/level5/evaluation_registry.json")

    environment = subparsers.add_parser("env", help="Inspect the hermetic environment contract.")
    environment_sub = environment.add_subparsers(dest="env_command", required=True)
    environment_doctor = environment_sub.add_parser("doctor", help="Verify environment metadata.")
    environment_doctor.add_argument("--repo-root", default=".")

    benchmark = subparsers.add_parser("benchmark", help="Author governed intervention benchmarks.")
    benchmark_sub = benchmark.add_subparsers(dest="benchmark_command", required=True)
    for name in (
        "init",
        "compile",
        "validate",
        "diversity",
        "review-packet",
        "freeze",
        "retire",
        "contamination-audit",
        "reachability-check",
        "static-reachability-check",
        "executable-reachability-check",
        "gold-reconstruction-check",
        "intervention-isolation-check",
        "intervention-audit",
    ):
        child = benchmark_sub.add_parser(name)
        child.add_argument("--spec", default="examples/level5/public_fixture/authoring.yaml")
        child.add_argument("--output-dir", default=".cab/benchmark")
        if name == "init":
            child.add_argument("--force", action="store_true")
        if name == "compile":
            child.add_argument("--allow-private-output", action="store_true")
        if name in {
            "reachability-check",
            "static-reachability-check",
            "executable-reachability-check",
            "gold-reconstruction-check",
            "intervention-isolation-check",
            "intervention-audit",
        }:
            child.add_argument(
                "--instances",
                default="data/compact20_reviewed/compact20_v2_instances.jsonl",
            )
            child.add_argument("--output", default=None)

    approval = subparsers.add_parser(
        "approval",
        help="Verify content-bound CAB execution approvals.",
    )
    approval_sub = approval.add_subparsers(dest="approval_command", required=True)
    approval_verify = approval_sub.add_parser("verify")
    approval_verify.add_argument("--fixture", action="store_true")
    approval_verify.add_argument("--receipt", default=None)
    approval_verify.add_argument(
        "--scope",
        choices=["fixture", "scientific"],
        default="scientific",
    )
    approval_verify.add_argument("--repo-root", default=".")

    power = subparsers.add_parser(
        "power",
        help="Validate the prospective hierarchical power design.",
    )
    power_sub = power.add_subparsers(dest="power_command", required=True)
    power_validate = power_sub.add_parser("validate")
    power_validate.add_argument("--repo-root", default=".")
    power_validate.add_argument(
        "--design",
        default="reports/final_pre_review/HIERARCHICAL_POWER_DESIGN.json",
    )

    final_pre_review = subparsers.add_parser(
        "final-pre-review",
        help="Validate final provider-free pre-review hardening.",
    )
    final_pre_review_sub = final_pre_review.add_subparsers(
        dest="final_pre_review_command",
        required=True,
    )
    final_pre_review_check = final_pre_review_sub.add_parser("check")
    final_pre_review_check.add_argument("--repo-root", default=".")
    final_pre_review_check.add_argument("--output", default=None)

    plan = subparsers.add_parser(
        "plan",
        help="Compile a fixture plan or derive scientific volume/resources/shards.",
    )
    plan.add_argument(
        "plan_command",
        nargs="?",
        choices=["volume", "resources", "shards"],
    )
    plan.add_argument("--spec", default=None)
    plan.add_argument("--output", default=None)
    plan.add_argument("--shards", type=int, default=None)
    plan.add_argument(
        "--study",
        choices=[
            "compact20",
            "compact20_raac_light",
            "scale100",
            "scale100_raac_light",
            "raac_equal_budget",
            "raac_ablations",
            "transfer",
        ],
        default="scale100",
    )
    plan.add_argument(
        "--scenario",
        choices=["minimum", "planned", "conservative", "rerun_reserve"],
        default="planned",
    )
    plan.add_argument(
        "--planner-config",
        default="configs/pre_run/study_execution_manifests.json",
    )
    plan.add_argument("--declared-total-trajectories", type=int, default=None)

    # Extend the legacy run command with a provider-free Level-5 dry-run surface.
    run_parser = subparsers.choices["run"]
    run_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Compile the Level-5 fixture plan only; no model execution.",
    )
    run_parser.add_argument(
        "--level5-fixture-dir",
        default=None,
        help="Execute the 20-unit Level-5 fixture vertical slice under this directory.",
    )

    status = subparsers.add_parser("status", help="Inspect a Level-5 fixture run.")
    status.add_argument("--run-dir", default=".cab/fixture_run")
    cancel = subparsers.add_parser("cancel", help="Write a fixture cancellation receipt.")
    cancel.add_argument("--run-dir", default=".cab/fixture_run")
    cancel.add_argument("--unit-id", required=True)
    resume = subparsers.add_parser("resume", help="Resume an interrupted Level-5 fixture run.")
    resume.add_argument("--run-dir", default=".cab/fixture_run")
    merge = subparsers.add_parser("merge", help="Inspect the deterministic Level-5 merge.")
    merge.add_argument("--run-dir", default=".cab/fixture_run")

    artifacts = subparsers.add_parser(
        "artifacts", help="Manage the Level-5 content-addressed store."
    )
    artifacts_sub = artifacts.add_subparsers(dest="artifacts_command", required=True)
    for name in ("verify", "export", "gc"):
        child = artifacts_sub.add_parser(name)
        child.add_argument("--store", default=".cab/artifacts")
        if name == "verify":
            child.add_argument("--digest", default=None)
        elif name == "export":
            child.add_argument("--digest", action="append", required=True)
            child.add_argument("--output", default=".cab/artifact_bundle")
        else:
            child.add_argument("--referenced", action="append", default=[])
            child.add_argument("--dry-run", action="store_true", default=True)

    reliability = subparsers.add_parser("reliability", help="Run fixture reliability campaigns.")
    reliability_sub = reliability.add_subparsers(dest="reliability_command", required=True)
    for name in ("inject", "campaign", "report"):
        child = reliability_sub.add_parser(name)
        child.add_argument("--fault", action="append", default=[])
        child.add_argument("--output", default="reports/level5/PHASE04_CHAOS_CAMPAIGN.json")

    review = subparsers.add_parser("review", help="Operate the human review control plane.")
    review_sub = review.add_subparsers(dest="review_command", required=True)
    for name in ("serve", "qualify", "assign", "status", "export", "adjudicate", "validate"):
        child = review_sub.add_parser(name)
        child.add_argument("--input", default=None)
        child.add_argument("--output", default=None)
        if name == "serve":
            child.add_argument("--host", default="127.0.0.1")
            child.add_argument("--port", type=int, default=8765)
            child.add_argument("--data-dir", default=".cab/review")
            child.add_argument(
                "--check",
                action="store_true",
                help="Validate local binding and print readiness without starting the server.",
            )

    evaluator = subparsers.add_parser("evaluator", help="Run protected-evaluator fixtures.")
    evaluator_sub = evaluator.add_subparsers(dest="evaluator_command", required=True)
    for name in ("validate-submission", "dry-run", "run-fixture", "audit", "receipt"):
        child = evaluator_sub.add_parser(name)
        child.add_argument("--submission", default=None)
        child.add_argument("--output", default=".cab/evaluator_receipt.json")
        if name == "audit":
            child.add_argument("--text", default="")

    evidence = subparsers.add_parser("evidence", help="Inspect evidence lineage.")
    evidence_sub = evidence.add_subparsers(dest="evidence_command", required=True)
    for name in ("trace", "verify"):
        child = evidence_sub.add_parser(name)
        child.add_argument("--graph", default="reports/level5/evidence_graph.fixture.json")
        child.add_argument("--node-id", default=None)

    certify = subparsers.add_parser("certify", help="Issue a fixture-only integrity certificate.")
    certify.add_argument("--output", default=".cab/fixture_certificate.json")
    certificate = subparsers.add_parser(
        "certificate",
        help="Manage persistent fixture certificates and their transparency log.",
    )
    certificate_sub = certificate.add_subparsers(
        dest="certificate_command",
        required=True,
    )
    for name in ("issue-fixture", "verify", "revoke", "list", "transparency-verify"):
        child = certificate_sub.add_parser(name)
        child.add_argument("--path", default=".cab/registry.sqlite3")
        if name in {"verify", "revoke"}:
            child.add_argument("--certificate-id", required=True)
        if name == "revoke":
            child.add_argument("--reason", required=True)
    model_card = subparsers.add_parser("model-card", help="Create a blocked model-card template.")
    model_card.add_argument("--model-id", required=True)
    model_card.add_argument("--revision", required=True)
    model_card.add_argument("--output", default=None)

    claims = subparsers.add_parser("claims", help="Validate Level-5 claim evidence.")
    claims_sub = claims.add_subparsers(dest="claims_command", required=True)
    claims_validate = claims_sub.add_parser("validate")
    claims_validate.add_argument("--state", default="reports/level5/CAB_LEVEL5_BUILD_STATE.json")

    plugins = subparsers.add_parser("plugins", help="Discover and inspect CAB plugins.")
    plugins_sub = plugins.add_subparsers(dest="plugins_command", required=True)
    plugins_sub.add_parser("list")

    reproduce = subparsers.add_parser("reproduce", help="Run internal fixture reproduction.")
    reproduce.add_argument("--workdir", default=".cab/reproduction")

    redteam = subparsers.add_parser("redteam", help="Run the malicious fixture campaign.")
    redteam.add_argument("--output", default="reports/level5/PHASE09_REDTEAM_FIXTURE_CAMPAIGN.json")

    level5 = subparsers.add_parser("level5", help="Evaluate the honest CAB Level-5 gate.")
    level5_sub = level5.add_subparsers(dest="level5_command", required=True)
    level5_check = level5_sub.add_parser("check")
    level5_check.add_argument("--state", default="reports/level5/CAB_LEVEL5_BUILD_STATE.json")
    hardening_check = level5_sub.add_parser("hardening-check")
    hardening_check.add_argument(
        "--state",
        default="reports/level5_hardening/CAB_LEVEL5_HARDENING_STATE.json",
    )

    pre_run = subparsers.add_parser(
        "pre-run",
        help="Validate the frozen provider-free pre-run scientific design.",
    )
    pre_run_sub = pre_run.add_subparsers(dest="pre_run_command", required=True)
    scientific_check = pre_run_sub.add_parser("scientific-check")
    scientific_check.add_argument("--repo-root", default=".")
    scientific_check.add_argument("--output", default=None)

    release_check = subparsers.add_parser(
        "release-check",
        help="Run legacy release validation plus the Level-5 gate.",
    )
    release_check.add_argument("--state", default="reports/level5/CAB_LEVEL5_BUILD_STATE.json")
