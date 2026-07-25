# Risk Register

| Risk ID | Risk | Severity | Probability | Detection | Mitigation | Owner | Status |
|---|---|---:|---:|---|---|---|---|
| R01 | Local Ollama runs too slow for iteration | High | High | `plan-run`, interrupted runs | Micro configs, run limiters, stub/mock first | Maintainers | Open |
| R02 | Paid provider pilot too expensive | High | Medium | `estimate-cost`, budget caps | `allow_paid_calls: false` default; pilot_20 before main_500 | Maintainers | Open |
| R03 | Synthetic benchmark criticized as unrealistic | Medium | High | Reviewer packet, mini-study plan | Bounded claims; web-shadow track; limitations section | Authors | Open |
| R04 | Causal wording overclaimed | High | Medium | Claim ledger, paper sync map | Paired interventions + audit; bounded causal language | Authors | Mitigated (scaffold) |
| R05 | ACRS composite too simple | Medium | Medium | Metric card, ablation plan | Report component metrics; human validation on disagreements | Authors | Open |
| R06 | Human validation delayed | High | Medium | Submission readiness checker | Pre-built export protocol; stratified sample plan | Maintainers | Open |
| R07 | Model API version drift | Medium | High | Run metadata model IDs | Freeze provider registry; pin configs | Maintainers | Open |
| R08 | Incomplete run accidentally cited | High | Medium | `check_evidence_safety`, score guards | `INCOMPLETE_RUN.json`; refuse score/export by default | Maintainers | Mitigated |
| R09 | Oracle agent contamination | High | Low | Run index oracle flags | Exclude oracle from leaderboards; filter in analysis | Maintainers | Mitigated |
| R10 | Task generator template bias | Medium | Medium | Dataset audit, template registry | Domain/family balance warnings; held-out templates | Maintainers | Open |
| R11 | Benchmark overfitting via dev tuning | Medium | Medium | Contamination audit, split policy | Freeze splits; separate held-out templates | Maintainers | Open |
| R12 | Missing citation relevance | Low | Medium | Bibliography check | Related work tracker; claimref audit | Authors | Open |
| R13 | Reviewer: “not novel” | Medium | Medium | Reviewer packet, attack matrix | Emphasize intervention methodology + diagnostics | Authors | Open |
| R14 | Reviewer: “engineering only” | High | High | Evidence level policy | Provider pilot + human validation before claims | Authors | Open (expected now) |
| R15 | Claims exceed evidence | High | Medium | Claim ledger validator, paper sync map | Draft vs submission modes; no mock→supported | Maintainers | Mitigated (scaffold) |

**Review cadence:** Update before each experiment stage transition and before submission.
