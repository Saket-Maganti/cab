# NeurIPS Paper Blueprint

**Working title candidates**

1. *When Agent Success Is Not Agent Skill: An Interventional Benchmark for Tool-Using Agents*
2. *Causal Agent Bench: Measuring Robustness of Tool-Using Agents Under Controlled Perturbations*
3. *Beyond Final Success: Interventional Evaluation of Planning, Tools, Memory, and Recovery in LLM Agents*

**Status:** Method/design skeleton ready · **Empirical results BLOCKED** · **NOT NeurIPS-ready**

---

## Abstract skeleton (forbidden empirical wording until Stage F)

**Allowed framing:**

> Tool-using language agents are increasingly scored by final task success, but such scores conflate planning, tool use, memory, observation interpretation, recovery, and stopping. We introduce **Causal Agent Bench (CAB)**, an interventional benchmark pairing clean tasks with controlled perturbations targeting individual skill components. CAB defines Agent Causal Robustness Score (ACRS) and trajectory-level diagnostics alongside deterministic simulated tools, split policy, and evidence-governance infrastructure. **Empirical results from completed non-oracle provider runs are not yet reported.** We describe the benchmark design, intervention taxonomy, evaluation protocol, and reproducibility artifact planned for a future multi-provider study over [N] tasks and [K] model families.

**Forbidden until eligible runs exist:**

- Degradation percentages, ranking correlations (ρ), "we show/find/demonstrate" on model behavior
- Human agreement statistics
- "State-of-the-art", "validated benchmark", "NeurIPS-ready"

---

## 1. Introduction — argument

| Beat | Content |
|------|---------|
| Problem | Final success conflates distinct agentic skills |
| Gap | Existing benchmarks rarely isolate causal factors |
| Hypothesis | Clean success overestimates robust competence (C1 — **planned**) |
| Contribution | Interventional design + ACRS + open artifact |
| Honesty | Empirical evaluation staged; results section blocked |

**LaTeX:** `paper/latexpaper/sections/01_introduction.tex`

---

## 2. Contributions (current vs future)

| Contribution | Type | Status |
|--------------|------|--------|
| Interventional evaluation design | Method | Draft-ready |
| CAB benchmark + frozen pilot data | Artifact | Pilot scale |
| ACRS + trajectory diagnostics | Metric | Definition-ready |
| Reproducible package + evidence gates | Artifact | Engineering (C9) |
| Clean vs intervention degradation | Empirical | **BLOCKED (C1)** |
| Ranking instability under ACRS | Empirical | **BLOCKED (C4)** |
| Human-validated diagnostics / interventions | Empirical | **BLOCKED (C3, C10)** |

---

## 3. Related work map

| Area | CAB positioning | Section |
|------|-----------------|---------|
| Tool-using agent benchmarks | Adds paired interventions | §2 Related Work |
| Agent benchmarks (WebArena, SWE-bench, etc.) | Skill decomposition + causal perturbations | §2 |
| Robustness / stress testing | Controlled taxonomy vs ad-hoc noise | §2, §4 |
| Process/trajectory evaluation | ACRS + component metrics | §5 |
| Reproducibility in ML | Evidence-level policy + claim ledger | §11, artifact |

---

## 4. Benchmark design (§3)

- Task domains and template registry
- Clean/intervention pairing protocol
- Simulated tool environment (deterministic)
- Split policy (`release_disjoint_v1`)
- Mini-study (template vs naturalistic) — **results blocked**

---

## 5. Dataset construction (§3 + appendix)

- Generation pipeline, seeds, quality filters
- Frozen `pilot_v0.1`; main_200/main_500 **not ready**
- Leakage controls (0 blocker clusters — static)
- Human audit queue for intervention validity

---

## 6. Intervention taxonomy (§4)

- 17 families from `configs/intervention_taxonomy.yaml`
- Intended causal factor per family
- Isolation audit (static) — not expert proof (C10 blocked)
- High-risk manual-review queue

---

## 7. Metrics (§5)

- Clean / intervention success
- Absolute & relative degradation
- ACRS definition
- Trajectory component metrics
- Statistical reporting plan (see `docs/STATISTICAL_ANALYSIS_PLAN.md`)

---

## 8. Experiment setup (§6) — **PLANNED NOT COMPLETED**

```
Stage A → no-run governance (current)
Stage B → tiny approved pilot (≤5 trajectories)
Stage C → 20-task multi-provider pilot
Stage D → 100-task intermediate
Stage E → main_200
Stage F → main_500
Stage G → human validation
Stage H → paper asset export
```

See `experiments/NEURIPS_EXPERIMENT_MATRIX.md`. **No completed provider main experiment.**

---

## 9. Results (§7) — **BLOCKED**

All subsections placeholder-only:

- RQ1: Clean vs intervention degradation (C1) — **BLOCKED**
- RQ2: Intervention-family breakdown (C2) — **BLOCKED**
- RQ3: ACRS ranking changes (C4) — **BLOCKED**
- RQ4: Trajectory disagreement (C3) — **BLOCKED**
- RQ5: Failure-mode distribution (C7, C8) — **BLOCKED**

`paper/latexpaper/generated/07_results.tex` — explicit no-claims banner.

---

## 10. Human validation (§8) — **BLOCKED**

- Protocol: `docs/HUMAN_VALIDATION_MASTER_PROTOCOL.md`
- Table 5 placeholder — **0 annotations**
- C3, C10 unsupported

---

## 11. Ablations (§9) — **BLOCKED**

- Planned matrix: `experiments/NEURIPS_ABLATION_PLAN.md`
- Table 4 placeholder — no provider ablation runs

---

## 12. Limitations (§10)

- Synthetic tasks
- Heuristic scorers
- No provider-backed results yet
- Human validation incomplete
- Main benchmark not frozen

---

## 13. Ethics (§11)

- Synthetic PII policy
- API cost caps
- Annotator compensation (TBD)
- Evidence-level enforcement

---

## 14. Artifact / reproducibility (§11 + supplement)

- Tier 0–5 reproduction (`docs/REPRODUCIBILITY_TIERS.md`)
- Claim ledger + export guards
- No-run report bundle
- **Not** a substitute for provider reproduction

---

## 15. Appendix plan

| Appendix | Content | Status |
|----------|---------|--------|
| A | Full intervention dossier | Ready (static) |
| B | Metric definitions + scorer version | Ready |
| C | Generation config hashes | Pilot ready |
| D | Statistical analysis details | Plan only |
| E | Human validation forms | Templates only |
| F | Extended failure gallery | **Blocked** |
| G | Cost/runtime tables | **Blocked** |
| H | Claim-evidence matrix | Static snapshot |

---

## Paper readiness verdict

| Check | Status |
|-------|--------|
| Method sections draftable | Yes |
| Empirical submission | **NOT READY** |
| NeurIPS submission | **NOT READY** |

See `docs/NEURIPS_SUBMISSION_GATE.md`.
