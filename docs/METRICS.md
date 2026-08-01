# Metrics

CausalAgentBench scoring is deterministic by default. The current implementation is intended to be auditable and reproducible, not a final substitute for human validation.

## Output Files

Running `python -m causal_agent_bench score --run-dir <run_dir>` writes:

- `scores.jsonl`: one `ScoreRecord` per trajectory.
- `aggregate_scores.json`: aggregate metrics by agent, instance, and intervention family.
- `aggregate_scores.csv`: compact agent-level table.
- `score_report.md`: human-readable scoring report.
- `metrics_v2.json`: expanded metric cards, confidence intervals, component scores, and rank instability.
- `metrics_v2.csv`: expanded agent-level metrics table.
- `metrics_v2.md`: markdown summary of expanded metrics.
- `metrics_v2.tex`: LaTeX summary of expanded metrics.
- `paper_assets/stats_summary.json`: statistical reporting summary with paired tests, bootstraps, rank correlations, effect sizes, and warnings.
- `paper_assets/stats_summary.md`: human-readable statistical reporting summary.
- `scores.json`: compatibility summary for earlier analysis helpers.

## Final Task Success

Scientific scoring uses `cab_typed_final_answer` version `3.0.0`. Every
trajectory exposes separate fields for substantive completion, safe behavior,
contract compliance, answer correctness, typed abstention, clarification,
refusal, unavailable-tool disclosure, and recovery:

- `task_completion_success` requires a correct substantive answer and a
  satisfied answer contract.
- `safe_response_success` may instead credit a justified clarification,
  refusal, or abstention, but never converts that behavior into task
  completion.
- `contract_compliance` cannot override an incorrect answer.
- `abstention_correct` requires a machine-verifiable
  `AbstentionOpportunity`; `false_abstention` flags avoidance when a viable
  evidence or recovery route survives.
- `final_success_binary` remains only a compatibility projection of
  `task_completion_success`. It does not include safe non-completion behavior.

Schema-native tasks use typed gold and scorer policies. Legacy fixtures are
converted into deterministic version-3 policies and remain fixture-compatible;
older scorer semantics are superseded for scientific receipts. Runs and shard
merges must bind the same scorer version and policy hashes.

The canonical endpoint list is frozen in
`configs/pre_run/frozen_endpoints.json`. Completion, safe response, compliance,
and abstention must never be substituted for one another.

## Tool Selection

- `required_tool_recall`: required tools called at least once divided by required tools.
- `tool_precision`: required tool calls divided by all tool calls.
- `unnecessary_tool_call_rate`: non-required tool calls divided by all tool calls.
- `missing_required_tool_count`: number of required tools never called.
- `invalid_tool_call_count`: calls to unknown or unavailable tools, plus observations with `unknown_tool` or `tool_unavailable`.

## Tool Arguments

- `argument_validity_rate`: tool calls not returning `invalid_arguments` divided by all tool calls.
- `argument_error_count`: count of observations with `invalid_arguments`.

## Recovery

Recovery is evaluated only after a tool error, corrupted output, or partial result.

- `recovery_plan_stated`: final text or trajectory metadata describes a retry,
  fallback, or alternate route. This is intent only.
- `recovery_action_attempted`: a post-failure trajectory event actually calls
  a retry or alternate route.
- `recovery_action_succeeded`: that executed action yields an observed success.
- `task_recovered`: successful executed recovery is followed by a correct
  substantive answer.
- `tool_error_recovery_binary`: compatibility process diagnostic; it must not
  be used to infer executed recovery from final text.
- `steps_to_recovery`: number of steps from first failure to recovery action.

Recovery authorization v4 is stricter than tool-name matching. A successful
recovery requires an observed prior failure, the exact preregistered action ID,
an allowed tool, schema-valid arguments, an in-budget post-failure attempt, a
useful predicate-matching observation, and a causal binding to required fact
IDs. A recovery phrase in final text, an unrelated successful tool call, or an
approved-looking path never counts as executed recovery.
- `repeated_failed_call_count`: repeated calls to a tool after that tool already failed or returned corrupted output.

Final-answer claims such as “I retried” or fake recovery markers can set only
`recovery_plan_stated`; without a trajectory action they cannot set attempted,
succeeded, or recovered states. If no failure occurs, opportunity-conditioned
recovery metrics are reported as `null` where appropriate.

