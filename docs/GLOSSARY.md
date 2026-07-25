# Glossary

Precise definitions for CausalAgentBench documentation and paper.

| Term | Definition |
|---|---|
| **Agent** | Policy that maps observations and tool affordances to actions (tool calls or final answers). |
| **Tool-using agent** | Agent whose actions include calls to structured tools with JSON arguments. |
| **Trajectory** | Ordered record of an agent's steps on one benchmark instance: actions, tool calls, observations, termination. |
| **Clean condition** | Instance with no intervention patch; baseline task environment. |
| **Intervention condition** | Instance derived from a base task with exactly one designed perturbation (one intervention family). |
| **Base task** | Template specifying user goal, tools, ground truth, and gold tool sequence. |
| **Paired task** | Clean and intervention instances sharing the same base task ID. |
| **ACRS** | Agent Causal Robustness Score — benchmark-specific composite of clean/intervention success and trajectory diagnostics. |
| **Final task success** | Binary/heuristic score whether the final answer satisfies success criteria vs hidden ground truth. |
| **Trajectory diagnostics** | Step-level metrics (tool precision, recovery, contradiction detection, premature stop, etc.). |
| **Intervention family** | Category of perturbation (e.g., `tool_failure`, `memory_corruption`) targeting one skill factor. |
| **Evidence level** | Label for what claims an artifact supports (`stub_engineering`, `mock_diagnostic`, `provider_pilot`, …). |
| **Oracle agent** | `scripted_oracle_agent` — upper-bound sanity check; excluded from leaderboards. |
| **Mock agent** | `mock_behavior_agent` — deterministic scripted failures; **engineering only**, not LLM behavior. |
| **Local preliminary run** | Open-weight/local run (e.g., Ollama); feasibility only, not main evidence. |
| **Provider pilot** | Bounded API-backed run on pilot split; pilot wording only until main gate. |
| **Human validation** | Expert/annotator review of interventions or trajectory failures; required for C3/C10 support. |
| **Claim ledger** | `docs/claim_ledger.json` — machine-readable map of claims C1–C10 to evidence status. |
| **Run artifact** | Files under `results/<run_dir>/` (metadata, trajectories, scores, reports). |
| **Config hash** | SHA of experiment YAML stored in `config_hash.txt` for reproducibility. |
| **Dataset version** | Frozen benchmark ID (e.g., `pilot_v0.1`) with manifest hashes. |
| **Intervention isolation** | Discipline that each intervention changes one targeted factor; audited automatically. |

See [EVIDENCE_LEVEL_POLICY.md](EVIDENCE_LEVEL_POLICY.md), [BENCHMARK_TAXONOMY.md](BENCHMARK_TAXONOMY.md).
