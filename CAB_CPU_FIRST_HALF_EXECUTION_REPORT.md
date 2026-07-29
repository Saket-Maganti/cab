# CAB CPU First-Half Execution Report

## Executive summary

CPU-H1 and CPU-H2 were executed. CPU-H1 passed. CPU-H2 found zero genuine
Compact-20 judgments and zero adjudications, so CPU-H3 through CPU-H10 were
blocked without fabrication.

Final state:

```text
CAB_CPU_FIRST_HALF_PARTIAL_GENUINE_INPUTS_MISSING
HUMAN_VALIDATION_REQUIRED
```

This is the correct fail-closed scientific outcome.

## Inputs

- Human-review evidence: zero genuine rows
- Adjudication: zero genuine rows
- Compact GPU shards: none eligible or expected because the slice is not locked
- Existing result directories: fixture/stub/mock/smoke/interrupted engineering
  artifacts only
- Evidence classification: `HUMAN_INPUT_REQUIRED`

Only configured review locations were inspected. A private path/hash audit was
written under an ignored private root. Public reports contain no identities,
protected task bodies, hidden answers, private hashes, or raw trajectories.

## Human validation

Compact-20 coverage is `0/20`, with two independent qualified reviewers
required per item. Agreement and reviewer diagnostics were not computed on an
empty input. C10 remains `C10_PENDING` with five registered blockers.

The two protected future candidate packets cover 160 items and pass static
prevalidation, but all 1,760 review-dimension rows remain blank. Static
prevalidation is not genuine human evidence.

## Compact lock

No slice was frozen. No included/excluded item decision, model panel, run
matrix, seed schedule, Kaggle live bundle, or slice-lock certificate was
created. C10 must pass first.

## Compact import and audit

No genuine shard was imported. Merge, rescore, common support, missingness,
failure taxonomy, scorer audit, trajectory audit, and blinded human audit
packets were not created because no locked raw evidence exists.

## Compact analysis

No success, robustness, ACRS, recovery, abstention, overhead, bootstrap, rank,
RAAC, sensitivity, or informative-null statistic was computed. Fixture outputs
were not used as empirical inputs.

## Decision

The prospective decision rule was preserved. No CPU-H9 decision was made
because there are no Compact outcomes or audits.

## Scale readiness

Scale-100 execution readiness was not claimed and no Scale model run was
performed. Protected Scale candidates are statically valid but human-input
pending.

## Runtime

Measured validation wall time was approximately 283.4 seconds, measured
subprocess CPU was at least 0.122 CPU-hours, and peak recorded RSS was 4.80
GiB. These are engineering measurements, not model throughput estimates.

## Scientific evidence

| Counter | Value |
|---|---:|
| Genuine human judgments | 0 |
| Genuine adjudications | 0 |
| Real model trajectories | 0 |
| Audited real runs | 0 |
| Paper-eligible empirical assets | 0 |
| Supported empirical claims | 0 |
| Independent external reproductions | 0 |
| Protected evaluator pilots | 0 |
| Community pilots | 0 |

Claim eligibility is unchanged. No report in this bundle is empirical paper
evidence.

## Validation

- Focused suite: 131 passed
- Full provider-free suite: 1,171 passed, 1 skipped
- Ruff, mypy, Codespell: PASS
- Structured data: 399/399 PASS
- Security, secret, protected-payload, evidence-safety: PASS
- Strict docs: PASS
- Package build/import: PASS
- Release checks and hardening gate: PASS

The default local registry was initially absent, then initialized under ignored
`.cab/`, migrated to schema 3, and verified with zero entities. The standalone
fixture evidence-graph JSON was absent; persistent evidence-graph tests passed
and no genuine graph was inferred.

## GitHub

Publication details are recorded in
`reports/cpu_first_half/CAB_CPU_FIRST_HALF_GITHUB_PUBLISH.md`.

## Exact next action

Collect genuine Compact-20 review and separate adjudication under the canonical
protocol, then run:

```bash
python3 scripts/validate_cab_human_reviews.py
```
