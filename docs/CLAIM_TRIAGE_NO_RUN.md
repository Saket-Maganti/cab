# Claim Triage, No-Run State

All rows reflect the current no-run state. This document is `engineering_only`, `manual_review_pending`, and `no_provider_evidence`.

| Claim | Current status | Evidence required | Mention now? | Minimum later validation | Safest wording |
|---|---|---|---|---|---|
| C1 clean success overestimates robustness | Planned / unsupported | Paired provider runs with intervals showing clean-to-intervention degradation | Planned only | Compact-20/50 provider run, post-run audit, claim safety pass | We plan to test whether clean success overstates robustness. |
| C2 tool failure and memory corruption expose weaknesses | Planned / unsupported | Per-family provider results and audited trajectories | Planned only | Provider run covering tool failure and memory corruption with scorer sanity | CAB includes intervention families designed to probe tool failure and memory handling. |
| C3 trajectory metrics detect failures missed by final answers | Planned / unsupported | Real trajectories plus human audit of hidden failures | Planned only | Provider outputs, trajectory audit, at least two reviewers for sampled cases | Trajectory metrics are planned diagnostics, not validated evidence. |
| C4 ACRS changes rankings | Planned / unsupported | Rank comparison with uncertainty across models | Planned only | Multi-model provider run, rank uncertainty, sensitivity analysis | ACRS is intended to test ranking instability. |
| C5 recovery is separable from planning | Planned / unsupported | Component analysis or scaffold ablation showing separability | Planned only | Provider trajectories and targeted ablation | Recovery and planning are measured separately by design. |
| C6 self-checking improves some families | Planned / unsupported | Fixed-task scaffold ablation | Planned only | Controlled ablation after Compact-20/50 | Self-checking is a future ablation, not a result. |
| C7 some agents overuse tools | Planned / unsupported | Irrelevant-tool intervention results and tool-use rates | Planned only | Provider run plus tool-call audit | Tool overuse is a planned diagnostic. |
| C8 premature success signals cause early stopping | Planned / unsupported | Premature-success intervention results and examples | Planned only | Provider run plus failure taxonomy audit | Early stopping is a planned failure family. |
| C9 smoke reproducibility without paid services | Engineering-only | Fresh install/help/smoke/static checks | Yes, with engineering-only label | Clean-clone reproduction log | Local smoke and static checks can support engineering readiness only. |
| C10 controlled interventions isolate intended skill components | Planned / unsupported | Human/expert intervention-isolation review with agreement | Planned only | Completed C10 packet with two reviewers and adjudication | Intervention isolation remains a validation target. |

## Summary

C1-C8 and C10 must remain planned/unsupported until real provider/model evidence and human validation exist. C9 may be described only as engineering reproducibility, not scientific benchmark validity.

