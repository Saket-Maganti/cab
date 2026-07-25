# Safe Next-Run Decision Tree

Choose a path based on **time, budget, and evidence goals**. This tree does **not** execute anything — it guides your next command.

**Default rule:** If unsure, run `make fast-check` and stop.

---

## Quick reference

| If you have… | Do this | Config | Runtime | Cost | Evidence level |
|---|---|---|---|---|---|
| 5 min | fast-check only | — | ~1 min | $0 | none |
| 10 min | plan + audit (no run) | `pilot_stub_micro_3.yaml` | ~2 min | $0 | dry_run/plan |
| 15 min | mock micro run | `pilot_mock_diagnostic_micro.yaml` | ~5–10 min | $0 | mock_diagnostic |
| 20 min | stub micro run | `pilot_stub_micro_3.yaml` | ~5 min | $0 | stub_engineering |
| 30 min | mock 10 run | `pilot_mock_diagnostic_10.yaml` | ~10–20 min | $0 | mock_diagnostic |
| 30–60 min | local micro 3 ⚠️ | `pilot_free_local_micro_3.yaml` | 30–60+ min | $0* | local_preliminary |
| overnight ⚠️ | local 20 ⚠️ | `pilot_free_local_20.yaml` | hours | $0* | local_preliminary |
| budget approved | provider pilot | `pilot_multi_provider_20.yaml` | hours | $$ | provider_pilot |
| paper deadline | **do not** run huge unvalidated experiments | — | — | — | — |

\*Local runs use your GPU/CPU time, not API spend. Still not scientific evidence without validation.

---

## Decision flow

```
START
  │
  ├─ Need status only? ──► make fast-check
  │                        python3 scripts/generate_master_status.py
  │
  ├─ Need to plan without running? ──► plan-run + audit-dataset (stub micro config)
  │
  ├─ First tiny experiment ever? ──► mock micro (safest)
  │     └─► then stub micro (pipeline check)
  │
  ├─ Want to test local Ollama? ──► local micro 3 ONLY if you accept:
  │     • long runtime
  │     • mark-interrupted if stopped
  │     • never claim real LLM benchmark results
  │
  ├─ Budget approved + checklist done? ──► provider pilot 20
  │
  └─ Main 500? ──► STOP unless MAIN_EXPERIMENT_GATE = GO
```

---

## Path details

### 5 minutes — health check only

```bash
make fast-check
python3 scripts/final_build_phase_audit.py
```

- **Allowed claims:** none
- **When to stop:** after pass/fail reviewed

### 10 minutes — plan and audit (no run)

```bash
python3 -m causal_agent_bench plan-run --config configs/pilot_stub_micro_3.yaml
python3 -m causal_agent_bench audit-dataset --config configs/pilot_stub_micro_3.yaml
python3 scripts/check_submission_readiness.py
```

- **Allowed claims:** none
- **Post-audit:** review PRE_EXPERIMENT_FREEZE_CHECKLIST.md

### 15 minutes — mock micro (recommended first experiment)

```bash
# Before run — complete freeze checklist for mock gate
python3 -m causal_agent_bench validate-config --config configs/pilot_mock_diagnostic_micro.yaml
python3 -m causal_agent_bench plan-run --config configs/pilot_mock_diagnostic_micro.yaml
python3 -m causal_agent_bench run --config configs/pilot_mock_diagnostic_micro.yaml
python3 -m causal_agent_bench score --run-dir results/<latest> --allow-incomplete
python3 scripts/check_evidence_safety.py
```

- **Evidence level:** mock_diagnostic
- **Allowed claims:** engineering_only — "mock diagnostic detected expected failure pattern"
- **Forbidden:** "agents fail", "models differ", any LLM generalization
- **When to stop:** after score; do not export-paper-assets without flags

### 20 minutes — stub micro

```bash
python3 -m causal_agent_bench run --config configs/pilot_stub_micro_3.yaml
python3 -m causal_agent_bench summarize-run --run-dir results/<latest>
```

- **Evidence level:** stub_engineering
- **Allowed claims:** C9 engineering_only (pipeline reproducibility)
- **Post-audit:** index-runs, evidence safety

### 30–60 minutes — local micro 3 ⚠️

**Only when explicitly ready for local model time.**

```bash
python3 -m causal_agent_bench plan-run --config configs/pilot_free_local_micro_3.yaml
python3 -m causal_agent_bench run --config configs/pilot_free_local_micro_3.yaml
# If interrupted:
python3 -m causal_agent_bench mark-interrupted --run-dir results/<dir>
```

- **Evidence level:** local_preliminary (interrupted = not evidence)
- **Allowed claims:** feasibility notes only — not benchmark results
- **When to stop:** hit limiters or mark interrupted — never score incomplete as scientific

### Budget approved — provider pilot

```bash
python3 -m causal_agent_bench list-providers
python3 -m causal_agent_bench estimate-cost --config configs/pilot_multi_provider_20.yaml
python3 -m causal_agent_bench dry-run --config configs/pilot_multi_provider_20.yaml
# Set allow_paid_calls: true ONLY after written approval
python3 -m causal_agent_bench run --config configs/pilot_multi_provider_20.yaml
```

- **Evidence level:** provider_pilot (if complete)
- **Allowed claims:** weakened pilot wording only — not C1–C8 supported
- **Post-audit:** analyze, export with care, update claim ledger to weakened max

### Paper deadline approaching

- Do **not** start 500-task main or unvalidated 100-task pilot
- Run: `make check-readiness`, `lint_paper_claims.py --mode draft`
- Write methods/limitations; leave results placeholders

---

See [PRE_EXPERIMENT_FREEZE_CHECKLIST.md](PRE_EXPERIMENT_FREEZE_CHECKLIST.md), [docs/DO_NOT_OVERCLAIM.md](../docs/DO_NOT_OVERCLAIM.md), [MASTER_STATUS.md](../MASTER_STATUS.md).
