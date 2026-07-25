# Professor-Ready Checklist

Use before showing the repository to an advisor or co-author. **Not submission-ready** — honest engineering scaffold with clear evidence gaps.

Classifications: **ready** · **partial** · **blocked** · **n/a**

| Item | Status | Notes |
|---|---|---|
| Can install (`pip install -e ".[dev]"`) | ready | Python 3.11+; see README pyenv note |
| `make fast-check` passes | ready | ~40s, no model runs |
| README clear (problem, scope, limits) | ready | Quick safe demo section |
| Docs navigation clear | ready | [docs/README.md](../docs/README.md) hub |
| Project brief ready | ready | [ONE_PAGE_PROJECT_BRIEF.md](ONE_PAGE_PROJECT_BRIEF.md) |
| Demo script ready | ready | [ADVISOR_DEMO_SCRIPT.md](ADVISOR_DEMO_SCRIPT.md) (~10–15 min) |
| Slide outline ready | ready | [DEMO_SLIDES_OUTLINE.md](DEMO_SLIDES_OUTLINE.md) |
| Architecture diagrams | ready | [docs/diagrams/](../docs/diagrams/) |
| Example walkthroughs (synthetic) | ready | [EXAMPLE_WALKTHROUGHS.md](../docs/EXAMPLE_WALKTHROUGHS.md) |
| Claims honest (C1–C8 planned) | ready | [claim_ledger.json](../docs/claim_ledger.json) |
| Evidence gap documented | ready | [EVIDENCE_GAP_MAP.md](../paper/EVIDENCE_GAP_MAP.md) |
| No fake empirical results | ready | Placeholders labeled; mock=engineering only |
| No secrets in repo | ready | `.env` gitignored; `security-check` |
| Interrupted runs marked | partial | Some interrupted runs in index; not used as evidence |
| Provider pilot complete | blocked | Required for empirical claims |
| Human validation complete | blocked | Required for C3, C10 |
| Paper numbers filled | blocked | Placeholders remain |
| Main experiment gate | blocked | [MAIN_EXPERIMENT_GATE.md](../experiments/MAIN_EXPERIMENT_GATE.md) NO-GO |
| Repro bundle published | n/a | Planned post-pilot |
| NeurIPS submission | blocked | Target 2027 roadmap |

## Safe demo flow (10 minutes)

```bash
make fast-check
python3 scripts/generate_project_status.py
python3 -m causal_agent_bench plan-run --config configs/pilot_stub_micro_3.yaml
python3 -m causal_agent_bench audit-dataset --config configs/pilot_stub_micro_3.yaml
python3 scripts/check_submission_readiness.py
python3 scripts/audit_repo_consistency.py
```

Show: [docs/diagrams/benchmark_flow.mmd](../docs/diagrams/benchmark_flow.mmd), [EXAMPLE_WALKTHROUGHS.md](../docs/EXAMPLE_WALKTHROUGHS.md), [EVIDENCE_GAP_MAP.md](../paper/EVIDENCE_GAP_MAP.md).

## Advisor questions to invite

1. Is the intervention pairing design sufficient for causal skill claims?
2. Is ACRS the right composite, or should we emphasize per-family diagnostics?
3. What pilot scale (N tasks, K agents) before committing to main 500?
4. Human validation: trajectory-level vs outcome-level — minimum viable protocol?
5. Which related-work baselines are mandatory for NeurIPS credibility?

## What not to claim in the meeting

- Frontier model performance or rankings
- That C1–C8 are supported
- That the benchmark is submission-ready
- That mock/stub runs reflect real LLM behavior

See [ADVISOR_HANDOFF_PACKET.md](ADVISOR_HANDOFF_PACKET.md) and [PROJECT_STATUS.md](../PROJECT_STATUS.md).
