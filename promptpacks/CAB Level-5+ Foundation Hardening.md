# CAB Level-5+ Foundation Hardening and Production-Readiness Master Prompt

## Intended Use

Run this prompt in Codex from:

`/Users/saketmaganti/Projects/causal-agent-bench`

Repository:

`Saket-Maganti/cab`

Branch:

`main`

Recommended effort:

> **Ultra**

This is a focused deepening and production-readiness pass.

It begins from the current CAB Level-5 foundation and must repair the weaknesses identified after the first Level-5 build. It must not create another disconnected package or another set of shallow interfaces.

The goal is:

> Convert CAB Research OS v0.1 from a broad fixture-validated foundation into a deeply integrated, stress-tested, operationally credible Level-5 foundation that is genuinely ready for human validation, live model execution, independent reproduction, and protected-evaluator pilots.

This prompt does not authorise fabricated human evidence, model evidence, external replication, protected-evaluator deployment evidence, or community feedback.

---

# 1. Verified Starting State

At prompt creation, the latest public `main` commit is:

`4bac229be426108ee0b44f3c816e3b7950e35cfb`

Foundation implementation commit:

`7d26e62824e03bd2995eac88a0d157e118ab6279`

Current reported state:

```text
CAB_LEVEL5_PLATFORM_FOUNDATION_COMPLETE
HUMAN_VALIDATION_REQUIRED
LIVE_EVIDENCE_REQUIRED
EXTERNAL_REPLICATION_REQUIRED
PROTECTED_EVALUATOR_PILOT_REQUIRED
COMMUNITY_PILOT_REQUIRED
CAB_LEVEL5_COMPLETE=false
```

Current validation summary:

* Level-5 focused tests: 52 passed;
* full provider-free suite: 1,143 passed, 1 skipped;
* nine Kaggle notebooks: 72 fixture receipts;
* Ruff, mypy and Codespell passed;
* package build and clean-wheel installation passed;
* non-strict documentation build passed;
* strict documentation build retained 44 warnings;
* all genuine scientific and external-evidence counters remain zero.

Inspect the live repository first and treat it as authoritative if it has advanced beyond this state.

---

# 2. Why This Pass Exists

The first Level-5 build created credible contracts, modules, documentation, and vertical slices. It did not make every subsystem operationally mature.

This pass must address the following verified weaknesses.

## 2.1 Execution OS weakness

The current scheduler is substantially a serial fixture runner.

Weaknesses include:

* `max_concurrency` is descriptive rather than truly enforced;
* no real worker pool;
* no priority scheduler;
* no dependency-aware queue;
* no task leases;
* no heartbeats;
* no stale-worker recovery;
* no quota manager;
* no retry backoff;
* no enforced backend timeout;
* no operational pause and cancellation model;
* no real local-subprocess backend;
* no complete Kaggle export/import backend;
* no backend capability negotiation across actual implementations.

## 2.2 Reliability weakness

The current fault campaign mostly enumerates expected invariants instead of physically injecting failures.

A fault must not pass merely because an expected-invariant tuple exists.

Each campaign case must create an actual failure state and verify a concrete recovery or fail-closed invariant.

## 2.3 Human-review OS weakness

The current human-review service is a minimal local endpoint with append-only JSONL storage.

Weaknesses include:

* no practical reviewer UI;
* no durable assignment system;
* no qualification workflow;
* no secure reviewer sessions;
* no adjudication interface;
* no amendment workflow;
* no administrator dashboard;
* no workload and coverage view;
* no private identity-provider abstraction;
* no robust concurrent-submission handling.

## 2.4 Protected evaluator weakness

The evaluator has a credible contract and initial Docker policy, but remains fixture-grade.

Weaknesses include:

* development signing keys;
* no production signer abstraction;
* no key rotation;
* no certificate or receipt revocation;
* no image digest enforcement;
* no image-policy inspection;
* no seccomp profile;
* no explicit rootless-runtime verification;
* no trusted task-broker service boundary;
* no encrypted task-store interface;
* no evaluation queue or quotas;
* no real malicious-container campaign;
* narrow regex-based exfiltration checks;
* cleanup and isolation are mainly asserted rather than independently verified.

## 2.5 Evidence and certification weakness

The evidence graph and result registry are primarily in-memory foundations.

Weaknesses include:

* no durable graph repository;
* weak transaction integration with the main registry;
* no certificate revocation;
* no signing-key rotation;
* no transparency log;
* no persistent lineage query;
* no complete artifact-to-paper provenance;
* no durable result-correction history.

## 2.6 Migration weakness

The registry contains a migration table but not a real ordered migration framework.

Weaknesses include:

* no multiple historical schema versions;
* no migration checksums;
* no pre-migration backup requirement;
* no interrupted-migration recovery;
* no old-database compatibility fixtures.

## 2.7 Reproduction weakness

The current reproduction command runs an internal fixture inside the same repository context.

It does not yet prove:

* clean source checkout;
* clean wheel installation;
* clean virtual environment;
* container reproduction;
* cross-platform hash agreement;
* deterministic discrepancy reporting.

## 2.8 Testing and documentation weakness

The new Level-5 code is broad relative to the focused test count.

Weaknesses include:

* limited concurrency stress testing;
* limited state-machine testing;
* limited migration testing;
* limited malicious-input testing;
* no Level-5 coverage threshold;
* no focused mutation testing;
* 44 strict documentation warnings;
* several specifications are brief summaries instead of operational manuals.

## 2.9 Red-team reporting weakness

