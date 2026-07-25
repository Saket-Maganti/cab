# Baseline Agents

These agents are benchmark controls, not claims about frontier agent performance.

| Agent | Purpose | Uses hidden information? | Limitations |
|---|---|---:|---|
| `random_tool_agent` | Lower-bound baseline that randomly chooses an available tool or stops. | No | Often stops early and uses shallow default arguments. |
| `scripted_oracle_agent` | Upper-bound sanity check that follows gold tool metadata and expected answers when available. | Yes | Not a realistic agent; exclude from model capability claims. |
| `greedy_tool_agent` | Weak realistic baseline using keyword heuristics from the user instruction. | No | No deep planning, no robust observation interpretation. |
| `react_stub_agent` | Deterministic ReAct-style thought/action/observation baseline. | No | Rule-based thoughts; no language-model reasoning. |
| `planner_executor_stub_agent` | Deterministic plan-then-execute baseline with simple error revision. | Partially, only for legacy `BenchmarkTask` compatibility when gold sequences are present | For schema-native `BenchmarkInstance` runs, it uses keyword-derived plans rather than gold tool sequences; still far weaker than an LLM planner. |

## LLM-Backed Agent Styles

The repository defines provider-backed agent styles for pilot experiments:

| Agent | Style | Uses hidden information? | Notes |
|---|---|---:|---|
| `direct_tool_agent` | Single-loop ReAct-style tool caller. | No | Chooses one tool or final answer per LLM turn. |
| `direct_llm_tool_agent` | Named direct LLM baseline for paper configs. | No | Uses the same shared provider adapter as `direct_tool_agent` with a versioned prompt card. |
| `react_style_llm_agent` | Explicit ReAct loop baseline. | No | Depends on the model following the single-action JSON protocol. |
| `planner_executor_agent` | Two-phase planner/executor. | No | Makes a compact plan, then executes and revises after failures. |
| `planner_executor_llm_agent` | Named planner/executor LLM baseline for paper configs. | No | Adds a versioned prompt card around the same two-phase control flow. |
| `self_check_agent` | Tool caller with explicit verification before final answer. | No | Intended to test whether self-checking improves interventional robustness. |
| `self_checking_llm_agent` | Named self-checking LLM baseline for paper configs. | No | Runs an extra self-check turn before accepting a final answer. |
| `memory_verifying_llm_agent` | Memory-robustness baseline. | No | Prompts verification when initial memory is present. |
| `recovery_prompt_llm_agent` | Tool-failure recovery baseline. | No | Adds a targeted recovery instruction after failed/corrupted observations. |
| `tool_conservative_llm_agent` | Minimal-tool-use baseline. | No | Prompts the model to avoid irrelevant or redundant calls. |

Provider-specific aliases are also available:

- `openai_chat_agent`
- `anthropic_agent`
- `gemini_agent`
- `openrouter_agent`
- `local_hf_chat_agent`

The implementation uses a common client interface and standard-library HTTP adapters, so missing provider SDKs do not affect smoke tests. API keys are read from environment variables and must never be committed. `local_stub` exists only for tests and dry-run plumbing; it is not a scientific baseline.

Provider names currently supported by the config layer are `openai`, `anthropic`, `gemini`, `openrouter`, `openai_compatible`, `local_openai`, and `local_stub`. OpenAI-compatible providers can set a per-run `base_url`; local OpenAI-compatible servers default to `http://localhost:8000/v1/chat/completions` and do not require an API key unless configured by the user.

Use `local_openai` for Ollama, vLLM, LM Studio, llama.cpp, or any local OpenAI-compatible endpoint. See [OPEN_WEIGHT_LOCAL_MODELS.md](OPEN_WEIGHT_LOCAL_MODELS.md). Runs stamp `evidence_scope: local_open_weight_unvalidated` so they stay separate from commercial API leaderboards.

LLM call records include prompt hash, response hash, tool-state hash, model-config hash, latency, token usage, estimated cost when pricing is configured, retry count, cache metadata, and provider error class when a provider fails. Optional response caching is controlled by `cache_dir` in the agent run config and never stores API keys.

Prompt templates live under `prompts/agents/`. Every LLM baseline records `prompt_version_hash`, `prompt_template_hash`, and prompt file names in trajectory metadata. These hashes are reproducibility links only; they are not evidence of model quality.

`configs/baseline_suite_local_stub.yaml` exercises the full baseline suite with the deterministic local stub provider for engineering checks only. Replace `local_stub` with configured providers and model IDs before treating a run as an LLM-backed experiment.

## Agent Cards

### `random_tool_agent`

- Description: Lower-bound deterministic-random tool selector.
- Intended use: Estimate a weak floor and exercise the tool loop.
- Limitations: No semantic planning; shallow default arguments.
- Prompt template: None; deterministic Python baseline.
- Expected strengths: Reproducible, cheap, and useful for detecting scorer/runner regressions.
- Expected failure modes: Wrong tool selection, premature stopping, missing required tools, inefficient repeated calls.

### `greedy_tool_agent`

- Description: Keyword-planned heuristic baseline with a simple verification fallback after tool errors.
- Intended use: Non-LLM heuristic baseline stronger than random.
- Limitations: Does not deeply interpret observations or contradictions.
- Prompt template: None; deterministic Python baseline.
- Expected strengths: Good coverage of common synthetic domains and required tool order.
- Expected failure modes: Unsupported final answers, brittle arguments, weak recovery beyond `verify_fact`.

