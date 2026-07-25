# Error Taxonomy

This taxonomy is used to mine candidate trajectory failures from run artifacts. The labels are deterministic audit aids, not final scientific evidence. Paper claims about failure prevalence or label quality require real provider-backed runs and human validation.

## Taxonomy

| Slug | Error type | Expected behavior |
|---|---|---|
| `wrong_tool_selected` | Wrong tool selected | Choose tools that are available and causally relevant to the requested evidence. |
| `required_tool_omitted` | Required tool omitted | Call every required evidence-gathering tool before answering, unless abstention is warranted. |
| `tool_argument_malformed` | Tool argument malformed | Construct arguments that satisfy the declared tool-call schema. |
| `tool_argument_semantically_wrong` | Tool argument semantically wrong | Use arguments that preserve the user's entity, filter, and constraint intent. |
| `observation_ignored` | Observation ignored | Ground later actions and the final answer in observations actually returned by tools. |
| `contradiction_missed` | Contradiction missed | Detect conflicting observations or intervention-induced contradictions. |
| `contradiction_noticed_but_unresolved` | Contradiction noticed but unresolved | Resolve the conflict with evidence or report calibrated uncertainty. |
| `blind_trust_in_corrupted_memory` | Blind trust in corrupted memory | Verify memory against a reliable tool or explicitly discount stale/corrupted memory. |
| `failure_to_recover_from_tool_error` | Failure to recover from tool error | Fix arguments, choose another tool, or abstain with uncertainty after an error. |
| `repeated_failed_calls` | Repeated failed calls | Change the call, switch tools, or stop with uncertainty after a failed call. |
| `premature_stopping` | Premature stopping | Continue until required evidence has been gathered or a principled abstention is warranted. |
| `overlong_inefficient_trajectory` | Overlong/inefficient trajectory | Avoid redundant calls once enough evidence is available. |
| `hallucinated_tool_result` | Hallucinated tool result | Only report tool results that appear in trajectory observations. |
| `final_answer_unsupported_by_trajectory` | Final answer unsupported by trajectory | Make final answers traceable to obtained observations. |
| `correct_final_answer_via_invalid_trajectory` | Correct final answer via invalid trajectory | Treat final correctness as insufficient when the path is invalid. |
| `uncertainty_failure` | Uncertainty failure | Express limitations when evidence is missing, corrupted, contradictory, ambiguous, or errored. |
| `clarification_failure` | Clarification failure | Ask a clarification question when the instruction is ambiguous and tools cannot resolve it. |
| `excessive_tool_overuse` | Excessive tool overuse | Avoid irrelevant tools and stop once needed evidence has been collected. |

## Filters

The gallery also writes cross-case filters under `error_cases/filters/`:

- `final_success_trajectory_failure`: final answer succeeded but trajectory/process scoring failed.
- `clean_succeeds_intervention_fails`: same agent succeeded on the clean base task but failed on an intervention variant.
- `model_a_succeeds_model_b_fails`: one model/agent succeeded on an instance where another failed.
- `high_cost_low_quality`: high-cost or long trajectories with low final/trajectory quality.

## Provenance Requirements

Every mined case includes the run directory, run id, config path or benchmark path when available, config hash, dataset version, seed, model id, prompt hash, scorer version, git commit, and cost/token metadata when recorded. Missing values remain explicit `null` fields rather than being inferred.

Provider keys must remain in environment variables. The gallery redacts obvious secret-shaped fields and values before writing markdown/JSONL excerpts.
