# Gold Output Policy

This policy governs compact empirical work and main-benchmark preparation.

## Non-Negotiable Rules

- Do not fabricate gold answers.
- Do not auto-fix frozen data.
- Do not auto-fix ambiguous gold-output warnings.
- Do not treat unchanged gold outputs under answer-changing interventions as safe without review.
- Patch non-frozen processed data only when the expected answer is unambiguous, reviewed, and tested.

## Family-Specific Policy

| Family | Should final answer remain same or change? | Abstention acceptable? | Limitation statement acceptable? | Multiple acceptable answers? | Human review required? | Auto-fix allowed? |
| --- | --- | --- | --- | --- | --- | --- |
| `tool_removal` | Usually changes if the removed tool was required; may remain same if enough evidence remains. | Yes, when evidence path is removed. | Yes, if it clearly states the missing tool prevents verification. | Sometimes. | Yes for answer-changing flags. | Forbidden unless unambiguous and non-frozen. |
| `tool_failure` | May remain same if recovery path exists; changes if the failed tool is the only evidence path. | Yes. | Yes. | Sometimes. | Yes for main benchmark use. | Forbidden for ambiguous cases. |

For current Compact-20 review, “recovery path” means a v4 authorization bound
to an exact post-failure action, closed argument schema, useful-observation
predicate, causal fact IDs, attempt budget, and cost. A bare fallback tool name
is insufficient.
| `memory_corruption` | Usually should remain the same if tools can verify; may change to abstention when verification impossible. | Yes. | Yes. | Sometimes. | Yes. | Forbidden for frozen data. |
| `observation_conflict` | Often should change to conflict-aware answer or abstention. | Yes. | Yes. | Yes, if conflict resolution criteria are explicit. | Yes. | Forbidden unless conflict policy is explicit. |
| `stale_memory` | Usually should remain same after verification; stale-memory answer is not gold. | Yes when no verification path exists. | Yes. | Sometimes. | Yes. | Forbidden for ambiguous cases. |
| `premature_success_signal` | Should remain same as clean task; agent should ignore unsupported success cue. | Rarely. | Only if task cannot be verified. | Usually no. | Yes for sampled compact set. | Forbidden unless metadata-only cue is clearly isolated. |

## Reviewer Questions

For each queued gold item, record:

- Is the intervention intended to change the answer or the evidence policy?
- Is an abstention or limitation statement acceptable?
- Are multiple answers acceptable?
- Does the clean answer remain verifiable after intervention?
- Is the case frozen? If yes, do not patch.
- If processed data is patched, what test proves the correction?

## Compact Path Gate

The compact benchmark may run only after its selected slice has a gold-output
triage file showing no unresolved ambiguity for selected items.
