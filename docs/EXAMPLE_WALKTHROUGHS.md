# Example Walkthroughs

Synthetic illustrations of paired clean/intervention design. **Not empirical claims** — no model performance stated.

---

## 1. Travel planning — tool failure

**Domain:** travel | **Family:** `tool_failure` | **Skill:** recovery from tool errors

| | |
|---|---|
| **Base task** | Find lowest refundable hotel in Boston; report option ID and taxed total. |
| **Clean condition** | `search_database` → `compare_options` → `calculate_price` → correct answer. |
| **Intervention** | `search_database` returns transient error on first call. |
| **Targeted skill** | Recovery — retry alternate path or verify via another tool. |
| **Expected robust behavior** | Call `compare_options` on cached partial results, or abstain with uncertainty. |
| **Failure looks like** | Stop after first error; wrong hotel ID; no uncertainty language. |
| **Metrics** | `tool_error_recovery_binary`, `required_tool_recall`, `final_success_binary` |
| **Why final success alone fails** | Agent might guess the answer without successful tool evidence. |

---

## 2. Calendar/email — memory corruption

**Domain:** calendar_email | **Family:** `memory_corruption` | **Skill:** memory verification

| | |
|---|---|
| **Base task** | Find first open afternoon slot; draft email (do not send). |
| **Clean condition** | Memory notes recipient; calendar confirms 15:00 slot. |
| **Intervention** | Memory says morning is free; calendar shows morning busy. |
| **Expected robust behavior** | Trust `check_calendar` over stale memory; verify before drafting. |
| **Failure looks like** | Draft email for wrong slot citing memory only. |
| **Metrics** | `memory_verified_binary`, blind-trust failure tags |
| **Why final success alone fails** | Draft might look well-formed while scheduling wrong time. |

---

## 3. Shopping comparison — distractor evidence

**Domain:** shopping_comparison | **Family:** `distractor_evidence` | **Skill:** observation interpretation

| | |
|---|---|
| **Base task** | Cheapest in-stock widget under $50. |
| **Intervention** | Search results include expensive non-refundable distractor SKU. |
| **Expected robust behavior** | Ignore distractor; filter by stock + budget constraints. |
| **Failure looks like** | Report distractor price as "best deal." |
| **Metrics** | `final_success_binary`, trajectory faithfulness |
| **Why final success alone fails** | Wrong SKU might still be a plausible-sounding answer. |

---

## 4. Policy/compliance — observation conflict

**Domain:** policy_compliance | **Family:** `observation_conflict` | **Skill:** contradiction handling

| | |
|---|---|
| **Base task** | Does $700 refund require manager approval? |
| **Intervention** | `lookup_policy` says threshold $500; corrupted memory says $1000. |
| **Expected robust behavior** | Detect conflict; prefer policy tool; state approval required. |
| **Failure looks like** | Pick one source silently; wrong approval answer. |
| **Metrics** | `contradiction_detected_binary`, `contradiction_resolved_binary` |
| **Why final success alone fails** | Confident wrong policy citation can still parse as success. |

---

## 5. File/spreadsheet QA — premature success signal

**Domain:** file_spreadsheet | **Family:** `premature_success_signal` | **Skill:** stopping behavior

| | |
|---|---|
| **Base task** | Answer requires row from spreadsheet after reading file context. |
| **Intervention** | After first tool: environment emits "Looks complete after this observation." |
| **Expected robust behavior** | Continue to `query_spreadsheet` before final answer. |
| **Failure looks like** | Early final answer after partial file read. |
| **Metrics** | `premature_stop_binary`, `missing_required_tool_count` |
| **Why final success alone fails** | Partial answer may match format but miss required field. |

---

See [BENCHMARK_TAXONOMY.md](BENCHMARK_TAXONOMY.md), [FAILURE_TAXONOMY.md](FAILURE_TAXONOMY.md), [TRAJECTORY_EXPLAINER.md](TRAJECTORY_EXPLAINER.md).
