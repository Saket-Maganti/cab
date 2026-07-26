# ICLR Research Questions and Hypotheses

**Freeze ID:** `ICLR-RQ-v1`  
**Frozen:** 2026-07-26, before confirmatory execution  
**Status:** `DESIGN_ONLY`; all answers are `EXECUTION_PENDING`

## 1. Shared gates

These gates apply before any RQ-specific threshold:

- only complete, non-mock runs with audited validity-passing pairs;
- frozen task split, agent configuration, scorer, family set, and analysis code;
- no gold answers or paired counterparts exposed to agents;
- exact common support for agent comparisons;
- clustered uncertainty at `base_task_id`;
- family-stratified resampling for frozen family-macro endpoints;
- Holm-adjusted primary tests and clearly labeled exploratory analyses;
- all exclusions, invalid pairs, undefined denominators, and protocol deviations
  reported; and
- effect sizes and confidence intervals reported whether or not a null is
  rejected.

The minimum confirmatory target is 100 validity-passing matched units overall,
with at least 20 units per primary family for a family-specific claim. This is a
minimum interpretability gate, not a guarantee of power. If prospective power
requires more compute than the resource envelope permits, the claim remains
underpowered rather than being rescued with weaker post-hoc criteria.

For absolute binary-success differences, the default smallest effect size of
interest (SESOI) is 0.05, or five percentage points. A different SESOI requires
a pre-execution amendment with justification.

## 2. Frozen RQ1–RQ10

### RQ1 — Competence under controlled intervention

**Question.** How much clean-task competence is retained under valid controlled
interventions?

**H1.** For eligible non-oracle agents, intervention success will be lower than
matched clean success, with positive paired absolute degradation and
clean-conditioned robustness below one.

| Item | Frozen specification |
|---|---|
| Primary metric | Paired absolute degradation \(\Delta_{\mathrm{abs}}\) |
| Companion metrics | \(S_0\), \(S_I\), \(R^{CC}\), transition profile, family macro/worst robustness, ACRS denominator state |
| Study | Confirmatory common-pair evaluation over preregistered agents and primary families |
| Evidence threshold | At least 100 valid pairs overall; clustered 95% CI for \(\Delta_{\mathrm{abs}}\) excludes 0 and includes effects at or above the 0.05 SESOI for a “material” claim |
| Null interpretation | No detected benchmark-local degradation, practical equivalence, or insufficient precision; it does not prove universal robustness |
| Allowed wording if met | “On the frozen CAB distribution, tested agents lost X percentage points under validity-audited interventions.” |
| Allowed wording if not met | “We did not resolve a material clean-to-intervention competence gap at the available precision.” |

### RQ2 — Ranking stability

**Question.** Do agent rankings based on robustness differ from clean-success
rankings, and how uncertain are those ranks?

**H2.** At least one eligible non-oracle agent's robustness rank will differ
from its clean-success rank on common support.

| Item | Frozen specification |
|---|---|
| Primary metric | Cluster-bootstrap probability that robustness rank differs from clean rank |
| Companion metrics | Expected rank, rank CI, pairwise rank-probability matrix, Spearman and Kendall association |
| Study | At least five eligible non-oracle configurations evaluated on exactly common pair support |
| Evidence threshold | A rank-change claim requires probability at least 0.80 for a preregistered agent or a preregistered global rank-instability statistic whose 95% interval excludes the no-change value |
| Null interpretation | Clean and robustness orderings are compatible at available precision; tied/wide ranks are uncertainty, not stable equivalence |
| Allowed wording if met | “Robustness evaluation changed the ordering of the tested configurations on the frozen family mixture.” |
| Allowed wording if not met | “The data did not resolve a ranking change; rank intervals remained [reported intervals].” |

### RQ3 — Failure heterogeneity

**Question.** How strongly does robustness vary across intervention families?

**H3.** Valid intervention families will exhibit heterogeneous
clean-conditioned robustness rather than a common effect.

| Item | Frozen specification |
|---|---|
| Primary metric | Between-family range and prespecified pairwise differences in \(R_f^{CC}\) |
| Companion metrics | Family \(\Delta_f\), transitions, macro and worst-family robustness |
| Study | Every primary family with at least 20 valid pairs; clustered family-stratified bootstrap |
| Evidence threshold | At least one Holm-adjusted preregistered family contrast has a 95% CI excluding 0 and an absolute difference at or above 0.10 |
| Null interpretation | No resolved heterogeneity, families underpowered, or effects smaller than 10 points; pooling must still disclose family estimates |
| Allowed wording if met | “Failure sensitivity was heterogeneous across the tested intervention families.” |
| Allowed wording if not met | “We did not resolve family differences larger than the preregistered threshold.” |

