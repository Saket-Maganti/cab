# Master Status — CausalAgentBench

**Generated:** 2026-07-23T17:18:37.365106+00:00
**Classification:** `build_infrastructure_ready`
**Readiness checker:** `local_preliminary` · submission_ready=False

> Readiness checker may report local_preliminary due to indexed local/stub runs; no provider pilot or supported empirical claims.

## 1. Executive status

The repository is a **build-infrastructure-ready** research scaffold: benchmark design,
tooling, docs, and validation gates are in place. Empirical claims remain **planned**.

## 2. What is built

- Pydantic schemas (tasks, interventions, instances, trajectories, scores)
- Deterministic benchmark generation (pilot_v0.1, main_v0.1 candidate)
- Simulated tools and local environment execution
- Experiment runner (config hash, resume, limits, scoring, metadata)
- Run management (plan-run, index-runs, mark-interrupted, run-status)
- Mock/stub agents and mock diagnostic configs
- Analysis export (tables, figures, failure gallery, leaderboard)
- Claim ledger + evidence safety validators
- Paper draft with placeholder protection
- Reviewer/advisor handoff package (Phases 5–8)
- Release/reproducibility scaffolding (manifest, repro bundle plan)
- Human validation export protocol (no annotations yet)
- CI fast-check workflows
- Consistency audits (repo, config, build phase)
- Phase 9 engineering demo bundle (mock micro E2E validated)

## 3. What is not built / not proven

- Completed provider-backed pilot on frozen split
- Human validation annotations / agreement tables
- Main 500-task multi-provider experiment
- Supported C1–C8 or C10 empirical claims
- Final NeurIPS-ready results or acceptance guarantee
- Frozen benchmark v1.0 with full human audit sign-off

## 4. Evidence map

- **dry_run:** 0 runs
- **stub_engineering:** 70 runs (e.g. ['smoke', 'smoke', 'smoke'])
- **mock_diagnostic:** 5 runs (e.g. ['pilot_mock_diagnostic_micro', 'pilot_mock_diagnostic_micro', 'pilot_mock_diagnostic_micro'])
- **interrupted_local:** 2 runs (e.g. ['pilot_free_local_20', 'pilot_free_local_fast_10'])
- **local_preliminary:** 0 runs
- **provider_pilot:** 0 runs
- **human_validated:** 0 runs
- **main_experiment:** 0 runs

## 5. Safe commands

```bash
make fast-check
```
```bash
make doctor
```
```bash
make plan-micro
```
```bash
make audit-repo
```
```bash
make audit-configs
```
```bash
make check-readiness
```
```bash
make status
```
```bash
python3 scripts/generate_master_status.py
```
```bash
python3 scripts/final_build_phase_audit.py
```
```bash
python3 scripts/check_evidence_safety.py
```
```bash
python3 scripts/check_claim_ledger.py
```
```bash
python3 -m causal_agent_bench plan-run --config configs/pilot_stub_micro_3.yaml
```
```bash
python3 -m causal_agent_bench audit-dataset --config configs/pilot_stub_micro_3.yaml
```
```bash
python3 -m causal_agent_bench index-runs
```
```bash
python3 -m causal_agent_bench dry-run --config configs/pilot_stub_micro_3.yaml
```

## 6. Dangerous / heavy commands (require approval)

- `python3 -m causal_agent_bench run --config configs/pilot_openai_20.yaml  # paid`
- `python3 -m causal_agent_bench run --config configs/pilot_multi_provider_20.yaml  # paid`
- `python3 -m causal_agent_bench run --config configs/pilot_free_local_20.yaml  # long local`
- `python3 -m causal_agent_bench run --config configs/commercial_api_main_500.yaml  # main scale`
- `python3 -m causal_agent_bench fill-paper-from-run  # without verified pilot`
- `make smoke  # runs smoke config`

## 7. Next exact steps

1. Review experiments/PRE_EXPERIMENT_FREEZE_CHECKLIST.md
2. Review experiments/SAFE_NEXT_RUN_DECISION_TREE.md
3. When ready: mock micro run (configs/pilot_mock_diagnostic_micro.yaml) — engineering only
4. After mock: optional stub micro (configs/pilot_stub_micro_3.yaml) — pipeline check
5. Before any paid run: budget approval + estimate-cost + freeze checklist gate
6. Export human validation sample after first complete non-stub pilot

## 8. Advisor / professor handoff

- **Safe to show:** True
- Engineering scaffold only — not submission-ready
- Mock/stub runs are not real LLM behavior
- C1–C8/C10 remain planned
- Use handoff/ADVISOR_REVIEW_BUNDLE_INDEX.md

## 9. Paper readiness

**Can write now:**
- Problem statement and motivation
- Benchmark design and intervention framework
- Metric definitions (ACRS, trajectory diagnostics)
- Experimental setup (planned)
- Limitations and ethics

**Must wait for experiments:**
- Results tables with real numbers
- Ranking / performance claims
- Human validation agreement statistics
- Abstract empirical claims ([N], [M], [K], [X], [rho])

## 10. Experiment readiness (tiny run when ready)

- **Safest:** `configs/pilot_mock_diagnostic_micro.yaml` (mock diagnostic micro)
- Evidence level: mock_diagnostic
- Allowed claims: engineering_only — detector wiring only
- **Then:** `configs/pilot_stub_micro_3.yaml` (stub micro)

## Claims

- **C1:** planned
- **C10:** planned
- **C2:** planned
- **C3:** planned
- **C4:** planned
- **C5:** planned
- **C6:** planned
- **C7:** planned
- **C8:** planned
- **C9:** engineering_only

## Blockers

- No completed provider-backed non-oracle pilot run.
- Human validation sample/annotations missing.
- Paper asset submission validation failed.
- Paper placeholders remain (submission mode).
