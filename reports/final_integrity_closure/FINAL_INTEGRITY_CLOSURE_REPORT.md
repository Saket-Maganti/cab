# CAB final integrity closure report

## 1. Executive result

```text
CAB_FINAL_INTEGRITY_CLOSURE_COMPLETE
```

The independently reproduced Stage-1 post-commitment mutation exploit is closed,
every adjacent defect of its class across the reviewer workflow is closed, and
committed review evidence is now immutable and cryptographically revalidated
before every downstream use.

```text
CAB_STAGE1_IMMUTABLE_SNAPSHOT_VALID
CAB_STAGE1_POST_COMMIT_MUTATION_EXPLOIT_CLOSED
CAB_ALL_REVIEW_RECEIPT_CHAINS_REVALIDATED
CAB_STAGE2_UNLOCK_BOUND_TO_COMMITTED_STAGE1_BYTES
CAB_STAGE2_ISSUANCE_BOUND_TO_IMMUTABLE_STAGE1
CAB_ADJUDICATION_INPUTS_IMMUTABLE_AND_BOUND
CAB_C10_INPUT_GRAPH_IMMUTABLE_AND_COMPLETE
CAB_SLICE_LOCK_INPUT_GRAPH_IMMUTABLE_AND_COMPLETE
CAB_EXECUTION_AUTHORIZATION_FAILS_CLOSED
CAB_SCIENTIFIC_KERNEL_V2_PRESERVED
CAB_PRIVATE_QUALIFICATION_V4_PRESERVED
CAB_STAGE2_PRIVATE_AND_UNEXPOSED
CAB_FREEZE_AND_RELEASE_PROVENANCE_REFRESHED
CAB_REPOSITORY_CLEAN
CAB_PUSHED_TO_ORIGIN_MAIN
CAB_READY_FOR_GENUINE_REVIEWER_DISTRIBUTION
HUMAN_VALIDATION_REQUIRED
C10_PENDING_GENUINE_REVIEW
MODEL_EXECUTION_BLOCKED
GENUINE_HUMAN_JUDGMENTS=0
GENUINE_ADJUDICATIONS=0
GENUINE_MODEL_TRAJECTORIES=0
PAPER_ELIGIBLE_EMPIRICAL_ASSETS=0
SUPPORTED_EMPIRICAL_CLAIMS=0
CAB_LEVEL5_COMPLETE=false
CAB_LEVEL6_COMPLETE=false
```

This is engineering completeness and integrity closure for reviewer onboarding
and Stage-1 package distribution. It is **not** empirical completeness, not
C10 completeness, not model-execution readiness, not submission readiness, and
not paper readiness.

## 2. Repository identity

| field | value |
| --- | --- |
| starting commit | `131cd10abe519a7174171bb47e90347326862ca4` |
| repair source commit (A) | `82315dccd4096d3522323de583de9f9bd3f0d1b7` |
| freeze and provenance commit (B) | `f63464b97148c3e87cdcf09bd0a6b325e193dff0` |
| branch | `main` |
| remote | `https://github.com/Saket-Maganti/cab.git` |
| push state | A and B pushed; the closure-evidence commit follows and is pushed with them |
| worktree state | clean |

Commit A is an ancestor of B, and the starting commit is an ancestor of both.

## 3. Files changed

**Integrity primitives**

- `src/causal_agent_bench/review_ready_v2/commitment_integrity.py` *(new)* —
  canonical digests, write-once snapshots, atomic writes, symlink and
  private-mode defences.

**Workflow integration**

- `src/causal_agent_bench/review_ready_v2/workflow.py` — Stage-1 snapshot
  creation, `verify_committed_stage1_snapshot`, `verify_committed_stage2_snapshot`,
  `review_input_graph`, one-way write guards, and the rewiring of every
  downstream gate onto committed evidence.
- `src/causal_agent_bench/review_ready_v2/stage2_issuance.py` — issuance binds
  the Stage-1 snapshot manifest, the reviewer's frozen judgement digest, and
  their frozen receipt hash.
- `src/causal_agent_bench/review_ready_v2/fixture_e2e.py` — the resumable
  `FixtureWorkflow` driver the hostile matrix and the audit both drive.
- `src/causal_agent_bench/review_ready_v2/cli.py` — `verify-committed-evidence`,
  item-coverage binding at commitment, and updated coordinator guidance.
- `src/causal_agent_bench/review_ready_v2/freeze.py` — freezes the new module and
  records the active and retired commitment, snapshot and workflow schemas.
- `src/causal_agent_bench/safety/pre_run_scientific_hardening.py` — accepts the
  new canonical state string.

**Hostile tests**

- `src/causal_agent_bench/review_ready_v2/hostile_integrity.py` *(new)* — the
  66-case mutation matrix and its gate runner.
- `tests/test_final_integrity_closure.py` *(new)* — the hostile suite and the
  positive, schema-policy, one-way-transition and canonicalisation contracts.
