# Intervention Validity Dossier

**Scope:** Static validity specification for Causal Agent Bench intervention families.  
**Evidence state:** No provider-backed runs · C3/C10 blocked · Human annotations missing  
**Taxonomy source:** `configs/intervention_taxonomy.yaml` v0.1-pre-provider-pilot

This dossier supports **method and review** claims about how interventions are *specified* and *audited*. It does **not** prove empirical isolation until human validation and provider runs complete.

---

## Dossier legend

| Field | Meaning |
|-------|---------|
| **Intended causal factor** | Single skill/environment variable the intervention targets |
| **Expected invariant** | Fields that must not change (unless taxonomy allows) |
| **Answer policy** | Whether gold answer should stay identical to clean pair |
| **Risk level** | `low` / `medium` / `high` / `blocker_if_violated` from taxonomy severity |
| **Human validation** | Expert review required before main-benchmark freeze? |
| **Claim dependency** | Ledger claims that eventually need this family validated |
| **Readiness** | `taxonomy_ready` · `static_audit_ready` · `human_review_pending` · `empirical_blocked` |

---

## Summary table

| Intervention type | Causal factor | Answer policy | Risk | HV required | Claims | Readiness |
|-------------------|---------------|---------------|------|-------------|--------|-----------|
| tool_removal | tool availability | depends | high | yes | C2,C7,C10 | human_review_pending |
| irrelevant_tools | tool distractor | preserving | medium | no | C7,C10 | static_audit_ready |
| tool_failure | tool reliability | depends | high | yes | C2,C7,C10 | human_review_pending |
| tool_corruption | output correctness | preserving | high | yes | C2,C3,C10 | human_review_pending |
| memory_corruption | initial memory | preserving | high | yes | C2,C3,C10 | human_review_pending |
| observation_conflict | observation conflict | preserving | high | yes | C2,C3,C10 | human_review_pending |
| distractor_evidence | distractor observation | preserving | medium | yes | C2,C3,C10 | human_review_pending |
| premature_success_signal | premature stopping signal | preserving | medium | yes | C3,C8,C10 | human_review_pending |
| ambiguous_instruction | instruction ambiguity | depends | high | yes | C1,C10 | human_review_pending |
| long_horizon_dependency | step dependency length | preserving | high | yes | C2,C8,C10 | human_review_pending |
| web_broken_link | web retrieval availability | depends | high | yes | C2,C10 | human_review_pending |
| web_stale_page | web content freshness | preserving | high | yes | C2,C10 | human_review_pending |
| web_irrelevant_search_result | search distraction | preserving | low | no | C7,C10 | static_audit_ready |
| web_conflicting_page | web evidence conflict | preserving | high | yes | C2,C10 | human_review_pending |
| web_hidden_evidence | evidence salience | preserving | high | yes | C2,C10 | human_review_pending |
| argument_perturbation | tool argument formation | preserving | medium | no | C7,C10 | static_audit_ready |
| stopping_recovery | recovery behavior | preserving | medium | yes | C3,C5,C8,C10 | human_review_pending |

**Overall empirical readiness:** `empirical_blocked` for all families.

---

## Per-intervention specifications

### tool_removal

| Attribute | Value |
|-----------|-------|
| Intended causal factor | Tool availability |
| Expected invariant | `base_task_id`, `user_instruction`, `success_criteria`, `hidden_ground_truth`, `initial_memory` |
| Allowed changed fields | `available_tools`, `tool_availability_patch`, `patch_details` |
| Forbidden changed fields | Instruction text, hidden ground truth, unrelated tool sets |
| Answer policy | **depends** — limitation-aware answer may be required |
| Failure mode tested | Agent hallucinates results after required tool removed |
| Example | Remove search tool; expect limitation-aware response |
| Risk level | **high** (severity_if_violated: blocker) |
| Human validation required | **yes** |
| Claim dependency | C2, C7, C10 |
| Current readiness | taxonomy_ready · static_audit_ready · **human_review_pending** |

### irrelevant_tools

| Attribute | Value |
|-----------|-------|
| Intended causal factor | Tool distractor availability |
| Expected invariant | All core task fields including `expected_final_answer` |
| Allowed changed fields | `available_tools`, patches |
| Answer policy | **answer_preserving** |
| Failure mode tested | Tool overuse on distractors (C7) |
| Risk level | **medium** (warning) |
| Human validation required | no (static review sufficient for pilot scaffolding) |
| Claim dependency | C7, C10 |
| Current readiness | **static_audit_ready** |

### tool_failure

| Attribute | Value |
|-----------|-------|
| Intended causal factor | Tool reliability |
| Expected invariant | Tools list, instruction, ground truth, memory |
| Allowed changed fields | `tool_output_patch`, `observations` |
| Answer policy | **depends** — recovery or limitation answer |
| Failure mode tested | No retry / no alternate tool / no graceful failure |
| Risk level | **high** (blocker) |
| Human validation required | **yes** |
| Claim dependency | C2, C7, C10 |
| Current readiness | **human_review_pending** |

### tool_corruption

| Attribute | Value |
|-----------|-------|
| Intended causal factor | Tool output correctness |
| Expected invariant | Gold answer, ground truth, instruction |
| Allowed changed fields | `tool_output_patch`, `observations` |
| Answer policy | **answer_preserving** (corruption must not change gold) |
| Failure mode tested | Agent accepts corrupted numeric/text evidence |
| Risk level | **high** |
| Human validation required | **yes** |
| Claim dependency | C2, C3, C10 |
| Current readiness | **human_review_pending** |

### memory_corruption

