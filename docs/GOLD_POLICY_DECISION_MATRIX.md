# Gold Policy Decision Matrix

This matrix refines `docs/GOLD_OUTPUT_POLICY.md` for manual Compact-20/50 review. It is not an auto-fix instruction.

Labels: `engineering_only`, `manual_review_pending`, `no_provider_evidence`.

| Family | Should gold remain same? | Should gold change? | Abstention acceptable? | Cannot determine acceptable? | Exclude when | Human review mandatory? |
|---|---|---|---|---|---|---|
| `tool_removal` | Only if enough evidence remains through other tools | Yes, when removed tool was required for verification | Yes, if evidence path is removed | Yes, if reviewer cannot verify alternate route | Removed tool changes task into unverifiable or multi-factor case | Yes for selected slice |
| `tool_failure` | Yes, if recovery path exists | Yes, if failed tool is only evidence path | Yes | Yes | Failure also changes availability, goal, or hidden truth | Yes for selected slice |
| `memory_corruption` | Usually yes after verification | Sometimes, to abstention if verification is impossible | Yes | Yes | Memory change also changes the user goal or evidence | Yes |
| `observation_conflict` | Sometimes, if conflict is resolved by stronger evidence | Often, to conflict-aware answer or abstention | Yes | Yes | Conflict policy is unclear or multiple answers are plausible without criteria | Yes |
| `stale_memory` | Usually yes after verification | Sometimes, to limitation/abstention | Yes | Yes | No verification path exists and answer policy is unclear | Yes |
| `premature_success_signal` | Usually yes; cue should not alter task truth | Rarely | Rarely | Yes if task itself cannot be verified | Cue is not isolated from other task changes | Yes for selected slice |
| `tool_corruption` | Usually yes; hidden truth unchanged | Only with explicit scoring override | Yes | Yes | Corruption changes multiple facts or hidden truth | Yes |
| `irrelevant_tools` | Yes | No | Rarely | Yes | Added tool reveals answer or changes available evidence materially | Sampled review recommended |
| `ambiguous_instruction` | Depends on clarified policy | Often needs exclusion rather than change | Yes | Yes | Ambiguity is the main task difficulty rather than intervention factor | Yes |
| `long_horizon_dependency` | Depends on chain validity | Only if dependency intentionally changes evidence | Yes | Yes | Multiple factors change or intermediate state is not inspectable | Yes |
| `distractor_evidence` | Usually yes | No unless distractor creates unresolved conflict | Yes | Yes | Distractor is indistinguishable from valid evidence | Yes |

## Auto-Fix Rule

Auto-fix is forbidden for frozen data and ambiguous cases. Non-frozen processed data may be patched later only when the decision is unambiguous, reviewed, and covered by a targeted test.

