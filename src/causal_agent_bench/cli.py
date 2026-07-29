from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

# Heavy analysis/report/figure modules (pandas, scipy, matplotlib) are imported
# lazily inside their command branches below, so lightweight commands (--help,
# generate, validate, run, plan-run) start ~1s faster and never load plotting/
# stats stacks they don't use.
from causal_agent_bench.agents.llm_clients import list_provider_status
from causal_agent_bench.cli_parsers import build_parser
from causal_agent_bench.generation.instances import generate_benchmark_from_config
from causal_agent_bench.phase2 import (
    audit_interventions,
    cli_json,
    config_error_payload,
    dry_run_config,
    freeze_dataset,
    summarize_run,
    update_claim_ledger,
    update_claim_ledger_from_run,
    validate_config_file,
)
from causal_agent_bench.runners.config import is_experiment_config
from causal_agent_bench.runners.costing import estimate_config_cost
from causal_agent_bench.runners.experiment import run_experiment_from_config
from causal_agent_bench.runners.runner import run_from_config
from causal_agent_bench.safety.export_guards import apply_export_watermark, validate_export_source
from causal_agent_bench.schemas import BenchmarkTask
from causal_agent_bench.task import generate_from_config
from causal_agent_bench.utils.io import load_yaml, read_jsonl
from causal_agent_bench.validation import validate_jsonl_file


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    repo_root = Path.cwd()

    from causal_agent_bench.level5.cli import handle_level5_command

    if handle_level5_command(args):
        return

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
            limiter_overrides = {
                key: value
                for key, value in {
                    "max_trajectories": args.max_trajectories,
                    "max_runtime_minutes": args.max_runtime_minutes,
                    "stop_after_trajectories": args.stop_after_trajectories,
                }.items()
                if value is not None
            }
            result = run_experiment_from_config(
                args.config,
                resume_dir=args.resume,
                retry_failed=args.retry_failed,
                checkpoint_every=args.checkpoint_every,
                force_resume=args.force_resume,
                limiter_overrides=limiter_overrides or None,
            )
            print(f"wrote {len(result['trajectories'])} trajectories to {result['run_dir']}")
        else:
            trajectories = run_from_config(args.config, repo_root=repo_root, resume_dir=args.resume)
            print(f"wrote {len(trajectories)} trajectories")
    elif args.command == "run-status":
        from causal_agent_bench.runners.run_status import (
            build_run_status,
            format_run_status,
            resolve_run_dir,
        )

        run_dir = resolve_run_dir(args.run_dir, latest=args.latest)
        print(format_run_status(build_run_status(run_dir)), end="")
    elif args.command == "mark-interrupted":
        from causal_agent_bench.runners.mark_interrupted import mark_run_interrupted

        state = mark_run_interrupted(args.run_dir, reason=args.reason)
        print(f"marked interrupted: {state['completed_trajectories']}/{state['expected_trajectories']}")
    elif args.command == "monitor":
        from causal_agent_bench.runners.monitor import monitor_run

        monitor_run(
            args.run_dir,
            latest=args.latest,
            watch=args.watch,
            interval_seconds=args.interval,
            max_iterations=args.max_iterations,
        )
    elif args.command == "plan-run":
        from causal_agent_bench.runners.plan_run import format_plan_report, plan_run

        plan = plan_run(args.config)
        print(format_plan_report(plan), end="")
    elif args.command == "index-runs":
        if getattr(args, "verify", False):
            from causal_agent_bench.safety.common import compute_run_index_freshness

            freshness = compute_run_index_freshness(repo_root, results_root=args.results_root)
            print(cli_json(freshness))
            raise SystemExit(1 if freshness["index_stale"] else 0)
        from causal_agent_bench.runners.index_runs import write_run_index

        json_path, jsonl_path = write_run_index(args.results_root)
        print(f"wrote {json_path}")
        print(f"wrote {jsonl_path}")
    elif args.command == "build-release-manifest":
        from causal_agent_bench.release.build_manifest import build_release_manifest

        manifest = build_release_manifest(output_dir=args.output_dir)
        print(f"wrote {args.output_dir}/release_manifest.json")
        print(f"release_bundle_hash: {manifest['release_bundle_hash']}")
    elif args.command == "plan-repro-bundle":
        from causal_agent_bench.release.repro_bundle import plan_repro_bundle

        plan = plan_repro_bundle()
        print("wrote release/REPRO_BUNDLE_PLAN.md")
        print("wrote release/repro_bundle_plan.json")
    elif args.command == "command-plan":
        from causal_agent_bench.release.command_plan import (
            build_command_plan,
            format_command_plan,
            write_all_command_plans,
        )

        if args.experiment == "all" or args.write_all:
            write_all_command_plans()
            print("wrote experiments/COMMAND_PLANS.md")
            print("wrote experiments/command_plans.json")
        else:
            plan = build_command_plan(args.experiment)
            print(format_command_plan(plan), end="")
    elif args.command == "capture-env":
        from causal_agent_bench.release.capture_env import capture_environment

        report = capture_environment()
        print("wrote environment/env_report.json")
        print(f"python: {report['python']['version'].split()[0]}")
    elif args.command == "generate-report":
        from causal_agent_bench.runners.generate_report import generate_report

        paths = generate_report(args.run_dir, latest=args.latest, include_html=not args.no_html)
        for path in paths.values():
            print(f"wrote {path}")
    elif args.command == "compare-runs":
        from causal_agent_bench.runners.compare_runs import write_compare_artifacts
        from causal_agent_bench.runners.run_status import find_latest_run_dirs

        if args.latest:
            latest = find_latest_run_dirs(count=args.count)
            if len(latest) < 2:
                raise SystemExit("need at least two run directories for --latest compare")
            run_a, run_b = latest[1], latest[0]
        elif args.run_dir and len(args.run_dir) == 2:
            run_a, run_b = args.run_dir
        else:
            raise SystemExit("compare-runs requires two --run-dir paths or --latest")
        paths = write_compare_artifacts(run_a, run_b, output_dir=args.output or run_a)
        for path in paths.values():
            print(f"wrote {path}")
    elif args.command == "failure-gallery":
        from causal_agent_bench.runners.failure_gallery_report import write_failure_gallery
        from causal_agent_bench.runners.run_status import resolve_run_dir

        run_path = resolve_run_dir(args.run_dir, latest=args.latest)
        paths = write_failure_gallery(run_path, max_cases=args.max_cases)
        for path in paths.values():
            print(f"wrote {path}")
    elif args.command == "audit-dataset":
        from causal_agent_bench.runners.audit_dataset import (
            resolve_dataset_path,
            write_dataset_audit,
        )

        dataset = resolve_dataset_path(dataset=args.dataset, config=args.config)
        paths = write_dataset_audit(dataset, output_dir=args.output)
        for path in paths.values():
            print(f"wrote {path}")
    elif args.command == "batch-plan":
        from causal_agent_bench.runners.batch import plan_batch_shards

        manifest = plan_batch_shards(
            args.config,
            shard_by=args.shard_by,
            shard_count=args.shard_count,
            output_dir=args.output_dir,
        )
        print(
            f"planned {manifest['shard_count']} shards "
            f"({manifest['n_expected_total']} expected pairs) under {Path(args.output_dir or 'default batch dir')}"
        )
    elif args.command == "batch-merge":
        from causal_agent_bench.runners.batch import merge_batch_shards

        result = merge_batch_shards(
            args.batch_dir,
            output_dir=args.output_dir,
            auto_score=not args.no_score,
            strict=not args.no_strict,
        )
        print(f"merged run at {result['merged_run_dir']} ({result['n_trajectories']} trajectories)")
    elif args.command == "failure-report":
        from causal_agent_bench.runners.batch import build_failure_report, failure_report_markdown

        report = build_failure_report(args.run_dir)
        out = Path(args.output_dir) if args.output_dir else Path(args.run_dir)
        out.mkdir(parents=True, exist_ok=True)
        report_path = out / "failure_report.json"
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
        md_path = out / "failure_report.md"
        md_path.write_text(failure_report_markdown(report), encoding="utf-8")
        print(f"wrote {report_path}")
        print(f"wrote {md_path}")
    elif args.command == "score":
        from causal_agent_bench.metrics.scoring import score_run

        if not _run_dir_exists(args.run_dir):
            return
        summary = score_run(args.run_dir, allow_incomplete=args.allow_incomplete)
        print(f"wrote scores for {len(summary.by_agent)} agents")
    elif args.command == "analyze":
        from causal_agent_bench.analysis.reports import analyze_run

        if not _run_dir_exists(args.run_dir):
            return
        report_path = analyze_run(args.run_dir, allow_incomplete=args.allow_incomplete)
        print(f"wrote {report_path}")
    elif args.command == "export-paper-assets":
        from causal_agent_bench.analysis.reports import export_paper_assets

        if not _run_dir_exists(args.run_dir):
            return
        paths = export_paper_assets(
            args.run_dir,
            write_global=not args.no_write_global,
            allow_engineering_only=args.allow_engineering_only,
            allow_incomplete=args.allow_incomplete,
            allow_placeholder=args.allow_placeholder,
            allow_mock_stub=args.allow_mock_stub,
        )
        for path in paths:
            print(f"wrote {path}")
    elif args.command == "export-ablation-table":
        from causal_agent_bench.analysis.load_results import load_run_results
        from causal_agent_bench.analysis.tables import (
            ablation_results_table,
            with_asset_metadata,
            write_table_bundle,
        )

        if not _run_dir_exists(args.run_dir):
            return
        guard = validate_export_source(
            args.run_dir,
            allow_engineering_only=args.allow_engineering_only,
            allow_incomplete=args.allow_incomplete,
            allow_placeholder=args.allow_placeholder,
            allow_mock_stub=args.allow_mock_stub,
            operation="export-ablation-table",
        )
        data = load_run_results(args.run_dir)
        output_dir = (
            Path(args.output_dir)
            if args.output_dir
            else Path(args.run_dir) / "paper_assets" / "tables"
        )
        output_dir.mkdir(parents=True, exist_ok=True)
        table = with_asset_metadata(ablation_results_table(data), data)
        paths = write_table_bundle(table, output_dir / "table4_ablation_results")
        _watermark_table_bundle(paths, guard.get("watermark"))
        for path in paths:
            print(f"wrote {path}")
    elif args.command == "ablation-matrix":
        from causal_agent_bench.ablation_matrix import (
            aggregate_ablation_matrix,
            export_ablation_matrix_artifacts,
            load_ablation_matrix_config,
            run_ablation_matrix,
        )

        matrix = load_ablation_matrix_config(args.config)
        matrix_root = (
            Path(args.output_dir)
            if args.output_dir
            else Path(matrix.output_dir) / matrix.run_name
        )
        if args.aggregate_only:
            frame = aggregate_ablation_matrix(matrix_root)
            paths = export_ablation_matrix_artifacts(matrix_root, frame)
            print(f"aggregated {len(frame)} rows from {matrix_root}")
        else:
            manifest = run_ablation_matrix(
                args.config,
                execute=args.execute,
                matrix_output_dir=args.output_dir,
                skip_existing=not args.no_skip_existing,
                replan=args.replan,
            )
            print(
                f"matrix {manifest.get('run_name')}: "
                f"{manifest.get('n_cells')} cells planned"
                + (" and executed" if args.execute else " (plan-only)")
            )
            if args.execute:
                paths = manifest.get("aggregate_paths", [])
            else:
                paths = [str(matrix_root / "matrix_manifest.json"), str(matrix_root / "matrix_plan.md")]
        for path in paths:
            print(f"wrote {path}")
    elif args.command == "export-leaderboard":
        from causal_agent_bench.analysis.leaderboard import export_leaderboard

        if not _run_dir_exists(args.run_dir):
            return
        paths = export_leaderboard(
            args.run_dir,
            args.output_dir,
            eval_split=args.eval_split,
            splits_path=args.splits_path,
            allow_engineering_only=args.allow_engineering_only,
            allow_incomplete=args.allow_incomplete,
            allow_placeholder=args.allow_placeholder,
            allow_mock_stub=args.allow_mock_stub,
        )
        for path in paths:
            print(f"wrote {path}")
    elif args.command == "export-failure-gallery":
        from causal_agent_bench.analysis.failure_gallery_doc import export_failure_gallery_doc

        if args.run_dir and not _run_dir_exists(args.run_dir):
            return
        paths = export_failure_gallery_doc(
            run_dir=args.run_dir,
            doc_path=args.doc_path,
            paper_path=args.paper_path,
            max_per_family=args.max_per_family,
            allow_engineering_only=args.allow_engineering_only,
            allow_incomplete=args.allow_incomplete,
            allow_placeholder=args.allow_placeholder,
            allow_mock_stub=args.allow_mock_stub,
        )
        for path in paths:
            print(f"wrote {path}")
    elif args.command == "mine-errors":
        from causal_agent_bench.analysis.error_analysis import generate_failure_gallery
        from causal_agent_bench.analysis.load_results import load_run_results

        if not _run_dir_exists(args.run_dir):
            return
        data = load_run_results(args.run_dir)
        output_dir = Path(args.output_dir) if args.output_dir else Path(args.run_dir) / "error_cases"
        paths = generate_failure_gallery(
            data,
            output_dir,
            max_cases=args.max_cases,
            include_filters=not args.no_filters,
            include_legacy_aliases=True,
        )
        for path in paths:
            print(f"wrote {path}")
    elif args.command == "doctor":
        from causal_agent_bench.doctor import doctor_failed, print_doctor_report, run_doctor

        checks = run_doctor(repo_root)
        print_doctor_report(checks)
        if doctor_failed(checks):
            raise SystemExit(1)
    elif args.command == "list-providers":
        for row in list_provider_status():
            configured = "configured" if row["configured"] else "not configured"
            env_hint = ", ".join(row["env_vars"]) if row["env_vars"] else "none"
            print(f"{row['provider']}: {configured} (env: {env_hint})")
    elif args.command == "estimate-cost":
        estimate = estimate_config_cost(args.config)
        print(json.dumps(estimate, indent=2, sort_keys=True))
    elif args.command == "validate-config":
        try:
            print(cli_json(validate_config_file(args.config)))
        except Exception as exc:
            print(cli_json(config_error_payload(args.config, exc)))
            raise SystemExit(1) from exc
    elif args.command == "dry-run":
        try:
            output_dir = args.output_dir or None
            print(cli_json(dry_run_config(args.config, output_dir=output_dir)))
        except Exception as exc:
            print(cli_json(config_error_payload(args.config, exc)))
            raise SystemExit(1) from exc
    elif args.command == "audit-contamination":
        from causal_agent_bench.contamination.audit import (
            contamination_report_markdown,
            run_contamination_audit,
        )
        from causal_agent_bench.utils.io import write_json

        output_dir = Path(args.output_dir) if args.output_dir else Path(args.benchmark_dir)
        report = run_contamination_audit(
            args.benchmark_dir,
            splits_path=args.splits_path,
            near_duplicate_threshold=args.near_duplicate_threshold,
        )
        write_json(output_dir / "contamination_audit_report.json", report)
        (output_dir / "contamination_audit_report.md").write_text(
            contamination_report_markdown(report),
            encoding="utf-8",
        )
        print(
            cli_json(
                {
                    "passed": report["passed"],
                    "errors": report.get("summary", {}).get("n_errors"),
                    "warnings": report.get("summary", {}).get("n_warnings"),
                    "json": str(output_dir / "contamination_audit_report.json"),
                    "markdown": str(output_dir / "contamination_audit_report.md"),
                }
            )
        )
        if not report["passed"]:
            raise SystemExit(1)
    elif args.command == "audit-interventions":
        try:
            report = audit_interventions(
                benchmark_dir=args.benchmark_dir,
                base_tasks_path=args.base_tasks,
                interventions_path=args.interventions,
                instances_path=args.instances,
                output_dir=args.output_dir,
            )
        except Exception as exc:
            print(cli_json({"passed": False, "error_type": type(exc).__name__, "message": str(exc)}))
            raise SystemExit(1) from exc
        print(
            cli_json(
                {
                    "passed": report["passed"],
                    "counts": report["counts"],
                    "warnings": report["warnings"],
                    "base_task_issues": len(report["base_task_issues"]),
                    "intervention_issues": len(report["intervention_issues"]),
                    "instance_issues": len(report["instance_issues"]),
                    "validity_score_counts": report.get("validity_score_counts", {}),
                }
            )
        )
    elif args.command == "freeze-dataset":
        try:
            manifest = freeze_dataset(
                args.source_dir,
                version=args.version,
                output_dir=args.output_dir,
                force=args.force,
            )
        except Exception as exc:
            print(cli_json({"frozen": False, "error_type": type(exc).__name__, "message": str(exc)}))
            raise SystemExit(1) from exc
        print(cli_json({"frozen": True, **manifest}))
    elif args.command == "summarize-run":
        try:
            print(cli_json(summarize_run(args.run_dir, output_path=args.output)))
        except Exception as exc:
            print(cli_json({"summarized": False, "error_type": type(exc).__name__, "message": str(exc)}))
            raise SystemExit(1) from exc
    elif args.command == "export-human-validation":
        from causal_agent_bench.analysis.human_validation import export_human_validation_sample

        try:
            print(
                cli_json(
                    export_human_validation_sample(
                        args.run_dir,
                        output_dir=args.output_dir,
                        sample_size=args.sample_size,
                        seed=args.seed,
                        annotators_per_item=args.annotators_per_item,
                        include_html=not args.no_html,
                    )
                )
            )
        except Exception as exc:
            print(cli_json({"exported": False, "error_type": type(exc).__name__, "message": str(exc)}))
            raise SystemExit(1) from exc
    elif args.command == "summarize-human-validation":
        from causal_agent_bench.analysis.human_validation import (
            summarize_human_validation_annotations,
        )

        try:
            print(
                cli_json(
                    summarize_human_validation_annotations(
                        args.annotations,
                        output_dir=args.output_dir,
                    )
                )
            )
        except Exception as exc:
            print(cli_json({"summarized": False, "error_type": type(exc).__name__, "message": str(exc)}))
            raise SystemExit(1) from exc
    elif args.command == "run-llm-judge":
        from causal_agent_bench.analysis.llm_judge import run_llm_judge

        try:
            print(
                cli_json(
                    run_llm_judge(
                        args.run_dir,
                        args.config,
                        output_dir=args.output_dir,
                    )
                )
            )
        except Exception as exc:
            print(cli_json({"judged": False, "error_type": type(exc).__name__, "message": str(exc)}))
            raise SystemExit(1) from exc
    elif args.command == "calibrate-llm-judge":
        from causal_agent_bench.analysis.llm_judge import calibrate_llm_judge

        try:
            print(
                cli_json(
                    calibrate_llm_judge(
                        args.judge_labels,
                        args.human_annotations,
                        output_dir=args.output_dir,
                    )
                )
            )
        except Exception as exc:
            print(cli_json({"calibrated": False, "error_type": type(exc).__name__, "message": str(exc)}))
            raise SystemExit(1) from exc
    elif args.command == "compare-mini-study":
        from causal_agent_bench.analysis.mini_study import compare_mini_study

        try:
            report = compare_mini_study(
                args.template_run_dir,
                args.naturalistic_run_dir,
                output_dir=args.output_dir,
            )
        except Exception as exc:
            print(cli_json({"compared": False, "error_type": type(exc).__name__, "message": str(exc)}))
            raise SystemExit(1) from exc
        print(cli_json({"compared": True, **report}))
    elif args.command == "run-health":
        from causal_agent_bench.safety.run_health import build_run_health_report

        report = build_run_health_report(
            args.repo_root or repo_root,
            results_root=args.results_root,
            output_dir=args.output_dir,
        )
        print(cli_json({"report": report["report_paths"], "total_runs": report["summary"]["total_runs"]}))
    elif args.command == "validate-paper-assets":
        from causal_agent_bench.safety.paper_asset_eligibility import (
            validate_paper_asset_eligibility,
        )

        report = validate_paper_asset_eligibility(
            args.repo_root or repo_root,
            output_dir=args.output_dir,
        )
        print(
            cli_json(
                {
                    "report": report["report_paths"],
                    "flagged": report["flagged_count"],
                    "eligible": report["eligible_count"],
                }
            )
        )
    elif args.command == "claim-evidence":
        from causal_agent_bench.safety.claim_evidence_matrix import build_claim_evidence_matrix

        report = build_claim_evidence_matrix(
            args.repo_root or repo_root,
            ledger_path=args.ledger,
            results_root=args.results_root,
            output_dir=args.output_dir,
            write_tex=not args.no_tex,
        )
        print(cli_json({"report": report["report_paths"], "claims": len(report["claims"])}))
    elif args.command == "paper-todo-inventory":
        from causal_agent_bench.safety.paper_todo_inventory import build_paper_todo_inventory

        report = build_paper_todo_inventory(
            args.repo_root or repo_root,
            output_dir=args.output_dir,
        )
        print(cli_json({"report": report["report_paths"], "items": report["total_items"]}))
    elif args.command == "reproducibility-report":
        from causal_agent_bench.safety.reproducibility_report import build_reproducibility_report

        report = build_reproducibility_report(
            args.repo_root or repo_root,
            output_dir=args.output_dir,
        )
        print(cli_json({"report": report["report_paths"]}))
    elif args.command == "benchmark-quality":
        from causal_agent_bench.safety.benchmark_quality import build_benchmark_quality_report

        report = build_benchmark_quality_report(
            args.repo_root or repo_root,
            benchmark_dir=args.benchmark_dir,
            output_dir=args.output_dir,
        )
        print(cli_json({"report": report["report_paths"], "verdicts": report["verdicts"]}))
    elif args.command == "intervention-isolation-audit":
        from causal_agent_bench.safety.intervention_isolation import (
            build_intervention_isolation_report,
        )

        report = build_intervention_isolation_report(
            args.repo_root or repo_root,
            benchmark_dir=args.benchmark_dir,
            instances_path=args.instances_path,
            output_dir=args.output_dir,
            taxonomy_path=args.taxonomy,
        )
        print(cli_json({"report": report["report_paths"], "summary": report["summary"]}))
    elif args.command == "synthetic-fixture-check":
        from causal_agent_bench.safety.synthetic_fixtures import build_synthetic_fixture_report

        report = build_synthetic_fixture_report(
            args.repo_root or repo_root,
            fixtures_dir=args.fixtures_dir,
            output_dir=args.output_dir,
        )
        print(cli_json({"report": report["report_paths"], "summary": report["summary"]}))
    elif args.command == "human-validation-packet":
        from causal_agent_bench.safety.human_validation_packet import build_human_validation_packet

        report = build_human_validation_packet(
            args.repo_root or repo_root,
            output_dir=args.output_dir,
        )
        print(cli_json({"report": report["report_paths"], "templates": report["templates"]}))
    elif args.command == "estimate-run-cost":
        from causal_agent_bench.safety.run_cost_estimator import build_run_cost_estimate

        report = build_run_cost_estimate(
            args.repo_root or repo_root,
            config_path=args.config,
            output_dir=args.output_dir,
        )
        print(
            cli_json(
                {
                    "report": report["report_paths"],
                    "runnable_without_approval": report["runnable_without_approval"],
                    "estimated_high_cost_usd": report["estimated_high_cost_usd"],
                }
            )
        )
    elif args.command == "method-figure-scaffolds":
        from causal_agent_bench.safety.method_figures import write_method_figure_scaffolds

        report = write_method_figure_scaffolds(
            args.repo_root or repo_root,
            output_dir=args.output_dir,
        )
        print(cli_json({"files": report["files"], "scope": report["scope"]}))
    elif args.command == "release-readiness":
        from causal_agent_bench.safety.release_readiness import build_release_readiness_report

        report = build_release_readiness_report(
            args.repo_root or repo_root,
            output_dir=args.output_dir,
            results_root=args.results_root,
        )
        print(cli_json({"report": report["report_paths"], "verdicts": report["verdicts"]}))
    elif args.command == "dataset-issue-triage":
        from causal_agent_bench.safety.dataset_issue_triage import build_dataset_issue_triage

        report = build_dataset_issue_triage(
            args.repo_root or repo_root,
            benchmark_dir=args.benchmark_dir,
            output_dir=args.output_dir,
        )
        print(cli_json({"report": report["report_paths"], "issues": report["total_issues"]}))
    elif args.command == "provider-pilot-preflight":
        from causal_agent_bench.safety.provider_pilot_preflight import (
            build_provider_pilot_preflight,
        )

        report = build_provider_pilot_preflight(
            args.repo_root or repo_root,
            config_path=args.config,
            output_dir=args.output_dir,
        )
        print(cli_json({"report": report["report_paths"], "verdicts": report["verdicts"]}))
    elif args.command == "human-validation-dry-run-sample":
        from causal_agent_bench.safety.human_validation_sampler import (
            build_human_validation_dry_run_sample,
        )

        report = build_human_validation_dry_run_sample(
            args.repo_root or repo_root,
            fixtures_dir=args.fixtures_dir,
            output_dir=args.output_dir,
        )
        print(cli_json({"report": report["report_paths"], "sample_count": report["sample_count"]}))
    elif args.command == "validity-scorecard":
        from causal_agent_bench.safety.validity_scorecard import build_validity_scorecard

        report = build_validity_scorecard(
            args.repo_root or repo_root,
            benchmark_dir=args.benchmark_dir,
            taxonomy_path=args.taxonomy,
            config_path=args.config,
            output_dir=args.output_dir,
        )
        print(
            cli_json(
                {
                    "report": report["report_paths"],
                    "overall_score": report["overall_score"],
                    "verdicts": report["verdicts"],
                }
            )
        )
    elif args.command == "high-risk-intervention-queue":
        from causal_agent_bench.safety.high_risk_intervention_queue import (
            build_high_risk_intervention_queue,
        )

        report = build_high_risk_intervention_queue(
            args.repo_root or repo_root,
            benchmark_dir=args.benchmark_dir,
            taxonomy_path=args.taxonomy,
            output_dir=args.output_dir,
        )
        print(cli_json({"report": report["report_paths"], "summary": report["summary"]}))
    elif args.command == "neurips-submission-gate":
        from causal_agent_bench.safety.neurips_submission_gate import build_neurips_submission_gate

        report = build_neurips_submission_gate(
            args.repo_root or repo_root,
            reports_dir=args.reports_dir,
            output_dir=args.output_dir,
        )
        print(
            cli_json(
                {
                    "report": report["report_paths"],
                    "verdict": report["verdict"],
                    "gates_passed": report["gates_passed"],
                    "gates_total": report["gates_total"],
                }
            )
        )
    elif args.command == "method-appendix":
        from causal_agent_bench.safety.method_appendix import build_method_appendix

        report = build_method_appendix(args.repo_root or repo_root, output_dir=args.output_dir)
        print(cli_json({"report": report["report_paths"], "scope": report["scope"]}))
    elif args.command == "evidence-dashboard":
        from causal_agent_bench.safety.evidence_dashboard import build_evidence_dashboard

        report = build_evidence_dashboard(
            args.repo_root or repo_root,
            reports_dir=args.reports_dir,
            output_dir=args.output_dir,
        )
        print(cli_json({"report": report["report_paths"], "state": report["current_evidence_state"]}))
    elif args.command == "lint-config-metadata":
        from causal_agent_bench.safety.config_metadata_lint import build_config_metadata_lint

        report = build_config_metadata_lint(
            args.repo_root or repo_root,
            config_dir=args.config_dir,
            output_dir=args.output_dir,
        )
        print(cli_json({"report": report["report_paths"], "issues": report["issue_count"]}))
    elif args.command == "repair-plan":
        from causal_agent_bench.safety.repair_plan import build_repair_plan

        report = build_repair_plan(
            args.repo_root or repo_root,
            input_dir=args.input_dir,
            output_dir=args.output_dir,
        )
        print(cli_json({"report": report["output_paths"], "items": report["summary"]["repair_item_count"]}))
    elif args.command == "benchmark-cards":
        from causal_agent_bench.safety.benchmark_cards import build_benchmark_cards

        report = build_benchmark_cards(
            args.repo_root or repo_root,
            benchmark_dir=args.benchmark_dir,
            output_dir=args.output_dir,
        )
        print(cli_json({"manifest": report["manifest_path"], "files": report["files"]}))
    elif args.command == "validate-gold-outputs":
        from causal_agent_bench.safety.gold_output_validation import build_gold_output_validation

        report = build_gold_output_validation(
            args.repo_root or repo_root,
            benchmark_dir=args.benchmark_dir,
            taxonomy_path=args.taxonomy,
            output_dir=args.output_dir,
        )
        print(cli_json({"report": report["report_paths"], "summary": report["summary"]}))
    elif args.command == "validate-tool-schemas":
        from causal_agent_bench.safety.tool_schema_validation import build_tool_schema_validation

        report = build_tool_schema_validation(
            args.repo_root or repo_root,
            benchmark_dir=args.benchmark_dir,
            output_dir=args.output_dir,
        )
        print(cli_json({"report": report["report_paths"], "summary": report["summary"]}))
    elif args.command == "static-leakage-check":
        from causal_agent_bench.safety.static_leakage import build_static_leakage_report

        report = build_static_leakage_report(
            args.repo_root or repo_root,
            benchmark_dir=args.benchmark_dir,
            output_dir=args.output_dir,
            near_duplicate_threshold=args.near_duplicate_threshold,
        )
        print(cli_json({"report": report["report_paths"], "summary": report["summary"]}))
    elif args.command == "benchmark-manifest":
        from causal_agent_bench.safety.benchmark_manifest import build_benchmark_manifest

        report = build_benchmark_manifest(
            args.repo_root or repo_root,
            output_dir=args.output_dir,
            results_root=args.results_root,
        )
        print(cli_json({"report": report["report_paths"], "readiness": report["readiness"]}))
    elif args.command == "config-profiles":
        from causal_agent_bench.safety.config_profiles import build_config_profiles

        report = build_config_profiles(
            args.repo_root or repo_root,
            config_dir=args.config_dir,
            output_dir=args.output_dir,
        )
        print(cli_json({"report": report["report_paths"], "summary": report["summary"]}))
    elif args.command == "advisor-review-packet":
        from causal_agent_bench.safety.advisor_review_packet import build_advisor_review_packet

        report = build_advisor_review_packet(
            args.repo_root or repo_root,
            reports_dir=args.reports_dir,
            output_dir=args.output_dir,
        )
        print(cli_json({"manifest": report["manifest_path"], "files": report["files"]}))
    elif args.command == "paper-readiness-map":
        from causal_agent_bench.safety.paper_readiness_map import build_paper_readiness_map

        report = build_paper_readiness_map(
            args.repo_root or repo_root,
            reports_dir=args.reports_dir,
            output_dir=args.output_dir,
        )
        print(cli_json({"report": report["report_paths"], "summary": report["summary"]}))
    elif args.command == "report-quality-check":
        from causal_agent_bench.safety.report_quality_check import build_report_quality_check

        report = build_report_quality_check(
            args.repo_root or repo_root,
            input_dir=args.input_dir,
            output_dir=args.output_dir,
        )
        print(cli_json({"report": report["report_paths"], "summary": report["summary"]}))
    elif args.command == "leakage-repair-plan":
        from causal_agent_bench.safety.leakage_repair_planner import build_leakage_repair_plan

        report = build_leakage_repair_plan(
            args.repo_root or repo_root,
            input_dir=args.input_dir,
            output_dir=args.output_dir,
        )
        print(cli_json({"report": report["report_paths"], "summary": report["summary"]}))
    elif args.command == "validate-leakage-patch-manifest":
        from causal_agent_bench.safety.leakage_repair_planner import validate_leakage_patch_manifest

        report = validate_leakage_patch_manifest(
            args.repo_root or repo_root,
            manifest_path=args.manifest,
            output_dir=args.output_dir,
        )
        print(cli_json({"report": report["report_paths"], "summary": report["summary"], "verdicts": report["verdicts"]}))
    elif args.command == "readiness-war-room":
        from causal_agent_bench.safety.readiness_war_room import build_readiness_war_room

        report = build_readiness_war_room(
            args.repo_root or repo_root,
            reports_dir=args.reports_dir,
            output_dir=args.output_dir,
        )
        print(cli_json({"report": report["report_paths"], "mission_status": report["mission_status"]}))
    elif args.command == "governance-os":
        from causal_agent_bench.safety.governance_os import build_governance_os

        report = build_governance_os(
            args.repo_root or repo_root,
            reports_dir=args.reports_dir,
            output_dir=args.output_dir,
        )
        print(cli_json({"report": report["report_paths"], "summary": report["summary"]}))
    elif args.command == "apply-leakage-patch":
        from causal_agent_bench.safety.leakage_repair_applier import (
            apply_leakage_patch,
            build_leakage_patch_preview,
        )

        if args.apply:
            try:
                report = apply_leakage_patch(
                    args.repo_root or repo_root,
                    manifest_path=args.manifest,
                    selected_ops=list(args.selected_op or []),
                    reviewed_ops_path=args.reviewed_ops,
                    reviewed_by=args.reviewed_by,
                    approval_note=args.approval_note,
                    output_dir=args.output_dir,
                )
            except ValueError as exc:
                print(cli_json({"applied": False, "error_type": "ValueError", "message": str(exc)}))
                raise SystemExit(2) from exc
        else:
            report = build_leakage_patch_preview(
                args.repo_root or repo_root,
                manifest_path=args.manifest,
                selected_ops=list(args.selected_op or []),
                output_dir=args.output_dir,
            )
        print(
            cli_json(
                {
                    "report": report["report_paths"],
                    "summary": report["summary"],
                    "verdicts": report["verdicts"],
                    "mode": report["mode"],
                }
            )
        )
    elif args.command == "leakage-suppression-registry":
        from causal_agent_bench.safety.leakage_suppressions import build_suppression_registry_report

        report = build_suppression_registry_report(
            args.repo_root or repo_root,
            path=args.path,
            output_dir=args.output_dir,
        )
        print(
            cli_json(
                {
                    "report": report["report_paths"],
                    "summary": report["summary"],
                    "verdicts": report["verdicts"],
                }
            )
        )
    elif args.command == "reviewed-ops-template":
        from causal_agent_bench.safety.leakage_repair_applier import build_reviewed_ops_template

        try:
            report = build_reviewed_ops_template(
                args.repo_root or repo_root,
                manifest_path=args.manifest,
                output_dir=args.output_dir,
                include_only=args.include,
            )
        except ValueError as exc:
            print(cli_json({"generated": False, "error_type": "ValueError", "message": str(exc)}))
            raise SystemExit(2) from exc
        print(
            cli_json(
                {
                    "report": report["report_paths"],
                    "candidate_count": report["candidate_count"],
                    "include_only": report["include_only"],
                }
            )
        )
    elif args.command == "manual-repair-preview":
        from causal_agent_bench.safety.manual_repair_preview import build_manual_repair_preview

        report = build_manual_repair_preview(
            args.repo_root or repo_root,
            manifest_path=args.manifest,
            output_dir=args.output_dir,
        )
        print(
            cli_json(
                {
                    "report": report["report_paths"],
                    "summary": report["summary"],
                    "verdicts": report["verdicts"],
                }
            )
        )
    elif args.command == "validate-pair-links":
        from causal_agent_bench.safety.pair_link_validator import build_pair_link_report

        report = build_pair_link_report(
            args.repo_root or repo_root,
            benchmark_dir=args.benchmark_dir,
            output_dir=args.output_dir,
        )
        print(
            cli_json(
                {
                    "report": report["report_paths"],
                    "summary": report["summary"],
                    "verdicts": report["verdicts"],
                }
            )
        )
    elif args.command == "next-action-plan":
        from causal_agent_bench.safety.next_action_plan import build_next_action_plan

        report = build_next_action_plan(
            args.repo_root or repo_root,
            reports_dir=args.reports_dir,
            output_dir=args.output_dir,
        )
        print(
            cli_json(
                {
                    "report": report["report_paths"],
                    "summary": report["summary"],
                    "verdicts": report["verdicts"],
                }
            )
        )
    elif args.command == "harden-provider-pilot-config":
        from causal_agent_bench.safety.provider_pilot_config_hardener import (
            build_provider_pilot_config_hardening_report,
        )

        report = build_provider_pilot_config_hardening_report(
            args.repo_root or repo_root,
            config_path=args.config,
            output_dir=args.output_dir,
        )
        print(
            cli_json(
                {
                    "report": report["report_paths"],
                    "summary": report["summary"],
                    "verdicts": report["verdicts"],
                }
            )
        )
    elif args.command == "reproducibility-manifest":
        from causal_agent_bench.safety.reproducibility_manifest import (
            build_reproducibility_manifest,
        )

        report = build_reproducibility_manifest(
            args.repo_root or repo_root,
            output_dir=args.output_dir,
        )
        print(
            cli_json(
                {
                    "report": report["report_paths"],
                    "summary": report["summary"],
                    "verdicts": report["verdicts"],
                }
            )
        )
    elif args.command == "release-blockers":
        from causal_agent_bench.safety.release_blocker_analyzer import build_release_blocker_report

        report = build_release_blocker_report(
            args.repo_root or repo_root,
            reports_dir=args.reports_dir,
            output_dir=args.output_dir,
        )
        print(
            cli_json(
                {
                    "report": report["report_paths"],
                    "summary": report["summary"],
                    "verdicts": report["verdicts"],
                }
            )
        )
    elif args.command == "all-safety-reports":
        from causal_agent_bench.safety.claim_evidence_matrix import build_claim_evidence_matrix
        from causal_agent_bench.safety.paper_asset_eligibility import (
            validate_paper_asset_eligibility,
        )
        from causal_agent_bench.safety.paper_todo_inventory import build_paper_todo_inventory
        from causal_agent_bench.safety.reproducibility_report import build_reproducibility_report
        from causal_agent_bench.safety.run_health import build_run_health_report

        root = args.repo_root or repo_root
        out = args.output_dir
        paths = {}
        paths["run_health"] = build_run_health_report(root, results_root=args.results_root, output_dir=out)[
            "report_paths"
        ]
        paths["paper_assets"] = validate_paper_asset_eligibility(root, output_dir=out)["report_paths"]
        paths["claim_evidence"] = build_claim_evidence_matrix(
            root, results_root=args.results_root, output_dir=out
        )["report_paths"]
        paths["paper_todo"] = build_paper_todo_inventory(root, output_dir=out)["report_paths"]
        paths["reproducibility"] = build_reproducibility_report(root, output_dir=out)["report_paths"]
        print(cli_json({"reports": paths}))
    elif args.command == "all-no-run-reports":
        from causal_agent_bench.safety.advisor_review_packet import build_advisor_review_packet
        from causal_agent_bench.safety.benchmark_cards import build_benchmark_cards
        from causal_agent_bench.safety.benchmark_manifest import build_benchmark_manifest
        from causal_agent_bench.safety.benchmark_quality import build_benchmark_quality_report
        from causal_agent_bench.safety.claim_evidence_matrix import build_claim_evidence_matrix
        from causal_agent_bench.safety.config_metadata_lint import build_config_metadata_lint
        from causal_agent_bench.safety.config_profiles import build_config_profiles
        from causal_agent_bench.safety.dataset_issue_triage import build_dataset_issue_triage
        from causal_agent_bench.safety.evidence_dashboard import build_evidence_dashboard
        from causal_agent_bench.safety.gold_output_validation import build_gold_output_validation
        from causal_agent_bench.safety.governance_os import build_governance_os
        from causal_agent_bench.safety.high_risk_intervention_queue import (
            build_high_risk_intervention_queue,
        )
        from causal_agent_bench.safety.human_validation_packet import build_human_validation_packet
        from causal_agent_bench.safety.human_validation_sampler import (
            build_human_validation_dry_run_sample,
        )
        from causal_agent_bench.safety.intervention_isolation import (
            build_intervention_isolation_report,
        )
        from causal_agent_bench.safety.leakage_repair_planner import (
            build_leakage_repair_plan,
            validate_leakage_patch_manifest,
        )
        from causal_agent_bench.safety.method_appendix import build_method_appendix
        from causal_agent_bench.safety.method_figures import write_method_figure_scaffolds
        from causal_agent_bench.safety.neurips_submission_gate import build_neurips_submission_gate
        from causal_agent_bench.safety.paper_asset_eligibility import (
            validate_paper_asset_eligibility,
        )
        from causal_agent_bench.safety.paper_readiness_map import build_paper_readiness_map
        from causal_agent_bench.safety.paper_todo_inventory import build_paper_todo_inventory
        from causal_agent_bench.safety.provider_pilot_preflight import (
            build_provider_pilot_preflight,
        )
        from causal_agent_bench.safety.readiness_war_room import build_readiness_war_room
        from causal_agent_bench.safety.release_readiness import build_release_readiness_report
        from causal_agent_bench.safety.repair_plan import build_repair_plan
        from causal_agent_bench.safety.report_quality_check import build_report_quality_check
        from causal_agent_bench.safety.run_cost_estimator import build_run_cost_estimate
        from causal_agent_bench.safety.run_health import build_run_health_report
        from causal_agent_bench.safety.static_leakage import build_static_leakage_report
        from causal_agent_bench.safety.synthetic_fixtures import build_synthetic_fixture_report
        from causal_agent_bench.safety.tool_schema_validation import build_tool_schema_validation
        from causal_agent_bench.safety.validity_scorecard import build_validity_scorecard

        root = args.repo_root or repo_root
        out = args.output_dir
        paths = {}
        paths["run_health"] = build_run_health_report(root, results_root=args.results_root, output_dir=out)[
            "report_paths"
        ]
        paths["paper_assets"] = validate_paper_asset_eligibility(root, output_dir=out)["report_paths"]
        paths["claim_evidence"] = build_claim_evidence_matrix(
            root, results_root=args.results_root, output_dir=out, write_tex=False
        )["report_paths"]
        paths["paper_todo"] = build_paper_todo_inventory(root, output_dir=out)["report_paths"]
        paths["benchmark_quality"] = build_benchmark_quality_report(
            root, benchmark_dir=args.benchmark_dir, output_dir=out
        )["report_paths"]
        paths["intervention_isolation"] = build_intervention_isolation_report(
            root, benchmark_dir=args.benchmark_dir, output_dir=out, taxonomy_path=args.taxonomy
        )["report_paths"]
        paths["gold_output_validation"] = build_gold_output_validation(
            root,
            benchmark_dir=args.benchmark_dir,
            taxonomy_path=args.taxonomy,
            output_dir=Path(out) / "gold_outputs",
        )["report_paths"]
        paths["high_risk_intervention_queue"] = build_high_risk_intervention_queue(
            root,
            benchmark_dir=args.benchmark_dir,
            taxonomy_path=args.taxonomy,
            output_dir=Path(out) / "high_risk_interventions",
        )["report_paths"]
        paths["validity_scorecard"] = build_validity_scorecard(
            root,
            benchmark_dir=args.benchmark_dir,
            taxonomy_path=args.taxonomy,
            config_path=args.config,
            output_dir=Path(out) / "validity_scorecard",
        )["report_paths"]
        paths["neurips_submission_gate"] = build_neurips_submission_gate(
            root,
            reports_dir=out,
            output_dir=Path(out) / "neurips_submission_gate",
        )["report_paths"]
        paths["tool_schema_validation"] = build_tool_schema_validation(
            root,
            benchmark_dir=args.benchmark_dir,
            output_dir=Path(out) / "tool_schemas",
        )["report_paths"]
        from causal_agent_bench.safety.pair_link_validator import build_pair_link_report

        paths["pair_link_validation"] = build_pair_link_report(
            root,
            benchmark_dir=args.benchmark_dir,
            output_dir=Path(out) / "pair_link_validator",
        )["report_paths"]
        from causal_agent_bench.safety.leakage_suppressions import build_suppression_registry_report

        paths["leakage_suppression_registry"] = build_suppression_registry_report(
            root, output_dir=Path(out) / "leakage_suppressions"
        )["report_paths"]
        paths["static_leakage"] = build_static_leakage_report(
            root,
            benchmark_dir=args.benchmark_dir,
            output_dir=Path(out) / "static_leakage",
        )["report_paths"]
        paths["dataset_issue_triage"] = build_dataset_issue_triage(
            root, benchmark_dir=args.benchmark_dir, output_dir=out
        )["report_paths"]
        from causal_agent_bench.safety.provider_pilot_config_hardener import (
            build_provider_pilot_config_hardening_report,
        )

        paths["provider_pilot_config_hardening"] = build_provider_pilot_config_hardening_report(
            root,
            config_path=args.config,
            output_dir=Path(out) / "provider_pilot_config_hardening",
        )["report_paths"]
        paths["config_metadata_lint"] = build_config_metadata_lint(root, output_dir=out)["report_paths"]
        paths["release_readiness"] = build_release_readiness_report(
            root, output_dir=out, results_root=args.results_root
        )["report_paths"]
        leakage_repair = build_leakage_repair_plan(
            root, input_dir=out, output_dir=Path(out) / "leakage_repair_plan"
        )
        paths["leakage_repair_plan"] = leakage_repair["report_paths"]
        paths["leakage_patch_validation"] = validate_leakage_patch_manifest(
            root,
            manifest_path=leakage_repair["patch_manifest_paths"]["json"],
            output_dir=Path(out) / "leakage_repair_plan",
        )["report_paths"]
        from causal_agent_bench.safety.leakage_repair_applier import build_reviewed_ops_template
        from causal_agent_bench.safety.manual_repair_preview import build_manual_repair_preview

        paths["reviewed_ops_template"] = build_reviewed_ops_template(
            root,
            manifest_path=leakage_repair["patch_manifest_paths"]["json"],
            output_dir=Path(out) / "leakage_repair_apply",
            include_only="safe_to_auto_patch",
        )["report_paths"]
        paths["manual_repair_preview"] = build_manual_repair_preview(
            root,
            manifest_path=leakage_repair["patch_manifest_paths"]["json"],
            output_dir=Path(out) / "manual_repair_preview",
        )["report_paths"]
        from causal_agent_bench.safety.answer_leakage_repair import (
            build_answer_leakage_repair_packet,
        )
        from causal_agent_bench.safety.split_metadata_repair import (
            build_split_metadata_repair_preview,
        )

        paths["answer_leakage_repair"] = build_answer_leakage_repair_packet(
            root,
            leakage_report_path=Path(out) / "static_leakage" / "static_leakage_report.json",
            output_dir=Path(out) / "answer_leakage_repair",
        )["report_paths"]
        paths["split_metadata_repair"] = build_split_metadata_repair_preview(
            root,
            leakage_report_path=Path(out) / "static_leakage" / "static_leakage_report.json",
            output_dir=Path(out) / "split_metadata_repair",
        )["report_paths"]
        paths["provider_pilot_preflight"] = build_provider_pilot_preflight(
            root,
            config_path=args.config,
            output_dir=out,
            reports_dir=out,
        )["report_paths"]
        paths["repair_plan"] = build_repair_plan(
            root, input_dir=out, output_dir=Path(out) / "repair_plan"
        )["output_paths"]
        paths["benchmark_cards"] = build_benchmark_cards(
            root,
            benchmark_dir=args.benchmark_dir,
            output_dir=Path(out) / "benchmark_cards",
            reports_dir=out,
        )["files"]
        paths["benchmark_manifest"] = build_benchmark_manifest(
            root,
            output_dir=Path(out) / "benchmark_manifest",
            results_root=args.results_root,
        )["report_paths"]
        paths["config_profiles"] = build_config_profiles(
            root,
            output_dir=Path(out) / "config_profiles",
        )["report_paths"]
        paths["advisor_review_packet"] = build_advisor_review_packet(
            root,
            reports_dir=out,
            output_dir=Path(out) / "advisor_review",
        )["files"]
        paths["paper_readiness_map"] = build_paper_readiness_map(
            root,
            reports_dir=out,
            output_dir=Path(out) / "paper_readiness",
        )["report_paths"]
        paths["synthetic_fixtures"] = build_synthetic_fixture_report(
            root, fixtures_dir=args.fixtures_dir, output_dir=out
        )["report_paths"]
        paths["human_validation_packet"] = build_human_validation_packet(root, output_dir=out)["report_paths"]
        paths["human_validation_dry_run_sample"] = build_human_validation_dry_run_sample(
            root, fixtures_dir=args.fixtures_dir, output_dir=Path(out) / "human_validation_dry_run"
        )["report_paths"]
        paths["run_cost_estimate"] = build_run_cost_estimate(
            root, config_path=args.config, output_dir=out
        )["report_paths"]
        paths["method_figures"] = write_method_figure_scaffolds(
            root, output_dir=Path(out) / "method_figures"
        )["files"]
        paths["method_appendix"] = build_method_appendix(
            root, output_dir=Path(out) / "method_appendix"
        )["report_paths"]
        from causal_agent_bench.safety.reproducibility_manifest import (
            build_reproducibility_manifest,
        )

        paths["reproducibility_manifest"] = build_reproducibility_manifest(
            root, output_dir=Path(out) / "reproducibility_manifest"
        )["report_paths"]
        paths["readiness_war_room"] = build_readiness_war_room(
            root, reports_dir=out, output_dir=Path(out) / "readiness_war_room"
        )["report_paths"]
        paths["governance_os"] = build_governance_os(
            root, reports_dir=out, output_dir=Path(out) / "governance_os"
        )["report_paths"]
        paths["evidence_dashboard"] = build_evidence_dashboard(
            root, reports_dir=out, output_dir=Path(out) / "evidence_dashboard"
        )["report_paths"]
        paths["report_quality_check"] = build_report_quality_check(
            root, input_dir=out, output_dir=Path(out) / "report_quality"
        )["report_paths"]
        from causal_agent_bench.safety.next_action_plan import build_next_action_plan

        paths["next_action_plan"] = build_next_action_plan(
            root, reports_dir=out, output_dir=Path(out) / "next_action_plan"
        )["report_paths"]
        from causal_agent_bench.safety.release_blocker_analyzer import build_release_blocker_report

        paths["release_blocker_report"] = build_release_blocker_report(
            root, reports_dir=out, output_dir=Path(out) / "release_blockers"
        )["report_paths"]
        from causal_agent_bench.safety.publication_readiness import (
            build_publication_readiness_report,
        )

        paths["publication_readiness"] = build_publication_readiness_report(
            root, reports_dir=out, output_dir=Path(out) / "publication_readiness"
        )["report_paths"]
        from causal_agent_bench.safety.god_tier_status import build_god_tier_status

        paths["god_tier_status"] = build_god_tier_status(
            root, reports_dir=out, output_dir=Path(out) / "god_tier_status"
        )["report_paths"]
        print(cli_json({"reports": paths, "safety": "static_no_run_only"}))
    elif args.command == "fill-paper-from-run":
        from causal_agent_bench.analysis.paper_fill import fill_paper_from_run

        try:
            report = fill_paper_from_run(
                args.run_dir,
                repo_root=args.repo_root or Path.cwd(),
                allow_engineering_only=args.allow_engineering_only,
                allow_incomplete=args.allow_incomplete,
                allow_placeholder=args.allow_placeholder,
                allow_mock_stub=args.allow_mock_stub,
                export_assets=not args.no_export,
                update_ledger=not args.no_ledger,
                promote_to_supported=args.promote_to_supported,
            )
        except Exception as exc:
            print(cli_json({"filled": False, "error_type": type(exc).__name__, "message": str(exc)}))
            raise SystemExit(1) from exc
        print(cli_json({"filled": True, **report}))
    elif args.command == "compare-web-shadow":
        from causal_agent_bench.analysis.web_shadow_study import compare_web_shadow_interfaces

        try:
            report = compare_web_shadow_interfaces(
                args.api_run_dir,
                args.web_run_dir,
                output_dir=args.output_dir,
            )
        except Exception as exc:
            print(cli_json({"compared": False, "error_type": type(exc).__name__, "message": str(exc)}))
            raise SystemExit(1) from exc
        print(cli_json({"compared": True, **report}))
    elif args.command == "update-claim-ledger":
        try:
            if args.run_dir:
                result = update_claim_ledger_from_run(
                    args.ledger,
                    args.run_dir,
                    repo_root=args.repo_root or repo_root,
                    claim_ids=[args.claim_id] if args.claim_id else None,
                    status=args.status,
                    notes=args.notes,
                    promote_to_supported=args.promote_to_supported,
                )
            else:
                result = update_claim_ledger(
                    args.ledger,
                    claim_id=args.claim_id,
                    status=args.status,
                    evidence_paths=args.evidence_path,
                    linked_run_dirs=args.linked_run_dir,
                    notes=args.notes,
                    blocking_items=args.blocking_item,
                    repo_root=args.repo_root or repo_root,
                    force_manual_supported=args.force_manual_supported,
                )
        except Exception as exc:
            print(cli_json({"updated": False, "error_type": type(exc).__name__, "message": str(exc)}))
            raise SystemExit(1) from exc
        print(cli_json(result))


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


def _watermark_table_bundle(paths: list[Path], watermark: str | None) -> None:
    if not watermark:
        return
    for path in paths:
        if path.suffix in {".md", ".tex"}:
            path.write_text(
                apply_export_watermark(path.read_text(encoding="utf-8"), watermark),
                encoding="utf-8",
            )
        elif path.suffix == ".csv":
            text = path.read_text(encoding="utf-8")
            if watermark not in text:
                path.write_text(f"# {watermark}\n{text}", encoding="utf-8")


if __name__ == "__main__":
    main()
