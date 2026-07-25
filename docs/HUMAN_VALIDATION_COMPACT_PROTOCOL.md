# Human Validation Compact Protocol

## Status

Blocked until real provider outputs exist. No annotations are completed.

## Purpose

Validate a small compact sample for:

- trajectory and final-answer review,
- intervention isolation review,
- scorer correctness review.

## Sample Size

If enough provider outputs exist:

- target 30 to 60 samples,
- two annotators per sample,
- adjudicator for disagreements.

If not enough outputs exist:

- keep recruitment/template status only,
- do not report agreement metrics.

## Sampling Rule

Stratify by:

- intervention family,
- model/provider category,
- scorer pass/fail,
- final-answer success/failure,
- suspected mismatch categories.

## Annotation Questions

Annotators review:

- Is the task understandable?
- Is the intervention isolated?
- Is the gold answer/policy plausible?
- Is the final answer correct?
- Is the deterministic scorer correct?
- What evidence span supports the judgment?

## Agreement Metrics

Planned only:

- percent agreement,
- Cohen kappa for two annotators,
- adjudication rate,
- invalid-sample rate.

Do not report any metric until annotation CSVs contain real completed rows.

## Completion Gate

Human validation status may be marked complete only when:

- annotation CSV has real rows,
- adjudication CSV has required disagreement resolutions,
- agreement summary is computed from real data,
- evidence safety passes.
