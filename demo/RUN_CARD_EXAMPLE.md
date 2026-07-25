# Run Card Example — Phase 9 Mock Diagnostic Micro

**⚠️ ENGINEERING ONLY — mock_diagnostic_only — NOT REAL LLM EVIDENCE**

| Field | Value |
|---|---|
| **Run ID** | `20260520T072032Z_pilot_mock_diagnostic_micro` |
| **Config** | `configs/pilot_mock_diagnostic_micro.yaml` |
| **Config hash** | `a2f790a475806c7c` |
| **Dataset** | `data/processed/pilot_v0_1/pilot_20_instances.jsonl` (3 instances used) |
| **Dataset version** | `pilot_v0.1` |
| **Evidence level** | `mock_diagnostic_only` |
| **Evidence scope** | `mock_diagnostic_only` |
| **scientific_evidence** | `false` |
| **not_real_llm_behavior** | `true` |
| **Agent list** | `mock_tool_overuser` |
| **Provider type** | `mock` (mock_behavior_agent — no API) |
| **Paid-call status** | `paid_calls_made: false`, `allow_paid_calls: false` |
| **Oracle agents** | none |
| **Completion status** | complete (3/3 trajectories) |
| **Metrics available** | yes (deterministic heuristic; n=3) |
| **Paper assets exported** | yes — `eligible_for_paper_claims: false` |

## Allowed claims

- "Mock diagnostic run completed the end-to-end pipeline"
- "Trajectory diagnostics detected expected mock failure patterns"
- "Scoring and export paths work for engineering validation"
- C9 **engineering_only** (pipeline reproducibility) — do not upgrade

## Forbidden claims

- "LLM agents fail on CausalAgentBench"
- "Clean success overestimates robustness" (C1)
- "Model rankings change under ACRS" (C4)
- Any performance percentage as scientific result
- Use of exported figures/tables in submission paper

## Key paths

- Run dir: `results/20260520T072032Z_pilot_mock_diagnostic_micro/`
- Report: `report.md`
- Failure gallery: `failure_gallery.md`
- Manifest: `paper_assets/paper_assets_manifest.json`

See [ENGINEERING_DEMO_BUNDLE.md](ENGINEERING_DEMO_BUNDLE.md).
