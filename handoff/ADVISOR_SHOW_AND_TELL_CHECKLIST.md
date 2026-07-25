# Advisor Show-and-Tell Checklist

Use this for a **10–20 minute advisor/co-author meeting**. Every item is safe to share if you state the caveat aloud.

---

## 1. MASTER_STATUS.md

| | |
|---|---|
| **Why show** | Single answer to "what is built vs missing?" |
| **What to say** | "Infrastructure is build-infrastructure-ready; empirical claims are still planned." |
| **Caveat** | Not submission-ready; classification is pre-experiment |
| **Ask advisor** | Is the scope right for a first paper, or should we narrow interventions? |

## 2. PROJECT_HEALTH.md

| | |
|---|---|
| **Why show** | Traffic-light honesty — green infra, red real experiments |
| **What to say** | "Code, docs, and evidence safety are green; provider pilot and human validation are blocked." |
| **Caveat** | Health dashboard reflects engineering state, not scientific success |
| **Ask advisor** | Which blocked area should we prioritize after this meeting? |

## 3. ONE_PAGE_PROJECT_BRIEF.md

| | |
|---|---|
| **Why show** | Fast orientation for someone new |
| **What to say** | Walk through problem → intervention design → ACRS in 2 minutes |
| **Caveat** | Empirical claims in brief are *proposed*, not demonstrated |
| **Ask advisor** | Is the problem framing compelling for NeurIPS-style venue? |

## 4. ADVISOR_HANDOFF_PACKET.md

| | |
|---|---|
| **Why show** | Deeper context if they want to read async |
| **What to say** | "Full packet for follow-up; we won't cover everything live." |
| **Caveat** | Long — use selectively |
| **Ask advisor** | What sections need the most revision before experiments? |

## 5. docs/diagrams/benchmark_flow.mmd

| | |
|---|---|
| **Why show** | Visual: base task → clean/intervention → trajectory → metrics |
| **What to say** | Paste into Mermaid Live or show DIAGRAMS_README |
| **Caveat** | Schematic — not backed by results yet |
| **Ask advisor** | Does the evaluation flow match how they'd expect causal skill claims? |

## 6. docs/EXAMPLE_WALKTHROUGHS.md

| | |
|---|---|
| **Why show** | Concrete synthetic examples (travel + tool failure, etc.) |
| **What to say** | "These illustrate design intent — not empirical findings." |
| **Caveat** | Synthetic only |
| **Ask advisor** | Are intervention families diverse enough? Missing families? |

## 7. demo/ENGINEERING_DEMO_BUNDLE.md

| | |
|---|---|
| **Why show** | Proof the pipeline runs end-to-end on mock data |
| **What to say** | "We ran a 13-second mock micro run; diagnostics fired as expected." |
| **Caveat** | **NOT real LLM behavior** — mock agent only |
| **Ask advisor** | Is mock validation sufficient before spending on provider pilot? |

## 8. paper/EVIDENCE_GAP_MAP.md

| | |
|---|---|
| **Why show** | Maps C1–C10 to missing evidence |
| **What to say** | "Every main claim is planned; here's what each needs." |
| **Caveat** | Honest gap map — may look incomplete |
| **Ask advisor** | Which claims to prioritize in first pilot? |

## 9. reviews/MOCK_REVIEW_SUMMARY.md

| | |
|---|---|
| **Why show** | Anticipated reviewer objections |
| **What to say** | "We simulated skeptical reviews to guide experiments." |
| **Caveat** | AI-generated reviews, not real |
| **Ask advisor** | Which mock rejection reasons worry them most? |

## 10. experiments/SAFE_NEXT_RUN_DECISION_TREE.md

| | |
|---|---|
| **Why show** | Shows disciplined next steps by time/budget |
| **What to say** | "Next real move is provider pilot after approval — not more building." |
| **Caveat** | Decision tree assumes you stop overbuilding |
| **Ask advisor** | Approve provider pilot scale (20 tasks, 3 agents)? Budget range? |

---

## Live demo commands (safe — no model runs in meeting)

```bash
make fast-check
python3 scripts/generate_master_status.py
python3 -m causal_agent_bench plan-run --config configs/pilot_stub_micro_3.yaml
cat demo/ENGINEERING_DEMO_BUNDLE.md | head -40
```

Optional: open `results/20260520T072032Z_pilot_mock_diagnostic_micro/failure_gallery.md` and label it **engineering mock only**.

---

## Do NOT show as empirical evidence

- Exported paper_assets figures from mock run
- Any table with performance numbers without "engineering only" label
- Root `figures/` from older exports

See [ADVISOR_REVIEW_BUNDLE_INDEX.md](ADVISOR_REVIEW_BUNDLE_INDEX.md).
