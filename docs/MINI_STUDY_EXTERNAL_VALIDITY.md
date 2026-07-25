# Synthetic-to-Realistic Mini-Study

This mini-study addresses a common reviewer concern: template-generated synthetic tasks may not resemble realistic agent workloads.

## Design

- **Template cohort**: standard domain templates (`task_style: template`).
- **Naturalistic cohort**: mock emails, calendars, spreadsheets, policy excerpts, bug reports, product catalogs, and escalation bundles (`task_style: naturalistic`).
- **Environment**: still local, deterministic, and fully synthetic.
- **Comparison**: intervention-family absolute degradation patterns between two runs on the same agents.

This is an external-validity scaffold, not a deployment claim.

## Generate datasets

```bash
python -m causal_agent_bench generate --config configs/generate_mini_study_template_40.yaml
python -m causal_agent_bench generate --config configs/generate_mini_study_naturalistic_40.yaml
python -m causal_agent_bench audit-interventions --benchmark-dir data/processed/mini_study_template_40
python -m causal_agent_bench audit-interventions --benchmark-dir data/processed/mini_study_naturalistic_40
```

Each config produces 40 base tasks (within the 30–50 target band), five interventions per task, and pilot/dev/heldout splits.

## Run engineering comparison (local stub)

```bash
python -m causal_agent_bench run --config configs/mini_study_template_stub.yaml
python -m causal_agent_bench run --config configs/mini_study_naturalistic_stub.yaml
python -m causal_agent_bench compare-mini-study \
  --template-run-dir results/<timestamp>_mini_study_template_stub \
  --naturalistic-run-dir results/<timestamp>_mini_study_naturalistic_stub \
  --output-dir results/mini_study_comparison
```

Outputs:

- `mini_study_comparison.json`
- `mini_study_comparison.md`
- `table_mini_study_family_comparison.{csv,md,tex}`
- `mini_study_paper_paragraph.tex`

## Interpretation rules

- Report Spearman correlation of family-level absolute degradation and per-family differences.
- If patterns diverge (`pattern_similarity: different`), do not merge cohorts in paper tables.
- Stub runs are `pilot_stub_engineering_only` evidence and must not be presented as validated model results.
- For scientific claims, repeat the comparison on validated commercial API runs with human audit on divergent families.

## Artifact types in naturalistic tasks

| Domain | Mock artifact |
| --- | --- |
| `mock_email_thread` | Internal email thread |
| `mock_calendar_scheduling` | Calendar export |
| `mock_spreadsheet_ops` | Workbook / fulfillment sheet |
| `mock_policy_document` | Policy excerpt |
| `mock_bug_report` | Bug report + log snippet |
| `mock_product_database` | Product catalog record |
| `mock_customer_escalation` | Escalation packet (email + policy + calendar) |
| `mock_incident_postmortem` | Incident postmortem draft |
