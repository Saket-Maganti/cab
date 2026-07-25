# Claim Update Recommendations — Zero-Cost Post-Run Audit

**Audit ID:** `20260520_no_completed_zero_cost_run`  
**Verdict:** `dry_run_only`  
**Evidence run directory:** *none* (dry-run only: `results/dry_runs/20260520T024350Z_pilot_zero_cost_matrix_20`)

**Do not update the claim ledger.** Do not run Prompt 67.

---

## Claim C1 — clean_success_overestimates_robustness

**Claim:** Clean success overestimates robust competence under intervention.  
**Current status:** `planned`  
**Recommended status:** `planned`  
**Evidence path:** *none*  
**Allowed wording:** None from this audit.  
**Forbidden wording:** Any empirical clean-vs-intervention comparison from dry-run or stub.  
**Reason:** No non-oracle LLM trajectories scored.

---

## Claim C2 — tool_failure_memory_corruption_expose_weaknesses

**Claim:** Tool failure and memory corruption expose hidden weaknesses.  
**Current status:** `planned`  
**Recommended status:** `planned`  
**Evidence path:** *none*  
**Allowed wording:** None.  
**Forbidden wording:** Family breakdown tables from stub (0% success, local_stub).  
**Reason:** No real model intervention-family metrics.

---

## Claim C3 — trajectory_metrics_reveal_hidden_failures

**Claim:** Trajectory metrics detect failures missed by final-answer scoring.  
**Current status:** `planned`  
**Recommended status:** `planned`  
**Evidence path:** *none*  
**Allowed wording:** None.  
**Forbidden wording:** Stub error-case mining as human-validated disagreement evidence.  
**Reason:** Stub error cases reflect deterministic stub behavior, not LLM agents.

---

## Claim C4 — acrs_changes_rankings

**Claim:** ACRS changes model rankings relative to clean success.  
**Current status:** `planned`  
**Recommended status:** `planned`  
**Evidence path:** *none*  
**Allowed wording:** None.  
**Forbidden wording:** Any ranking or Spearman claim.  
**Reason:** ACRS null in stub; no zero-cost run.

---

## Claim C5 — recovery_separable_from_planning

**Claim:** Recovery ability is separable from planning ability.  
**Current status:** `planned`  
**Recommended status:** `planned`  
**Evidence path:** *none*  
**Allowed wording:** None.  
**Forbidden wording:** Component analysis from stub.  
**Reason:** No credible agent component scores.

---

## Claim C6 — self_checking_selectively_improves_robustness

**Claim:** Simple self-checking improves some intervention families but not all.  
**Current status:** `planned`  
**Recommended status:** `planned`  
**Evidence path:** *none*  
**Allowed wording:** None.  
**Forbidden wording:** Self-check agent comparisons.  
**Reason:** No ablation or real self-check run.

---

## Claim C7 — agents_overuse_tools

**Claim:** Some agents overuse tools even when unnecessary.  
**Current status:** `planned`  
**Recommended status:** `planned`  
**Evidence path:** *none*  
**Allowed wording:** None.  
**Forbidden wording:** Irrelevant-tools rates from stub.  
**Reason:** Stub overuse patterns are not LLM behavior.

---

## Claim C8 — agents_stop_prematurely

**Claim:** Some agents stop prematurely under misleading success signals.  
**Current status:** `planned`  
**Recommended status:** `planned`  
**Evidence path:** *none*  
**Allowed wording:** None.  
**Forbidden wording:** Premature-stop rates from stub.  
**Reason:** No real agent premature-stop audit.

---

## Claim C9 — smoke_tests_are_local_and_reproducible

**Claim:** CausalAgentBench smoke tests are reproducible without paid services.  
**Current status:** `engineering_only`  
**Recommended status:** `engineering_only` (unchanged)  
**Evidence path:** `README.md`, smoke runs, zero-cost dry-run pass  
**Allowed wording:** "Zero-cost config dry-run passes without paid calls."  
**Forbidden wording:** Conflating dry-run with completed zero-cost pilot evidence.  
**Reason:** Dry-run supports engineering readiness only.

---

## Claim C10 — interventions_isolate_targeted_components

**Claim:** Controlled interventions isolate intended skill components.  
**Current status:** `planned`  
**Recommended status:** `planned`  
**Evidence path:** *none* for run evidence; frozen audit reports exist separately  
**Allowed wording:** None from this run audit.  
**Forbidden wording:** Intervention validity from agent performance.  
**Reason:** Requires human/expert audit, not agent scores.

---

## Summary

| Action | Count |
|---|---|
| Keep `planned` | C1–C8, C10 |
| Keep `engineering_only` | C9 |
| Upgrade to `zero_cost_preliminary` | **0** |
| Upgrade to `pilot_supported` or `supported` | **0** |

After a real zero-cost run with score/analyze/export, re-evaluate whether any claim may move to `zero_cost_preliminary` with cautious wording only.