The current red-team campaign can mark a manual-policy case as passed without proving mitigation.

The hardened campaign must distinguish:

* prevented;
* automatically detected;
* detected and contained;
* recovered;
* manually reviewable;
* not mitigated;
* not executed;
* accepted residual risk.

---

# 3. Mission and Correct End State

Deepen every weak subsystem until CAB reaches:

```text
CAB_LEVEL5_HARDENED_FOUNDATION_READY
```

This means CAB is genuinely ready to begin:

* qualified human review;
* C10;
* live model calibration;
* Compact-20 execution;
* external clean-room reproduction;
* a protected-evaluator pilot.

The final state must still include:

```text
HUMAN_VALIDATION_REQUIRED
LIVE_EVIDENCE_REQUIRED
EXTERNAL_REPLICATION_REQUIRED
PROTECTED_EVALUATOR_PILOT_REQUIRED
COMMUNITY_PILOT_REQUIRED
```

Do not emit:

```text
CAB_LEVEL5_COMPLETE
```

Do not emit:

```text
PROTECTED_EVALUATOR_PRODUCTION_READY
```

The correct evaluator state after this pass is:

```text
PROTECTED_EVALUATOR_HARDENED_PILOT_READY
```

---

# 4. Non-Negotiable Rules

Do not:

* generate human judgments;
* auto-adjudicate;
* mark fixture review as genuine;
* run real models;
* call provider APIs;
* launch paid compute;
* fabricate external reproduction;
* fabricate protected-evaluator pilot results;
* fabricate community feedback;
* promote fixture outputs into empirical evidence;
* expose or commit protected task bodies;
* commit private reviewer identities;
* commit signing secrets;
* weaken C10;
* weaken evidence transitions;
* weaken contamination or leakage gates;
* weaken security tests;
* create a parallel Level-5 package;
* duplicate canonical registry, CLI, benchmark, evaluator, review, or evidence systems;
* preserve shallow behaviour solely for compatibility;
* force-push;
* rewrite Git history;
* create a feature branch;
* open a pull request;
* stage unrelated user-owned files.

Always:

* inspect before modifying;
* extend the canonical `src/causal_agent_bench/level5/` package;
* preserve compatible public APIs where sensible;
* provide migrations when storage formats change;
* use typed schemas;
* use explicit state transitions;
* fail closed;
* preserve immutable raw evidence;
* keep protected data outside Git;
* use content hashes and provenance;
* record every irreversible decision;
* maintain an incremental ledger;
* retain original failure logs;
* run narrow tests after each repair;
* run broad tests at phase boundaries;
* update documentation with code;
* push directly to `main`;
* verify local and remote SHA equality.

---

# 5. Baseline and Live Audit

Before editing:

```bash
cd /Users/saketmaganti/Projects/causal-agent-bench

git status --short
git status --branch --short
git branch --show-current
git rev-parse HEAD
git remote -v
git fetch origin main
git rev-list --left-right --count origin/main...main
```

Create immediately:

* `reports/level5_hardening/CAB_LEVEL5_HARDENING_BASELINE.md`
* `reports/level5_hardening/CAB_LEVEL5_HARDENING_STATE.json`
* `reports/level5_hardening/CAB_LEVEL5_HARDENING_LEDGER.md`
* `reports/level5_hardening/CAB_LEVEL5_HARDENING_DECISIONS.md`
* `cab_level5_hardening_handoff.md`

Record:

* current commit;
* current remote commit;
* current CI state where available;
* changed and untracked paths;
* preserved user-owned files;
* current test counts;
* current Level-5 gate;
* exact weak links confirmed from live code;
* public-API compatibility risks;
* migration requirements;
* planned file ownership.

Inspect at minimum:

* all modules under `src/causal_agent_bench/level5/`;
* CLI parsers and SDK;
* current Level-5 tests;
* workflows;
* documentation;
* Docker and Apptainer files;
* package metadata;
* release manifest;
* current reports and handoffs.

Do not rely only on the previous summary.

---

# 6. Phase 1 — Real Registry Migration Framework

Replace nominal migration handling with an ordered, testable migration system.

## 6.1 Migration model

Each migration must record:

* migration ID;
* source schema version;
* target schema version;
* checksum;
* application timestamp;
* duration;
* preconditions;
* postconditions;
* reversible or non-reversible status;
* backup requirement;
* status;
* failure record.

Create meaningful versions:

* schema v1: legacy fixture foundation;
* schema v2: scheduler queues, leases, and heartbeats;
* schema v3: review, evidence, certificates, revocations, and evaluator records.

Do not add meaningless columns merely to claim migration support.

## 6.2 Safety

Implement:

* automatic pre-migration backup;
* backup hash;
* database integrity check;
* dry-run migration plan;
* transactional migration where SQLite permits;
* interrupted-migration marker;
* recovery procedure;
* refusal when a previously applied migration checksum changes;
* no destructive in-place downgrade;
* explicit export-before-upgrade option.

## 6.3 Persistent repositories

Persist:

* queue entries;
* worker leases;
* heartbeats;
* scheduler attempts;
* resource reservations;
* review users and sessions;
* assignments;
* judgments;
* amendments;
* adjudications;
* evidence nodes and edges;
* certificates;
* revocations;
* transparency entries;
* result corrections;
* evaluator submissions;
* evaluator receipts.

Never persist protected task bodies or plaintext signing secrets in the public registry.

## 6.4 Concurrency and recovery tests

Test:

