Prompt version: `ablation_contradiction_resolution_instruction_v1`

Ablation factor: contradiction resolution.

Add this scaffold:
- Look for contradictions between memory, tool outputs, and previous observations.
- If evidence conflicts, acknowledge the conflict.
- Resolve it with a verification tool when available, or state that the conflict remains unresolved.
