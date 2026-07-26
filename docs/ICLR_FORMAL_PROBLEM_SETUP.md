# ICLR Formal Problem Setup

**Status:** `DESIGN_ONLY` formalization with `ENGINEERING_ONLY` support  
**Empirical status:** `EXECUTION_PENDING`  
**Scope:** Controlled evaluation methodology for tool-using agents

## 1. Methodology contribution

CausalAgentBench (CAB) evaluates whether an agent retains task competence under
a named, validity-audited change to its operating conditions. The methodological
object is not a bag of perturbed tasks. It is a tuple:

1. a base-task distribution;
2. an explicit intervention operator;
3. a contract describing what may and may not change;
4. a clean/intervention matched unit;
5. a validity profile that gates inclusion independently of model outcomes;
6. paired estimands and uncertainty procedures; and
7. a claim policy separating controlled contrasts from broader causal claims.

This tuple can be instantiated beyond CAB's current synthetic task suite. That
is the intended general evaluation contribution.

## 2. Objects and notation

Let a base task be

\[
B=(G,E^0,A^0,M),
\]

where:

- \(G\) is the user goal, including required information and success criteria;
- \(E^0\) is the clean environment: tools, observations, initial state, and
  transition rules;
- \(A^0\) is the clean answer contract, including the reference answer and
  whether uncertainty or abstention is permitted; and
- \(M\) is metadata fixed before evaluation, including domain, template, split,
  and generation provenance.

Base tasks are sampled from a frozen target distribution
\(B\sim\mathcal{D}_{B}\). CAB's finite benchmark is an auditable sample from
this distribution, not evidence that it represents all real tool-use tasks.

### 2.1 Clean condition

The clean condition is the identity evaluation:

\[
X^0(B)=(G,E^0,A^0,M).
\]

“Clean” means the designated reference condition. It does not mean easy,
natural, unbiased, or error-free.

### 2.2 Intervention operator

For intervention family \(f\), variant \(z\), and base task \(B\), define

\[
\mathcal{T}_{f,z}(X^0)
  = (G',E^{f,z},A^{f,z},M').
\]

Every operator declaration must contain:

- the intended factor \(F_f\) that it manipulates;
- the fields it may change;
- preserved invariances \(\mathcal{I}_f\);
- the answer-contract transformation \(\tau_{f,z}:A^0\mapsto A^{f,z}\);
- the expected robust behavior; and
- an exclusion rule.

The generated pair is valid only when the intervention-validity profile
confirms that the intended manipulation occurred, the declared invariances were
preserved, and the resulting task is solvable and scoreable. A large model
effect cannot be used to validate the intervention.

### 2.3 Intended factor and preserved invariances

The intended factor is the smallest named environmental property that the
operator is designed to change, such as tool availability, observation
reliability, memory correctness, or evidence salience.

The invariance set \(\mathcal{I}_f\) lists properties that must be equivalent
between the clean and intervened instances. At minimum it addresses:

- the user-level goal;
- latent facts not targeted by the operator;
- permitted information sources, except when availability is the target;
- task budget, unless budget is the preregistered factor;
- agent interface and system policy;
- scoring semantics after applying \(\tau_{f,z}\); and
- non-target difficulty drivers.

Literal field equality is sufficient for some invariances but not necessary for
all of them. Semantic invariances require outcome-blinded human review.

### 2.4 Answer-contract transformation

The answer contract is a first-class part of an intervention. CAB permits three
declared transformations:

- **answer preserving:** the same substantive answer remains required;
- **answer updating:** the environment legitimately changes the correct answer,
  and a deterministic transformation or new reference is recorded; or
- **abstention updating:** the intervention makes a definitive answer
  unsupported, so calibrated uncertainty or abstention becomes correct.

If no unambiguous transformation can be specified before agent execution, the
pair is excluded. Reusing the clean answer blindly is not an acceptable default.

## 3. Agent policy and trajectories

For agent or agent configuration \(a\), let \(\pi_a\) be a possibly stochastic
policy over actions conditional on interaction history:

\[
\pi_a(u_t\mid h_t),\quad
h_t=(X,u_1,o_1,\ldots,u_{t-1},o_{t-1}).
\]

The policy includes the model, prompt or scaffold, decoding parameters, tool
protocol, stopping rule, and resource limits. A change to any of these creates
a different agent configuration. The trajectory \(H_a(X;r)\) also depends on
a recorded repeat identifier or randomness state \(r\).

The gold answer, gold tool sequence, hidden validity annotations, and paired
counterpart are not exposed in the policy's observation history.

## 4. Outcome variables and scorer

Let the frozen scorer be \(g(H,A)\). The primary binary outcome is

\[
Y_a^{c}(B,r)=g(H_a(X^0(B);r),A^0)
\]

for the clean condition and

\[
Y_a^{f,z}(B,r)
  =g(H_a(\mathcal{T}_{f,z}(X^0(B));r),A^{f,z})
\]

