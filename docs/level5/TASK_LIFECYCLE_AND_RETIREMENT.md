# Task lifecycle and retirement

Legal transitions are:

`DRAFT → STATIC_VALIDATED → HUMAN_REVIEW_REQUIRED`.

Review can move to `ADJUDICATION_REQUIRED` and back, or to `C10_ELIGIBLE`.
Only a valid C10 decision permits `FROZEN → ACTIVE`. Active tasks may be
deprecated or immediately marked contaminated. Deprecated tasks may be retired
or contaminated; contaminated tasks may only be retired.

Every exclusion, contamination decision, amendment and retirement creates a new
versioned receipt. Historical runs retain their original task-version hashes.
Corrections never rewrite old evidence. Contamination propagates to downstream
claims and certificates through invalidation edges.
