# Scorer Robustness Policy

Status: deterministic scorer safety policy. Not a substitute for human validation.

## Supported Matching Modes

- exact match for strict identifiers,
- normalized match for punctuation/case differences,
- numeric tolerance for quantities,
- list/set matching with optional order sensitivity,
- date normalization for explicit dates,
- abstention/uncertainty handling for insufficient-evidence tasks.

## Risks

- false positive substring matches, such as matching `cat` inside `concatenate`,
- false negative paraphrases,
- numeric unit mismatch,
- date format ambiguity,
- over-rewarding refusals when a definitive answer is expected,
- undercounting implicit recovery or verification.

## Policy

Use exact or structured matching where possible. Use substring matching only with word-boundary guards. Any task that requires semantic paraphrase grading, nuanced refusal assessment, or conflict resolution must be marked `human_review_required`.

## Fixture Tests

`tests/test_scorer_robustness_fixture_only.py` covers matching and abstention examples. These fixtures are labeled not evidence.
