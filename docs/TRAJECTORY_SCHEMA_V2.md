# Trajectory Schema v2

CausalAgentBench uses trajectory logs to explain why an agent succeeded or failed. Final-answer
scores alone are not enough for the paper claims, so Schema v2 records raw model behavior, parsed
actions, tool evidence, parser failures, recovery markers, and cost metadata in an auditable format.

Schema v2 is backward compatible with earlier `trajectories.jsonl` files. Older records can be
validated with:

```bash
python -m causal_agent_bench validate results/<run>/trajectories.jsonl --schema trajectories_v2
```

## Root Fields

| Field | Meaning | Why It Matters |
|---|---|---|
| `schema_version` | Always `trajectory_v2` for v2-compatible records. | Lets analysis code reject stale or ambiguous formats. |
| `run_id` | Run directory or run identifier. | Links results to config, seed, metadata, and git commit. |
| `instance_id` | Specific clean or intervention benchmark instance. | Enables paired clean/intervention comparisons. |
| `base_task_id` | The clean base task shared by paired instances. | Required for causal robustness and paired bootstrap analyses. |
| `intervention_id` | Intervention identifier, or `null` for clean instances. | Links failures to the targeted perturbation. |
| `agent_id` | Concrete agent/provider/model run ID. | Separates realistic agents from oracle or debugging baselines. |
| `agent_name` | Agent implementation name. | Useful for grouping by agent style. |
| `provider_model_metadata` | Provider, model, prompt hash, and related metadata when available. | Makes LLM-backed results reproducible and auditable without storing secrets. |
| `steps` | Ordered list of `TrajectoryStepV2` records. | Primary evidence for trajectory-level metrics. |
| `final_answer` | Final answer text, if any. | Used by final-answer and faithfulness scorers. |
| `stop_reason` / `terminated_reason` | Why the trajectory ended. | Supports premature-stop and max-step-failure metrics. |
| `started_at` / `completed_at` | Optional run timestamps. | Useful for audit trails and latency accounting. |
| `token_cost_metadata` | Token usage, estimated cost, latency, model-call count, tool-call count, retry counts, and related fields. | Required for pilot cost reporting and provider reproducibility. |
| `metadata` | Flexible extra metadata. | Preserves run-specific context without loosening core fields. |

## Step Fields

| Field | Meaning | Why It Matters |
|---|---|---|
| `step_index` | Zero-based step number. | Makes trajectories stable and easy to diff. |
| `raw_model_output` | Exact raw model action output when an LLM agent is used. | Preserves evidence for parser and prompting failures. |
| `parsed_action` | `ToolCallParseResult` from the canonical tool protocol parser. | Distinguishes model errors from environment/tool errors. |
| `tool_call` | Parsed tool call, if any. | Supports tool-selection and invalid-call metrics. |
| `tool_arguments` | Parsed JSON arguments. | Supports argument-validity and argument-error metrics. |
| `tool_result` | Tool observation returned by the simulated environment. | Establishes what evidence the agent actually saw. |
| `parser_status` | Parser outcome such as `valid_tool_call`, `invalid_json`, or `unknown_tool`. | Supports parser-quality and invalid-action diagnostics. |
| `tool_error_status` | `none`, `error`, `corrupted`, `invalid_action`, `missing_observation`, or `not_applicable`. | Supports recovery and tool-failure analyses. |
| `recovery_marker` | Optional marker that recovery was attempted or completed. | Used to audit recovery metrics before relying on aggregate claims. |
| `contradiction_marker` | Optional marker that a conflict was detected or resolved. | Supports contradiction-handling metrics. |
| `memory_use_marker` | Optional marker for memory use or verification. | Supports memory verification and blind-trust diagnostics. |
| `final_answer` | Step-level final answer, if the agent stopped on this step. | Helps identify premature stopping. |
| `stop_reason` | Step-level stop reason, when known. | Explains termination behavior. |
| `started_at` / `completed_at` | Optional per-step timestamps. | Useful for latency audits. |
| `token_cost_metadata` | Step-level LLM/cost metadata, when available. | Allows cost attribution by step. |
| `action`, `observation`, `state` | Compatibility fields retained from v1 logs. | Keeps existing metrics and analysis code working during the transition. |

## Compatibility

The validator accepts older trajectory records by deriving v2 fields from existing `metadata`,
`action`, and `observation` fields. This is a migration layer, not a guarantee that old records
contain enough evidence for every v2 metric. Missing markers remain `null` or `not_applicable`.

## Markdown Export

Readable markdown transcripts can be produced with the `trajectory_to_markdown` and
`write_trajectory_markdown` helpers in `causal_agent_bench.trajectory`. Experiment configs can set:

```yaml
write_markdown_trajectories: true
```

This writes per-trajectory transcripts under `results/<run>/trajectories_md/`. These files are for
manual audit and error-case review; JSONL remains the canonical machine-readable artifact.

## Limitations

- Diagnostic markers are logged when agents or metrics can identify them; their absence should not
  be interpreted as proof that a failure did not occur.
- Timestamps are optional to preserve deterministic dry-run comparisons where needed.
- Cost metadata is estimated when providers expose token usage or pricing is configured; unknown
  costs must remain explicit rather than filled with guessed values.
- Schema v2 supports paper-ready trajectory evidence, but scientific claims still require real
  provider-backed runs and human validation where appropriate.