- `tests/test_review_workflow_integrity.py`,
  `tests/test_reviewer_distribution_patch.py` — updated to the active schema and
  to C10's fail-closed reporting contract.

**Documentation**

- `docs/reviewer_ready_v2/IMMUTABLE_REVIEW_CHAIN.md` *(new)*
- `docs/reviewer_ready_v2/COORDINATOR_RUNBOOK.md` *(new)*
- `docs/reviewer_ready_v2/RECOVERY_AND_CORRECTION_POLICY.md` *(new)*
- `CHANGELOG.md`

**Freeze and release**

- `reports/reviewer_ready_v2/SCIENTIFIC_FREEZE_V2.json`,
  `GENERATOR_PROVENANCE.json`, `REVIEWER_DISTRIBUTION_SCHEMAS.json`
- `release/release_manifest.{json,md}`

**Status and audit**

- `CURRENT_PROJECT_STATE.md`
- `scripts/audit_final_review_integrity.py` *(new)*
- `scripts/build_final_integrity_closure_reports.py` *(new)*
- `reports/final_integrity_closure/` *(new)*

**Removed**

- `promptpacks/CAB_FINAL_REVIEW_WORKFLOW_INTEGRITY_REPAIR_PROMPT.md` — an
  untracked, superseded prompt targeting an older commit. Deleted, not executed.

## 4. The confirmed exploit

**Before the repair**, against `131cd10`:

```text
Stage-1 commitment unchanged:                 true
committed payload hashes unchanged:           true
current Stage-1 receipt hashes changed:       true
altered parsed content visible downstream:    true
non-fixture mechanics checks still passing:   true   ← C10_MECHANICS_PASS
```

**After the repair**, the identical attack:

```text
Stage-1 commitment unchanged:                 true
committed payload hashes unchanged:           true
current Stage-1 receipt hashes changed:       true
altered parsed content visible downstream:    false
non-fixture mechanics checks still passing:   false  ← C10_MECHANICS_FAIL
```

**First gate rejecting the attack:** `verify_committed_stage1_snapshot`, on the
check `stage1_judgement_hashes_match_commitment` when the snapshot is edited, or
`stage1_live_receipts_not_conflicting` when the live receipt is edited.

**All downstream gates protected:** Stage-2 unlock, Stage-2 issuance, Stage-2
ingestion, pairing, both disagreement queues, agreement, both adjudicator
packages, both adjudications, the final adjudicated records, C10, the exclusion
register, the reviewed-slice lock and the execution authorization all route
through the same verifier and cannot be reached past a refusal.

No private content appears in this report.

## 5. Adjacent-chain audit

| artifact | commitment point | immutable digest | downstream verifier | hostile attacks | result |
| --- | --- | --- | --- | --- | --- |
| assignment registry | `create_assignment` (write-once) | `canonical_assignment_registry_digest` | Stage-1 verifier, C10, lock | pseudonym rebind, post-commit change | rejected |
| reviewer declarations | ingestion | `canonical_declaration_digest` | Stage-1 verifier | hash change, content change, pseudonym rebind | rejected |
| qualification receipts | scoring | `canonical_qualification_digest` | Stage-1 verifier | hash change, content change | rejected |
| Stage-1 submissions | `commit_stage1` | payload + sealed-file + canonical judgement | every downstream gate | 25 mutations | rejected |
| Stage-1 commitment | `commit_stage1` | `receipt_content_sha256`, schema-gated | Stage-1 verifier | packet mismatch, stale commitment, retired schema | rejected |
| committed Stage-1 snapshot | `commit_stage1` | sealed manifest | Stage-1 verifier | file replace, manifest replace, delete, symlink, world-readable | rejected |
| Stage-2 unlock | unlock | verified Stage-1 graph | issuance, ingestion | changed Stage-1 evidence | rejected |
| Stage-2 issuance | issuance | receipt hash + Stage-1 snapshot bindings | ingestion, Stage-2 verifier, C10, lock | swap, replay, cross-workspace copy, namespace and archive swap | rejected |
| Stage-2 submissions | second ingestion | payload + sealed-file + canonical judgement | queues, agreement, final records, C10, lock | 12 mutations incl. retained payload hash | rejected |
| committed Stage-2 snapshot | second ingestion | sealed manifest | Stage-2 verifier | third submission after commitment | rejected |
| disagreement queues | generation | `canonical_queue_digest` | adjudication, final records, C10, lock | disputed-set change, post-adjudication regeneration | rejected |
| adjudicator packages | issuance | package hash + binding | adjudication, C10 | stale package | rejected |
| adjudications | ingestion | `canonical_adjudication_digest` | final records, C10, lock | 12 mutations incl. rationale and evidence-reference edits | rejected |
| final adjudicated records | build | content hash + recomputation | C10, exclusion register, lock, authorization | replacement, included-pair change, exclusion-reason change | rejected |
| agreement report | computation | recomputed from committed judgements in C10 | C10 | stale flattering number | rejected |
| C10 report | evaluation | `sha256_json` bound by the lock | lock, authorization | cross-workspace copy, post-lock change | rejected |
| exclusion register | build | content hash | lock, authorization | replacement | rejected |
| reviewed-slice lock | lock | full immutable digest set | authorization | replacement, freeze/commit/packet mismatch | rejected |
| execution authorization | authorization | whole-chain revalidation | — | replay under a changed chain | rejected |
| scientific freeze | `build-reports` | `freeze_sha256` + generator provenance | every gate that binds it | mismatch | rejected |

