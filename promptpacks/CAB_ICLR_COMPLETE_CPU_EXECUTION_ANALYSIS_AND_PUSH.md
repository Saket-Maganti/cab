# CAB ICLR Complete CPU Execution, Analysis, Reporting, and GitHub Push

## Intended Use

Run this prompt in Codex from:

`/Users/saketmaganti/Projects/causal-agent-bench`

Repository:

`Saket-Maganti/cab`

Branch:

`main`

Recommended effort:

> **High**

Use **XHigh** only if failures require nontrivial debugging across multiple CPU lanes.

This prompt is for the complete CPU-only execution phase that is legally allowed by the current evidence state.

It must:

1. execute every currently permitted CPU-only validation, audit, fixture, analysis, paper, and release lane;
2. measure actual runtimes, resource use, outputs, and failures;
3. analyse the results;
4. create a comprehensive CPU execution report and machine-readable ledger;
5. repair CPU-side defects that are clearly caused by the current repository;
6. rerun affected checks until stable;
7. commit the intentional outputs;
8. push directly to `origin/main`;
9. verify local and remote SHA equality.

This prompt must not run any real model, GPU, provider, or human-evidence stage.

---

# 1. Current Scientific State

The expected unified state before this run is:

`HUMAN_VALIDATION_REQUIRED`

The current pre-execution build is complete.

Expected genuine evidence counts remain:

- human review rows: 0;
- real model trajectories: 0;
- audited real runs: 0;
- paper-eligible empirical assets: 0;
- supported empirical claims: 0.

This CPU run must preserve those counts unless genuine user-supplied evidence already exists.

Do not fabricate or infer missing evidence.

---

# 2. Hard Boundaries

Do not:

- run Kaggle live inference;
- enable notebook live mode;
- load or download large language-model weights;
- call provider APIs;
- run local model inference;
- generate fake human-review rows;
- auto-fill adjudication;
- pass C10 with fixtures;
- lock a scientific slice without genuine C10;
- execute Compact-20 model runs;
- execute Scale-100 model runs;
- execute RAAC model ablations;
- execute naturalistic-transfer model runs;
- execute Main expansion;
- create fake statistical results from fixture data;
- promote fixture outputs into paper evidence;
- expose private task text, answers, or evaluator metadata;
- commit ignored private payloads;
- rewrite Git history;
- force-push;
- create a branch;
- create a pull request;
- push code with a known unexpected focused-test failure;
- silently stage unrelated user-owned changes.

Allowed:

- provider-free CPU tests;
- static analysis;
- schema validation;
- leakage and contamination scans;
- private-candidate structural validation without exposing payloads;
- offline notebook fixture execution;
- deterministic fixture analysis;
- M4 resource preflight;
- paper compilation with placeholders;
- release-bundle validation;
- security and protected-payload scanning;
- reproducibility audits;
- runtime and disk measurement;
- report generation;
- repair of CPU-side implementation defects;
- direct commit and push to `main`.

---

# 3. Baseline and Repository Safety

Before editing or running generated-report commands:

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

Required state:

- branch is `main`;
- remote is `Saket-Maganti/cab`;
- no unsafe divergence;
- no force-push required.

Create:

`reports/CAB_CPU_EXECUTION_GIT_BASELINE.md`

Record:

- timestamp;
- local commit;
- remote main commit;
- divergence;
- tracked modifications;
- untracked files;
- ignored private paths;
- unrelated user-owned files that must remain unstaged.

The previously preserved untracked file:

`reports/ICLR_PROMPT1_POSTFIX_BASELINE.md`

must remain untouched and uncommitted unless the user has explicitly incorporated it later.

Do not run `git add -A` blindly.

---

# 4. Machine and Environment Inventory

Capture the execution environment.

Record:

```bash
date
sw_vers
uname -a
sysctl -n machdep.cpu.brand_string 2>/dev/null || true
sysctl -n hw.memsize 2>/dev/null || true
sysctl -n hw.logicalcpu 2>/dev/null || true
df -h .
python3 --version
python3 -m pip --version
git --version
gh --version || true
```

Capture tool versions:

```bash
python3 -m pytest --version
python3 -m ruff --version
python3 -m mypy --version
python3 -m codespell --version || true
```

Create:

- `reports/CAB_CPU_ENVIRONMENT.json`
- `reports/CAB_CPU_ENVIRONMENT.md`

