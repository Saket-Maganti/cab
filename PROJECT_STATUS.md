# Project Status

> `SUPERSEDED_BY: CURRENT_PROJECT_STATE.md` — use the canonical pre-run state instead of this historical generated snapshot.

**Generated:** 2026-07-23T17:18:22.880115+00:00
**Classification:** `local_preliminary`
**Submission ready:** False

## Build phases completed

- Phase 2: reports, dashboards, readiness
- Phase 3: benchmark quality and reviewer package
- Phase 4: automation, release packaging, orchestration
- Phase 5: paper package, advisor handoff, review simulation
- Phase 6: visuals, docs navigation, demo package
- Phase 7: consolidation, quality gate, tech debt
- Phase 8: pre-experiment freeze and master status pack

## Fast checks

- Run `make fast-check` locally (skipped during status generation)

## Evidence status

- Completed runs: 77 (stub=5, mock=4)
- Interrupted runs: 2
- Provider pilot runs: 0

### Claim ledger

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

## Ready artifacts

- docs/README.md
- docs/REPO_MAP.md
- docs/GLOSSARY.md
- docs/CLI_REFERENCE.md
- handoff/ADVISOR_DEMO_SCRIPT.md
- handoff/PROFESSOR_READY_CHECKLIST.md
- audits/repo_consistency/REPO_CONSISTENCY_AUDIT.md
- audits/config_consistency/CONFIG_AUDIT.md
- paper/latexpaper/figures/figure1_benchmark_overview_placeholder.png
- release/release_manifest.json

## Blocked artifacts

- provider-backed pilot run (complete)
- human validation annotations
- main experiment (500 tasks)
- submission-ready paper numbers

## Safe commands

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
python3 scripts/generate_project_status.py
```
```bash
python3 -m causal_agent_bench plan-run --config configs/pilot_stub_micro_3.yaml
```
```bash
python3 -m causal_agent_bench audit-dataset --config configs/pilot_stub_micro_3.yaml
```
```bash
python3 scripts/check_submission_readiness.py
```

## Do not run (without approval)

- `python3 -m causal_agent_bench run --config configs/pilot_openai_20.yaml`
- `python3 -m causal_agent_bench run --config configs/pilot_multi_provider_20.yaml`
- `python3 -m causal_agent_bench run --config configs/pilot_free_local_20.yaml`
- `make smoke  # runs model stub smoke config`

## Next recommended steps

- Run a bounded paid pilot with explicit budget approval.
- Export and annotate a human validation sample.