Totals: **66 attacks attempted, 66 rejected, 0 falsely accepted.** See
[`HOSTILE_INTEGRITY_AUDIT.md`](HOSTILE_INTEGRITY_AUDIT.md).

## 6. Preservation report

| surface | before | after |
| --- | --- | --- |
| active pair-content digest (20 pairs) | `01a2ed72c58d052cc36e64907b3ac5f2b19de5f314ad63915c4d975c51d6973d` | unchanged |
| public packet commitment | `03653ff304126cd460fc8ee51a371e6741f4b2fb294b44632145aa687f48745b` | unchanged |
| Stage-1 Reviewer A archive | `3fcd2192c68cc356b2a1506a2ca32f191caf00ccf5dc7769a87bcd47db618113` | unchanged |
| Stage-1 Reviewer B archive | `0185fcfbe89402e6284999fa6ed472fb0e1f90d28335a8ccfc6094e158a2d6cf` | unchanged |
| qualification package REVIEWER_A | `5a844155f7c67c1fbc77359b488270ffc1bc86730037624ff39b67e705856f55` | unchanged |
| qualification package REVIEWER_B | `98ba00fdf79f3c20c02cc04d7142d9dacf84d5a1a774c695ae531c76b3328a0f` | unchanged |
| qualification commitment | `03c4ab20a9b2a9e4fc23ec351528d97b7ff294f31aaa417ef4bd8a7371830e91` | unchanged |
| encrypted qualification vault | `793486ffc6b08a30f03d3e33812939712fec69bcefa32adef17153eaa3bb9005` | unchanged |
| Stage-2 encrypted vault | `d5f83c3788552588ed758989ec9bcd6b55952d67c1d0b2285a4a7e06173358c9` | unchanged |
| seed commitment | `38fec0ccea7f439c2858e046205551081a953a0acf9f98126b4f22c8cf239e85` | unchanged |
| intervention-family, domain and difficulty composition | — | unchanged |
| **scientific freeze** | `6a7b15b21d4a899e7cb95bf110625c5f72fc33899da20dfa93f9ce9c6b023fad` | `3789cc2b78e51dac886feaac945acc810aae3d6f8cbb03d40700d0bf2f301675` |

The freeze hash is the only listed value that changed, and changing it is the
point of the refresh: it now binds `commitment_integrity.py`, the modified
workflow sources, and the active and retired schema versions. Every scientific
task-content surface is byte-identical.
See [`SCIENTIFIC_KERNEL_PRESERVATION_FINAL.json`](SCIENTIFIC_KERNEL_PRESERVATION_FINAL.json).

## 7. Validation

See [`FULL_VALIDATION_REPORT.md`](FULL_VALIDATION_REPORT.md) and
[`FRESH_CLONE_VERIFICATION.md`](FRESH_CLONE_VERIFICATION.md).

- full provider-free suite: **1505 passed, 1 skipped, 0 failed**; the single skip
  is an OpenAI integration test that requires `OPENAI_API_KEY`, and no provider
  call was made anywhere in this pass;
- `tests/test_final_integrity_closure.py`: **102 passed**;
- Ruff: all checks passed. mypy: no issues in 298 source files. Codespell: pass.
- security check, config audit, repo-consistency audit, claim ledger, evidence
  safety, reviewer proofing, freeze verification and generator provenance: all
  pass;
- packaging: wheel and sdist build, `twine check` PASSED, and two clean builds
  produce byte-identical archive *contents* (raw archive hashes differ only
  because zip and tar embed modification times);
- private-material tracking scan: **empty**;
- fresh clone (`--single-branch`, no untracked files copied): every check passes,
  including freeze verification, provenance, the fixture end-to-end, the full
  hostile audit, retired-schema rejection, status-document contents and release
  hashes.

## 8. Current scientific state

```text
genuine human judgments: 0
genuine adjudications: 0
genuine model trajectories: 0
paper-eligible empirical assets: 0
supported empirical claims: 0
C10: pending genuine review
model execution: blocked
```

## 9. Exact next action

> Recruit two independent reviewers and one separate adjudicator; create
> production assignments and declarations; run private qualification V4;
> distribute only the role-specific frozen Stage-1 packages; commit immutable
> Stage-1 evidence; unlock Stage 2; adjudicate; run C10; lock the reviewed slice;
> and only then begin the one-task live smoke.
