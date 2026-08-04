# CAB ICLR Ultimate Master Orchestrator


## Repository

`/Users/saketmaganti/Projects/causal-agent-bench`

## Hard Resource Envelope

Assume the user has only:

- MacBook Air M4, 16 GB unified memory, 512 GB storage;
- free Kaggle notebooks with two NVIDIA T4 GPUs when available;
- no A100/H100 cluster;
- no guaranteed paid API budget;
- no background compute service;
- limited storage and session duration.

Design every solution around this envelope. Prefer streaming, sharding, quantisation, resumability, compact artifacts, incremental exports, and CPU-safe validation.

## Scientific Integrity Rules

Never:

- fabricate human review;
- fabricate model trajectories;
- fabricate results, costs, timings, tables, plots, or claims;
- tune the benchmark after seeing confirmatory results;
- expose gold answers to agents;
- mark fixture, mock, stub, dry-run, or interrupted outputs as scientific evidence;
- use provider secrets found in the environment;
- commit or push unless explicitly authorised;
- silently delete user work;
- claim ICLR acceptance or submission readiness without evidence.

Always distinguish:

- `DESIGN_ONLY`
- `ENGINEERING_ONLY`
- `FIXTURE_ONLY`
- `HUMAN_INPUT_REQUIRED`
- `EXECUTION_PENDING`
- `PRELIMINARY_REAL_EVIDENCE`
- `AUDITED_REAL_EVIDENCE`
- `PAPER_ELIGIBLE_EVIDENCE`

## Required Working Style

- Inspect before modifying.
- Repair locally fixable defects instead of only reporting them.
- Preserve reversible history.
- Prefer canonical implementations over duplicate layers.
- Record exact commands and exit codes.
- Keep the public surface clean.
- Build fail-closed gates.
- Stop when the stated phase is complete.


## Mission

Transform the existing maximum-ceiling pre-execution CAB repository into the strongest honest ICLR-oriented research system achievable before real scientific runs.

Do not merely enlarge the benchmark. Build a coherent ICLR paper contribution around:

1. intervention validity;
2. paired robustness inference;
3. recovery-aware agent control;
4. naturalistic predictive validity.

The benchmark must become the empirical vehicle for a general methodology.

## Phase 1 — Reconstruct Current Truth

Inspect current Git state, canonical handoff, scorer, answer contracts, paired metrics, split registry, leakage gates, human-review gate, C10, Compact-20, Scale-100, naturalistic transfer, Main candidate set, Kaggle notebooks, paper scaffold, release surface, CI, and evidence counts.

Re-run all locally safe gates. Do not assume prior reports remain current.

Produce:

- `reports/ICLR_CURRENT_STATE_VERIFIED.md`
- `reports/ICLR_CURRENT_STATE_VERIFIED.json`
- `reports/ICLR_GAP_MATRIX.md`

Classify every ICLR requirement as built, partially built, blocked by human input, blocked by execution, blocked by compute, optional, or scientifically unjustified.

## Phase 2 — Lock the ICLR Contribution

Create one canonical thesis and one contribution hierarchy.

Target thesis:

> Clean task success does not fully characterise the competence of tool-using agents. Robust evaluation requires goal-preserving interventions, explicit validity checks, matched clean/intervention inference, and analysis of recovery, abstention, and failure transitions.

Build a contribution contract covering:

- intervention validity;
- paired robustness inference;
- recovery-aware control;
- naturalistic predictive validity.

Create:

- `docs/ICLR_RESEARCH_THESIS.md`
- `docs/ICLR_CONTRIBUTION_CONTRACT.md`
- `docs/ICLR_RESEARCH_QUESTIONS_AND_HYPOTHESES.md`
- `docs/ICLR_NULL_RESULT_POLICY.md`

## Phase 3 — Execute All Build Prompts Internally

Implement the full requirements of Prompts 01–05. Do not execute Prompts 06–10.

## Phase 4 — ICLR Pre-Execution Gate

Create:

```bash
python3 scripts/check_iclr_preexecution_readiness.py
```

It must verify thesis, contribution contract, scorer validity, paired metrics, intervention validity schema, recovery-controller fixture tests, dataset diversity, split isolation, leakage, human-review packet readiness, C10, Kaggle fixture execution, provenance, frozen analysis plan, paper asset refusal, release safety, and zero fabricated evidence.

Possible states:

- `ICLR_BUILD_INCOMPLETE`
- `HUMAN_VALIDATION_REQUIRED`
- `COMPACT20_READY`
- `COMPACT20_AUDIT_REQUIRED`
- `SCALE100_READY`
- `NATURALISTIC_TRANSFER_READY`
- `ICLR_EMPIRICAL_PACKAGE_READY`
- `ICLR_SUBMISSION_CANDIDATE`

Expected build-only state: `HUMAN_VALIDATION_REQUIRED`.

## Phase 5 — Final Build Artifacts

Create:

- `CAB_ICLR_COMPLETE_BUILD_REPORT.md`
- `CAB_ICLR_EXECUTION_AND_EXPERIMENT_HANDBOOK.md`
- `CAB_ICLR_RESOURCE_AND_RUNTIME_PLAN.md`
- `CAB_ICLR_PAPER_CLAIM_LEDGER.md`
- `cab_iclr_handoff.md`

The handbook must list every future run in dependency order and classify it as CPU, single GPU, T4×2 data parallel, optional model parallel, provider API, human-only, or hybrid.

Every unmeasured runtime must be labelled `ESTIMATE_NOT_MEASURED`.

## Validation

Run fast tests, medium tests, full provider-free tests, Ruff, mypy, leakage gate, scorer conformance, paired metric properties, controller fixtures, notebook fixture execution, paper compilation, release validation, and Git diff check.

## Final Response

Report verified state, contribution readiness, repairs, new systems, validation, resource fit, blockers, exact next action, and handoff paths.

Stop after the no-execution ceiling is reached.
