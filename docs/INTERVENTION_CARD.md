# Intervention Card: CausalAgentBench

**Design principle:** paired clean/intervention instances with **one primary patch group** per intervention when possible.

## Intended Use

Isolate environmental factors (tool availability, reliability, observations, memory, instructions, completion signals, evidence relevance) to study **which skill components fail** under named perturbations — not just whether accuracy drops.

## Out-of-Scope Use

- Claiming perfect single-factor causality without human audit.
- Production incident simulation (real systems combine failures).
- Using interventions to change the gold answer without documenting `expected_final_answer_change`.
- Applying web-shadow families to API-interface tasks without reading the interface-specific docs.

## Data Construction

For each `BaseTask`:

1. Emit clean `BenchmarkInstance` (`condition: clean`).
2. Apply `make_intervention()` or `make_web_shadow_intervention()` → `InterventionSpec`.
3. Emit intervention instance with patched tools, memory, tool outputs, or instruction text.
4. Record `changed_factor`, `expected_behavior`, `severity`, `metadata.designed_failure_mode`.

Audit tooling: `audit-interventions` → `intervention_audit_report.json` (`docs/INTERVENTION_AUDIT.md`).

## Synthetic Data Policy

Interventions are **programmatic patches** on synthetic tasks. They are reproducible from JSONL + generator seed but are not validated against real API failure distributions.

## Intervention Families

### Core (template benchmark)

| Family | Patch group | Primary factor |
|--------|-------------|----------------|
| `tool_removal` | `tool_availability_patch` | Required tool removed |
| `tool_failure` | `tool_output_patch` | Deterministic tool error |
| `tool_corruption` | `tool_output_patch` | Incorrect tool output |
| `irrelevant_tools` | `tool_availability_patch` | Distractor tools added |
| `memory_corruption` | `memory_patch` | Stale initial memory |
| `observation_conflict` | `tool_output_patch` | Conflicting observations |
| `ambiguous_instruction` | `instruction_patch` | Underspecified criterion |
| `long_horizon_dependency` | `tool_output_patch` | Cross-step dependency marker |
| `premature_success_signal` | `tool_output_patch` | Early completion signal |
| `distractor_evidence` | `tool_output_patch` | Irrelevant evidence record |

### Web shadow (optional, static snapshot)

| Family | Primary factor |
|--------|----------------|
| `web_broken_link` | Hyperlink 404 in frozen site |
| `web_stale_page` | Archived/stale page body |
| `web_conflicting_page` | Contradictory on-page facts |
| `web_irrelevant_search_result` | High-ranked search distractor |
| `web_hidden_evidence` | Section hidden until navigation |

API-interface web-shadow tasks use **mirrored** core families instead (`docs/WEB_SHADOW_STUDY.md`).

## Scoring Methodology

Intervention instances are scored with the same heuristic final-success rules as clean tasks unless `expected_final_answer_change` is `yes` (e.g. `tool_removal` may require limitation statements). Component metrics:

- `tool_error_recovery_binary`, `contradiction_*`, `memory_*`, `premature_stop_binary`, family-level ACRS.

See `docs/INTERVENTIONS.md` for generation details and `docs/METRIC_CARD_ACRS.md` for robustness aggregation.

## Validation Status

| Check | Status |
|-------|--------|
| Automated patch-isolation warnings | Implemented |
| Family audit guide (`INTERVENTION_FAMILY_AUDIT_GUIDE`) | Implemented |
| Pilot intervention audit on `pilot_v0.1` | Available |
| Expert/human single-factor verification | **Incomplete** |
| Claim C10 (intervention validity) | **Engineering only** |

## Known Failure Modes

- Secondary difficulty shifts (step budget, evidence removal side effects).
- `tool_failure` + answer still reachable via alternate tools.
- Keyword-based contradiction/memory detectors vs human judgment.
- Web/API intervention analogy is approximate, not identical.

## Contamination Risk

Publishing full `interventions.jsonl` exposes patch templates. Agents may overfit to family names or patch shapes. Use held-out templates and undisclosed seeds for final evaluation.

## Maintenance Plan

- New families require schema `InterventionType` update, audit guide entry, quality-check rules, and changelog.
- Renaming families breaks comparability — bump `benchmark_version`.
- Human audit samples: `human_audit_sample.jsonl` in frozen bundles.

## License

MIT (`LICENSE`). Intervention specs are part of the synthetic dataset release.
