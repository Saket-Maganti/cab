# Main-Set Resource-Aware Decision Policy

Status: `DESIGN_ONLY`
Current decision: do not execute or freeze Main-500.

CAB optimises scientific diversity and uncertainty reduction, not a headline
task count. Main expansion is a gated decision after Compact-20 and Scale-100,
not an automatic milestone.

## Candidate scopes

| Scope | Scientific role | Human burden | T4×2 burden | Current disposition |
|---|---|---|---|---|
| Scale-100 only | controlled confirmatory core | bounded | bounded | preferred minimum |
| Scale-100 + naturalistic 50–100 | controlled core plus transfer | moderate | moderate | preferred ICLR design if validity passes |
| diverse 150–250 main set | narrower uncertainty / richer family allocation | high | high | conditional |
| Main-500 | large expansion | very high | very high | not justified pre-execution |

All burdens are qualitative planning judgements. Numerical runtime, storage,
and reviewer-time values must be labelled `ESTIMATE_NOT_MEASURED`.

## Mandatory prerequisites for any expansion

Every condition must pass:

1. Compact-20 review, adjudication, C10, slice lock, scorer sanity, and audited
   pilot completion;
2. Scale-100 genuine task diversity and human validity;
3. a stable, scientifically meaningful controlled-robustness signal or an
   uncertainty analysis showing why more clusters are needed;
4. a naturalistic-transfer design with provenance, licence, privacy, injection,
   and answer-contract review;
5. a prospective power calculation showing material uncertainty reduction;
6. measured T4×2 feasibility from a small approved run;
7. measured storage and checkpoint/export feasibility;
8. funded and scheduled human review/adjudication capacity;
9. no performance-based task selection;
10. no contaminated or publicly exposed task entering a confirmatory role.

Failure of any item keeps the current scope.

## Decision rule

Prefer Scale-100 plus 50–100 naturalistic tasks when it can test the primary
controlled effect, RAAC, and transfer hypotheses with honest uncertainty.

Move to 150–250 only if:

- the predicted interval remains too wide at the current cluster count;
- additional tasks add domains, contracts, workflows, or intervention support
  rather than template variants;
- Scale-100 signal and scorer reliability are stable enough to justify cost;
- the human and T4×2 plans remain feasible.

Move to Main-500 only if all of the above still hold and a preregistered
calculation shows that 150–250 cannot resolve a central question. “Bigger
benchmark” is not a scientific justification.

## Stop conditions

Stop expansion when task additions mostly repeat normalized instruction
patterns, answer contracts, tools, or source artifacts; when reviewer
adjudication cannot keep pace; when sessions cannot checkpoint/export safely;
or when the naturalistic transfer question is already answered within planned
precision.

Null or weak pilot signal does not automatically demand more tasks. First
distinguish a precise null from low power, intervention invalidity, scorer
error, and model-floor/ceiling effects.

## Required decision record

Before changing scope, record:

- evidence hashes;
- audited Compact-20 and Scale-100 summaries;
- prospective power scenarios;
- incremental diversity profile;
- reviewer hours and adjudication reserve;
- measured runtime/storage assumptions;
- selected scope and rejected alternatives;
- date, accountable human decision-maker, and deviation from this policy.

Until that record exists, the only allowed main-set action is further
pre-execution validation—not generation, locking, or execution.
