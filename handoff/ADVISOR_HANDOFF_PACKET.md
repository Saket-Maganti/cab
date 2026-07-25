# Advisor / Co-Author Handoff Packet

**Project:** CausalAgentBench — *When Agent Success Is Not Agent Skill*  
**Status:** Research scaffold with deterministic prototype; **not submission-ready**  
**Audience:** Advisor, co-author, or senior reviewer doing a feasibility read

---

## One-paragraph summary

CausalAgentBench is a Python research benchmark for tool-using LLM agents that pairs each clean task with controlled intervention variants (tool failure, memory corruption, observation conflict, etc.) so robustness can be measured beyond final-answer success. The repository already implements dataset generation, intervention auditing, deterministic stub/mock agents, scoring (including Agent Causal Robustness Score, ACRS), run management, release packaging, and paper scaffolding. **No provider-scale empirical study has been completed**; claims C1–C8 and C10 remain **planned** in the claim ledger.

## One-sentence thesis

Final task success systematically overstates agent competence unless we evaluate paired clean/intervention trajectories with explicit skill-level diagnostics.

## Why this problem matters

Tool-using agents are deployed in workflows where silent failures (wrong tool, unverified memory, premature stopping) are costly even when the final answer looks acceptable. Existing benchmarks often report aggregate success without isolating which skills break under stress.

## What is already built

| Layer | Status |
|---|---|
| Benchmark generator + frozen pilot v0.1 | Built, audited |
| Intervention isolation audit | Passes on pilot |
| Scoring + ACRS + trajectory metrics | Implemented (heuristic v1) |
| Mock diagnostic agents | Engineering validation only |
| Run limits, status, reports, failure gallery | Built |
| Release manifest, command plans, evidence policy | Phase 4 complete |
| Paper LaTeX scaffold + claim ledger | Draft; placeholders remain |

## What is **not** supported by evidence

- Clean vs intervention performance gaps across real LLM agents (C1)
- Family-level degradation patterns on provider runs (C2)
- Trajectory metrics vs human judgment (C3)
- ACRS ranking changes vs clean success (C4)
- Recovery vs planning separability (C5)
- Self-check ablations (C6)
- Tool overuse / premature stop rates on real agents (C7, C8)
- Expert human validation of intervention validity (C10)

## Current status classification

`local_preliminary` — engineering + interrupted local runs exist; **no provider pilot**; submission readiness **False**.

## Core claims C1–C10

| ID | Status | Notes |
|---|---|---|
| C1–C8 | **planned** | Require provider/main experiments |
| C9 | **engineering_only** | Smoke/repro scaffold |
| C10 | **planned** | Requires human/expert validation |

Full ledger: [docs/claim_ledger.json](../docs/claim_ledger.json). Gap map: [paper/EVIDENCE_GAP_MAP.md](../paper/EVIDENCE_GAP_MAP.md).

## Artifact map

| Artifact | Path |
|---|---|
| Code | `src/causal_agent_bench/` |
| Configs | `configs/` |
| Frozen dataset | `data/frozen/pilot_v0.1/` |
| Docs | `docs/`, `benchmark_specs/` |
| Paper | `paper/` |
| Audits | `audits/` |
| Release | `release/release_manifest.json` |
| Handoff (this packet) | `handoff/` |
| Command plans | `experiments/COMMAND_PLANS.md` |

## What we need from advisor/co-author

1. **Problem framing:** Is interventional robustness the right primary contribution vs another angle?
2. **Benchmark validity:** Are synthetic tools + paired interventions credible for NeurIPS D&B / ED track?
3. **Evidence bar:** Minimum experiment set before any empirical claims (pilot size, models, human validation n)?
4. **Causal wording:** Is our bounded “paired perturbation” language acceptable?
5. **Related work positioning:** AgentBench / WebArena / GAIA / τ-bench — is our contrast sharp enough?

## 30-day plan (build + bounded experiments when approved)

| Week | Focus |
|---|---|
| 1 | Advisor feedback on contribution map + mock reviews |
| 2 | Provider pilot dry-run + budget approval; human validation protocol sign-off |
| 3 | Run bounded provider pilot (20-task config); **do not** update claims until audited |
| 4 | Human validation sample export; revise paper method sections from feedback |

## 90-day plan

| Month | Focus |
|---|---|
| 1 | Pilot + human validation sample |
| 2 | Main frozen dataset run (if gate passes) or expanded pilot |
| 3 | Paper results integration, rebuttal prep, submission checklist |

## Risks and mitigations

See [docs/RISK_REGISTER.md](../docs/RISK_REGISTER.md). Top risks: synthetic criticism (R03), no provider evidence yet (R14), human validation delay (R06), claims exceed evidence (R15). Mitigations: evidence gap map, claim ledger gates, mock reviews.

## Exact next experiment (when resources available)

**First:** Bounded provider pilot — no main run until gate passes.

```bash
python3 -m causal_agent_bench command-plan --experiment provider_pilot
# After approval only:
# python3 -m causal_agent_bench dry-run --config configs/pilot_multi_provider_20.yaml
# python3 -m causal_agent_bench run --config configs/pilot_multi_provider_20.yaml
```

**Not yet:** `main_500_multi_provider.yaml` — blocked by [experiments/MAIN_EXPERIMENT_GATE.md](../experiments/MAIN_EXPERIMENT_GATE.md).

## Related handoff docs

- [ONE_PAGE_PROJECT_BRIEF.md](ONE_PAGE_PROJECT_BRIEF.md)
- [ADVISOR_MESSAGE_DRAFT.md](ADVISOR_MESSAGE_DRAFT.md)
- [paper/CONTRIBUTION_MAP.md](../paper/CONTRIBUTION_MAP.md)
- [reviews/MOCK_REVIEW_SUMMARY.md](../reviews/MOCK_REVIEW_SUMMARY.md)
