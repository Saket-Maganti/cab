from causal_agent_bench.cli_parsers import build_parser


def test_final_hostile_cli_surface_is_complete() -> None:
    parser = build_parser()
    commands = (
        "exposed-candidate-check",
        "new-compact-novelty-check",
        "primitive-evidence-check",
        "stage1-black-box-check",
        "actual-tool-gold-check",
        "expected-fact-injection-check",
        "causal-route-check",
        "recovery-isolation-check",
        "power-calibration-check",
        "exact-head-release-check",
        "scientific-freeze-check",
        "hostile-pre-run-check",
    )
    for command in commands:
        args = parser.parse_args(["final", command])
        assert args.command == "final"
        assert args.final_command == command
