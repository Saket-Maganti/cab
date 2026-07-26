# Paired Robustness and Inference

**Status:** `DESIGN_ONLY` analysis contract with `ENGINEERING_ONLY` estimators  
**Results:** `EXECUTION_PENDING`  
**Primary unit:** frozen, validity-passing clean/intervention pair

## 1. Analysis principle

CAB estimates robustness from exact matched units. It does not compare a pool
of clean tasks with a different pool of intervention tasks. Every aggregate is
traceable to a pair ledger, and every exclusion has a reason.

Let \(C_u,I_u\in\{0,1\}\) be the clean and intervention success outcomes for
matched unit \(u\). Let \(f(u)\) denote its intervention family.

## 2. Primary estimands

### 2.1 Clean and intervention competence

\[
S_0=\frac{1}{n}\sum_u C_u,\qquad
S_I=\frac{1}{n}\sum_u I_u.
\]

These rates use the exact same pair support. Raw unpaired rates may be exported
for diagnostics but cannot replace them.

### 2.2 Paired absolute degradation

\[
\Delta_{\mathrm{abs}}
  =\frac{1}{n}\sum_u(C_u-I_u)=S_0-S_I.
\]

Positive values are degradation; negative values are improvement under the
intervention. This signed estimand remains defined when clean success is zero.

### 2.3 Clean-conditioned robustness

\[
R^{CC}
  =\Pr(I=1\mid C=1)
  =\frac{\sum_u C_uI_u}{\sum_u C_u}.
\]

This is the primary retention estimand: of the units solved cleanly, what
fraction remained successful? It is undefined when no matched clean outcome is
successful. Its denominator is always reported.

Conditioning changes the target population. \(R^{CC}\) should not be described
as overall success or compared across agents without also reporting \(S_0\),
because agents can condition on different clean-success subsets.

### 2.4 Transition profile

Define:

\[
p_{xy}=\Pr(C=x,I=y),\qquad x,y\in\{0,1\}.
\]

The four cells are:

- \(p_{11}\): success retained;
- \(p_{10}\): success broken by the intervention;
- \(p_{01}\): clean failure followed by intervention success; and
- \(p_{00}\): persistent failure.

Counts and rates are both mandatory. A robustness narrative based only on
\(p_{10}\) is incomplete when \(p_{01}\) is nonzero.

### 2.5 ACRS ratio as a secondary estimand

\[
\mathrm{ACRS}=S_I/S_0,\qquad
\Delta_{\mathrm{rel}}=1-\mathrm{ACRS}.
\]

ACRS is a descriptive ratio, not the sole contribution. It is suppressed when:

- no complete pair exists;
- \(S_0=0\); or
- \(S_0\leq 0.05\), the current frozen near-zero threshold.

The threshold is configurable only before confirmatory analysis. Reports always
show \(S_0\), \(S_I\), \(\Delta_{\mathrm{abs}}\), pair count, and denominator
state next to ACRS.

## 3. Recovery and abstention

### 3.1 Recovery

Recovery is evaluated only when the intervention creates an observable,
recoverable failure opportunity under the answer contract. The recovery rate is

\[
R_{\mathrm{rec}}
  =\frac{\text{successful recoveries}}
         {\text{eligible recovery opportunities}}.
\]

Eligibility is frozen by intervention metadata and scorer logic, not inferred
from whether the agent eventually succeeded. The report includes the
opportunity count and final success because process recovery can occur without
a correct final answer.

### 3.2 Abstention

CAB distinguishes:

- **correct abstention:** uncertainty/refusal when the transformed answer
  contract permits or requires it;
- **false abstention:** uncertainty/refusal when the available evidence supports
  a definitive answer; and
- **incorrect definitive answer:** a claim made when abstention was required.

Correct- and false-abstention rates use separate opportunity denominators.
Abstention is not universally rewarded.

## 4. Family summaries

For each family \(f\), all quantities are recomputed on its exact matched
subset \(U_f\). CAB reports family-specific \(S_{0,f}\), \(S_{I,f}\),
\(\Delta_f\), \(R_f^{CC}\), ACRS, transitions, and counts.

For the preregistered family set \(\mathcal{F}^{*}\):

