# 18 README Audit

## Findings

README command categories align with available CLI behavior: install, doctor, smoke/local runs, generation, validation, scoring, analysis, provider configuration, and paper asset export.

Tested commands:

- editable install with `python3`
- CLI help
- doctor
- provider listing
- data validation
- deterministic run/score/analyze/export
- provider dry-run and estimate-cost

## Risks

- Bare `python` fails in this environment because pyenv is misconfigured; README examples should prefer `python3` or document interpreter setup.
- Provider sections must stay clearly conditional on API keys, model IDs, pricing, and explicit paid-call approval.
- Current paper/results language must not imply real LLM findings.

## Fixes

No README edits were needed during this audit beyond respecting the existing setup-dependent wording.

