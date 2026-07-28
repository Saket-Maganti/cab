# ICLR Human Validation and C10 Protocol

**Protocol version:** 1.0
**Canonical contract:** `configs/human_validation/c10_contract_v1.json`
**Canonical validator:** `scripts/validate_cab_human_reviews.py`
**Current evidence:** `HUMAN_INPUT_REQUIRED`
**Completed genuine human rows:** 0
**C10 status:** `C10_PENDING`

This is the canonical protocol for intervention-validity review in Causal
Agent Bench. It defines future human work; it does not contain, infer, or
simulate human judgments. Blank assignment rows, deterministic checks, worked
qualification examples, AI/proxy labels, and fixture-only tests are not human
evidence.

## 1. Review objective and unit

The review unit is one clean/intervention candidate pair. Reviewers see the
task, clean gold and scorer policies, intervention specification, and
deterministic manipulation-check linkage. They do not see model outputs,
provider/model identities, aggregate results, rankings, or another reviewer's
judgments.

Each reviewer records every dimension below:

| Dimension | Allowed values | Passing value | Question |
|---|---|---|---|
| `task_clarity` | yes / no / unclear | yes | Can the task be understood without unstated repository context? |
| `clean_gold_correctness` | yes / no / unclear | yes | Is the clean gold answer/policy correct and complete? |
| `manipulation_success` | yes / no / unclear | yes | Is the intended manipulation actually present? |
| `goal_preservation` | yes / no / unclear | yes | Is the high-level user goal preserved as declared? |
| `invariance_preservation` | yes / no / unclear | yes | Are declared non-target factors preserved? |
| `solvability` | yes / no / unclear | yes | Is the intervened task solvable under its stated abstention/recovery policy? |
| `answer_contract_correctness` | yes / no / unclear | yes | Does the clean-to-intervention answer policy follow from the intervention? |
| `scorer_compatibility` | yes / no / unclear | yes | Can the scorer accept every valid answer allowed by the contract? |
| `realism` | yes / no / unclear | yes | Is the scenario plausible enough for the intended evaluation scope? |
| `ambiguity` | acceptable / problematic / unclear | acceptable | Is any ambiguity absent or explicitly managed? |
| `exclusion_recommendation` | include / revise / exclude | include | Should this exact candidate enter the frozen evaluated slice? |

Every completed row also requires a confidence score from 1 to 5, a substantive
note, a timezone-aware timestamp, the assigned privacy-safe reviewer ID, and
explicit declarations that the source is human and no AI assistance was used.

## 2. Reviewer design

### Compact-20

- Exactly two or more independent qualified reviewers per candidate are
  required.
- A separate qualified adjudicator resolves every dimension-level
  disagreement.
- The adjudicator cannot be either reviewer for that candidate.
- Required C10 evidence cannot come from a study author. Authors may test the
  packet or provide design feedback, but those rows are not eligible.

### Scale-100

- Use two independent reviewers for every candidate.
- A third independent reviewer may be assigned prospectively to high-risk
  families or used as an additional judgment before adjudication when resources
  permit.
- Staged review is allowed for budgeting, but C10 cannot pass until the final
  candidate manifest has full coverage.

Reviewers must work independently before the review sheets are locked. They
must not discuss candidate labels, see aggregate agreement, or inspect
adjudication outcomes during initial review.

## 3. Qualification, expertise, conflicts, and identity

Before assignment, a reviewer must:

1. read this protocol and the packet instructions;
2. complete an independently administered calibration based on
   `REVIEWER_QUALIFICATION_EXAMPLES.md`;
3. score at least 80%;
4. disclose relevant tool-agent, benchmark, scoring, and domain expertise;
5. disclose task authorship, financial/personal conflicts, and prior access;
6. provide consent and acknowledge the compensation disclosure; and
7. attest that the work is human-only and was completed without an AI/proxy.

Eligible IDs use `rvw_<12–64 lowercase hex characters>`; adjudicator IDs use
`adj_<12–64 lowercase hex characters>`. The coordinator creates these from a
salted one-way mapping. The salt and real-name mapping remain outside the
repository. Never invent an ID to fill a row. Obvious placeholders, duplicate
IDs, unregistered IDs, and proxy/synthetic markers are rejected.

## 4. Blinding

The packet includes no model output or model/provider identity. Reviewers
cannot access live run outputs or leaderboards until the review and
adjudication artifacts are locked. The clean/intervention condition and
intervention family remain visible because validity cannot be judged without
them. Gold and scorer policies are visible only in the reviewer packet; they
must never enter the agent-facing payload.

## 5. Packet construction and data entry

Generate or refresh a still-blank packet:

