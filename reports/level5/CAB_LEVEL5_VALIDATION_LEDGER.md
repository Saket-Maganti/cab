# CAB Level-5 validation ledger

Validation date: 2026-07-29
Branch: `main`
Provider or paid-model execution: none

## Final state

```text
CAB_LEVEL5_PLATFORM_FOUNDATION_COMPLETE
HUMAN_VALIDATION_REQUIRED
LIVE_EVIDENCE_REQUIRED
EXTERNAL_REPLICATION_REQUIRED
PROTECTED_EVALUATOR_PILOT_REQUIRED
COMMUNITY_PILOT_REQUIRED
```

The platform foundation is complete. `CAB_LEVEL5_COMPLETE` is deliberately
unreachable while genuine evidence and external pilot counters remain zero.

## Automated validation

| Validation | Result | Measured detail |
|---|---:|---|
| Level-5 focused tests | PASS | 52 passed |
| Full provider-free suite | PASS | 1,143 passed, 1 skipped in 118.56 s |
| Release-manifest affected tests | PASS | 15 passed in 3.33 s |
| Ruff | PASS | repository clean |
| mypy | PASS | 220 source files |
| Codespell | PASS | repository clean |
| Structured-data validation | PASS | 381 of 381 files |
| Git whitespace validation | PASS | `git diff --check` |
| Package build | PASS | wheel and source distribution built |
| Clean wheel install | PASS | `cab` smoke and fixture reproduction |
| Documentation build | PASS | non-strict MkDocs build in 0.98 s |
| Paper draft | PASS | 14-page PDF built |
| Security check | PASS | public-safe fixture set |
| Claim ledger | PASS | unsupported empirical claims blocked |
| Release check | PASS | 710-item inventory |
| Kaggle offline validation | PASS | 9 notebooks, 72 fixture receipts |
| Split-registry validation | PASS | public/private boundary checks |
| Internal fixture reproduction | PASS | interrupted at 7; resumed to 20 |
| Reliability campaign | PASS | 18 of 18 deterministic fault classes |
| Red-team fixture campaign | PASS | 15 of 15 policy cases |
| Level-5 gate | PASS | foundation complete; five genuine gates blocked |

The signed release bundle hash at validation was
`85862b21e94bdb32bb95027f56e6c17f841d28f20b35806f2d4c6b8c052ffdc8`.

## Fixture demonstrations

- Registry: 22 entities persisted with append-only event/provenance records,
  transaction rollback, freeze, backup/restore and tamper checks.
- Execution: a deterministic 20-unit, two-shard plan interrupted after seven
  units and resumed to all 20 using checkpoints and content-addressed objects.
- Review: role-isolated fixture assignments, judgments, adjudication,
  amendments and agreement diagnostics; fixture rows cannot pass C10.
- Evaluator: archive traversal and malformed-output defenses, mock isolation,
  trusted-broker boundary and signed development-only receipt.
- Evidence: acyclic lineage, legal maturity transitions, public redaction,
  claim blocking, certificate construction and versioned corrections.

## Packaging and documentation notes

The built wheel installed in a fresh temporary virtual environment and its
`cab` entry point completed help, registry and reproduction smoke checks.
`twine` was not installed in the validation environment, so no independent
`twine check` was recorded; wheel installation and import/execution checks
passed.

MkDocs completed in non-strict mode. Strict mode reports 44 pre-existing
cross-tree link warnings in legacy documentation; the new Level-5 navigation
and pages build successfully. These warnings do not weaken a scientific or
security gate, but remain documentation maintenance work.

The paper draft builds with visible placeholders and existing LaTeX warnings.
No placeholder is represented as empirical evidence.

## Genuine evidence counters

| Counter | Value |
|---|---:|
| Human judgment rows | 0 |
| Real model trajectories | 0 |
| Audited real runs | 0 |
| Paper-eligible empirical assets | 0 |
| Supported empirical claims | 0 |
| Independent external reproductions | 0 |
| Protected evaluator pilots | 0 |
| Community external pilots | 0 |
| Critical red-team issues | 0 |
| Protected payloads committed | 0 |

## Interpretation

The tests establish engineering behavior for the foundation and its fixtures.
They do not establish scientific effects, human validity, independent
reproducibility, evaluator production readiness or community usability.
Those claims remain fail-closed behind the five explicit blockers above.
