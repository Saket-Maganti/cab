# NeurIPS Ablation Plan

**Empirical ablation tables:** **BLOCKED UNTIL ELIGIBLE PROVIDER RUNS EXIST**

---

## Fixture-only / engineering checks (no provider)

| Ablation | Config / agent | Purpose | Evidence |
|----------|----------------|---------|----------|
| Mock failure modes | `pilot_mock_agents_failure_modes.yaml` | Detector wiring | engineering_only |
| Stub prompt scaffolds | `configs/ablations/*_local_stub.yaml` | Pipeline check | engineering_only |
| Zero-cost debug matrix | `pilot_zero_cost_debug_matrix.yaml` | Multi-mock debug | engineering_only |
| Metric fixture check | `synthetic-fixture-check` | Scorer unit behavior | engineering_only |
| Oracle sanity | `provider_pilot_oracle_sanity_check_template.yaml` | Upper bound (excluded from claims) | engineering_only |

**These cannot support C5, C6, or any empirical claim.**

---

## Provider-required ablations (Stage D–F)

| Ablation | Agent / condition | Claim | Config direction |
|----------|-------------------|-------|----------------|
| No-tool baseline | Direct answer without tools | Baseline | New baseline agent profile |
| Random tool baseline | `random_tool_agent` | Lower bound | `baseline_suite_local_stub.yaml` → provider |
| Scripted oracle upper bound | `scripted_oracle_agent` | Sanity (exclude from rankings) | oracle sanity template |
| Memory-blind agent | `mock_memory_blind` → LLM variant | C2 component | diagnostic → provider |
| Contradiction-blind agent | `mock_contradiction_blind` | C2 | diagnostic → provider |
| Recovery-disabled agent | Scaffold: no retry policy | C5 | ablation matrix |
| No-final-verifier agent | Scaffold: skip self-check | C6 | `self_check_local_stub` → provider |
| Tool-error ablation | tool_failure family only | C2 | subset filter |
| Dataset-size ablation | 20 / 100 / 200 / 500 slices | Scaling | staged configs |
| Intervention-family ablation | One family at a time | C2 | eval-split filters |
| Metric ablation | Final-only vs +trajectory vs +ACRS | C3,C4 | scorer flags |

---

## Ablation matrix structure

Factorial design (planned) from `configs/ablation_matrix_local_stub.yaml`:

- Self-check on/off
- Explicit plan on/off
- Memory verification on/off
- Tool failure recovery prompt on/off

**Provider cells:** replace stub agents with same scaffold on frozen tasks.

---

## Evidence rules

| Run type | Table 4 use |
|----------|-------------|
| Mock/stub | Appendix engineering only |
| Local Ollama | Preliminary footnote at most |
| Provider complete + eligible | Candidate for C5,C6 |

---

## Gates before ablation spend

1. Main benchmark frozen (Stage E+)
2. Baseline agent profiles validated
3. Budget approval per ablation cell
4. Same scorer version across cells

See `paper/RESULT_TABLES_AND_FIGURES_PLAN.md` (T9).
