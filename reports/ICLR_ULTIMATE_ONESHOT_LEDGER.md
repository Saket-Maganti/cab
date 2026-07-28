# ICLR Ultimate One-Shot Live Ledger

This is the recovery checkpoint for the ICLR pre-execution build. Evidence
boundaries are active: no scientific model execution, fabricated human review,
or invented empirical results are permitted.

## Phase 0 — Git baseline and rapid inspection

- Started: 2026-07-28
- Files inspected:
  - `/Users/saketmaganti/Downloads/CAB_ICLR_ULTIMATE_ONESHOT_BUILD_AND_PUSH_MAIN.md`
  - initial tracked-file inventory
  - Git branch, status, HEAD, upstream, and remote configuration
- Files modified:
  - `reports/ICLR_ULTIMATE_ONESHOT_GIT_BASELINE.md`
  - `reports/ICLR_ULTIMATE_ONESHOT_LEDGER.md`
- Commands: prompt read in sequential chunks; Git baseline commands; `rg --files`;
  parent-directory `AGENTS.md` discovery.
- Exit codes: all `0`.
- Elapsed time: in progress.
- Blockers: none yet; one pre-existing untracked file is preserved as user-owned.
- Decisions:
  - remain on `main`;
  - treat `d3469045a78de3a20b37783b29167805e7417e04`
    as the pre-run commit;
  - exclude private/protected payloads from Git;
  - run no scientific inference.
- Next phase: focused current-state and known-blocker reproduction.

## Phase 0 — Completed current-state verification

- Files inspected:
  - canonical split registry and held-out release policy;
  - human/C10 gate output;
  - agent, runner, manifest, analysis, notebook, data, and paper inventories;
  - pre-existing Prompt 1 post-fix baseline.
- Files modified:
  - `reports/ICLR_ONESHOT_CURRENT_STATE.json`
  - `reports/ICLR_ONESHOT_CURRENT_STATE.md`
- Commands:
  - four-test serial Prompt 1 reproduction;
  - protected-path Git inventory and history inventory;
  - focused JSON and filesystem inventories.
- Exit codes:
  - inspection commands: `0`;
  - focused reproduction: `1` as expected, with 4 reproduced failures.
- Elapsed time:
  - focused reproduction: 64.03 seconds.
- Blockers:
  - 12 tracked protected payloads;
  - stale state assertion;
  - stale release inventory/hash.
- Decisions:
  - permanently invalidate publicly exposed held-out material;
  - preserve genuine evidence counts at zero;
  - parallelise RAAC, contamination/state, and human/C10 work.
- Next phase: implement blocker repairs and remaining ICLR infrastructure.

## Phase 1 — Contamination, protected splits, and canonical state

- Files inspected:
  - public Git history and tracked protected payload surfaces;
  - held-out release policy, split registry, run gates, notebooks, and archives.
- Files modified:
  - `data/manifests/CAB_PUBLIC_CONTAMINATION_REGISTRY.json`
  - `data/manifests/heldout_challenge_v2_public_manifest.json`
  - `data/manifests/CAB_CANONICAL_SPLIT_REGISTRY.json`
  - `reports/PROTECTED_HELDOUT_EXPOSURE_INVENTORY.json`
  - `docs/PUBLIC_HELDOUT_CONTAMINATION_AND_HISTORY_POLICY.md`
  - protected-heldout, release, leakage, split, and workflow-state modules/tests.
- Commands:
  - public exposure inventory generation;
  - protected architecture validation;
  - canonical split generation and read-only check.
- Exit codes: all final checks `0`.
- Results:
  - all publicly exposed v1 Scale/naturalistic/Main/held-out material is
    permanently development-only or contaminated-not-confirmatory;
  - three v2 protected roles use commitment-only public manifests;
  - 9 canonical roles, 0 cross-role overlaps;
  - new private payload roots are ignored and 0 private files are tracked.
- Decision: history rewriting is optional hygiene and cannot restore scientific
  secrecy; no history rewrite was performed.
- Next phase: RAAC and human-validation infrastructure.

## Phase 2 — Recovery-Aware Agent Control

- Files modified:
  - `src/causal_agent_bench/raac/`
  - runner, manifest, metadata, trajectory, scoring, and schema integration;
  - `configs/raac/`
  - `docs/RAAC_METHOD.md`
  - `docs/RAAC_FAIRNESS_AND_BUDGET_POLICY.md`
  - `experiments/RAAC_ABLATION_PLAN.md`
  - Kaggle baselines/ablations notebook and generator.
- Results:
  - 12-state typed fail-closed controller;
  - 16 observable anomaly signals and 11 decision kinds;
  - LIGHT/FULL, 6 ablations, and 5 baseline wrappers;
  - equal/practical budget contracts, overhead accounting, deterministic
    fixtures, checkpoint/resume, and hidden-metadata blindness.