\[
R_{\mathrm{macro}}^{CC}
  =\frac{1}{|\mathcal{F}_{R}|}
     \sum_{f\in\mathcal{F}_{R}}R_f^{CC},
\qquad
R_{\mathrm{worst}}^{CC}
  =\min_{f\in\mathcal{F}_{R}}R_f^{CC},
\]

where \(\mathcal{F}_{R}\subseteq\mathcal{F}^{*}\) contains families with a
reportable clean-conditioned denominator. The number of reportable and excluded
families is mandatory. Macro summaries are not computed after selectively
dropping an unfavorable family.

Historical `macro_acrs` and worst-family ACRS remain available but are named
explicitly. The canonical implementation additionally exports:

```text
family_macro_clean_conditioned_robustness
worst_family_clean_conditioned_robustness
worst_family_acrs
```

## 5. Pair ledger and missingness

The matched key is:

```text
(agent_name, model_name, base_task_id,
 intervention_id_or_family, repeat_id)
```

Only `completeness_state=complete` records enter estimation. The ledger rejects:

- missing clean condition;
- missing intervention condition;
- duplicate clean run at a repeat;
- duplicate intervention run at a repeat;
- missing base-task or intervention identity;
- unknown condition; and
- missing or non-binary primary success.

Invalid units are retained in `invalid_pairs` with source-row indices and reason
counts. The primary analysis is complete-case on predeclared matched units; it
does not impute model outcomes. Attrition and invalid-pair rates are reported by
agent, family, and condition. Differential missingness blocks a simple
robustness claim and triggers bounds or sensitivity analysis.

## 6. Repeated clean runs and clustering

An explicit `repeat_id`, repeat field, or seed identifies stochastic repeats.
If none exists, the record receives implicit repeat 0; multiple such records
are duplicates and are rejected.

A clean run may serve as comparator for multiple intervention variants. Those
pairs are correlated. The default uncertainty unit is therefore
`base_task_id`, which keeps every repeat and intervention variant from the same
base task in the same resampled cluster.

When family composition is fixed by design, the confirmatory bootstrap is
stratified by intervention family and clustered by base task. If the number of
clusters is too small for credible bootstrap inference, CAB reports descriptive
estimates and labels inference underpowered.

## 7. Uncertainty and tests

### 7.1 Confidence intervals

The default is a seeded, clustered percentile bootstrap:

1. resample base-task clusters with replacement;
2. retain all pair records belonging to each sampled cluster;
3. recompute the full estimand, including denominator gates;
4. keep undefined bootstrap replicates out of that metric's interval; and
5. report valid replicate counts.

The seed, number of replicates, alpha, cluster count, and valid-replicate count
are part of the artifact. Ten thousand replicates are preferred for final
tables; 1,000 may be used for resource-constrained audited pilots and must be
declared.

### 7.2 Binary paired test

For \(C,I\in\{0,1\}\), the default null test is exact McNemar/binomial on the
discordant counts \(n_{10},n_{01}\). If no discordant pair exists, the p-value
is undefined rather than zero or one. Effect sizes and confidence intervals
remain primary; a p-value alone does not support a robustness claim.

### 7.3 Multiplicity

Primary RQs, families, and contrasts are frozen. Holm correction controls the
family-wise error rate for the primary confirmatory family. Benjamini-Hochberg
may be used for clearly labeled exploratory families. Unadjusted and adjusted
p-values, family definition, and test count are all reported.

## 8. Rank uncertainty

Cross-agent rankings require exact common pair support. For each bootstrap
replicate:

1. synchronously resample common base-task clusters;
2. compute the frozen ranking metric per agent;
3. assign average ranks to ties; and
4. retain the replicate only when every compared agent has a reportable metric.

CAB reports:

- point clean and robustness ranks;
- rank delta;
- expected rank and rank interval;
- probability of each rank;
- pairwise probability \(P(a\text{ ranks above }b)\), with a tie worth \(1/2\);
- probability that robustness rank differs from clean rank;
- Spearman and Kendall association when defined; and
- excluded non-common units and invalid bootstrap replicates.

A point rank is not called stable unless its bootstrap distribution and pairwise
probabilities support that wording. Ranking claims require at least the frozen
minimum model count in the RQ protocol.

