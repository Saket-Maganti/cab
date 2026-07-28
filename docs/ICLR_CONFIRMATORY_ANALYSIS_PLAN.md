# ICLR Confirmatory Analysis Plan

Status: `DESIGN_ONLY`
Evidence at freeze: 0 real trajectories, 0 audited runs, 0 empirical claims.

This is the confirmatory plan for “Success Is Not Skill:
Intervention-Validated Robustness Evaluation and Recovery for Tool-Using
Agents.” It must be hashed with the locked task slice before model execution.
Any later change requires a dated deviation record and separate exploratory
label.

## Analysis populations and unit

- Primary unit: paired clean/intervention outcome at the base-task level.
- Clustering: resample `base_task_id`; correlated repeats and variants stay
  together.
- Family analyses: preserve intervention-family strata while resampling base
  tasks.
- Model comparisons: use common task support. Never compare ranks computed from
  different missing subsets without an explicit sensitivity analysis.
- Clean-conditioned outcomes: use only pairs whose clean trial succeeded, and
  report that denominator beside the estimate.
- Recovery and abstention: use explicit opportunity flags. A positive outcome
  without an eligible opportunity is invalid, not a zero.
- Oracle, scripted, fixture, stub, interrupted, corrupt, duplicate, and
  non-audited runs are excluded from empirical claims.

## Primary endpoints

1. Absolute paired degradation:
   \(P(S_{\mathrm{clean}}=1)-P(S_{\mathrm{intervention}}=1)\).
2. ACRS, reported with both component rates and its denominator policy.
3. Clean-conditioned robustness:
   \(P(S_{\mathrm{intervention}}=1\mid S_{\mathrm{clean}}=1)\).
4. RAAC treatment effect on intervention success under the preregistered budget
   comparison.

No primary endpoint is reportable until C10, slice lock, scorer validation,
run-integrity audit, and evidence promotion pass.

## Secondary endpoints

- transition profile: success→success, success→failure, failure→success,
  failure→failure;
- per-family degradation and worst-family robustness;
- recovery success among recovery opportunities;
- correct abstention among abstention opportunities and false abstention on
  solvable clean tasks;
- clean-performance change under RAAC;
- added model calls, tool calls, tokens, latency, and measured cost;
- rank probability and pairwise superiority probability;
- naturalistic-transfer success and calibration.

## Exploratory endpoints

- model × intervention-family interaction;
- contradiction, verification, clarification, and alternate-route trace
  frequencies;
- leave-one-family-out transfer;
- leave-one-model-out transfer only if the model count permits stable fitting;
- cost-normalised efficiency frontier;
- error-taxonomy and failure-gallery summaries;
- optional provider/open-model heterogeneity.

Exploratory multiplicity is not converted into confirmatory wording.

## Estimation and uncertainty

- Pilot intervals: 1,000 deterministic bootstrap replicates.
- Final intervals: 10,000 deterministic replicates.
- Seed: `20260728`, unless the locked manifest names a replacement before data
  exist.
- Default confidence level: 95%.
- Headline bootstrap: base-task cluster bootstrap.
- Sensitivity: pair-level bootstrap, family-stratified cluster bootstrap, and
  BCa intervals where stable.
- Binary paired test: exact McNemar/binomial test on discordant pairs.
- Rank uncertainty: synchronized cluster bootstrap over common support; report
  expected rank, rank interval, full probability matrix, and tie handling.
- Pairwise superiority: bootstrap probability that the row model ranks above
  the column model, ties contributing one half.

One cluster, no pairs, no discordant pairs, zero clean success, near-zero clean
success, constant outcomes, non-identifiable scorer rates, and undefined model
fits return explicit blocked/undefined states.

## Multiplicity

- One primary RAAC comparison and the locked primary robustness endpoint use
  familywise error control by Holm adjustment.
- Secondary family-level tests use Benjamini–Hochberg FDR and are labelled
  secondary.
- Exploratory analyses report unadjusted and adjusted values where useful but
  cannot support headline confirmatory language.
- Model and intervention subsets cannot be chosen from observed performance.

## SESOI and equivalence

Before the slice is locked, the human research lead must record a smallest
effect size of interest (SESOI) for absolute paired degradation and RAAC
benefit. Until that field is filled, superiority claims remain blocked.

