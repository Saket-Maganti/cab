# NeurIPS Contribution Map

**Purpose:** Separate what CAB contributes today from what remains blocked. This map must not imply empirical results, human validation, or public release readiness.

**Evidence snapshot (2026-06-10):** 0 paper-eligible runs · 0 eligible empirical assets · C1–C8/C10 planned · C9 engineering_only

---

## Conceptual contribution

**What:** Tool-using agent evaluation should decompose skills (planning, tool use, memory, observation interpretation, recovery, stopping) rather than collapsing them into final success.

| Aspect | Status | Paper section | Evidence |
|--------|--------|---------------|----------|
| Problem framing | **Ready (draft)** | §1 Introduction | Motivation text, related work |
| Interventional evaluation hypothesis | **Ready (hypothesis only)** | §4 Framework | No empirical support yet (C1–C8) |
| Causal robustness vs clean success | **Planned** | §7 Results | C1, C4 blocked |

**Reviewer note:** Conceptual claims are method-level. Do not treat hypothesis language as confirmed findings.

---

## Benchmark contribution

**What:** Paired clean/intervention task design with controlled perturbations targeting individual skill components.

| Aspect | Status | Evidence |
|--------|--------|----------|
| Task template registry | **Ready** | `benchmark_specs/task_template_registry.json` |
| Intervention families + pairing | **Ready** | `docs/INTERVENTION_TAXONOMY.md` |
| Simulated tool environment | **Ready** | `docs/TOOL_CALL_PROTOCOL.md` |
| Run orchestration (80+ CLI) | **Ready** | `docs/CLI_REFERENCE.md` |
| Main-scale benchmark configs | **Planned** | `configs/main_200_*.yaml`, `configs/commercial_api_main_500.yaml` — not frozen/released |

---

## Dataset contribution

**What:** Synthetic, deterministically generated agent tasks with frozen pilot bundle and split policy.

| Aspect | Status | Evidence |
|--------|--------|----------|
| `pilot_v0.1` frozen bundle | **Ready (pilot scale)** | `data/frozen/pilot_v0.1/` |
| Split protocol (`release_disjoint_v1`) | **Ready** | `docs/SPLIT_PROTOCOL.md` |
| Leakage tooling (0 blocker clusters) | **Ready** | Static leakage reports |
| `main_200` / `main_v0.1_500` release | **Blocked** | See `docs/DATASET_RELEASE_READINESS.md` |
| Human audit of task quality | **Blocked** | No completed annotations |

---

## Metric contribution

**What:** Agent Causal Robustness Score (ACRS) and trajectory-level diagnostics beyond final-answer success.

| Aspect | Status | Evidence |
|--------|--------|----------|
| Metric definitions | **Ready** | `docs/METRICS.md`, `docs/METRIC_CARD_ACRS.md` |
| Deterministic scoring implementation | **Ready** | `src/causal_agent_bench/metrics/` |
| Mock diagnostic wiring (engineering) | **Ready** | C9 only |
| Empirical ranking / degradation analysis | **Blocked** | C1, C4 — no provider runs |

---

## Artifact contribution

**What:** Open-source reproducible evaluation package with evidence governance.

| Aspect | Status | Evidence |
|--------|--------|----------|
| No-run report bundle | **Ready** | `all-no-run-reports` |
| Claim ledger + export guards | **Ready** | `docs/claim_ledger.json`, `reports/claim_evidence_matrix.md` |
| Release / repro scaffolding | **Ready (dev)** | `release/`, `artifact/` |
| NeurIPS reviewer quickstart | **Ready** | `docs/REVIEWER_QUICKSTART_NEURIPS.md` |
| Provider pilot template + gates | **Ready (template)** | `configs/provider_pilot_tiny_template.yaml` |
| Public v1.0 artifact release | **Blocked** | No Zenodo/HF bundle |

---

## Empirical contribution — **currently blocked**

**What would be claimed:** Clean success overestimates robustness; intervention-family breakdowns; ACRS ranking changes; ablation effects; tool-overuse and premature-stop patterns.

| Claim IDs | Status | Blocker |
|-----------|--------|---------|
| C1–C8 | planned / unsupported | 0 paper-eligible provider/main runs |
| Required artifacts | None eligible | `reports/paper_asset_eligibility.md` |

**Do not write:** "our experiments show…", performance tables, degradation percentages, or model rankings until claim ledger rows move to `supported` with linked run dirs.

---

## Human-validation contribution — **currently blocked**

**What would be claimed:** Trajectory diagnostics catch failures final scoring misses (C3); interventions isolate intended skills (C10).

| Aspect | Status | Blocker |
|--------|--------|---------|
| Protocol + export tooling | Ready | — |
| Completed annotations | **Missing** | No `data/human_validation/completed*` |
| Agreement statistics (κ, etc.) | **Missing** | Table 5 placeholder |
| C3, C10 promotion | **Blocked** | Human validation incomplete |

---

## Release contribution — **currently blocked**

**What would be claimed:** Public benchmark v1.0 with frozen main split, leaderboard, and downloadable dataset.

| Aspect | Status | Blocker |
|--------|--------|---------|
| Code + docs in repo | Ready | — |
| `benchmark_status` | `research_scaffold` | `release/release_manifest.json` |
| Frozen main benchmark | Blocked | main_200 / main_v0.1_500 |
| Leaderboard with provider results | Blocked | No eligible runs |
| External archival (Zenodo/HF) | Blocked | Release checklist incomplete |

---

## Contribution decision gate

Promotion rules (all must pass):

1. Claim ledger row → `supported` with linked `run_dir` and artifacts.
2. `reports/claim_evidence_matrix.json` → `eligible_run_count > 0` for empirical claims.
3. `reports/paper_asset_eligibility.json` → asset `eligible_for_paper_claims: true`.
4. Human validation complete for C3/C10 before intervention-validity language.
5. Signed approval docs before any `*_APPROVED.yaml` or `allow_paid_calls: true`.

Cross-reference: [paper/CONTRIBUTION_MAP.md](../paper/CONTRIBUTION_MAP.md), [docs/claim_ledger.json](claim_ledger.json), [docs/DO_NOT_OVERCLAIM.md](DO_NOT_OVERCLAIM.md).