* multiple readers;
* competing writers;
* lease-acquisition races;
* transaction rollback;
* process crash during write;
* stale lock handling;
* backup under active read workload;
* public-safe export during concurrent activity;
* migration interruption and recovery.

## 6.5 CLI

Implement:

```text
cab registry version
cab registry migrate --dry-run
cab registry migrate
cab registry backup
cab registry restore
cab registry verify
cab registry inspect-events
```

## Acceptance state

```text
CAB_REGISTRY_MIGRATIONS_HARDENED
```

---

# 7. Phase 2 — Real Concurrent Execution OS

Replace the serial scheduling path with an operational concurrent scheduler.

## 7.1 Scheduler requirements

Implement:

* priority queue;
* dependency-aware ready queue;
* global concurrency limit;
* per-backend concurrency limit;
* per-model concurrency limit;
* fair scheduling across studies;
* deterministic tie-breaking;
* resource reservations;
* unit leases;
* lease expiry;
* worker heartbeats;
* stale-unit recovery;
* cancellation;
* pause and resume;
* deterministic retry backoff;
* terminal failure state;
* timeout enforcement;
* quota exhaustion and deferral;
* idempotent submission;
* exactly-once committed results under at-least-once execution.

A practical local design is acceptable:

* coordinator in the primary process;
* thread or process workers selected by backend;
* SQLite-backed queue and leases;
* monotonic runtime tracking;
* future-compatible remote worker interface.

## 7.2 Backend contract

Each backend must expose:

* immutable name and version;
* capabilities;
* compatibility validation;
* resource estimate;
* prepare;
* launch;
* poll;
* heartbeat;
* checkpoint;
* resume;
* cancel;
* collect;
* cleanup;
* failure classification;
* provenance receipt.

Implement:

### Fixture backend

Deterministic and failure-injectable.

### Local subprocess backend

It must:

* launch commands without shell injection;
* enforce wall-clock timeout;
* capture bounded stdout and stderr;
* support cancellation;
* classify signals and exit reasons;
* use an environment allowlist;
* clean child processes;
* report orphan-process checks.

### Kaggle export/import backend

Do not call Kaggle automatically.

It must:

* export deterministic notebook/run bundles;
* support T4×2 and single-T4 fallback;
* include task, model, policy, and manifest hashes;
* create deterministic shard assignments;
* validate returned receipts;
* reject manifest mismatches;
* import results into the registry and CAS;
* support partial-session resume.

### Provider backend contract

Keep provider execution disabled by default.

Require explicit approval, credentials, and budget before any future call.

## 7.3 Run states

Use explicit states:

```text
PLANNED
QUEUED
LEASED
STARTING
RUNNING
CHECKPOINTING
PAUSED
RETRY_WAIT
SUCCEEDED
FAILED
CANCELLED
TIMED_OUT
QUOTA_DEFERRED
STALE
AUDIT_REQUIRED
```

All transitions must be validated and recorded.

## 7.4 Atomic success contract

A unit is complete only when:

1. raw output is stored in CAS;
2. CAS integrity passes;
3. registry artifact record is committed;
4. provenance edge is committed;
5. scheduler terminal state is committed.

Design recovery for crashes between every step.

## 7.5 Stress demonstration

Run a 1,000-unit fixture study with concurrency:

* 1;
* 2;
* 4;
* 8.

Include:

* mixed task durations;
* dependencies;
* deterministic failures;
* cancellation;
* stale leases;
* retries;
* quota deferral;
* pause and resume.

Measure:

* throughput;
* queue latency;
* duplicate execution attempts;
* duplicate committed results;
* memory;
* registry contention;
* recovery time;
* deterministic merged hash.

Required outcomes:

* zero duplicate committed results;
* zero missing terminal states;
* bounded memory;
* explicit failures;
* deterministic final hash;
* complete interruption recovery.

## Acceptance state

```text
CAB_EXECUTION_OS_OPERATIONALLY_HARDENED
```

---

# 8. Phase 3 — Actual Fault Injection

Remove declarative auto-passing.

Every fault case must:

1. arrange a real fixture state;
2. inject the actual failure;
3. observe the result;
4. verify concrete invariants;
5. preserve logs;
6. classify the outcome honestly.

## Required fault injections

### Worker kill

Launch a subprocess fixture, terminate it with a signal, verify failure classification, lease recovery, retry linkage, and final recovery.

### Timeout

Run a sleeping process beyond its deadline, verify termination, timeout state, and no orphan process.

### Disk full

Use a deterministic filesystem adapter or injected `ENOSPC`.

Verify:

* prior object remains intact;
* partial object is invisible;
* no success record is committed;
* retry succeeds after recovery.

### Permission failure

Inject `EACCES` or use a read-only fixture directory.

### Corrupt checkpoint

Test:

* invalid JSON;
* truncated JSON;
* wrong manifest hash;
* missing completed unit;
* invalid artifact digest.

### Corrupt artifact

Modify object bytes and metadata independently.

Verify quarantine and evidence-promotion refusal.

### Duplicate shard race

Allow two workers to attempt the same unit.

Verify one committed result and linked duplicate attempt.

### Partial upload

Interrupt CAS staging before atomic replacement.

### Network disconnect

Use a local fixture server or transport abstraction that closes mid-transfer.

### Malformed model output

Return:

* invalid JSON;
* invalid schema;
* oversized output;
* invalid encoding;
* missing required fields.

### Scorer crash

Raise during scoring, preserve raw evidence, and prove deterministic rescore.

### Registry contention

Hold an active write transaction and verify timeout, backoff, and recovery.

