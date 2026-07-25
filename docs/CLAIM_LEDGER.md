# Claim Ledger

Every paper claim must be linked to actual experiments or marked as planned/unproven. Do not move a claim to `Supported` without adding run IDs, configs, seeds, and reproducible artifact paths.

Machine-readable companion: `docs/claim_ledger.json` (schema v3 in
`docs/claim_ledger_schema.json`). Schema v3 adds the required study,
validation threshold, validator-derived current state, allowed wording,
forbidden wording, and governed paper locations. Those planning fields do not
promote a claim.

```bash
python scripts/check_claim_ledger.py              # ledger schema + paper claimrefs
python scripts/check_paper_claims.py --list-ids     # claim IDs cited in paper/
python -m causal_agent_bench update-claim-ledger --run-dir results/<run_dir>
```

Run `python scripts/check_claim_ledger.py --mode submission` before treating any claim as submission-ready.

Status meanings:

- `Planned`: required experiment or validation has not been run.
- `Engineering-only`: supported only by smoke/dev artifacts, not scientific evidence.
- `Supported`: backed by final experiment artifacts and audit.
- `Weakened`: evidence contradicts or substantially narrows the claim.

| ID | Claim | Evidence required | Current evidence / artifact | Status | Risk | Minimum figure/table needed |
|---|---|---|---|---|---|---|
| C1 | Clean success overestimates robustness. | Paired clean vs intervention runs across multiple non-oracle agents with confidence intervals; intervention success lower than clean success for credible agents. | Development assets exist at `results/20260510T110807Z_dev_20`, but this run is not a final scientific experiment. | Planned | If gaps are small or inconsistent, the central claim weakens. | Table 2: clean success, intervention success, ACRS by agent. |
| C2 | Tool failure and memory corruption expose hidden weaknesses. | Intervention-family breakdown showing degradation under tool failure and memory corruption; representative trajectories. | Analysis scripts generate family tables/figures, but final run and audit are missing. | Planned | Effects may be template artifacts or dominated by one agent. | Figure 3 and Table 3: success drop by intervention family. |
| C3 | Trajectory metrics detect failures missed by final-answer scoring. | Cases where final answer is correct but component metrics fail; human audit agreement on hidden failures. | Error-case mining implemented; human validation not yet run. | Planned | Metrics may reward superficial process markers or disagree with humans. | Figure 6 plus audited case table. |
| C4 | ACRS changes model rankings relative to clean success. | Ranking comparison between clean success and ACRS, with rank correlation and uncertainty. | Ranking script implemented; no final model run. | Planned | Rankings may remain stable, making ACRS less compelling as a distinct summary. | Figure 4: clean-success rank vs ACRS rank. |
| C5 | Recovery ability is separable from planning ability. | Component analysis showing agents with similar planning/tool-selection scores differ in recovery after failures, or controlled scaffold ablation. | Recovery metrics implemented; no final separability analysis. | Planned | Metrics may not cleanly separate planning from recovery. | Scatter/table: planning metric vs recovery rate. |
| C6 | Simple self-checking improves some intervention families but not all. | Prompt/scaffold ablation with fixed agents and tasks; improvement on targeted families and non-improvement or tradeoff elsewhere. | Table 4 is an explicit `not yet run` placeholder. | Planned | Self-checking may uniformly help, uniformly hurt, or mostly increase tool use. | Table 4 / ablation delta figure. |
| C7 | Some agents overuse tools even when unnecessary. | Irrelevant-tools intervention showing higher unnecessary-tool-call rate for some agents without matching final-success gains. | Metric implemented; final experiment not run. | Planned | Overuse may be an artifact of prompting or tool metadata. | Table: unnecessary-tool-call rate by agent under irrelevant-tools condition. |
| C8 | Some agents stop prematurely under misleading success signals. | Premature-success-signal intervention showing increased premature-stop rate and examples of early final answers. | Metric and error-case category implemented; final experiment not run. | Planned | The signal may be too obvious or too artificial. | Figure/table: premature-stop rate by agent and condition. |
| C9 | CausalAgentBench is reproducible without paid services for smoke tests. | Fresh environment run of install, help, smoke CLI, lint, tests, and local dev run. | Local commands passed with `python3`; resume now rejects config-hash mismatches; `python` pyenv shim on this machine points to a missing 3.11. | Engineering-only | Local machine success may not imply clean clone reproducibility. | Reproducibility log/table in appendix or artifact README. |
| C10 | Controlled interventions isolate intended skill components. | Human or expert audit that interventions preserve the user goal and primarily alter the intended factor. | Quality checks implemented; human/expert audit not yet run. | Planned | If auditors find multi-factor changes, causal interpretation weakens. | Table: intervention-validity agreement by family. |

## Pilot Notes

- `pilot_v0.1` generation artifacts exist locally and pass schema validation.
- A `pilot_20_multi_agent_stub` run exercises 3 local-stub LLM-style agents and 2 deterministic non-oracle baselines. This is engineering-only because no real provider-backed LLM calls were made.
- Main claims C1-C8 and C10 remain `Planned`; the stub run must not be used as scientific evidence.
