# Rebuttal Preparation

Likely reviewer objections → response strategy. Status reflects **May 2026 scaffold** (no provider results).

| Objection | Response strategy | Required evidence | Paper section | Experiment/analysis | Status now |
|---|---|---|---|---|---|
| **Synthetic tasks are unrealistic.** | Acknowledge; position as controlled skill probe; cite mini-study/web-shadow roadmap; compare to lab benchmarks in chemistry/RL. | Optional naturalistic mini-study | Limitations §10; Related Work | `mini_study` configs (future) | Partial (docs only) |
| **This is robustness, not causal evaluation.** | Agree we use **bounded interventional language**; paired perturbations estimate sensitivity to designed factors, not deployment ACEs. | Intervention audit + human validity | §4 Framework | Isolation audit (done on pilot) | **Method draft OK** |
| **ACRS is too simple.** | Report component metrics alongside ACRS; run weight sensitivity; justify composite for ranking stability. | Ablation on weights; table2 components | §5 Metrics; §7 Results | Sensitivity script (to add) | Blocked (needs runs) |
| **Trajectory diagnostics are heuristic.** | Present mock calibration as engineering; commit to human agreement study; open-source scorer version. | C3 human κ | §5 Metrics; §8 Human Val | Human validation | Blocked |
| **No human validation.** | Protocol exists; commit to n≥100 stratified sample before claims C3/C10. | table5, annotation export | §8 | `export-human-validation` | Blocked |
| **No frontier model results.** | Commit to pilot with named mid-tier + one frontier if budget allows; pre-register models. | Complete pilot run metadata | §6 Setup; §7 | `pilot_multi_provider_20` | **Not started** |
| **AgentBench/WebArena/GAIA exist.** | Table: we add **paired interventions + trajectory diagnostics + ACRS**; they measure success in rich envs without isolated skill factors. | Related work checklist | §2 Related Work | — | Partial |
| **Interventions change multiple factors.** | Cite automated + human audit; publish failure examples; isolation audit pass rate. | Audit reports, human sample | §4; Appendix | Isolation audit ✅ | Partial (auto only) |
| **Dataset can be gamed.** | Held-out templates, contamination audit, leaderboard policy, no public test prompts. | `audit-contamination`, freeze manifest | §3; Ethics | Contamination audit | Partial |
| **No theoretical contribution.** | Frame as **measurement infrastructure** + empirical regularities (planned); not claiming new identifiability theory. | — | Intro; Limitations | — | OK (framing) |
| **Engineering, not science.** | Separate engineering (C9) from empirical claims; submit when pilot + human validation complete. | Provider pilot tables | §7 Results | Pilot run | Blocked |

## Rebuttal tone guidelines

- Never cite stub/mock/interrupted runs as LLM behavior.
- Offer artifacts (audit reports, frozen data) even when results pending.
- Propose concrete timeline (30/90 day) if asked for roadmap.

## Cross-links

- [REVIEWER_ATTACK_MATRIX.md](REVIEWER_ATTACK_MATRIX.md)
- [paper/EVIDENCE_GAP_MAP.md](../paper/EVIDENCE_GAP_MAP.md)
- [paper/REVIEWER_PACKET.md](../paper/REVIEWER_PACKET.md)
