# 11 Run Pipeline Audit

## Deterministic pilot run

- Config: `configs/pilot_20_multi_agent.yaml`
- Run directory: `results/20260519T053609Z_pilot_20_multi_agent_stub`
- Dataset version: `pilot_v0.1`
- Config hash: `6c0a1da78f8a8f53`
- Agents: `direct_tool_local_stub`, `planner_executor_local_stub`, `self_check_local_stub`, `greedy_tool_agent`, `react_stub_agent`
- Instances: 120
- Trajectories: 600
- Scores: 600
- Errors: 0

## Commands

- `python3 -m causal_agent_bench run --config configs/pilot_20_multi_agent.yaml`
- `python3 -m causal_agent_bench score --run-dir results/20260519T053609Z_pilot_20_multi_agent_stub`
- `python3 -m causal_agent_bench analyze --run-dir results/20260519T053609Z_pilot_20_multi_agent_stub`
- `python3 -m causal_agent_bench export-paper-assets --run-dir results/20260519T053609Z_pilot_20_multi_agent_stub --allow-engineering-only --no-write-global`
- `python3 -m causal_agent_bench summarize-run --run-dir results/20260519T053609Z_pilot_20_multi_agent_stub`

## Completeness

The run directory contains config, config hash, metadata, git commit, package/python versions, instances, trajectories, errors, scores, aggregate summaries, metric exports, analysis report, run summary, paper assets, statistical summary, and error-case exports.

## Evidence scope

The run summary reports `scientific_scope: engineering_only_local_stub` and `evidence_scope: pilot_stub_engineering_only`. This run is useful for pipeline verification only.