Do not include usernames, tokens, private paths outside the repository, or secrets.

---

# 5. Live CPU Execution Ledger

Create immediately:

`reports/CAB_CPU_EXECUTION_LEDGER.jsonl`

Each command entry must contain:

- run ID;
- command;
- working directory;
- start timestamp;
- end timestamp;
- elapsed seconds;
- exit code;
- expected exit code;
- peak resident memory when measurable;
- disk before;
- disk after;
- generated paths;
- evidence class;
- status;
- failure summary.

Also create a readable mirror:

`reports/CAB_CPU_EXECUTION_LEDGER.md`

Update both incrementally after every major run so interruption does not lose progress.

Use a reproducible wrapper script if helpful, for example:

`scripts/run_and_record_cpu_stage.py`

Do not introduce a large orchestration framework if a small robust wrapper is sufficient.

---

# 6. CPU Run Order

Execute in this exact order.

Stop and repair unexpected failures before continuing.

Expected fail-closed states are not defects.

## CPU-00 — Unified pre-execution readiness gate

Run:

```bash
python3 scripts/check_iclr_preexecution_readiness.py
```

Expected:

- state: `HUMAN_VALIDATION_REQUIRED`;
- build complete: true;
- expected blocking exit code: 2;
- exact next allowed action: genuine human review;
- no unexpected implementation blocker.

Record the gate JSON and text outputs.

If the state is earlier than `HUMAN_VALIDATION_REQUIRED`, identify and repair the CPU-side defect.

Do not bypass human/C10 blockers.

## CPU-01 — Fast repository gate

Run the repository’s canonical fast check, preferably:

```bash
make fast-check
```

If the Make target differs, inspect the Makefile and use the canonical equivalent.

Record sub-check durations where available.

## CPU-02 — Focused scientific-safety regression

Run a serial focused suite covering at minimum:

- Prompt 1 paired metrics;
- intervention-validity profile;
- workflow states;
- pre-execution gate;
- held-out contamination;
- protected commitments;
- split registry;
- release checks;
- RAAC;
- human-review gate;
- agreement analysis;
- manipulation checks;
- private-candidate materialisation;
- Scale-100/naturalistic audits;
- resource profiles;
- analysis primitives;
- paper-asset eligibility.

Use explicit files, for example:

```bash
python3 -m pytest -q -n0   tests/test_intervention_validity_profile.py   tests/test_phase5_paired_metrics.py   tests/test_cab_phase2_phase3_gate.py   tests/test_max_ceiling_gate.py   tests/test_iclr_preexecution_gate.py   tests/test_protected_heldout_contamination.py   tests/test_cab_split_registry.py   tests/test_release_check.py   tests/test_raac.py   tests/test_cab_human_review_gate.py   tests/test_human_agreement_analysis.py   tests/test_manipulation_checks.py   tests/test_private_candidate_materialization.py   tests/test_iclr_dataset_audit.py   tests/test_iclr_resources.py   tests/test_iclr_analysis.py
```

Adapt only to actual test names in the repository.

Do not omit a named test merely because it fails.

## CPU-03 — Static analysis and formatting

Run:

```bash
python3 -m ruff check .
python3 -m mypy
python3 -m codespell . || true
git diff --check
```

If codespell is part of CI, it must ultimately pass.

Do not auto-format unrelated files.

Repair only clear task-owned or repository defects.

## CPU-04 — JSON, YAML, manifest, and schema validation

Validate all tracked:

- JSON;
- JSONL;
- YAML;
- YML;
- notebook JSON;
- canonical manifests;
- configuration files;
- public-safe manifests;
- review packet files;
- run-manifest templates.

Create a machine-readable validation report listing:

- files scanned;
- files passed;
- files failed;
- schema used;
- error location;
- fix applied.

Output:

`reports/CAB_CPU_STRUCTURED_DATA_VALIDATION.json`

## CPU-05 — Security, leakage, contamination, and release scans

Run all canonical repository scans for:

- secrets;
- private protected payloads;
- hidden answers;
- evaluator-only metadata;
- private reviewer identities;
- contaminated split eligibility;
- public/private role overlap;
- release-manifest safety;
- large files;
- ignored-private-path enforcement;
- archive/notebook protected-content leakage.

Run the canonical release check.

Confirm:

- zero tracked `private_data` payloads;
- zero protected answers in Git;
- contaminated v1 data cannot be confirmatory;
- protected v2 public manifests remain aggregate/non-reversible;
- release bundle excludes private payloads.

Create:

- `reports/CAB_CPU_SECURITY_AND_LEAKAGE_AUDIT.json`
- `reports/CAB_CPU_SECURITY_AND_LEAKAGE_AUDIT.md`

## CPU-06 — Human packet and C10 fail-closed validation

Run the genuine human-review validator against the blank packet:

```bash
python3 scripts/validate_cab_human_reviews.py   --review-dir data/human_validation/compact20_real_review
```

Expected:

- genuine review count remains zero;
- validation blocks;
- C10 blocks;
- slice locking blocks;
- exact missing requirements are listed;
- no fixture or blank row passes.

Also run packet-generation consistency checks.

Do not generate review judgments.

Create:

`reports/CAB_CPU_HUMAN_GATE_STATUS.md`

## CPU-07 — Private candidate structural validation

Run the structural validator for:

- Scale-100 v2;
- naturalistic transfer v2;
- held-out challenge v2;
- any conditional Main candidate.

Confirm:

- aggregate counts;
- exact duplicates;
- normalised duplicates;
- lexical near-duplicates;
- role overlap;
- answer-contract canonicality;
- manipulation-check coverage;
- provenance;
- licence;
- privacy;
- PII;
- prompt injection;
- hidden-field safety;
- public-fragment safety;
- private-path exclusion.

Do not expose private payload contents in reports.

Run:

```bash
python3 scripts/validate_iclr_private_candidates.py
```

or the canonical equivalent.

Create:

- `reports/CAB_CPU_PRIVATE_CANDIDATE_AUDIT.json`
- `reports/CAB_CPU_PRIVATE_CANDIDATE_AUDIT.md`

## CPU-08 — M4 resource preflight

Run:

```bash
PYTHONPATH=src python3 scripts/cab_resource_preflight.py
```

Measure:

- available disk;
- repository size;
- cache size where safely inspectable;
- recommended worker mode;
- estimated intermediate size;
- bootstrap shard plan;
- compression plan;
- cleanup suggestions.

Do not delete raw evidence or caches automatically.

Create:

- `reports/CAB_CPU_M4_RESOURCE_PREFLIGHT.json`
- `reports/CAB_CPU_M4_RESOURCE_PREFLIGHT.md`

Every projected value must remain labelled:

`ESTIMATE_NOT_MEASURED`

Actual command timings from this CPU run may be labelled:

`MEASURED_ON_LOCAL_M4`

## CPU-09 — Offline Kaggle notebook fixture validation

Run:

```bash
python3 scripts/validate_kaggle_notebooks.py --execute-offline
```

Expected:

- all nine notebooks parse;
- all nine validate;
- 72 fixture receipts or the current canonical expected count;
- live execution false;
- no model loaded;
- no provider calls;
- deterministic sharding;
- checkpoint/resume;
- merge;
- corruption detection;
- archive/export safety.

Create:

`reports/CAB_CPU_NOTEBOOK_FIXTURE_VALIDATION.md`

Do not enable GPUs or scientific execution.

## CPU-10 — Deterministic fixture analysis

Run only fixture-safe analysis tests and self-checks.

Include:

- paired metric fixtures;
- RAAC trace fixtures;
- 1,000-replicate fixture bootstrap if canonical and lightweight;
- resumable bootstrap-shard merge;
- rank/tie/zero-denominator edge cases;
- scorer-sensitivity fixture;
- naturalistic predictive-validity function tests using synthetic fixtures;
- paper-asset refusal on noneligible evidence.

All outputs must remain:

`FIXTURE_ONLY`

Do not present numerical fixture outcomes as research findings.

Create:

`reports/CAB_CPU_FIXTURE_ANALYSIS_REPORT.md`

## CPU-11 — Paper build and claim-safety validation

Compile the paper using the repository’s canonical command.

Confirm:

- successful compilation;
- page count;
- seven or current expected empirical placeholders remain visible;
- no fabricated table;
- no unsupported abstract;
- RAAC section exists;
- references resolve;
- claim ledger blocks unsupported wording;
- paper assets refuse noneligible data.

Create:

- `reports/CAB_CPU_PAPER_BUILD.json`
- `reports/CAB_CPU_PAPER_BUILD.md`

