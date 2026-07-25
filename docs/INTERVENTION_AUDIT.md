# Intervention Audit

`audit-interventions` checks whether generated intervention instances preserve the benchmark's single-factor-change discipline. It is an automated audit aid, not a substitute for expert or human validation.

Run it on a generated benchmark directory:

```bash
python -m causal_agent_bench audit-interventions --benchmark-dir data/processed/pilot_v0_1
```

The command writes:

- `intervention_audit_report.json`
- `intervention_audit_report.md`

Each intervention family has an audit guide in `causal_agent_bench.generation.interventions` defining the target factor, non-target factors that should remain stable, expected robust behavior, whether the final answer should change, acceptable severity range, and invalid examples. Generated interventions copy this guide metadata into each `InterventionSpec`.

The report checks:

- user-goal preservation metadata,
- required-tool availability for non-target tools,
- ground-truth validity or explicit scoring override policy,
- patch isolation and patch-field limits,
- expected behavior and robust behavior metadata,
- scoring notes aligned with the expected final-answer behavior.

Every instance receives an `instance_validity_scores` row with `score: pass`, `warning`, or `fail`. A `fail` means the instance or its linked base task/intervention has audit issues. A `warning` means the instance has no hard audit failure but needs reviewer attention, such as high intervention-validity risk or expected changed-answer scoring.

The JSON report also includes `provenance` with input paths, benchmark directory, output directory, git commit when available, generation config hash, benchmark version, and generation seed when a `generation_report.json` is present.
