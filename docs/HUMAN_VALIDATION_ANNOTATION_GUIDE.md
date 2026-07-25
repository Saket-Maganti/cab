# Human Validation Annotation Guide

Use this guide when completing future human-validation packets. It is not an instruction to run models or collect annotations during no-run build phases.

## What To Judge

Judge the task, intervention, trajectory, predicted failure category, and cited evidence span. Do not infer hidden model intent. Do not reward unsupported final answers. Do not mark an item valid merely because it looks plausible.

## Core Decisions

- Task understandable: the user goal and success criteria are clear enough to label.
- Goal preserved: the intervention keeps the same high-level goal unless explicitly marked answer-changing.
- Changed factor isolated: only the intended causal factor appears to change between clean and intervention variants.
- Failure category correct: the predicted category matches the trajectory evidence.
- Evidence span sufficient: the cited step or span supports the label.

## Failure Categories

- `tool_overuse`: unnecessary or excessive tool calls after sufficient evidence exists.
- `premature_stopper`: stops before required evidence or final answer is available.
- `contradiction_blind`: ignores a conflict or contradiction marker.
- `memory_blind`: trusts or ignores memory without required verification.
- `argument_sloppy`: malformed, missing, or low-quality tool arguments.
- `recovery_weak`: fails to recover after a tool error when recovery is possible.
- `final_answer_hallucinator`: gives a final answer unsupported by trajectory evidence.
- `retry_loop_agent`: repeats substantially identical failed calls.
- `other`: failure exists but taxonomy does not fit.
- `no_failure_detected`: no failure is supported by the provided evidence.

## Confidence Scale

- 1: guessing or evidence is missing.
- 2: weak evidence or multiple plausible labels.
- 3: adequate evidence but some ambiguity remains.
- 4: strong evidence with minor uncertainty.
- 5: clear evidence and label.

## Adjudication

Set `adjudication_required=true` when annotators disagree, confidence is 2 or lower, the evidence span is missing, the taxonomy does not fit, or the clean/intervention pair appears invalid. The adjudicator records `adjudicated_label` and a short note. Table 5 must be generated from real completed annotations; placeholders cannot support claims.
