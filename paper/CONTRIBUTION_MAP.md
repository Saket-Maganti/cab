# Contribution Map

Maps each contribution to paper section, evidence, status, and risk. **Empirical contributions are planned unless real provider/main evidence exists.**

| Contribution | Paper Section | Required Evidence | Current Evidence | Status | Risk |
|---|---|---|---|---|---|
| Interventional evaluation design | §4 Interventional Framework | Audit reports, taxonomy, reviewer packet | `audit-interventions`, isolation audit pass, `docs/BENCHMARK_TAXONOMY.md` | **Method ready (draft)** | Causal wording overreach (R04) |
| CausalAgentBench benchmark | §3 Benchmark Design | Frozen dataset, dataset card, generation reproducibility | `data/frozen/pilot_v0.1/`, template registry | **Artifact ready (pilot scale)** | Synthetic validity (R03) |
| ACRS + trajectory diagnostics | §5 Metrics | Metric definitions, mock diagnostic wiring | `docs/METRICS.md`, mock agents (engineering only) | **Method ready (draft)** | Heuristic scorers (R05) |
| Reproducible evaluation package | §11 Ethics/Repro + artifact | Release manifest, repro scripts, CI, run management, evidence validators | Phase 4–9 release/orchestration, `demo/ENGINEERING_DEMO_BUNDLE.md`, `artifact/` | **Engineering ready (E2E mock validated)** | Packaging drift |
| Clean success overestimates robustness | §7 Results RQ1 | C1: paired runs, CIs, table2/fig2 | Placeholder tables only | **Planned (C1)** | No provider runs (R14) |
| Ranking instability under ACRS | §7 Results RQ2 | C4: ranking correlation, fig4 | None | **Planned (C4)** | Too few models |
| Human validation of interventions/diagnostics | §8 Human Validation | C3/C10: annotations, κ, table5 | Protocol scaffold only | **Planned (C3, C10)** | Delay (R06) |
| Ablations on prompting/scaffolds | §9 Ablations | C5/C6: ablation matrix runs, table4 | Configs exist; no runs | **Planned (C5, C6)** | Scope creep |

## Claim ledger cross-reference

| Claim | Contribution row |
|---|---|
| C1 | Clean success overestimates robustness |
| C2 | Tool failure / memory corruption expose weaknesses |
| C3 | Trajectory metrics vs final success |
| C4 | ACRS changes rankings |
| C5 | Recovery separable from planning |
| C6 | Self-checking selective improvement |
| C7 | Tool overuse |
| C8 | Premature stopping |
| C9 | Smoke reproducibility (engineering_only) |
| C10 | Interventions isolate components |

## Decision gate

Do **not** upgrade any row to "Supported" until `docs/claim_ledger.json` status changes with linked run dirs and artifacts. See [EVIDENCE_GAP_MAP.md](EVIDENCE_GAP_MAP.md).