Do not remove empirical placeholders.

## CPU-12 — Full provider-free test suite

Run the complete suite:

```bash
python3 -m pytest -q -n4 -m 'not provider and not model and not local_run'
```

If four workers cause memory instability, retry with:

```bash
python3 -m pytest -q -n2 -m 'not provider and not model and not local_run'
```

Use serial mode only if necessary.

Do not hide the original failure.

Record:

- collection count;
- passed;
- skipped;
- deselected;
- failed;
- elapsed time;
- worker count;
- retry reason.

Target:

- zero unexpected failures.

## CPU-13 — Release and reproducibility gate

Run the canonical release, security, paper, artifact, and reproducibility checks after all generated files are stable.

Refresh deterministic release hashes only after source and report files have stopped changing.

Then rerun exact release tests.

Confirm:

- bundle hash matches;
- no stale source hash;
- no private payload;
- no secret;
- no unsupported result;
- no dirty generated source;
- reproduction commands are valid.

## CPU-14 — Final readiness rerun

Rerun:

```bash
python3 scripts/check_iclr_preexecution_readiness.py
```

Expected final state:

`HUMAN_VALIDATION_REQUIRED`

Expected build:

`build_complete=true`

Expected scientific evidence counts:

all zero.

Compare this final output with CPU-00.

Any state regression must be explained and repaired.

---

# 7. Deferred CPU Runs

Some CPU-only stages are not legally executable yet because their inputs do not exist.

Do not fabricate those inputs.

Explicitly mark these as deferred:

## Deferred after genuine human review and C10

- slice lock;
- final frozen-run manifest generation;
- post-C10 CPU preflight;
- exact Compact-20 trajectory-count plan.

## Deferred after Compact-20 GPU execution

- shard merge;
- rescoring;
- scorer-sanity packet creation;
- paired preliminary analysis;
- Compact-20 bootstrap;
- audit promotion.

## Deferred after Scale-100 and naturalistic GPU execution

- final 10,000-replicate bootstrap;
- rank uncertainty from real outcomes;
- mixed-effects analysis;
- RAAC effect and overhead analysis;
- naturalistic predictive-validity analysis;
- scorer-error sensitivity on real data;
- claim promotion;
- final empirical figures and tables.

## Deferred final release

- paper-eligible empirical export;
- final submission bundle containing audited results.

Create exact future commands and expected prerequisites for each deferred stage.

Output:

`reports/CAB_CPU_DEFERRED_RUNS.md`

The report must make clear:

> All currently legal CPU runs were completed. Evidence-dependent CPU runs remain blocked because genuine human or GPU outputs do not yet exist.

---

# 8. Performance Analysis

Analyse the measured CPU results.

Produce:

## 8.1 Runtime table

For every CPU stage report:

- measured elapsed time;
- measured peak memory where available;
- disk change;
- exit code;
- rerun count;
- final status.

## 8.2 Bottleneck analysis

Identify:

- slowest tests;
- slowest scripts;
- serial-only components;
- avoidable duplicate work;
- release-hash regeneration cost;
- notebook validation cost;
- paper-build cost;
- bootstrap cost.

## 8.3 M4 recommendations

Recommend:

- default worker count;
- low-memory fallback;
- whether `-n4` is stable;
- when to use `-n2`;
- safe bootstrap shard size;
- free-disk floor;
- cache-retention policy.

## 8.4 Future CPU forecast

Using measured values from this run and existing manifest sizes, estimate:

- Compact-20 postrun CPU time;
- Scale-100 postrun CPU time;
- naturalistic postrun CPU time;
- final 10,000-bootstrap time;
- paper-asset generation time.

Clearly separate:

- `MEASURED_ON_LOCAL_M4`;
- `PROJECTED_FROM_CURRENT_MEASUREMENTS`;
- `ESTIMATE_NOT_MEASURED`.

Do not present projected values as measurements.

---

# 9. Required Final Reports

Create:

