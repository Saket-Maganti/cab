# Experimental Roadmap

## E0: Smoke Tests

- Purpose: Verify that the package, CLI, deterministic tools, JSONL outputs, scoring, and analysis scripts run locally without paid services.
- Required data: Tiny generated sample from `configs/smoke.yaml`.
- Agents: Random tool agent, scripted oracle agent, and any local stub agents.
- Metrics: CLI pass/fail, schema validation, trajectory count, score file existence.
- Expected output: `tasks.jsonl`, `trajectories.jsonl`, `scores.json`, `analysis_report.md`.
- Figure/table target: Reproducibility log table.
- Failure mode: Passing smoke tests may only prove engineering wiring, not scientific validity.

## E1: Clean vs Intervention Success

- Purpose: Test whether clean final success overestimates robustness under interventions.
- Required data: Paired clean/intervention task set with balanced domains and fixed seeds.
- Agents: Baselines, scaffolded agents, and LLM-backed agents once adapters exist.
- Metrics: Clean success, intervention success, ACRS, confidence intervals.
- Expected output: Agent-level summary table and paired per-task scores.
- Figure/table target: Main table with clean success, intervention success, ACRS, and sample size.
- Failure mode: Clean and intervention performance may be similar, weakening the central empirical claim.

## E2: Intervention Family Breakdown

- Purpose: Identify which intervention families cause the largest degradation.
- Required data: Balanced tasks across all intervention families, with enough samples per family.
- Agents: Same set as E1.
- Metrics: Success drop, ACRS by family, recovery rate, contradiction detection, memory verification, premature stop, unnecessary tool calls.
- Expected output: Per-family score table and family-level degradation plot.
- Figure/table target: Bar chart of success drop by intervention family.
- Failure mode: Differences may reflect task difficulty rather than intervention mechanism if the task set is not balanced.

## E3: Model Ranking Instability

- Purpose: Test whether model/agent rankings change when using ACRS instead of clean success.
- Required data: E1 outputs with multiple credible agents.
- Agents: At least 5 non-oracle agents or agent configurations.
- Metrics: Clean-success rank, intervention-success rank, ACRS rank, rank correlation, confidence intervals.
- Expected output: Ranking comparison and instability analysis.
- Figure/table target: Rank-shift plot or clean-rank vs ACRS-rank scatter.
- Failure mode: Rankings may remain stable, making ACRS more diagnostic than ranking-changing.

## E4: Trajectory vs Final Scoring

- Purpose: Determine whether trajectory metrics reveal failures hidden by final-answer correctness.
- Required data: Trajectory JSONL with full tool calls, observations, final answers, and component labels.
- Agents: Include agents with different tool-use styles, including over-tooling and under-tooling tendencies.
- Metrics: Final answer correctness, tool-selection accuracy, argument validity, trajectory faithfulness, premature stop, unnecessary tool-call rate, contradiction detection.
- Expected output: Confusion-style table showing final-correct trajectories with process failures.
- Figure/table target: Table of hidden-failure rates by agent and component.
- Failure mode: Component metrics may be too coarse or too correlated with final success.

## E5: Prompt/Scaffold Ablation

- Purpose: Test whether self-checking, ReAct-style, or planner/executor scaffolds improve interventional robustness.
- Required data: Fixed task set reused across prompt/scaffold variants.
- Agents: Same base model with variants: direct, ReAct-style, self-check, planner/executor, recovery-specific prompt.
- Metrics: ACRS, family-level success, recovery rate, unnecessary tool-call rate, latency/cost.
- Expected output: Ablation table with deltas relative to direct baseline.
- Figure/table target: Family-level delta plot for each scaffold.
- Failure mode: Scaffolds may trade robustness for cost or over-tooling, complicating claims.

## E6: Human Validation Subset

- Purpose: Validate task quality, intervention validity, final answer labels, and trajectory component labels.
- Required data: Stratified subset across domains, interventions, agents, successes, and failures.
- Agents: Outputs sampled from E1-E5.
- Metrics: Human agreement, intervention validity rate, label accuracy, adjudicated error taxonomy.
- Expected output: Human validation report and corrected labels where needed.
- Figure/table target: Agreement table by label type and intervention family.
- Failure mode: Low agreement may require redefining metrics or simplifying claims.

## E7: Cost and Latency Analysis

- Purpose: Quantify practical tradeoffs of robust agent behavior.
- Required data: Run logs with model, token counts if available, tool calls, wall-clock time, and retries.
- Agents: API-backed and local agents where possible.
- Metrics: Cost per task, latency per task, tool calls per task, success per dollar, ACRS per dollar.
- Expected output: Cost/latency summary by agent and scaffold.
- Figure/table target: Scatter plot of ACRS vs cost or latency.
- Failure mode: Missing or inconsistent provider metadata may limit comparison.

## E8: Robustness Across Task Domains

- Purpose: Test whether robustness findings generalize across domains.
- Required data: Balanced tasks across travel, calendar/email, file/spreadsheet QA, shopping, research, policy, coding, and operations.
- Agents: Same set as E1 when feasible.
- Metrics: Domain-level clean success, intervention success, ACRS, component metrics.
- Expected output: Domain-by-agent matrix and domain interaction analysis.
- Figure/table target: Heatmap of ACRS by agent and domain.
- Failure mode: Some domains may be underpowered or easier due to template artifacts.
