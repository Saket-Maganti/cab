# Blocked Items Board

Honest blockers as of Build Mode Phase 8. Update after each experiment milestone.

---

## Blocked by experiments

| Item | Owner | Priority | Blocker | Unblock action | Effort | Risk if ignored |
|---|---|---|---|---|---|---|
| C1–C8 empirical support | maintainers | P0 | No provider pilot | Complete 20-task pilot + analysis | days + $$ | Paper rejected for unsupported claims |
| C10 human agreement | maintainers | P0 | No annotations | Export sample + annotate | weeks | Validation claims impossible |
| Main 500 experiment | maintainers | P1 | MAIN_EXPERIMENT_GATE NO-GO | Pilot + human val + gate GO | weeks | No main-scale evidence |
| Paper results section | maintainers | P0 | Placeholders [N]…[rho] | fill-paper-from-run after verified pilot | hours | Camera-ready blocked |

## Unblocked (Phase 9)

| Item | Status | Notes |
|---|---|---|
| E2E pipeline validation | **done** | Mock micro demo — [demo/ENGINEERING_DEMO_BUNDLE.md](demo/ENGINEERING_DEMO_BUNDLE.md) |
| Build mode infrastructure | **done** | Phases 2–9; see [NEXT_DECISION.md](NEXT_DECISION.md) to pause |
| Advisor show-and-tell pack | **ready** | [handoff/ADVISOR_SHOW_AND_TELL_CHECKLIST.md](handoff/ADVISOR_SHOW_AND_TELL_CHECKLIST.md) |

## Blocked by human validation

| Item | Owner | Priority | Blocker | Unblock action | Effort | Risk if ignored |
|---|---|---|---|---|---|---|
| Trajectory failure labels | maintainers | P0 | No annotators | Run export-human-validation | days | C3 stays planned |
| Intervention validity audit | maintainers | P1 | No expert review | Advisor/expert subset review | days | Reviewer attack on construct validity |
| Judge calibration | maintainers | P2 | No human baseline | calibrate-llm-judge after annotations | days | Optional judge claims weak |

## Blocked by advisor feedback

| Item | Owner | Priority | Blocker | Unblock action | Effort | Risk if ignored |
|---|---|---|---|---|---|---|
| Pilot scale decision | user/advisor | P1 | Not discussed | Advisor meeting using bundle index | 1 meeting | Wrong N/K for pilot |
| ACRS design sign-off | user/advisor | P2 | Not reviewed | Share METRIC_CARD_ACRS + walkthroughs | async | Metric rework later |
| Related-work positioning | user/advisor | P2 | Partial bib pass | Complete RELATED_WORK_RELEVANCE_CHECKLIST | days | Weak related work section |

## Blocked by compute / runtime

| Item | Owner | Priority | Blocker | Unblock action | Effort | Risk if ignored |
|---|---|---|---|---|---|---|
| Clean local 20 completion | user | P2 | Long Ollama runs / interrupts | Limits + dedicated machine or skip to provider | overnight | False sense of local evidence |
| Batch main shards | maintainers | P1 | Main not started | batch-plan after gate GO | weeks | Cannot scale to 500 |

## Blocked by budget

| Item | Owner | Priority | Blocker | Unblock action | Effort | Risk if ignored |
|---|---|---|---|---|---|---|
| Provider pilot 20 | user | P0 | No budget approval | Approve cap; set allow_paid_calls | $$ | No real agent data |
| Commercial 100 pilot | user | P1 | No 20-task pilot | Sequential gate in freeze checklist | $$$ | Overspend / premature scale |
| Main 500 | user | P1 | No main budget | estimate-cost + advisor approval | $$$$ | Cannot run main claim |

## Blocked by paper writing

| Item | Owner | Priority | Blocker | Unblock action | Effort | Risk if ignored |
|---|---|---|---|---|---|---|
| Abstract empirical sentences | maintainers | P0 | Placeholders | Experiments or rewrite as proposed work | hours | Overclaim in abstract |
| Results figures 2–6 | maintainers | P0 | No pilot data | Export after verified run | hours | Fake figures temptation |
| Human validation section | maintainers | P0 | No κ stats | Annotations | weeks | Empty validation section |

## Blocked by citation review

| Item | Owner | Priority | Blocker | Unblock action | Effort | Risk if ignored |
|---|---|---|---|---|---|---|
| Recent agent benchmarks | maintainers | P2 | Incomplete reads | RELATED_WORK_TRACKER pass | days | Stale related work |
| Causal eval citations | maintainers | P3 | Partial coverage | Bibliography audit | days | Missing positioning |

## Blocked by release / legal / licensing

| Item | Owner | Priority | Blocker | Unblock action | Effort | Risk if ignored |
|---|---|---|---|---|---|---|
| Public repro bundle | maintainers | P2 | No frozen release tag | plan-repro-bundle after pilot | days | Artifact eval weak |
| Data license finalization | maintainers | P3 | Synthetic only so far | Confirm DATA_LICENSE.md at scale | hours | Distribution questions |

---

See [MASTER_STATUS.md](MASTER_STATUS.md), [PROJECT_HEALTH.md](PROJECT_HEALTH.md), [experiments/PRE_EXPERIMENT_FREEZE_CHECKLIST.md](experiments/PRE_EXPERIMENT_FREEZE_CHECKLIST.md).
