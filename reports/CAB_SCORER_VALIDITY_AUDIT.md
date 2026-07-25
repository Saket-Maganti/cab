# CAB Scorer Validity Audit

> Canonical maximum-ceiling artifact. Regenerate with `python3 scripts/generate_cab_max_ceiling_reports.py`.

Generated: 2026-07-23T17:23:44.726749+00:00

- Production scorer: `cab_typed_final_answer`
- Version: `2.0.0`
- Canonical source: `trajectory.final_answer`; trajectory behavior is used only when preregistered by the answer/scorer policy.
- Legacy substring behavior is a named, limited compatibility fallback, not the typed production default.
- Evidence class: `FIXTURE_ONLY` for conformance results.

## Answer contracts

- `ORIGINAL_ANSWER_REQUIRED`
- `ORIGINAL_ANSWER_WITH_VERIFICATION_REQUIRED`
- `RECOVERY_ROUTE_REQUIRED`
- `QUALIFIED_UNCERTAINTY_ACCEPTED`
- `CLARIFICATION_REQUIRED`
- `ABSTENTION_REQUIRED`
- `MULTIPLE_VALID_OUTCOMES`
- `HUMAN_REVIEW_REQUIRED`

## Typed comparison coverage

- normalized strings and categories;
- numeric absolute/relative tolerances, percentages, units, and currencies;
- dates, datetimes, time zones, and booleans;
- ordered lists, unordered sets, key-value objects, structured JSON, and ranges;
- multiple accepted answers and preregistered partial credit;
- abstention, clarification, refusal, recovery actions, unavailable-tool disclosure, and required tool use.

## False-positive controls

Expected fragments in negations, rejected alternatives, quoted task text, tool logs, intermediate values, malformed JSON, injection strings, or an incorrect final selection do not receive credit.

## Provenance and rescoring

Every score record carries scorer name/version/config, scorer-policy ID/hash, gold-policy ID/hash, answer contract, code revision, intervention ID, and repeat ID. Raw trajectories remain immutable and can be rescored offline.

## Conformance result

- Command: `/Library/Frameworks/Python.framework/Versions/3.11/bin/python3 -c 'import json; from causal_agent_bench.metrics.typed_final_answer import typed_scorer_fixture_self_check as f; r=f(); print(json.dumps(r, sort_keys=True)); raise SystemExit(0 if r.get('"'"'status'"'"') == '"'"'PASS'"'"' else 1)'`
- Exit code: `0`
- Elapsed: `0.113` seconds
- Outcome: `PASS`

## Future scorer-sanity workflow

Sample by model, family, condition, and auto-score; blind model identity; collect independent human correctness; estimate false-positive/negative rates; adjudicate disagreements; and block paper eligibility above the preregistered disagreement threshold. No real scorer-sanity rows are populated.

## Residual limits

- Typed parsing cannot resolve genuinely ambiguous gold policies.
- Currency conversion is intentionally not inferred.
- Human-review-required contracts remain unscored automatically.
- Conformance fixtures prove code behavior, not benchmark validity.