### Stale heartbeat

Stop heartbeat updates and verify lease reclamation.

### Model OOM classification

Use an explicit backend failure fixture. Do not exhaust the actual Mac.

### Quota exhaustion

Consume a fixture quota and verify deferral.

### Clock skew

Inject wall-clock anomalies while preserving monotonic event ordering.

### Reboot marker

Restart the coordinator from persisted state and verify completed work is not rerun.

## Outcome classes

```text
PREVENTED
DETECTED_AND_CONTAINED
RECOVERED
FAILED_CLOSED
MANUAL_RECOVERY_REQUIRED
NOT_MITIGATED
NOT_EXECUTED
```

Do not count `MANUAL_RECOVERY_REQUIRED` as an automatic pass.

## Property and state-machine tests

Add properties for:

* no duplicate committed result;
* no successful unit without an artifact;
* no paper-eligible evidence from a corrupt parent;
* monotonic event sequence;
* deterministic resume;
* bounded retry;
* immutable raw output;
* changed manifest creates a new identity.

Use Hypothesis if appropriate.

## Acceptance state

```text
CAB_RELIABILITY_FAULT_INJECTION_HARDENED
```

---

# 9. Phase 4 — Durable Human-Review Operating System

Upgrade the review system from a JSON endpoint into a usable local-first application.

## 9.1 Persistence

Use the canonical hardened registry or a dedicated private SQLite review database integrated through hashes.

Private reviewer data must remain outside public Git.

## 9.2 Identity and access

Implement interfaces for:

* local development identity;
* external identity-provider adapter;
* reviewer qualification;
* reviewer role;
* adjudicator role;
* administrator role;
* secure session creation;
* hashed session tokens;
* expiry;
* logout;
* role-based authorisation;
* private identity mapping;
* audit events.

Do not claim real-world identity verification without a genuine identity provider.

## 9.3 Review UI

Build a usable interface containing:

* login;
* qualification and consent;
* reviewer dashboard;
* assignment queue;
* review form;
* autosave draft;
* immutable final submission;
* conflict declaration;
* confidence;
* timing;
* manipulation/invariance/solvability fields;
* notes;
* progress;
* adjudicator dashboard;
* disagreement comparison;
* adjudication form;
* amendment request;
* administrator coverage view;
* agreement statistics;
* workload view;
* export status.

If server-rendered HTML is used:

* escape all content;
* set CSP;
* implement CSRF protection;
* use secure session handling;
* enforce request-size limits;
* reject arbitrary file access.

## 9.4 Assignment lifecycle

Persist:

* assignment version;
* blinded order;
* coverage;
* conflicts;
* replacement history;
* workload;
* receipt hash.

Use states:

```text
INVITED
QUALIFICATION_PENDING
QUALIFIED
ACTIVE
ASSIGNED
DRAFT
SUBMITTED
AMENDMENT_REQUESTED
SUPERSEDED
ADJUDICATION_PENDING
ADJUDICATED
EXCLUDED
C10_READY
ARCHIVED
```

## 9.5 Audit and privacy

Every action records:

* actor;
* role;
* event;
* object;
* previous hash;
* new hash;
* time;
* session;
* public/private classification.

Implement:

* public-safe aggregate export;
* private full export;
* retention plan;
* encrypted-storage adapter interface;
* directory permission checks;
* backup and restore.

## 9.6 C10 integration

The final export must feed the existing canonical C10 validator.

Do not create an alternate weaker C10 path.

## Tests

Include:

* unauthorised access;
* forged role header;
* expired session;
* CSRF;
* duplicate submission;
* amendment history;
* conflict;
* two-reviewer coverage;
* adjudicator separation;
* fixture/genuine isolation;
* concurrent submissions;
* crash during submission;
* backup restore;
* public redaction;
* missing consent;
* AI/proxy attestation rejection.

## Acceptance state

```text
CAB_HUMAN_REVIEW_OS_PILOT_READY
```

The scientific state remains:

```text
HUMAN_VALIDATION_REQUIRED
```

---

# 10. Phase 5 — Hardened Protected Evaluator

## 10.1 Signing system

Replace hard-coded signing defaults in production paths.

Implement:

* signer protocol;
* verifier protocol;
* fixture-only HMAC signer;
* optional Ed25519 signer and verifier;
* key ID;
* public-key export;
* key loading from explicit private path or provider interface;
* key rotation;
* receipt and certificate revocation;
* revocation list;
* signing audit;
* refusal to use development keys in protected mode.

Never generate or commit a production private key.

## 10.2 Submission inspection

Before execution:

* validate archive members;
* limit archive size;
* limit file count;
* reject unsafe symlinks;
* validate entry point;
* require image digest in protected mode;
* inspect image declaration;
* scan for secrets;
* detect bundled protected-like payloads;
* compute package hash;
* produce a policy report.

Provide optional hooks for external vulnerability scanners.

## 10.3 Container hardening

Require where supported:

* digest-pinned image;
* rootless runtime preference;
* user namespace policy;
* seccomp profile;
* AppArmor/SELinux hook;
* `no-new-privileges`;
* all capabilities dropped;
* read-only root;
* no Docker socket;
* isolated PID and IPC;
* tmpfs with `noexec`, `nosuid`, and `nodev`;
* process limit;
* CPU limit;
* memory and swap limit;
* output-size limit;
* network none;
* environment allowlist;
* read-only task mount;
* isolated writable output mount;
* explicit kill and cleanup;
* post-run surviving-process and container inspection.

