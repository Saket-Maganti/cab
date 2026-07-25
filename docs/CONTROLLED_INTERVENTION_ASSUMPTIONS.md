# Controlled Intervention Assumptions

Status: assumptions register. None of these assumptions are validated yet.

## Assumption A1: Goal Preservation

The intervention keeps the high-level user goal unchanged. Valid answer form may change only when the intervention makes the original route unavailable or unsafe. Review question: would a human say the clean and intervention tasks are still the same practical task?

## Assumption A2: Single-Factor Change

Each intervention family has one intended changed factor. Non-target changes must be absent or documented as exclusion reasons. Examples of forbidden confounds include changing both tool availability and hidden ground truth, or adding ambiguity while also changing success criteria.

## Assumption A3: Scoring Policy Stability

The scorer must evaluate clean and intervention tasks according to a documented policy. If the intervention changes the valid final answer, the gold policy must say so explicitly before any run.

## Assumption A4: Comparable Evidence Access

Apart from the intended perturbation, the agent should have comparable access to required evidence. Removing all routes to success without allowing abstention creates an invalid robustness test.

## Assumption A5: Trajectory Auditability

Tool calls, observations, final answers, errors, uncertainty statements, and stop reasons must be stored so scorer and human reviewers can reconstruct why a trajectory passed or failed.

## Assumption A6: Human Isolation Review

C10 requires real human reviewers to check goal preservation, isolation, gold policy, and confounding. AI-proxy review cannot satisfy C10.

## Failure Modes

- Answer-changing interventions without updated gold policy.
- Tool failures that also remove tool availability.
- Memory corruption that changes hidden ground truth.
- Observation conflicts that make the task impossible but still require a definitive answer.
- Distractors that introduce a second valid answer.

## Current State

Current CAB state is no-execution: provider-backed evidence is absent, human annotations are absent, and C10 is blocked. These assumptions are design constraints only.
