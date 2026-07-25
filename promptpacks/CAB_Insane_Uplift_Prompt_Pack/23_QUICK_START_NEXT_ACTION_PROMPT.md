# Quick Start Prompt — The Next Best CAB Action

You are working in `/Users/saketmaganti/Projects/causal-agent-bench`.

You are Codex acting as a benchmark scientist and evidence-safety auditor.

The external audit says CAB is currently scaffold-heavy: real provider evidence 0, human validation 0, C1-C8/C10 planned/unsupported, C9 engineering-only. Do **not** add broad governance. The next scientific gate is Compact-20 review and first 3-model pilot preparation.

## Task

Start the next best no-execution action:

1. verify repo reality,
2. identify the current Compact-20 slice,
3. inspect gold/scorer/leakage blockers,
4. create or update the reviewed Compact-20 manifest,
5. prepare the real human review packet,
6. do not run models/providers.

## Global Evidence Rules

- Do not fabricate results, human annotations, provider outputs, costs, or reviewer labels.
- Do not promote C1-C8/C10 unless the required real evidence exists and the evidence-safety checks pass.
- C9 may remain `engineering_only`; stub/mock/dry-run outputs can only support pipeline wiring.
- Do not mark paper assets eligible manually.
- Do not store API keys, tokens, or secrets in YAML, Markdown, JSON, logs, CSVs, or repo files.
- Provider credentials must be checked only through environment presence checks without printing values.
- Do not leave `allow_paid_calls=true` after any live run.
- Do not run providers, local LLMs, `causal_agent_bench run`, `main_200`, `main_500`, Compact-50, or broad sweeps unless the prompt explicitly allows it and every gate passes.
- Always distinguish `engineering_only`, `zero_cost_local_preliminary`, `provider_pilot_preliminary`, `paper_candidate_pending_audit`, and `paper_eligible`.


## Deliver

- `reports/NEXT_ACTION_COMPACT20_READINESS.md`
- reviewed slice status,
- human review packet status,
- exact blockers,
- commands run,
- next prompt to execute.

## Final response

# CAB Next Action Report

## 1. Executive Summary
## 2. Repo Reality
## 3. Compact-20 Slice Status
## 4. Gold/Scorer/Leakage Blockers
## 5. Human Review Packet
## 6. Files Added
## 7. Tests/Checks Run
## 8. Evidence State
## 9. Next Prompt to Run

Final verdict must be one of:

- `COMPACT20_NEXT_ACTION_COMPLETE`
- `COMPACT20_BLOCKED_NEEDS_REPAIR`
- `CAB_BLOCKED_REPO_STATE_UNCLEAR`