Protected mode must fail closed when a mandatory control is unavailable.

## 10.4 Trusted task broker

Implement:

* opaque task IDs;
* encrypted task-store adapter;
* authenticated evaluator access;
* one-time task lease;
* audit log;
* no task body returned to an untrusted coordinator;
* public task-set commitment;
* no plaintext protected task in logs.

Fixture mode may use an encrypted local fixture store.

## 10.5 Evaluation queue

Persist:

* submission;
* approval;
* queue state;
* evaluator worker;
* status;
* receipt;
* disqualification;
* correction;
* withdrawal.

Add submitter quotas and rate-limit interfaces.

## 10.6 Anti-exfiltration and anti-gaming

Add layered controls:

* strict output schema;
* field allowlist;
* output-size checks;
* entropy and encoding analysis;
* task/prompt echo similarity;
* repeated-probe detection;
* submission-similarity checks;
* suspicious hardcoded mapping detection;
* score-query prevention;
* resource-anomaly detection;
* abstention abuse policy;
* retry-amplification policy;
* collusion indicators;
* manual review queue.

Clearly label heuristic and manual controls.

## 10.7 Malicious-container campaign

When Docker is available, run local malicious fixtures for:

* filesystem enumeration;
* network access;
* fork attempt;
* memory pressure;
* timeout;
* output flooding;
* prompt echo;
* path traversal;
* signal handling;
* orphan child process;
* environment scraping;
* writable-root assumption.

When Docker is unavailable:

* run contract tests;
* mark container tests `NOT_EXECUTED`;
* do not report them as passed.

## 10.8 Hardened receipt

Record:

* evaluator and runtime versions;
* security-profile hash;
* task-set hash;
* package and image digests;
* signer key ID;
* resources requested;
* resources measured;
* findings;
* cleanup verification;
* output hash;
* evidence class;
* revocation state.

## Acceptance state

```text
PROTECTED_EVALUATOR_HARDENED_PILOT_READY
```

---

# 11. Phase 6 — Persistent Evidence Graph and Certification

## 11.1 Durable graph

Persist evidence nodes and edges in the canonical registry.

Require:

* immutable node IDs;
* content hash;
* node version;
* evidence class;
* public/private status;
* metadata redaction;
* cycle prevention;
* parent existence;
* lineage indexes;
* graph export/import;
* backup;
* integrity verification;
* concurrency safety.

## 11.2 Atomic transitions

An evidence transition must:

1. verify parent states;
2. verify required audits and certificates;
3. validate transition policy;
4. append an immutable event;
5. update materialised state atomically;
6. preserve state history.

Do not mutate evidence state only in memory.

## 11.3 Durable certificates

Persist:

* certificate ID;
* type;
* subject;
* supporting evidence;
* signer key ID;
* issue time;
* expiry;
* status;
* revocation reason;
* superseding certificate;
* public/private fields.

Implement:

```text
cab certificate verify
cab certificate revoke
cab certificate list
cab certificate transparency-verify
```

## 11.4 Transparency log

Create an append-only hash chain containing:

* sequence;
* previous hash;
* current hash;
* event;
* subject;
* timestamp.

Verify the complete chain.

## 11.5 Claim compiler

A claim must specify:

* claim text hash;
* required node types;
* minimum evidence classes;
* common-support requirement;
* scorer audit requirement;
* uncertainty requirement;
* external-reproduction requirement where applicable;
* invalidating nodes;
* eligibility;
* missing prerequisites.

Integrate it with the existing claim ledger.

## 11.6 Paper provenance fixture

Demonstrate:

```text
raw fixture
→ score
→ audit
→ fixture analysis
→ fixture table
→ blocked paper claim
```

Prove fixture evidence cannot become paper eligible.

## 11.7 Corrections

Persist:

* original result;
* corrected result;
* reason;
* reviewer;
* superseding link;
* public notice;
* withdrawal;
* restoration policy if allowed.

## Acceptance state

```text
CAB_EVIDENCE_GRAPH_DURABLY_HARDENED
```

---

# 12. Phase 7 — Benchmark Factory and Plugin Hardening

## 12.1 Factory persistence

Persist:

* authoring specification;
* compilation receipt;
* validation findings;
* review packet version;
* lifecycle;
* contamination event;
* retirement;
* superseding version.

## 12.2 Compiler depth

Add:

* formal before/after target-hash check;
* scorer compatibility;
* executable manipulation-check fixture contract;
* tool-schema compatibility;
* intervention-family plugin validation;
* deterministic canonicalisation;
* provenance completeness;
* privacy classification;
* separate public/private outputs;
* bounded inputs;
* malicious YAML/JSON tests;
* no arbitrary code execution.

## 12.3 Diversity engine

Improve:

* structural fingerprints;
* template concentration;
* source concentration;
* author concentration;
* domain balance;
* tool balance;
* answer-contract balance;
* intervention-family balance;
* difficulty balance;
* duplicate clusters;
* role overlap;
* protected commitment overlap.

Keep semantic similarity optional and provider-free.

## 12.4 Plugin security

Add:

* hashed plugin metadata;
* compatibility constraints;
* controlled entry points;
* isolated loading failures;
* diagnostic timeout where feasible;
* capability permission model;
* no canonical-gate override;
* plugin provenance;
* plugin test kit;
* malicious plugin fixtures.

## Acceptance state

```text
CAB_BENCHMARK_FACTORY_AND_PLUGINS_HARDENED
```

---

# 13. Phase 8 — Clean-Room Reproduction

Implement three internal reproduction modes.