- Focused validation: RAAC tests included in the 58-test and 145-test passing
  slices recorded below.
- Evidence boundary: fixture and engineering only; no RAAC performance claim.
- Next phase: human validation and C10.

## Phase 3 — Human validation, agreement, manipulation checks, and C10

- Files modified:
  - canonical review packet below
    `data/human_validation/compact20_real_review/`;
  - `configs/human_validation/c10_contract_v1.json`;
  - human-review, packet, agreement-analysis, and manipulation-check modules;
  - human protocol, resource plan, ethics, and C10 documentation/tests.
- Results:
  - 20 candidates, two blank independent-review slots per candidate;
  - separate reviewer registry and adjudication sheet;
  - privacy-safe IDs, qualification, conflicts, consent, timestamps, blinding,
    raw agreement, kappa, alpha, prevalence, intervals, and family diagnostics;
  - 20/20 interventions linked to deterministic engineering-only checks;
  - empty, proxy, AI-assisted, duplicate-reviewer, incomplete, and
    unadjudicated inputs fail closed.
- Genuine human rows: `0`.
- State: `HUMAN_REVIEW_INCOMPLETE`; C10: `C10_PENDING`.
- Next phase: private-safe Scale and naturalistic candidates.

## Phases 4–6 — Scale-100, naturalistic transfer, and main-set decision

- Files modified:
  - private candidate authoring schema and materializer/validator;
  - ignored private candidate packs for Scale-100 v2 and naturalistic v2;
  - public-safe manifests and aggregate validation reports;
  - `docs/MAIN_SET_RESOURCE_AWARE_DECISION_POLICY.md`.
- Commands:
  - deterministic private materialization;
  - `PYTHONPATH=src:. python3 scripts/validate_iclr_private_candidates.py
    --write-json reports/ICLR_PRIVATE_CANDIDATE_VALIDATION.json`.
- Exit code: `0`.
- Results:
  - Scale: 100 base tasks, 500 intervention mappings, 600 planned instances,
    10 domains, 100 normalised patterns, 0 registered overlap signals;
  - naturalistic: 60 base tasks, 300 mappings, 360 planned instances,
    10 domains, 60 normalised patterns, 0 registered overlap signals;
  - four canonical answer contracts, all 10 intervention families, static
    provenance/licence/privacy/injection passes, blank review packets;
  - public Git contains only aggregates and non-reversible commitments.
- Blocker: task-level human review, adjudication, C10, and slice lock.
- Decision: Main expansion remains conditional; raw scale is not a contribution
  by itself.
- Next phase: resource, analysis, and paper infrastructure.

## Phases 7–12 — Resource, notebook, analysis, paper, and reviewer readiness

- Files modified:
  - `src/causal_agent_bench/resources.py`
  - `scripts/cab_resource_preflight.py`
  - `configs/iclr/`
  - M4 and Kaggle operations documentation;
  - `src/causal_agent_bench/analysis/iclr_preexecution.py`
  - confirmatory analysis plan, claim ledger, paper method section, phase-15
    assets, reviewer gauntlet, and execution handbook.
- Commands and results:
  - resource preflight: exit `0`, read-only, 2-worker low-memory plan,
    1,000-replicate deterministic pilot bootstrap, all projections labelled
    `ESTIMATE_NOT_MEASURED`;
  - Kaggle offline fixture validation: exit `0`, 9/9 notebooks, 72 fixture
    receipts, live execution refused, no scientific execution;
  - draft paper checks and 3-pass LaTeX build: exit `0`, 14-page PDF, seven
    deliberately visible result placeholders.
- Analysis coverage:
  paired/cluster/stratified bootstrap, exact paired tests, equivalence,
  missingness and opportunity denominators, rank uncertainty, RAAC
  trade-off/efficiency, predictive validity, calibration, and resumable shards.
- Next phase: unified gate and complete validation.

## Phases 13–15 — Unified gate and validation

- Files modified:
  - `src/causal_agent_bench/safety/iclr_preexecution_gate.py`
  - `scripts/check_iclr_preexecution_readiness.py`
  - `tests/test_iclr_preexecution_gate.py`
  - release manifest and final validation artifacts.
- Unified gate:
  - command:
    `PYTHONPATH=src:. python3 scripts/check_iclr_preexecution_readiness.py`
  - exit code: `2`, expected for external human/evidence prerequisites;
  - state: `HUMAN_VALIDATION_REQUIRED`;
  - build complete: true;
  - genuine human rows, real trajectories, audited runs, paper-eligible
    assets, and supported empirical claims: all `0`.
- Focused validation:
  - command: 20-file serial ICLR regression slice;
  - exit code `0`; `145 passed in 69.05s`.
- Static validation:
  - Ruff: exit `0`, all files clean;
  - mypy: exit `0`, 205 source files clean;
  - JSON/YAML parsing: exit `0`, 15 JSON and 102 YAML files;
  - security, release, split registry, protected commitment, and
    `git diff --check`: exit `0`.