1. `reports/CAB_CPU_EXECUTION_GIT_BASELINE.md`
2. `reports/CAB_CPU_ENVIRONMENT.json`
3. `reports/CAB_CPU_ENVIRONMENT.md`
4. `reports/CAB_CPU_EXECUTION_LEDGER.jsonl`
5. `reports/CAB_CPU_EXECUTION_LEDGER.md`
6. `reports/CAB_CPU_STRUCTURED_DATA_VALIDATION.json`
7. `reports/CAB_CPU_SECURITY_AND_LEAKAGE_AUDIT.json`
8. `reports/CAB_CPU_SECURITY_AND_LEAKAGE_AUDIT.md`
9. `reports/CAB_CPU_HUMAN_GATE_STATUS.md`
10. `reports/CAB_CPU_PRIVATE_CANDIDATE_AUDIT.json`
11. `reports/CAB_CPU_PRIVATE_CANDIDATE_AUDIT.md`
12. `reports/CAB_CPU_M4_RESOURCE_PREFLIGHT.json`
13. `reports/CAB_CPU_M4_RESOURCE_PREFLIGHT.md`
14. `reports/CAB_CPU_NOTEBOOK_FIXTURE_VALIDATION.md`
15. `reports/CAB_CPU_FIXTURE_ANALYSIS_REPORT.md`
16. `reports/CAB_CPU_PAPER_BUILD.json`
17. `reports/CAB_CPU_PAPER_BUILD.md`
18. `reports/CAB_CPU_DEFERRED_RUNS.md`
19. `CAB_ICLR_COMPLETE_CPU_EXECUTION_REPORT.md`
20. `cab_cpu_execution_handoff.md`
21. `reports/CAB_CPU_GITHUB_PUBLISH.md`

Reuse canonical generated outputs where they already exist.

Do not duplicate large data.

---

# 10. Complete CPU Execution Report

Create:

`CAB_ICLR_COMPLETE_CPU_EXECUTION_REPORT.md`

It must include:

## Executive Summary

- final status;
- CPU runs executed;
- CPU runs passed;
- expected blocked gates;
- unexpected failures repaired;
- final unified state;
- Git publication status.

## Environment

- Mac model;
- memory;
- logical CPUs;
- Python;
- tool versions;
- free disk.

## Command Ledger

A compact table of every command and outcome.

## Validation Summary

Include:

- focused tests;
- full provider-free suite;
- Ruff;
- mypy;
- codespell;
- structured-data validation;
- security;
- leakage;
- release;
- notebooks;
- paper;
- unified gate.

## Runtime Analysis

Show measured durations and bottlenecks.

## Resource Analysis

Show:

- peak memory;
- worker stability;
- disk impact;
- cache impact;
- safe future settings.

## Scientific State

Confirm:

- no model execution;
- no provider call;
- no human judgment fabricated;
- no scientific evidence created;
- no claim promoted.

## Deferred Work

List every CPU stage blocked on human or GPU evidence.

## Exact Next Action

Use:

> Have two independent qualified human reviewers complete the locked Compact-20 review packet.

Do not recommend GPU execution before that.

## Files Changed

List all committed paths.

## Git Publication

Include commit and remote verification.

---

# 11. Repair Policy

If a CPU run fails:

1. preserve the original log;
2. determine whether it is:
   - implementation defect;
   - stale generated manifest;
   - environment/tool-version mismatch;
   - expected human/evidence block;
   - external configuration issue;
3. repair only implementation or deterministic generated-state defects;
4. rerun the narrow failing command;
5. rerun the affected broader gate;
6. document the repair.

Examples:

- stale release hash → regenerate after source stabilises;
- newer Ruff/codespell issue → repair source wording/type syntax;
- missing dev dependency → add only if genuinely required by tests;
- expected human gate exit → do not suppress;
- GitHub Pages disabled → document, do not treat as code failure.

Do not weaken tests.

---

# 12. Git Staging and Commit

Before staging:

```bash
git status --short
git diff --stat
git diff
git diff --check
```

Exclude:

- ignored private data;
- raw protected task payloads;
- secrets;
- caches;
- temporary logs;
- unrelated user-owned files;
- the preserved untracked Prompt 1 baseline report.

Stage only:

- CPU execution reports;
- deterministic ledgers;
- necessary CPU-side repairs;
- refreshed canonical manifests;
- validated release metadata;
- updated handoff.

Prefer explicit paths.

Review:

```bash
git diff --cached --stat
git diff --cached
```

Commit directly on `main`.

Preferred message:

```bash
git commit -m "Run and report CAB CPU validation suite"
```

If implementation repairs are substantial, use at most two logical commits:

```bash
git commit -m "Repair CAB CPU validation defects"
git commit -m "Run and report CAB CPU validation suite"
```

