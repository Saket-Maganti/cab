# Intervention Validity Profile

**Status:** `DESIGN_ONLY` protocol with `ENGINEERING_ONLY` validation code  
**Human-review status:** `HUMAN_INPUT_REQUIRED`  
**Empirical-claim status:** no validity or agreement results are asserted here

## 1. Purpose

An intervention-validity profile (IVP) determines whether a generated
clean/intervention pair measures the declared factor well enough to enter a
paired analysis. It is frozen and reviewed without access to agent identities,
trajectories, scores, or effect sizes.

The IVP is not a quality score averaged across dimensions. A critical failure
cannot be offset by strengths elsewhere. Primary inclusion is fail-closed.

## 2. Unit and provenance

One profile belongs to one:

```text
(base_task_id, intervention_id, intervention_family)
```

The record also has a stable `profile_id`, evidence class, review sources,
reviewer count, agreement, and an explicit exclusion reason when applicable.
Profiles must be regenerated or invalidated after a task, operator, answer
contract, scorer, or rendered-environment change.

## 3. Required dimensions

Each dimension records:

```text
judgment: pass | fail | uncertain | not_reviewed
rationale: non-empty text tied to visible evidence
source: artifact or review-packet identifier
```

| Dimension | Question answered | Pass criterion | Primary gate |
|---|---|---|---|
| Manipulation success | Did the intended factor actually change in the rendered instance? | The target change is observable and matches the operator declaration. | Yes |
| Goal preservation | Is the user-level objective equivalent after the intervention? | Required intent and success semantics are preserved, except for a declared answer-contract transformation. | Yes |
| Invariance preservation | Did all declared non-target properties remain equivalent? | Every frozen invariance is checked; no material non-target difficulty change is found. | Yes |
| Solvability | Can a policy following the allowed interface still satisfy the answer contract? | A valid evidence or recovery path exists within the frozen budget, or correct abstention is explicitly allowed. | Yes |
| Answer-contract validity | Is the clean contract correctly preserved, updated, or changed to abstention? | The transformation is deterministic or independently reviewable and contains no unresolved gold ambiguity. | Yes |
| Scorer compatibility | Does the frozen scorer implement the transformed contract? | Structured and boundary cases pass; semantic cases are routed to blinded review. | Yes |
| Realism | Is the scenario plausible for the external setting named in a claim? | Reviewers judge the setting and presentation plausible for that claim's target population. | No for internal contrast; yes for realism/transfer claims |
| Ambiguity | Is there a unique defensible scoring interpretation? | The item is acceptably unambiguous under the annotation guide. | Yes |

`ambiguity=pass` means ambiguity is below the preregistered exclusion threshold;
it does not mean language contains no uncertainty.

## 4. Reviewer agreement

`reviewer_agreement` is a proportion in \([0,1]\) computed only after at least
two independent human reviews. Static validators, generators, LLM proxies, and
the person who wrote the item do not silently count as independent human
reviewers.

The default confirmatory gate is:

```text
reviewer_count >= 2
reviewer_agreement >= 0.80
```

Agreement below the threshold produces `adjudication_required`, not a negative
validity conclusion. Agreement is reported by dimension and overall in the
eventual study; the profile stores the frozen per-item gate value. The
threshold must be frozen before confirmatory model outcomes are inspected.

## 5. Fail-closed states

The canonical evaluator returns:

| State | Trigger | Primary paired analysis |
|---|---|---|
| `valid` | All primary dimensions pass and the human-agreement gate passes. | Eligible only with audited evidence class |
| `human_input_required` | A primary dimension is uncertain/not reviewed, or independent review is incomplete. | Excluded |
| `adjudication_required` | Primary dimensions pass but agreement is below threshold. | Excluded pending adjudication |
| `excluded` | Any primary dimension fails or an exclusion reason is recorded. | Excluded |

