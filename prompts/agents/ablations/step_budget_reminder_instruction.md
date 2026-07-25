Prompt version: `ablation_step_budget_reminder_instruction_v1`

Ablation factor: step budget reminder.

Add this scaffold:
- Track how many tool-use steps remain.
- Prefer the fewest sufficient tool calls.
- If the task cannot be completed within the remaining budget, state the limitation instead of looping.