for the intervention.

The robustness profile may additionally contain:

- recovery after an observable and recoverable failure;
- correct abstention when the answer contract permits or requires it;
- false abstention when a definitive answer remains supported;
- tool-selection and invalid-call outcomes;
- contradiction detection and resolution;
- memory verification and blind-trust failures;
- premature stopping; and
- cost, latency, and step count as secondary deployment outcomes.

Each component outcome has an opportunity denominator. For example, recovery is
undefined when no recoverable failure occurred; it is not silently scored zero.

## 5. Matched unit

The canonical matched unit is

\[
u=(a,m,B,f\text{ or }z,r),
\]

implemented as:

```text
agent_name
model_name
base_task_id
intervention_id_or_family
repeat_id
```

The clean and intervention observations must agree on agent configuration,
model, base task, and repeat policy. One clean observation may be a comparator
for multiple declared intervention variants, but those variants remain
correlated through `base_task_id`. Duplicate observations at the same matched
key, missing counterparts, non-binary outcomes, and missing identifiers are
invalid units; they are logged and excluded rather than averaged.

## 6. Target estimands

For a frozen valid-pair distribution \(Q_f\), CAB reports:

\[
S_0 = \mathbb{E}_{Q_f}[Y^c],\qquad
S_f = \mathbb{E}_{Q_f}[Y^f],
\]

\[
\Delta_f = \mathbb{E}_{Q_f}[Y^c-Y^f],
\]

and clean-conditioned retention

\[
R_f^{CC}
  = \Pr_{Q_f}(Y^f=1\mid Y^c=1).
\]

\(\Delta_f>0\) denotes degradation. \(R_f^{CC}\) answers a narrower question:
among matched units the agent solved cleanly, how often was success retained?
The four transition probabilities
\(p_{11},p_{10},p_{01},p_{00}\) show success retention, breakage, improvement,
and persistent failure.

The historical ACRS ratio \(S_f/S_0\) is secondary. It is suppressed when clean
success is zero or at or below the frozen near-zero threshold. Absolute and
transition estimands remain reportable in that case.

Family-macro and worst-family summaries operate over family-specific valid
matched subsets. Uncertainty is clustered by base task, and cross-agent ranks
are computed only on exact common support.

## 7. Controlled intervention versus causal claims

### 7.1 What the design directly supports

When both conditions are executed under the frozen policy and budget, and the
validity gate passes, the paired contrast estimates the effect of replacing
the clean benchmark condition with the declared intervention condition for the
tested agent on the frozen benchmark distribution.

This interpretation relies on:

- **consistency:** the executed instance matches its declared condition;
- **intervention isolation:** the intended factor changes and required
  invariances hold;
- **no cross-unit interference:** running one unit does not alter another;
- **condition parity:** policy, budget, scorer, and stopping limits are fixed;
- **pair completeness:** missingness does not enter the primary estimator; and
- **scorer validity:** the scorer represents the frozen answer contract.

These assumptions are audited, not inferred from performance.

### 7.2 Causal motivation

The intervention taxonomy is causally motivated because it changes named
environmental factors and measures paired outcome transitions. This design can
localize brittleness more sharply than an unpaired task collection.

### 7.3 What is not identified

CAB does not, without additional assumptions or studies, identify:

- the internal cognitive mechanism that caused a model failure;
- effects in arbitrary natural deployment distributions;
- the effect of model scale, provider, or architecture from observational model
  comparisons;
- a natural-world treatment effect of tool failures generally; or
- transport from synthetic to human-authored tasks.

Paper language must use “controlled intervention” or “paired perturbation”
unless the exact benchmark-local causal estimand and its assumptions are stated.
The benchmark name is not itself a causal-identification claim.

## 8. Validity and evidence gates

A result enters primary analysis only if:

1. the task, intervention operator, answer contract, and analysis plan were
   frozen before confirmatory outcomes were inspected;
2. the pair passes the intervention-validity profile;
3. the run is complete, non-mock, and evidence-eligible;
4. the scorer and pair ledger pass audit;
5. the model comparison uses common support; and
6. uncertainty and exclusions are reported.

Current documents and tests establish `DESIGN_ONLY` and `ENGINEERING_ONLY`
artifacts. They do not create model results, human agreement, or
`PAPER_ELIGIBLE_EVIDENCE`.

## 9. Implementation map

- Pair construction and descriptive estimators:
  `src/causal_agent_bench/metrics/causal_robustness.py`
- Paired tests, clustered bootstrap, rank uncertainty, and scorer sensitivity:
  `src/causal_agent_bench/metrics/statistics.py`
- Fail-closed validity profile:
  `src/causal_agent_bench/safety/intervention_validity_profile.py`
- Property and fixture checks:
  `tests/test_phase5_paired_metrics.py` and
  `tests/test_intervention_validity_profile.py`

The detailed estimator and inference contract is frozen in
`docs/PAIRED_ROBUSTNESS_INFERENCE.md`.
