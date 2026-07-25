Prompt version: `ablation_self_check_instruction_v1`

Ablation factor: self-check before final answer.

Add this scaffold:
- Before finalizing, check whether each required information item is supported by an observation.
- If support is missing, call one useful tool or state that the answer is not fully supported.
- Do not present hidden assumptions as evidence.
