# CausalAgentBench Benchmark Taxonomy

This document defines the skill dimensions, task domains, and intervention families used by CausalAgentBench. It is a specification for reviewers and dataset authors—not empirical evidence about model behavior.

## Agent skills

| Skill | Definition | Primary metrics / signals |
|---|---|---|
| **Planning** | Decomposing the user goal into an ordered tool-use plan before acting. | Gold-sequence overlap, step budget use, long-horizon dependency success |
| **Tool selection** | Choosing the correct tool among available options. | Wrong-tool rate, invalid tool calls, required-tool recall |
| **Tool argument construction** | Populating tool schemas with valid, task-relevant arguments. | Argument validity rate, schema errors |
| **Observation interpretation** | Reading tool outputs and updating beliefs. | Trajectory faithfulness, contradiction detection |
| **Memory use** | Consulting seeded memory when relevant. | Memory consult rate, blind-trust failures |
| **Memory verification** | Cross-checking memory against tools when corruption is possible. | Memory verified binary, verify_fact after memory |
| **Contradiction handling** | Detecting and resolving conflicting observations. | Contradiction detected/resolved binaries |
| **Recovery from tool errors** | Continuing productively after tool failure or partial output. | Tool error recovery binary, repeated failed calls |
| **Stopping behavior** | Deciding when enough evidence exists to answer. | Premature stop binary, max-step exhaustion |
| **Final answer synthesis** | Producing an answer aligned with evidence and success criteria. | Final success binary, unsupported final answer |
| **Trajectory faithfulness** | Actions and final answer consistent with observations. | Trajectory success vs final success disagreement |
| **Tool efficiency** | Avoiding unnecessary tool calls. | Unnecessary tool call rate, tool precision |

## Task domains

| Domain | Description | Typical tools |
|---|---|---|
| **Travel planning** | Option search, comparison, pricing under constraints. | search_database, compare_options, calculate_price |
| **Calendar/email workflow** | Scheduling lookup and draft-only email composition. | check_calendar, send_email_draft |
| **File/spreadsheet QA** | Evidence from files and tabular data. | read_file, query_spreadsheet |
| **Shopping/comparison** | Product comparison with cost and constraint reasoning. | compare_options, calculate_price |
| **Research assistant** | Evidence search and claim verification. | search_database, verify_fact |
| **Policy/compliance** | Policy lookup and compliance determination. | lookup_policy, verify_fact |
| **Coding/debugging** | Synthetic code/issue evidence and bug identification. | read_file, search_database |
| **Multi-hop operational planning** | Cross-tool dependencies and long-horizon plans. | check_calendar, lookup_policy, query_spreadsheet, compare_options |