- Complete provider-free suite:
  - command:
    `python3 -m pytest -q -n4 -m 'not provider and not model and not local_run'`;
  - first run: exit `1`, 1087 passed, 1 skipped, 4 release-hash failures after
    a final source lint cleanup;
  - release manifest refreshed and the exact four failures rerun:
    `4 passed in 3.53s`;
  - stable-tree rerun: exit `0`,
    `1091 passed, 1 skipped in 171.32s`.
- Unexpected blockers: none.
- Next phase: final report, explicit staging/security review, direct main
  commit, push, remote SHA verification, and CI observation.

## Phase 16 — Direct-main publication

- Staged scope: 153 task-owned files; 26,838 insertions and 591 deletions.
- Pre-commit sanitation:
  - security, release, split-registry, held-out commitment, private-candidate,
    and whitespace checks passed;
  - staged private paths: 0;
  - tracked private paths: 0;
  - the pre-existing untracked
    `reports/ICLR_PROMPT1_POSTFIX_BASELINE.md` remained excluded.
- Implementation commit:
  `45f9209631c6152314dcb82d3e315a8cf4e751a9`
  (`Complete CAB ICLR pre-execution build`).
- Push: `git push origin main`, exit `0`; no force push and no pull request.
- First remote verification:
  local and `refs/heads/main` both resolved to
  `45f9209631c6152314dcb82d3e315a8cf4e751a9`.
- GitHub Actions observation: CI queued; Fast Check, Docs Check, Claim Safety,
  Max Ceiling Provider-Free Gates, Batch smoke, and Docs in progress. The
  aggregate legacy-status endpoint was pending with zero attached contexts.
- Next phase: commit this mandatory publication record, push it to `main`, and
  repeat exact remote-SHA and CI-state verification.

## Phase 17 — Remote CI follow-up

- Implementation-check outcomes:
  - passed: Docs Check, Batch smoke, Claim Safety;
  - in progress at observation: CI and Max Ceiling Provider-Free Gates;
  - failed: Fast Check and Docs deployment.
- Fast Check root cause: GitHub's newer Ruff enforced `RUF036` on two
  pre-existing union annotations in
  `src/causal_agent_bench/agents/llm_clients.py`.
- Repair: reordered the union members without semantic change.
- Exact local workflow: `make fast-check`, exit `0`, 61.0 seconds; included
  Ruff, mypy over 205 source files, 91 fast tests, 62 governance tests,
  evidence/claim/paper checks, zero-cost preflights, and security.
- Release check: exit `0`; refreshed bundle hash
  `7db51c3dd07eebb6f4ac2a5e86fdeb10d050c9dfb20e1ff0095586ad21651578`,
  652 files.
- Docs diagnosis: the site built and uploaded; `actions/deploy-pages` returned
  HTTP 404 because GitHub Pages is not enabled in repository settings. No
  repository setting was changed implicitly.
- Next phase: push the focused CI repair, verify exact remote SHA, and observe
  the replacement workflows without waiting indefinitely.

## Phase 18 — Broad CI spelling repair

- The replacement `Fast Check`, Docs Check, Claim Safety, and Max Ceiling
  Provider-Free Gates all passed on GitHub.
- The broad CI lint/type job passed Ruff and mypy but failed its independent
  `codespell` step on four wording-only findings:
  two pre-existing comments, one RAAC fixture description, and one evaluation
  protocol sentence.
- Repair: normalized `re-declaring` to `redeclaring` and `unparseable` to
  `unparsable`; no executable semantics changed.
- Local validation: `codespell`, Ruff, mypy, 28 focused RAAC/tool-schema tests,
  security, release, and whitespace checks all passed.
- Refreshed release bundle hash:
  `0c8c1b990eb0890065d7cfccfd487df4fd9c651315e46f45bd5fcf990cb3ac64`,
  652 files.
- Next phase: commit and push this final CI repair, verify the remote SHA, and
  observe the replacement checks.

## Phase 19 — Python 3.13 development-dependency repair

- The replacement broad CI Python 3.13 job passed 1,092 tests with three
  skips, then ended with one collection error:
  `ModuleNotFoundError: No module named 'nbformat'`.
- Root cause: `tests/test_cab_insane_autorun_artifacts.py` directly imports
  `nbformat`, but the project's `dev` optional dependency set did not declare
  it. The Python 3.13 runner had no incidental copy installed.
- Repair: added `nbformat>=5.10` to `project.optional-dependencies.dev`.
- Local validation: TOML parse, four affected notebook-artifact tests,
  `codespell`, Ruff, security, release, and whitespace checks passed.
- Next phase: push the dependency repair, verify the exact remote SHA, and
  inspect the replacement Python matrix state.
