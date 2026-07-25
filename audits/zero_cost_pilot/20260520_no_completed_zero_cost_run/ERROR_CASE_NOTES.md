# Error Case Notes — Zero-Cost Post-Run Audit

**Audit ID:** `20260520_no_completed_zero_cost_run`  
**Verdict:** `dry_run_only`  
**Zero-cost run directory:** *none*

---

## Primary finding: no zero-cost run to mine

No `results/<timestamp>_pilot_zero_cost_matrix_20` (or `pilot_free_local_20`, etc.) exists. Error-case mining from a zero-cost LLM run is **not possible**.

The sections below document **reference cases from the engineering stub run** `results/20260519T053609Z_pilot_20_multi_agent_stub`. These illustrate taxonomy coverage only — **not** zero-cost or preliminary LLM evidence. Do not cite in claims.

---

## Example 1 — Contradiction missed (stub reference)

| Field | Value |
|---|---|
| Task ID | `operations_planning_stress_001` |
| Instance ID | `operations_planning_stress_001.observation_conflict` |
| Agent | `direct_tool_local_stub` |
| Condition | intervention |
| Intervention family | `observation_conflict` |
| Trajectory | `results/20260519T053609Z_pilot_20_multi_agent_stub/trajectories.jsonl` |
| What happened | Agent made one stub tool call then emitted generic final answer; `contradiction_detected_binary=false`, `trajectory_faithfulness=0.0` |
| Why it matters | Illustrates taxonomy for C3/C10 — not valid LLM evidence |
| Human audit needed | **Yes** if ever cited from a real run |

---

## Example 2 — Failure to recover from tool error (stub reference)

| Field | Value |
|---|---|
| Task ID | `research_assistant_hard_001` |
| Instance ID | `research_assistant_hard_001.tool_failure` |
| Agent | `direct_tool_local_stub` |
| Condition | intervention |
| Intervention family | `tool_failure` |
| Trajectory | stub run trajectories |
| What happened | `search_database` returned `simulated_tool_failure`; agent stopped without recovery (`tool_error_recovery_binary=false`) |
| Why it matters | Recovery taxonomy for C2/C5 — stub only |
| Human audit needed | **Yes** for real runs |

---

## Example 3 — Tool corruption without adaptation (stub reference)

| Field | Value |
|---|---|
| Task ID | `research_assistant_hard_001` |
| Instance ID | `research_assistant_hard_001.tool_corruption` |
| Agent | `direct_tool_local_stub` |
| Condition | intervention |
| Intervention family | `tool_corruption` |
| What happened | Corrupted observation (`is_corrupted=true`); no cross-check or recovery |
| Why it matters | Memory/tool corruption family for C2 |
| Human audit needed | **Yes** |

---

## Example 4 — Excessive tool overuse (stub reference)

| Field | Value |
|---|---|
| Task ID | `file_spreadsheet_qa_medium_000` |
| Instance ID | `file_spreadsheet_qa_medium_000.irrelevant_tools` |
| Agent | `direct_tool_local_stub` |
| Condition | intervention |
| Intervention family | `irrelevant_tools` |
| What happened | Called `search_database` instead of required `read_file`/`query_spreadsheet`; `unnecessary_tool_call_rate=1.0` |
| Why it matters | C7 taxonomy — irrelevant-tools overuse |
| Human audit needed | **Yes** |

---

## Example 5 — Premature stop pattern (stub aggregate)

| Field | Value |
|---|---|
| Scope | All agents, stub run |
| Metric | `premature_stop`: **467** instances (score report) |
| What happened | Stub agents stop after 1–2 steps with generic final answer |
| Why it matters | C8 premature-stop family — aggregate stub pattern |
| Human audit needed | N/A for stub; **Yes** for real LLM runs |

---

## Example 6 — Missing required tools (stub aggregate)

| Field | Value |
|---|---|
| Scope | Stub run aggregate |
| Metric | `missing_required_tools`: **467** |
| What happened | Stub calls one random available tool, skips most required tools |
| Why it matters | Planning/tool-selection diagnostic |
| Human audit needed | N/A for stub |

---

## Example 7 — Memory blind trust (stub reference)

| Field | Value |
|---|---|
| Category | `blind_trust_in_corrupted_memory` |
| Source | `error_cases/blind_trust_in_corrupted_memory.jsonl` |
| What happened | Stub did not verify corrupted memory observations |
| Why it matters | C2 memory corruption family |
| Human audit needed | **Yes** for real runs |

---

## Example 8 — Final success via invalid trajectory (stub taxonomy)

| Field | Value |
|---|---|
| Category | `correct_final_answer_via_invalid_trajectory` |
| Source | `error_cases/correct_final_answer_via_invalid_trajectory.jsonl` |
| What happened | Taxonomy bucket for final/trajectory disagreement (stub: none succeeded) |
| Why it matters | C3 trajectory vs final disagreement |
| Human audit needed | **Yes** |

---

## Example 9 — Dry-run simulation only (zero-cost preflight)

| Field | Value |
|---|---|
| Instance ID | `travel_planning_medium_000.clean` |
| Agent | `direct_tool_local_ollama` (simulated) |
| Provider used | `local_stub` (not Ollama) |
| What happened | 2-step dry-run simulation; `provider_calls_made=false` |
| Why it matters | Confirms preflight wiring only — **not** an error case from real execution |
| Human audit needed | **No** |

---

## Example 10 — Scoring suspicious case (stub-wide)

| Field | Value |
|---|---|
| Scope | Entire stub run |
| Observation | **0% clean and intervention success** for all agents; ACRS **NA** |
| What happened | Deterministic stub cannot satisfy task success criteria |
| Why it matters | Demonstrates scorer behavior on engineering runs — must not be read as model failure rates |
| Human audit needed | **No** — expected stub behavior |

---

## Next step to obtain real error cases

Execute a zero-cost run, then re-audit:

```bash
export LOCAL_OPENAI_BASE_URL=http://localhost:11434/v1
export LOCAL_OPENAI_MODEL_ID=qwen2.5:7b
python3 -m causal_agent_bench run --config configs/pilot_free_local_20.yaml
# Then re-run this audit prompt against results/<timestamp>_pilot_free_local_20
```
