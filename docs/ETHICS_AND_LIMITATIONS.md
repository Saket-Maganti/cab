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

## Responsible release

Versioned releases via `release/release_manifest.json`. Distinguish code, frozen data, run artifacts, and paper claims.
