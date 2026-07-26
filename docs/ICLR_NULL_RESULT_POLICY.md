# ICLR Null-Result and Claim Policy

**Policy freeze:** `ICLR-NULL-v1`, 2026-07-26  
**Status:** `DESIGN_ONLY`  
**Applies to:** RQ1–RQ10 and every confirmatory CAB analysis

## 1. Principle

A null or unfavorable result changes the conclusion, not the benchmark,
threshold, scorer, family mixture, or evidence label. CAB will not optimize the
evaluation design against confirmatory outcomes and then present the optimized
version as if it had been fixed in advance.

Null results are part of the methodology evaluation. They can show that an
intervention family is invalid, a ratio adds little, rankings are stable, a
scaffold does not help, or synthetic behavior fails to transfer.

## 2. Result states

Every confirmatory claim receives one of these states:

| State | Definition | Permitted conclusion |
|---|---|---|
| `supported_at_frozen_threshold` | Eligibility gates pass and the preregistered effect/precision threshold is met. | Use the RQ's conditional allowed wording with estimate and uncertainty. |
| `practically_equivalent_within_SESOI` | A valid equivalence procedure places the effect inside the frozen equivalence region. | Evidence of practical equivalence for the tested distribution and precision. |
| `null_not_rejected` | Eligibility gates pass, but the interval includes the null and effects beyond the SESOI. | No resolved effect; neither equivalence nor absence is established. |
| `underpowered` | Valid data exist, but cluster/opportunity/model counts or prospective precision gates fail. | Descriptive estimate only; no confirmatory conclusion. |
| `invalid_design_or_measurement` | Intervention validity, scorer reliability, common support, or run integrity fails. | No target-effect conclusion; report the methodological failure. |
| `protocol_deviation` | A frozen element changed or outcomes were inspected before a material decision. | Affected analysis is exploratory unless an untouched holdout remains. |
| `not_executed` | No eligible real run exists. | `EXECUTION_PENDING`; fixtures and plans are not substituted. |

“No significant difference” is never treated as practical equivalence.

## 3. Mandatory reporting for every state

Reports include:

- point estimate and uncertainty interval;
- SESOI or equivalence region;
- valid pair, base-task, family, agent, and opportunity counts;
- invalid, missing, and excluded counts with reasons;
- denominator and bootstrap-validity states;
- adjusted and unadjusted p-values when tests are used;
- scorer and intervention-validity status;
- protocol deviations;
- evidence class; and
- the frozen allowed wording selected for the result state.

Null results are not moved only to an appendix while favorable secondary
results become the headline.

## 4. Prohibited rescue actions

After confirmatory outcomes are inspected, do not:

- remove difficult tasks or intervention families without applying a
  pre-existing validity rule;
- redefine “clean,” the matched unit, success, recovery, or abstention;
- switch from paired to unpaired denominators;
- lower the human-agreement, sample, model-count, or effect-size threshold;
- choose a new near-zero denominator cutoff;
- change the scorer because it improves the preferred conclusion;
- add repeats selectively for agents or families;
- increase only one method arm's budget;
- choose the best-looking seed, prompt, checkpoint, provider, or model version;
- replace family-macro with micro aggregation, or vice versa, post hoc;
- report point ranks without their uncertainty;
- call fixtures, mocks, dry runs, interrupted runs, or proxy review real
  evidence; or
- use the confirmatory split for benchmark repair and then reuse it as untouched
  evidence.

Legitimate data-integrity corrections require a logged, outcome-independent
rule, versioned artifacts, rerunning all affected conditions, and a sensitivity
report including the original analysis when possible.

## 5. RQ-specific null handling

