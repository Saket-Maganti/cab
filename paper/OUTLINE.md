# Paper Outline

## 1. Abstract

- State the problem: final success alone can hide why tool-using agents succeed or fail.
- State the proposed solution: paired clean/intervention tasks with trajectory-level component metrics.
- Report only verified empirical findings once experiments exist.
- Avoid claiming robustness gaps before E1-E8 are run.

## 2. Introduction

- Motivate why aggregate task success is insufficient for agent evaluation.
- Explain the skill components that final success conflates.
- Introduce CausalAgentBench and ACRS.
- Clearly distinguish benchmark design claims from empirical results.
- Must prove: the problem is important and the intervention framework is a plausible remedy.

## 3. Related Work

- Cover agent benchmarks, tool-use benchmarks, web/navigation benchmarks, software engineering agent benchmarks, LLM-as-judge evaluation, causal/intervention-based evaluation, robustness benchmarks, and trajectory-level evaluation.
- Use `docs/RELATED_WORK_TRACKER.md` as the source tracker.
- Must prove: existing benchmarks leave room for causal skill decomposition in tool-using agents.

## 4. Benchmark Design

- Define base tasks, clean condition, interventions, trajectories, and controlled mock tools.
- Describe task domains and task construction rules.
- Explain schema validation and JSONL artifacts.
- Must prove: tasks are auditable, reproducible, and structured for controlled comparison.

## 5. Interventional Framework

- Define each intervention family and its intended causal factor.
- Explain the paired-task design.
- Discuss intervention validity and single-factor-change assumptions.
- Must prove: intervention design supports meaningful causal robustness analysis.

## 6. Metrics

- Define final success, component metrics, trajectory faithfulness, and ACRS.
- Explain edge cases such as zero clean success.
- Discuss why metrics are complementary rather than interchangeable.
- Must prove: metrics map to interpretable agent skills and can be computed reproducibly.

## 7. Experimental Setup

- Describe datasets, splits, configs, seeds, agents, prompts, tools, and graders.
- Include oracle/stub baselines only as sanity checks.
- Specify cost and latency logging.
- Must prove: experiments are reproducible and fair across agents.

## 8. Results

- Present E1 clean vs intervention success.
- Present E2 intervention-family breakdowns.
- Present E3 ranking instability.
- Present E4 trajectory vs final scoring.
- Must prove: empirical evidence supports or weakens the central claim.

## 9. Human Validation

- Describe validation subset sampling.
- Report agreement and adjudication results.
- Analyze intervention validity and label quality.
- Must prove: key labels and intervention assumptions are not solely author-defined.

## 10. Ablations

- Present E5 prompt/scaffold ablations.
- Analyze robustness-cost and robustness-overtooling tradeoffs.
- Include negative or mixed results.
- Must prove: robustness can or cannot be improved by simple scaffolds, with clear boundaries.

## 11. Limitations

- Discuss synthetic task limitations, intervention validity risks, metric limitations, possible overfitting, and external validity.
- Include negative results that weaken strong claims.
- Must prove: the paper is honest about what the benchmark does not establish.

## 12. Ethics and Reproducibility

- Discuss privacy, synthetic data, API use, cost, environmental considerations, and benchmark misuse.
- Document artifacts: configs, seeds, code, task JSONL, trajectory JSONL, score scripts, and claim ledger.
- Must prove: readers can inspect and reproduce the reported evidence.

## 13. Conclusion

- Restate the evidence-backed conclusion.
- Avoid unsupported generalization beyond the benchmark.
- Identify future work: human-authored tasks, broader agent adapters, held-out benchmark versions, and richer causal analysis.
