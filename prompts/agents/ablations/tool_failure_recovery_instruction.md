Prompt version: `ablation_tool_failure_recovery_instruction_v1`

Ablation factor: tool-failure recovery.

Add this scaffold:
- If a tool fails, inspect the error before acting again.
- Do not repeat the same failed call with identical arguments.
- Recover by repairing arguments, choosing another relevant tool, or stating the limitation.
