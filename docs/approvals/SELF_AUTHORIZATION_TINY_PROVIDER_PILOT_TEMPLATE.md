# Self-Authorization Template - Tiny Provider Pilot

Status: template only. This file is not an approval until copied or completed
with all fields filled by the responsible user.

## Required Fields

| Field | Value |
| --- | --- |
| Name |  |
| Date | YYYY-MM-DD |
| Max budget USD |  |
| Provider/model category |  |
| Max trajectories | 5 or fewer |
| Dry-run approval | yes / no |
| Live-run approval | yes / no |
| Approval ID | SELF-TINY-YYYY-NNN |

## Required Acknowledgements

- I understand this pilot is preliminary/debug evidence only.
- I understand it cannot support C1-C8, C10, model rankings, or paper asset eligibility.
- I understand `allow_paid_calls=true` is forbidden unless live-run approval is explicitly `yes`.
- I understand API keys must never be written into YAML.
- I understand the live run must remain capped at 5 or fewer trajectories.
- I understand the cost estimate must be within the approved budget before live execution.
- I understand failed gates must remain visible in reports.

## Approval Metadata To Copy Into An APPROVED Config

```yaml
approval:
  advisor_approved: true
  budget_approved: true
  approved_for_dry_run: true
  approved_for_live_run: false
  approved_by: "<name>"
  approval_date: "YYYY-MM-DD"
  advisor_approval_id: "SELF-TINY-YYYY-NNN"
  max_budget_usd: 5.0
  notes: "Self-authorized tiny provider pilot; preliminary/debug evidence only."
```

## Signature

Name:

Date:

Signature or typed authorization:
