# Ethics and Limitations

**Release:** `0.1.0-rc1`

## Intended Use

Support responsible research on robust tool-using agents: transparent limitations, claim-ledger discipline, and safe defaults (no live side effects in the default environment).

## Out-of-Scope Use

- Deploying benchmark agents against real users without separate safety review.
- Using synthetic success rates to justify automated decisions in high-stakes domains.
- Omitting oracle/stub labeling in public comparisons.

## Data Construction

Synthetic tasks avoid personal data by design. Human-validation samples may include task text exported for annotation — follow `docs/HUMAN_VALIDATION_PROTOCOL.md` for consent, compensation, and escalation.

## Synthetic Data Policy

- No default collection of user PII or proprietary corpora.
- Simulated tools only (`send_email_draft`, `book_stub`, static `web_*` tools).
- Researchers adding real data must complete privacy review and update the dataset card.
- See [SECURITY_AND_PRIVACY.md](SECURITY_AND_PRIVACY.md) for secrets handling and `.env.example`.

## Intervention Families

Interventions may cause agents to produce incorrect or overconfident answers in simulation. They must not be used to elicit harmful content or to automate real harmful actions. Web-shadow tools do not access the live internet.

## Scoring Methodology

Heuristic scoring can disadvantage non-English phrasing or valid paraphrases. LLM judges introduce bias and instability — report judge model, prompts, and agreement with humans (`docs/LLM_JUDGE_RISKS.md`).

## Validation Status

Human validation and intervention audits are **incomplete** for publication-grade claims. Stub runs are **engineering-only** (`validation_status.scientific_evidence_from_stub_runs: forbidden` in `release/release_manifest.json`).

## Known Failure Modes

- **Overconfidence:** high clean success under templates does not imply deployment readiness.
- **Misleading robustness:** ACRS alone can hide uniformly low success.
- **Oracle misuse:** `scripted_oracle_agent` is an upper bound, not a product agent.
- **Environmental harm:** not applicable to default sandbox; applies if users wire real tools externally.
- **Annotator burden:** ambiguous tasks without clear rubrics waste annotator time.

## Contamination Risk

Training on public benchmark instances without disclosure undermines community trust. Report data exposure and use held-out evaluation splits.

## Maintenance Plan

- Track claim status in `docs/claim_ledger.json`.
- Update this document when enabling real tools, human data, or paid API defaults.
- Release-check gate before version tags.

## License

MIT (`LICENSE`). Ethical use remains the responsibility of downstream researchers.

---

## Synthetic benchmark limits

Template tasks understate ambiguity, latency, authentication, and interface drift present in production systems.

## Simulated actions

The default environment does not send email, modify calendars, complete purchases, or browse the live web. Commercial API runs require explicit opt-in (`docs/COMMERCIAL_API_RUNS.md`).

## Data and privacy

Do not commit API keys, `.env` files, private documents, or customer records. Redaction helpers strip secrets from persisted run metadata where implemented.

## Intervention validity

Single-factor design is a **target**, not a guarantee. Expert review is required before causal skill claims (Claim C10).

## Misuse risks

- Treating smoke results as leaderboards.
- Overgeneralizing from synthetic tasks.
- Contaminated training on benchmark instances.
- Optimizing to heuristic scorer quirks.

## Human validation

When annotations are collected: fair compensation, clear instructions, agreement reporting, and adjudication for disagreements (`docs/HUMAN_VALIDATION_GUIDELINES.md`).

### Prospective consent language

Before collecting any row, provide language substantively equivalent to:

> You are invited to review synthetic benchmark task pairs for research on
> tool-using agents. Participation is voluntary. You will judge task and
> intervention validity, not a person's behavior. The packet should contain no
> private user data or model outputs. You may skip an item, pause, or withdraw
> before the de-identified review dataset is locked, without penalty. Your
> name and contact details will not enter the research repository; review rows
> use a privacy-safe pseudonymous ID. We will disclose expected time,
> compensation, data retention, intended publication, and a contact for
> questions before you consent. Do not use an AI or proxy to complete the
> review.

The coordinator must adapt this language to the actual recruitment and
oversight context. This repository does not assert institutional-review or
exemption status; the study owner must obtain any review required by their
institution or jurisdiction before recruitment.

### Reviewer data handling

- Keep the real-name-to-reviewer-ID mapping, salt, consent records, contact
  details, and payment records outside the repository with access limited to
  the review coordinator.
- Commit only privacy-safe IDs, judgments, timestamps, and disclosures needed
  for audit. Do not commit signatures, emails, demographic data, tax/payment
  data, IP addresses, or free text containing identifying information.
- Screen notes for accidental personal or confidential information before any
  release. Public artifacts should prefer aggregate agreement and family-level
  results; release pseudonymous row data only when the consent and release plan
  explicitly permit it.
- State a retention and deletion schedule before consent. Honor withdrawal
  requests made before the de-identified dataset is locked, and explain any
  later limits to withdrawal in advance.
- A privacy-safe ID is pseudonymous, not proof that a reviewer is human. The
  registry, qualification, provenance attestations, and coordinator audit are
  all required.

### Compensation, expertise, and conflicts

Disclose the payment unit, rate, expected minutes, training/adjudication pay,
minimum payment, and payment timing before consent. Report actual compensation
only after it is measured; prospective figures in
`docs/HUMAN_REVIEW_RESOURCE_PLAN.md` are all
`ESTIMATE_NOT_MEASURED`.

Reviewers disclose relevant expertise, prior benchmark access, candidate
authorship, and financial or personal conflicts. Aggregate expertise may be
reported, but it does not justify exposing identities. Reviewers who authored
an assigned candidate or have a material conflict are ineligible for that
candidate.

### Authors as reviewers

Authors may design the rubric, create worked qualification examples, and test
fixture plumbing. Their judgments cannot count toward the two independent C10
reviewers or the separate adjudicator. If resources force author-only review,
those rows are design/pilot feedback, C10 remains pending, and no independent-
validation claim is allowed.

### Human-review limitations

Two-reviewer agreement is sensitive to prevalence, small samples, shared
training, and ambiguous rubrics. Adjudication creates final labels but does not
erase initial disagreement or increase pre-adjudication agreement. Review of
synthetic pairs establishes neither deployment realism nor model performance.
Report raw agreement, confidence intervals, prevalence, exclusions,
adjudication, qualifications, compensation, and any protocol deviations.

## Responsible release

Versioned releases via `release/release_manifest.json`. Distinguish code, frozen data, run artifacts, and paper claims.
