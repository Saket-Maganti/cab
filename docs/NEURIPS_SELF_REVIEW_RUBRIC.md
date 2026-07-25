# NeurIPS Self-Review Rubric

**Purpose:** Conservative self-audit for Datasets/Evaluations-track submission readiness. Scores are **1–5** (1 = missing, 5 = venue-ready). This is not a prediction of acceptance.

**Evidence snapshot:** 0 paper-eligible runs · 0 eligible empirical assets · infrastructure strong · empirical blocked

---

## 1. Significance

| Field | Assessment |
|-------|------------|
| **Current score** | **3 / 5** |
| **Why** | Problem (final success conflates agent skills) is timely and well-motivated for tool-using agents. |
| **Blocker** | No empirical demonstration that CAB changes how we evaluate or rank models. |
| **Exact upgrade needed** | Complete Tier 4 multi-provider main run; show C1 degradation and C4 ranking shift with CIs. |

---

## 2. Novelty

| Field | Assessment |
|-------|------------|
| **Current score** | **3 / 5** |
| **Why** | Paired interventional design + ACRS + trajectory diagnostics is a coherent novel package at method level. |
| **Blocker** | Similar themes exist in agent benchmarks; empirical differentiation not shown. |
| **Exact upgrade needed** | Headline results + human-validated examples showing diagnostics catch failures final scoring misses (C3). |

---

## 3. Dataset quality

| Field | Assessment |
|-------|------------|
| **Current score** | **2.5 / 5** |
| **Why** | Pilot frozen bundle with leakage tooling and split policy; automated QA implemented. |
| **Blocker** | Synthetic-only; main scale not frozen; human task-quality audit incomplete. |
| **Exact upgrade needed** | Freeze `main_v0.1_500`, complete human audit sample, document failure modes with audited examples. |

---

## 4. Benchmark validity

| Field | Assessment |
|-------|------------|
| **Current score** | **2.5 / 5** |
| **Why** | Intervention taxonomy and isolation audit tooling exist; pairing protocol documented. |
| **Blocker** | C10 (interventions isolate skills) unsupported; no expert validation annotations. |
| **Exact upgrade needed** | Tier 5 human validation + intervention expert audit; publish agreement stats. |

---

## 5. Evaluation rigor

| Field | Assessment |
|-------|------------|
| **Current score** | **2 / 5** |
| **Why** | Metric definitions, statistical reporting guide, and evidence-level policy are strong. |
| **Blocker** | Zero provider-backed non-oracle runs; no uncertainty quantification on real agents. |
| **Exact upgrade needed** | Tier 3–4 provider runs with multi-seed, confidence intervals, oracle excluded from rankings. |

---

## 6. Reproducibility

| Field | Assessment |
|-------|-------|
| **Current score** | **4 / 5** |
| **Why** | 80+ CLI, no-run bundle, claim ledger, config hashes, artifact scripts, reproducibility tiers documented. |
| **Blocker** | No lockfile pinned in repo; RUN_INDEX may be stale; provider reproduction blocked. |
| **Exact upgrade needed** | Add dependency lockfile; refresh RUN_INDEX; publish Tier 3+ reproduction path after approval. |

---

## 7. Artifact usability

| Field | Assessment |
|-------|------------|
| **Current score** | **4 / 5** |
| **Why** | Reviewer quickstart, NeurIPS checklist, contribution map, benchmark manifest, attack matrix. |
| **Blocker** | Public release bundle (Zenodo/HF) not shipped; broad `make test` not default safe path. |
| **Exact upgrade needed** | Ship `release/` bundle with frozen data; Docker optional path; clearer safe-command index in README. |

---

## 8. Ethical clarity

| Field | Assessment |
|-------|------------|
| **Current score** | **4 / 5** |
| **Why** | Synthetic PII policy, cost caps, ethics section, security doc, annotator compensation placeholder flagged. |
| **Blocker** | Compensation details unfilled; live API cost risk until pilot audited. |
| **Exact upgrade needed** | Fill compensation paragraph before human validation; document actual pilot spend. |

---

## 9. Limitations honesty

| Field | Assessment |
|-------|------------|
| **Current score** | **5 / 5** |
| **Why** | `DO_NOT_OVERCLAIM`, placeholder results section, abstract guard, 0 eligible runs stated consistently. |
| **Blocker** | None for honesty — maintain discipline after empirical runs arrive. |
| **Exact upgrade needed** | Keep claim-evidence matrix synchronized after any pilot; resist premature promotion. |

---

## 10. Empirical completeness

| Field | Assessment |
|-------|------------|
| **Current score** | **1 / 5** |
| **Why** | C1–C8 and C10 are planned; no provider-backed scientific evidence. |
| **Blocker** | Entire empirical contribution path blocked. |
| **Exact upgrade needed** | Tier 3 pilot → Tier 4 main → Tier 5 human validation → claim ledger promotion. |

---

## Aggregate conservative summary

| Category | Score |
|----------|-------|
| Significance | 3.0 |
| Novelty | 3.0 |
| Dataset quality | 2.5 |
| Benchmark validity | 2.5 |
| Evaluation rigor | 2.0 |
| Reproducibility | 4.0 |
| Artifact usability | 4.0 |
| Ethical clarity | 4.0 |
| Limitations honesty | 5.0 |
| Empirical completeness | 1.0 |
| **Mean (excluding honesty as gating)** | **~2.9** |

**Interpretation:** Strong **artifact/infrastructure** candidate for method-forward review; **not** an empirical results paper yet. Honesty score is high by design — do not trade it for premature claim language.

---

## Reviewer-facing statement (safe to quote)

> Causal Agent Bench provides a NeurIPS-style benchmark artifact scaffold with frozen pilot data, interventional design, evidence governance, and reproducibility tooling. Empirical claims (C1–C8, C10) remain unsupported with 0 paper-eligible provider runs. Human validation and public v1.0 release are blocked.
