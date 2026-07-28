# ICLR Scale-100 v2 Diversity Audit

Status: `STATIC_PREVALIDATION_PASS_HUMAN_REVIEW_REQUIRED`

Evidence class: `HUMAN_INPUT_REQUIRED`

This report contains public-safe aggregate facts only. The complete candidate,
answer keys, intervention mappings, and review rows remain under ignored
`private_data/`. The public commitment is
`data/manifests/scale100_confirmatory_v2_public_manifest.json`.

## Candidate counts

| Measure | Count |
|---|---:|
| Base tasks | 100 |
| Intervention mappings | 500 |
| Total planned instances | 600 |
| Unique task IDs | 100 |
| Unique content hashes | 100 |
| Unique templates | 100 |
| Unique workflows | 100 |
| Normalised instruction patterns | 100 |
| Conservative genuinely-distinct lower bound | 100 |

The 100 tasks cover 10 domains with 10 tasks per domain, 10 tool
combinations, four canonical answer contracts, and four difficulty bands with
25 tasks each.

## Contract and intervention coverage

Canonical answer-contract counts:

- `ORIGINAL_ANSWER_REQUIRED`: 20
- `ORIGINAL_ANSWER_WITH_VERIFICATION_REQUIRED`: 20
- `QUALIFIED_UNCERTAINTY_ACCEPTED`: 40
- `RECOVERY_ROUTE_REQUIRED`: 20

All 10 registered intervention families occur 50 times, yielding 500 linked
deterministic manipulation checks. Missing manipulation checks: 0.
Non-canonical answer contracts: 0.

## Duplication and overlap

| Check | Result |
|---|---:|
| Exact duplicate groups | 0 |
| Normalised duplicate groups | 0 |
| Structural duplicate groups | 0 |
| Lexical pairs at or above 0.82 | 0 |
| Maximum observed lexical similarity | 0.6875 |
| Answer-overlap groups | 0 |
| Public/development role-overlap signals | 0 |
| Compact-20 overlap signals | 0 |
| Contaminated-v1 overlap signals | 0 |
| Naturalistic-v2 overlap signals | 0 |

Coarse structural archetypes are intentionally shared because tool schemas and
answer semantics recur; this does not create exact, normalised, structural, or
lexical duplication under the registered audit. The template-variant risk is
`low`.

## Safety and provenance

The static provenance, licence, privacy, PII, path, secret, prompt-injection,
label-revealing-ID, and evaluator-visibility checks all returned zero blockers.
The public-surface scan found zero private payload fragments, and no file below
`private_data/` is tracked.

## Freeze and evidence boundary

The public manifest supplies deterministic SHA-256 payload commitments and the
canonical registry records the role as
`scale100_confirmatory_v2_protected`. It is not frozen for scientific
execution: two independent human reviews per task, adjudication, C10, answer
contract confirmation, leakage confirmation, and a final slice lock remain
mandatory. No model-output-based selection was performed.

Prospective power and allocation scenarios are frozen in
`docs/ICLR_CONFIRMATORY_ANALYSIS_PLAN.md`. They are labelled
`ESTIMATE_NOT_MEASURED`; no measured variance or effect is claimed here.

Reproduce the aggregate validation with:

```bash
PYTHONPATH=src:. python3 scripts/validate_iclr_private_candidates.py
```