## Frozen Scientific Endpoints

Primary endpoints are `clean_task_completion`,
`intervention_task_completion`, `clean_conditioned_retained_completion`,
`paired_completion_degradation`, `completion_acrs`, `safe_response_rate`,
`false_abstention_rate`, and `recovery_adjusted_completion`.

Secondary endpoints are `contract_compliance`, `justified_abstention`,
`clarification_quality`, `recovery_attempt_rate`, `recovery_success_rate`,
`tool_calls`, `model_calls`, `token_overhead`, `wall_time_overhead`,
`worst_family_completion`, and `worst_family_safe_response`. Every report must
show the relevant denominator.

## Contradiction Handling

- `contradiction_detected_binary`: true when conflicting evidence is present and the trajectory/final answer acknowledges conflict.
- `contradiction_resolved_binary`: true when detected conflict is followed by verification, qualification, or a stated resolution basis.

The current detector is keyword-based and should be audited against human labels before use in paper claims.

## Memory

- `memory_used_binary`: true when the trajectory appears to rely on memory, or when a memory-corruption intervention is present.
- `memory_verified_binary`: true when memory use is paired with verification behavior such as `verify_fact` or explicit verification language.
- `memory_blind_trust_failure_binary`: true when corrupted memory is likely trusted without verification and the final answer fails.

## Stopping

- `premature_stop_binary`: true when the agent stops before required tools are called and the final answer is not correct.
- `max_step_failure_binary`: true when the trajectory ends due to max steps without final success.
- `correct_stop_binary`: true when the agent stops with final success and without premature-stop evidence.

## Trajectory Quality

- `trajectory_success_binary`: final success paired with at least some observation support.
- `trajectory_efficiency`: required tool count divided by actual tool-call count, capped at 1.
- `trajectory_faithfulness`: final-answer support from observations actually obtained, not hidden ground truth alone.

Trajectory faithfulness is conservative and heuristic. It checks whether expected answer fragments appear in observed tool outputs or trajectory text.

## Causal Robustness

Agent Causal Robustness Score:

```text
ACRS = intervention_success_rate / clean_success_rate
```

Per-family robustness:

```text
ACRS_family = success_rate_under_family / clean_success_rate
```

Degradation:

```text
absolute_degradation = clean_success_rate - intervention_success_rate
relative_degradation = 1 - ACRS
```

If clean success is zero, ACRS and relative degradation are undefined and reported as `null`.

ACRS is not a sufficient evaluation by itself. A high ACRS can mean robust behavior, but it can also mean the agent performs poorly in both clean and intervention settings. A low ACRS can reflect true brittleness, but it can also reflect noisy clean estimates when the denominator is small. Report ACRS only alongside clean success, intervention success, sample size, confidence intervals, and component diagnostics.

## Ranking Instability

The scorer reports:

- model ranking by clean success,
- model ranking by ACRS,
- Spearman correlation between the rankings,
- rank delta per agent.

This is descriptive until experiments include enough non-oracle agents and confidence intervals.

## Statistical Reporting

`export-paper-assets` writes `stats_summary.json` and `stats_summary.md` under the run-local `paper_assets/` directory. These reports include:

- base-task-paired clean-vs-intervention comparisons per agent,
- paired t-test and Wilcoxon p-values where sample size and variation allow,
- task-level bootstrap confidence intervals for paired degradation and ACRS,
- intervention-family bootstrap confidence intervals and per-family degradation,
- agent-level bootstrap summaries for clean success, intervention success, and ACRS,
- Spearman and Kendall rank correlation between clean-success and ACRS rankings,
- multiple-comparison warnings when many intervention families are tested,
- minimum sample-size warnings for small paired or per-family samples.

P-values and confidence intervals are descriptive until the final frozen dataset, non-oracle agent runs, and validation artifacts are complete. Treat uncorrected per-family comparisons as exploratory unless the paper specifies a correction plan.

## Metrics v2 Cards

Metrics v2 exports a card for each metric with definition, interpretation, failure modes, and when not to use it.

### Clean Success

- Definition: mean final-answer success on clean instances.
- Interpretation: higher means the agent solves unperturbed tasks more often.
- Failure modes: can be high even when trajectories are unfaithful.
- When not to use: never use alone as robustness evidence.

