# Advisor Demo Script (10–15 minutes)

**Audience:** Professor, co-author, or senior reviewer  
**Goal:** Show what is built vs what evidence is missing — **no model runs during demo**

---

## 0. 30-second pitch

"CausalAgentBench evaluates tool-using agents under paired clean/intervention conditions so we can measure robustness beyond final-answer success. The repo is a complete evaluation scaffold; empirical claims are explicitly **planned**, not yet supported."

---

## 1. Problem statement (2 min)

- Final success conflates planning, tools, memory, recovery, stopping.
- Open [docs/EXAMPLE_WALKTHROUGHS.md](../docs/EXAMPLE_WALKTHROUGHS.md) — one travel + tool failure example.
- Point: same goal, one factor changed, different skill tested.

---

## 2. Why final success is insufficient (1 min)

- Show [docs/TRAJECTORY_EXPLAINER.md](../docs/TRAJECTORY_EXPLAINER.md) synthetic mini-example.
- Mention trajectory vs final-success disagreement (claim C3 — **planned**).

---

## 3. Benchmark design (2 min)

- [docs/BENCHMARK_TAXONOMY.md](../docs/BENCHMARK_TAXONOMY.md) — 8 domains, 10 intervention families.
- Diagram: [docs/diagrams/intervention_pairing.mmd](../docs/diagrams/intervention_pairing.mmd) (paste in Mermaid Live if needed).
- Frozen pilot: `data/frozen/pilot_v0.1/`.

---

## 4. Paired interventions (1 min)

- Isolation audit passed on pilot (engineering QA):
  ```bash
  python3 scripts/audit_intervention_isolation.py --dataset data/frozen/pilot_v0.1/instances.jsonl
  ```
- Human validation for C10 still **planned**.

---

## 5. ACRS and trajectory diagnostics (2 min)

- [docs/METRIC_CARD_ACRS.md](../docs/METRIC_CARD_ACRS.md)
- Placeholder schematic (not a result):
  ```bash
  ls paper/latexpaper/figures/figure3_acrs_concept_placeholder.png
  ```
- Emphasize: **PLACEHOLDER — NOT EMPIRICAL RESULT**

---

## 6. Current repo capabilities (2 min)

Live commands (safe, no `run`):

```bash
make fast-check
python3 -m causal_agent_bench plan-run --config configs/pilot_stub_micro_3.yaml
python3 -m causal_agent_bench audit-dataset --config configs/pilot_stub_micro_3.yaml
python3 scripts/check_submission_readiness.py
```

Optional:

```bash
python3 -m causal_agent_bench build-release-manifest
python3 scripts/lint_paper_claims.py --mode draft
```

Show [docs/REPO_MAP.md](../docs/REPO_MAP.md) or [docs/README.md](../docs/README.md).

### 6b. Governance bundle (2 min) — god-tier differentiator

```bash
python3 scripts/god_tier_status.py
python3 -m causal_agent_bench all-no-run-reports --output-dir /tmp/cab_advisor_demo
```

Open in `/tmp/cab_advisor_demo/`:

- `evidence_dashboard/evidence_dashboard.md` — next action, blockers
- `advisor_review/advisor_one_page_summary.md` — no empirical claims disclaimer
- `publication_readiness/publication_readiness.md` — venue honesty (all main venues blocked)
- `provider_pilot_preflight/provider_pilot_preflight.md` — gate status

Say explicitly: **reports are governance, not empirical results.**

---

## 7. What evidence is missing (2 min)

- Open [paper/EVIDENCE_GAP_MAP.md](../paper/EVIDENCE_GAP_MAP.md) — C1–C8 planned.
- [reviews/MOCK_REVIEW_SUMMARY.md](../reviews/MOCK_REVIEW_SUMMARY.md) — top rejection risks.
- Classification: `local_preliminary`, not submission-ready.

---

## 8. What experiments come next (1 min)

```bash
python3 -m causal_agent_bench command-plan --experiment provider_pilot
```

First run after approval: `configs/pilot_multi_provider_20.yaml` — **not during this demo**.

---

## 9. Feedback requested (1 min)

1. Is interventional robustness the right headline contribution?
2. Minimum evidence bar for a D&B/ED submission?
3. Is synthetic + paired design credible vs WebArena/AgentBench?
4. Human validation sample size and protocol?
5. Track recommendation?

---

## Do NOT run during demo

```bash
# python3 -m causal_agent_bench run --config ...   # any config
# Ollama / paid provider configs
```

Mock/stub trajectories are **engineering_only** — do not describe as model results.

## Leave-behind links

- [ADVISOR_HANDOFF_PACKET.md](ADVISOR_HANDOFF_PACKET.md)
- [ONE_PAGE_PROJECT_BRIEF.md](ONE_PAGE_PROJECT_BRIEF.md)
- [DEMO_SLIDES_OUTLINE.md](DEMO_SLIDES_OUTLINE.md)
