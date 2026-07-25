# Advisor Message Draft (internal — do not send automatically)

**Subject:** Feedback request — CausalAgentBench interventional agent benchmark (pre-pilot)

Hi [Advisor Name],

I'm writing to share a pre-pilot research package for **CausalAgentBench**, a benchmark that evaluates tool-using LLM agents under paired clean/intervention conditions (tool failure, memory corruption, observation conflict, etc.) with trajectory-level diagnostics and an Agent Causal Robustness Score (ACRS).

**What's built:** dataset generator, frozen pilot v0.1, intervention/isolation audits, scoring pipeline, reproducibility/release tooling, and a full paper scaffold with an explicit claim ledger. Stub and mock runs validate engineering only — **no provider-scale results yet**.

**What I'd value your feedback on:**

1. **Problem framing** — Is "clean success overestimates robust competence" the right headline, or should we emphasize diagnostics / benchmark design differently?
2. **Benchmark validity** — Are synthetic tools + single-factor interventions credible for a venue like NeurIPS D&B or ED track, given WebArena/AgentBench/GAIA exist?
3. **Intervention design** — Does our audit + human-validation plan adequately address "you changed more than one thing" critiques?
4. **Evidence bar** — What minimum experiment would you require before empirical claims (e.g., 20-task multi-provider pilot + n=100 human audit)?
5. **Track fit** — Do you see this as D&B, main track methods, or ED track — and what would make it competitive?

I've attached internal docs: `handoff/ADVISOR_HANDOFF_PACKET.md`, `paper/CONTRIBUTION_MAP.md`, and `reviews/MOCK_REVIEW_SUMMARY.md` (simulated harsh reviews).

**Not asking you to endorse results** — there aren't any yet. Claims C1–C8/C10 are marked *planned* in `docs/claim_ledger.json`.

If you have 30 minutes in the next two weeks, I'd appreciate a skim and blunt feedback on whether to proceed to a bounded paid pilot.

Thanks,  
[Your name]

**Attachments (paths in repo):**
- `handoff/ADVISOR_HANDOFF_PACKET.md`
- `handoff/ONE_PAGE_PROJECT_BRIEF.md`
- `paper/EVIDENCE_GAP_MAP.md`
- `reviews/MOCK_REVIEW_SUMMARY.md`
