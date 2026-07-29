# CAB Level-5 hardening baseline

Captured: 2026-07-29

## Repository

- Branch: `main`
- Local commit: `4bac229be426108ee0b44f3c816e3b7950e35cfb`
- Remote commit: `4bac229be426108ee0b44f3c816e3b7950e35cfb`
- Divergence: 0 ahead, 0 behind
- Remote CI: Level-5 foundation, provider-free ceiling, Fast Check, Docs
  Check, Claim Safety and CI all completed successfully for the baseline commit.

Three pre-existing untracked user-owned paths are preserved:

- `promptpacks/CAB_ICLR_ULTIMATE_ONESHOT_BUILD_AND_PUSH_MAIN.md`
- `promptpacks/CAB_ICLR_ULTIMATE_PROMPT_PACK/`
- `reports/ICLR_PROMPT1_POSTFIX_BASELINE.md`

## Scientific state

```text
CAB_LEVEL5_PLATFORM_FOUNDATION_COMPLETE
HUMAN_VALIDATION_REQUIRED
LIVE_EVIDENCE_REQUIRED
EXTERNAL_REPLICATION_REQUIRED
PROTECTED_EVALUATOR_PILOT_REQUIRED
COMMUNITY_PILOT_REQUIRED
CAB_LEVEL5_COMPLETE=false
```

All genuine evidence and external-pilot counters are zero.

## Validation baseline

- Level-5 focused tests: 52 passed
- Full provider-free suite: 1,143 passed, 1 skipped
- Kaggle offline fixtures: 9 notebooks and 72 fixture receipts
- Ruff, mypy and Codespell: passed
- Wheel, source distribution and clean-wheel smoke: passed
- MkDocs non-strict: passed
- MkDocs strict: failed with the documented warning set

## Confirmed weak links

### Registry

`SCHEMA_VERSION` is 1. The migration table stores only a version and timestamp.
There are no ordered migration checksums, backup requirement, interrupted
marker, recovery plan or persistent scheduler/review/evidence/evaluator
repositories.

### Execution

`LocalScheduler` loops serially. `max_concurrency` is descriptive. The backend
contract has only prepare/execute/cancel/cleanup. There are no dependencies,
priority, leases, heartbeats, quotas, timeouts, pause state or subprocess and
offline Kaggle implementations.

### Reliability

`run_fixture_chaos_campaign` marks a case passed whenever its expected-invariant
tuple is non-empty. No physical fault is required.

### Human review

The domain store is in-memory and the HTTP service appends JSONL. A caller can
claim reviewer role with `X-CAB-Role`; there are no sessions, CSRF controls,
qualification UI, durable assignment/adjudication/amendment workflows or
coverage dashboard.

### Evaluator

The runtime command has useful fixture controls but protected mode, image
digest policy, seccomp, rootless verification, signer abstraction, rotation,
revocation, encrypted broker, durable queue and executed malicious-container
classification are absent. HMAC defaults are embedded fixture keys.

### Evidence

Graph nodes, edges, transitions, certificates and result corrections are
in-memory. There is no durable transaction boundary, revocation or transparency
chain.

### Reproduction and quality

Reproduction executes in the developer checkout. It does not create a clean
venv, source archive or container receipt. Level-5-specific coverage is not
gated. Strict documentation does not pass.

## Compatibility and migration risks

- Existing schema-v1 databases must upgrade without losing entities, events,
  dependencies or provenance.
- Existing CLI commands and fixture reproduction must remain compatible.
- Existing fixture receipts must remain clearly non-scientific.
- New durable tables must never store protected task bodies, reviewer identity
  details or signing secrets in the public registry.

## Planned task ownership

Task-owned changes are limited to the canonical Level-5 package, its CLI/SDK
integration, focused tests, Level-5 documentation, hardening reports,
workflows, package/release metadata and public-safe fixtures. The three
pre-existing untracked paths remain outside that ownership.
