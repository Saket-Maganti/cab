# Claim Update Recommendations — Post-Provider-Pilot Audit

**Audit ID:** `20260519_no_real_provider_pilot`  
**Run directory audited:** *none* (no provider-backed pilot exists)  
**Verdict:** **invalid** — do not update claim ledger with pilot evidence

---

## Summary

No non-oracle provider-backed pilot run was found under `results/`. Dry-run and local-stub runs exist but do **not** satisfy `required_evidence` for any main scientific claim. **Keep all main claims at `planned`.** Do not run Prompt 67 (claim ledger / paper sync) until a valid audited provider run exists.

---

## Per-claim recommendations

| Claim | Short name | Current status | Recommendation | Rationale |
|---|---|---|---|---|
| **C1** | clean_success_overestimates_robustness | planned | **Keep planned** | Requires paired clean/intervention runs across multiple **non-oracle LLM** agents with CIs. Stub run has 0% success; dry-run used `local_stub`. |
| **C2** | tool_failure_memory_corruption_expose_weaknesses | planned | **Keep planned** | Needs family breakdown from real LLM trajectories. Stub metrics are zero-valued engineering artifacts. |
| **C3** | trajectory_metrics_reveal_hidden_failures | planned | **Keep planned** | Needs human validation + real disagreement cases. No provider trajectories scored. |
| **C4** | acrs_changes_rankings | planned | **Keep planned** | ACRS null in stub run (no successes). No ranking comparison possible for real models. |
| **C5** | recovery_separable_from_planning | planned | **Keep planned** | Requires component analysis on credible non-oracle agents. |
| **C6** | self_checking_selectively_improves_robustness | planned | **Keep planned** | Ablation/scaffold evidence not produced. |
| **C7** | agents_overuse_tools | planned | **Keep planned** | Irrelevant-tools family needs real agent behavior. |
| **C8** | agents_stop_prematurely | planned | **Keep planned** | Premature-success-signal family needs real trajectories + error-case audit. |
| **C9** | smoke_tests_are_local_and_reproducible | engineering_only | **Keep engineering_only** | Still valid for local/smoke reproducibility. Do **not** conflate with provider pilot success. |
| **C10** | interventions_isolate_targeted_components | planned | **Keep planned** | Human/expert audit not linked to provider run. Frozen intervention audit exists separately but does not satisfy full claim. |

---

## What would change after a valid provider pilot

After a completed `results/<timestamp>_pilot_multi_provider_20` run with score/analyze/export passing:

| Claim | Possible post-pilot status | Wording constraint |
|---|---|---|
| C1 | **Support only as pilot evidence** (not `supported`) | "In a 20-task provider-backed pilot, we observe…" |
| C2 | **Support only as pilot evidence** | Per-family pilot observations only; no main-scale extrapolation |
| C4 | **Support only as pilot evidence** | 3 agents insufficient for stable ranking claims |
| C7, C8 | **Weaken or keep planned** | Depends on error-case yield in tiny pilot |
| C3, C5, C6, C10 | **Keep planned** | Require human validation or ablations beyond tiny pilot |

---

## Engineering vs pilot vs main claim split

| Tier | What exists today | Allowed claim language |
|---|---|---|
| **Engineering** | Dry-run pass, cost estimate, stub pipeline, tests | "Pipeline is ready for paid pilot"; "Dry-run simulates without provider calls" |
| **Pilot** | *Nothing yet* | N/A |
| **Main (NeurIPS-scale)** | *Nothing yet* | N/A |

---

## Actions explicitly not recommended

- Do **not** mark C1–C8 or C10 as `supported` or `pilot-supported` from stub/dry-run data
- Do **not** link `results/20260519T053609Z_pilot_20_multi_agent_stub` to scientific claims
- Do **not** run Prompt 67 until Prompt 66 verdict is at least `real pilot with usable pilot evidence`
- Do **not** fill paper placeholders from stub zero-success tables

---

## Next command

Return to Prompt 65 execution with explicit paid approval:

```bash
python3 -m causal_agent_bench run --config configs/pilot_multi_provider_20.yaml
```

Then re-run Prompt 66 against the resulting `results/<run_dir>`.
