# Compact-20 Task Audit Guide

Status: review infrastructure only. Do not treat this as human review.

## Audit Dimensions

- task clarity: the user instruction, available tools, and success criteria are understandable without private context.
- gold ambiguity: expected final answer and acceptable variants are documented.
- scorer fragility: deterministic scorer cannot pass/fail on accidental substrings alone.
- intervention confounding: only the intended intervention factor changes.
- human review required: any unclear dimension routes to real human review before execution.

## Required Reviewer Fields

- `task_clarity_risk`: `low`, `medium`, `high`
- `gold_ambiguity_risk`: `low`, `medium`, `high`
- `scorer_fragility_risk`: `low`, `medium`, `high`
- `intervention_confounding_risk`: `low`, `medium`, `high`
- `exclusion_reason`: blank only if no exclusion applies
- `replacement_priority`: `none`, `low`, `medium`, `high`
- `human_review_required`: boolean

## No-Execution Rule

This guide may improve candidate review. It must not prefill human-review CSVs, C10 rows, or paper-eligibility fields.