Evidence class is a separate gate. An all-pass fixture or static profile remains
`FIXTURE_ONLY` or `ENGINEERING_ONLY`; it does not become scientific evidence.
Primary inclusion requires `AUDITED_REAL_EVIDENCE` or
`PAPER_ELIGIBLE_EVIDENCE`.

Low realism does not invalidate an otherwise well-controlled benchmark-local
contrast. It makes `supports_realism_or_transfer_claim=false`. This separation
prevents external-validity concerns from being hidden while preserving a valid
internal methodology study.

## 6. Exclusion reasons

The profile retains both structured reasons and free-text `exclusion_reason`.
Canonical structured reasons include:

- `failed_dimensions:<comma-separated dimensions>`;
- `unresolved_dimensions:<comma-separated dimensions>`;
- `independent_human_review_incomplete`;
- `reviewer_agreement_below_threshold`; and
- `recorded_exclusion:<reason>`.

Excluded pairs remain in the audit ledger but never enter the primary
denominator. Exclusion counts are reported by family and reason. They are not
deleted or silently regenerated until they pass.

## 7. Review procedure

### 7.1 Freeze

Before review, freeze:

- base task and rendered clean instance;
- operator version and rendered intervention;
- intended factor and invariance checklist;
- answer-contract transformation;
- scorer version and boundary cases;
- review rubric and agreement threshold; and
- split and profile identifiers.

### 7.2 Outcome-blinded packet

The packet contains the clean and intervention instances in randomized order,
the declared goal, intended factor, invariances, answer contracts, allowed tool
interface, and scorer behavior examples. It excludes model names, trajectories,
aggregate scores, and whether the intervention produced a large effect.

### 7.3 Independent review

Each reviewer assesses all eight dimensions and supplies a rationale. A
reviewer may choose `uncertain`; forced certainty is not treated as agreement.
Disagreements are preserved before adjudication.

### 7.4 Adjudication

An adjudicator may:

- confirm the pair;
- correct a locally fixable specification defect and require re-review;
- narrow the claim supported by the pair; or
- record an exclusion.

If an item is edited, it receives a new content hash/profile version. The old
decision remains in the audit trail.

### 7.5 Freeze before outcomes

The primary-valid set and exclusions are frozen before confirmatory agent
outcomes are inspected. Any post-outcome validity concern is reported as a
protocol deviation and analyzed through a preregistered sensitivity analysis,
not silently used to curate the effect.

## 8. Aggregated validity reporting

The validity study reports, overall and by family:

- number sampled, reviewed, adjudicated, passed, and excluded;
- pass/uncertain/fail rate for every dimension;
- agreement statistic with uncertainty;
- exclusion reasons;
- differences between generated and human-authored subsets;
- answer-preserving, answer-updating, and abstention-updating counts; and
- sensitivity of model estimates to the frozen validity gate.

Do not report only the retained set. Retention rate is part of the methodology
result because a family that often fails validity may not support its intended
claim.

## 9. Machine implementation

The canonical implementation is:

```text
src/causal_agent_bench/safety/intervention_validity_profile.py
```

It provides:

- immutable `ValidityAssessment` and `InterventionValidityProfile` records;
- validation of judgments, identifiers, evidence classes, reviewer counts, and
  agreement bounds;
- `evaluate_intervention_validity(...)`; and
- distinct gates for controlled-intervention and realism/transfer claims.

Tests in `tests/test_intervention_validity_profile.py` verify all-pass
eligibility, fail-closed behavior for every primary dimension, missing review,
low agreement, low realism, impossible agreement metadata, and recorded
exclusions. These tests are `ENGINEERING_ONLY`, not human-validity evidence.

## 10. Relationship to existing audits

The IVP consumes or links to CAB's intervention-isolation, gold-output,
tool-schema, leakage, and human-review artifacts. The repository-wide validity
scorecard summarizes infrastructure readiness; it does not replace this
per-pair profile.