See [benchmark_specs/TASK_TEMPLATE_REGISTRY.md](https://github.com/Saket-Maganti/causal-agent-bench/blob/main/benchmark_specs/TASK_TEMPLATE_REGISTRY.md) for template-level coverage.

## Intervention families

Each family changes **one targeted skill factor** while holding the user goal stable (when valid).

### tool_removal

- **Targeted skill:** Tool selection / planning under reduced affordances
- **Changed factor:** Tool availability
- **Expected robust behavior:** Agent finds alternate valid path or abstains with justification
- **Scoring signals:** Required-tool recall, final success, recovery/abstention quality
- **Common invalid designs:** Removing all required tools without marking answer change
- **Example clean task:** Travel refund comparison requiring search + compare + price
- **Example intervention:** Remove `calculate_price`; agent must estimate or abstain
- **Reviewer concern:** “Task becomes impossible.”
- **Mitigation:** Mark `expected_final_answer_change`, document scoring override

### tool_failure

- **Targeted skill:** Recovery from tool errors
- **Changed factor:** Tool reliability
- **Expected robust behavior:** Retry alternate tool, verify, or state uncertainty
- **Scoring signals:** Tool error recovery binary, repeated failed call count
- **Common invalid designs:** First-step failure with no alternate path
- **Example clean task:** Policy lookup then verify_fact
- **Example intervention:** `lookup_policy` returns transient error once
- **Reviewer concern:** “Failure is arbitrary.”
- **Mitigation:** Document failure mode, ensure at least one recovery path exists

### tool_corruption

- **Targeted skill:** Observation interpretation
- **Changed factor:** Tool output correctness
- **Expected robust behavior:** Cross-check corrupted output against another source
- **Scoring signals:** Contradiction detection, verify_fact usage
- **Common invalid designs:** Corruption on only tool with no verification path
- **Example clean task:** Spreadsheet QA with read_file backup
- **Example intervention:** Corrupt `query_spreadsheet` row for target SKU
- **Reviewer concern:** “Agents cannot detect synthetic corruption.”
- **Mitigation:** Pair with verify_fact or second tool; score verification not guessing

### irrelevant_tools

- **Targeted skill:** Tool efficiency / selection
- **Changed factor:** Distractor tools in action space
- **Expected robust behavior:** Ignore distractors; use minimal sufficient tool set
- **Scoring signals:** Unnecessary tool call rate, wrong-tool rate
- **Common invalid designs:** Distractors that accidentally satisfy success criteria
- **Example clean task:** Calendar slot lookup
- **Example intervention:** Add `book_stub`, `search_database` not needed for answer
- **Reviewer concern:** “Action space is unrealistic.”
- **Mitigation:** Cap distractor count; ensure gold sequence unchanged

### memory_corruption

- **Targeted skill:** Memory verification
- **Changed factor:** Memory correctness
- **Expected robust behavior:** Verify memory against tools before trusting
- **Scoring signals:** Memory verified binary, blind-trust failures
- **Common invalid designs:** Corrupted keys not auditable in hidden ground truth
- **Example clean task:** Refund threshold from memory + policy lookup
- **Example intervention:** Memory states threshold 1000; policy says 500
- **Reviewer concern:** “Memory interventions are not realistic.”
- **Mitigation:** Explicit corrupted keys; require tool cross-check in rubric

### observation_conflict

- **Targeted skill:** Contradiction handling
- **Changed factor:** Observation consistency
- **Expected robust behavior:** Detect conflict, resolve or abstain with rationale
- **Scoring signals:** Contradiction detected/resolved binaries
- **Common invalid designs:** No resolution path documented in scoring notes
- **Example clean task:** Compare two hotel options
- **Example intervention:** Two tools return conflicting totals for same option
- **Reviewer concern:** “Conflict resolution is subjective.”
- **Mitigation:** Scoring notes name acceptable resolutions and uncertainty wording

### ambiguous_instruction

- **Targeted skill:** Stopping / ambiguity handling
- **Changed factor:** Instruction specificity
- **Expected robust behavior:** Ask clarifying question, abstain, or state assumptions explicitly
- **Scoring signals:** Premature stop (negative), correct abstention/uncertainty (positive)
- **Common invalid designs:** Instruction so vague no rubric applies
- **Example clean task:** “Find the best option” with clear criteria
- **Example intervention:** Remove “refundable” constraint from instruction
- **Reviewer concern:** “Ambiguity makes scoring arbitrary.”
- **Mitigation:** Machine-checkable success criteria for allowed assumption classes

### long_horizon_dependency

- **Targeted skill:** Planning / state tracking
- **Changed factor:** Step dependency length
- **Expected robust behavior:** Carry forward intermediate results across steps
- **Scoring signals:** Required-tool recall, trajectory faithfulness
- **Common invalid designs:** max_steps too low for dependency chain
- **Example clean task:** Multi-hop ops: calendar → policy → spreadsheet → email draft
- **Example intervention:** Insert delayed dependency marker in mid-sequence tool output
- **Reviewer concern:** “Long tasks are expensive to evaluate.”
- **Mitigation:** Deterministic synthetic tools; cap steps with explicit budget

### premature_success_signal

- **Targeted skill:** Stopping behavior
- **Changed factor:** Environment completion signal
- **Expected robust behavior:** Continue until success criteria met despite early “done” signal
- **Scoring signals:** Premature stop binary, missing required tools
- **Common invalid designs:** Signal appears before any useful observation
- **Example clean task:** Three-tool travel comparison
- **Example intervention:** After first tool: “Looks complete after this observation.”
- **Reviewer concern:** “Success signal is contrived.”
- **Mitigation:** Document signal as intervention-only metadata; pair with trajectory metrics

### distractor_evidence

- **Targeted skill:** Observation interpretation / efficiency
- **Changed factor:** Evidence relevance
- **Expected robust behavior:** Ignore plausible but irrelevant evidence
- **Scoring signals:** Final answer grounded in required evidence; unnecessary tool rate
- **Common invalid designs:** Distractor is actually decisive for correct answer
- **Example clean task:** Identify cheapest refundable hotel
- **Example intervention:** Inject high-price non-refundable option in search results
- **Reviewer concern:** “Distractors may teach pattern-matching shortcuts.”
- **Mitigation:** Audit distractors are labeled non-decisive in hidden ground truth

## Audit tooling

- Dataset quality: `python3 -m causal_agent_bench audit-dataset --config <config>`
- Intervention validity: `python3 -m causal_agent_bench audit-interventions --benchmark-dir data/processed/<version>`
- Isolation audit: `python3 scripts/audit_intervention_isolation.py --dataset data/processed/<version>/instances.jsonl`

These audits are **engineering QA** until human validation and provider pilots complete.
