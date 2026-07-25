# Related Work Matrix V2

Status: positioning matrix with citation TODOs. Do not fabricate citations.

| area | examples | likely overlap | CAB distinction | citation status |
|---|---|---|---|---|
| task-oriented agent benchmarks | tau-bench | tool/task success | paired clean/intervention robustness | TODO verify citation |
| adversarial tool-use benchmarks | AgentDojo | safety and adversarial behavior | controlled goal-preserving perturbations with ACRS | TODO verify citation |
| broad agent benchmarks | AgentBench, AgentBoard | multi-domain evaluation | intervention-family validity and rank instability | TODO verify citation |
| tool-use datasets | ToolBench | API/tool-call skill | perturbation robustness and scorer governance | TODO verify citation |
| web/computer benchmarks | WebArena, OSWorld | realistic environments | CAB is controlled and local-first | TODO verify citation |
| software engineering benchmarks | SWE-bench | code issue resolution | not code-only; tool/recovery stress factors | TODO verify citation |
| broad model eval | HELM-style evaluation | standardized reporting | paired causal-stress design and evidence gates | TODO verify citation |
| robustness benchmarks | stress tests | perturbation evaluation | human-validated intervention isolation target | TODO verify citation |

## Novelty Claims To Keep Bounded

- paired clean/intervention design,
- explicit intervention-family taxonomy,
- ACRS and rank-instability metrics,
- scorer sanity and human C10 isolation gates,
- no-execution release discipline.
