# Interventions

CausalAgentBench creates paired clean and intervened tasks. Each intervention keeps the high-level user goal family fixed while changing one controlled factor.

## Families

| Family | Targeted factor | Realistic analogue | Expected robust behavior |
|---|---|---|---|
| `tool_removal` | Tool availability | API disabled, permission missing, connector not installed | Use an alternative route or disclose the limitation. |
| `tool_failure` | Tool reliability | Timeout, rate limit, 500 error, partial response | Retry sensibly, switch tools, or qualify uncertainty. |
| `tool_corruption` | Tool output correctness | Stale cache, parser bug, wrong row returned | Cross-check suspicious data before finalizing. |
| `irrelevant_tools` | Tool-set distractors | Bloated plugin/tool list | Ignore irrelevant tools and avoid gratuitous calls. |
| `memory_corruption` | Memory correctness | Outdated profile, stale prior task state | Verify memory against current evidence. |
| `observation_conflict` | Evidence consistency | Two systems disagree, policy conflicts with ticket text | Detect conflict and state a resolution basis or uncertainty. |
| `ambiguous_instruction` | Instruction specificity | User omits a criterion | Ask for clarification or state a bounded assumption. |
| `long_horizon_dependency` | Cross-step state tracking | Later API call depends on earlier ID/value | Preserve intermediate observations and use them correctly. |
| `premature_success_signal` | Completion signal | UI says done before backend state is verified | Continue until success criteria are actually satisfied. |
| `distractor_evidence` | Evidence relevance | Search result shares keywords but answers another question | Separate relevant evidence from plausible noise. |

## Audit Principle

Every intervention should be inspectable from JSONL and should name the changed field in one of the structured patch fields:

- `tool_availability_patch`
- `memory_patch`
- `tool_output_patch`
- `instruction_patch`

Generated interventions also include `metadata.final_answer_should_change` and `metadata.designed_failure_mode`.

## Generation Process

The schema-native generator lives in `src/causal_agent_bench/generation/`. For each `BaseTask`, it creates one clean `BenchmarkInstance` and a configurable number of intervention instances. Each intervention links back to the clean task with `base_task_id`.

The generator tries to change one factor per intervention:

- tool availability for `tool_removal` and `irrelevant_tools`
- tool reliability/output for `tool_failure`, `tool_corruption`, `observation_conflict`, `long_horizon_dependency`, `premature_success_signal`, and `distractor_evidence`
- memory for `memory_corruption`
- instruction wording for `ambiguous_instruction`

This is a design target, not a proven causal guarantee. Human review is still required before making strong causal claims.

## Why This Is Not Just Random Perturbation

The benchmark intervention is paired with a clean instance and records the intended changed factor, expected robust behavior, severity, and designed failure mode. Ordinary benchmark perturbations often ask whether performance changes; CausalAgentBench asks which skill component failed under a named environmental change. That distinction is only valid if the intervention really isolates the intended factor, which is why the human audit remains required.

## Realism Limitations

The simulated interventions are deliberately controlled and therefore less messy than production failures. Real systems may combine multiple failures at once: an unavailable tool may also change latency, authentication, user expectations, and available evidence. The first benchmark version prioritizes causal attribution and reproducibility over deployment realism. Later versions should add messier multi-factor stress tests only after the single-factor suite is audited.

## TODO

Add pairwise human review to verify that each intervention changes exactly one causal factor.
