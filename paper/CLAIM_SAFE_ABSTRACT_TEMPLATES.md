# Claim-Safe Abstract Templates

Status: templates only. Bracketed slots are not results.

## 1. No-Run Scaffold Version

Tool-using LLM agents are often evaluated by clean-task success, but deployment failures can arise from tool failures, stale memory, conflicting observations, and ambiguity. We introduce CausalAgentBench, a controlled perturbation benchmark design for paired clean/intervention tasks, with a taxonomy of intervention families, ACRS robustness metrics, scorer-sanity checks, and human-validation protocols. This paper reports the benchmark scaffold and preregistered analysis plan; provider-backed results are RESULT_REQUIRED.

## 2. Compact-20 Pilot Version

We evaluate [MODEL_COUNT] agents on a human-reviewed Compact-20 subset of CausalAgentBench. Across paired clean/intervention tasks, we report clean success, intervention success, ACRS, per-family degradation, and rank-instability diagnostics with uncertainty. RESULT_REQUIRED: insert only validated numbers after provider runs, scorer sanity, and C10 validation.

## 3. Five-Model / 100-Task Version

We run [MODEL_COUNT] agents on [TASK_COUNT] paired CausalAgentBench tasks spanning [FAMILY_COUNT] intervention families. The study tests whether clean-task rankings are stable under controlled perturbations and which families induce robustness degradation. RESULT_REQUIRED: all estimates, intervals, and rank correlations must come from audited provider trajectories.

## 4. Main-500 Version

CausalAgentBench is a 500-task paired clean/intervention benchmark for evaluating robustness of tool-using LLM agents. Using [MODEL_COUNT] models and audited trajectories, we estimate clean success, intervention success, ACRS, family-level degradation, recovery behavior, abstention correctness, and rank instability. RESULT_REQUIRED: no numbers may be inserted until Main-500 evidence gates pass.
