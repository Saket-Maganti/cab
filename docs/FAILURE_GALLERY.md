# Agent Failure Gallery

Qualitative evidence for *When Agent Success Is Not Agent Skill*. Each panel highlights an intervention family where **final-answer success can diverge from agent skill**.

> **Evidence discipline.** Mined examples link to run directories, config hashes, and scorer versions when available. Scaffold examples (no run linked) illustrate the gallery layout only and must **not** be cited as NeurIPS-scale empirical results. Deterministic stub/smoke runs are engineering checks.

## Provenance

- Source: `illustrative_scaffold`
- Run directory: `None`
- Config hash: `None`
- Dataset version: `None`
- Git commit: `dea8e25f0e429ed2054c628fb37d24e7c1c9020e`
- Evidence scope: `illustrative_scaffold_not_empirical_evidence`

## Gallery index

- [Tool failure recovery](#tool_failure_recovery): `illustrative_scaffold_not_empirical_evidence`
- [Memory corruption](#memory_corruption): `illustrative_scaffold_not_empirical_evidence`
- [Observation conflict](#observation_conflict): `illustrative_scaffold_not_empirical_evidence`
- [Irrelevant tool distraction](#irrelevant_tool_distraction): `illustrative_scaffold_not_empirical_evidence`
- [Premature success signal](#premature_success_signal): `illustrative_scaffold_not_empirical_evidence`
- [Distractor evidence](#distractor_evidence): `illustrative_scaffold_not_empirical_evidence`
- [Long-horizon dependency](#long_horizon_dependency): `illustrative_scaffold_not_empirical_evidence`

## Tool failure recovery {#tool_failure_recovery}

**Evidence scope:** `illustrative_scaffold_not_empirical_evidence`

### Task

- Task id: `file_spreadsheet_qa_medium_001`
- Instance: `n/a`
- Domain: `file_spreadsheet_qa`
- Instruction: Read the Q2 sheet and report the total revenue for the West region.
- Available tools: read_file, query_spreadsheet, verify_fact
- Required tools: read_file, query_spreadsheet

### Intervention

- Family: `tool_failure`
- Description: The spreadsheet tool returns a transient error on the first call.
- Expected robust behavior: Agent should recover, retry a relevant alternative, or state the limitation.

### Failure label

`Failure to recover from tool error`

### Agent trajectory excerpt (redacted summary)

```json
[
  "Step 0: query_spreadsheet -> error tool_failure",
  "Step 1: repeated query_spreadsheet with identical arguments -> error tool_failure",
  "Step 2: final_answer claims West revenue without a successful read"
]
```

- Final answer (if any): West revenue is $1.2M according to the spreadsheet.

### Why final-answer scoring would miss it

A final answer can still match the reference if the agent guesses, copies a partial hint, or answers from stale context even though the trajectory never recovered from the tool error.

### Linked artifacts

- Run: `n/a`
- Instance: `n/a`
- Agent: `n/a`
- Config hash: `n/a`
- Prompt hash: `n/a`
- Scorer: `n/a`

## Memory corruption {#memory_corruption}

**Evidence scope:** `illustrative_scaffold_not_empirical_evidence`

### Task

- Task id: `policy_compliance_easy_001`
- Instance: `n/a`
- Domain: `policy_compliance`
- Instruction: Determine whether a $650 refund requires manager approval.
- Available tools: lookup_policy, verify_fact
- Required tools: lookup_policy, verify_fact

### Intervention

- Family: `memory_corruption`
- Description: Initial memory states approval is not required, but policy lookup disagrees.
- Expected robust behavior: Agent should verify memory against current evidence before using it.

### Failure label

`Blind trust in corrupted memory`

### Agent trajectory excerpt (redacted summary)

```json
[
  "Step 0: answer cites initial_memory approval_required=false",
  "Step 1: lookup_policy returns threshold=500 and approval_required=true",
  "Step 2: final_answer still says no approval is required"
]
```

- Final answer (if any): No manager approval is required for a $650 refund.

### Why final-answer scoring would miss it

Final-answer scoring checks the answer text, not whether the agent verified memory against a reliable tool observation before trusting a corrupted initial-memory field.

### Linked artifacts

- Run: `n/a`
- Instance: `n/a`
- Agent: `n/a`
- Config hash: `n/a`
- Prompt hash: `n/a`
- Scorer: `n/a`

## Observation conflict {#observation_conflict}

**Evidence scope:** `illustrative_scaffold_not_empirical_evidence`

### Task

- Task id: `shopping_comparison_medium_001`
- Instance: `n/a`
- Domain: `shopping_comparison`
- Instruction: Compare SKU-12 prices and report the cheaper in-stock option.
- Available tools: search_database, compare_options, verify_fact
- Required tools: search_database, compare_options

### Intervention

- Family: `observation_conflict`
- Description: Two tool observations report incompatible prices for the same SKU.
- Expected robust behavior: Agent should detect conflict and resolve or disclose uncertainty.

### Failure label

`Contradiction missed or unresolved`

### Agent trajectory excerpt (redacted summary)

```json
[
  "Step 0: search_database returns price=$12",
  "Step 1: compare_options returns price=$19 for the same sku",
  "Step 2: final_answer picks $12 without noting the conflict"
]
```

- Final answer (if any): SKU-12 costs $12 and is the cheaper option.

### Why final-answer scoring would miss it

An answer can look definitive while ignoring conflicting tool observations; aggregate success does not separate contradiction handling from ordinary completion.

### Linked artifacts

- Run: `n/a`
- Instance: `n/a`
- Agent: `n/a`
- Config hash: `n/a`
- Prompt hash: `n/a`
- Scorer: `n/a`

## Irrelevant tool distraction {#irrelevant_tool_distraction}

**Evidence scope:** `illustrative_scaffold_not_empirical_evidence`

### Task

- Task id: `research_assistant_hard_001`
- Instance: `n/a`
- Domain: `research_assistant`
- Instruction: Summarize the cited paper findings on refund policy compliance.
- Available tools: read_file, verify_fact, weather_tool
- Required tools: read_file, verify_fact

### Intervention

- Family: `irrelevant_tools`
- Description: An irrelevant weather tool is available and returns distracting content.
- Expected robust behavior: Agent should ignore irrelevant tools and avoid unnecessary calls.

### Failure label

`Excessive or irrelevant tool use`

### Agent trajectory excerpt (redacted summary)

```json
[
  "Step 0: weather_tool called with city=Boston",
  "Step 1: weather_tool called again",
  "Step 2: final_answer discusses weather instead of the paper"
]
```

- Final answer (if any): Boston will be sunny; refund compliance summary omitted.

### Why final-answer scoring would miss it

Process inefficiency and irrelevant calls are invisible to final-answer-only metrics even when they predict intervention failure and wasted budget.

### Linked artifacts

- Run: `n/a`
- Instance: `n/a`
- Agent: `n/a`
- Config hash: `n/a`
- Prompt hash: `n/a`
- Scorer: `n/a`

## Premature success signal {#premature_success_signal}

**Evidence scope:** `illustrative_scaffold_not_empirical_evidence`

### Task

- Task id: `operations_planning_medium_001`
- Instance: `n/a`
- Domain: `operations_planning`
- Instruction: Confirm shipment status and report the delivery window.
- Available tools: search_database, verify_fact, send_email_draft
- Required tools: search_database, verify_fact

### Intervention

- Family: `premature_success_signal`
- Description: An early tool emits a premature completion signal.
- Expected robust behavior: Agent should continue until success criteria are satisfied.

### Failure label

`Premature stopping after misleading signal`

### Agent trajectory excerpt (redacted summary)

```json
[
  "Step 0: search_database returns premature_success_signal=true",
  "Step 1: final_answer reports delivery complete",
  "Step 2: verify_fact never called"
]
```

- Final answer (if any): Delivery is complete tomorrow 9am-11am.

### Why final-answer scoring would miss it

A premature environment success cue can trick agents into stopping early; the final answer may still be wrong or unsupported while looking complete.

### Linked artifacts

- Run: `n/a`
- Instance: `n/a`
- Agent: `n/a`
- Config hash: `n/a`
- Prompt hash: `n/a`
- Scorer: `n/a`

## Distractor evidence {#distractor_evidence}

**Evidence scope:** `illustrative_scaffold_not_empirical_evidence`

### Task

- Task id: `calendar_email_workflow_easy_005`
- Instance: `n/a`
- Domain: `calendar_email`
- Instruction: Find the first open afternoon slot and draft an email proposing it.
- Available tools: check_calendar, send_email_draft
- Required tools: check_calendar, send_email_draft

### Intervention

- Family: `distractor_evidence`
- Description: A distractor calendar entry suggests a morning slot that does not satisfy the request.
- Expected robust behavior: Agent should distinguish relevant from irrelevant evidence.

### Failure label

`Distractor evidence accepted`

### Agent trajectory excerpt (redacted summary)

```json
[
  "Step 0: check_calendar returns distractor morning slot 09:00",
  "Step 1: send_email_draft proposes 09:00",
  "Step 2: ignores afternoon availability in observations"
]
```

- Final answer (if any): Draft email proposes 09:00.

### Why final-answer scoring would miss it

Scoring the final string does not record whether the agent relied on irrelevant distractor observations instead of the evidence required by the success criteria.

### Linked artifacts

- Run: `n/a`
- Instance: `n/a`
- Agent: `n/a`
- Config hash: `n/a`
- Prompt hash: `n/a`
- Scorer: `n/a`

## Long-horizon dependency {#long_horizon_dependency}

**Evidence scope:** `illustrative_scaffold_not_empirical_evidence`

### Task

- Task id: `travel_planning_stress_000`
- Instance: `n/a`
- Domain: `travel_planning`
- Instruction: Find a refundable hotel, compute taxed price, and report option id plus total.
- Available tools: search_database, compare_options, calculate_price
- Required tools: search_database, compare_options, calculate_price

### Intervention

- Family: `long_horizon_dependency`
- Description: Intermediate compare output must be reused by the pricing step.
- Expected robust behavior: Agent should preserve intermediate evidence and use it in later calls.

### Failure label

`Broken long-horizon dependency`

### Agent trajectory excerpt (redacted summary)

```json
[
  "Step 0: search_database returns candidate hotels",
  "Step 1: compare_options selects saver_hotel",
  "Step 2: calculate_price called without prior compare output -> wrong total",
  "Step 3: final_answer reports inconsistent option id and total"
]
```

- Final answer (if any): Option saver_hotel totals $99.

### Why final-answer scoring would miss it

Multi-step tasks can fail when intermediate evidence is dropped, even if a lucky final guess matches the reference answer on a subset of checks.

### Linked artifacts

- Run: `n/a`
- Instance: `n/a`
- Agent: `n/a`
- Config hash: `n/a`
- Prompt hash: `n/a`
- Scorer: `n/a`

## Paper-ready shortened examples

See `paper/generated/failure_gallery_short.tex` for LaTeX fragments. Do not include in the camera-ready paper until examples are backed by validated provider runs.

### Tool failure recovery (short)

Under tool failure, the agent repeats the failing call and answers confidently without recovery, yet a lenient final-answer matcher might still accept the number.

### Memory corruption (short)

The agent trusts corrupted memory after a contradicting policy tool result, showing memory verification failure invisible to answer-only scoring.

### Observation conflict (short)

Conflicting observations are ignored; the trajectory never resolves or discloses uncertainty.

### Irrelevant tool distraction (short)

Irrelevant tools consume the budget and derail evidence gathering while a terse wrong answer can still fail silently under weak matchers.

### Premature success signal (short)

The agent stops after a misleading success cue without verifying required evidence.

### Distractor evidence (short)

The agent latches onto irrelevant evidence; final-answer scoring does not mark which observations were used.

### Long-horizon dependency (short)

A broken dependency chain drops intermediate evidence; the answer looks structured but uses the wrong prior result.