### `scripted_oracle_agent`

- Description: Sanity-check upper bound that may use gold tool sequence and expected-answer metadata.
- Intended use: Detect benchmark/tool/scorer regressions, not realistic agent capability.
- Limitations: Uses hidden information and must be excluded from leaderboards and model ranking claims.
- Prompt template: None; deterministic oracle.
- Expected strengths: Exercises idealized happy paths where metadata is available.
- Expected failure modes: Misleading if compared to realistic agents; can mask benchmark leakage if mislabeled.

### `direct_llm_tool_agent`

- Description: Direct single-loop LLM tool caller.
- Intended use: Primary simple LLM baseline.
- Limitations: No explicit planning or second-pass checking.
- Prompt template: `prompts/agents/direct_llm_tool_agent.md`, version `direct_llm_tool_agent_v1`.
- Expected strengths: Low overhead; should handle straightforward tool selection.
- Expected failure modes: Premature final answers, insufficient recovery, unsupported confidence.

### `react_style_llm_agent`

- Description: ReAct-style LLM baseline that alternates compact reasoning, one action, and observation use.
- Intended use: Standard reasoning/action scaffold baseline.
- Limitations: Relies on model compliance with JSON and one-action discipline.
- Prompt template: `prompts/agents/react_style_llm_agent.md`, version `react_style_llm_agent_v1`.
- Expected strengths: Observation-aware iteration and better handling of multi-step tasks than direct prompting.
- Expected failure modes: Repeated failed calls, observation ignoring, overlong trajectories.

### `planner_executor_llm_agent`

- Description: Two-phase plan-then-execute LLM baseline.
- Intended use: Stronger scaffold for long-horizon and dependency-heavy tasks.
- Limitations: Planning is text-only and can be stale after unexpected observations.
- Prompt template: `prompts/agents/planner_executor_llm_agent.md`, version `planner_executor_llm_agent_v1`.
- Expected strengths: Required-evidence coverage, ordered tool use, and plan revision after errors.
- Expected failure modes: Plan rigidity, overlong trajectories, final answers that inherit bad plan assumptions.

### `self_checking_llm_agent`

- Description: LLM baseline that runs a self-check before accepting a final answer.
- Intended use: Test whether explicit final-answer auditing improves trajectory validity.
- Limitations: Self-checking can become process theater if the model does not actually use observations.
- Prompt template: `prompts/agents/self_checking_llm_agent.md`, version `self_checking_llm_agent_v1`.
- Expected strengths: Better detection of unsupported final answers and missing evidence.
- Expected failure modes: Extra cost/latency, unnecessary verification, false confidence after shallow checks.

### `memory_verifying_llm_agent`

- Description: LLM baseline specialized for tasks with initial memory.
- Intended use: Memory-corruption and stale-context interventions.
- Limitations: Verification depends on available tools and model compliance.
- Prompt template: `prompts/agents/memory_verifying_llm_agent.md`, version `memory_verifying_llm_agent_v1`.
- Expected strengths: Avoids blind trust in corrupted memory.
- Expected failure modes: Unnecessary verification when memory is irrelevant, failure to resolve conflicting evidence.

### `recovery_prompt_llm_agent`

- Description: LLM baseline with targeted recovery instructions after tool failures or corrupted outputs.
- Intended use: Tool-failure and tool-corruption interventions.
- Limitations: Recovery is prompted, not guaranteed; no hidden retries outside the logged trajectory.
- Prompt template: `prompts/agents/recovery_prompt_llm_agent.md`, version `recovery_prompt_llm_agent_v1`.
- Expected strengths: Fewer repeated failed calls and better calibrated abstention.
- Expected failure modes: Over-abstention, wrong alternative tool, unsupported recovery claims.

### `tool_conservative_llm_agent`

- Description: LLM baseline that minimizes unnecessary tool use.
- Intended use: Irrelevant-tool and cost/efficiency analyses.
- Limitations: May under-call tools on tasks that need broad evidence.
- Prompt template: `prompts/agents/tool_conservative_llm_agent.md`, version `tool_conservative_llm_agent_v1`.
- Expected strengths: Lower tool overuse and cleaner trajectories.
- Expected failure modes: Required tool omission, premature stopping, uncertainty failure.

## Reporting Guidance

- Report oracle results separately from non-oracle baselines.
- Exclude `scripted_oracle_agent` from any claim about realistic agent capability or model ranking. The default leaderboard tables exclude it and write a separate oracle sanity-check table.
- Mark legacy `BenchmarkTask` compatibility runs separately, because some legacy stubs may use expected-behavior metadata for smoke-test continuity.
- Use `random_tool_agent` only as a floor.
- Treat stub agents as engineering baselines for validating benchmark mechanics.
- Do not use any baseline smoke result as a scientific model ranking.

## Minimum Baseline Set For Paper Claims

A credible paper experiment should include:

- at least one random or degenerate floor,
- at least one weak heuristic baseline,
- at least one scaffolded non-oracle baseline,
- at least two LLM-backed agents or agent configurations,
- the oracle baseline reported in a separate sanity-check table only.
