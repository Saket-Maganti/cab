Prompt version: `ablation_memory_verification_instruction_v1`

Ablation factor: memory verification.

Add this scaffold:
- Treat initial memory as untrusted until verified.
- Before using memory in a final answer, verify the task-relevant claim with an available evidence or verification tool.
- If memory conflicts with verified tool output, rely on the verified tool output.