| RQ | Null or adverse outcome | Required interpretation or reframe |
|---|---|---|
| RQ1 competence | \(\Delta\) is near zero or imprecise. | CAB did not resolve a material competence gap. Reframe toward the controlled evaluation framework and validity findings only if those stand independently. |
| RQ2 rankings | Clean and robustness ranks agree or rank intervals overlap widely. | Report rank stability/uncertainty. Do not claim success rankings are misleading. |
| RQ3 heterogeneity | Family contrasts are small or unresolved. | Report pooled and family estimates; do not invent a vulnerable-family narrative. |
| RQ4 recovery | Recovery is rare, unreliable, or unrelated to final success. | Treat recovery labels as non-informative or revise them only on a new development split. |
| RQ5 abstention | No calibrated tradeoff appears. | Report over-abstention, under-abstention, or lack of opportunity coverage as observed. |
| RQ6 validity | Pass rate/agreement misses threshold. | Exclude or reframe affected families. A failed validity study blocks the associated controlled claim even if model effects are large. |
| RQ7 scorer | Scorer agreement is weak or conclusions change under plausible error. | Label results scorer-sensitive; withhold affected headline claims. |
| RQ8 transfer | Human-authored results reverse or materially differ. | Restrict claims to the generated CAB distribution and foreground the transfer failure. |
| RQ9 improvement | The scaffold has no benefit, harms clean success, or uses more compute. | Report a negative method result; do not retune on confirmatory tasks. |
| RQ10 scale | Association is absent or non-monotone. | Report no resolved association in the tested set; never infer that scale cannot matter. |

## 6. Missingness, failures, and interrupted runs

The primary estimator uses complete, predeclared matched units. CAB reports
condition-specific attrition. If missingness differs by condition, agent, or
family, the result is not assumed missing completely at random.

Required actions are:

1. preserve incomplete and invalid rows in the run ledger;
2. attempt only policy-compliant, configuration-identical resume;
3. never score partial output as a complete run;
4. report complete-case estimates;
5. add worst/best-case bounds when missingness could change the conclusion; and
6. downgrade to `underpowered` or `invalid_design_or_measurement` when bounds
   cross the claim threshold.

Provider outages, quota failures, and resource exhaustion are operational
facts, not zero model outcomes. Selective retry is forbidden.

## 7. Multiplicity and exploratory findings

The confirmatory family of hypotheses is frozen in
`docs/ICLR_RESEARCH_QUESTIONS_AND_HYPOTHESES.md`. Holm-adjusted primary results
determine support. Exploratory analyses:

- are labeled `exploratory`;
- disclose how many variants were examined;
- preserve all tested families/configurations in an analysis manifest;
- do not inherit confirmatory wording; and
- require replication on untouched tasks before promotion.

An interesting post-hoc subgroup can motivate a new study, not retroactively
become RQ1.

## 8. Equivalence

Practical equivalence may be claimed only when:

- the equivalence region was frozen before outcomes;
- the intervention, scorer, and evidence gates pass;
- both one-sided tests or an equivalent interval criterion pass;
- the cluster count supports the procedure; and
- the statement is restricted to the tested benchmark distribution.

For RQ1 and RQ9, the default absolute-success SESOI is five percentage points.
Other metrics use RQ-specific frozen thresholds. An imprecise interval spanning
both benefit and harm is `null_not_rejected`, not equivalent.

## 9. Evidence-language gate

| Evidence class | May support |
|---|---|
| `DESIGN_ONLY` | Definitions, planned hypotheses, proofs under stated assumptions |
| `ENGINEERING_ONLY` | Implementation and test claims |
| `FIXTURE_ONLY` | Arithmetic and pipeline diagnostics |
| `HUMAN_INPUT_REQUIRED` | A documented unresolved human-review dependency |
| `EXECUTION_PENDING` | A documented unexecuted study |
| `PRELIMINARY_REAL_EVIDENCE` | Directional pilot observations with explicit limitations |
| `AUDITED_REAL_EVIDENCE` | Audited empirical statements within the audit scope |
| `PAPER_ELIGIBLE_EVIDENCE` | Frozen, audited, complete results mapped to a paper claim |

Evidence cannot be upgraded by rhetoric. In particular, a passing estimator
fixture cannot support a model-behavior hypothesis, and an LLM proxy cannot
fabricate reviewer agreement.

## 10. Paper decision after nulls

The paper may remain a methodology contribution if:

- the formal operator/contract framework is coherent;
- intervention validity is credibly measured;
- paired inference and scorer auditing are useful and reproducible; and
- empirical results, including nulls, demonstrate what the methodology does or
  does not reveal.

The paper must narrow or stop if intervention validity or scorer reliability
fails. It must not claim submission readiness merely because the engineering
and theory artifacts are complete.

All frozen nulls and adverse results remain in the claim ledger and released
analysis bundle, subject to privacy and licensing constraints.
