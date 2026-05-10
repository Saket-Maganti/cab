# Metrics

CausalAgentBench scoring is deterministic by default. The current implementation is intended to be auditable and reproducible, not a final substitute for human validation.

## Output Files

Running `python -m causal_agent_bench score --run-dir <run_dir>` writes:

- `scores.jsonl`: one `ScoreRecord` per trajectory.
- `aggregate_scores.json`: aggregate metrics by agent, instance, and intervention family.
- `aggregate_scores.csv`: compact agent-level table.
- `score_report.md`: human-readable scoring report.
- `scores.json`: compatibility summary for earlier analysis helpers.

## Final Task Success

- `final_success_binary`: 1 when the final answer contains all expected answer fragments; otherwise 0.
- `final_success_partial`: fraction of expected fragments found in the final answer.

For schema-native tasks, expected fragments come from `TaskGoal.expected_final_answer`. For legacy smoke tasks, they come from `ExpectedBehavior.final_answer_contains` or the first acceptable answer.

Future extension: human or LLM-assisted grading can replace or supplement this deterministic heuristic, but default tests must not depend on it.

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

- `tool_error_recovery_binary`: true if the agent retries appropriately, uses a different tool, or acknowledges uncertainty instead of blindly finalizing.
- `steps_to_recovery`: number of steps from first failure to recovery action.
- `repeated_failed_call_count`: repeated calls to a tool after that tool already failed or returned corrupted output.

If no failure occurs, recovery is reported as `null` where appropriate.

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
