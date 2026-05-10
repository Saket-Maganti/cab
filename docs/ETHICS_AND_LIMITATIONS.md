# Ethics and Limitations

## Synthetic Benchmark Limits

This benchmark can make agents look better or worse than they would behave in open-ended deployments. Synthetic tools are useful for control, but they do not cover all real operational risks, interface changes, ambiguous data, latency, or human-in-the-loop workflows.

## Simulated Actions

The default environment does not send real email, create real calendar events, make real bookings, purchase products, access live web pages, or call paid model APIs. The `send_email_draft` and `book_stub` tools are simulations only.

## Data and Privacy

Default tasks use synthetic mock data only. No API keys, private documents, personal email, real calendar data, or customer records should be committed. Any future human-authored or enterprise task data must go through privacy review.

## Scoring Limits

Default scoring is deterministic and auditable, but heuristic. It may miss semantically valid answers or overfit to template wording. If LLM-as-judge scoring is used, judge prompts, model versions, instability, and bias must be reported.

## Intervention Validity

Interventions are designed to change one factor at a time, but they may accidentally alter difficulty, available evidence, or answerability. Human or expert audit is required before making causal claims about isolated skill components.

## Misuse Risks

- Treating smoke results as a leaderboard.
- Overgeneralizing from template tasks.
- Using oracle stub baselines as realistic model estimates.
- Training on public benchmark instances and reporting contaminated results.
- Optimizing agents to benchmark quirks rather than robust behavior.

## Human Validation

If human validation is used, annotators should receive clear instructions, fair compensation, consent information, and an escalation route for ambiguous examples. Reports should include agreement rates and adjudication procedures.

## Responsible Release

Public releases should be versioned and should distinguish code, generated data, run artifacts, and paper claims. Claims should remain tied to `docs/CLAIM_LEDGER.md`.
