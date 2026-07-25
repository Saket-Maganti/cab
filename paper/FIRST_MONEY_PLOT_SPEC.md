# First Money Plot Spec

Status: `SPEC_ONLY_REQUIRES_REAL_RESULTS`

This plot must not be produced from placeholder, mock, stub, dry-run, interrupted, or local-preliminary evidence. It requires real audited 3-model Compact-20 results.

## Plot

Success-rank vs ACRS-rank plot.

Each model gets two rank positions:

- rank by clean-task success,
- rank by ACRS or the current paired robustness score.

The visual should make rank changes inspectable without implying more precision than Compact-20 supports.

## Required Data Fields

- `run_id`
- `model_id`
- `provider_id`
- `deployment_class`
- `candidate_id`
- `family`
- `clean_instance_id`
- `intervention_instance_id`
- `clean_success`
- `intervention_success`
- `paired_delta`
- `acrs`
- `clean_success_rank`
- `acrs_rank`
- `rank_delta`
- `score_uncertainty_interval`
- `rank_uncertainty_interval`
- `scorer_issue_flags`
- `audit_status`
- `paper_eligible_after_audit`

## Rank Computation

1. Compute clean success per model over the reviewed Compact-20 clean conditions.
2. Compute intervention success and paired deltas over matched intervention conditions.
3. Compute ACRS per model using the preregistered scorer implementation.
4. Rank models by clean success.
5. Rank models by ACRS.
6. Compute `rank_delta = clean_success_rank - acrs_rank`.
7. Preserve ties explicitly. Do not break ties silently for visual drama.

## Uncertainty

Show uncertainty using one of:

- paired bootstrap over Compact-20 pairs,
- confidence intervals for success/degradation plus bootstrap rank frequencies,
- a preregistered exact/small-sample interval appropriate for paired binary outcomes.

The plot must show uncertainty bands, rank-change frequencies, or tie/overlap markers. A clean line crossing is not enough by itself.

## Interesting Result

An interesting result would be:

- clean-success ranking differs from ACRS ranking,
- rank change persists in a meaningful share of bootstrap resamples,
- degradation is concentrated in interpretable intervention families,
- scorer sanity and manual review do not invalidate the affected pairs.

The paper wording must remain "in this Compact-20 pilot" unless larger evidence exists.

## Negative Or Null Result

A negative/null result would be:

- clean-success rank and ACRS rank are identical,
- rank differences vanish under uncertainty,
- all models degrade similarly,
- scorer issues or review exclusions dominate the result.

This is still useful. It would show that the ranking-instability hypothesis was not supported in the first compact sample.

## Honest Reporting If Rankings Do Not Change

If rankings do not change:

- say the Compact-20 pilot did not show rank instability,
- report clean success, ACRS, and uncertainty anyway,
- discuss possible explanations: small sample, family mix, model choice, scorer limitations, or genuinely stable rankings,
- do not call the benchmark validated,
- do not claim C4 support,
- use the result to decide whether to revise the slice or defer to a larger approved run.

## Hard Gate

Do not create this plot for the paper until real results, scorer sanity, audit outputs, and paper-asset eligibility checks all pass.

