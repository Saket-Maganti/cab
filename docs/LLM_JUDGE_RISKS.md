# LLM Judge Risks

LLM judges can make annotation cheaper, but they introduce risks that are especially serious for a benchmark about agent skill. This document lists the default safeguards.

## Risks

- **Circular evaluation:** The same model family may appear as both agent and judge.
- **Position and order bias:** A judge may prefer the first answer or the answer presented last.
- **Verbosity bias:** Longer answers may appear more justified even when wrong.
- **Agent-name bias:** The judge may treat known agent or model names as quality signals.
- **Prompt sensitivity:** Small prompt changes can change labels.
- **Model-version drift:** Provider-side changes can alter judge behavior over time.
- **Overconfidence:** A judge can produce confident labels for underspecified evidence.
- **Intervention misunderstanding:** A judge may treat an intended limitation or uncertainty answer as a normal failure.
- **Ground-truth leakage:** If hidden labels are exposed in prompts, agreement can be inflated.

## Safeguards

- Judge labels are written to `judge_labels.jsonl` and never overwrite deterministic scores or human annotations by default.
- Every judge run requires explicit provider, model, prompt version, temperature, max tokens, and retry settings.
- Prompt hashes and config hashes are recorded.
- Calibration compares judge labels to a human validation subset before any scientific use.
- Reports include agreement, bias by agent/model family, sensitivity to answer length, and answer-order sensitivity.
- Provider API keys stay in environment variables and are never printed or saved.
- Oracle-agent results must remain sanity-check upper bounds and should not be used to claim realistic judge agreement.

## Use In The Paper

The paper must not state that LLM judge labels are ground truth unless:

- human validation has been completed,
- judge-human agreement is reported,
- systematic disagreements are analyzed,
- prompts, model ids, prompt hashes, scorer versions, seeds, configs, run directories, and git commits are linked,
- the claim ledger records the evidence.

Until then, judge outputs are exploratory diagnostics only.
