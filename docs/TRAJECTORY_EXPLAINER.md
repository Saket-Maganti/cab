# Trajectory Explainer

How to read agent trajectories in CausalAgentBench. Examples are **synthetic** for illustration.

## Trajectory format

Stored in `results/<run_dir>/trajectories.jsonl` (one JSON object per line). Schema: `trajectory_v2`.

Key fields:

| Field | Meaning |
|---|---|
| `run_id` | Experiment run identifier |
| `instance_id` | Benchmark instance ID |
| `base_task_id` | Underlying base task |
| `intervention_id` | Set if intervention condition |
| `agent_name` | Agent configuration name |
| `steps` | List of step records |
| `final_answer` | Agent's closing response |
| `terminated_reason` | e.g., `final_answer`, `max_steps`, `error` |

## Step record anatomy

Each step typically contains:

```json
{
  "action": {
    "thought": "Mock helpful: call search_database.",
    "tool_call": {"tool_name": "search_database", "arguments": {"query": "hotels Boston"}},
    "final_answer": null
  },
  "observation": {
    "tool_name": "search_database",
    "output": {"options": ["saver_hotel", "lux_hotel"]},
    "error": null
  }
}
```

| Part | Role |
|---|---|
| **Tool call record** | `action.tool_call` — name + arguments |
| **Observation record** | Tool output or error after execution |
| **Final answer record** | `action.final_answer` when agent stops |
| **Error record** | `observation.error` — tool failure, invalid args, unavailable tool |

## Scoring fields

After `score`, see `scores.jsonl` per trajectory:

- `final_success_binary` — answer vs ground truth
- `trajectory_success_binary` — faithfulness to evidence
- `unnecessary_tool_call_rate`, `required_tool_recall`
- `tool_error_recovery_binary`, `premature_stop_binary`
- `contradiction_detected_binary`, `memory_verified_binary`
- `diagnostics.failure_modes` — taxonomy tags

## How to read a trajectory

1. Check `instance_id` and condition (clean vs intervention) in run metadata.
2. Walk `steps` in order: did the agent follow a sensible tool plan?
3. Compare tool calls to `gold_tool_sequence` in base task (not visible to agent).
4. Read `final_answer` against success criteria.
5. Compare `final_success_binary` vs trajectory metrics for hidden failures.

## Identifying bad tool use

- **Invalid tool:** `observation.error` = `unknown_tool` / `tool_unavailable`
- **Bad arguments:** `invalid_arguments` error
- **Unnecessary calls:** tools not in gold sequence without justification
- **Missing required tools:** never called `verify_fact` after memory patch

## Identifying recovery

- After `observation.error`, look for different tool call or uncertainty in final answer
- Metric: `tool_error_recovery_binary`, `steps_to_recovery`

## Identifying premature stopping

- Few steps + early `final_answer` before required tools called
- Metric: `premature_stop_binary`
- Common with `premature_success_signal` interventions

## Connecting to claims

| Pattern | Relevant claims |
|---|---|
| Clean high / intervention low final success | C1 |
| Family-specific degradation | C2 |
| Final success but bad trajectory metrics | C3 |
| ACRS reordering vs clean success | C4 |

**Mock trajectories** validate detector wiring only — label `engineering_only`.

## Synthetic mini-example

```
Step 1: call search_database → error tool_failure
Step 2: final_answer "Failed." (no retry)
→ premature_stop or recovery failure; final_success likely 0
```

Inspect live (engineering run):

```bash
python3 -m causal_agent_bench run-status --run-dir results/<mock_run_dir>
python3 -m causal_agent_bench generate-report --run-dir results/<mock_run_dir>
```

Do not cite mock runs as LLM behavior.

See [EXAMPLE_WALKTHROUGHS.md](EXAMPLE_WALKTHROUGHS.md), [GLOSSARY.md](GLOSSARY.md).