| Attribute | Value |
|-----------|-------|
| Intended causal factor | Initial memory |
| Expected invariant | Instruction, tools, gold answer |
| Allowed changed fields | `initial_memory`, `memory_patch` |
| Answer policy | **answer_preserving** |
| Failure mode tested | memory_blind — trusts stale seeded memory |
| Risk level | **high** |
| Human validation required | **yes** |
| Claim dependency | C2, C3, C10 |
| Current readiness | **human_review_pending** |

### observation_conflict

| Attribute | Value |
|-----------|-------|
| Intended causal factor | Observation conflict |
| Expected invariant | Gold answer, ground truth |
| Allowed changed fields | `tool_output_patch`, `observations` |
| Answer policy | **answer_preserving** |
| Failure mode tested | contradiction_blind |
| Risk level | **high** |
| Human validation required | **yes** |
| Claim dependency | C2, C3, C10 |
| Current readiness | **human_review_pending** |

### distractor_evidence

| Attribute | Value |
|-----------|-------|
| Intended causal factor | Distractor observation |
| Expected invariant | Gold answer unchanged |
| Answer policy | **answer_preserving** |
| Failure mode tested | Overweighting plausible irrelevant evidence |
| Risk level | **medium** |
| Human validation required | **yes** (salience / leakage check) |
| Claim dependency | C2, C3, C10 |
| Current readiness | **human_review_pending** |

### premature_success_signal

| Attribute | Value |
|-----------|-------|
| Intended causal factor | Premature stopping signal |
| Expected invariant | Gold answer, success criteria semantics |
| Allowed changed fields | observations, `metadata` |
| Answer policy | **answer_preserving** |
| Failure mode tested | premature_stopper (C8) |
| Risk level | **medium** — signal may be metadata-only |
| Human validation required | **yes** (visibility check) |
| Claim dependency | C3, C8, C10 |
| Current readiness | **human_review_pending** |

### ambiguous_instruction

| Attribute | Value |
|-----------|-------|
| Intended causal factor | Instruction ambiguity |
| Allowed changed fields | `instruction_patch`, `user_instruction` |
| Forbidden | Changing success_criteria or ground truth silently |
| Answer policy | **depends** |
| Failure mode tested | New task created instead of controlled perturbation |
| Risk level | **high** (blocker) |
| Human validation required | **yes** |
| Claim dependency | C1, C10 |
| Current readiness | **human_review_pending** |

### long_horizon_dependency

| Attribute | Value |
|-----------|-------|
| Intended causal factor | Step dependency length |
| Allowed changed fields | `tool_output_patch`, `observations` only (not instruction) |
| Answer policy | **answer_preserving** |
| Failure mode tested | Agent stops after early sufficient-looking evidence |
| Risk level | **high** |
| Human validation required | **yes** |
| Claim dependency | C2, C8, C10 |
| Current readiness | **human_review_pending** — high-risk queue priority |

### web_broken_link

| Attribute | Value |
|-----------|-------|
| Intended causal factor | Web retrieval availability |
| Answer policy | **depends** |
| Failure mode tested | Recovery after 404 / broken fetch |
| Risk level | **high** |
| Human validation required | **yes** |
| Current readiness | **human_review_pending** |

### web_stale_page

| Attribute | Value |
|-----------|-------|
| Intended causal factor | Web content freshness |
| Answer policy | **answer_preserving** |
| Failure mode tested | Treating stale policy/value as current |
| Risk level | **high** |
| Human validation required | **yes** |
| Current readiness | **human_review_pending** |

### web_irrelevant_search_result

| Attribute | Value |
|-----------|-------|
| Intended causal factor | Search-result distraction |
| Answer policy | **answer_preserving** |
| Risk level | **low–medium** |
| Human validation required | no |
| Current readiness | **static_audit_ready** |

### web_conflicting_page

| Attribute | Value |
|-----------|-------|
| Intended causal factor | Web evidence conflict |
| Answer policy | **answer_preserving** |
| Failure mode tested | Trusting wrong web page |
| Risk level | **high** |
| Human validation required | **yes** |
| Current readiness | **human_review_pending** |

### web_hidden_evidence

| Attribute | Value |
|-----------|-------|
| Intended causal factor | Evidence salience |
| Answer policy | **answer_preserving** |
| Risk level | **high** — may become impossible |
| Human validation required | **yes** |
| Current readiness | **human_review_pending** |

### argument_perturbation

| Attribute | Value |
|-----------|-------|
| Intended causal factor | Tool argument formation |
| Answer policy | **answer_preserving** |
| Failure mode tested | argument_sloppy |
| Risk level | **medium** |
| Human validation required | no |
| Current readiness | **static_audit_ready** |

### stopping_recovery

| Attribute | Value |
|-----------|-------|
| Intended causal factor | Recovery behavior |
| Answer policy | **answer_preserving** |
| Failure mode tested | recovery_weak after false completion |
| Risk level | **medium** |
| Human validation required | **yes** |
| Claim dependency | C3, C5, C8, C10 |
| Current readiness | **human_review_pending** |

---

## Review workflow

```bash
python3 -m causal_agent_bench intervention-isolation-audit --output-dir reports/intervention_isolation
python3 -m causal_agent_bench high-risk-intervention-queue --output-dir reports/high_risk_interventions
python3 -m causal_agent_bench validate-gold-outputs --output-dir reports/gold_outputs
```

**Do not auto-approve** high-risk pairs. Queue items require expert review per `high_risk_intervention_queue.csv`.

---

## Evidence boundary

- This dossier supports **C10 protocol design** only.
- **C10 empirical support** requires completed human validation + provider runs.
- Static isolation pass ≠ causal validity proof.

See also: [INTERVENTION_TAXONOMY.md](INTERVENTION_TAXONOMY.md), [HUMAN_VALIDATION_MASTER_PROTOCOL.md](HUMAN_VALIDATION_MASTER_PROTOCOL.md).
