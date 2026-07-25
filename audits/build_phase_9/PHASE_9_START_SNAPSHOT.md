# Build Mode Phase 9 — Start Snapshot

**Generated:** 2026-05-20 (BUILD MODE PHASE 9)

## Branch

`main`

## Working tree

- **Dirty paths:** ~422 modified/untracked (not committed)
- **Phase 9 adds:** mock micro demo run, engineering demo bundle, run/agent cards, advisor show-and-tell, NEXT_DECISION

## fast-check

```
make fast-check → PASS (~61s) [from Phase 8 baseline]
```

## Submission readiness

```
classification: local_preliminary (readiness checker)
project classification: build_infrastructure_ready (MASTER_STATUS)
submission_ready: False
```

## Final build audit

```
scripts/final_build_phase_audit.py → PASS (Phase 8)
```

## Demo run (Phase 9)

```
results/20260520T072032Z_pilot_mock_diagnostic_micro
config: configs/pilot_mock_diagnostic_micro.yaml
trajectories: 3/3 complete
runtime: ~13s
evidence: mock_diagnostic_only, scientific_evidence=false
```

## Active runs

None (demo run completed)

## Current evidence status

| Claims | Status |
|---|---|
| C1–C8 | **planned** |
| C9 | **engineering_only** |
| C10 | **planned** |

## Top blockers

1. No provider-backed pilot
2. No human validation
3. Paper placeholders unfilled
4. MAIN_EXPERIMENT_GATE: NO-GO

## Safe commands

```bash
make fast-check
python3 scripts/generate_master_status.py
python3 -m causal_agent_bench plan-run --config configs/pilot_stub_micro_3.yaml
cat demo/ENGINEERING_DEMO_BUNDLE.md
```

## Forbidden commands (without approval)

```bash
python3 -m causal_agent_bench run --config configs/pilot_free_local_20.yaml
python3 -m causal_agent_bench run --config configs/pilot_multi_provider_20.yaml
python3 -m causal_agent_bench run --config configs/pilot_openai_20.yaml
```

## Phase 9 safety

- Demo run: mock only, no LLM/Ollama/paid calls
- No claim upgrades
- Paper assets exported with engineering_only labels
