# Engineering Demo Bundle

**⚠️ ENGINEERING ONLY — NOT REAL LLM EVIDENCE — DO NOT USE FOR PAPER CLAIMS**

This bundle documents a **Phase 9 mock diagnostic micro run** that validates the end-to-end CausalAgentBench pipeline without calling any real LLM, Ollama, or paid API.

---

## Project thesis

Final task success can hide which agentic skills survive under controlled interventions. CausalAgentBench pairs clean and intervention instances to measure robustness beyond final-answer scoring (ACRS + trajectory diagnostics).

---

## What this demo proves

- Config → run → score → analyze → export → report → failure gallery works end-to-end
- Mock diagnostic agent (`mock_tool_overuser`) runs deterministically in ~13 seconds
- Trajectory diagnostics detect scripted failure patterns (tool overuse, invalid calls, etc.)
- Paper asset export sets `eligible_for_paper_claims: false` and `engineering_only: true`
- Evidence safety and claim ledger remain valid after the run

---

## What this demo does NOT prove

- Real LLM agent behavior, rankings, or generalization
- C1–C8 or C10 empirical claims
- Human validation or NeurIPS-ready results
- That "agents fail" on the benchmark — only that **mock instrumentation works**

---

## Run details

| Field | Value |
|---|---|
| **Run directory** | `results/20260520T072032Z_pilot_mock_diagnostic_micro` |
| **Config** | `configs/pilot_mock_diagnostic_micro.yaml` |
| **Evidence level** | `mock_diagnostic_only` |
| **scientific_evidence** | `false` |
| **not_real_llm_behavior** | `true` |
| **paid_calls_made** | `false` |
| **provider_type** | `mock` |
| **Status** | complete (3/3 trajectories) |
| **Runtime** | ~13 seconds |

---

## Agent behavior

- **Agent:** `mock_tool_overuser` (`mock_behavior_agent`)
- **Mode:** scripted `tool_overuser` — deliberately over-calls tools
- **Not a real LLM** — deterministic mock for detector validation

---

## Generated artifacts

| Artifact | Path |
|---|---|
| Trajectories | `trajectories.jsonl` |
| Scores | `scores.jsonl`, `aggregate_scores.json` |
| Analysis | `analysis_report.md` |
| Report | `report.md`, `report.html` |
| Failure gallery | `failure_gallery.md` |
| Paper assets | `paper_assets/` (engineering-only labeled) |
| Error cases | `error_cases/` |

Example figures (engineering-only, n=3):

- `paper_assets/figures/figure2_clean_vs_intervention_success.png`
- `paper_assets/figures/figure3_intervention_family_breakdown.png`

---

## Command sequence (reproducible)

```bash
python3 -m causal_agent_bench plan-run --config configs/pilot_mock_diagnostic_micro.yaml
python3 -m causal_agent_bench run --config configs/pilot_mock_diagnostic_micro.yaml
python3 -m causal_agent_bench score --run-dir results/20260520T072032Z_pilot_mock_diagnostic_micro
python3 -m causal_agent_bench analyze --run-dir results/20260520T072032Z_pilot_mock_diagnostic_micro
python3 -m causal_agent_bench export-paper-assets --run-dir results/20260520T072032Z_pilot_mock_diagnostic_micro --allow-engineering-only --no-write-global
python3 -m causal_agent_bench generate-report --run-dir results/20260520T072032Z_pilot_mock_diagnostic_micro
python3 -m causal_agent_bench failure-gallery --run-dir results/20260520T072032Z_pilot_mock_diagnostic_micro
```

---

## Limitations

- n=3 trajectories; single domain slice (travel_planning)
- One mock agent; no multi-model comparison
- Heuristic scoring only; no human audit
- Exported tables/figures must **not** replace paper placeholders

---

## Next real experiment

After advisor review and budget approval:

1. Complete `experiments/PRE_EXPERIMENT_FREEZE_CHECKLIST.md`
2. Run bounded provider pilot: `configs/pilot_multi_provider_20.yaml`
3. Export human validation sample

---

## Machine-readable bundle

See [engineering_demo_bundle.json](engineering_demo_bundle.json).

Related: [RUN_CARD_EXAMPLE.md](RUN_CARD_EXAMPLE.md) · [AGENT_CARD_EXAMPLE.md](AGENT_CARD_EXAMPLE.md)