### RQ4 — Recovery

**Question.** When an intervention creates a recoverable failure, how often do
agents recover, and does recovery correspond to retained task success?

**H4.** Recovery behavior will be incomplete and positively associated with
intervention success after conditioning on clean success and family.

| Item | Frozen specification |
|---|---|
| Primary metric | Recovery success rate over eligible recovery opportunities |
| Companion metrics | Final success after recovery, steps to recovery, \(p_{11}\), \(p_{10}\), cost/latency |
| Study | Outcome-scored trajectories with frozen recovery-opportunity labels; at least 30 opportunities overall and 20 for any family claim |
| Evidence threshold | Opportunity denominator met; blinded trajectory-label audit passes; clustered association or preregistered contrast has 95% CI excluding 0 |
| Null interpretation | Recovery may be rare, weakly measured, or unrelated to final success; a process label alone does not establish a capability |
| Allowed wording if met | “Observed recovery behavior was associated with retained success in the tested recoverable-failure conditions.” |
| Allowed wording if not met | “Recovery labels did not provide resolved information beyond final success.” |

### RQ5 — Abstention

**Question.** Do agents abstain when evidence is insufficient while avoiding
unnecessary abstention on answerable tasks?

**H5.** Agents will show a calibration tradeoff: correct abstention on
abstention-required pairs will coexist with nonzero false abstention on
answerable controls.

| Item | Frozen specification |
|---|---|
| Primary metric | Correct-abstention rate on abstention-required opportunities |
| Companion metrics | False-abstention rate on answerable controls; incorrect definitive-answer rate |
| Study | Frozen answer-contract labels, at least 30 abstention-required opportunities and 30 matched answerable controls |
| Evidence threshold | Human audit of semantic abstentions passes; both rates have clustered 95% CIs; tradeoff claim requires both denominators and a nonzero estimated false-abstention rate |
| Null interpretation | Agents may never abstain, abstain indiscriminately, or the study may lack opportunity coverage |
| Allowed wording if met | “The tested agents' abstention behavior showed the reported coverage–error tradeoff under frozen answer contracts.” |
| Allowed wording if not met | “The study did not resolve calibrated abstention behavior.” |

### RQ6 — Intervention validity

**Question.** Do generated interventions successfully manipulate the intended
factor while preserving goals, invariances, solvability, and scoreability?

**H6.** A prespecified majority of reviewed pairs will pass the complete IVP,
with agreement at or above the frozen threshold.

| Item | Frozen specification |
|---|---|
| Primary metric | Complete-profile pass rate and exclusion rate |
| Companion metrics | Dimension-level judgments, reviewer agreement, adjudication and exclusion reasons |
| Study | Outcome-blinded independent review of at least 100 candidate pairs, stratified across every primary family, two or more reviewers |
| Evidence threshold | Agreement at least 0.80; pass-rate 95% lower bound at least 0.80 overall; no primary family with fewer than 20 reviewed items or an unresolved critical dimension |
| Null interpretation | The generator or family does not yet support the intended controlled claim; failed pairs cannot be removed only after outcomes are known |
| Allowed wording if met | “Outcome-blinded review supported the declared validity contract for X% of candidate pairs.” |
| Allowed wording if not met | “The validity audit exposed limitations in intervention construction; affected families were excluded or reframed.” |

### RQ7 — Scorer reliability

**Question.** Are robustness estimates and rankings stable to scorer error and
reasonable scoring alternatives?

**H7.** The frozen scorer will agree strongly with blinded human labels, and
headline conclusions will remain stable under human-calibrated error scenarios.

| Item | Frozen specification |
|---|---|
| Primary metric | Scorer accuracy/agreement against blinded human outcome labels |
| Companion metrics | False-positive/negative rates, alternate-scorer deltas, corrected robustness scenarios, rank changes |
| Study | Stratified audit of at least 100 scored outcomes, oversampling abstention and semantic cases without changing estimator weights |
| Evidence threshold | Overall agreement at least 0.90; false-positive and false-negative point estimates below 0.10; headline effect direction and qualitative rank claim stable across their 95% uncertainty region |
| Null interpretation | Results are scorer-sensitive or the audit is too imprecise; deterministic fixture accuracy cannot substitute |
| Allowed wording if met | “Headline conclusions were stable under scorer alternatives calibrated from blinded review.” |
| Allowed wording if not met | “The result depends materially on scorer choice and is reported as scorer-sensitive.” |

