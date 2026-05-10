# Dataset Card

## Dataset Name

CausalAgentBench synthetic task instances.

## Intended Use

This dataset is intended for controlled research on tool-using language agents under paired clean and intervention conditions. It supports debugging, method development, metric auditing, and reproducibility checks for interventional agent evaluation.

## Out-of-Scope Use

- Treating smoke or development results as a public leaderboard.
- Claiming real-world agent reliability from synthetic tasks alone.
- Training agents directly on benchmark instances and reporting contaminated evaluations.
- Evaluating live email, calendar, payment, booking, or web actions.

## Data Source and Construction Process

All default tasks are synthetic and generated from deterministic templates in `src/causal_agent_bench/generation/`. The older smoke helper in `src/causal_agent_bench/task.py` is retained for backward compatibility. No live web data, private user data, or paid API outputs are used.

Generation configs specify seed, number of base tasks, domain set, difficulty mix, interventions per task, and output directory. The generator writes base tasks, interventions, benchmark instances, a generation report, and a quality report.

## Task Domains

- Travel planning
- Calendar/email workflow
- File and spreadsheet QA
- Shopping/comparison
- Research assistant tasks
- Policy/compliance tasks
- Coding/debugging tasks
- Multi-hop operational planning

## Intervention Families

- Tool removal
- Tool failure
- Tool corruption
- Irrelevant tools
- Memory corruption
- Observation conflict
- Ambiguous instruction
- Long-horizon dependency
- Premature success signal
- Distractor evidence

## Data Fields

Schema-native generated datasets are stored as JSONL:

- `base_tasks.jsonl`: rows validate as `BaseTask`.
- `interventions.jsonl`: rows validate as `InterventionSpec`.
- `instances.jsonl`: rows validate as `BenchmarkInstance`.
- `generation_report.json`: config hash and output counts.
- `quality_report.md`: quality-check summary.

Each base task includes user instruction, available tools, hidden ground truth, success criteria, required information, forbidden assumptions, expected final answer, gold tool sequence, max steps, difficulty, tags, and metadata.

## Evaluation Metrics

The default scorer reports final success, partial success, tool-selection metrics, argument validity, recovery, contradiction handling, memory verification, stopping behavior, trajectory quality, ACRS, per-family robustness, rank instability, and failure-mode diagnostics.

## Generated Splits

- `configs/dev_20_tasks.yaml`: 20 base tasks, 3 interventions per task.
- `configs/main_200_tasks.yaml`: 200 base tasks, 5 interventions per task.

These configs are templates until the final paper dataset is frozen.

## Known Limitations

The first dataset is template-based. More diverse human-authored tasks, annotation audits, held-out templates, and human validation are required before publication claims. Controlled interventions may still change multiple factors; this risk is tracked in Claim C10.

## Licensing TODO

Specify the final dataset license before release. The current repository license applies to code unless a separate dataset license is added.

## Maintenance Plan

Planned maintenance includes versioned dataset releases, schema migration notes, held-out templates, changelogs for intervention families, and archived run artifacts for paper results.
