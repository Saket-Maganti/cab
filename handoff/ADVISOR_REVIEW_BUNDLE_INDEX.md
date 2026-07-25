# Advisor Review Bundle Index

Exact files to send or screen-share with an advisor/co-author. **All are safe to share** if you include the caveats column — none contain API keys or fake empirical results.

| File | Why it matters | Status | Safe to share? | Caveats |
|---|---|---|---|---|
| [ONE_PAGE_PROJECT_BRIEF.md](ONE_PAGE_PROJECT_BRIEF.md) | 60-second project summary | current | yes | Says scaffold, not results |
| [ADVISOR_HANDOFF_PACKET.md](ADVISOR_HANDOFF_PACKET.md) | Full context packet | current | yes | Evidence gaps explicit |
| [ADVISOR_DEMO_SCRIPT.md](ADVISOR_DEMO_SCRIPT.md) | 10–15 min live demo flow | current | yes | Uses plan/audit only in demo |
| [DEMO_SLIDES_OUTLINE.md](DEMO_SLIDES_OUTLINE.md) | Slide outline (no PPT) | current | yes | No filled result numbers |
| [../paper/CONTRIBUTION_MAP.md](../paper/CONTRIBUTION_MAP.md) | Contributions ↔ evidence | current | yes | Most contributions planned |
| [../paper/EVIDENCE_GAP_MAP.md](../paper/EVIDENCE_GAP_MAP.md) | C1–C10 gap analysis | current | yes | Honest about missing runs |
| [../reviews/MOCK_REVIEW_SUMMARY.md](../reviews/MOCK_REVIEW_SUMMARY.md) | Simulated reviewer risks | current | yes | Synthetic reviews, not real |
| [../docs/BENCHMARK_TAXONOMY.md](../docs/BENCHMARK_TAXONOMY.md) | Skills, domains, interventions | current | yes | Design doc, not results |
| [../docs/EVIDENCE_LEVEL_POLICY.md](../docs/EVIDENCE_LEVEL_POLICY.md) | What claims each level allows | current | yes | Policy reference |
| [../MASTER_STATUS.md](../MASTER_STATUS.md) | Single master status file | current | yes | Pre-experiment freeze state |
| [PROFESSOR_READY_CHECKLIST.md](PROFESSOR_READY_CHECKLIST.md) | Show-to-advisor gate | current | yes | Blocked items listed |
| [../PROJECT_HEALTH.md](../PROJECT_HEALTH.md) | Traffic-light dashboard | current | yes | Red = blocked experiments |
| [../docs/DO_NOT_OVERCLAIM.md](../docs/DO_NOT_OVERCLAIM.md) | Wording guardrails | current | yes | For you and advisor |
| [../PROJECT_FULL_CURRENT_AUDIT_FOR_OPUS.md](../PROJECT_FULL_CURRENT_AUDIT_FOR_OPUS.md) | Full static audit dossier | current | yes | No empirical claims; post-calibration leakage |
| [../docs/COMMAND_AND_RUNTIME_GUIDE.md](../docs/COMMAND_AND_RUNTIME_GUIDE.md) | Safe vs unsafe commands | current | yes | Provider runs blocked until APPROVED |
| Generated `advisor_review/advisor_one_page_summary.md` | One-page advisor handout | after `all-no-run-reports` | yes | Regenerate before meetings |
| Generated `publication_readiness/publication_readiness.md` | Venue-tier honesty map | after `all-no-run-reports` | yes | All main venues blocked today |
| [../GOD_TIER_MANIFEST.md](../GOD_TIER_MANIFEST.md) | God-tier manifest (infra vs evidence) | current | yes | No empirical claims |
| `python3 scripts/god_tier_status.py` | One-screen status banner | on demand | yes | Regenerate before meetings |

**Regenerate bundle before meetings:**

```bash
python3 -m causal_agent_bench all-no-run-reports --output-dir /tmp/cab_advisor_$(date +%Y%m%d)
python3 scripts/god_tier_status.py
```

Meeting date reviewed: ____________

## Recommended share order

1. **Email/async:** ONE_PAGE_PROJECT_BRIEF + `PROJECT_FULL_CURRENT_AUDIT_FOR_OPUS.md` + EVIDENCE_GAP_MAP
2. **Meeting prep:** ADVISOR_DEMO_SCRIPT + DEMO_SLIDES_OUTLINE
3. **Live demo:** fast-check → plan-run → audit-dataset → diagrams/walkthroughs
4. **Deep dive (optional):** ADVISOR_HANDOFF_PACKET + BENCHMARK_TAXONOMY + MOCK_REVIEW_SUMMARY

## Do not share as empirical evidence

- Anything under `results/` without labeling evidence level
- Root `figures/` or `tables/` from old exports (may predate claim policy)
- Mock/stub run outputs described as "model performance"

## Questions to ask the advisor

See [PROFESSOR_READY_CHECKLIST.md](PROFESSOR_READY_CHECKLIST.md) — intervention design, ACRS, pilot scale, human validation protocol, related work.