Clean-performance non-inferiority/equivalence uses a paired two-one-sided-test
contract with a preregistered absolute margin. The repository implements the
test but intentionally supplies no margin. Post-hoc margins are forbidden.

## Mixed-effects model

A binary mixed-effects model is secondary and used only when there are at least
10 independent base-task clusters, both outcome classes occur, convergence is
reported, and the random intercept is identifiable. Fixed effects may include
policy, intervention family, model, and preregistered interactions; the base
task receives a random intercept. If convergence or identifiability fails,
report the failure and retain the paired non-parametric analysis as primary.

## Missingness and integrity

- Report missingness by model, condition, policy, family, and run.
- Never silently perform complete-case analysis.
- Infrastructure failure, policy abstention, scorer failure, and missing
  trajectory are distinct states.
- Duplicates are rejected before scoring or merging.
- Interrupted sessions stay ineligible until resumably completed and audited.
- Missing-not-at-random risk is a limitation and receives worst/best-case
  sensitivity where material.

## Scorer sensitivity

Estimate scorer false-positive and false-negative rates only from blinded human
review. Apply preregistered correction scenarios and flip sensitivity after
those rates exist. If assumed error rates are unidentifiable or not human
validated, the sensitivity result is blocked and cannot validate a claim.

## RAAC analysis

Compare:

- standard tool use;
- `RAAC_LIGHT`;
- `RAAC_FULL` on the preregistered subset;
- `VERIFY_ONLY`, `RETRY_ONLY`, `ABSTAIN_ONLY`, `NO_CROSS_CHECK`,
  `NO_ALTERNATE_ROUTE`, and `NO_FINAL_VERIFY` as selected ablations.

Primary fairness analysis uses equal-budget mode. Practical-budget mode is a
separate deployment analysis. Report clean and intervention outcomes plus every
overhead dimension. An improvement that comes only from extra budget is not an
equal-budget effect.

## Naturalistic predictive validity

The outcome is naturalistic task success on the locked transfer set. Candidate
predictors are clean success, ACRS, clean-conditioned robustness, recovery
score, abstention score, worst-family robustness, and the full robustness
profile.

Report:

- Pearson and Spearman association with bootstrap intervals;
- multivariable regression with rank/conditioning diagnostics;
- calibration bins and error;
- leave-one-family-out performance;
- leave-one-model-out only if the panel is sufficiently large;
- uncertainty and explicit small-panel limitations.

These are predictive associations, not causal deployment effects.

## Power and allocation

Power calculations are prospective scenarios only and must be labelled
`ESTIMATE_NOT_MEASURED`. They vary paired degradation, within-task correlation,
cluster count, family allocation, repeats, and expected uncertainty width.
Measured variance cannot be substituted until a genuinely executed pilot is
audited. Compact-20 informs feasibility and scorer sanity; it is not
automatically adequate for headline claims.

## Exclusions

Exclude only by rules frozen before results:

- failed C10 or manipulation check;
- answer-contract invalidity;
- duplicate or overlapping split membership;
- corrupt/incomplete trajectory;
- unpinned task/scorer/code/model revision;
- disallowed hidden-label access;
- infrastructure failure under the separately defined missingness policy.

Every exclusion is logged with reason, stage, actor, timestamp, and affected
hash. Outcome-based exclusion is forbidden.

## Rank-claim policy

Do not say that one model “ranks first” unless common-support rank uncertainty
and pairwise superiority support that wording under the locked threshold.
Otherwise report distributions and ties. A changed clean-versus-robust order is
descriptive until uncertainty and multiplicity are accounted for.

## Null-result policy

A well-powered null result is a valid result. Do not broaden endpoints, change
families, alter the SESOI, add repetitions selectively, or elevate exploratory
findings to recover a positive paper. Report the compatible interval and what
it rules out. If the study is underpowered, state that rather than claiming
equivalence.

## Implementation

- Core paired/bootstrap/rank/scorer functions:
  `src/causal_agent_bench/metrics/statistics.py`
- Report integration:
  `src/causal_agent_bench/analysis/statistics.py`
- ICLR edge, transfer, RAAC, equivalence, missingness, efficiency, and resumable
  shard contracts:
  `src/causal_agent_bench/analysis/iclr_preexecution.py`
