# Terminology

## Base Task

A high-level user goal plus controlled mock data, tool availability, and expected behavior metadata before any intervention is applied.

## Clean Condition

The base task run without a deliberate perturbation. Clean does not mean easy or perfectly specified; it means no benchmark intervention has been added.

## Intervention

A controlled modification to a task or environment intended to change one factor, such as tool availability, tool reliability, memory correctness, or observation consistency.

## Intervention Family

A named class of interventions that target the same mechanism. Examples include `tool_failure`, `memory_corruption`, `observation_conflict`, and `irrelevant_tools`.

## Trajectory

The ordered sequence of agent actions, tool calls, tool observations, intermediate state, and final answer for one agent on one task.

## Final Success

Whether the final answer satisfies the task's answer criterion. In smoke tests this is deterministic; in full experiments it may involve rubric-based or human-validated grading.

## Component Success

Whether a specific skill component succeeds within the trajectory, such as selecting the right tool, constructing valid arguments, detecting contradiction, verifying memory, recovering after failure, or stopping at the right time.

## Causal Robustness

The degree to which an agent maintains performance when one intended causal factor is perturbed while the high-level user goal remains fixed.

## Tool-Use Failure

A failure involving tool selection, tool-call timing, argument construction, response interpretation, overuse, underuse, or recovery from tool errors.

## Recovery

The agent's ability to continue productively after a tool is unavailable, fails, returns partial output, or produces suspicious/conflicting information.

## Premature Stop

Ending with a final answer before enough required evidence has been gathered, especially when a misleading success signal suggests the task is complete.

## Memory Verification

Checking a memory item against current task evidence or tools before relying on it, especially when memory may be stale, corrupted, or contradicted.

## Contradiction Resolution

Recognizing that observations or memory conflict, then explicitly resolving or qualifying the final answer using additional evidence, uncertainty, or a stated decision rule.