## 9. Scorer perturbation and reliability

Primary results use a frozen scorer. Robustness to scorer error is examined in
three layers:

1. deterministic boundary and property tests;
2. scorer agreement against an outcome-blinded human sample; and
3. sensitivity scenarios over explicit false-positive and false-negative rates.

For observed binary rate \(q\), assumed false-positive rate \(\alpha\), and
false-negative rate \(\beta\), the diagnostic correction is:

\[
q^*=\frac{q-\alpha}{1-\alpha-\beta},
\]

clipped to \([0,1]\). It is unidentified when
\(\alpha+\beta\geq1\). Scenario outputs are not evidence that the assumed error
rates are true. Human-derived estimates and uncertainty are required for a
paper claim.

If a headline conclusion or rank changes under plausible scorer scenarios, the
result is labeled scorer-sensitive and narrowed or withheld.

## 10. Formal results

### Proposition 1: transition decomposition of degradation

For any matched distribution with binary outcomes,

\[
\Delta_{\mathrm{abs}}=p_{10}-p_{01}.
\]

**Proof.** The random variable \(C-I\) equals \(1\) on transition \((1,0)\),
\(-1\) on \((0,1)\), and \(0\) on \((1,1)\) and \((0,0)\). Taking expectations
gives
\(\mathbb{E}[C-I]=p_{10}-p_{01}\). By definition,
\(\mathbb{E}[C-I]=\Delta_{\mathrm{abs}}\). \(\square\)

**Use.** Absolute degradation is not merely a difference of two opaque rates;
it is net breakage after subtracting intervention-associated improvements.
The full transition profile is therefore required.

### Proposition 2: family-mixture rank reversal

Let agents \(a,b\) have reportable family robustness values \(R_{a,f}\) and
\(R_{b,f}\). Under family-mixture weights \(w\) on the probability simplex,
define

\[
R_a(w)=\sum_f w_fR_{a,f},\qquad
R_b(w)=\sum_f w_fR_{b,f}.
\]

If there are families \(j,k\) such that
\(R_{a,j}>R_{b,j}\) and \(R_{a,k}<R_{b,k}\), then there exist family mixtures
\(w^+\) and \(w^-\) for which \(a\) ranks above \(b\) and below \(b\),
respectively.

**Proof.** Put all weight on \(j\). Then
\(R_a(w^+)-R_b(w^+)=R_{a,j}-R_{b,j}>0\). Put all weight on \(k\). Then
\(R_a(w^-)-R_b(w^-)=R_{a,k}-R_{b,k}<0\). If strictly positive weight on every
family is required, mixtures sufficiently close to these two vertices preserve
the strict inequalities by continuity. \(\square\)

**Use.** A global ranking is inseparable from the intervention-family mixture.
CAB must publish family weights, family profiles, and mixture-shift sensitivity;
it cannot present one ordering as universal.

## 11. Property and regression tests

The estimator suite pins:

- identity intervention: zero degradation and full clean-success retention;
- transition/degradation identity;
- monotonicity when intervention outcomes improve with clean outcomes fixed;
- exact family-specific denominators;
- zero and near-zero clean denominators;
- missing and malformed pairs;
- explicit and implicit repeated runs;
- base-task clustering and family stratification;
- common-support ranking;
- average-rank ties and coherent pairwise rank probabilities; and
- scorer perturbation, including unidentified error scenarios.

The principal tests are in `tests/test_phase5_paired_metrics.py` and
`tests/test_property_metrics.py`. Passing fixtures validate implementation
properties only; they are `FIXTURE_ONLY`/`ENGINEERING_ONLY`.

## 12. Reporting bundle

Every headline robustness table must include:

```text
evidence class
validity-passing pair count and invalid/excluded count
unique base-task and family counts
S0, SI, paired absolute degradation, clean-conditioned robustness
transition counts/rates
family macro and worst-family clean-conditioned robustness
ACRS and denominator state
clustered uncertainty
scorer version and sensitivity state
rank uncertainty when ranks are shown
```

No table generated from a mock, fixture, dry run, interrupted run, or
non-audited profile is paper-eligible.