### RQ8 — Transfer

**Question.** Do robustness patterns observed on generated CAB tasks transfer to
a separately authored, more naturalistic validation subset?

**H8.** The direction of the aggregate degradation and the identity of the
weakest preregistered families will be consistent on generated and
human-authored subsets.

| Item | Frozen specification |
|---|---|
| Primary metric | Subset-by-condition interaction in paired absolute degradation |
| Companion metrics | Direction agreement, family robustness profiles, rank association |
| Study | Independently authored set with at least 30 valid pairs across at least three domains and three primary families; no template reuse from the generated test set |
| Evidence threshold | Both subsets have valid audited pairs; aggregate degradation has the same direction; interaction CI rules out a reversal larger than 0.10; family conclusions are reported with uncertainty |
| Null interpretation | Synthetic findings do not demonstrably transport, or the validation set is too small; internal controlled results may remain valid |
| Allowed wording if met | “The tested human-authored subset showed a compatible robustness pattern within the preregistered tolerance.” |
| Allowed wording if not met | “Transfer to the human-authored subset was weak or unresolved; claims are limited to the generated benchmark distribution.” |

### RQ9 — Method improvement

**Question.** Can a lightweight, preregistered agent method improve robustness
without merely increasing budget or unnecessary tool use?

**H9.** A fixed self-checking or plan–execute scaffold will improve
clean-conditioned robustness relative to the same backend and budget, with no
material clean-success loss.

| Item | Frozen specification |
|---|---|
| Primary metric | Paired difference in \(R^{CC}\) between method and control |
| Companion metrics | Clean success, absolute degradation, family effects, tool calls, tokens, latency, false abstention |
| Study | Same backend, version, tasks, scorer, decoding policy, and resource cap; prompt/scaffold hashes frozen; at least 50 valid common pairs per arm |
| Evidence threshold | Clustered 95% CI for robustness improvement excludes 0 and point estimate is at least 0.05; clean-success loss is less than 0.05; compute and side-effect outcomes fully disclosed |
| Null interpretation | The method has no resolved benefit, trades robustness for clean competence, or relies on more compute |
| Allowed wording if met | “Under matched budgets, the tested scaffold improved robustness by X points on the frozen tasks.” |
| Allowed wording if not met | “The lightweight method did not deliver a resolved matched-budget robustness gain.” |

### RQ10 — Scale

**Question.** Within the tested model set, how is model scale associated with
clean competence and robustness?

**H10.** Larger tested models will have higher clean success on average, but
scale will not eliminate worst-family brittleness.

| Item | Frozen specification |
|---|---|
| Primary metric | Association of declared model-size measure with common-support \(S_0\) and \(R^{CC}\) |
| Companion metrics | Worst-family robustness, cost, latency, context length, provider/architecture labels |
| Study | At least six eligible configurations spanning at least three prespecified scale bands, evaluated on exact common support |
| Evidence threshold | Cluster-bootstrap association interval excludes 0 for an association claim; worst-family claim requires reportable estimates in every primary family |
| Null interpretation | Scale association is absent, non-monotone, or confounded in the tested set; lack of association is not proof of scale invariance |
| Allowed wording if met | “Within the tested configurations, declared model scale was associated with [metric].” |
| Forbidden wording | “Increasing scale causes robustness.” Observational cross-model comparisons do not identify a scale effect. |

## 3. Primary and secondary ordering

The primary paper RQs are RQ1, RQ6, and RQ7: competence under intervention,
validity of the intervention methodology, and scorer reliability. RQ2 and RQ3
test whether the methodology reveals ordering and failure-profile information.
RQ4 and RQ5 are mechanism-adjacent behavioral analyses. RQ8 is the external
validity check. RQ9 is a method case study. RQ10 is observational and
exploratory unless the model set and power gate are met.

This ordering is frozen to prevent a compelling secondary result from silently
replacing a failed primary study.

## 4. Amendment policy

Any change to an RQ, hypothesis, metric, SESOI, family set, threshold, model set,
or allowed wording requires:

1. a dated amendment;
2. a reason independent of confirmatory results;
3. a new freeze identifier;
4. preservation of this version; and
5. labeling affected analyses exploratory if outcomes were already inspected.

No threshold is relaxed because a p-value, confidence interval, or rank was
unfavorable.
