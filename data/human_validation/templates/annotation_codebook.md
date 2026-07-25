# Annotation Codebook

Dry-run / protocol scaffolding only. No annotations exist yet.

## Validity questions

- `task_understandable_yes_no`: Can a competent annotator understand the task without hidden repo context?
- `intervention_isolation_valid_yes_no`: Does the intervention vary one intended factor only (C10)?
- `gold_answer_correct_yes_no`: Is the reference gold answer plausible and complete?
- `trajectory_label_valid_yes_no`: Does the predicted failure category match visible trajectory evidence (C3)?

## Invalid sample flags

Set `invalid_sample_flag=true` for leakage, missing steps, ambiguous instructions, or PII.
Record `invalid_sample_reason`. Invalid items are excluded from agreement metrics.

## Failure categories

tool_overuse, premature_stopper, contradiction_blind, memory_blind, argument_sloppy,
recovery_weak, final_answer_hallucinator, retry_loop_agent, other, no_failure_detected
