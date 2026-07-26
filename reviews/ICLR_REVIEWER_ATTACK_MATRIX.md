# ICLR Reviewer Attack Matrix

**Status:** `DESIGN_ONLY` pre-mortem  
**Empirical defenses:** `EXECUTION_PENDING` or `HUMAN_INPUT_REQUIRED`  
**Rule:** an engineering safeguard is not presented as empirical validation

## 1. Core attacks

| Reviewer attack | Strongest version of the concern | Design response | Evidence required to answer it | Current state and residual limit |
|---|---|---|---|---|
| **“This is only a benchmark.”** | CAB contributes a task collection and a ratio, not a reusable research method. | Define a domain-independent evaluation tuple: base distribution, intervention operator, invariance and answer contracts, per-pair validity profile, matched estimands, clustered/rank inference, and claim governance. Release the operator/profile schemas and tested estimators separately from the current task set. | Demonstrate at least two operator families and the full IVP/inference workflow; show that the same method applies to the independently authored transfer subset. | Formalization and code are `DESIGN_ONLY`/`ENGINEERING_ONLY`. General usefulness still needs audited application. |
| **“It is not causal.”** | Naming perturbations “causal” does not identify causal mechanisms or deployment effects; multiple factors may change. | Separate controlled intervention, causal motivation, and formal identification. State the benchmark-local paired estimand and assumptions. Never infer internal mechanisms or universal effects. Gate every pair on manipulation success and invariance preservation. | Outcome-blinded intervention-validity review, condition parity audit, complete pair ledger, and narrow benchmark-local language. | The boundary is explicit. Isolation and agreement remain `HUMAN_INPUT_REQUIRED`; no broad causal claim is currently allowed. |
| **“Synthetic tasks are unrealistic.”** | Template artifacts, simplified tools, or unnatural failures dominate results and prevent external validity. | Treat realism as a separate IVP dimension. Measure generated-to-human-authored transfer rather than assuming it. Freeze a naturalistic subset with no test-template reuse and report subset interactions. | At least 30 audited human-authored pairs across three domains/families; validity, scorer, and mixture-comparability audit; uncertainty on transfer differences. | Transfer is `EXECUTION_PENDING`. Internal controlled contrasts may survive a realism failure, but deployment claims may not. |
| **“ACRS is a trivial or unstable ratio.”** | \(S_I/S_0\) is elementary, explodes at low clean success, and hides transitions. | Make paired absolute degradation and clean-conditioned retention primary; expose \(p_{11},p_{10},p_{01},p_{00}\), recovery, abstention, family macro/worst profiles, and uncertainty. Suppress ACRS at zero/near-zero denominators. Provide transition and mixture-shift propositions. | Property tests plus real matched estimates with clustered CIs, denominator states, and transition counts. | Estimators pass fixtures, but this is `ENGINEERING_ONLY`. The paper cannot make novelty rest on ACRS. |
| **“The result is a scorer artifact.”** | Exact matching misses paraphrases, semantic judging injects bias, and scorer choice changes ranks. | Freeze answer contracts and scorer versions; prefer structured scoring; route semantic/abstention cases to blinded review; estimate FP/FN rates; run alternate-scorer and error-rate sensitivity. | At least 100 stratified human-audited outcomes, agreement/error uncertainty, and stability of every headline conclusion over plausible scorer scenarios. | Boundary/property tests exist. Real scorer agreement is `HUMAN_INPUT_REQUIRED`; sensitive claims must be withheld. |
| **“You just used more compute.”** | Robust agents or the proposed scaffold get more tokens, tools, retries, or latency, so gains are budget effects. | Treat policy, decoding, tool permissions, max steps, retry policy, and budget as part of the agent configuration. Match budgets in method comparisons and report calls, tokens, latency, and cost. | Config/prompt hashes, run manifests, equal caps, paired common-task comparison, and resource-use table including failures and retries. | Infrastructure can record parity, but no matched-budget method result exists. Scale comparisons remain observational. |
| **“Rankings are unstable.”** | Small samples, ties, missing tasks, or intervention-family weights can reverse the leaderboard. | Rank only on exact common support; synchronously cluster-bootstrap; use average ranks for ties; publish rank distributions and pairwise probabilities; perform family-mixture sensitivity. | At least five eligible non-oracle configurations on common units, valid bootstrap replicates, disclosed family weights, and rank uncertainty. | Rank machinery is tested with fixtures. Any current point ranking lacks paper evidence. Mixture-dependent rank reversal is an explicit limitation. |
| **“The interventions are obvious.”** | Agents merely detect artificial error tokens or memorize public templates; no substantive robustness is measured. | Audit cue visibility and intervention salience; include severity/realism variants; hold out templates/seeds; compare surface-cue controls; require expected behavior beyond naming the intervention. | Blinded cue audit, held-out generator/template evaluation, ablation removing explicit cues, contamination check, and trajectory evidence of appropriate recovery/verification. | Existing isolation/leakage infrastructure helps, but real cue and human audits remain pending. A successful obvious-intervention subset cannot establish general robustness. |
| **“The benchmark was tuned post hoc.”** | Tasks, exclusions, thresholds, scorer, and hypotheses were changed after model results were seen. | Freeze RQ1–RQ10, SESOIs, primary families, IVP, scorer, pair key, denominator policy, and null handling. Version every amendment and preserve excluded/old artifacts. Keep development and confirmatory splits separate. | Timestamped hashes/manifests, untouched confirmatory split, claim ledger, amendment log, and complete analysis manifest. | The present documents freeze the intended contract. Actual temporal integrity must be verified when runs occur; a document date alone is not proof. |
| **“Transfer is weak.”** | Results hold only for CAB's generator, domains, or family mixture and do not predict other agent settings. | Define the target distribution narrowly; test an independently authored subset; publish family profiles rather than one universal score; state mixture-shift theorem and transport limitations. | RQ8 transfer study, domain/family coverage, subset interaction intervals, and replication or explicit failure. | `EXECUTION_PENDING`. Without this study, allowed claims stop at the frozen CAB distribution. |

