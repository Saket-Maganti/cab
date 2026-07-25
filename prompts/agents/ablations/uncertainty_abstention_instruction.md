Prompt version: `ablation_uncertainty_abstention_instruction_v1`

Ablation factor: uncertainty and abstention.

Add this scaffold:
- If required evidence is missing, failed, corrupted, ambiguous, or contradictory, do not guess.
- State uncertainty or abstain when the available tools cannot support a reliable final answer.
- Separate verified facts from limitations.
