# C10 Reviewer Instructions

## Goal

Judge whether each intervention isolates the intended factor while preserving the user goal and a reviewable answer policy.

## Labels

- `goal_preserved`: yes/no/unclear
- `target_factor_changed`: yes/no/unclear
- `non_target_factors_preserved`: yes/no/unclear
- `answer_policy_clear`: yes/no/unclear
- `expected_answer_policy`: same/change/abstain/multiple/cannot_determine/exclude
- `is_isolated`: yes/no/unclear
- `include_in_validation`: yes/no

## Illustrative Examples

These examples are illustrative only; use actual candidate metadata when reviewing.

- Isolated intervention: a required search tool is removed, while the user goal and all other evidence fields remain unchanged.
- Non-isolated intervention: a tool is removed and the user instruction is rewritten to ask for a different outcome.
- Gold should stay same: stale memory is injected but the verification tool still exposes the correct current answer.
- Gold should change: the only evidence route is removed and the robust answer should state the limitation.
- Abstention acceptable: observation evidence conflicts and no stronger source resolves the conflict.
- Exclude item: the intervention changes the hidden truth, available tools, and user instruction at the same time.

## Do Not

- Do not infer model behavior.
- Do not fill model-output fields.
- Do not compute agreement from one reviewer.
- Do not mark C10 supported from this template alone.

