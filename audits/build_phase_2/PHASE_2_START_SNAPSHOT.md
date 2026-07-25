# Phase 2 build snapshot

- **Date:** 2026-05-20
- **Branch:** main
- **Working tree:** dirty (many modified/untracked files from build mode; see `git status --short`)
- **Fast-check:** run after Phase 2 enhancements (target: pass under 10 minutes)
- **Active causal_agent_bench runs:** none expected
- **Long model processes:** none (Ollama may run separately; no experiment runs started by build mode)
- **Paper claims:** unchanged (C1–C8/C10 planned)
- **Phase 2 scope:** reports, compare-runs, failure-gallery, dataset audit, paper/submission validators, registry, roadmap, issue templates

## Interrupted runs (do not use as evidence)

- `results/20260520T030034Z_pilot_free_local_20` — 21/360
- `results/20260520T034642Z_pilot_free_local_fast_10` — 3/10

## New CLI (Phase 2)

- `generate-report`, `compare-runs`, `failure-gallery`, `audit-dataset`

## Allowed next step (build-only smoke)

```bash
python3 -m causal_agent_bench generate-report --run-dir results/20260519T053609Z_pilot_20_multi_agent_stub
python3 -m causal_agent_bench audit-dataset --config configs/pilot_stub_micro_3.yaml
```

Do **not** run `causal_agent_bench run` without explicit user approval.
