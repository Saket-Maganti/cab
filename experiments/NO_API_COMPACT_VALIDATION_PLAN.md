# No-API Compact Validation Plan

Status labels for every output from this plan:

- `engineering_only`
- `no_provider_evidence`
- `not_scientific_model_performance`

## Purpose

Provide a zero-cost fallback path while the live provider pilot is blocked by missing `OPENAI_API_KEY`.

This plan improves benchmark design readiness and review hygiene. It does not create provider-backed evidence, human-validation evidence, or empirical model-performance results.

## Allowed Inputs

Use only:

- dry-run outputs from `configs/provider_pilot_tiny_APPROVED.yaml`,
- stub/mock artifacts already supported by the repo,
- static task/intervention inspection,
- `docs/GOLD_OUTPUT_POLICY.md`,
- gold-output manual-review queue reports,
- high-risk intervention queue reports,
- scorer fixture tests,
- no-API task review templates under `data/human_validation/no_api_task_review/`.

Do not call providers. Do not run local LLMs unless using the repo's documented safe stub/mock path. Do not run `main_200`, `main_500`, Compact-20, Compact-50, or broad sweeps.

## Workstream A: Dry-Run And Static Gates

Commands:

```bash
python3 scripts/check_evidence_safety.py
PYTHONPATH=src python3 -m causal_agent_bench all-no-run-reports --output-dir /tmp/cab_no_api_fallback
PYTHONPATH=src python3 -m causal_agent_bench neurips-submission-gate --output-dir /tmp/cab_no_api_fallback/neurips_submission_gate
PYTHONPATH=src python3 -m causal_agent_bench validity-scorecard --output-dir /tmp/cab_no_api_fallback/validity_scorecard
```

Interpretation:

- governance and readiness only,
- no provider-backed evidence,
- no scientific model-performance evidence,
- no paper asset eligibility.

## Workstream B: Gold-Policy Review

Source policy:

- `docs/GOLD_OUTPUT_POLICY.md`
- `reports/GOLD_OUTPUT_TRIAGE_COMPACT_PLAN.md`

Review questions:

- Should the intervention change the expected answer?
- Is abstention acceptable?
- Is a limitation statement acceptable?
- Are multiple answers acceptable?
- Is the sample too ambiguous for a compact slice?
- Is the sample frozen and therefore documentation-only?

Deliverable:

- completed copy of `data/human_validation/no_api_task_review/gold_policy_review_template.csv`

Evidence status:

- `engineering_only`
- `no_provider_evidence`
- `not_scientific_model_performance`

## Workstream C: Task And Intervention Review

Source surfaces:

- `docs/INTERVENTION_VALIDITY_DOSSIER.md`
- `reports/INTERVENTION_VALIDITY_DOSSIER.md`
- high-risk intervention queue output from a no-run report bundle

Review questions:

- Is the task instruction clear?
- Is the intervention isolated?
- Does the perturbation introduce multiple simultaneous changes?
- Should the sample be excluded from a compact slice?
- Does the sample require a gold-policy decision before use?

Deliverable:

- completed copy of `data/human_validation/no_api_task_review/task_review_template.csv`

This is task-design review only. It is not C3 trajectory evidence and cannot support C10.

## Workstream D: Scorer Fixture Tests

Use deterministic fixture tests only. Acceptable targets include scorer and governance tests that do not call providers.

Minimum expected checks:

- deterministic scorer handles exact answers,
- mismatch categories are closed and documented,
- no-API artifacts cannot promote claims,
- incomplete provider outputs remain blocked from evidence.

Evidence status:

- scorer engineering readiness only,
- not provider trajectory validation.

## Workstream E: Compact Slice Readiness Notes

After no-API review, create a candidate compact slice note only if every selected row has:

- clear task wording,
- isolated intervention,
- explicit gold-policy decision,
- no unresolved high-risk ambiguity,
- no claim that model outputs were evaluated.

The note must say:

- no provider was run,
- no model ranking is supported,
- no C1-C8/C10 claim is supported,
- human validation remains incomplete until completed annotation rows exist.

## Explicit Non-Claims

This plan does not support:

- C1-C8,
- C3 trajectory claims,
- C10,
- NeurIPS readiness,
- COLM empirical readiness,
- model rankings,
- provider integration evidence,
- human-validation metrics.

## Exit Criteria

No-API fallback is ready when:

- blocker report exists,
- future API checklist exists,
- manual task/gold review templates exist,
- compact strategy docs include the blocked-provider/no-API fallback,
- targeted fixture tests pass,
- safe no-provider commands complete.

Final no-API verdict target: `NO_API_FALLBACK_READY`.
