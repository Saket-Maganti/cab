# Failure Taxonomy

Engineering taxonomy for annotating agent failures in CausalAgentBench. Mock/stub trajectories validate **detector wiring only**—not real LLM behavior.

| ID | Name | Definition | Trajectory symptom | Final-answer symptom | Metric signal | Example | Likely intervention | Human annotation | Auto-detectable | Reviewer caveat |
|---|---|---|---|---|---|---|---|---|---|---|
| F01 | invalid_tool_call | Tool name not in available set | unknown_tool / tool_unavailable errors | Answer may still look plausible | invalid_tool_call_count | Call `web_search` when unavailable | irrelevant_tools | Mark tool name invalid | Yes | Stub agents may not reflect provider tool schemas |
| F02 | missing_required_tool | Required tool never invoked | Gold sequence incomplete | Answer missing key evidence | missing_required_tool_count | Skip verify_fact on memory task | memory_corruption | List missing tools | Yes | Required set is benchmark-defined |
| F03 | unnecessary_tool_call | Tool not needed for task | Extra calls beyond gold | Answer unchanged | unnecessary_tool_call_rate | Call all tools “just in case” | irrelevant_tools | Count extra calls | Yes | “Necessary” can be subjective for hard tasks |
| F04 | repeated_failed_tool_call | Retry same failing tool | Same tool errors repeat | Stuck or generic failure | repeated_failed_call_count | Retry broken lookup 3× | tool_failure | Note retry pattern | Yes | Some retries are valid recovery |
| F05 | wrong_tool_argument | Schema/semantic argument errors | invalid_arguments errors | Wrong entity/field in answer | argument_error_count | Empty query string | tool_corruption | Copy bad args | Yes | Semantic validity partially heuristic |
| F06 | blind_memory_trust | Uses corrupted memory without check | No verify after memory consult | Answer matches bad memory | blind_trust_in_corrupted_memory | Quote wrong threshold | memory_corruption | Flag memory reliance | Partial | Needs memory-corruption instances |
| F07 | failed_memory_verification | Should verify memory but does not | verify_fact absent after memory patch | Confident wrong answer | memory_verified_binary=false | Skip policy lookup | memory_corruption | Note missing verification | Partial | Detector calibrated on mock agents |
| F08 | contradiction_miss | Conflicting observations ignored | No branching after conflict | Overconfident unified answer | contradiction_detected_binary=false | Ignore conflicting totals | observation_conflict | Mark missed conflict | Partial | Conflict patterns are synthetic |
| F09 | contradiction_unresolved | Conflict noticed but not resolved | Mentions conflict, no resolution | “Unclear” without rationale | contradiction_resolved_binary=false | “Tools disagree” then guess | observation_conflict | Rate resolution quality | Partial | Human rubric needed for edge cases |
| F10 | premature_stop | Stops before criteria met | Few steps, early final action | Short unsupported answer | premature_stop_binary | Answer after one tool | premature_success_signal | Mark early stop | Yes | Step budget affects detection |
| F11 | max_step_exhaustion | Hits step limit without answer | max_steps termination | Empty or partial answer | terminated_reason=max_steps | Loop without final | long_horizon_dependency | Note budget exhaustion | Yes | Not always a “failure” if abstaining |
| F12 | unsupported_final_answer | Answer not entailed by observations | Tools called but ignored | Confident wrong conclusion | final_success=0, trajectory_success=0 | Wrong hotel ID | tool_corruption | Judge answer support | Partial | Final-success rubric is heuristic |
| F13 | overconfident_uncertainty | Should abstain but answers confidently | No uncertainty language | Definitive wrong answer | correct_abstention_uncertainty_binary=false | Guess policy threshold | ambiguous_instruction | Rate calibration | Partial | Wording-based detector |
| F14 | answer_changed_unchanged_evidence | Answer flips without new evidence | Same observations, new answer | Inconsistent across repeats | N/A (repeat/comparison) | Random flip on rerun | N/A | Compare trajectories | No | Requires multi-run comparison |
| F15 | answer_unchanged_contradicted_evidence | Keeps answer despite contradiction | Conflict observations present | Same answer as clean | contradiction + final match clean | Ignore conflict | observation_conflict | Flag unchanged wrong answer | Partial | Pair clean/intervention instances |

## Annotation guidance

Human validators should tag primary failure IDs (max 2) per trajectory in the validation export. Automatic detectors emit overlapping diagnostic labels in `scores.jsonl` → `diagnostics.failure_modes`.

## Mock diagnostic mapping

| Mock agent | Expected primary failures |
|---|---|
| mock_tool_overuser | F03 |
| mock_memory_blind | F06, F07 |
| mock_contradiction_blind | F08, F09 |
| mock_premature_stop | F10 |
| mock_argument_sloppy | F05 |
| mock_recovery_weak | F04, F11 (when errors injected) |
| mock_brittle | F04, F10 |

See [docs/EVIDENCE_LEVEL_POLICY.md](EVIDENCE_LEVEL_POLICY.md)—mock diagnostics are **engineering_only**.