```bash
python3 scripts/build_c10_review_packet.py
```

The builder refuses to overwrite completed reviewer, registry, adjudication, or
session data. The canonical directory is
`data/human_validation/compact20_real_review/`.

1. Confirm `review_items.jsonl` matches the candidate-manifest hash.
2. Keep both model-blinding flags true in `review_session.json`.
3. Register qualified reviewers in `reviewer_registry.csv`.
4. Assign the pre-created reviewer slots out of band.
5. Each reviewer independently completes only their rows in
   `review_judgments.csv`.
6. Lock initial sheets before computing agreement.
7. Populate `adjudication.csv` only for observed disagreements.
8. Update prerequisite report paths/hashes in `c10_prerequisites.json`.
9. Change the session to `real_human` and attest human-only completion only
   after the statements are true.
10. Run the validator. Do not edit output state by hand.

Legacy split sheets (`task_clarity_review.csv`, `gold_policy_review.csv`,
`intervention_isolation_review.csv`, and `adjudication_template.csv`) are
retained only for compatibility with older no-run artifacts. The canonical
validator ignores them.

## 6. Deterministic manipulation checks

`manipulation_checks.json` links every candidate to a versioned check. The
registry covers:

- absent tool;
- injected tool failure;
- stale timestamp exceeding an explicit threshold;
- conflicting observations with distinct values;
- premature success signal;
- missing-evidence marker;
- distractor presence;
- memory-corruption marker;
- tool-output corruption;
- instruction ambiguity; and
- long-horizon dependency markers.

The report is deterministic and hash-bound to the candidate manifest and
instances file. A missing marker returns `BLOCKED`; it is never guessed.
Passing these checks establishes marker presence only (`ENGINEERING_ONLY`).
Reviewers must still judge manipulation success, isolation, goal preservation,
realism, and solvability.

## 7. Agreement and adjudication analysis

For each dimension, report:

- exact raw agreement;
- a 95% Wilson interval for raw agreement;
- Cohen's kappa only for items with exactly two distinct reviewers;
- nominal Krippendorff's alpha for two or more reviewers;
- deterministic item-bootstrap 95% intervals for kappa and alpha;
- label counts, majority prevalence, normalized entropy, and high-prevalence
  warnings;
- adjudication and exclusion rates;
- family-specific final validity; and
- reviewer-confidence distributions and summaries.

Metrics return explicit blocked states when there are fewer than five
comparable candidates. Chance-corrected coefficients return a degenerate-
prevalence blocked state when all labels occupy one category; they must not be
reported as perfect kappa/alpha. Kappa and alpha are diagnostics, not C10 pass
thresholds, because prevalence can make them undefined.

The preregistered raw-agreement threshold is 0.80 both overall and for every
dimension. Adjudication resolves final labels but does not raise pre-
adjudication raw agreement. All disagreements require a linked decision and
rationale from the separate adjudicator.

## 8. Canonical C10 contract

C10 passes only when all of the following are true for one hash-bound review
slice:

1. the session is explicitly `real_human` and `AUDITED_REAL_EVIDENCE`;
2. genuine completed rows exist;
3. every candidate has at least two distinct qualified reviewers;
4. no proxy, AI, synthetic, fixture, placeholder, or duplicate reviewer is
   counted;
5. model-output and model-identity blinding are confirmed;
6. overall and per-dimension raw agreement meet 0.80;
7. every disagreement has valid separate adjudication;
8. every final dimension has its passing value;
9. the verified leakage report passes and its SHA-256 matches;
10. the verified answer-contract report passes and its SHA-256 matches;
11. every candidate's deterministic manipulation check is linked and passes;
12. the review-slice manifest hash and slice hash are frozen and match; and
13. no schema, value, qualification, coverage, timestamp, identity, or
    provenance blocker remains.

Header-only files and metadata-only blank rows cannot pass. Fixture-only inputs
may produce `FIXTURE_CONTRACT_PASS` to test plumbing, but they always retain
`FIXTURE_ONLY`, `C10_PENDING`, zero genuine human rows, and
`slice_lock_allowed=false`.

Validate with:

```bash
python3 scripts/validate_cab_human_reviews.py
```

Exit code 2 is expected while real human work or another C10 prerequisite is
pending. Never weaken the contract to obtain exit code 0.

## 9. Evidence boundary

Human validity review may support an audited claim about the reviewed slice
only after the contract passes. It does not establish model rankings, RAAC
improvement, external validity, or paper-asset eligibility. Those require
separate real execution and postrun audits. See
`docs/HUMAN_REVIEW_RESOURCE_PLAN.md` and `docs/ETHICS_AND_LIMITATIONS.md`.
