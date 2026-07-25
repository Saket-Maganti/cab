# Mock Review Summary

Synthesizes [MOCK_REVIEW_1_SUPPORTIVE.md](MOCK_REVIEW_1_SUPPORTIVE.md), [MOCK_REVIEW_2_SKEPTICAL.md](MOCK_REVIEW_2_SKEPTICAL.md), [MOCK_REVIEW_3_BORDERLINE.md](MOCK_REVIEW_3_BORDERLINE.md).

**Verdict:** Paper is **not submission-ready**. Benchmark package is advisor-showable; empirical claims are not.

---

## Top 10 changes before submission

1. Complete **bounded provider pilot** (multi-agent, frozen pilot split) — non-negotiable.
2. Run **human validation** on intervention validity + trajectory failures (n≥100 stratified).
3. Replace all result placeholders with **linked artifacts** (run dir, config hash, CIs).
4. **Calibrate trajectory diagnostics** against human labels (C3).
5. Add **ACRS sensitivity analysis** (weight ablations).
6. Sharpen **related-work contrast** (AgentBench, WebArena, GAIA, τ-bench, AgentBoard).
7. Bound **causal language** everywhere (abstract especially).
8. Operationalize **leaderboard/gaming policy** with held-out templates.
9. Document **model/API versions** in appendix metadata table.
10. Pass **submission-mode** lint: claim ledger, placeholders, paper assets, evidence safety.

## Must-have experiments

| Priority | Experiment | Config |
|---|---|---|
| P0 | Provider pilot | `configs/pilot_multi_provider_20.yaml` |
| P0 | Human validation export + annotation | post-pilot |
| P1 | Ablation matrix (scaffolds) | `configs/ablations/*` |
| P2 | Main 500 (only if gate GO) | `configs/main_500_multi_provider.yaml` |

## Must-have paper edits

- Abstract: remove unfilled [N]/[M]/[K]/[X]/[rho] or mark as planned study explicitly.
- Results §7: either results or clearly labeled "planned experiments" subsection.
- Limitations: synthetic environment, heuristic scorers, no deployment claims.
- Ethics: complete compensation/consent placeholders before human collection.

## Must-have validation

- Intervention validity: human agreement on audit sample (C10).
- Diagnostic quality: human agreement on failure tags (C3).
- Scorer version pinned in all tables.

## Top rejection risks

| Risk | Severity | Mitigation |
|---|---|---|
| No real LLM results | **Critical** | Provider pilot |
| Synthetic = unrealistic | High | Limitations + mini-study roadmap |
| Causal overclaim | High | Bounded wording + rebuttal prep |
| ACRS arbitrary | Medium | Sensitivity + component reporting |
| Not novel vs existing benchmarks | Medium | Contribution map + sharper related work |
| Engineering not science | Medium | Empirical package in paper |
| Heuristic diagnostics | Medium | Human calibration |
| Gaming / contamination | Medium | Split policy + audits |
| Incomplete runs cited | Medium | Evidence safety gates |
| Human validation missing | **Critical** | Execute protocol |

## Recommended track

**NeurIPS Datasets & Benchmarks** or **ED track** — not main track until strong empirical + validation package.

## Internal actions

1. Share [handoff/ADVISOR_HANDOFF_PACKET.md](../handoff/ADVISOR_HANDOFF_PACKET.md) with advisor.
2. Work through [REBUTTAL_PREP.md](REBUTTAL_PREP.md).
3. Track tasks in [paper/PAPER_TASK_BOARD.md](../paper/PAPER_TASK_BOARD.md).

**Do not claim the paper is ready.**
