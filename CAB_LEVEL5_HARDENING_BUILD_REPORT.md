# CAB Level-5 hardening build report

Captured on 2026-07-29.

## Executive summary

CAB is now in state `CAB_LEVEL5_HARDENED_FOUNDATION_READY`. The pass repaired
the operational weak links identified at baseline without manufacturing
scientific evidence. Registry upgrades, concurrent execution, crash recovery,
human review, protected-evaluator controls, persistent evidence, benchmark and
plugin boundaries, internal clean-room reproduction, deep tests, strict docs,
and red-team controls are implemented and exercised.

This is a hardened production-readiness foundation. It is not full scientific
Level 5: `CAB_LEVEL5_COMPLETE=false`, and every genuine evidence counter
remains zero.

## Before and after

Baseline `4bac229be426108ee0b44f3c816e3b7950e35cfb` had a schema-v1 registry,
serial descriptive scheduling, invariant-label-only chaos tests, in-memory
review/evidence stores, a fixture evaluator without protected-mode operational
controls, developer-checkout reproduction, no Level-5 coverage gate, and a
strict documentation failure.

The hardened implementation at
`1a810a0f059d18e65d4dae2ee3c2fabda7e08fe1` has executable and persistent
contracts for every one of those surfaces. Its fixture and internal-cleanroom
evidence is explicitly classified and cannot promote a scientific claim.

## Registry schema and migrations

The canonical SQLite schema is version 3. Ordered v1→v2→v3 migrations are
checksum-pinned and covered by dry-run planning, automatic pre-upgrade backup,
transactional rollback, interruption markers, recovery, integrity checks, and
old-v1 compatibility tests. Durable scheduler, review, evaluator, evidence,
certificate, correction, transparency, benchmark, and plugin tables are
created only through this framework.

## Scheduler architecture and stress

The operational scheduler uses a primary coordinator, durable SQLite queue,
thread workers, content-addressed artifacts, priority and dependency rules,
per-backend/per-model quotas, pause/resume, cancellation, leases, fencing,
heartbeats, timeout, retry/backoff, stale recovery, and terminal-state
idempotency. Local subprocess and offline Kaggle backends execute real fixture
contracts.

The mandatory campaign ran 1,000 units at each concurrency of 1, 2, 4, and 8:

| Workers | Succeeded | Cancelled | Quota-deferred | Attempts | Wall time | Peak RSS |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 990 | 5 | 5 | 1,010 | 58.77 s | 137,347,072 B |
| 2 | 990 | 5 | 5 | 1,010 | 58.69 s | 147,783,680 B |
| 4 | 990 | 5 | 5 | 1,010 | 58.25 s | 147,783,680 B |
| 8 | 990 | 5 | 5 | 1,010 | 58.33 s | 147,783,680 B |

Every run recovered one forced stale lease, had zero registry-contention
errors, zero duplicate commits, zero missing terminal states, and the same
merged result hash
`aa6b63acbef06efb6f68fb100ae808dfd2d7ca83c602ab568ea022bdf7d41e9e`.

## Fault injection and recovery

All five crash points passed after durable reopen: after lease, after artifact
write, before registry commit, after artifact registration, and before
terminal scheduler state. There were zero duplicate committed results.

The physical fixture campaign executed 18/18 faults: nine recovered, four
prevented, three failed closed, and two were detected and contained. No case
was unmitigated and no case required manual recovery. These are real local
fault injections against fixtures, not real-provider service-level evidence.

## Human review

The review system now provides durable authenticated sessions, CSRF
protection, role checks, qualification, conflict-aware two-reviewer
assignment, immutable judgments, adjudication, amendments, coverage views,
privacy-filtered export, backup, and restore. The pilot fixture exercises the
full lifecycle. It created no genuine human judgment row.

## Protected evaluator

Protected mode now enforces immutable image digests, network denial,
read-only/rootless/resource policies, output limits, kill/cleanup behavior,
signer abstraction, key rotation and revocation, encrypted fixture-task
handling, durable queue leases, replay protection, and signed receipts.
Development HMAC keys are rejected by protected mode, and no production secret
is stored in the repository.

Twelve malicious-container cases were enumerated. No usable local evaluator
image/daemon was available, so all 12 are honestly `NOT_EXECUTED`. Mocked
orchestration tests cover classifier and cleanup paths but do not count as a
protected-evaluator pilot. State:
`PROTECTED_EVALUATOR_HARDENED_PILOT_READY`.

## Evidence and certification

Nodes, edges, transitions, certificates, corrections, revocations, and the
transparency chain are durable and tamper-evident. Certificate issuance is
policy-gated and fixture evidence cannot support empirical promotion.
Corrections preserve the original record and revocation state. Transaction,
hash, replay, and restart behaviors are exercised.

## Factory and plugins

Benchmark authoring has bounded YAML/JSON parsing, strict schemas, lifecycle
persistence, diversity commitments, deterministic compilation, provenance,
and malicious-input tests. Plugins have typed metadata, API compatibility,
forbidden governance capability checks, sensitive-permission fail-closed
behavior, bounded diagnostics, persistent provenance, and isolated discovery
failure reporting.

## Clean-room reproduction

Committed source `1a810a0f059d18e65d4dae2ee3c2fabda7e08fe1`
built and installed successfully in a clean virtual environment. Clean-wheel
and clean-checkout reproduction produced identical manifest, merge, and graph
hashes with zero discrepancies. The container mode is `NOT_EXECUTED` because
the local Docker daemon was unavailable; external independent reproduction is
also `NOT_EXECUTED`.

## Tests, coverage, packaging, and docs

- Focused Level-5 slice excluding slow tests: 77 passed in 4.47 s.
- Complete Level-5 suite: 79 passed in 25.19 s for coverage; the final
  post-CI-fix local contract run passed 79 in 19.66 s.
- Full provider-free suite in an isolated clean clone: 1,167 passed, 4 skipped
  in 165.74 s.
- Level-5 line coverage: 87.68% overall against an 85% floor. Critical modules
  range from 91.12% to 92.86% against a 90% floor.
- Ruff, Codespell, and mypy over 224 source files passed.
- Strict MkDocs passed with zero warnings in 1.05 s build time.
- Wheel, source distribution, Twine metadata, dependency consistency, release
  inventory, release dry-run, security check, and evidence-safety checks
  passed.
- Release inventory: 720 files; bundle hash
  `10296676ed6fbc3fec0247ec90cf3991922fff48183485d3e46fc0300bc3c85c`.

The first post-change full-suite run had three failures, all caused by a stale
release inventory. After deterministic regeneration, the affected tests and
the complete isolated suite passed. The first macOS CI pass exposed one
clock-edge timeout fixture; widening its margin produced a green six-platform
matrix.

## Red team and security

Twenty-two adversarial cases executed: nine prevented, seven detected, five
contained, and one routed to manual review. Zero were unmitigated and zero
critical issues remain. Tracked protected payloads: 0. Production secrets: 0.

## Scientific evidence counters

| Counter | Genuine count |
|---|---:|
| Human judgment rows | 0 |
| Real model trajectories | 0 |
| Audited real runs | 0 |
| Paper-eligible empirical assets | 0 |
| Supported empirical claims | 0 |
| Independent external reproductions | 0 |
| Protected evaluator pilots | 0 |
| Community external pilots | 0 |

## Remaining genuine Level-5 blockers

```text
HUMAN_VALIDATION_REQUIRED
LIVE_EVIDENCE_REQUIRED
EXTERNAL_REPLICATION_REQUIRED
PROTECTED_EVALUATOR_PILOT_REQUIRED
COMMUNITY_PILOT_REQUIRED
CAB_LEVEL5_COMPLETE=false
```

Container reproduction remains unexecuted locally. GitHub Pages deployment
also requires the repository owner to enable Pages with GitHub Actions as its
source; the strict docs build itself is green. Neither limitation changes the
scientific counters.

## Publication

Direct, non-force pushes to `main` published:

- `d1819b0b213c696c4fa0c4982ae0dc5fbae894b7` — operational foundation
- `6eb3bed9ba6ee692fbea15ae9587af9d6aecfb93` — production-readiness pass
- `1a810a0f059d18e65d4dae2ee3c2fabda7e08fe1` — stable macOS timeout contract

For `1a810a0`, the Level-5 foundation workflow passed all eight jobs, including
all Ubuntu/macOS and Python 3.11/3.12/3.13 matrix jobs. Claim Safety, Docs
Check, and Max Ceiling Provider-Free Gates also passed. The final publication
receipt records the remaining workflow results and local/remote SHA equality.

## Exact next action

Recruit and onboard genuine qualified Compact-20 reviewers using the hardened
human-review operating system.
