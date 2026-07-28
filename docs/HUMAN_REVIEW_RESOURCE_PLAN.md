# Human Review Resource Plan

**Status:** prospective design; no human review has been performed.
**Evidence class:** `DESIGN_ONLY` / `HUMAN_INPUT_REQUIRED`
**Completed human rows:** 0

Every duration, rate, workload, and reserve below is labelled
`ESTIMATE_NOT_MEASURED`. Replace estimates with measured, privacy-preserving
operations logs only after genuine review.

## Planning assumptions

| Quantity | Prospective value | Status |
|---|---:|---|
| Standard pair review | 12–18 minutes | `ESTIMATE_NOT_MEASURED` |
| High-risk pair review | 18–25 minutes | `ESTIMATE_NOT_MEASURED` |
| Qualification and protocol training per reviewer | 45–60 minutes | `ESTIMATE_NOT_MEASURED` |
| Adjudication per disputed dimension group | 5–10 minutes | `ESTIMATE_NOT_MEASURED` |
| Adjudication reserve | 20–30% of initial-review time | `ESTIMATE_NOT_MEASURED` |
| Coordinator setup, hashing, and QA for Compact-20 | 1.5–2.5 hours | `ESTIMATE_NOT_MEASURED` |

These estimates include reading the clean/intervention pair, gold and scorer
policies, deterministic check result, eleven judgments, confidence, and a
substantive note. They exclude recruiting, institutional review, contracting,
and payment-processing time.

## Compact-20 plan

Two independent reviewers cover all 20 pairs.

| Work | Prospective effort | Status |
|---|---:|---|
| Reviewer A: 20 × 12–18 min | 4–6 hours | `ESTIMATE_NOT_MEASURED` |
| Reviewer B: 20 × 12–18 min | 4–6 hours | `ESTIMATE_NOT_MEASURED` |
| Two reviewer training sessions | 1.5–2 hours | `ESTIMATE_NOT_MEASURED` |
| Separate adjudicator training | 0.75–1 hour | `ESTIMATE_NOT_MEASURED` |
| Adjudication reserve | 1.6–3.6 hours | `ESTIMATE_NOT_MEASURED` |
| Coordination and QA | 1.5–2.5 hours | `ESTIMATE_NOT_MEASURED` |
| Total Compact-20 labor | 13.35–21.1 hours | `ESTIMATE_NOT_MEASURED` |

Book the adjudicator before initial review. Unavailable adjudication capacity
must leave C10 pending; it is not a reason to resolve disagreements with an
author or AI.

## Scale-100 staged plan

Staging controls burden but does not relax final coverage.

1. **Calibration:** both reviewers independently complete 10 non-evidence
   calibration examples; revise instructions, then restart any affected
   candidate judgments.
2. **High-risk stage:** review 25 candidates from conflict, corruption,
   ambiguity, hidden-evidence, and answer-changing families first.
3. **Remaining stage:** review the other 75 candidates only after protocol
   ambiguities from stage 2 are frozen.
4. **Optional third review:** prospectively assign a third reviewer to high-
   risk families or collect it before adjudication for predeclared cases.
5. **Adjudication:** a separate person resolves all dimension-level
   disagreements after initial sheets are locked.

| Work | Prospective effort | Status |
|---|---:|---|
| Two reviewers × 100 × 12–18 min | 40–60 hours | `ESTIMATE_NOT_MEASURED` |
| High-risk review increment | 5–9 hours | `ESTIMATE_NOT_MEASURED` |
| Reviewer training | 1.5–2 hours | `ESTIMATE_NOT_MEASURED` |
| Separate adjudicator training | 0.75–1 hour | `ESTIMATE_NOT_MEASURED` |
| Adjudication reserve | 9–20.7 hours | `ESTIMATE_NOT_MEASURED` |
| Optional third-reviewer lane | 5–10 hours | `ESTIMATE_NOT_MEASURED` |
| Coordination and QA | 3–5 hours | `ESTIMATE_NOT_MEASURED` |
| Total Scale-100 labor | 59.25–107.7 hours | `ESTIMATE_NOT_MEASURED` |

If resources are below this envelope, complete Compact-20 first and keep
Scale-100 at `HUMAN_INPUT_REQUIRED`. Sampling or single-reviewer coverage must
not be described as full Scale-100 validation.

## Compensation and scheduling

Before consent, disclose the unit of payment, rate, expected minutes, minimum
pay, payment timing, and whether training/adjudication are paid. Set the actual
rate using the reviewer's location, expertise, employment arrangement, and
applicable policy; no unmeasured rate is asserted here. Report the final
compensation method and aggregate labor transparently without exposing private
identities.

Use bounded sessions of 60–90 minutes with breaks. Reviewers may pause or
withdraw under the consent policy. Do not use unpaid speculative work to close
C10.

## Quality controls

- hash-bind every packet to the candidate manifest;
- require two distinct qualified reviewer IDs per candidate;
- keep model output, identity, results, and peer labels blinded;
- administer and record qualification before assignment;
- preserve timezone-aware timestamps;
- reject partial, invalid, duplicate, placeholder, AI, and proxy rows;
- lock initial sheets before agreement analysis;
- report raw agreement, kappa/alpha applicability, prevalence, confidence
  intervals, exclusions, and adjudication;
- reserve a separate adjudicator with no authorship or candidate-review role;
- rerun leakage, answer-contract, manipulation, and slice-hash prerequisites;
  and
- retain raw private mappings outside the repository.

## Compute and storage fit

Packet generation, CSV review, agreement analysis, and C10 validation are CPU-
only and stream small text artifacts. They require neither model inference nor
Kaggle. The expected packet is well within the stated 16 GB M4 / 512 GB
resource envelope. Do not collect screenshots, audio, or unnecessary personal
data; compact CSV/JSON artifacts are sufficient.

## Evidence boundaries

Training examples, blank assignment rows, coordinator checks, AI/proxy labels,
and fixture-only tests are not human evidence. Human review can validate only
the reviewed slice and cannot establish model performance or RAAC effects.
Actual counts, time, compensation, exclusions, agreement, and adjudication
must remain unreported until measured.
