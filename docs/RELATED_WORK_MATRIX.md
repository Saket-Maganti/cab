# Related Work Matrix

Comparison of benchmarks and evaluation frameworks cited in `paper/sections/02_related_work.tex` against **CausalAgentBench (CAB)**. Legend: **Y** = primary focus, **P** = partial or secondary, **N** = not a stated focus. This table summarizes positioning only; it does not claim CAB has been validated at NeurIPS scale.

| Paper | Task type | Environment | Final score vs trajectory | Interventions / perturbations | Causal framing | Tool failure | Memory corruption | Contradiction handling |
|---|---|---|---|---|---|---|---|---|
| **CausalAgentBench (this work)** | Tool-using agent tasks (multi-domain synthetic + optional web shadow) | Deterministic simulated tools; optional frozen web snapshots | Both: task success + trajectory/component metrics | **Y**: paired clean/intervention instances per family | **Y**: explicit paired estimand + audits | **Y** | **Y** | **Y** |
| AgentBench | Multi-environment agents | Mixed (games, web, APIs, etc.) | Mostly final success per env | P: diverse envs, not single-factor paired | N | P | P | N |
| GAIA | General assistant QA | Real tools / web / files as needed | Final answer correctness | N | N | P | N | N |
| AgentBoard | Multi-turn agents (embodied, web, tools) | 9 interactive environments | **Y** progress rate + sub-skills + success | P: harder/easy splits, not named tool interventions | N | P | P | N |
| Toolformer | Tool-call learning | API/tool simulation for training | Tool-call accuracy / downstream LM | N | N | N | N | N |
| ReAct | Prompting method | User-provided envs | Trajectory via action traces (method, not benchmark) | N | N | P | P | N |
| API-Bank | Tool-augmented dialogue | Simulated APIs + dialogue | Dialogue + API call success | N | N | P | N | N |
| ToolLLM / ToolBench | Large-scale API use | Real/mirrored APIs at scale | API execution success | P: API instability as noise | N | P | N | N |
| Gorilla / APIBench | API call generation | API docs + execution checks | API match / execution | N | N | P | N | N |
| StableToolBench | Tool-learning benchmark stability | Large API suite with stability fixes | Tool-call success under stable APIs | P: reduces external API variance | N | P | N | N |
| $\tau$-bench | Tool–agent–user customer service | DB + APIs + simulated user | End-state DB match (+ pass^k reliability) | P: stochastic user phrasing | N | P | P | P (policy conflicts) |
| World of Bits / MiniWoB | Web navigation RL | Simulated web UIs | Reward / task success | P: env stochasticity | N | N | N | N |
| Mind2Web | Generalist web agent | Real websites (offline traces) | Action sequence / task success | N | N | N | N | N |
| WebArena | Autonomous web agents | Self-hosted realistic sites | Task success in browser | P: site/version changes | N | P | N | N |
| WebShop | Grounded e-commerce dialogue | Simulated shopping site | Purchase / goal match | N | N | N | N | N |
| VisualWebArena | Multimodal web agents | Visual web environments | Task success | P: visual/UX variation | N | P | N | N |
| OSWorld | Desktop / OS multimodal agents | Real computer VMs | Task success in OS | P: open-ended tasks | N | P | P | N |
| SWE-bench | Software engineering repair | Real GitHub repos | Issue resolution (tests pass) | P: repo/issue variation | N | P (editors, CI) | P (retrieval) | N |
| Process supervision (step verify) | Math reasoning | Static problems | Step-level + final | N | N | N | N | N |
| HELM | Holistic LLM eval | Many scenarios | Many metrics, mostly outputs | **Y** multi-scenario stress, not paired agent tasks | N | N | N | N |
| BIG-bench | Broad LM tasks | Static / light interaction | Task accuracy | P: diverse tasks | N | N | N | N |
| DecodingTrust | Trustworthiness / robustness | Many GPT stress tests | Scenario pass rates | **Y** adversarial/OOD suites | N | N | N | N |
| Pearl / Holland (foundations) | Causal inference theory | N/A | N/A | **Y** (conceptual) | **Y** (theory) | N | N | N |
| LLM-as-judge (MT-Bench) | Chat preference judging | Static multi-turn chats | Model-judge scores vs humans | N | N | N | N | N |

## How to use this matrix

- Add a row only after a BibTeX entry exists in `paper/references.bib` and the one-sentence positioning in `paper/sections/02_related_work.tex` has been checked against the source paper.
- Do not treat **Y** in CAB columns as evidence of completed experiments; it marks design intent documented in benchmark cards and intervention specs.
- Papers marked **Pending** in `docs/RELATED_WORK_TRACKER.md` should not appear here until cited.

## Maintenance

Run `python scripts/check_bibliography.py` (also invoked by `make paper-check`) to ensure every `\cite{...}` key in related work resolves to a bibliography entry and no `todo_` citation keys remain.