## 13.1 Clean virtual environment

* build wheel and source distribution;
* create empty temporary venv;
* install with locked constraints;
* run fixture reproduction;
* compare expected hashes;
* remove environment after receipt.

## 13.2 Clean source checkout

Use a temporary detached checkout or `git archive`.

Do not run from the developer working tree.

## 13.3 Container reproduction

Build from a clean source context.

Run:

* CLI doctor;
* registry init and migrations;
* fixture reproduction;
* public sample benchmark;
* hardened gate.

When Docker is unavailable, mark it `NOT_EXECUTED`.

## 13.4 Receipt

Record:

* source commit;
* source archive hash;
* wheel hash;
* lockfile hash;
* Python;
* OS;
* architecture;
* container digest;
* commands;
* exit codes;
* observed artifacts;
* expected artifacts;
* discrepancies;
* reproduction class.

Classes:

```text
INTERNAL_CLEAN_ENVIRONMENT
INTERNAL_CLEAN_CHECKOUT
INTERNAL_CONTAINER
EXTERNAL_INDEPENDENT
```

Only a genuine external person can create the final class.

## 13.5 Cross-platform CI

Run on:

* Ubuntu;
* macOS;
* Python 3.11;
* Python 3.12;
* Python 3.13 where supported.

Include:

* Level-5 tests;
* migrations;
* clean-wheel smoke;
* fixture reproduction;
* strict docs;
* package metadata;
* supply-chain checks.

## Acceptance state

```text
CAB_INTERNAL_CLEANROOM_REPRODUCTION_READY
```

---

# 14. Phase 9 — Deep Test Expansion

Create test groups for:

* unit;
* integration;
* concurrency;
* migrations;
* fault injection;
* security;
* malicious submissions;
* web application;
* evidence lineage;
* reproduction;
* performance;
* capability gates.

## Coverage

Measure coverage for:

`src/causal_agent_bench/level5/`

Targets:

* overall line coverage at least 85%;
* critical modules at least 90%:

  * registry;
  * execution;
  * evaluator;
  * review;
  * evidence.

Do not add meaningless tests solely to increase coverage.

Document untested defensive paths.

## Mutation testing

Run focused mutation testing where practical for:

* C10;
* scheduler states;
* artifact integrity;
* evidence transitions;
* certificate verification;
* evaluator policy.

Record surviving critical mutants and repair them.

## Static quality

Run:

* Ruff;
* mypy;
* Codespell;
* structured-data validation;
* package metadata validation;
* shell lint where available;
* Dockerfile lint where available;
* dead-code audit;
* dependency-cycle audit.

Optional unavailable tools must be marked honestly.

## Performance budgets

Add stable benchmark checks for:

* registry inserts and queries;
* queue lease operations;
* 1,000-unit scheduling;
* concurrent CAS writes;
* evidence lineage;
* review dashboard queries;
* migrations.

Avoid fragile wall-clock assertions.

## Acceptance state

```text
CAB_LEVEL5_TEST_DEPTH_HARDENED
```

---

# 15. Phase 10 — Strict Documentation

Run:

```bash
mkdocs build --strict
```

Required:

* zero warnings;
* zero broken internal links;
* complete navigation.

Expand the documentation into operational manuals.

## Required manuals

### Architecture

* bounded contexts;
* data flow;
* trust boundaries;
* deployment boundaries;
* public/private split;
* failure model;
* state diagrams.

### Registry and migrations

* schema;
* upgrade;
* backup;
* restore;
* corruption recovery;
* compatibility.

### Execution

* queues;
* dependencies;
* leases;
* heartbeats;
* retries;
* pause and resume;
* cancellation;
* Kaggle export/import;
* diagnosis.

### Reliability

For every fault:

* injection;
* invariant;
* result;
* recovery;
* residual risk.

### Human review

* onboarding;
* identity assumptions;
* consent;
* qualification;
* assignment;
* review;
* adjudication;
* amendments;
* privacy;
* C10;
* backup.

### Evaluator

* threat model;
* setup;
* keys;
* image policy;
* sandbox policy;
* broker;
* incidents;
* receipts;
* revocation.

### Evidence and claims

* graph;
* transitions;
* certificates;
* transparency;
* claims;
* corrections;
* paper assets.

### Reproduction

* clean venv;
* clean checkout;
* container;
* discrepancy handling;
* external attestation.

### Governance

* release;
* contributions;
* contamination;
* retirement;
* corrections;
* appeals;
* security disclosure.

## Tutorials

Provide public-safe tutorials for:

1. benchmark authoring;
2. registry migration;
3. concurrent fixture run;
4. interruption and resume;
5. reliability campaign;
6. fixture review;
7. evaluator fixture;
8. evidence tracing;
9. clean-checkout reproduction.

Use reviewable text-based diagrams.

## Acceptance state

```text
CAB_LEVEL5_DOCUMENTATION_STRICT_READY
```

---

# 16. Phase 11 — Red-Team Hardening

Use honest outcome states:

```text
PREVENTED
DETECTED
CONTAINED
MANUAL_REVIEW
NOT_MITIGATED
NOT_EXECUTED
ACCEPTED_RISK
```

A critical `NOT_MITIGATED` issue is a release blocker.

Implement safe fixture attacks for:

* archive traversal;
* symlink escape;
* environment scraping;
* output flooding;
* prompt echo;
* encoded exfiltration;
* duplicate-result injection;
* artifact substitution;
* certificate tampering;
* evidence-graph tampering;
* plugin gate override;
* session forgery;
* CSRF;
* SQL injection attempts;
* malicious benchmark schemas;
* stale-lease takeover;
* retry amplification;
* quota bypass;
* abstention abuse;
* scorer failure;
* score-oracle requests;
* correction-history abuse.

Manual-policy cases must include:

* review checklist;
* evidence packet;
* decision state;
* named residual risk.

They must not count as automatically mitigated.

## Acceptance state

```text
CAB_LEVEL5_REDTEAM_HARDENED
```

No unresolved critical blocker may remain.

---

# 17. Phase 12 — Unified Hardened Foundation Gate

Add:

```bash
cab level5 hardening-check
```

The gate must require:

* real registry migrations;
* concurrent scheduler;
* operational backend contracts;
* actual fault injection;
* durable review application;
* hardened evaluator pilot contract;
* persistent evidence graph;
* certificate revocation and transparency;
* benchmark and plugin hardening;
* clean-room internal reproduction;
* Level-5 coverage gate;
* strict documentation;
* red-team hardening;
* zero protected payloads;
* zero critical unresolved issues;
* full provider-free suite;
* packaging and release checks.

Correct output:

```text
CAB_LEVEL5_HARDENED_FOUNDATION_READY
HUMAN_VALIDATION_REQUIRED
LIVE_EVIDENCE_REQUIRED
EXTERNAL_REPLICATION_REQUIRED
PROTECTED_EVALUATOR_PILOT_REQUIRED
COMMUNITY_PILOT_REQUIRED
```

Do not report full Level 5.

---

# 18. Mandatory End-to-End Demonstrations

## Demo A — Concurrent execution

* compile 1,000 fixture units;
* run four workers;
* include dependencies;
* inject deterministic failures;
* pause and resume;
* cancel selected units;
* recover stale leases;
* verify deterministic hash;
* verify zero duplicate committed results.

## Demo B — Crash consistency

Crash the coordinator at:

* after lease;
* after artifact write;
* before registry commit;
* after artifact registration;
* before terminal scheduler state.

Restart and verify consistency.

## Demo C — Review pilot fixture

Through the actual service:

* create fixture users;
* qualify;
* assign two reviewers;
* submit fixture judgments;
* create disagreement;
* adjudicate;
* amend;
* export;
* verify fixture isolation;
* prove genuine C10 remains blocked.

## Demo D — Evaluator fixture

* validate a benign submission;
* execute malicious fixtures;
* verify sandbox controls;
* issue a development-signed receipt;
* rotate the development test key;
* revoke the receipt;
* verify revocation.

## Demo E — Evidence lineage

* create persistent graph;
* issue certificate;
* trace lineage;
* attempt illegal transition;
* tamper;
* revoke;
* correct a result;
* export public graph;
* verify transparency chain.

## Demo F — Clean-room reproduction

* clean source;
* wheel build;
* clean venv;
* fixture reproduction;
* hash comparison;
* container reproduction when available;
* discrepancy report.

---

# 19. Required Reports

Create:

1. `CAB_LEVEL5_HARDENING_BUILD_REPORT.md`
2. `cab_level5_hardening_handoff.md`
3. `reports/level5_hardening/CAB_LEVEL5_HARDENING_BASELINE.md`
4. `reports/level5_hardening/CAB_LEVEL5_HARDENING_STATE.json`
5. `reports/level5_hardening/CAB_LEVEL5_HARDENING_LEDGER.md`
6. `reports/level5_hardening/CAB_LEVEL5_HARDENING_DECISIONS.md`
7. `reports/level5_hardening/REGISTRY_MIGRATION_REPORT.md`
8. `reports/level5_hardening/SCHEDULER_STRESS_REPORT.json`
9. `reports/level5_hardening/SCHEDULER_STRESS_REPORT.md`
10. `reports/level5_hardening/REAL_FAULT_INJECTION_REPORT.json`
11. `reports/level5_hardening/REAL_FAULT_INJECTION_REPORT.md`
12. `reports/level5_hardening/HUMAN_REVIEW_PILOT_FIXTURE_REPORT.md`
13. `reports/level5_hardening/EVALUATOR_HARDENING_REPORT.md`
14. `reports/level5_hardening/EVALUATOR_MALICIOUS_FIXTURE_REPORT.json`
15. `reports/level5_hardening/EVIDENCE_PERSISTENCE_AND_CERTIFICATION_REPORT.md`
16. `reports/level5_hardening/BENCHMARK_FACTORY_PLUGIN_HARDENING_REPORT.md`
17. `reports/level5_hardening/CLEANROOM_REPRODUCTION_REPORT.json`
18. `reports/level5_hardening/CLEANROOM_REPRODUCTION_REPORT.md`
19. `reports/level5_hardening/LEVEL5_COVERAGE_REPORT.md`
20. `reports/level5_hardening/STRICT_DOCS_REPORT.md`
21. `reports/level5_hardening/REDTEAM_HARDENING_REPORT.json`
22. `reports/level5_hardening/REDTEAM_HARDENING_REPORT.md`
23. `reports/level5_hardening/CAB_LEVEL5_HARDENING_VALIDATION_LEDGER.md`
24. `reports/level5_hardening/CAB_LEVEL5_HARDENING_GITHUB_PUBLISH.md`

Do not commit huge raw logs. Commit compact summaries and hashes.

---

# 20. Validation Order

## Focused tests

Run narrow tests after each subsystem.

## Hardening integration suite

Create a dedicated marker or test selection.

## Static checks

