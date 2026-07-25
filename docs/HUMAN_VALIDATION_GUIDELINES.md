# Human validation guidelines

Human validation is **planned**, not complete. Do not mark label-quality claims as supported from automation alone.

## Sampling

Export a sample without running annotation:

```bash
python3 scripts/sample_human_validation.py --run-dir results/<run_dir> --max-cases 5
python3 scripts/validate_human_audit_sample.py data/human_validation/sample.jsonl
```

Works with stub, mock, micro, or completed real runs.

## Annotation schema

Each row in `data/human_validation/sample.jsonl`:

- `instance_id`, `agent_name` (required)
- `labels` (optional until annotated)
- `notes` (optional)

## Analysis (when labels exist)

```bash
python3 scripts/analyze_human_validation.py data/human_validation/sample.jsonl
```

## Claim safety

- Incomplete human audit → keep C6/C7-style claims `planned`
- Agreement metrics require sufficient labeled pairs and documented protocol

See also: `docs/HUMAN_VALIDATION_PILOT_PLAN.md`, `docs/HUMAN_VALIDATION_FORM_SCHEMA.md`