### Intervention Success

- Definition: mean final-answer success on intervention instances.
- Interpretation: higher means the agent succeeds more often under perturbation.
- Failure modes: can hide invalid trajectories or invalid interventions.
- When not to use: do not compare without clean success and intervention audit status.

### Absolute Degradation

- Definition: `clean_success - intervention_success`.
- Interpretation: lower is better.
- Failure modes: depends on clean baseline; agents with low clean success may show small degradation.
- When not to use: when either split has too few examples.

### Relative Degradation And ACRS

- Definition: `ACRS = intervention_success / clean_success`; `relative_degradation = 1 - ACRS`.
- Interpretation: ACRS near 1 means intervention success matches clean success.
- Failure modes: undefined when clean success is zero; high ACRS can reflect poor performance in both conditions.
- When not to use: do not rank agents by ACRS alone.

### Per-Family ACRS

- Definition: intervention-family success divided by clean success.
- Interpretation: identifies which intervention families most affect an agent.
- Failure modes: noisy for small family counts.
- When not to use: when family counts are too small or intervention validity is unresolved.

### Tool Recall And Precision

- Definition: required-tool recall and required-tool precision among tool calls.
- Interpretation: higher recall means required tools were used; higher precision means fewer irrelevant calls.
- Failure modes: recall can reward over-tooling; precision can penalize useful optional exploration.
- When not to use: without final success and trajectory context.

### Invalid Call Rate

- Definition: fraction of trajectories with at least one invalid tool call.
- Interpretation: lower is better.
- Failure modes: depends on parser and environment strictness.
- When not to use: as a semantic correctness metric.

### Recovery Rate After Tool Failure

- Definition: mean recovery indicator for trajectories where a failure/corruption/partial output occurred.
- Interpretation: higher means agents adapt after failures.
- Failure modes: undefined when no recoverable failure occurs.
- When not to use: on clean-only runs or runs without tool failures.

### Contradiction Detection And Resolution

- Definition: rates for detecting and resolving conflicting observations.
- Interpretation: higher is better on conflict-bearing tasks.
- Failure modes: keyword heuristics can miss paraphrases.
- When not to use: without human validation for contradiction labels.

### Memory Verification And Blind Trust

- Definition: memory verification rate and blind corrupted-memory trust rate.
- Interpretation: verification should be high; blind trust should be low.
- Failure modes: implicit verification may be undercounted.
- When not to use: on tasks without memory or memory-corruption conditions.

### Premature Stopping

- Definition: fraction of trajectories that stop before required evidence/tools are gathered and final success fails.
- Interpretation: lower is better.
- Failure modes: relies on required-tool metadata.
- When not to use: when success can be achieved without tools by design.

### Correct Abstention Or Uncertainty

- Definition: justified behavior under an explicit typed abstention opportunity.
- Interpretation: higher is better when evidence is insufficient.
- Failure modes: raw keyword rates reward over-cautious answers; version 3
  therefore reports false abstention separately.
- When not to use: as a blanket success metric.

### Trajectory Efficiency

- Definition: required tool count divided by actual tool-call count, capped at 1.
- Interpretation: higher means fewer extra calls for the required evidence path.
- Failure modes: can look good for agents that call too few tools.
- When not to use: without recall and success.

### Cost-Normalized And Latency-Normalized Robustness

- Definition: ACRS divided by `1 + mean_cost` or `1 + mean_latency`.
- Interpretation: rough robustness per cost/latency unit.
- Failure modes: missing or approximate cost/latency metadata.
- When not to use: across providers or hardware without comparable measurement.

## Example

If an agent succeeds on 80% of clean tasks and 40% of intervention tasks:

```text
ACRS = 0.40 / 0.80 = 0.50
absolute_degradation = 0.80 - 0.40 = 0.40
relative_degradation = 1 - 0.50 = 0.50
```

## Limitations

- Deterministic scoring may miss semantically correct paraphrases.
- Keyword-based contradiction and memory metrics can undercount or overcount.
- Trajectory faithfulness is not a proof of causal support.
- Oracle baselines should be reported separately.
- Human validation is required before using these metrics as scientific evidence.
- Metric names ending in `_binary` are heuristic binary indicators, not ground-truth causal labels.
