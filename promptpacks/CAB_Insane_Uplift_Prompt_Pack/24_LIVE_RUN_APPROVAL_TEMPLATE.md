# CAB Live Run Approval Template

Use this only when you are ready to authorize paid/provider execution.

## Authorization Type

Authorization type:
Project:
Run name:
Purpose:

## Authorizing Person

Name:
Role:

## Approved Scope

- Run config path:
- Task slice:
- Number of task pairs:
- Conditions:
- Number of models:
- Expected total trajectories:
- Maximum trajectories:
- Provider/model list:
- Maximum provider calls:
- Maximum approved budget USD:
- Evidence scope:

## Live Run Approval

Live-run approval: No

To approve, change exactly this line to:

Live-run approval: Yes

## Required Safety Conditions

Before execution, all must pass:

- evidence safety check,
- config validation,
- plan-run,
- estimate-run-cost,
- dry-run/preflight,
- no API keys in YAML,
- provider credentials via environment only,
- budget estimate <= approved budget,
- trajectory count <= approved maximum,
- `scientific_claims_allowed=false` before post-run audit,
- `paper_asset_eligibility=false` before post-run audit.

## Post-Run Requirements

After execution, create:

- post-run audit,
- trajectory review CSV,
- scorer sanity report,
- evidence classification report,
- claim ledger update if supported,
- paper asset eligibility report if supported.

## Risk Acknowledgement

I understand that:

- provider calls may cost money,
- outputs may fail,
- pilot evidence may be preliminary only,
- this run may not support paper claims,
- no claims may be promoted until audit passes,
- API keys must not be stored in the repo.

## Authorization Statement

I authorize only the exact run described above.

Signature / typed name:
Date:
