# Baseline And Ablation Matrix

Status: future design only.

| baseline | hypothesis | required config fields | trajectory metadata | supports if run | cannot support |
|---|---|---|---|---|---|
| direct answer | measures tool-free guessing/priors | `agent=direct_answer`, no tool calls | final answer, abstention flag | lower-bound behavior | tool-use robustness |
| ReAct tool user | measures basic tool-use planning | tool schema, max steps | thought/action/observation sequence | standard agent comparison | provider-general claims alone |
| function-calling | measures structured call reliability | function schema, parser policy | parse outcomes, invalid call count | tool schema robustness | natural language planning claims alone |
| self-checking | tests verification behavior | self-check prompt, verification budget | verification calls, correction events | recovery/verification hypotheses | causal claims without C10 |
| recovery-aware | tests response to errors | retry/backoff policy | error detection, alternate route | tool-failure robustness | global model quality |
| abstention-aware | tests safe uncertainty | abstention policy | uncertainty/refusal reason | ambiguity safety | success-only leadership |
| oracle/stub engineering-only | pipeline sanity | local stub/oracle marker | synthetic flag | engineering reproducibility | scientific model performance |

No baseline is authorized for execution by this matrix.
