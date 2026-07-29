# CAB Level-5 foundation build report

Date: 2026-07-29
Repository: `Saket-Maganti/cab`
Branch: `main`

## Final state

```text
CAB_LEVEL5_PLATFORM_FOUNDATION_COMPLETE
HUMAN_VALIDATION_REQUIRED
LIVE_EVIDENCE_REQUIRED
EXTERNAL_REPLICATION_REQUIRED
PROTECTED_EVALUATOR_PILOT_REQUIRED
COMMUNITY_PILOT_REQUIRED
```

Phases 1–10 of the self-contained Level-5 programme are implemented and
validated. Phases 11–14 were not executed because their genuine prerequisites
do not exist. The platform does not emit `CAB_LEVEL5_COMPLETE`.

## Architecture

The implementation adds bounded contexts for:

- immutable experiment registry and provenance;
- benchmark authoring, deterministic compilation and lifecycle;
- execution planning, scheduling, checkpoints and content-addressed artifacts;
- structured observability and deterministic reliability campaigns;
- human review, adjudication and immutable amendments;
- protected evaluator contracts, isolation and signed development receipts;
- public CLI, Python SDK and typed plugin discovery;
- evidence lineage, certification, claims and corrections;
- internal reproduction, external protocols and red-team fixtures;
- governance, supply-chain records, release checks and the Level-5 maturity gate.

SQLite and in-memory registries share one contract. The filesystem artifact
store uses canonical content hashes and atomic writes. Public/private
boundaries, evidence maturity and lifecycle transitions are explicit and
fail-closed.

## Subsystem maturity

| Subsystem | Maturity |
|---|---|
| Registry, benchmark factory, execution OS, artifact store | Engineering complete for the foundation |
| Observability and reliability lab | Fixture-validated; real SLOs not yet measured |
| Human review OS | Fixture-validated; genuine C10 evidence absent |
| Protected evaluator | Development fixture ready; protected pilot absent |
| CLI, SDK and plugins | Public beta foundation |
| Evidence graph and certification | Foundation ready; empirical certificates blocked |
| Reproduction and red team | Internal fixture harness ready; not independent reproduction |
| Governance and release | Foundation complete |

## Validation

The Level-5 focused suite passed 52 tests. The full provider-free suite passed
1,143 tests with 1 skip in 118.56 seconds. Ruff, mypy over 220 source files,
Codespell, 381 structured-data checks, security checks, claim checks, package
build, clean wheel installation, release checks and `git diff --check` passed.

Nine Kaggle notebooks executed offline and emitted 72 fixture receipts. MkDocs
built successfully in non-strict mode; strict mode retains 44 legacy link
warnings. The paper draft built as a 14-page PDF with its placeholders intact.

See `reports/level5/CAB_LEVEL5_VALIDATION_LEDGER.md` for the full ledger.

## Fixture demonstrations

The one-command internal reproduction created a 22-entity registry and 22 CAS
objects, interrupted a 20-unit run after seven units, then resumed and merged
all 20. The evaluator fixture emitted a development-only signed receipt.
Review fixtures remained isolated from C10. The evidence graph and fixture
certificate passed. This demonstration is explicitly not independent
reproduction and contains no real model trajectory.

The reliability campaign passed all 18 deterministic fault classes. The
red-team fixture campaign covered 15 malicious or policy cases: eight
automatically detected and seven explicitly governed as manual-policy cases.

## Scientific evidence

All genuine evidence counters are zero:

- human judgment rows;
- real model trajectories;
- audited real runs;
- paper-eligible empirical assets;
- supported empirical claims;
- independent external reproductions;
- protected evaluator pilots;
- community external pilots.

This report makes no scientific performance claim.

## Security

Archive traversal, malformed output, resource-contract, redaction, provenance,
payload-boundary and receipt-verification fixtures passed. The repository
contains zero protected evaluator payloads. The Docker and Apptainer
definitions exclude private data and default to a public fixture surface.

Remaining risks require real deployment exercises: container-runtime hardening,
identity-backed reviewer operations, protected evaluator administration,
production key custody and external security review.

## Packaging and reproduction

Wheel and source distributions build successfully. A clean temporary
environment installed the wheel and passed CLI, registry and internal fixture
reproduction smoke tests. The internal reproduction is deterministic and
provider-free; it is not a substitute for an external replication.

## Deferred genuine gates

- Human evidence: recruit qualified reviewers and complete genuine C10.
- Live evidence: run models only after the human and approval gates pass.
- Independent reproduction: obtain a genuinely external reproduction.
- Protected evaluator: complete an audited protected pilot.
- Community usability: complete an external community pilot.

## Exact next action

Recruit and onboard qualified human reviewers for the frozen Compact-20
validation protocol under the documented consent, identity, privacy and C10
controls.