## 2. Additional pressure tests

| Attack | Required response |
|---|---|
| **“The validity gate cherry-picks favorable pairs.”** | Freeze the gate before outcomes, blind reviewers, publish candidate/retained counts and every exclusion reason, and show a sensitivity analysis over the frozen candidate set where logically possible. |
| **“Clean-conditioned robustness rewards weak models.”** | Always report clean success and its denominator; do not compare \(R^{CC}\) alone across agents with different clean-success subsets; use exact common support and companion absolute degradation. |
| **“One clean run is reused many times.”** | Cluster uncertainty by `base_task_id`, disclose the number of variants per base task, and provide family-stratified sensitivity. |
| **“Stochastic repeats are pseudoreplication.”** | Match explicit repeats, keep base-task clusters intact, and report task and repeat counts separately. |
| **“Human validation is too small or fabricated.”** | Use real independent reviewers, preserve completed packets, report sampling and uncertainty, and leave the claim `HUMAN_INPUT_REQUIRED` until those artifacts exist. |
| **“Null results will disappear.”** | Apply `docs/ICLR_NULL_RESULT_POLICY.md`; release all frozen primary estimates and state changes regardless of direction. |
| **“The method overfits the public intervention taxonomy.”** | Hold out operator templates/seeds, distinguish public development from protected evaluation artifacts, and audit contamination. |
| **“An oracle inflates performance.”** | Use oracles only as scorer/environment sanity checks; exclude them from realistic ranking and competence claims. |

## 3. Evidence package expected by a skeptical reviewer

A defensible submission package must contain:

1. the frozen formal problem setup and operator declarations;
2. candidate and retained IVP ledgers with real review provenance;
3. a complete pair ledger with invalid/missing reasons;
4. scorer version, boundary tests, and blinded scorer audit;
5. common-support robustness estimates with clustered uncertainty;
6. transition, family macro, worst-family, recovery, and abstention profiles;
7. rank distributions and family-mixture sensitivity;
8. compute-parity and cost/latency records;
9. human-authored transfer results or a clear limitation;
10. freeze hashes, amendments, claim ledger, and null results; and
11. an artifact eligibility report excluding fixtures, stubs, interrupted runs,
    and oracle results from scientific claims.

Until those empirical artifacts exist, the strongest accurate statement is:

> CAB now has a specified and tested controlled-intervention evaluation
> methodology; its empirical research questions remain pending audited
> execution.

## 4. Methodology-contribution acceptance gate

The design clears the *conceptual* “more than a task collection” gate when CAB
can be described without naming its current domains:

> Given a base-task distribution, declare an intervention operator and its
> invariances, validate each generated pair independently of model outcomes,
> execute matched policies, estimate retention and transitions with
> cluster-aware uncertainty, and bound claims by scorer, mixture, and transfer
> sensitivity.

The repository now specifies and tests that workflow. This is not equivalent to
ICLR submission readiness. The validity, scorer, model, and transfer studies
remain required empirical gates.