Do not create trivial commits.

---

# 13. Push Directly to GitHub Main

Before push:

```bash
git fetch origin main
git rev-list --left-right --count origin/main...main
```

If remote is ahead:

```bash
git pull --rebase --autostash origin main
```

Resolve only safe conflicts.

Rerun affected checks after rebase.

Push:

```bash
git push origin main
```

Never use force.

Verify:

```bash
LOCAL_HEAD="$(git rev-parse HEAD)"
REMOTE_HEAD="$(git ls-remote origin refs/heads/main | awk '{print $1}')"

printf 'local=%s
remote=%s
' "$LOCAL_HEAD" "$REMOTE_HEAD"
test "$LOCAL_HEAD" = "$REMOTE_HEAD"
```

Create:

`reports/CAB_CPU_GITHUB_PUBLISH.md`

Include:

- repository;
- branch;
- starting commit;
- final commit;
- commit message;
- push command;
- push result;
- local SHA;
- remote SHA;
- force push: no;
- private files committed: 0;
- unrelated files preserved.

---

# 14. Remote CI Verification

After push, inspect GitHub Actions:

```bash
gh run list --commit "$(git rev-parse HEAD)" --limit 20
```

Observe:

- CI;
- Fast Check;
- Docs Check;
- Claim Safety;
- Security Audit;
- Max Ceiling;
- any newer workflows.

Use a bounded wait.

If a workflow fails:

- inspect logs;
- fix deterministic repository defects;
- rerun locally;
- commit;
- push;
- verify replacement run.

Do not alter repository settings such as GitHub Pages unless explicitly authorised.

Do not claim all CI is green unless completed workflows are actually successful.

---

# 15. Acceptance Criteria

This task is complete only when:

- every currently legal CPU-only run has executed;
- all relevant focused tests pass;
- full provider-free suite has zero unexpected failures;
- static checks pass;
- structured-data validation passes;
- leakage and security gates pass;
- blank human packet remains fail-closed;
- private candidate audits pass structurally;
- M4 preflight is recorded;
- all nine notebooks pass offline validation;
- fixture analysis remains clearly fixture-only;
- paper compiles with empirical placeholders;
- release and reproducibility gates pass;
- final unified state is `HUMAN_VALIDATION_REQUIRED`;
- all evidence counts remain honest;
- deferred CPU runs are documented;
- measured runtime analysis exists;
- final report exists;
- intended files are committed;
- push to `origin/main` succeeds;
- local HEAD equals remote main HEAD;
- private payloads are not committed;
- no force push occurs.

---

# 16. Final Response Format

## Final Status

Use one exact status:

- `CAB_CPU_EXECUTION_COMPLETE`
- `CAB_CPU_EXECUTION_COMPLETE_WITH_EXPECTED_HUMAN_BLOCK`
- `PARTIAL_SUCCESS_CPU_FAILURE_REMAINS`
- `LOCAL_CPU_COMPLETE_PUSH_BLOCKED`
- `PUSHED_TO_GITHUB_MAIN`

## CPU Runs

List every completed CPU stage.

## Validation

List exact pass/fail/skip counts and timings.

## Resource Findings

Report measured M4 performance.

## Repairs

List defects fixed during execution.

## Scientific Evidence

Confirm genuine counts.

## Deferred CPU Runs

List human-dependent and GPU-output-dependent CPU stages.

## Final Gate

Report unified state and expected exit code.

## Git Publication

Report repository, branch, SHA, push, and CI state.

## Exact Next Action

State only:

> Have two independent qualified human reviewers complete the locked Compact-20 review packet.

## Handoff

Point to:

- `CAB_ICLR_COMPLETE_CPU_EXECUTION_REPORT.md`;
- `cab_cpu_execution_handoff.md`;
- `reports/CAB_CPU_EXECUTION_LEDGER.md`;
- `reports/CAB_CPU_DEFERRED_RUNS.md`.

---

# 17. Final Directive

Execute all CPU-only work that is currently scientifically legal.

Measure it.

Analyse it.

Repair genuine CPU-side defects.

Do not fabricate inputs for blocked stages.

Do not run models.

Do not create human evidence.

Produce a complete report and handoff.

Commit only intentional public-safe outputs.

Push directly to GitHub `main`.

Verify remote SHA equality and report the true CI state.
