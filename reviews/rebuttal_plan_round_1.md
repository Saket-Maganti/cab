# Rebuttal Plan Round 1

This is the plan for responding to the strongest likely reviewer attacks. It is not a claim that all issues are solved.

## Attack: "This is just another benchmark."

Response: The benchmark does not only add harder tasks. It creates paired clean/intervention instances with an explicit changed factor, expected robust behavior, and component-level trajectory diagnostics. We patched the paper and intervention docs to state the estimand: which agent skill survives a named intervention while the high-level user goal is held fixed.

Remaining work: Fill related work with exact citations and show empirically that component diagnostics reveal information beyond final success.

## Attack: "The interventions are unrealistic."

Response: The intervention docs now map each family to realistic analogues such as API outages, stale memory, conflicting systems, bloated tool lists, and premature UI completion signals.

Remaining work: Human/expert audit must verify that interventions preserve the goal and mostly isolate one factor.

## Attack: "Synthetic tasks are fake."

Response: The paper now argues that deterministic simulation is the right first step for causal attribution because live tools drift and confound the intervention. We explicitly call this a tradeoff, not a substitute for deployment evaluation.

Remaining work: Add a second-stage external-validity suite after the controlled benchmark is stable.

## Attack: "ACRS is too simple."

Response: Metrics docs and paper now say ACRS is not sufficient. It must be reported with clean success, intervention success, sample size, uncertainty, and component diagnostics.

Remaining work: Add confidence intervals to all final paper tables and consider sensitivity analyses for low clean-success agents.

## Attack: "Your scores are unreliable."

Response: Docs now label deterministic metrics as heuristic indicators, not ground-truth causal labels. Human validation remains required for paper claims.

Remaining work: Implement annotation schemas, sample selection, agreement metrics, and adjudication workflow.

## Attack: "Baselines are too weak."

Response: The baseline docs now say deterministic stubs are mechanics checks. Paper claims require non-oracle LLM-backed agents. Oracle is separated.

Remaining work: Implement or configure real LLM adapters and run at least two non-oracle LLM agents/configurations.

## Attack: "You have data leakage."

Response: Fixed a real leak. `PlannerExecutorStubAgent` no longer uses schema-native gold tool sequences. Added regression test.

Remaining work: Audit every baseline for hidden-field access before final runs.

## Attack: "Runs cannot be trusted."

Response: Resume now rejects config-hash mismatches instead of silently appending incompatible trajectories. Commands and timestamped run dirs are documented.

Remaining work: Add CI and archived final-run artifacts.

## Attack: "The paper overclaims."

Response: Abstract and contribution bullets were downgraded from "we find/show" to planned-test language. Claim ledger remains the source of truth.

Remaining work: Before submission, run final experiments and update each claim with artifact paths or mark it weakened.
