# Project Health Dashboard

Traffic-light status — **honest as of Build Mode Phase 9**. Regenerate with `make master-status` and `python3 scripts/final_build_phase_audit.py`.

| Area | Status | Notes |
|---|---|---|
| Code health | 🟢 good | Package installs; CLI wired; schemas stable |
| Tests | 🟢 good | `make fast-check` ~60s; build phase tests pass |
| Configs | 🟡 partial | 50+ configs; audit warnings on missing descriptions |
| Docs | 🟢 good | Hub + master status + command map complete |
| Run management | 🟢 good | plan-run, index-runs, mark-interrupted, limits |
| Evidence safety | 🟢 good | check_evidence_safety + claim ledger enforced |
| **E2E mock demo** | 🟢 good | Phase 9 mock micro run; pipeline validated |
| Paper package | 🟡 partial | Draft + placeholders; no empirical fill |
| Reviewer package | 🟢 good | Reviewer packet + mock reviews + gap map |
| Human validation | ⚪ not started | Protocol only; no annotations |
| Real experiments | 🔴 blocked | No provider pilot; main gate NO-GO |
| Release packaging | 🟡 partial | Manifest exists; public bundle not cut |
| Advisor readiness | 🟢 good | Show-and-tell checklist + demo bundle ready |
| Submission readiness | 🔴 blocked | submission_ready=False; placeholders remain |
| **Build mode** | 🟢 pause | See [NEXT_DECISION.md](NEXT_DECISION.md) — stop overbuilding |

## Summary

**Infrastructure:** ready for advisor review; **Phase 9 mock E2E demo complete.**  
**Science:** blocked until provider pilot + human validation.  
**Classification:** `build_infrastructure_ready` · **Recommend:** [NEXT_DECISION.md](NEXT_DECISION.md)

## Quick health commands

```bash
make fast-check
python3 scripts/final_build_phase_audit.py
python3 scripts/generate_master_status.py
python3 scripts/check_submission_readiness.py
```

## Legend

- 🟢 **good** — usable now, no known integrity issues
- 🟡 **partial** — usable with documented caveats
- 🔴 **blocked** — cannot proceed without major prerequisite
- ⚪ **not started** — intentionally not begun

See [MASTER_STATUS.md](MASTER_STATUS.md), [BLOCKED_ITEMS.md](BLOCKED_ITEMS.md).
