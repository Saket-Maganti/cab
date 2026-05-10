# Research Spec

## One-Sentence Thesis

Final task success can substantially overestimate tool-using agent competence because it conflates planning, tool selection, memory use, observation interpretation, error recovery, and stopping behavior; controlled interventions are needed to isolate these skills.

## Target Venue

Primary target: NeurIPS Evaluations and Datasets style submission.

Secondary targets if scope changes: ICLR benchmark track, ACL/EMNLP resources track, or a dedicated agent evaluation workshop.

## Target Contribution Type

CausalAgentBench should be positioned as an evaluation and dataset contribution with:

- A benchmark methodology for paired clean and intervened tool-use tasks.
- A synthetic, controllable benchmark suite with auditable task specifications.
- Trajectory-level component metrics that complement final answer scoring.
- Baseline agents and reproducible experiment scripts.
- A claim ledger that separates implemented infrastructure, observed evidence, and unproven hypotheses.

## Primary Research Questions

- RQ1: How much does final task success overestimate robust agent competence?
- RQ2: Which interventions cause the largest degradation in agent performance?
- RQ3: Do stronger clean-setting agents remain stronger under intervention?
- RQ4: Do trajectory-level metrics reveal failures hidden by final-answer scoring?
- RQ5: Can simple prompting or planning scaffolds improve interventional robustness?

## Secondary Research Questions

- How much do intervention effects vary by task domain?
- Which component metrics best predict intervention success?
- Are recovery failures distinct from initial planning failures?
- Do agents overuse tools when irrelevant tools are introduced?
- Do agents underuse tools when memory appears confident but may be stale?
- How often do agents stop prematurely when the environment emits misleading completion signals?
- How sensitive are rankings to final-answer grader choice?
- What level of human validation is needed to trust trajectory labels?

## Hypotheses

- H1: Clean success will be higher than intervention success for most non-oracle agents.
- H2: Tool corruption, memory corruption, observation conflict, and premature success signals will reveal failures not visible from clean-setting final success alone.
- H3: Model rankings under ACRS will differ from rankings under clean success.
- H4: Trajectory-level metrics will identify unsupported or brittle successes that final-answer correctness marks as successful.
- H5: Lightweight self-checking or plan-then-execute prompting will improve recovery and contradiction handling, but may increase unnecessary tool use.
- H6: Recovery from tool failure will be empirically separable from clean-task planning quality.

These are hypotheses and planned tests. They should not be written as results until the corresponding experiments are run.

## Required Evidence

The paper needs at minimum:

- A validated benchmark specification with clean/intervention pairs.
- Human or expert audit showing interventions preserve the high-level goal while changing one intended factor.
- Clean vs intervention success rates across multiple agent families.
- ACRS with uncertainty estimates and clear handling of zero clean-success cases.
- Intervention-family breakdowns.
- Model-ranking comparison between clean success and ACRS.
- Trajectory-level analysis showing cases where final answers are correct but process metrics fail.
- Prompt/scaffold ablations with fixed tasks and fixed model backends.
- Reproducibility artifacts: configs, seeds, task JSONL, trajectory JSONL, score scripts, environment metadata, and cost/latency logs for API-backed runs.

## Negative Results That Would Weaken The Paper

- Intervention performance is nearly identical to clean performance for all credible agents and all intervention families.
- ACRS rankings match clean-success rankings exactly or nearly exactly across all experiments.
- Human auditors find that interventions often change more than one factor or alter task difficulty in uncontrolled ways.
- Trajectory metrics show little relation to human error analysis.
- Prompt/scaffold ablations dominate all intervention families, making the benchmark too easy.
- Synthetic tasks fail to transfer even qualitatively to a human-authored validation subset.
- Results are highly sensitive to one grader, one task generator seed, or one domain.

Negative results should still be reported honestly, but they would require reframing the paper toward benchmark limitations or methodology lessons.

## Minimum Publishable Unit

The smallest credible paper should include:

- At least 100 clean/intervention task pairs across several domains.
- At least 5 intervention families, including tool failure, tool corruption, memory corruption, observation conflict, and irrelevant tools.
- At least 5 agents or agent configurations, including non-oracle baselines and at least 2 LLM-backed agents.
- Clean success, intervention success, ACRS, and core component metrics.
- A human-validated subset of tasks and trajectories.
- A complete reproducibility package.
- A claim ledger where unsupported claims are explicitly excluded from the paper narrative.

## NeurIPS-Level Version

The stronger version should include:

- 200 to 500 benchmark instances with balanced clean/intervention coverage.
- All 10 planned intervention families.
- Multiple model families, prompting styles, and planner/executor scaffolds.
- Confidence intervals, paired significance tests where appropriate, and ranking stability analysis.
- Human validation of intervention validity and trajectory labels.
- Domain-level analysis and cross-domain robustness.
- Public benchmark card, dataset card, metrics card, and reproducible scoring package.
- Cost and latency analysis for realistic agent deployment tradeoffs.
- Failure taxonomy with representative trajectory examples.

## Risks and Mitigations

| Risk | Why it matters | Mitigation |
|---|---|---|
| Synthetic tasks are too simple. | Agents may solve templates without demonstrating general skill. | Add human-authored validation subset and domain diversity. |
| Interventions change multiple factors. | Causal interpretation becomes weak. | Add intervention audit rubric and pairwise review. |
| Oracle metadata leaks into baselines. | Baselines may overstate achievable performance. | Label oracle agents as sanity checks; separate them from model comparisons. |
| Metrics reward process theater. | Agents may mention verification without doing useful verification. | Ground trajectory metrics in tool calls and observations where possible. |
| LLM-as-judge bias affects final scoring. | Reported success may depend on grader choice. | Use deterministic exact checks for smoke tests and compare graders in main runs. |
| ACRS is unstable when clean success is low. | Ratios can be misleading. | Report clean success, intervention success, ACRS, and undefined cases together. |
| Benchmark encourages overfitting. | Public tasks may become training data. | Maintain held-out task templates and versioned private validation splits if needed. |
| API cost limits reproducibility. | Reviewers may not reproduce large runs. | Provide deterministic local baselines and small reproducible subsets. |
