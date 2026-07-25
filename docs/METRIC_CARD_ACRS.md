# Metric Card: Agent Causal Robustness Score (ACRS)

**Metric ID:** `acrs`  
**Scorer family:** `deterministic_heuristic_v1`  
**Implementation:** `src/causal_agent_bench/metrics/causal_robustness.py`, `src/causal_agent_bench/scoring.py`

## Intended Use

ACRS summarizes how much **final-task success** drops from clean to intervention conditions for the same agent:

```text
ACRS = intervention_success_rate / clean_success_rate
```

Use ACRS to compare **relative robustness** across agents on the same frozen dataset and split, alongside component metrics (recovery, contradiction handling, tool precision).

## Out-of-Scope Use

- Sole metric for agent quality (always report clean success and sample sizes).
- Cross-dataset comparison without matching intervention mix and difficulty.
- Scientific claims from stub/oracle-only runs.
- Replacing human judgment on answer correctness or intervention validity.

## Data Construction

ACRS is computed from `ScoreRecord` rows aggregated by agent:

- **Numerator:** mean `final_success_binary` on intervention instances.
- **Denominator:** mean `final_success_binary` on clean instances for the same agent and evaluation scope.

Per-family ACRS uses the same formula restricted to one `intervention_family`. Inputs come from trajectories scored against `BenchmarkInstance` contexts — not from hidden ground truth alone.

## Synthetic Data Policy

ACRS inherits dataset syntheticity. It does not correct for template leakage or intervention audit gaps. Engineering pilots may use `evidence_scope: pilot_stub_engineering_only` — such runs must not be cited as validated robustness evidence.

## Intervention Families

ACRS is defined over the benchmark’s intervention families. Family-level breakdowns are exploratory unless multiple-comparison corrections and human audits are reported (`docs/METRICS.md` statistical reporting section).

## Scoring Methodology

1. Score each trajectory with `score_trajectory()` → `final_success_binary` and diagnostics.
2. Aggregate clean vs intervention success per agent.
3. Compute ACRS; if clean success is 0, ACRS is `null` / undefined.
4. Optional: `absolute_degradation = clean - intervention`, `relative_degradation = 1 - ACRS`.
5. Metrics v2 exports confidence intervals via bootstrap; paired tests use base-task pairing where implemented.

**Required metadata for published numbers:** run config path, `run_metadata.json`, seeds, model IDs, prompt hashes, scorer string, git commit, frozen `dataset_hash`.

## Validation Status

| Aspect | Status |
|--------|--------|
| Deterministic implementation | Implemented |
| Statistical reporting exports | Implemented |
| Human agreement on final success | **Not complete** |
| Human agreement on intervention validity | **Not complete** |
| Calibrated LLM-judge alternative | Optional; not default |

## Known Failure Modes

- **Low clean success:** ACRS unstable or undefined; small-sample warnings emitted.
- **High clean + high intervention success:** ACRS ≈ 1 but agent may still be weak absolutely.
- **Heuristic final answers:** paraphrases scored as failures; keyword matches as successes.
- **Family imbalance:** agents compared on different intervention exposure if splits differ.
- **Oracle inflation:** scripted agents inflate denominators — exclude from realistic rankings.

## Contamination Risk

Agents tuned on intervention patterns in public JSONL may inflate ACRS without true robustness. Mitigate with held-out templates and unreleased generation seeds.

## Maintenance Plan

- Metric definition versioned in `docs/METRICS.md` and scorer metadata field.
- Breaking changes require bumping scorer ID and re-running frozen analysis scripts.
- Paper tables should pin `metrics_v2.json` and `stats_summary.json` from the cited run directory.

## License

Documentation MIT. Metric computation code MIT (`LICENSE`).
