# Generation Rules

Generated CausalAgentBench data is synthetic, deterministic, and schema-first.

## Base Tasks

- Each base task must validate as `BaseTask`.
- Each base task must include a user instruction, success criteria, required information, forbidden assumptions, expected final answer, hidden ground truth, gold tool sequence, difficulty, tags, and max step budget.
- Difficulty controls the approximate number of required tool steps:
  - `easy`: one or two tools, direct answer.
  - `medium`: three to four tools, multi-step.
  - `hard`: five or more steps, dependency across observations, possible conflict.
  - `stress`: long-horizon or multiple constraints.

## Interventions

- Each intervention must validate as `InterventionSpec`.
- Each intervention links to exactly one base task through `base_task_id`.
- Each intervention should modify one patch group where possible: tool availability, memory, tool output, or instruction.
- Each intervention must include expected robust behavior and designed failure mode metadata.
- The intended final answer should usually remain unchanged; exceptions must be explicit in metadata.

## Instances

- Every base task must have one clean instance.
- Every intervention must produce one intervention instance.
- Instance ids must be unique.
- Generated files must include `base_tasks.jsonl`, `interventions.jsonl`, `instances.jsonl`, `generation_report.json`, and `quality_report.md`.

## Quality Gate

The quality checker flags missing expected answers, no required tools, multi-factor interventions, impossible step budgets, ambiguous success criteria, tool-sequence mismatches, missing expected intervention behavior, and duplicate instances.
