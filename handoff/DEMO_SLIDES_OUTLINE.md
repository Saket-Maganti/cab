# Demo Slides Outline (8–12 slides)

Markdown outline only — **no PPTX**. Pair with [ADVISOR_DEMO_SCRIPT.md](ADVISOR_DEMO_SCRIPT.md).

---

## Slide 1 — Title

**When Agent Success Is Not Agent Skill: CausalAgentBench**  
Subtitle: Interventional benchmark for tool-using LLM agents  
Footer: Research scaffold — empirical claims planned

---

## Slide 2 — Problem

- Tool-using agents scored on final success
- Hidden failures: wrong tools, bad memory trust, no recovery, early stop
- Need skill-level measurement under stress

---

## Slide 3 — Existing evaluation gap

- AgentBench, WebArena, GAIA: rich environments, aggregate success
- Gap: **paired interventions** + trajectory diagnostics + explicit evidence policy
- Related work table (no performance comparison yet)

---

## Slide 4 — Core idea

- Same base task → clean instance + intervention instance
- One designed factor changes per intervention family
- Bounded "interventional" language (not deployment causal inference)

---

## Slide 5 — Benchmark design

- 8 domains, 10 intervention families, synthetic deterministic tools
- Frozen pilot v0.1; main candidate 500 tasks
- Automated + isolation audits

---

## Slide 6 — Intervention examples

- Tool failure (travel)
- Memory corruption (calendar/email)
- Visual: `paper/latexpaper/figures/figure2_intervention_pairing_placeholder.png` (**schematic**)

---

## Slide 7 — Metrics

- Final success vs trajectory diagnostics
- ACRS composite (concept diagram — placeholder figure)
- Failure taxonomy F01–F15

---

## Slide 8 — Repository / artifact status

- What exists: generator, runner, scoring, release manifest, claim ledger, CI
- Evidence levels policy; mock diagnostics for detector wiring
- `make fast-check` passes (~40s)

---

## Slide 9 — Evidence still missing

- No provider pilot results
- No human validation
- C1–C8/C10: **planned**
- Submission readiness: **False**

---

## Slide 10 — Roadmap

- 30 days: advisor feedback → provider pilot
- 90 days: human validation → main gate decision
- Target: NeurIPS D&B or ED track (hypothesis)

---

## Slide 11 — Feedback requested

- Problem framing, benchmark validity, evidence bar, track fit
- Required experiments before empirical claims

---

## Slide 12 — Appendix (optional)

- Repo map, docs hub, handoff packet QR/path
- Contact / repo URL

**Do not include fake result charts or model rankings.**
