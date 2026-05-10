# Related Work Tracker

This file is a planning tracker, not a finished related-work section. Do not treat rows as verified citations until the `Status` column says `citation verified`.

| Paper / Benchmark | Area | What it measures | Limitation relevant to CausalAgentBench | How we differ | Status |
|---|---|---|---|---|---|
| AgentBench | Agent benchmarks | Broad agent performance across interactive environments. | Need to verify whether it isolates causal skill components or mainly reports aggregate success. | Planned focus on paired clean/intervention tasks and trajectory component metrics. | TODO: verify citation and exact scope. |
| HELM | Robustness / holistic LLM evaluation | Multi-metric evaluation across scenarios. | Not primarily a tool-using agent intervention benchmark. | Focus on tool-use trajectories and causal perturbations. | TODO: verify relevant sections. |
| BIG-bench / BIG-bench Hard | General LLM benchmark | Task performance across many language tasks. | Mostly final-answer evaluation; not tool trajectory causal analysis. | Evaluate agent-tool interaction under controlled perturbation. | TODO: decide if relevant enough. |
| WebArena | Web/navigation benchmarks | Web task completion in realistic browser environments. | High realism can make causal attribution difficult. | Sacrifice some realism for controlled interventions and auditable mock tools. | TODO: verify citation and metrics. |
| MiniWoB++ | Web/navigation benchmarks | Browser interaction and web UI control. | Low-level navigation focus; less emphasis on modern LLM tool-use failure decomposition. | Target language-agent tool use and intervention robustness. | TODO: verify current usage. |
| Mind2Web | Web/navigation benchmarks | Mapping natural language instructions to web actions. | Need to verify whether final success vs trajectory failure is separated. | Planned trajectory-level causal metrics. | TODO: verify citation and task format. |
| ToolBench | Tool-use benchmarks | Tool/API use by LLMs. | May emphasize successful tool invocation rather than paired causal perturbations. | Controlled tool failure, corruption, removal, and distractor interventions. | TODO: verify citation and evaluation protocol. |
| API-Bank | Tool-use benchmarks | API call planning and execution. | Need to verify coverage of corrupted observations and memory conflicts. | Explicit intervention families and ACRS. | TODO: verify citation. |
| Gorilla / APIBench | Tool-use benchmarks | API selection and invocation. | Often centered on tool/API matching rather than full agent trajectory robustness. | Include recovery, stopping, contradiction handling, and memory verification. | TODO: verify citation and naming. |
| τ-bench / tau-bench | Tool-use / conversational agents | Tool-agent behavior in domain workflows. | Need to verify exact domains, metrics, and perturbation coverage. | Emphasize causal interventions and component metrics. | TODO: verify official name and citation. |
| SWE-bench | Software engineering agent benchmarks | Issue resolution from real repositories. | Realistic final outcome, but causal skill attribution can be hard. | Use controlled mock tools and interventions to isolate components. | TODO: verify citation and variants. |
| SWE-bench Verified | Software engineering agent benchmarks | Human-validated subset of SWE-bench tasks. | Still primarily issue-resolution success rather than intervention-pair analysis. | Human validation planned for intervention validity and trajectory labels. | TODO: verify citation and validation protocol. |
| HumanEval / MBPP | Coding benchmarks | Code generation correctness. | Not agentic tool-use trajectory evaluation. | Evaluate multi-step tool-using agents, not only code output. | TODO: decide if background only. |
| GAIA | Agent benchmarks | General assistant tasks requiring reasoning/tool use. | Need to verify whether hidden failures under perturbation are measured. | Planned paired clean/intervention design. | TODO: verify citation and scoring. |
| WorkArena / enterprise workflow benchmarks | Web/navigation / agent benchmarks | Work-oriented browser or SaaS workflows. | Realistic workflows may not isolate single causal factors. | Controlled simulated environment with auditability. | TODO: verify relevant benchmarks. |
| LLM-as-judge studies | LLM-as-judge evaluation | Model-graded evaluation quality, bias, and agreement. | LLM judges can confound final-answer scoring. | Use deterministic checks in smoke tests and planned human validation. | TODO: collect exact papers. |
| Causal evaluation papers | Causal evaluation / intervention-based evaluation | Interventions, counterfactuals, causal attribution in model evaluation. | Often not specific to tool-using agent trajectories. | Apply intervention logic to agent tool-use skill decomposition. | TODO: literature search required. |
| Robustness benchmarks | Robustness benchmarks | Performance under distribution shift, adversarial inputs, or perturbations. | Perturbations may not map to agent skill components. | Define intervention families tied to tool-use mechanisms. | TODO: collect representative work. |
| Process supervision / trajectory evaluation | Trajectory-level evaluation | Intermediate reasoning/process quality. | May evaluate reasoning traces without executable tool observations. | Score observable tool calls, arguments, observations, and final answer faithfulness. | TODO: collect exact papers. |
| ReAct | Agent prompting / tool use | Interleaved reasoning and acting with tools. | Prompting method, not a benchmark for causal robustness by itself. | Include ReAct-style baselines and perturbation evaluation. | TODO: verify citation. |
| Plan-and-execute agent work | Agent scaffolding | Planning decomposition and execution. | Often evaluated by task success only. | Test whether scaffolds improve intervention robustness. | TODO: collect exact papers. |

## Literature Search TODOs

- Verify official citations, venues, and dates for every named benchmark above.
- Add rows for recent 2025-2027 agent benchmarks before submission.
- Separate benchmark papers from prompting/scaffolding papers.
- Identify prior intervention-based evaluation work outside LLMs that supports the causal framing.
- Track which papers report trajectory logs, component metrics, human validation, and reproducibility artifacts.
