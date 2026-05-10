# Internal Review Round 1

Reviewer stance: reject unless the authors prove this is more than a software scaffold and stop implying empirical findings before running the main experiments.

## Issue Checklist

| ID | Severity | Type | Location | Explanation | Required fix | Fixed |
|---|---|---|---|---|---|---|
| R1 | fatal | validity / clarity | `paper/sections/00_abstract.tex`, `paper/sections/01_introduction.tex` | The draft used "we find" and "we evaluate and show" with bracket placeholders. That is still an unsupported result claim. | Downgrade to planned tests or protocol language until final runs exist. | Yes |
| R2 | major | novelty | `paper/sections/02_related_work.tex`, `docs/INTERVENTIONS.md` | The framing risked sounding like ordinary perturbation robustness with a new name. It did not state the estimand clearly enough. | Explain that paired interventions target named skill components and require intervention-validity audit. | Yes |
| R3 | major | validity | `docs/INTERVENTIONS.md`, `paper/sections/04_interventional_framework.tex` | Intervention realism was underdeveloped. A reviewer could say these are toy perturbations disconnected from real agent failures. | Add realistic analogues, expected robust behavior, and explicit realism limitations. | Yes |
| R4 | major | validity | `docs/DATASET_CARD.md`, `paper/sections/03_benchmark_design.tex` | Synthetic tasks are easy to dismiss as fake. The paper needs to justify why simulation is scientifically useful. | State the causal-control argument and admit external-validity limits. | Yes |
| R5 | major | metric validity | `docs/METRICS.md`, `paper/sections/05_metrics.tex` | ACRS is a crude ratio. Alone it can reward uniformly bad agents or blow up when clean success is low. | Emphasize ACRS as one summary metric, always reported with clean/intervention success and diagnostics. | Yes |
| R6 | major | metric validity | `docs/METRICS.md` | Deterministic scoring is keyword/heuristic-based, so paper claims about hidden failures are not reliable without human validation. | Strengthen warning that binary metrics are heuristic indicators, not causal truth. | Yes |
| R7 | fatal if unresolved | validity / engineering | `src/causal_agent_bench/agents/planner_executor_stub_agent.py` | The planner-executor baseline used schema-native gold tool sequences, leaking oracle metadata into a supposedly non-oracle baseline. | Remove schema-native gold-sequence use; add regression test. | Yes |
| R8 | major | validity | `docs/BASELINE_AGENTS.md`, `paper/sections/06_experimental_setup.tex` | Baselines are too weak for a paper. Stub agents validate mechanics, not scientific claims about LLM agents. | Require non-oracle LLM-backed agents for paper claims and separate oracle results. | Yes |
| R9 | major | reproducibility | `src/causal_agent_bench/runners/experiment.py` | Resume could silently append trajectories from a different config. That corrupts runs. | Reject resume when config hash differs; add test. | Yes |
| R10 | major | reproducibility | `README.md` | README still pointed scoring at `results/smoke`, which is stale for timestamped experiment runs. | Update commands to timestamped run dirs and dev-run workflow. | Yes |
| R11 | major | validity | `docs/CLAIM_LEDGER.md`, `paper/sections/07_results.tex` | Most scientific claims remain unproven. This is acceptable only if brutally explicit. | Keep claim ledger statuses planned/engineering-only and results section as TODO planned tests. | Yes |
| R12 | major | ethics | `docs/ETHICS_AND_LIMITATIONS.md`, `paper/sections/11_ethics_reproducibility.tex` | Release risks include benchmark gaming, contaminated training, and mistaken leaderboard use. | Add explicit misuse and responsible-release guidance. | Yes |
| R13 | minor | engineering | `paper/` | LaTeX generated auxiliary files should not be tracked. | Ignore paper aux/log/out/toc artifacts. | Yes |
| R14 | major | reproducibility | project environment | Local `python` shim points to a missing pyenv 3.11. A clean user may fail with `python`. | Document `python3` fallback; keep Python 3.11 tests passing. | Partially |
| R15 | major | validity | human validation docs | Human validation is planned but not operationalized into runnable annotation tooling. | Future fix: add annotation schema, sampled validation set, and agreement scripts. | No |
| R16 | major | novelty / related work | `docs/RELATED_WORK_TRACKER.md`, `paper/references.bib` | Related work remains TODO placeholders. A real submission would be rejected for missing citations. | Future fix: fill exact citations and sharpen differentiation. | No |
| R17 | major | external validity | benchmark design | No live web/browser/enterprise runs. The benchmark currently proves control, not deployment realism. | Future fix: add optional messy-environment suite after controlled suite is audited. | No |
| R18 | minor | code quality | analysis outputs | Analysis can generate many global files, which is useful but noisy. | Keep deterministic scripts; future fix could add `--no-global` CLI option. | No |

## Verdict Before Fixes

Reject. The repo was promising but too easy to attack on three fronts: unsupported result language, oracle leakage in a non-oracle baseline, and weak intervention-realism framing.

## Verdict After Fixes

Still not submission-ready, but no longer dead on arrival as a research artifact. It is ready for a real experiment run only after LLM-backed agents, human validation, and related-work citations are added.