* Ruff;
* mypy;
* Codespell;
* structured data;
* `git diff --check`;
* package metadata.

## Security checks

* secret scan;
* protected-payload scan;
* unsafe archive tests;
* malicious fixtures;
* container policy;
* key-policy checks;
* public/private export.

## Documentation

```bash
mkdocs build --strict
```

## Packaging

* wheel;
* source distribution;
* clean wheel installation;
* CLI smoke;
* clean source reproduction.

## Full provider-free suite

```bash
python3 -m pytest -q -n4 -m 'not provider and not model and not local_run'
```

Use `-n2` only if memory pressure is documented.

## Release checks

Regenerate release inventory only after source stabilises.

## Hardened gate

```bash
cab level5 hardening-check
```

---

# 21. Acceptance Criteria

The task is complete only when:

## Registry

* real v1→v2→v3 migrations exist;
* backups and recovery work;
* migration checksums are enforced;
* queue, review, evidence, and evaluator records persist.

## Execution

* true concurrent scheduling works;
* priorities and dependencies work;
* leases and heartbeats work;
* timeouts and cancellations work;
* retry and backoff work;
* quotas work;
* local subprocess backend works;
* Kaggle export/import works offline;
* 1,000-unit stress test is deterministic.

## Reliability

* faults are physically injected;
* invariants are concretely checked;
* declarative auto-pass is removed;
* unresolved risks are classified honestly.

## Review

* usable UI exists;
* persistence exists;
* sessions and roles exist;
* qualification, assignment, adjudication, and amendments work;
* privacy and audit work;
* C10 remains canonical.

## Evaluator

* production signer interface exists;
* development key is fixture-restricted;
* rotation and revocation work;
* protected mode requires hardened controls;
* broker contract exists;
* malicious fixtures execute where possible;
* unavailable cases are not falsely passed.

## Evidence

* graph persists;
* transitions are atomic;
* certificates persist;
* revocation works;
* transparency works;
* claims use durable evidence;
* corrections persist.

## Reproduction

* clean venv works;
* clean checkout works;
* container works when available;
* hashes are compared;
* receipt class is honest.

## Quality

* meaningful Level-5 coverage threshold passes;
* critical modules receive deep tests;
* strict documentation has zero warnings;
* no full-suite regression occurs.

## Security

* zero protected payloads are committed;
* zero production secrets are committed;
* no unresolved critical red-team issue remains.

## Publication

* coherent commits;
* direct push to `main`;
* no force push;
* local SHA equals remote SHA;
* CI is observed honestly.

---

# 22. Git Commit and Push

Before staging:

```bash
git status --short
git diff --stat
git diff
git diff --check
```

Preserve all pre-existing user-owned paths.

Stage explicit task-owned paths.

Recommended commits:

```text
Harden CAB registry scheduler and reliability
Harden CAB review evaluator and evidence systems
Complete CAB Level-5 production-readiness pass
```

Use fewer commits when appropriate.

Push directly:

```bash
git push origin main
```

Never force-push.

Verify:

```bash
LOCAL_HEAD="$(git rev-parse HEAD)"
REMOTE_HEAD="$(git ls-remote origin refs/heads/main | awk '{print $1}')"
test "$LOCAL_HEAD" = "$REMOTE_HEAD"
```

Observe remote workflows with a bounded wait.

Fix deterministic failures.

Do not claim CI is green while required checks remain queued or running.

---

# 23. Final Build Report

`CAB_LEVEL5_HARDENING_BUILD_REPORT.md` must include:

* executive summary;
* before-and-after maturity;
* registry schema and migrations;
* scheduler architecture and stress measurements;
* actual fault injections and recovery outcomes;
* review UI, persistence, and security;
* evaluator controls and residual risks;
* evidence persistence, certificates, and transparency;
* clean-room reproduction;
* test counts and coverage;
* documentation status;
* scientific evidence counters;
* remaining genuine Level-5 blockers;
* commits, SHAs, push, and CI;
* exact next action.

The exact next action after successful hardening is:

> Recruit and onboard genuine qualified Compact-20 reviewers using the hardened human-review operating system.

---

# 24. Final Response Format

## Final State

Use one exact status:

* `CAB_LEVEL5_HARDENED_FOUNDATION_READY`
* `PARTIAL_SUCCESS_HARDENING_REMAINS`
* `LOCAL_HARDENING_COMPLETE_PUSH_BLOCKED`
* `HARDENING_BLOCKED_BY_REPOSITORY_INCONSISTENCY`

## Weak Links Repaired

List each repaired subsystem.

## Demonstrations

Report measured fixture demonstrations.

## Validation

Report exact counts, timings, coverage, and failures.

## Residual Risks

Do not hide them.

## Scientific Evidence

Report exact genuine counts.

## GitHub Publication

Report commits, local SHA, remote SHA, and CI state.

## Exact Next Action

Give one concrete next action.

---

# 25. Final Directive

Do not add another superficial layer.

Deepen the existing CAB Level-5 foundation until its core systems are operationally credible.

The scheduler must actually schedule concurrently.

The reliability laboratory must actually inject faults.

The review system must be usable.

The evaluator must enforce hardened contracts and distinguish executed tests from unexecuted tests.

The evidence graph must persist.

Migrations must be real.

Reproduction must occur in clean environments.

Documentation must pass strict mode.

Tests must become deep enough to defend the new code.

Preserve every scientific evidence boundary.

Build the strongest truthful foundation possible, publish it safely to `main`, and leave CAB genuinely ready for human validation and live research execution.
