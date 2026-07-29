# CAB Level-5 hardening ledger

Baseline commit: `4bac229be426108ee0b44f3c816e3b7950e35cfb`

## Phase 0 — Live audit

State: complete.

The live repository, canonical Level-5 modules, public CLI/SDK, focused tests,
workflows, container definitions, documentation, release records and handoffs
were inspected. The master prompt's weak links were confirmed from current
code. Baseline `main` and `origin/main` were equal and baseline CI was green.

## Phase 1 — Registry migrations

State: complete. Ordered checksum-pinned v1→v2→v3 migrations, automatic
pre-upgrade backups, transactional rollback, an interruption marker, recovery,
integrity checks, dry-run planning and old-v1 compatibility are tested.

## Phases 2–3 — Execution and reliability

State: complete. The durable queue implements priority, dependencies, quotas,
pause/resume, cancellation, leases, fencing, heartbeats, retry/backoff and
crash recovery. Local subprocess and offline Kaggle contracts are operational.
The required 1,000-unit matrix passed at 1/2/4/8 workers. Eighteen faults were
physically injected and all were prevented, contained, recovered or failed
closed.

## Phases 4–6 — Review, evaluator and evidence

State: complete at hardened-pilot scope. Review sessions, CSRF, RBAC,
qualification, two-reviewer assignment, immutable judgments, adjudication,
amendments, privacy-safe exports and backup/restore are durable. The evaluator
enforces protected-mode policy and supplies signer, rotation, revocation,
broker, encrypted fixture-task and queue contracts. Evidence graphs,
certificates, corrections and transparency are persistent and tamper-evident.

No genuine human judgment, model run or protected-evaluator pilot was created.

## Phases 7–10 — Factory, plugins, reproduction and quality

State: complete. Bounded benchmark parsing, lifecycle persistence, diversity
commitments and fail-closed plugin permissions are tested. A committed Git
archive built a wheel and source distribution, installed into an empty virtual
environment and reproduced the same hashes as a clean checkout. Container
execution remains honestly `NOT_EXECUTED` because no usable daemon/image was
available. Level-5 line coverage is 87.68% overall and at least 91.12% in every
critical subsystem. Strict MkDocs completes with zero warnings.

## Phases 11–12 — Red team and unified gate

State: complete. Twenty-two adversarial cases produced 9 prevented, 7 detected,
5 contained and 1 manual-review outcome; zero cases were not mitigated and zero
critical issues remain. The unified gate returns
`CAB_LEVEL5_HARDENED_FOUNDATION_READY` while preserving all five genuine
evidence blockers and `CAB_LEVEL5_COMPLETE=false`.
